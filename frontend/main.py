"""
Chargelogger Streamlit frontend.
"""

# Ruff gets confused by loguru's logger, so we need to disable the check for this file.
# ruff: noqa: PLE1205

import datetime
import os
import sys
import time

import loguru
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit_cookies_controller import CookieController

LOGGER = loguru.logger


class BackendConnector:
    """
    Backend connector for the Chargelogger API.

    Abstracts the API calls to the Chargelogger backend and handles error checking.
    """

    def __init__(self, url):
        """
        Initialize the backend connector.

        Args:
            url (str): The base URL of the Chargelogger backend API.
        """
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
        LOGGER.error('Error {}: {}', response.status_code, response.text)
        msg = f'Error {response.status_code}: {response.text}'
        raise ValueError(msg)

    def login(self, username, password):
        """
        Log in to the Chargelogger backend. A prerequisite for all other API calls.

        Args:
            username (str): The username to log in with.
            password (str): The password to log in with.
        """
        # We cannot use _do_request here as this is a form-encoded request
        response = requests.post(
            f'{self.url}/users/token', data={'username': username, 'password': password}, timeout=10
        )
        if response.status_code != 200:
            LOGGER.error('Error {}: {}', response.status_code, response.text)
            return False
        res = response.json()
        self.token = res['access_token']
        self.user = username
        return True

    def me(self):
        """
        Get the user's own profile.

        Returns:
            dict: The user's profile data.
        """
        return self._do_request('GET', 'users/me')

    def get_cars(self):
        """
        Get a list of all cars of the logged in user.

        Returns:
            list[dict]: A list of all cars.
        """
        cars = self._do_request('GET', 'car/')
        if not cars:
            return []
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
        """
        Get all charges for a specific car.

        Args:
            car_id (int): The ID of the car to get charges for.
            timeframe (datetime.datetime): The earliest date to get charges from.

        Returns:
            list[dict]: A list of all charges for the car.
        """
        req_data = {'limit': 1000}
        if timeframe:
            req_data['from_date'] = timeframe.isoformat()
        all_charges = self._do_request('GET', 'charge/', data=req_data)
        if not all_charges:
            return []
        return [charge for charge in all_charges if charge['car_id'] == car_id]

    def get_cpos(self):
        """
        Get all CPOs of the logged in user.

        Returns:
            list[dict]: A list of all CPOs.
        """
        return self._do_request('GET', 'cpo/', data={'limit': 100})

    def edit_cpo(self, cpo_dict):
        """
        Edit a CPO.

        Args:
            cpo_dict (dict): The CPO data to edit. Must contain an 'id' key.

        Returns:
            str: An error message if the edit failed, otherwise None.
        """
        if 'id' not in cpo_dict:
            msg = 'CPO ID is required'
            raise ValueError(msg)
        api_dict = cpo_dict.copy()
        del api_dict['id']
        try:
            self._do_request('PUT', f'cpo/{cpo_dict["id"]}', data=api_dict)
        except ValueError as err:
            return err.args[0]
        else:
            return None

    def add_cpo(self, cpo_dict):
        """
        Create a new CPO.

        Args:
            cpo_dict (dict): The CPO data to create. Must contain a 'name' and 'default_price' key.

        Returns:
            str: An error message if the creation failed, otherwise None.
        """
        if 'name' not in cpo_dict or 'default_price' not in cpo_dict:
            msg = 'Name and default price are required'
            raise ValueError(msg)
        cpo_dict = {'name': cpo_dict['name'].strip(), 'default_price': cpo_dict['default_price']}
        try:
            self._do_request('POST', 'cpo/', data=cpo_dict)
        except ValueError as err:
            return err.args[0]
        else:
            return None

    def add_charge(self, charge_dict):
        """
        Add a new charge. Handles conversion of float values to integer cents.

        Args:
            charge_dict (dict): The charge data to add.

        Returns:
            str: An error message if the creation failed, otherwise None.
        """
        api_dict = charge_dict.copy()
        api_dict['kwh_charged'] = int(api_dict['kwh_charged'] * 100)
        api_dict['price_total'] = int(api_dict['price_total'] * 100)
        try:
            self._do_request('POST', 'charge/', data=api_dict)
        except ValueError as err:
            return err.args[0]
        else:
            return None

    def edit_charge(self, charge_dict):
        """
        Edit a charge. Handles conversion of float values to integer cents.

        Args:
            charge_dict (dict): The charge data to edit. Must contain an 'id' key.

        Returns:
            str: An error message if the edit failed, otherwise None.
        """
        api_dict = charge_dict.copy()
        api_dict['kwh_charged'] = int(api_dict['kwh_charged'] * 100)
        api_dict['price_total'] = int(api_dict['price_total'] * 100)
        del api_dict['id']
        try:
            self._do_request('PUT', f'charge/{charge_dict["id"]}', data=api_dict)
        except ValueError as err:
            return err.args[0]
        else:
            return None

    def delete_charge(self, charge_id):
        """
        Delete a charge.

        Args:
            charge_id (int): The ID of the charge to delete.

        Returns:
            str: An error message if the deletion failed, otherwise None.
        """
        try:
            return self._do_request('DELETE', f'charge/{charge_id}')
        except ValueError as err:
            return err.args[0]


