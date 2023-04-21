import os

from peewee import MySQLDatabase

from flask_app.models.model_auth import TokenBlocklist
from flask_app.models.model_user import User
from flask_app.models.model_recipe import Recipe
from flask_app.models.model_recipe_background import RecipeBackground
from flask_app.models.model_nutrition_information import NutritionInformation
from flask_app.models.model_tag import Tag, RecipeTagThrough
from flask_app.models.model_comment import Comment
from flask_app.models.model_follow import Follow

user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"

db = MySQLDatabase(database=database, user=user, password=password,
                   host=host)

models = [TokenBlocklist, NutritionInformation, Recipe, RecipeBackground, Tag, User, RecipeTagThrough, Comment, Follow]

class Database(object):

    def __init__(self,app):
        self.app = app
        self.db = db
        self.register_handlers()

    def init_app(self,app):
        self.app = app

        return db

    def create_tables(self):
        return self.db.create_tables(models)

    def drop_db(self):
        return self.db.drop_tables(models)

    def connect_db(self):
        if self.db.is_closed():
            self.db.connect()


    def close_db_(self,ext):
        if not db.is_closed():
            db.close()


    def register_handlers(self):
        self.app.before_request(self.connect_db)
        self.app.teardown_request(self.close_db_)
