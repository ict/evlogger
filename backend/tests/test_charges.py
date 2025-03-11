"""
Test for the charging operations
"""

# ruff: noqa: S101 D103
from datetime import UTC, datetime, timedelta
from pathlib import Path

import dateparser
from starlette import status

from app.models.charging import CPO, Car, CarInDb, ChargeInDb, ChargeSubmission, ChargeTypeEnum, CPOInDb
from tests.conftest import register_and_login

TEST_DATA_DIR = Path(__file__).parent.parent / 'test_data'


def test_unauthenticated_list(test_app):
    response = test_app.get('/charge')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_editing_old_charge(test_app):
    token = register_and_login(test_app, 'editor')

    # create car and cpo for testing
    car_model = Car(name='Editor Car', make='Hyundai', model='Kona', color='#ff1295', battery_capacity=50)
    response = test_app.post(
        '/car',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': car_model.name,
            'make': car_model.make,
            'model': car_model.model,
            'color': '#ff1295',
            'battery_capacity': car_model.battery_capacity,
        },
    )
    assert response.status_code == 201, response.content
    charges = response.json()
    my_car = CarInDb(**charges)

    cpo_model = CPO(name='Infra', default_price=49)
    response = test_app.post('/cpo', headers={'Authorization': f'Bearer {token}'}, json=cpo_model.model_dump())
    assert response.status_code == 201, response.content
    charges = response.json()
    my_cpo = CPOInDb(**charges)

    # create different charges at different times
    dates = [
        datetime.now(UTC) - timedelta(days=90) + timedelta(hours=1),
        datetime.now(UTC) - timedelta(days=60) + timedelta(hours=1),
        datetime.now(UTC) - timedelta(days=30) + timedelta(hours=1),
        datetime.now(UTC) - timedelta(days=1) + timedelta(hours=1),
    ]
    for i, date in enumerate(dates):
        charge_model = ChargeSubmission(
            date=date,
            car_id=my_car.id,
            car_soc_after=90,
            car_odometer=200 * (i + 1),
            cpo_id=my_cpo.id,
            kwh_charged=1500,
            charge_type=ChargeTypeEnum.ac,
        )
        response = test_app.post(
            '/charge', headers={'Authorization': f'Bearer {token}'}, json=charge_model.model_dump(mode='json')
        )
        assert response.status_code == 201, response.content

    # get all charges
    response = test_app.get('/charge', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    charges = response.json()
    assert len(charges) == len(dates)

    # Edit the price of the newest charge
    charge_model = ChargeSubmission(
        date=dates[0],
        car_id=my_car.id,
        car_odometer=200,
        cpo_id=my_cpo.id,
        kwh_charged=1500,
        charge_type=ChargeTypeEnum.ac,
        price_total=1500,
    )
    response = test_app.put(
        f'/charge/{charges[-1]["id"]}',
        headers={'Authorization': f'Bearer {token}'},
        json=charge_model.model_dump(mode='json'),
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['price_total'] == 1500
    assert response_data['price_per_kwh'] == 100

    # Try to change the km of the oldest charge to an invalid value
    charge_model.car_odometer = 5000
    response = test_app.put(
        f'/charge/{charges[-1]["id"]}',
        headers={'Authorization': f'Bearer {token}'},
        json=charge_model.model_dump(mode='json'),
    )
    assert response.status_code == 422, response.content

    # Now do something valid
    charge_model.car_odometer = 100
    response = test_app.put(
        f'/charge/{charges[-1]["id"]}',
        headers={'Authorization': f'Bearer {token}'},
        json=charge_model.model_dump(mode='json'),
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['car_odometer'] == 100
    # Check if the second charge has been updated as well
    response = test_app.get(f'/charge/{charges[-2]["id"]}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['car_odometer'] == 400  # Still the same


def test_multiple_charges_and_list(test_app):
    token = register_and_login(test_app, 'myuser')

    # create car and cpo for testing
    car_model = Car(name='Admin Car', make='Tesla', model='Model S', color='#ffffff', battery_capacity=90)
    response = test_app.post(
        '/car',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': car_model.name,
            'make': car_model.make,
            'model': car_model.model,
            'color': '#ffffff',
            'battery_capacity': car_model.battery_capacity,
        },
    )
    assert response.status_code == 201, response.content
    response_data = response.json()
    my_car = CarInDb(**response_data)

    cpo_model = CPO(name='SWM', default_price=35)
    response = test_app.post('/cpo', headers={'Authorization': f'Bearer {token}'}, json=cpo_model.model_dump())
    assert response.status_code == 201, response.content
    response_data = response.json()
    my_cpo = CPOInDb(**response_data)

    # create different charges at different times
    dates = [
        datetime.now(UTC) - timedelta(days=365) + timedelta(hours=1),
        datetime.now(UTC) - timedelta(days=30) + timedelta(hours=1),
        datetime.now(UTC) - timedelta(days=9) + timedelta(hours=1),
        datetime.now(UTC) - timedelta(days=1) + timedelta(hours=1),
        datetime.now(UTC),
    ]
    for i, date in enumerate(dates):
        charge_model = ChargeSubmission(
            date=date,
            car_id=my_car.id,
            car_soc_after=90,
            car_odometer=200 * (i + 1),
            cpo_id=my_cpo.id,
            kwh_charged=1500,
            charge_type=ChargeTypeEnum.ac,
        )
        response = test_app.post(
            '/charge', headers={'Authorization': f'Bearer {token}'}, json=charge_model.model_dump(mode='json')
        )
        assert response.status_code == 201, response.content

    # get all charges
    response = test_app.get('/charge', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert len(response_data) == len(dates)
    expected_km = 1000
    for charge in response_data:
        assert charge['car_odometer'] == expected_km
        expected_km -= 200

    # check if the global car odometer is updated
    response = test_app.get(f'/car/{my_car.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    assert response.json()['odometer'] == 1000

    # check if inserting a charge with an older date than the last one fails
    charge_model = ChargeSubmission(
        date=datetime.now(UTC) - timedelta(days=80),
        car_id=my_car.id,
        car_soc_after=90,
        car_odometer=137,
        cpo_id=my_cpo.id,
        kwh_charged=1500,
        charge_type=ChargeTypeEnum.ac,
    )
    response = test_app.post(
        '/charge', headers={'Authorization': f'Bearer {token}'}, json=charge_model.model_dump(mode='json')
    )
    assert response.status_code == 422, response.content

    # check if charges are sorted by date, newest first (pop from the end)
    dates2 = dates[:]
    for charge in response_data:
        assert charge['date'][:19] == dates2.pop().isoformat()[:19]  # skip subsecond precision

    # get charges from different timespans
    spans = {
        '1h': 1,  # now
        '24h': 2,  # now + 24h
        '7d': 2,  # nothing additional
        '10d': 3,  # +9 d
        '30d': 4,  # +30 d
        '2y': 5,  # +365 d
    }
    for span, count in spans.items():
        response = test_app.get(f'/charge?timespan={span}', headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200, response.content
        response_data = response.json()
        assert len(response_data) == count, response_data

    # get charges from different timespans with from_date
    response = test_app.get(
        f'/charge?from_date={dates[0].isoformat()[:19]}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert len(response_data) == len(dates), response_data

    response = test_app.get(
        f'/charge?from_date={dates[0].isoformat()[:19]}&to_date={(dates[1] + timedelta(minutes=1)).isoformat()[:19]}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert len(response_data) == 2, response_data

    # Check if we can submit a charge without car_soc_after
    charge_model = ChargeSubmission(
        date=datetime.now(UTC),
        car_id=my_car.id,
        car_odometer=137,
        cpo_id=my_cpo.id,
        kwh_charged=1500,
        charge_type=ChargeTypeEnum.ac,
    )
    model_dump = charge_model.model_dump(mode='json')
    del model_dump['car_soc_after']
    response = test_app.post('/charge', headers={'Authorization': f'Bearer {token}'}, json=model_dump)
    assert response.status_code == 201, response.content


def test_authenticated_crud(test_app):
    token = register_and_login(test_app, 'admin')

    # create a car and cpo for testing
    car_model = Car(name='Admin Car', make='Tesla', model='Model S', color='#ffffff', battery_capacity=90)
    response = test_app.post(
        '/car',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': car_model.name,
            'make': car_model.make,
            'model': car_model.model,
            'color': '#ffffff',
            'battery_capacity': car_model.battery_capacity,
        },
    )
    assert response.status_code == 201, response.content
    response_data = response.json()
    my_car = CarInDb(**response_data)

    cpo_model = CPO(name='SWM', default_price=35)
    response = test_app.post('/cpo', headers={'Authorization': f'Bearer {token}'}, json=cpo_model.model_dump())
    assert response.status_code == 201, response.content
    response_data = response.json()
    my_cpo = CPOInDb(**response_data)

    # get charges
    response = test_app.get('/charge', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # create charge
    charge_model = ChargeSubmission(
        date=datetime(2020, 1, 1, 14, 00, tzinfo=UTC),
        car_id=my_car.id,
        cpo_id=my_cpo.id,
        car_odometer=200,
        car_soc_after=90,
        kwh_charged=1500,
        charge_type=ChargeTypeEnum.ac,
    )
    response = test_app.post(
        '/charge',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'date': charge_model.date.isoformat(),
            'car_id': charge_model.car_id,
            'cpo_id': charge_model.cpo_id,
            'car_odometer': charge_model.car_odometer,
            'car_soc_after': charge_model.car_soc_after,
            'kwh_charged': charge_model.kwh_charged,
            'charge_type': charge_model.charge_type,
        },  # cannot use model_dump() here because of computed fields that cause errors on unfilled model
    )
    assert response.status_code == 201, response.content
    response_data = response.json()
    expected_price = int(round(charge_model.kwh_charged / 100 * my_cpo.default_price))
    assert dateparser.parse(response_data['date']) == charge_model.date
    assert response_data['car_id'] == charge_model.car_id
    assert response_data['cpo_id'] == charge_model.cpo_id
    assert response_data['car_odometer'] == charge_model.car_odometer
    assert response_data['car_soc_after'] == charge_model.car_soc_after
    assert response_data['kwh_charged'] == charge_model.kwh_charged
    assert response_data['charge_type'] == charge_model.charge_type
    assert response_data['price_total'] == expected_price
    assert response_data['price_per_kwh'] == int(round(expected_price / (charge_model.kwh_charged / 100)))
    assert response_data['car_name'] == my_car.name
    assert response_data['cpo_name'] == my_cpo.name

    my_charge = ChargeInDb(**response_data)

    # try with nonexistent car
    response = test_app.post(
        '/charge',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'date': charge_model.date.isoformat(),
            'car_id': '123456789012345678901234',
            'cpo_id': charge_model.cpo_id,
            'car_odometer': charge_model.car_odometer,
            'kwh_charged': charge_model.kwh_charged,
            'charge_type': charge_model.charge_type,
        },
    )
    assert response.status_code == 422, response.content

    # try with nonexistent cpo
    response = test_app.post(
        '/charge',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'date': charge_model.date.isoformat(),
            'car_id': charge_model.car_id,
            'cpo_id': '123456789012345678901234',
            'car_odometer': charge_model.car_odometer,
            'kwh_charged': charge_model.kwh_charged,
            'charge_type': charge_model.charge_type,
        },
    )
    assert response.status_code == 422, response.content

    # try with someone else's car
    token2 = register_and_login(test_app, 'user')
    response = test_app.post(
        '/car',
        headers={'Authorization': f'Bearer {token2}'},
        json={'name': 'User Car', 'make': 'Fiat', 'model': 'Multipla', 'color': 'blue', 'battery_capacity': 44},
    )
    assert response.status_code == 201, response.content
    response_data = response.json()
    other_car = CarInDb(**response_data)

    response = test_app.post(
        '/charge',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'date': charge_model.date.isoformat(),
            'car_id': other_car.id,
            'cpo_id': charge_model.cpo_id,
            'car_odometer': charge_model.car_odometer,
            'car_soc_after': charge_model.car_soc_after,
            'kwh_charged': charge_model.kwh_charged,
            'charge_type': charge_model.charge_type,
        },
    )
    assert response.status_code == 422, response.content

    # get charges
    response = test_app.get('/charge', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]['id'] == my_charge.id

    # get charge by id
    response = test_app.get(f'/charge/{my_charge.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    also_my_charge = ChargeInDb(**response_data)
    assert also_my_charge == my_charge

    # get one that does not exist
    response = test_app.get('/charge/123456789012345678901234', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404, response.content

    # get charge with another account
    response = test_app.get('/charge', headers={'Authorization': f'Bearer {token2}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # check for IDOR
    response = test_app.get(f'/charge/{my_charge.id}', headers={'Authorization': f'Bearer {token2}'})
    assert response.status_code == 404, response.content

    # update charge with a fixed price
    charge_model.price_total = 1000
    response = test_app.put(
        f'/charge/{my_charge.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'date': charge_model.date.isoformat(),
            'car_id': charge_model.car_id,
            'cpo_id': charge_model.cpo_id,
            'car_odometer': charge_model.car_odometer,
            'car_soc_after': charge_model.car_soc_after,
            'kwh_charged': charge_model.kwh_charged,
            'charge_type': charge_model.charge_type,
            'price_total': charge_model.price_total,
        },
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['price_total'] == charge_model.price_total
    assert response_data['price_per_kwh'] == int(round(charge_model.price_total / (charge_model.kwh_charged / 100)))

    # check this has also been written
    response = test_app.get(f'/charge/{my_charge.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['price_total'] == charge_model.price_total
    assert response_data['price_per_kwh'] == int(round(charge_model.price_total / (charge_model.kwh_charged / 100)))

    # try deleting with another account
    response = test_app.delete(f'/charge/{my_charge.id}', headers={'Authorization': f'Bearer {token2}'})
    assert response.status_code == 404, response.content

    # try changing with another account
    response = test_app.put(
        f'/charge/{my_charge.id}',
        headers={'Authorization': f'Bearer {token2}'},
        json={
            'date': charge_model.date.isoformat(),
            'car_id': charge_model.car_id,
            'cpo_id': charge_model.cpo_id,
            'car_odometer': charge_model.car_odometer,
            'car_soc_after': charge_model.car_soc_after,
            'kwh_charged': charge_model.kwh_charged,
            'charge_type': charge_model.charge_type,
            'price_total': 9001,
        },
    )
    assert response.status_code == 404, response.content

    # delete the charge
    response = test_app.delete(f'/charge/{my_charge.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 204, response.content

    # check it is deleted from the listing
    response = test_app.get('/charge', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # check if direct access is no longer possible
    response = test_app.get(f'/charge/{my_charge.id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404, response.content


def test_csv_import(test_app):
    token = register_and_login(test_app, 'importer')

    # Create a car
    car_model = Car(name='Import Car', make='Tesla', model='Model S', color='#ffffff', battery_capacity=90)
    response = test_app.post(
        '/car', headers={'Authorization': f'Bearer {token}'}, json=car_model.model_dump(mode='json')
    )
    assert response.status_code == 201, response.content
    car_id = response.json()['id']

    # Push the CSV
    with TEST_DATA_DIR.joinpath('e208.csv').open('rb') as f:
        response = test_app.post(
            '/charge/csv_import',
            headers={'Authorization': f'Bearer {token}'},
            files={'csv_file': f},
            params={'car_id': car_id},
        )

    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['result'] == 'completed'
    messages = response_data['message'].split('\n')
    assert len(messages) > 20
