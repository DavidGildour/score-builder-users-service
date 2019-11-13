import re
import requests
import os

from flask import session
from flask_restful import Resource, reqparse
from werkzeug.security import check_password_hash, generate_password_hash

from models.user import UserModel
from models.role import Role
from utils import login_required

class Me(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('old_password')
    parser.add_argument('password1')
    parser.add_argument('password2')
    parser.add_argument('language')

    @classmethod
    @login_required
    def get(cls):
        response = Me.get_id()
        if 'user_id' in response:
            return User.get(response['user_id'])
        return {
           'message': 'Invalid token',
           'content': response,
        }, 400

    @classmethod
    @login_required
    def put(cls):
        response = Me.get_id()
        if 'user_id' in response:
            data = Me.parser.parse_args()
            user = UserModel.find_by_id(response['user_id'])

            if all((data['old_password'], data['password1'], data['password2'])):
                if not check_password_hash(user.password, data['old_password']) or data['password1'] != data['password2']:
                    return {
                        'message': 'Passwords do not match.'
                    }, 401
                user.password = generate_password_hash(data['password1'])
                user.save_to_db()

                return {
                    'message': f'Password changed.'
                }
            elif data['language'] and data['language'] in UserModel.VALID_LANGS:
                user.language = data['language']
                user.save_to_db()

                return {
                    'message': f'Language changed to {data["language"]} for user {user.username}.'
                }
            else:
                return {
                    'message': 'Required arguments missing or invalid argument(s) provided.'
                }, 400
        return {
           'message': 'Invalid token',
           'content': response,
               }, 400

    @classmethod
    @login_required
    def delete(cls):
        response = Me.get_id()
        if 'user_id' in response:
            user = UserModel.find_by_id(response['user_id'])
            user.delete_from_db()
            UserLogout.get()
            return {
                'message': f'Successfully deleted user {user.username} ({response["user_id"]}).'
            }

        return {
           'message': 'Invalid token',
           'content': response,
        }, 400

    @classmethod
    def get_id(cls):
        return requests.get(url=f'{os.environ["TOKEN_SERVICE"]}/user_id',
                            headers={'Authorization': f'Bearer {session["access_token"]}'}).json()


class User(Resource):
    @classmethod
    def get(cls, user_id):
        user = UserModel.find_by_id(user_id)

        if not user:
            return {'message': 'User not found'}, 404

        return {
            'message': 'Success',
            'content': user.json()
        }

    @classmethod
    @login_required
    def delete(cls, user_id):
        if cls.get_claims() != 'ADMIN':
            return {
                'message': f'Admin privileges required.'
            }, 401

        user = UserModel.find_by_id(user_id)

        if not user:
            return {
                'message': 'No such user.'
            }, 400

        user.delete_from_db()

        return {
            'message': f'User {user.username} ({user.id}) successfully deleted.'
        }

    @classmethod
    def get_claims(cls):
        claims = requests.get(url=f'{os.environ["TOKEN_SERVICE"]}/user_role',
                              headers={'Authorization': f'Bearer {session["access_token"]}'}).json()
        return claims['user_role']


class UserList(Resource):
    @classmethod
    @login_required
    def get(cls):
        users = [user.json() for user in UserModel.find_all()]

        # import time
        # time.sleep(2)

        if User.get_claims() != 'ADMIN':
            return {
                'message': 'Success. Get admin privileges for more detailed info.',
                'content': [user['username'] for user in users],
            }

        return {
            'message': 'Success.',
            'content': users,
        }


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', required=True, type=str, help="This field cannot be left blank")
    parser.add_argument('password', required=True, type=str, help="This field cannot be left blank")

    @classmethod
    def post(cls):
        data = UserLogin.parser.parse_args()

        user = UserModel.find_by_username(data['username'])

        if user and check_password_hash(user.password, data['password']):
            user_role = Role.find_by_id(user.role_id).name
            content = user.json()
            token = requests.get(f'{os.environ["TOKEN_SERVICE"]}/token?user_id={user.id}&role={user_role}').json()
            session['access_token'] = token['access_token']
            content.update(token)
            return {
                'message': 'Successfully logged in.',
                'content': content,
            }

        return {
            'message': 'Invalid credentials or user does not exist.'
        }, 404


class UserLogout(Resource):
    @classmethod
    @login_required
    def get(cls):
        resp = requests.get(f'{os.environ["TOKEN_SERVICE"]}/blacklist',
                     headers={
                         'Authorization': f'Bearer {session["access_token"]}'
                     })
        if not resp.status_code == 200:
            return {
                'message': 'Something went wrong, try again.'
            }, 503
        session.clear()
        return {
            'message': 'Logged out.'
        }


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True, help="Please provide valid username.")
    parser.add_argument('password1', type=str, required=True, help="Please provide valid password.")
    parser.add_argument('password2', type=str, required=True, help="Please repeat your password.")
    parser.add_argument('email', type=str, required=True, help="Please provide your email address.")
    parser.add_argument('lang')

    @classmethod
    def post(cls):
        data = UserRegister.parser.parse_args()

        if not data['username']:
            return {'message': 'Username cannot be blank.'}, 400
        if not data['password1']:
            return {'message': 'Password cannot be blank.'}, 400
        if data['password1'] != data['password2']:
            return {'message': 'Passwords do not match.'}, 400
        elif not re.fullmatch(r'[^@\s\'\"]{1,64}@[a-z0-9\-]*\.[a-z0-9]*', data['email']):
            return {'message': 'Invalid email address.'}, 400
        elif UserModel.find_by_email(data['email']):
            return {'message': 'User already registered with this email.'}, 400
        elif UserModel.find_by_username(data['username']):
            return {'message': 'Username taken.'}, 400

        user = UserModel(data['username'], data['password1'], data['email'], data['lang'])
        user.save_to_db()

        return {
            'message': 'User successfully created. Log in to continue.',
            'content': user.json(),
        }, 201


class GenerateUsers(Resource):
    """ This endpoint is only for development and should be deleted before production """
    @classmethod
    @login_required
    def get(cls):
        if User.get_claims() != 'ADMIN':
            return {
                'message': 'Admin privileges required.'
            }, 401

        import random
        ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJLKMNOPQRSTUVWXYZ0123456789'

        users = [{
                    'username': ''.join(random.choice(ALPHABET) for _ in range(10)),
                    'password': ''.join(random.choice(ALPHABET) for _ in range(10)),
                    'email': ''.join(random.choice(ALPHABET) for _ in range(10)) + '@test.com'
                } for __ in range(100)]

        for user in users:
            UserModel(**user).save_to_db()

        return {
            'message': 'Succesfully generated 100 random test users.'
        }, 201


class PurgeTestUsers(Resource):
    """ This endpoint is only for development and should be deleted before production """
    @classmethod
    @login_required
    def delete(cls):
        if User.get_claims() != 'ADMIN':
            return {
                'message': 'Admin privileges required.'
            }, 401

        test_users = UserModel.query.filter(UserModel.email.endswith('@test.com')).all()

        for user in test_users:
            user.delete_from_db()

        return {
            'message': 'Test users purged successfully',
        }