class ChargeloggerFrontend:
    """
    Frontend for the Chargelogger application.
    """

    def __init__(self, backend):
        """
        Initialize the frontend.

        Args:
            backend (str): The URL of the Chargelogger backend
        """
        self.backend = BackendConnector(backend)
        self.cookies = CookieController()
        self.me: dict | None = None
        self.cars: list[dict] | None = []
        self.cpos: list[dict] | None = []
        self.charges_df: pd.DataFrame | None = None
        # Try to load the token from state or cookie
        st.session_state.user_token = st.session_state.get('user_token') or self.cookies.get('user_token')
        if st.session_state.user_token:
            self.backend.token = st.session_state.user_token
            try:
                self.backend.me()
            except ValueError:
                st.session_state.user_token = None
                return
            self.refresh_data()

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
            self.cookies.set('user_token', self.backend.token)
        else:
            st.error('Login failed')

    def logout(self):
        """Logs out the user."""
        st.session_state.user_token = None
        st.session_state.username = None
        if self.cookies.get('user_token'):
            self.cookies.remove('user_token')

    def check_authentication(self):
        """Handles login and authentication state."""
        if st.session_state.user_token is None:
            LOGGER.info('User not authenticated, showing login form')
            center = st.columns(3)
            with center[1], st.form('login_form'):
                st.title('Login')
                st.text_input('Username', key='username')
                st.text_input('Password', type='password', key='password')
                st.form_submit_button('Login', on_click=self.try_login)
            return False  # Not authenticated

        LOGGER.info('User authenticated, fetching data')
        self.backend.token = st.session_state.user_token
        try:
            me = self.backend.me()
            self.refresh_data()
            if me:
                LOGGER.info('User authenticated as {}', me.get('username'))
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
            car_names = sorted([car['Name'] for car in self.cars or []])
            st.selectbox('Select a car', car_names, key='selected_car')
            st.selectbox(
                'See CPO Details',
                sorted([cpo['name'] for cpo in self.cpos or []], key=str.casefold),
                key='selected_cpo',
                index=None,
                on_change=self.handle_cpo_selection,
            )
            st.button('Add CPO', on_click=self.add_cpo)
            st.radio(
                'Timeframe',
                ['Last month', 'Last year', 'All time'],
                key='selected_timeframe',
                index=1,
                on_change=self.load_charges,
            )
            st.divider()
            if self.me:
                st.write(f'Logged in as {self.me["username"]}')
            st.button('Logout', on_click=self.logout)

    def show_car_info(self):
        """
        Displays an overview of the selected car.
        """
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
            'default_price': st.column_config.NumberColumn('Default Price', format='0.%d €', required=True),
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

    @st.dialog('Add CPO')
    def add_cpo(self):
        """Adds a new CPO."""
        columns_config = {
            'name': st.column_config.TextColumn('Name', required=True),
            'default_price': st.column_config.NumberColumn('Default Price', format='0.%d €', required=True),
        }
        empty_column = {'name': '', 'default_price': 0}
        st.data_editor([empty_column], key='cpo_new', column_config=columns_config)
        if st.button('Add'):
            if not st.session_state.cpo_new.get('edited_rows'):
                st.error('No data entered')
            new_cpo = st.session_state.cpo_new['edited_rows'][0]
            if not new_cpo.get('name').strip():
                st.error('Name is required and cannot be empty')
            if msg := self.backend.add_cpo(new_cpo):
                st.error(msg)
            else:
                st.balloons()
                time.sleep(1)
                st.rerun()

    def load_charges(self):
        """Fetches and processes charge data."""
        selected_timeframe = st.session_state.selected_timeframe
        if selected_timeframe == 'Last month':
            timeframe = datetime.datetime.now(datetime.UTC)
            timeframe = timeframe.replace(month=timeframe.month - 1)
        elif selected_timeframe == 'Last year':
            timeframe = datetime.datetime.now(datetime.UTC)
            timeframe = timeframe.replace(year=timeframe.year - 1)
        else:
            timeframe = None
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
    def review_charge_edits(self):  # noqa: C901, PLR0912, PLR0915
        """Handles reviewing and saving charge edits."""
        car_name = st.session_state.selected_car
        changeset = st.session_state.charges_editor
        cpo_ids = {cpo['name']: cpo['id'] for cpo in self.cpos or []}
        if not all((changeset, self.charges_df is not None, self.cars)):
            st.error('No changes to review or data error. Try reloading the page.')
            return

        to_change = []
        to_add = []
        to_delete = []
        if self.charges_df is None or not self.cars:
            st.error('No charge data to edit')
            return
        for edit_row, changes in changeset.get('edited_rows', {}).items():
            log = []
            affected_row = self.charges_df.iloc[edit_row].to_dict()
            affected_row['date'] = str(self.charges_df.index[edit_row])
            st.subheader(f'Charge on {affected_row["date"]}')
            for key, new_value in changes.items():
                if key == '_index':
                    key = 'date'  # noqa: PLW2901
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
        """Displays charge data."""
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
                a, b, c, d, _ = st.columns(5)
                total_km = year_df['car_km_driven'].sum()
                total_price = round(year_df['price_total'].sum(), 2)
                price_100_km = round(year_df['price_total'].sum() / year_df['car_km_driven'].sum() * 100, 2)
                kwh_per_100_km = round(year_df['kwh_charged'].sum() / year_df['car_km_driven'].sum() * 100, 2)
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
                d.metric(
                    'kWh / 100 km',
                    f'{kwh_per_100_km}',
                    border=True,
                    delta=round(kwh_per_100_km - prev_year['kwh_per_100_km'], 2) if prev_year else None,
                    delta_color='inverse',
                )
                prev_year = {
                    'total_km': total_km,
                    'total_price': total_price,
                    'price_100_km': price_100_km,
                    'kwh_per_100_km': kwh_per_100_km,
                }
        else:
            if self.charges_df is None:
                return
            st.subheader('Statistics')
            a, b, c, d = st.columns(4)
            total_km = self.charges_df['car_km_driven'].sum()
            total_price = round(self.charges_df['price_total'].sum(), 2)
            price_100_km = round(self.charges_df['price_total'].sum() / self.charges_df['car_km_driven'].sum() * 100, 2)
            kwh_per_100_km = round(
                self.charges_df['kwh_charged'].sum() / self.charges_df['car_km_driven'].sum() * 100, 2
            )
            a, b, c, d, _ = st.columns(5)
            a.metric('Total Distance', f'{total_km} km', border=True)
            b.metric('Total Price', f'{total_price} €', border=True)
            c.metric('Price per 100 km', f'{price_100_km} €', border=True)
            d.metric('kWh / 100 km', f'{kwh_per_100_km}', border=True)

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
    backend_url = 'http://localhost:8000'
    backend_url = os.environ.get('CHARGELOGGER_BACKEND', backend_url)
    if len(sys.argv) > 1:
        backend_url = sys.argv[1]

    st.set_page_config(page_title='Chargelogger', page_icon='🔌', layout='wide')
    frontend = ChargeloggerFrontend(backend_url)
    LOGGER.info('Starting application with backend at {}', backend_url)

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
