import datetime
import time

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

        if method == 'GET':
            response = requests.request(method, f'{self.url}/{endpoint}', headers=headers, params=data, timeout=10)
        else:
            response = requests.request(method, f'{self.url}/{endpoint}', headers=headers, json=data, timeout=10)

        if response.status_code == 204:
            return None
        if 200 <= response.status_code < 300:
            return response.json()
        LOGGER.error('Error {}: {}', response.status_code, response.text)  # noqa: PLE1205
        msg = f'Error {response.status_code}: {response.text}'
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
        cars = self._do_request('GET', 'car/')
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

    def get_charges(self, car_id, timeframe):
        req_data = {'limit': 1000}
        if timeframe:
            req_data['from_date'] = timeframe.isoformat()
        all_charges = self._do_request('GET', 'charge/', data=req_data)
        return [charge for charge in all_charges if charge['car_id'] == car_id]

    def get_cpos(self):
        return self._do_request('GET', 'cpo/', data={'limit': 100})

    def edit_cpo(self, cpo_dict):
        api_dict = cpo_dict.copy()
        del api_dict['id']
        try:
            self._do_request('PUT', f'cpo/{cpo_dict["id"]}', data=api_dict)
            return None
        except ValueError as err:
            return err.args[0]

    def add_charge(self, charge_dict):
        api_dict = charge_dict.copy()
        api_dict['kwh_charged'] = int(api_dict['kwh_charged'] * 100)
        api_dict['price_total'] = int(api_dict['price_total'] * 100)
        try:
            self._do_request('POST', 'charge/', data=api_dict)
            return None
        except ValueError as err:
            return err.args[0]

    def edit_charge(self, charge_dict):
        api_dict = charge_dict.copy()
        api_dict['kwh_charged'] = int(api_dict['kwh_charged'] * 100)
        api_dict['price_total'] = int(api_dict['price_total'] * 100)
        del api_dict['id']
        try:
            self._do_request('PUT', f'charge/{charge_dict["id"]}', data=api_dict)
            return None
        except ValueError as err:
            return err.args[0]

    def delete_charge(self, charge_id):
        try:
            return self._do_request('DELETE', f'charge/{charge_id}')
        except ValueError as err:
            return err.args[0]


