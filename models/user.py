from werkzeug.security import generate_password_hash
from datetime import datetime
from shortuuid import uuid

from db import db


class UserModel(db.Model):
    VALID_LANGS = "EN", "PL"
    __tablename__ = 'users'

    id = db.Column(db.String(22), primary_key=True, autoincrement=False, default=uuid)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, default=2)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.now)
    email = db.Column(db.String(100), nullable=False, unique=True)
    language = db.Column(db.String(2), nullable=False, default="EN")

    def __init__(self, username, password, email, language=None, role_id=None, user_id=None):
        if role_id:
            self.role_id = role_id
        if user_id:
            self.id = user_id
        if language and language in UserModel.VALID_LANGS:
            self.language = language
        self.email = email
        self.username = username
        self.password = generate_password_hash(password)

    def json(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'username': self.username,
            'email': self.email,
            'language': self.language,
            'registration_date': str(self.registration_date)[:19]
        }

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
