import json

def get_json_content(response) -> dict:
    """ Returns a dict-translated JSON with content of the response """
    return json.loads(response.get_data(as_text=True))['content']

def register(client, user: str, password: str, email: str, lang: str = 'EN'):
    """ Function for creating a new user """
    return client.post('/register', data=dict(
        username=user,
        password1=password,
        password2=password,
        email=email,
        lang=lang,
    ))

def login(client, user: str, password: str):
    """ Function for logging on to the service """
    return client.post('/login', data=dict(
        username=user,
        password=password
    ))

def logout(client):
    """ Function for logging out of the service """
    return client.get('/logout')
