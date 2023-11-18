from starlette import status

from app.models.charging import CPO
from tests.conftest import register_and_login


def test_unauthenticated_list(test_app):
    response = test_app.get('/cpo')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticated_crud(test_app):
    token = register_and_login(test_app, 'admin')
    # get cpos
    response = test_app.get('/cpo', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # create cpo
    cpomodel = CPO(name='SWM', default_price=35)
    response = test_app.post('/cpo', headers={'Authorization': f'Bearer {token}'}, json=cpomodel.model_dump())
    assert response.status_code == 201, response.content
    response_data = response.json()
    assert response_data['name'] == cpomodel.name
    assert response_data['default_price'] == cpomodel.default_price

    cpo_id = response_data['id']
    assert cpo_id

    # get cpos
    response = test_app.get('/cpo', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert len(response_data) == 1

    # get cpo by id
    response = test_app.get(f'/cpo/{cpo_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['name'] == cpomodel.name
    assert response_data['default_price'] == cpomodel.default_price

    # get one that does not exist
    response = test_app.get('/cpo/123456789012345678901234', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404, response.content

    # get cpo with another account
    token2 = register_and_login(test_app, 'user')
    response = test_app.get('/cpo', headers={'Authorization': f'Bearer {token2}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []

    # check for IDOR
    response = test_app.get(f'/cpo/{cpo_id}', headers={'Authorization': f'Bearer {token2}'})
    assert response.status_code == 404, response.content

    # update cpo
    cpomodel.name = 'N-Ergie'
    response = test_app.put(f'/cpo/{cpo_id}', headers={'Authorization': f'Bearer {token}'}, json=cpomodel.model_dump())
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['name'] == cpomodel.name
    assert response_data['default_price'] == cpomodel.default_price

    # make sure it's also saved
    response = test_app.get(f'/cpo/{cpo_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['name'] == cpomodel.name
    assert response_data['default_price'] == cpomodel.default_price

    # try deleting with another account
    response = test_app.delete(f'/cpo/{cpo_id}', headers={'Authorization': f'Bearer {token2}'})
    assert response.status_code == 404, response.content

    # try changing with another account
    response = test_app.put(
        f'/cpo/{cpo_id}',
        headers={'Authorization': f'Bearer {token2}'},
        json={'name': 'Now my cpo', 'default_price': 9001},
    )
    assert response.status_code == 404, response.content

    # delete cpo
    response = test_app.delete(f'/cpo/{cpo_id}', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 204, response.content

    # check it is deleted from the listing
    response = test_app.get('/cpo', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data == []
