import uuid

import pytest
from pymongo_inmemory import MongoClient
from starlette.testclient import TestClient

from app.core import config
from app.main import app


@pytest.fixture(scope='module')
def test_app():
    """
    This will setup a test client, but will NOT call the startup and shutdown events,
    so the database connection will not be established.
    We can use this to mock the database with pymongo-inmemory.
    """
    mock = MongoClient()
    client = TestClient(app)
    config.MONGODB_URL = f'mongodb://{mock.HOST}:{mock.PORT}/chargelogger'
    with client as c:
        # Trigger startup event that should connect to the database
        yield c
    mock.close()


def register_and_login(test_app, username):
    # register the user
    response = test_app.post('/users/register', json={'username': username, 'password': username})
    assert response.status_code == 200, response.content

    # get auth token
    response = test_app.post('/users/token', data={'username': username, 'password': username})
    assert response.status_code == 200, response.content
    response_data = response.json()
    token = response_data['access_token']
    assert token
    return token


def new_user_headers(test_app) -> dict:
    """Register a fresh user with a unique name and return its auth headers."""
    token = register_and_login(test_app, f'user-{uuid.uuid4().hex[:12]}')
    return {'Authorization': f'Bearer {token}'}


def create_car(test_app, headers: dict, **overrides) -> dict:
    payload = {'name': 'Test Car', 'battery_capacity': 50, **overrides}
    response = test_app.post('/car', headers=headers, json=payload)
    assert response.status_code == 201, response.content
    return response.json()


def create_cpo(test_app, headers: dict) -> dict:
    response = test_app.post('/cpo', headers=headers, json={'name': 'Test CPO', 'default_price': 40})
    assert response.status_code == 201, response.content
    return response.json()


def charge_payload(car_id: str, cpo_id: str, date: str, odometer: int) -> dict:
    return {
        'date': date,
        'car_id': car_id,
        'car_odometer': odometer,
        'kwh_charged': 2000,
        'cpo_id': cpo_id,
        'charge_type': 'AC',
    }
