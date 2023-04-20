import json

from flask import Response, Blueprint
from flask_app.ext.database import db
admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix="/api/v1")

from flask_app.models.model_auth import TokenBlocklist
from flask_app.models.model_user import User
from flask_app.models.model_recipe import Recipe
from flask_app.models.model_recipe_background import RecipeBackground
from flask_app.models.model_nutrition_information import NutritionInformation
from flask_app.models.model_tag import Tag, RecipeTagThrough
from flask_app.models.model_comment import Comment
from flask_app.models.model_follow import Follow

# Admin API Model
models = [TokenBlocklist, NutritionInformation, Recipe, RecipeBackground, Tag, User, RecipeTagThrough, Comment, Follow]

@admin_blueprint.route("/create_tables", methods=["GET"])
def teste():
    db.create_tables(models)
    db.close()
    return Response(status=200, response=json.dumps("Tables successfully created."))

