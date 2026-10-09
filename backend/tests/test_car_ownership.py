"""
Tests for the ownership data of cars: purchase/sale fields, retiring, frozen cars and cascading deletes
"""

import pytest
from starlette import status

from tests.conftest import charge_payload, create_car, create_cpo, new_user_headers

PURCHASE = {'purchase_price': 2_500_000, 'purchase_date': '2022-05-01', 'purchase_odometer': 12000}
SALE = {'sale_price': 1_800_000, 'sale_date': '2024-06-30', 'sale_odometer': 61000}
SALE_FIELDS = ['sale_price', 'sale_date', 'sale_odometer']


@pytest.fixture
def headers(test_app):
    return new_user_headers(test_app)


@pytest.fixture
def car(test_app, headers):
    return create_car(test_app, headers, name='Owned Car', **PURCHASE)


@pytest.fixture
def cpo(test_app, headers):
    return create_cpo(test_app, headers)


def put_car(test_app, headers, car: dict, **changes):
    """Full PUT of a car, like the frontend does: all editable fields, with changes applied."""
    fields = ['name', 'battery_capacity', 'odometer', 'purchase_price', 'purchase_date', 'purchase_odometer']
    payload = {key: car[key] for key in fields + SALE_FIELDS} | changes
    return test_app.put(f'/car/{car["id"]}', headers=headers, json=payload)


def add_charge(test_app, headers, car: dict, cpo: dict, date: str, odometer: int):
    return test_app.post('/charge', headers=headers, json=charge_payload(car['id'], cpo['id'], date, odometer))


def add_expense(test_app, headers, car: dict, date: str):
    return test_app.post(
        '/expense',
        headers=headers,
        json={'date': date, 'car_id': car['id'], 'category': 'insurance', 'amount': 5000},
    )


class TestPurchaseAndSaleFields:
    def test_default_to_null(self, test_app, headers):
        car = create_car(test_app, headers)
        for key in ['purchase_price', 'purchase_date', 'purchase_odometer', *SALE_FIELDS]:
            assert car[key] is None
        assert car['retired'] is False

    def test_purchase_round_trip(self, test_app, headers, car):
        loaded = test_app.get(f'/car/{car["id"]}', headers=headers).json()
        for key, value in PURCHASE.items():
            assert loaded[key] == value

    def test_sale_round_trip(self, test_app, headers):
        car = create_car(test_app, headers, **PURCHASE, **SALE)
        loaded = test_app.get(f'/car/{car["id"]}', headers=headers).json()
        for key, value in SALE.items():
            assert loaded[key] == value

    def test_fields_survive_list(self, test_app, headers, car):
        listed = test_app.get('/car', headers=headers).json()
        assert listed[0]['purchase_date'] == PURCHASE['purchase_date']

    @pytest.mark.parametrize('field', ['purchase_price', 'purchase_date', 'purchase_odometer'])
    def test_purchase_field_can_be_cleared(self, test_app, headers, car, field):
        response = put_car(test_app, headers, car, **{field: None})
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()[field] is None
        assert test_app.get(f'/car/{car["id"]}', headers=headers).json()[field] is None

    def test_clearing_one_field_keeps_the_others(self, test_app, headers, car):
        put_car(test_app, headers, car, purchase_price=None)
        loaded = test_app.get(f'/car/{car["id"]}', headers=headers).json()
        assert loaded['purchase_date'] == PURCHASE['purchase_date']
        assert loaded['purchase_odometer'] == PURCHASE['purchase_odometer']

    def test_partial_update_keeps_unsent_fields(self, test_app, headers, car):
        response = test_app.put(f'/car/{car["id"]}', headers=headers, json={'name': 'Renamed', 'battery_capacity': 50})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Renamed'
        assert response.json()['purchase_price'] == PURCHASE['purchase_price']


