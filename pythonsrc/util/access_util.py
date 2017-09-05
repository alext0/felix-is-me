"""
Authentication and access control logic.
"""

import sys
from functools import wraps
from flask import g, request


ATN_HEADER = 'X-Forwarded-Email'


def login_required(f):
    """
    API route decorator to enforce user login for an API call and to set the current_user global.
    Allows access iff the authentication header is present,
    returns 403 (Unauthorised) otherwise.
    Assumes that only the gateway authenticator can provide this header.
    :param f:
    :return:
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_email = request.headers[ATN_HEADER].lower()
            user = db.session.query(User).filter(func.lower(User.email) == user_email).one()
            g.current_user = user
        except:
            # TODO log error
            print('Error checking {} request header: {}'.format(ATN_HEADER, sys.exc_info()[0]))
            return 'Not logged in. <p>The {} header is missing.'.format(ATN_HEADER), 401
        return f(*args, **kwargs)

    return decorated_function

