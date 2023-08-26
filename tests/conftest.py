import pytest
from pymongo_inmemory import MongoClient
from starlette.testclient import TestClient

from app.core import config
from app.main import app


@pytest.fixture(scope="module")
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
    response = test_app.post("/users/register", json={"username": username, "password": username})
    assert response.status_code == 200, response.content

    # get auth token
    response = test_app.post("/users/token", data={"username": username, "password": username})
    assert response.status_code == 200, response.content
    response_data = response.json()
    token = response_data['access_token']
    assert token
    return token
