from flask import session

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'access_token' not in session:
            return {
                'message': 'Login required.'
            }, 418
        return f(*args, **kwargs)
    return wrapper
