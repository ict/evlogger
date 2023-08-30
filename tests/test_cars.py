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


def test_authenticated_crud(test_app):
    token = register_and_login(test_app, 'admin')
    # get cars
    response = test_app.get("/car", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # create car
    carmodel = Car(name="Admin Car", make="Tesla", model="Model S", color='#ffffff', battery_capacity=90)
    response = test_app.post(
        "/car",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": carmodel.name,
            "make": carmodel.make,
            "model": carmodel.model,
            "color": '#ffffff',
            "battery_capacity": carmodel.battery_capacity,
        },
    )
    assert response.status_code == 201, response.content
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

    # update car
    carmodel.name = "Admin Car 2"
    carmodel.color = '#000000'
    response = test_app.put(
        f"/car/{car_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": carmodel.name,
            "make": carmodel.make,
            "model": carmodel.model,
            "color": '#000000',
            "battery_capacity": carmodel.battery_capacity,
        },
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['name'] == carmodel.name
    assert response_data['color'] == str(carmodel.color) or response_data['color'] == 'black'

    # make sure it's also saved
    response = test_app.get(f"/car/{car_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['name'] == carmodel.name
    assert response_data['color'] == str(carmodel.color) or response_data['color'] == 'black'

    # try deleting with another account
    response = test_app.delete(f"/car/{car_id}", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 404, response.content

    # try changing with another account
    response = test_app.put(
        f"/car/{car_id}",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "name": "Now my car",
            "make": carmodel.make,
            "model": carmodel.model,
            "color": '#000000',
            "battery_capacity": carmodel.battery_capacity,
        },
    )
    assert response.status_code == 404, response.content

    # delete car
    response = test_app.delete(f"/car/{car_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204, response.content

    # check it is deleted from the listing
    response = test_app.get("/car", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []
