from flask import Blueprint

api = Blueprint('api', __name__)

from . import healthcheck, main, swagger
