import math

import requests
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource

from backend.dbManager import DBManager
from backend.endpoints.fitness_model import Peso, Calorias, Proteina, Gordura, Hidratos_De_Carbono, Full_Model
from backend.endpoints.recipes import Recipe, RECIPE_ENDPOINT
from backend.endpoints.user import User, USER_ENDPOINT


app = Flask(__name__)
api = Api(app)

LOCAL_HOST = "http://localhost:8000"


api.add_resource(Peso, '/peso')
api.add_resource(Calorias, '/calorias')
api.add_resource(Gordura, '/gordura')
api.add_resource(Proteina, '/proteina')
api.add_resource(Hidratos_De_Carbono, '/hidratos_de_carbono')
api.add_resource(Full_Model, '/full_model')
api.add_resource(Recipe, '/'+RECIPE_ENDPOINT)
api.add_resource(User, '/'+USER_ENDPOINT)


if __name__ == '__main__':
    #Database
    conn = DBManager()
    conn.populate_db()
    #main()
    app.run(debug=True,host="0.0.0.0")
