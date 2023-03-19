import os

from peewee import Model, MySQLDatabase

user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"


db = MySQLDatabase(database=database, user=user, password=password,
                   host=host)

class BaseModel(Model):
    class Meta:
        database = db
