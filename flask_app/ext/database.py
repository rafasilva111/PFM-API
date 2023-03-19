import os

import toml
from peewee import MySQLDatabase
# from os.path import dirname, abspath
#
# db = MySQLDatabase(database=app.config.get('DATABASE_Name'), user=app.config.get('DATABASE_USER'), password=app.config.get('DATABASE_PASSWORD'),
#                    host=app.config.get('DATABASE_HOST'))
#
#
# def init_app(app):
#     # # Load the configuration from the TOML file
#     # with open(fr"{dirname(dirname(dirname(abspath(__file__))))}\settings.toml") as f:
#     #     config = toml.load(f)
#     #
#     #
#     # # Get the configuration for the current environment
#     env = app.config.get('DATABASE_HOST')
#     # env_config = config.get(env, {})
#
#     # Set the database URI based on the app configuration
#     # todo idk why this is true app.config.get('ENV') == 'production', so i inverted the signal
#     # if app.config.get('ENV') == 'production':
#     #     db_uri = app.config['SQLALCHEMY_DATABASE_URI']
#     # else:
#     db_uri = 'mysql+pymysql://root:12345678@flask_db/flask_api'
#     # db_uri = 'mysql+pymysql://root:12345678@localhost:3306/flask_api'
#     # Connect to the database using the URI
#     db.connect(reuse_if_open=True)
#     app.db = db
from flask_app.models import TokenBlocklist, NutritionInformation, Preparation, Recipe, RecipeBackground, Tag, User

user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"

db = MySQLDatabase(database=database, user=user, password=password,
                   host=host)


class DBManager:

    def __init__(self):
        db.connect()
        self.populate_db()

    def populate_db(self):
        db.create_tables([TokenBlocklist, NutritionInformation, Preparation, Recipe, RecipeBackground, Tag, User])


    def drop_tables(self):
        db.drop_tables([TokenBlocklist, NutritionInformation, Preparation, Recipe, RecipeBackground, Tag, User])

    def query_titles(self):
        return

    # RECIPE

    def post_recipes(self):
        try:
            Recipe.create(title="")
        except Exception as err:
            print(err)

        return 1
