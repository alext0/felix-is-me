from api import api
from util.json_util import jsonify
from marshmallow import missing


class Location:
    """
    Namespace with Webargs input value locations as constants.
    """
    json = ('json',)  # in the request body
    query = ('query',)  # == 'querystring'
    headers = ('headers',)


@api.errorhandler(404)
def not_found(error=None):
    message = {
        'message': 'Not Found'
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp


@api.errorhandler(422)
def handle_unprocessable_entity(error):
    """
    This error is raised by webargs when input parameters fail validation.
    E.g. if a string value is supplied for a numeric ID.
    :param error: An UnprocessableEntity exception. Its "data" attribute holds the validation failure messages from \
    Webargs and the original exception.
    :return: JSON-format error description with original exception name and individual error details (may be several).
    """
    data = getattr(error, 'data')
    if data:
        exception_name = data['exc'].__class__.__name__
        error_messages = data['exc'].messages
    else:
        exception_name = getattr(error, 'name', error.__class__.__name__)
    return jsonify({
        'message': exception_name,
        'errors': error_messages,
    }), 422


@api.errorhandler(400)
def bad_request(error='The request could not be processed.'):
    message = {
        'message': error
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


def already_exists():
    message = {
        'message': 'Validation Failed',
        'errors': [
            {
                'code': 'already_exists'
            }
        ]
    }
    resp = jsonify(message)
    resp.status_code = 422
    return resp


def update_from_args(obj, args):
    for key, value in args:
        if key.startswith('_') == False and value != missing:
            setattr(obj, key, value)
    return obj


@api.after_request
def disable_browser_cache(response):
    """
    Disable caching (needed for IE).
    """
    response.cache_control.max_age = 0
    response.cache_control.must_revalidate = True
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    return response

