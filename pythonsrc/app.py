import sys
import json
from os.path import isfile
import sqlalchemy
import warnings

# Remove the test module dir from the Python path if present (added by the PyCharm debugger)
if 'tests' in sys.path[0]:
    del sys.path[0]

import apispec
import os
from flask import Flask
from util.json_util import AppJSONEncoder

Flask.json_encoder = AppJSONEncoder
app = Flask(__name__)
app.config.from_pyfile('secrets.config', silent=True)
app.config.from_pyfile(os.path.join(os.getcwd(), 'config', os.getenv('APPLICATION_ENV', 'development').lower() + '.config'))


# Create an API doc store for Swagger
version_file_path = 'version.json'
if isfile(version_file_path):
    version_details = json.loads(open(version_file_path).read())
    version = 'Build: {0}, Commit: {1}'.format(version_details['build_no'], version_details['commit'])
else:
    version = 'No {} file found.'.format(version_file_path)

app.api_doc = apispec.APISpec(
    title='Range Planning Tool',
    version=version,
    description='Sainsburys range planner project.',
    plugins=[
        'apispec.ext.flask',
        'apispec.ext.marshmallow',
    ],
)

from api import api as api_blueprint
app.register_blueprint(api_blueprint, url_prefix='/api')

for view_name in app.view_functions.keys():
    if not view_name.startswith('_') and view_name not in ['static']:
        view_fn = app.view_functions[view_name]
        app.api_doc.add_path(view=view_fn)
