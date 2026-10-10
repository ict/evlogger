"""
Tests for GET /charge/stats
"""

import bson
from pymongo import MongoClient
from starlette import status

from app.core import config
from tests.conftest import charge_payload, create_car, create_cpo, new_user_headers


def _add(test_app, headers, car, cpo, date, odometer, **overrides):
    payload = {**charge_payload(car['id'], cpo['id'], date, odometer), **overrides}
    response = test_app.post('/charge', headers=headers, json=payload)
    assert response.status_code == status.HTTP_201_CREATED, response.content
    return response.json()


def test_stats_requires_auth(test_app):
    assert test_app.get('/charge/stats').status_code == status.HTTP_401_UNAUTHORIZED


def test_stats_empty(test_app):
    headers = new_user_headers(test_app)
    response = test_app.get('/charge/stats', headers=headers)
    assert response.status_code == status.HTTP_200_OK, response.content
    assert response.json() == {
        'from_date': None,
        'to_date': None,
        'total': {'count': 0, 'kwh_charged': 0, 'price_total': 0, 'charges_without_price': 0},
        'per_car': [],
    }


def test_stats_month_range_bounds(test_app):
    headers = new_user_headers(test_app)
    car, cpo = create_car(test_app, headers), create_cpo(test_app, headers)
    _add(test_app, headers, car, cpo, '2026-09-30T23:59:59Z', 100, price_total=1000)  # before
    _add(test_app, headers, car, cpo, '2026-10-01T00:00:00Z', 200, price_total=2000)  # on lower bound
    _add(test_app, headers, car, cpo, '2026-10-31T23:59:59Z', 300, price_total=3000)  # inside
    _add(test_app, headers, car, cpo, '2026-11-01T00:00:01Z', 400, price_total=4000)  # after

    params = {'from_date': '2026-10-01T00:00:00Z', 'to_date': '2026-10-31T23:59:59Z'}
    data = test_app.get('/charge/stats', headers=headers, params=params).json()
    assert data['total'] == {'count': 2, 'kwh_charged': 4000, 'price_total': 5000, 'charges_without_price': 0}

    all_time = test_app.get('/charge/stats', headers=headers).json()
    assert all_time['total']['count'] == 4
    assert all_time['total']['price_total'] == 10000


def test_stats_per_car_and_filter(test_app):
    headers = new_user_headers(test_app)
    car_a = create_car(test_app, headers, name='Alpha')
    car_b = create_car(test_app, headers, name='Beta')
    cpo = create_cpo(test_app, headers)
    _add(test_app, headers, car_a, cpo, '2026-10-01T10:00:00Z', 100, price_total=1000)
    _add(test_app, headers, car_a, cpo, '2026-10-02T10:00:00Z', 200, price_total=500, kwh_charged=1000)
    _add(test_app, headers, car_b, cpo, '2026-10-03T10:00:00Z', 100, price_total=700)

    data = test_app.get('/charge/stats', headers=headers).json()
    assert data['total'] == {'count': 3, 'kwh_charged': 5000, 'price_total': 2200, 'charges_without_price': 0}
    by_car = {c['car_id']: c for c in data['per_car']}
    assert by_car[car_a['id']] == {
        'car_id': car_a['id'],
        'car_name': 'Alpha',
        'count': 2,
        'kwh_charged': 3000,
        'price_total': 1500,
        'charges_without_price': 0,
    }
    assert by_car[car_b['id']]['count'] == 1
    assert by_car[car_b['id']]['price_total'] == 700

    only_b = test_app.get('/charge/stats', headers=headers, params={'car_id': car_b['id']}).json()
    assert [c['car_id'] for c in only_b['per_car']] == [car_b['id']]
    assert only_b['total']['count'] == 1


def test_stats_charge_without_price(test_app):
    headers = new_user_headers(test_app)
    car, cpo = create_car(test_app, headers), create_cpo(test_app, headers)
    _add(test_app, headers, car, cpo, '2026-10-01T10:00:00Z', 100, price_total=1000)
    charge = _add(test_app, headers, car, cpo, '2026-10-02T10:00:00Z', 200)  # priced from CPO default on create
    assert charge['price_total'] == 800  # 20 kWh * 40

    # legacy/imported charges can lack a price: remove it directly in the DB
    client = MongoClient(config.MONGODB_URL)
    client[config.DATABASE_NAME][config.COLLECTION_CHARGES].update_one(
        {'_id': bson.ObjectId(charge['id'])}, {'$set': {'price_total': None}}
    )
    client.close()

    data = test_app.get('/charge/stats', headers=headers).json()
    assert data['total'] == {'count': 2, 'kwh_charged': 4000, 'price_total': 1000, 'charges_without_price': 1}
    assert data['per_car'][0]['charges_without_price'] == 1


def test_stats_isolated_between_users(test_app):
    mine, other = new_user_headers(test_app), new_user_headers(test_app)
    other_car, other_cpo = create_car(test_app, other), create_cpo(test_app, other)
    _add(test_app, other, other_car, other_cpo, '2026-10-01T10:00:00Z', 100, price_total=1000)

    data = test_app.get('/charge/stats', headers=mine).json()
    assert data['total']['count'] == 0
    assert data['per_car'] == []
    assert test_app.get('/charge/stats', headers=other).json()['total']['count'] == 1
