from api import api
from app import app
from flask import json, Response


@api.route('/swagger', methods=['GET'])
def get_swagger():
    """
    ---
    get:
        description: Return the app's REST API specification in Swagger 2.0 format

        responses:
            200:
                description: Swagger spec. in JSON form
    """
    spec_dict = app.api_doc.to_dict()
    return Response(json.dumps(spec_dict), status=200, mimetype='application/json')
