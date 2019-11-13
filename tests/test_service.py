from .utils import register, login, logout, get_json_content

def test_get_no_auth(client):
    """ Returns 418 when accessing GET requests while not authenticated. """
    endpoints = ['/me', '/users', '/logout']
    for endpoint in endpoints:
        resp = client.get(endpoint)
        assert '418' in resp.status

def test_user_handling(client):
    """ Tests user registration and logging """
    resp = client.post('/register', data=dict(
        username='test',
        password1='test1',
        password2='test2',
        email='test@test.com'
    ))

    assert '400' in resp.status, 'Should fail to register if passwords do not match'

    resp = register(client, 'test', 'test1', 'wrongemail')

    assert '400' in resp.status, "Should fail to register with invalid email address."

    resp = register(client, 'test', 'test1', 'test@test.com')

    assert '201' in resp.status, "Should successfully register a new user"


    resp = login(client, 'test', 'test1')

    assert '200' in resp.status, "Should successfully login a user"

    resp = client.get('/me')

    assert '200' in resp.status, "Should successfully get logged user's info"

    data = get_json_content(resp)

    assert data['username'] == 'test', 'User data should match'
    assert data['role_id'] == 2, 'User data should match'
    assert data['email'] == 'test@test.com', 'User data should match'
    assert data['language'] == 'EN', 'User data should match'

    resp = logout(client)

    assert '200' in resp.status, "Should successfully logout a user"

    resp = login(client, 'test1', 'test')

    assert '404' in resp.status, "Should fail upon passing invalid credentials"

    resp = login(client, 'test', 'test')

    assert '404' in resp.status, "Should fail upon passing invalid credentials"

    resp = register(client, 'test', 'test', 'test@test.com')

    assert '400' in resp.status, "Should fail to register the same username twice"

    resp = register(client, 'test1', 'test1', 'test@test.com')

    assert '400' in resp.status, "Should fail to register with duplicate email address."

def test_searching_for_user_via_id(client):
    """ Tests /user/<id> endpoint """
    resp = client.get('/user/0')

    assert '200' in resp.status, "Should succeed"

    resp = client.get('/user/1')

    assert '404' in resp.status, "Should fail"

def test_admin_functionality(client):
    """ Tests if admin user is available in the db and has proper privileges """
    resp = login(client, 'admin', 'admin')
    data = get_json_content(resp)

    assert '200' in resp.status, "Should successfully login as admin"
    assert data['username'] == 'admin', "Should successfully login as admin"
    assert data['role_id'] == 1, "Should successfully login as admin"

    resp = client.get('/users')
    data = get_json_content(resp)
    user_id = data[1]['id']

    assert len(data) == 2, "Number of users should be 2"

    resp = client.delete(f'/user/{user_id}')

    assert '200' in resp.status, "Should successfully delete user"

    resp = client.get('/users')
    data = get_json_content(resp)

    assert '200' in resp.status
    assert len(data) == 1, "Number of users after deletion should be 1"

    resp = client.delete(f'/user/{user_id}')

    assert '400' in resp.status, "Should fail to delete non-existent user"

    logout(client)

def test_changing_users_password(client):
    """ Tests user's ability to change their password """
    register(client, 'test', 'test', 'test@test.com')
    login(client, 'test', 'test')

    resp = client.put('/me', data=dict())

    assert resp.status_code == 400, "Should handle no arguments provided"

    resp = client.put('/me', data=dict(
        old_password='test',
        password1='test1',
        password2='test2',
    ))

    assert '401' in resp.status, "Should fail to change passwords if new passwords do not match"

    resp = client.put('/me', data=dict(
        old_password='test1',
        password1='test1',
        password2='test1',
    ))

    assert '401' in resp.status, "Should fail to change passwords if old password do not match"

    resp = client.put('/me', data=dict(
        old_password='test',
        password1='test1',
        password2='test1',
    ))

    assert '200' in resp.status, "Should successfully change users password"

    logout(client)

    resp = login(client, 'test', 'test')

    assert '404' in resp.status, "Should fail to login with old password"

    resp = login(client, 'test', 'test1')

    assert '200' in resp.status, "Should successfully login with new password"

    logout(client)

def test_changing_language(client):
    """ Tests changing user's language column in database """
    resp = login(client, 'test', 'test1')
    user = get_json_content(resp)

    assert user['language'] == 'EN', "Default language should be english"

    resp = client.put('/me', data=dict())

    assert resp.status_code == 400, "Should require argument"

    resp = client.put('/me', data=dict(
        language="DE"
    ))

    assert resp.status_code == 400, "Should fail to change to not-implemented language"

    resp = client.put('/me', data=dict(
        language="PL"
    ))

    assert resp.status_code == 200, "Should succesfully change users language"

    user = get_json_content(client.get('/me'))

    assert user['language'] == 'PL', "Make sure"

    logout(client)

def test_authorization_differences(client):
    """ Tests if user role impacts certain endpoint responses """
    # regular user
    login(client, 'test', 'test1')

    resp = client.get('/users')
    data = get_json_content(resp)

    assert 'id' not in data[0], "Should provide only list of usernames"

    logout(client)
    # admin user
    login(client, 'admin', 'admin')

    resp = client.get('/users')
    data = get_json_content(resp)

    assert 'id' in data[0], "Should provide detailed information about users"

    logout(client)

def test_generating_random_users(client):
    login(client, 'admin', 'admin')

    resp = client.get('/spam')

    assert resp.status_code == 201

    resp = client.get('/users')
    data = get_json_content(resp)

    assert len(data) > 100

    logout(client)

def test_purging_test_users(client):
    login(client, 'admin', 'admin')

    resp = client.delete('/purge')

    assert resp.status_code == 200

    resp = client.get('/users')
    data = get_json_content(resp)

    assert len(data) == 1, 'The only user remaining should be admin'

def test_deleting_self(client):
    register(client, 'test', 'test', 'test@test.com')
    login(client, 'test', 'test')

    resp = client.delete('/me')

    assert resp.status_code == 200

    resp = client.get('/me')

    assert resp.status_code == 418

    login(client, 'admin', 'admin')

    resp = client.get('/users')
    data = get_json_content(resp)

    assert len(data) == 1
