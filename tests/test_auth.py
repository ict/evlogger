from starlette import status


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
