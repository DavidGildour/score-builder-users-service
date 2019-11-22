import os
import sys

from sqlalchemy import exc
from flask_session import Session

from app import app
from db import db


@app.before_first_request
def create_tables():
    db.create_all()

    try:
        from models.role import Role
        from models.user import UserModel

        Role('ADMIN').save_to_db()
        Role('USER').save_to_db()
        UserModel('admin', 'admin', 'admin@admin.com', role_id=1, user_id='0').save_to_db()
    except exc.IntegrityError:
        db.session.rollback()


if __name__ == '__main__':
    app.config.from_object('config.DevelopmentConfig')
    Session(app)
    db.init_app(app)


    if len(sys.argv) > 1:
        if sys.argv[1] == 'docker':
            app.run(debug=True, host="0.0.0.0")
        elif sys.argv[1] == 'default':
            os.environ['FLASK_ENV'] = 'development'
            os.environ['TOKEN_SERVICE'] = 'http://127.0.0.1:5001'
            app.run(debug=True)
        else:
            print('Unknown command: {}'.format(sys.argv[1]))
            sys.exit()
    else:
        os.environ['FLASK_ENV'] = 'development'
        os.environ['TOKEN_SERVICE'] = 'http://127.0.0.1:5001'
        app.run(debug=True)