class TestRetiring:
    def test_retired_is_computed_from_sale_date(self, test_app, headers, car):
        response = put_car(test_app, headers, car, **SALE)
        assert response.status_code == status.HTTP_200_OK, response.content
        assert response.json()['retired'] is True

    def test_retired_is_not_stored_input(self, test_app, headers, car):
        response = put_car(test_app, headers, car, retired=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['retired'] is False

    def test_sale_date_before_purchase_date_is_400(self, test_app, headers, car):
        response = put_car(test_app, headers, car, sale_date='2022-04-30')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_date_on_purchase_date_is_allowed(self, test_app, headers, car):
        response = put_car(test_app, headers, car, sale_date=PURCHASE['purchase_date'])
        assert response.status_code == status.HTTP_200_OK

    def test_sale_date_before_purchase_date_on_create_is_400(self, test_app, headers):
        response = test_app.post(
            '/car',
            headers=headers,
            json={'name': 'Bad', 'battery_capacity': 50, 'purchase_date': '2024-01-02', 'sale_date': '2024-01-01'},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_odometer_below_latest_charge_is_400(self, test_app, headers, car, cpo):
        add_charge(test_app, headers, car, cpo, '2024-03-01T12:00:00Z', 5000)
        response = put_car(test_app, headers, car, sale_date='2024-06-30', sale_odometer=4999)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_sale_odometer_equal_to_latest_charge_is_allowed(self, test_app, headers, car, cpo):
        add_charge(test_app, headers, car, cpo, '2024-03-01T12:00:00Z', 5000)
        response = put_car(test_app, headers, car, sale_date='2024-06-30', sale_odometer=5000)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['sale_odometer'] == 5000

    def test_sale_odometer_defaults_to_current_odometer(self, test_app, headers, car, cpo):
        add_charge(test_app, headers, car, cpo, '2024-03-01T12:00:00Z', 5000)
        car = test_app.get(f'/car/{car["id"]}', headers=headers).json()
        response = put_car(test_app, headers, car, sale_date='2024-06-30')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['sale_odometer'] == 5000

    def test_sale_price_defaults_to_zero(self, test_app, headers, car):
        response = put_car(test_app, headers, car, sale_date='2024-06-30')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['sale_price'] == 0

    @pytest.mark.parametrize(
        'changes',
        [{'sale_price': 100}, {'sale_odometer': 100}, {'sale_price': 100, 'sale_odometer': 100}],
        ids=['price-only', 'odometer-only', 'price-and-odometer'],
    )
    def test_sale_fields_without_sale_date_is_400(self, test_app, headers, car, changes):
        response = put_car(test_app, headers, car, **changes)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'sale_date' in response.json()['detail']

    def test_sale_fields_without_sale_date_on_create_is_400(self, test_app, headers):
        response = test_app.post('/car', headers=headers, json={'name': 'Bad', 'battery_capacity': 50, 'sale_price': 1})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_failed_retire_leaves_car_untouched(self, test_app, headers, car):
        put_car(test_app, headers, car, sale_date='2022-04-30')
        assert test_app.get(f'/car/{car["id"]}', headers=headers).json()['retired'] is False

    def test_unretire_clears_all_sale_fields(self, test_app, headers, car):
        retired = put_car(test_app, headers, car, **SALE).json()
        response = put_car(test_app, headers, retired, sale_price=None, sale_date=None, sale_odometer=None)
        assert response.status_code == status.HTTP_200_OK, response.content
        loaded = test_app.get(f'/car/{car["id"]}', headers=headers).json()
        assert loaded['retired'] is False
        for key in SALE_FIELDS:
            assert loaded[key] is None

    def test_unretire_allows_new_entries_again(self, test_app, headers, car, cpo):
        retired = put_car(test_app, headers, car, **SALE).json()
        put_car(test_app, headers, retired, sale_price=None, sale_date=None, sale_odometer=None)
        assert add_expense(test_app, headers, car, '2024-12-01T12:00:00Z').status_code == status.HTTP_201_CREATED


class TestRetiredCarIsFrozen:
    @pytest.fixture
    def retired_car(self, test_app, headers, car, cpo):
        add_charge(test_app, headers, car, cpo, '2024-03-01T12:00:00Z', 5000)
        response = put_car(test_app, headers, car, sale_date='2024-06-30', sale_odometer=5000)
        assert response.status_code == status.HTTP_200_OK, response.content
        return response.json()

    def test_charge_after_sale_date_is_rejected(self, test_app, headers, retired_car, cpo):
        response = add_charge(test_app, headers, retired_car, cpo, '2024-07-01T00:00:00Z', 5100)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'car was retired on 2024-06-30' in response.json()['detail']

    @pytest.mark.parametrize('date', ['2024-06-01T12:00:00Z', '2024-06-30T23:59:00Z'])
    def test_charge_up_to_sale_date_is_accepted(self, test_app, headers, retired_car, cpo, date):
        response = add_charge(test_app, headers, retired_car, cpo, date, 5100)
        assert response.status_code == status.HTTP_201_CREATED, response.content

    def test_expense_after_sale_date_is_rejected(self, test_app, headers, retired_car):
        response = add_expense(test_app, headers, retired_car, '2024-07-01T00:00:00Z')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'car was retired on 2024-06-30' in response.json()['detail']

    @pytest.mark.parametrize('date', ['2024-03-15T12:00:00Z', '2024-06-30T23:59:00Z'])
    def test_expense_up_to_sale_date_is_accepted(self, test_app, headers, retired_car, date):
        assert add_expense(test_app, headers, retired_car, date).status_code == status.HTTP_201_CREATED

    def test_moving_expense_after_sale_date_is_rejected(self, test_app, headers, retired_car):
        expense = add_expense(test_app, headers, retired_car, '2024-05-01T12:00:00Z').json()
        response = test_app.put(
            f'/expense/{expense["id"]}',
            headers=headers,
            json={'date': '2024-08-01T12:00:00Z', 'car_id': retired_car['id'], 'category': 'tax', 'amount': 1},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_moving_charge_after_sale_date_is_rejected(self, test_app, headers, retired_car):
        charge = test_app.get('/charge', headers=headers, params={'car_id': retired_car['id']}).json()[0]
        payload = charge | {'date': '2024-08-01T12:00:00Z'}
        response = test_app.put(f'/charge/{charge["id"]}', headers=headers, json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_existing_entries_stay_deletable(self, test_app, headers, retired_car):
        expense = add_expense(test_app, headers, retired_car, '2024-05-01T12:00:00Z').json()
        assert test_app.delete(f'/expense/{expense["id"]}', headers=headers).status_code == 204


class TestDeleteCascade:
    def test_deleting_car_removes_charges_and_expenses(self, test_app, headers, car, cpo):
        add_charge(test_app, headers, car, cpo, '2024-03-01T12:00:00Z', 5000)
        expense = add_expense(test_app, headers, car, '2024-03-02T12:00:00Z').json()
        assert test_app.delete(f'/car/{car["id"]}', headers=headers).status_code == status.HTTP_204_NO_CONTENT
        assert test_app.get('/charge', headers=headers).json() == []
        assert test_app.get('/expense', headers=headers).json() == []
        assert test_app.get(f'/expense/{expense["id"]}', headers=headers).status_code == status.HTTP_404_NOT_FOUND

    def test_other_cars_are_untouched(self, test_app, headers, car, cpo):
        other_car = create_car(test_app, headers, name='Keeper')
        add_charge(test_app, headers, other_car, cpo, '2024-03-01T12:00:00Z', 100)
        kept_expense = add_expense(test_app, headers, other_car, '2024-03-02T12:00:00Z').json()
        add_expense(test_app, headers, car, '2024-03-02T12:00:00Z')
        test_app.delete(f'/car/{car["id"]}', headers=headers)
        assert len(test_app.get('/charge', headers=headers).json()) == 1
        assert [item['id'] for item in test_app.get('/expense', headers=headers).json()] == [kept_expense['id']]

    def test_foreign_delete_removes_nothing(self, test_app, headers, car):
        expense = add_expense(test_app, headers, car, '2024-03-02T12:00:00Z').json()
        other_headers = new_user_headers(test_app)
        assert test_app.delete(f'/car/{car["id"]}', headers=other_headers).status_code == status.HTTP_404_NOT_FOUND
        assert test_app.get(f'/expense/{expense["id"]}', headers=headers).status_code == status.HTTP_200_OK
