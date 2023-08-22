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
