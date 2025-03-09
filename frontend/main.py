import datetime

import loguru
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

BACKEND_URL = 'http://localhost:8000'
LOGGER = loguru.logger


class BackendConnector:
    def __init__(self, url):
        self.url = url
        self.user = None
        self.token = None

    def _do_request(self, method, endpoint, data=None):
        headers = {
            'Content-Type': 'application/json',
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        if method != 'POST':
            # LOGGER.debug('Requesting {} with params {}', endpoint, data)
            response = requests.request(method, f'{self.url}/{endpoint}', headers=headers, params=data, timeout=10)
        else:
            # LOGGER.debug('POSTing to {} with data {}', endpoint, data)
            response = requests.post(f'{self.url}/{endpoint}', headers=headers, json=data, timeout=10)

        if 200 <= response.status_code < 300:
            return response.json()
        LOGGER.error('Error {}: {}', response.status_code, response.text)  # noqa: PLE1205
        msg = f'Error {response.status_code}'
        raise ValueError(msg)

    def login(self, username, password):
        # We cannot use _do_request here as this is a form-encoded request
        response = requests.post(
            f'{self.url}/users/token', data={'username': username, 'password': password}, timeout=10
        )
        if response.status_code != 200:
            LOGGER.error('Error {}: {}', response.status_code, response.text)  # noqa: PLE1205
            return False
        res = response.json()
        self.token = res['access_token']
        self.user = username
        return True

    def me(self):
        return self._do_request('GET', 'users/me')

    def get_cars(self):
        cars = self._do_request('GET', 'car')
        return [
            {
                'Name': car['name'],
                'Make': car['make'],
                'Model': car['model'],
                'Color': car['color'],
                'Odometer': car['odometer'],
                'Battery Capacity': car['battery_capacity'],
                'id': car['id'],
            }
            for car in cars
        ]

    def get_charges(self, car_id):
        last_year = datetime.datetime.now(datetime.UTC)
        last_year = last_year.replace(year=last_year.year - 1)
        all_charges = self._do_request('GET', 'charge/', data={'from_date': last_year.isoformat(), 'limit': 1000})
        return [charge for charge in all_charges if charge['car_id'] == car_id]

    def pretty_charges(self, charges):
        return [
            {
                'Date': charge['date'],
                'Odometer': charge['car_odometer'],
                'Distance': charge['car_km_driven'],
                'kWh': float(charge['kwh_charged']) / 100,
                'CPO': charge['cpo_name'],
                'Type': charge['charge_type'],
                'Price': float(charge['price_total']) / 100,
                'Price per kWh': float(charge['price_per_kwh']) / 100,
                'Note': charge['note'],
            }
            for charge in charges
        ]


BACKEND = BackendConnector(BACKEND_URL)


# Function to handle login
def login():
    username = st.session_state.get('username', '')
    password = st.session_state.get('password', '')

    logged_in = BACKEND.login(username, password)
    if logged_in:
        st.session_state.user_token = BACKEND.token
    else:
        st.error('Invalid username or password')


def logout():
    st.session_state.user_token = None


def main():
    st.set_page_config(layout='wide')
    # Initialize session state for authentication
    if 'user_token' not in st.session_state:
        st.session_state.user_token = None

    # Display login form if not authenticated
    if st.session_state.user_token is None:
        st.title('Login')
        st.text_input('Username', key='username')
        st.text_input('Password', type='password', key='password')
        st.button('Login', on_click=login)

    else:
        # Main app content after login
        BACKEND.token = st.session_state.user_token
        me = BACKEND.me()
        st.session_state.username = me['username']
        st.title(f'Welcome {st.session_state.username}')

        st.header('Cars')
        cars = BACKEND.get_cars()
        car_name = st.selectbox('Select a car', [car['Name'] for car in cars], key='selected_car')
        st.dataframe([car for car in cars if car['Name'] == car_name])
        st.divider()

        st.header('Charges')
        charges = BACKEND.get_charges(next(car['id'] for car in cars if car['Name'] == car_name))
        raw = st.checkbox('Show raw data')
        if raw:
            st.dataframe(charges)
        else:
            st.dataframe(BACKEND.pretty_charges(charges))

        st.header('Statistics')

        st.subheader('Charging Distribution')
        acdc_cols = st.columns(5)

        pdf = pd.DataFrame(charges)
        pdf['kwh_charged'] = pdf['kwh_charged'] / 100
        pdf['date'] = pd.to_datetime(pdf['date'])
        pdf = pdf.set_index('date')

        # Aggregate AC vs DC charging
        ac_charging = pdf[pdf['charge_type'] == 'AC']['kwh_charged'].sum()
        dc_charging = pdf[pdf['charge_type'] == 'DC']['kwh_charged'].sum()

        total_charging = ac_charging + dc_charging
        ac_dc_ratio = ac_charging / total_charging if total_charging > 0 else 0  # Avoid division by zero

        with acdc_cols[0]:
            st.metric('Total AC Charging (kWh)', round(ac_charging, 2), border=True)
        with acdc_cols[1]:
            st.metric('Total DC Charging (kWh)', round(dc_charging, 2), border=True)
        with acdc_cols[2]:
            st.metric('AC/DC Ratio', f'{ac_dc_ratio:.2%}', border=True)  # Display as percentage

        # Plot AC vs DC charging in a pie chart
        fig = px.pie(
            names=['AC', 'DC'],
            values=[ac_charging, dc_charging],
            color=['AC', 'DC'],
            color_discrete_map={'AC': '#66b3ff', 'DC': '#ff6666'},
        )
        # Adjust size
        fig.update_layout(width=400, height=400, showlegend=True)  # Set smaller size
        fig.update_traces(textinfo='label+percent', textfont_size=14)  # Set text size
        with st.expander('Charging Distribution'):
            st.plotly_chart(fig, use_container_width=True)

        # Calculate monthly totals
        st.subheader('Monthly Totals')
        monthly_totals = pdf.resample('M').agg({'kwh_charged': 'sum', 'car_km_driven': 'sum'})

        # Rename the columns for display
        monthly_totals['consumption_kwh_per_100km'] = (
            monthly_totals['kwh_charged'] / monthly_totals['car_km_driven'] * 100
        )
        monthly_totals.index = monthly_totals.index.strftime('%Y-%m')
        monthly_totals = monthly_totals.rename(columns={'kwh_charged': 'kWh charged', 'car_km_driven': 'km driven'})

        st.bar_chart(
            monthly_totals['consumption_kwh_per_100km'],
            x_label='Month',
            y_label='kWh / 100km',
            use_container_width=True,
        )
        st.line_chart(monthly_totals, x_label='Month', y=['kWh charged', 'km driven'])

        st.button('Logout', on_click=logout)


if __name__ == '__main__':
    main()
