from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow,fields

bcrypt = Bcrypt()

def init_app(app):
    bcrypt.init_app(app)
