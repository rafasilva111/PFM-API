from flask_marshmallow import Marshmallow,fields

ma = Marshmallow()

def init_app(app):
    ma.init_app(app)
