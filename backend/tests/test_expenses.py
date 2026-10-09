"""
Tests for the expense endpoints
"""

import pytest
from starlette import status

from tests.conftest import create_car, new_user_headers


def expense_payload(car_id: str, **overrides) -> dict:
    return {'date': '2024-03-01T12:00:00Z', 'car_id': car_id, 'category': 'tires', 'amount': 45000, **overrides}


def create_expense(test_app, headers: dict, car_id: str, **overrides) -> dict:
    response = test_app.post('/expense', headers=headers, json=expense_payload(car_id, **overrides))
    assert response.status_code == status.HTTP_201_CREATED, response.content
    return response.json()


@pytest.fixture
def headers(test_app):
    return new_user_headers(test_app)


@pytest.fixture
def car(test_app, headers):
    return create_car(test_app, headers, name='Expense Car')


def test_unauthenticated_list(test_app):
    response = test_app.get('/expense')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_returns_expense(test_app, headers, car):
    expense = create_expense(test_app, headers, car['id'], note='Winter set')
    assert expense['id']
    assert expense['category'] == 'tires'
    assert expense['amount'] == 45000
    assert expense['note'] == 'Winter set'


def test_create_denormalizes_car_name(test_app, headers, car):
    expense = create_expense(test_app, headers, car['id'])
    assert expense['car_name'] == 'Expense Car'


def test_get_by_id(test_app, headers, car):
    expense = create_expense(test_app, headers, car['id'])
    response = test_app.get(f'/expense/{expense["id"]}', headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expense


def test_get_missing_is_404(test_app, headers):
    response = test_app.get('/expense/64b7f0c2a1b2c3d4e5f60718', headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update(test_app, headers, car):
    expense = create_expense(test_app, headers, car['id'])
    response = test_app.put(
        f'/expense/{expense["id"]}', headers=headers, json=expense_payload(car['id'], category='tax', amount=9900)
    )
    assert response.status_code == status.HTTP_200_OK, response.content
    assert response.json()['category'] == 'tax'
    assert response.json()['amount'] == 9900
    assert test_app.get(f'/expense/{expense["id"]}', headers=headers).json()['amount'] == 9900


def test_update_missing_is_404(test_app, headers, car):
    response = test_app.put('/expense/64b7f0c2a1b2c3d4e5f60718', headers=headers, json=expense_payload(car['id']))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete(test_app, headers, car):
    expense = create_expense(test_app, headers, car['id'])
    response = test_app.delete(f'/expense/{expense["id"]}', headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert test_app.get(f'/expense/{expense["id"]}', headers=headers).status_code == status.HTTP_404_NOT_FOUND


def test_delete_missing_is_404(test_app, headers):
    response = test_app.delete('/expense/64b7f0c2a1b2c3d4e5f60718', headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize('category', ['food', '', 'Tires'])
def test_invalid_category_is_422(test_app, headers, car, category):
    response = test_app.post('/expense', headers=headers, json=expense_payload(car['id'], category=category))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize('amount', [0, -1, -45000])
def test_non_positive_amount_is_422(test_app, headers, car, amount):
    response = test_app.post('/expense', headers=headers, json=expense_payload(car['id'], amount=amount))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize('car_id', ['not-an-id', '64b7f0c2a1b2c3d4e5f60718'])
def test_unknown_car_is_400(test_app, headers, car_id):
    response = test_app.post('/expense', headers=headers, json=expense_payload(car_id))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestOwnerIsolation:
    @pytest.fixture
    def other_headers(self, test_app):
        return new_user_headers(test_app)

    def test_list_does_not_leak(self, test_app, headers, car, other_headers):
        create_expense(test_app, headers, car['id'])
        response = test_app.get('/expense', headers=other_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_is_404(self, test_app, headers, car, other_headers):
        expense = create_expense(test_app, headers, car['id'])
        response = test_app.get(f'/expense/{expense["id"]}', headers=other_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_is_404_and_unchanged(self, test_app, headers, car, other_headers):
        expense = create_expense(test_app, headers, car['id'])
        response = test_app.put(
            f'/expense/{expense["id"]}', headers=other_headers, json=expense_payload(car['id'], amount=1)
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert test_app.get(f'/expense/{expense["id"]}', headers=headers).json()['amount'] == 45000

    def test_delete_is_404_and_kept(self, test_app, headers, car, other_headers):
        expense = create_expense(test_app, headers, car['id'])
        response = test_app.delete(f'/expense/{expense["id"]}', headers=other_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert test_app.get(f'/expense/{expense["id"]}', headers=headers).status_code == status.HTTP_200_OK

    def test_cannot_create_on_foreign_car(self, test_app, car, other_headers):
        response = test_app.post('/expense', headers=other_headers, json=expense_payload(car['id']))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_move_expense_to_foreign_car(self, test_app, headers, car, other_headers):
        other_car = create_car(test_app, other_headers)
        expense = create_expense(test_app, headers, car['id'])
        response = test_app.put(f'/expense/{expense["id"]}', headers=headers, json=expense_payload(other_car['id']))
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestListFilters:
    @pytest.fixture
    def populated(self, test_app, headers, car):
        second_car = create_car(test_app, headers, name='Second Car')
        return {
            'car': car,
            'second_car': second_car,
            'jan_tires': create_expense(test_app, headers, car['id'], date='2024-01-10T10:00:00Z'),
            'feb_tax': create_expense(test_app, headers, car['id'], date='2024-02-10T10:00:00Z', category='tax'),
            'mar_tires': create_expense(test_app, headers, car['id'], date='2024-03-10T10:00:00Z'),
            'other_car': create_expense(test_app, headers, second_car['id'], date='2024-02-20T10:00:00Z'),
        }

    def ids(self, test_app, headers, **params) -> list[str]:
        response = test_app.get('/expense', headers=headers, params=params)
        assert response.status_code == status.HTTP_200_OK, response.content
        return [item['id'] for item in response.json()]

    def test_sorted_by_date_descending(self, test_app, headers, populated):
        assert self.ids(test_app, headers) == [
            populated[key]['id'] for key in ('mar_tires', 'other_car', 'feb_tax', 'jan_tires')
        ]

    def test_filter_by_car(self, test_app, headers, populated):
        assert self.ids(test_app, headers, car_id=populated['second_car']['id']) == [populated['other_car']['id']]

    def test_filter_by_category(self, test_app, headers, populated):
        assert self.ids(test_app, headers, category='tax') == [populated['feb_tax']['id']]

    def test_filter_by_date_range(self, test_app, headers, populated):
        ids = self.ids(test_app, headers, from_date='2024-02-01T00:00:00Z', to_date='2024-02-28T00:00:00Z')
        assert ids == [populated['other_car']['id'], populated['feb_tax']['id']]

    def test_filters_combine(self, test_app, headers, populated):
        ids = self.ids(
            test_app, headers, car_id=populated['car']['id'], category='tires', from_date='2024-02-01T00:00:00Z'
        )
        assert ids == [populated['mar_tires']['id']]

    def test_invalid_category_filter_is_422(self, test_app, headers):
        response = test_app.get('/expense', headers=headers, params={'category': 'nope'})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_limit_and_offset(self, test_app, headers, populated):
        assert self.ids(test_app, headers, limit=2, offset=1) == [
            populated[key]['id'] for key in ('other_car', 'feb_tax')
        ]
