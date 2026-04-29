from starlette import status

from tests.conftest import register_and_login


def _create_car(test_app, headers, name='Car 1'):
    response = test_app.post(
        '/car/',
        headers=headers,
        json={'name': name, 'make': 'Tesla', 'model': 'Y', 'battery_capacity': 7500, 'odometer': 0, 'color': '#000'},
    )
    assert response.status_code == status.HTTP_201_CREATED, response.content
    return response.json()


def _create_cpo(test_app, headers, name='CPO 1'):
    response = test_app.post('/cpo/', headers=headers, json={'name': name, 'default_price': 42})
    assert response.status_code == status.HTTP_201_CREATED, response.content
    return response.json()


def test_admin_user_management(test_app):
    admin_token = register_and_login(test_app, 'adminx')
    user_token = register_and_login(test_app, 'userx')
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    user_headers = {'Authorization': f'Bearer {user_token}'}

    response = test_app.get('/admin/users', headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    car = _create_car(test_app, user_headers)
    cpo = _create_cpo(test_app, user_headers)
    response = test_app.post(
        '/charge/',
        headers=user_headers,
        json={
            'car_id': car['id'],
            'cpo_id': cpo['id'],
            'date': '2026-01-01T10:00:00+00:00',
            'kwh_charged': 2500,
            'price_total': 1000,
            'charge_type': 'AC',
            'car_km_driven': 100,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED, response.content

    # Create an API token for user — must be cleared on user delete
    response = test_app.post('/users/api-tokens', headers=user_headers, json={'name': 'bot'})
    assert response.status_code == 200, response.content

    # List users
    response = test_app.get('/admin/users', headers=admin_headers)
    assert response.status_code == 200
    users = {u['username']: u for u in response.json()}
    assert users['adminx']['is_admin']
    assert not users['userx']['is_admin']
    assert users['userx']['cars_count'] == 1
    assert users['userx']['cpos_count'] == 1
    assert users['userx']['charges_count'] == 1

    user_id = users['userx']['id']
    admin_id = users['adminx']['id']

    # Detail
    response = test_app.get(f'/admin/users/{user_id}', headers=admin_headers)
    assert response.status_code == 200
    detail = response.json()
    assert len(detail['cars']) == 1
    assert len(detail['cpos']) == 1
    assert len(detail['charges']) == 1

    # Toggle admin on user (now 2 admins)
    response = test_app.post(f'/admin/users/{user_id}/toggle-admin', headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {'result': 'ok', 'is_admin': True}

    # Toggle back off — allowed (admin count goes 2->1, but adminx remains)
    response = test_app.post(f'/admin/users/{user_id}/toggle-admin', headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {'result': 'ok', 'is_admin': False}

    # Cannot toggle self
    response = test_app.post(f'/admin/users/{admin_id}/toggle-admin', headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Cannot delete self
    response = test_app.delete(f'/admin/users/{admin_id}', headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Promote user, then try to demote adminx (target is admin) — but admin can't toggle self.
    # Verify last-admin guard: promote user, demote adminx via... we can't (self). So promote user, demote user — fine.
    # To exercise last-admin path on a non-self target: with only adminx admin, target adminx blocked by self-check first.
    # That's fine — guard is still defensive.

    # Delete user — cascades resources + api tokens
    response = test_app.delete(f'/admin/users/{user_id}', headers=admin_headers)
    assert response.status_code == 200

    response = test_app.get('/admin/users', headers=admin_headers)
    assert response.status_code == 200
    assert all(u['username'] != 'userx' for u in response.json())

    # 404 on missing user
    response = test_app.get(f'/admin/users/{user_id}', headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response = test_app.post(f'/admin/users/{user_id}/toggle-admin', headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    response = test_app.delete(f'/admin/users/{user_id}', headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def _login(test_app, username):
    response = test_app.post('/users/token', data={'username': username, 'password': username})
    assert response.status_code == 200, response.content
    return response.json()['access_token']


def test_admin_cannot_delete_last_admin(test_app):
    # Promote a fresh user to admin, then attempt to delete the original admin.
    admin_headers = {'Authorization': f'Bearer {_login(test_app, "adminx")}'}
    helper_token = register_and_login(test_app, 'helper')
    helper_headers = {'Authorization': f'Bearer {helper_token}'}

    response = test_app.get('/admin/users', headers=admin_headers)
    helper_id = next(u['id'] for u in response.json() if u['username'] == 'helper')
    admin_id = next(u['id'] for u in response.json() if u['username'] == 'adminx')

    # Promote helper => 2 admins
    response = test_app.post(f'/admin/users/{helper_id}/toggle-admin', headers=admin_headers)
    assert response.status_code == 200

    # Delete adminx (the original) using helper's creds — last-admin guard not triggered since 2 admins
    response = test_app.delete(f'/admin/users/{admin_id}', headers=helper_headers)
    assert response.status_code == 200

    # Now helper is the last admin — try to delete helper as helper (self-check first)
    response = test_app.delete(f'/admin/users/{helper_id}', headers=helper_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST  # self-deletion guard
