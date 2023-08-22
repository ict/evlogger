from starlette import status

from app.models.charging import Car
from tests.conftest import test_app


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


def test_unauthenticated_list(test_app):
    response = test_app.get("/car")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticated_create_list(test_app):
    token = register_and_login(test_app, 'admin')
    # get cars
    response = test_app.get("/car", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # create car
    carmodel = Car(name="Admin Car", make="Tesla", model="Model S", color='#ffffff')
    response = test_app.post(
        "/car",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": carmodel.name, "make": carmodel.make, "model": carmodel.model, "color": '#ffffff'},
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['name'] == carmodel.name
    assert response_data['make'] == carmodel.make
    assert response_data['model'] == carmodel.model
    assert response_data['color'] == str(carmodel.color)

    car_id = response_data['id']
    assert car_id

    # get cars
    response = test_app.get("/car", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert len(response_data) == 1

    response = test_app.get(f"/car/{car_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['name'] == carmodel.name
    assert response_data['make'] == carmodel.make
    assert response_data['model'] == carmodel.model
    assert response_data['color'] == str(carmodel.color)

    # get car with another account
    token2 = register_and_login(test_app, 'user')
    response = test_app.get("/car", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # check for IDOR
    response = test_app.get(f"/car/{car_id}", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 404, response.content
