import os

from peewee import MySQLDatabase

from flask_app.models.model_auth import TokenBlocklist
from flask_app.models.model_user import User
from flask_app.models.model_recipe import Recipe
from flask_app.models.model_recipe_background import RecipeBackground
from flask_app.models.model_nutrition_information import NutritionInformation
from flask_app.models.model_tag import Tag, RecipeTagThrough

user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"

db = MySQLDatabase(database=database, user=user, password=password,
                   host=host)

models = [TokenBlocklist, NutritionInformation, Recipe, RecipeBackground, Tag, User, RecipeTagThrough]


class DBManager:

    def __init__(self):
        db.connect()

    def create_tables(self):
        db.create_tables(models)

    def drop_tables(self):
        db.drop_tables(models)

    def query_titles(self):
        return

    # RECIPE

    def post_recipes(self):
        try:
            Recipe.create(title="")
        except Exception as err:
            print(err)

        return 1
