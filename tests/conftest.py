import pytest

from app import app
from db import db

from models.user import UserModel
from models.role import Role

@pytest.fixture(scope="module")
def client():
    """ Testing client for the app, initialized with test database """
    app.config.from_object('config.TestingConfig')
    app.app_context().push()
    db.init_app(app)

    client = app.test_client()
    db.create_all()

    Role('ADMIN').save_to_db()
    Role('USER').save_to_db()
    UserModel('admin', 'admin', 'admin@admin.com', role_id=1, user_id='0').save_to_db()

    yield client

    db.session.close()
    db.drop_all()
