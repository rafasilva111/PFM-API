import sys

from .util.constants import BASE_URL_PREFIX

sys.path.append(".")

from flask import Blueprint
from flask_restx import Api, Resource
from flask_app.ext.database import db
# from flask_app.models.model_student import Student
# from flask_app.models.model_school import School
#from .ns_student import api as api_student
#from .ns_school import api as api_school
from .ns_recipe import api as api_recipe,BASE_RECIPE_PREFIX
from .bp_auth import auth_blueprint
from .ns_admin import admin_blueprint

# Here you create the API path


bp = Blueprint("restapi", __name__, url_prefix=BASE_URL_PREFIX)

description = r"""
This is an example of a RESTful API using Flask-RESTX, it consists (actually it was the first thing that came to my mind) of relationships with schools, students, managers and what the rest entails, it is somewhat simple but it would be a complete example using Marshmallow and SQLAlchemy, just add ¯¯\\\_(ツ)_/¯
"""

api = Api(bp, version="Version 1.0 ", title="API Documentation", description=description, doc="/doc")
#api.add_namespace(api_student, path="/student")
#api.add_namespace(api_school, path="/school")
api.add_namespace(api_recipe, path=BASE_RECIPE_PREFIX)

def init_app(app):
    app.register_blueprint(bp)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(admin_blueprint)

