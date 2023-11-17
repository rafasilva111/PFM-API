import sys

from .bp_fitness import fitness_blueprint
from .util.constants import BASE_URL_PREFIX

sys.path.append(".")

from flask import Blueprint
from flask_restx import Api, Resource
from .ns_recipe import api as api_recipe, ENDPOINT as RECIPE_ENDPOINT
from .ns_user import api as api_user, ENDPOINT as USER_ENDPOINT
from .ns_comment import api as api_comment, ENDPOINT as COMMENT_ENDPOINT
from .ns_follow import api as api_follow, ENDPOINT as FOLLOW_ENDPOINT
from .ns_calendar import api as api_calendar, ENDPOINT as CALENDAR_ENDPOINT
from .ns_shopping_list import api as api_shopping_list, ENDPOINT as SHOPPING_LIST_ENDPOINT
from .ns_notifications import api as api_notifications, ENDPOINT as NOTIFICATIONS_ENDPOINT

from .ns_auth import api as api_auth, ENDPOINT as ENDPOINT_AUTH
from .ns_admin import api as api_admin_company, ENDPOINT as ENDPOINT_ADMIN
from .ns_miscellaneous import api as api_miscellaneous, ENDPOINT as ENDPOINT_MISCELLANEOUS

# Here you create the API path


bp = Blueprint("restapi", __name__, url_prefix=BASE_URL_PREFIX)

# TODO
description = r"""
This is an example of a RESTful API using Flask-RESTX, it consists (actually it was the first thing that came to my mind) of relationships with schools, students, managers and what the rest entails, it is somewhat simple but it would be a complete example using Marshmallow and SQLAlchemy, just add ¯¯\\\_(ツ)_/¯
"""

api = Api(bp, version="Version 1.0 ", title="API Documentation", description=description, doc="/doc")
api.add_namespace(api_recipe, path=RECIPE_ENDPOINT)
api.add_namespace(api_user, path=USER_ENDPOINT)
api.add_namespace(api_comment, path=COMMENT_ENDPOINT)
api.add_namespace(api_follow, path=FOLLOW_ENDPOINT)
api.add_namespace(api_calendar, path=CALENDAR_ENDPOINT)
api.add_namespace(api_shopping_list, path=SHOPPING_LIST_ENDPOINT)
api.add_namespace(api_notifications, path=NOTIFICATIONS_ENDPOINT)

api.add_namespace(api_auth, path=ENDPOINT_AUTH)
api.add_namespace(api_admin_company, path=ENDPOINT_ADMIN)
api.add_namespace(api_miscellaneous, path=ENDPOINT_MISCELLANEOUS)


def init_app(app):
    app.register_blueprint(bp)


