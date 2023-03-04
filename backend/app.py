import math

from flask_bcrypt import Bcrypt
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

from backend.dbManager import DBManager, TokenBlocklist
from backend.endpoints.auth import auth_blueprint
from backend.endpoints.fitness_model import Peso, Calorias, Proteina, Gordura, Hidratos_De_Carbono, Full_Model
from backend.endpoints.recipes import Recipe, RECIPE_ENDPOINT
from backend.endpoints.user import User, USER_ENDPOINT, SEXES
from backend.endpoints.comments import Comments, COMMENTS_ENDPOINT
from backend.endpoints.recipe_background import *
from flask_jwt_extended import JWTManager


app = Flask(__name__)
api = Api(app)

app.config.from_envvar('ENV_FILE_LOCATION')
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

HOST = "0.0.0.0"


# Callback function to check if a JWT exists in the database blocklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    try:
        TokenBlocklist.get(jti=jti)
    except peewee.DoesNotExist:
        return False
    return True

api.add_resource(Peso, '/peso')
api.add_resource(Calorias, '/calorias')
api.add_resource(Gordura, '/gordura')
api.add_resource(Proteina, '/proteina')
api.add_resource(Hidratos_De_Carbono, '/hidratos_de_carbono')
api.add_resource(Full_Model, '/full_model')
api.add_resource(Recipe, RECIPE_ENDPOINT)
api.add_resource(User, USER_ENDPOINT)
api.add_resource(Recipe_Background_Likes, RECIPE_BACKGROUND_LIKES_ENDPOINT)
api.add_resource(Recipe_Background_Saves, RECIPE_BACKGROUND_SAVES_ENDPOINT)
api.add_resource(Recipe_Background_Creates, RECIPE_BACKGROUND_CREATES_ENDPOINT)
api.add_resource(Comments, COMMENTS_ENDPOINT)

app.register_blueprint(auth_blueprint)

if __name__ == '__main__':
    #Database
    conn = DBManager()
    conn.populate_db()
    #main()
    app.run(debug=True,host=HOST)
