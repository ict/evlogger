import datetime

import loguru
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
        this_year = datetime.datetime.now(datetime.UTC).replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        all_charges = self._do_request('GET', 'charge/', data={'from_date': this_year.isoformat(), 'limit': 1000})
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
            }
            for charge in all_charges
            if charge['car_id'] == car_id
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
        st.header('Charges this year')
        charges = BACKEND.get_charges(next(car['id'] for car in cars if car['Name'] == car_name))
        st.dataframe(charges)
        st.button('Logout', on_click=logout)


if __name__ == '__main__':
    main()
