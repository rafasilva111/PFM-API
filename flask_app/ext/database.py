import os

from peewee import MySQLDatabase

from flask_app.classes.models import *
from playhouse.shortcuts import ReconnectMixin

user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"


class ReconectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


db = ReconectMySQLDatabase(database=database, user=user, password=password,
                           host=host)

models = [TokenBlocklist, NutritionInformation, Recipe, RecipeBackground, Tag, User, RecipeTagThrough, Comment, Follow,
          Ingredient, IngredientQuantity,CalendarEntry]


class Database(object):

    def __init__(self, app):
        self.app = app
        self.db = db
        self.register_handlers()

    def init_app(self, app):
        self.app = app

        return db

    def create_tables(self):
        return db.create_tables(models)

    def drop_tables(self):
        return db.drop_tables(models)

    def connect_db(self):
        if self.db.is_closed():
            self.db.connect()

    def close_db_(self, ext):
        if not db.is_closed():
            db.close()

    def register_handlers(self):
        # li em algum lugar que não era preciso abrir a connection vou deixar assim para exprimentar
        ##self.app.before_request(self.connect_db)
        self.app.teardown_request(self.close_db_)
