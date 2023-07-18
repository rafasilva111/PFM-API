import sys

from .bp_fitness import fitness_blueprint
from .util.constants import BASE_URL_PREFIX

sys.path.append(".")

from flask import Blueprint
from flask_restx import Api, Resource
from .ns_recipe import api as api_recipe,ENDPOINT as RECIPE_ENDPOINT
from .ns_user import api as api_user,ENDPOINT as USER_ENDPOINT
from .ns_comment import api as api_comment,ENDPOINT as COMMENT_ENDPOINT
from .ns_follow import api as api_follow,ENDPOINT as FOLLOW_ENDPOINT
from .ns_calendar import api as api_calendar,ENDPOINT as CALENDAR_ENDPOINT

from .bp_auth import auth_blueprint
from .bp_admin import admin_blueprint
from .bp_admin import api as api_admin_company,ENDPOINT_COMPANY
# Here you create the API path


bp = Blueprint("restapi", __name__, url_prefix=BASE_URL_PREFIX)

description = r"""
This is an example of a RESTful API using Flask-RESTX, it consists (actually it was the first thing that came to my mind) of relationships with schools, students, managers and what the rest entails, it is somewhat simple but it would be a complete example using Marshmallow and SQLAlchemy, just add ¯¯\\\_(ツ)_/¯
"""

api = Api(bp, version="Version 1.0 ", title="API Documentation", description=description, doc="/doc")
api.add_namespace(api_recipe, path=RECIPE_ENDPOINT)
api.add_namespace(api_user, path=USER_ENDPOINT)
api.add_namespace(api_comment, path=COMMENT_ENDPOINT)
api.add_namespace(api_follow, path=FOLLOW_ENDPOINT)
api.add_namespace(api_calendar, path=CALENDAR_ENDPOINT)
api.add_namespace(api_admin_company, path=ENDPOINT_COMPANY)

def init_app(app):
    app.register_blueprint(bp)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(fitness_blueprint)

