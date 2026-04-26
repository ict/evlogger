from starlette import status

from tests.conftest import register_and_login


def test_register_users(test_app):
    response = test_app.post(
        '/users/register', json={'username': 'admin', 'email': 'admin@koala.de', 'password': 'admin'}
    )
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['username'] == 'admin'
    assert response_data['email'] == 'admin@koala.de'
    assert response_data['is_admin']

    response = test_app.post('/users/register', json={'username': 'user', 'email': 'user@koala.de', 'password': 'user'})
    assert response.status_code == 200, response.content
    response_data = response.json()
    assert response_data['username'] == 'user'
    assert response_data['email'] == 'user@koala.de'
    assert not response_data['is_admin']

    response = test_app.post(
        '/users/register', json={'username': 'user', 'email': 'user2@koala.de', 'password': 'user'}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, 'Same username should reject registration'

    response = test_app.post(
        '/users/register', json={'username': 'user2', 'email': 'user@koala.de', 'password': 'user'}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, 'Same email should reject registration'


def test_api_tokens(test_app):
    jwt_token = register_and_login(test_app, 'tokenuser')
    auth = {'Authorization': f'Bearer {jwt_token}'}

    response = test_app.post('/users/api-tokens', headers=auth, json={'name': 'CI bot'})
    assert response.status_code == 200, response.content
    created = response.json()
    raw_token = created['token']
    token_id = created['id']
    assert raw_token.startswith('clk_')
    assert created['preview'] and 'token' not in created['preview']

    response = test_app.get('/users/api-tokens', headers=auth)
    assert response.status_code == 200
    listed = response.json()
    assert len(listed) == 1
    assert 'token' not in listed[0]
    assert listed[0]['name'] == 'CI bot'

    response = test_app.get('/users/me', headers={'Authorization': f'Bearer {raw_token}'})
    assert response.status_code == 200, response.content
    assert response.json()['username'] == 'tokenuser'

    response = test_app.get('/users/me', headers={'Authorization': 'Bearer clk_invalidtoken'})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = test_app.delete(f'/users/api-tokens/{token_id}', headers=auth)
    assert response.status_code == 200

    response = test_app.get('/users/me', headers={'Authorization': f'Bearer {raw_token}'})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
