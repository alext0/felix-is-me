from decimal import Decimal
from flask.json import JSONEncoder as FlaskJSONEncoder
from flask_sqlalchemy import Model
from flask import jsonify as flask_jsonify


class AppJSONEncoder(FlaskJSONEncoder):
    def default(self, o):
        if isinstance(o, Model):
            # Explicit optimization for the case when there is no __json_exclude__
            json_exclude = getattr(o, '__json_exclude__', None)
            if json_exclude:
                return {
                    k: v for k, v in o.__dict__.items() if not k.startswith('_') and k not in json_exclude
                }
            else:
                return {
                    k: v for k, v in o.__dict__.items() if not k.startswith('_')
                }
        elif isinstance(o, Decimal):
            return str(o)
        else:
            return super().default(o)


_app_json_encoder = AppJSONEncoder()


def jsonify(*args, **kwargs):
    """
    :param args: top level model objects are converted to dicts, anything else goes right to flask jsonify
    :param kwargs: passed along to flask jsonify
    :return: flask jsonification result
    """
    args = map(lambda o: _app_json_encoder.default(o) if isinstance(o, Model) else o, args)
    return flask_jsonify(*args, **kwargs)