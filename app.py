import os

from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from resources.user import User, UserList, UserRegister, UserLogin, UserLogout, Me, PurgeTestUsers, GenerateUsers

if not 'FRONT_END' in os.environ:
    os.environ['FRONT_END'] = 'http://127.0.0.1:3000'

app = Flask(__name__)
cors = CORS(app, supports_credentials=True, origins='http://localhost:3000')
# cors = CORS(
#     app,
#     supports_credentials=True,
#     origins=[
#                 'http://localhost:3000/',
#                 'http://127.0.0.1:3000/',
#                 os.environ['FRONT_END'],
#                 'http://0.0.0.0:3000/',
#                 'http://172.20.0.5:3000/'
#             ]
# )
api = Api(app)

api.add_resource(Me, '/me')
api.add_resource(User, '/user/<string:user_id>')
api.add_resource(UserList, '/users')
api.add_resource(UserLogin, '/login')
api.add_resource(UserLogout, '/logout')
api.add_resource(UserRegister, '/register')
api.add_resource(PurgeTestUsers, '/purge')
api.add_resource(GenerateUsers, '/spam')


# resources={
#     r'/*': {
#         'origins': [
#             'http://localhost:3000/',
#             'http://127.0.0.1:3000/',
#             # os.environ['FRONT_END'],
#             # 'http://0.0.0.0:3000/',
#             # 'http://172.20.0.5:3000/'
#         ]
#     }
# }