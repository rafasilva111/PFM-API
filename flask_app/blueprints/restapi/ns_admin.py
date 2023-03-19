import json

from flask import Response, Blueprint
from flask_restx import Namespace

from flask_app.ext.database import db
from flask_app.models import TokenBlocklist, NutritionInformation, Preparation, Recipe, RecipeBackground, Tag, User
admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix="/api/v1")

# Admin API Model


@admin_blueprint.route("/teste", methods=["GET"])
def teste():
    db.create_tables([TokenBlocklist, NutritionInformation, Preparation, Recipe, RecipeBackground, Tag, User])
    return Response(status=200, response=json.dumps("User logged out sucessfully."))