class ChargeloggerFrontend:
    def __init__(self, backend):
        self.backend = BackendConnector(BACKEND_URL)
        self.me: dict | None = None
        self.cars: list[dict] | None = []
        self.cpos: list[dict] | None = []
        self.charges_df: pd.DataFrame | None = None
        if 'user_token' not in st.session_state:
            st.session_state.user_token = None
        else:
            self.backend.token = st.session_state.user_token
            try:
                self.backend.me()
            except ValueError:
                st.session_state.user_token = None

    def refresh_data(self):
        """Refreshes car and CPO data."""
        try:
            self.cars = self.backend.get_cars()
            self.cpos = self.backend.get_cpos()
            self.me = self.backend.me()
        except ValueError as err:
            st.error(err.args[0])
            self.me = None
            self.cars = None
            self.cpos = None
            st.session_state.user_token = None

    def try_login(self):
        """Attempts to log in the user."""
        if self.backend.login(st.session_state.username, st.session_state.password):
            st.session_state.user_token = self.backend.token
            st.session_state.username = self.backend.user
        else:
            st.error('Login failed')

    def logout(self):
        """Logs out the user."""
        st.session_state.user_token = None
        st.session_state.username = None
        st.rerun()

    def check_authentication(self):
        """Handles login and authentication state."""
        if st.session_state.user_token is None:
            LOGGER.info('User not authenticated, showing login form')
            st.title('Login')
            st.text_input('Username', key='username')
            st.text_input('Password', type='password', key='password')
            st.button('Login', on_click=self.try_login)
            return False  # Not authenticated

        LOGGER.info('User authenticated, fetching data')
        self.backend.token = st.session_state.user_token
        try:
            me = self.backend.me()
            self.refresh_data()
            LOGGER.info('User authenticated as {}', me.get('username'))
            if me:
                st.session_state.username = me['username']
                self.me = me
                return True  # Authenticated
        except ValueError:
            st.session_state.user_token = None
            return False

    def configure_sidebar(self):
        """Configures the sidebar for selecting cars, CPOs, and timeframe."""
        if not all((self.cars, self.cpos, self.me)):
            self.refresh_data()
            return
        with st.sidebar:
            st.header('View settings')
            car_names = sorted([car['Name'] for car in self.cars])
            st.selectbox('Select a car', car_names, key='selected_car')
            st.selectbox(
                'See CPO Details',
                sorted([cpo['name'] for cpo in self.cpos], key=str.casefold),
                key='selected_cpo',
                index=None,
                on_change=self.handle_cpo_selection,
            )
            st.radio(
                'Timeframe',
                ['Last month', 'Last year', 'All time'],
                key='selected_timeframe',
                index=1,
                on_change=self.load_charges,
            )
            st.divider()
            st.write(f'Logged in as {self.me["username"]}')
            st.button('Logout', on_click=self.logout)

    def show_car_info(self):
        car_name = st.session_state.selected_car
        if not self.cars:
            self.refresh_data()
            return
        st.title(f'{car_name} Overview')
        st.dataframe([car for car in self.cars if car['Name'] == car_name], hide_index=True)

    def handle_cpo_selection(self):
        """Handles selection of a CPO."""
        if st.session_state.selected_cpo:
            self.cpo_details()

    @st.dialog('CPO Details')
    def cpo_details(self):
        """Displays CPO details and allows editing."""
        if not self.cpos:
            return
        cpo_ids = {cpo['name']: cpo['id'] for cpo in self.cpos}
        cpo_name = st.session_state.selected_cpo
        cpo = next(cpo for cpo in self.cpos if cpo['id'] == cpo_ids[cpo_name])
        columns_config = {
            'name': st.column_config.TextColumn('Name', required=True),
            'default_price': st.column_config.NumberColumn('Default Price', format='%.2f €', required=True),
            'id': None,
            'owner_id': None,
        }
        st.data_editor([cpo], key='cpo_editor', column_config=columns_config)
        if st.button('Save changes'):
            updated_data = st.session_state.cpo_editor['edited_rows'][0]
            cpo['name'] = updated_data.get('name', cpo['name'])
            cpo['default_price'] = updated_data.get('default_price', cpo['default_price'])
            if msg := self.backend.edit_cpo(cpo):
                st.error(msg)
            else:
                st.balloons()
                time.sleep(1)
                st.rerun()

    def load_charges(self):
        """Fetches and processes charge data."""
        selected_timeframe = st.session_state.selected_timeframe
        LOGGER.info('Loading charges for {}', selected_timeframe)
        if selected_timeframe == 'Last month':
            timeframe = datetime.datetime.now(datetime.UTC)
            timeframe = timeframe.replace(month=timeframe.month - 1)
        elif selected_timeframe == 'Last year':
            timeframe = datetime.datetime.now(datetime.UTC)
            timeframe = timeframe.replace(year=timeframe.year - 1)
        else:
            timeframe = None
        LOGGER.info('Timeframe: {}', timeframe)
        if not self.cars:
            self.refresh_data()
            return
        car_name = st.session_state.selected_car
        charges_raw = self.backend.get_charges(
            next(car['id'] for car in self.cars if car['Name'] == car_name), timeframe
        )
        charges_df = pd.DataFrame(charges_raw)
        charges_df['kwh_charged'] /= 100
        charges_df['price_total'] /= 100
        charges_df['price_per_kwh'] /= 100
        charges_df['date'] = pd.to_datetime(charges_df['date'])
        charges_df = charges_df.set_index('date')
        charges_df['car_km_driven'] = charges_df['car_odometer'][::-1].diff().fillna(0)[::-1]
        self.charges_df = charges_df

    @st.dialog('Review Changes')
    def review_charge_edits(self):
        """Handles reviewing and saving charge edits."""
        car_name = st.session_state.selected_car
        changeset = st.session_state.charges_editor
        cpo_ids = {cpo['name']: cpo['id'] for cpo in self.cpos}
        if not all((changeset, self.charges_df is not None, self.cars)):
            st.error('No changes to review or data error. Try reloading the page.')
            return

        to_change = []
        to_add = []
        to_delete = []
        for edit_row, changes in changeset.get('edited_rows', {}).items():
            log = []
            affected_row = self.charges_df.iloc[edit_row].to_dict()
            affected_row['date'] = str(self.charges_df.index[edit_row])
            st.subheader(f'Charge on {affected_row["date"]}')
            for key, new_value in changes.items():
                log.append(f'- {key}:  {affected_row[key]} -> **{new_value}**')
                affected_row[key] = new_value
            if 'cpo_name' in changes:
                log.append(f'- cpo_id: {affected_row["cpo_id"]} -> **{cpo_ids[changes["cpo_name"]]}**')
                affected_row['cpo_id'] = cpo_ids[changes['cpo_name']]
            st.info('\n'.join(log))
            to_change.append(affected_row)
        for new_row in changeset.get('added_rows', []):
            st.subheader('New Charge')
            new_charge = {
                'car_id': next(car['id'] for car in self.cars if car['Name'] == car_name),
            }
            for key, value in new_row.items():
                if key == 'cpo_name':
                    new_charge['cpo_id'] = cpo_ids[value]
                if key == '_index':
                    new_charge['date'] = value
                    continue
                new_charge[key] = value
            st.write(new_charge)
            to_add.append(new_charge)
        if changeset.get('deleted_rows'):
            st.subheader('Deleted Charges')
            lines = []
            for row in changeset.get('deleted_rows'):
                affected_row = self.charges_df.iloc[row].to_dict()
                affected_row['date'] = str(self.charges_df.index[row])
                to_delete.append(affected_row['id'])
                lines.append(f'- Charge at {affected_row["date"]} {affected_row["kwh_charged"]} kWh')
            st.warning('\n'.join(lines))
        if st.button('Save changes'):
            success = True
            for row in to_change:
                if msg := self.backend.edit_charge(row):
                    st.error(msg)
                    success = False
            for row in to_add:
                if msg := self.backend.add_charge(row):
                    st.error(msg)
                    success = False
            for row in to_delete:
                if msg := self.backend.delete_charge(row):
                    st.error(msg)
                    success = False
            if success:
                st.balloons()
                time.sleep(1)
                st.rerun()

    def show_charges(self):
        if not all((self.charges_df is not None, self.cpos is not None)):
            self.refresh_data()
            return

        cpo_ids = {cpo['name']: cpo['id'] for cpo in self.cpos or []}
        columns_config = {
            'date': st.column_config.DateColumn('Date', required=True, disabled=False),
            'car_odometer': st.column_config.NumberColumn('Odometer (km)', format='localized', required=True),
            'car_km_driven': st.column_config.NumberColumn('Distance', format='%f km', disabled=True),
            'kwh_charged': st.column_config.NumberColumn('kWh', required=True),
            'cpo_name': st.column_config.SelectboxColumn('CPO', options=list(cpo_ids.keys()), required=True),
            'price_total': st.column_config.NumberColumn('Price', format='%.2f €', required=True),
            'charge_type': st.column_config.SelectboxColumn('Type', options=['AC', 'DC'], required=True),
            'price_per_kwh': st.column_config.NumberColumn('Price per kWh', format='%.2f €', disabled=True),
            'note': st.column_config.TextColumn('Note'),
            'id': None,
            'car_id': None,
            'car_name': None,
            'owner_id': None,
            'car_soc_after': None,
            'cpo_id': None,
        }

        columns_order = [
            'date',
            'car_odometer',
            'car_km_driven',
            'kwh_charged',
            'price_total',
            'price_per_kwh',
            'cpo_name',
            'charge_type',
            'note',
        ]

        allow_edit = st.checkbox('Allow editing', key='allow_edit')
        if allow_edit:
            st.data_editor(
                self.charges_df,
                column_config=columns_config,
                column_order=columns_order,
                key='charges_editor',
                num_rows='dynamic',
            )
            st.button('Review changes', on_click=self.review_charge_edits)
        else:
            st.dataframe(self.charges_df, column_config=columns_config, column_order=columns_order)

    def display_statistics(self):
        """Displays statistics for charge data."""
        timeframe = st.session_state.selected_timeframe
        if timeframe == 'All time':
            years = self.charges_df.index.year.unique()
            prev_year = None

            for year in sorted(years):
                year_df = self.charges_df[self.charges_df.index.year == year]
                st.subheader(f'{year}')
                a, b, c, d, e = st.columns(5)
                total_km = year_df['car_km_driven'].sum()
                total_price = round(year_df['price_total'].sum(), 2)
                price_100_km = round(year_df['price_total'].sum() / year_df['car_km_driven'].sum() * 100, 2)
                a.metric(
                    'Total Distance',
                    f'{total_km} km',
                    border=True,
                    delta=int(total_km - prev_year['total_km']) if prev_year else None,
                    delta_color='off',
                )
                b.metric(
                    'Total Price',
                    f'{total_price} €',
                    border=True,
                    delta=(round(total_price - prev_year['total_price'], 2) if prev_year else None),
                    delta_color='inverse',
                )
                c.metric(
                    'Price per 100 km',
                    f'{price_100_km} €',
                    border=True,
                    delta=round(price_100_km - prev_year['price_100_km'], 2) if prev_year else None,
                    delta_color='inverse',
                )
                prev_year = {
                    'total_km': total_km,
                    'total_price': total_price,
                    'price_100_km': price_100_km,
                }

    def display_charging_distribution(self):
        """Displays charging distribution statistics."""
        if self.charges_df is None:
            self.refresh_data()
            return

        st.subheader('Charging Distribution')

        ac_charging = self.charges_df[self.charges_df['charge_type'] == 'AC']['kwh_charged'].sum()
        dc_charging = self.charges_df[self.charges_df['charge_type'] == 'DC']['kwh_charged'].sum()

        acdc_cols = st.columns(5)

        # Aggregate AC vs DC charging
        ac_charging = self.charges_df[self.charges_df['charge_type'] == 'AC']['kwh_charged'].sum()
        dc_charging = self.charges_df[self.charges_df['charge_type'] == 'DC']['kwh_charged'].sum()

        total_charging = ac_charging + dc_charging
        ac_dc_ratio = ac_charging / total_charging if total_charging > 0 else 0  # Avoid division by zero

        with acdc_cols[0]:
            st.metric('Total AC Charging (kWh)', round(ac_charging, 2), border=True)
        with acdc_cols[1]:
            st.metric('Total DC Charging (kWh)', round(dc_charging, 2), border=True)
        with acdc_cols[2]:
            st.metric('AC/DC Ratio', f'{ac_dc_ratio:.2%}', border=True)  # Display as percentage

        with acdc_cols[0]:
            fig = px.pie(
                names=['AC', 'DC'],
                values=[ac_charging, dc_charging],
                color=['AC', 'DC'],
                color_discrete_map={'AC': '#66b3ff', 'DC': '#ff6666'},
            )
            with st.expander('Charging Distribution'):
                st.plotly_chart(fig)


if __name__ == '__main__':
    frontend = ChargeloggerFrontend(BackendConnector(BACKEND_URL))
    LOGGER.info('Starting application')
    st.set_page_config(page_title='Chargelogger', page_icon='🔌', layout='wide')

    if not frontend.check_authentication():
        LOGGER.info('User not authenticated')

    else:
        LOGGER.info('Displaying UI')
        frontend.configure_sidebar()
        frontend.show_car_info()

        frontend.load_charges()
        frontend.show_charges()
        frontend.display_charging_distribution()
        frontend.display_statistics()
