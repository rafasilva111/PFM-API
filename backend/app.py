import math

import requests
from flask import Flask
from flask_restful import reqparse, abort, Api, Resource
from bs4 import *
from requests import request

from backend.dbManager import DBManager
from backend.endpoints.recipes import Recipe
from backend.endpoints.user import User
from backend.teste import main

app = Flask(__name__)
api = Api(app)

LOCAL_HOST = "http://localhost:8000"

ACTIVIDADE = {
            'absolutamente_nenhum': ['Taxa metabólica basal', 1],
            'sedentario': ['Pouco ou nenhum execício', 1.2],
            'leve': ['Execício de 1 a 3 vezes', 1.375],
            'moderado': ['Execício 4-5 vezes/semana', 1.465],
            'ativo': ['Execício diario ou exercícios intensos 3-4 vezes/semana', 1.55],
            'muito_ativo': ['Exercícios intensos 6-7 vezes/semana', 1.725],
            'extra_ativo': ['Execício intesso diário, ou te um trabalho muito fisico', 1.9]
        }

parser = reqparse.RequestParser()
parser.add_argument('altura')
parser.add_argument('peso')
parser.add_argument('idade')
parser.add_argument('genero')
parser.add_argument('atividade')
parser.add_argument('task')
parser.add_argument('class', type=list)


# /peso?altura=180&idade=20&genero=m
class Peso(Resource):
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero']:
            url = f"https://www.calculator.net/ideal-weight-calculator.html?ctype=metric&cage={args['idade']}&csex={str(args['genero']).lower()}&cheightmeter={args['altura']}"
            base_response = requests.get(url)
            html = BeautifulSoup(base_response.content, 'html.parser')
            main_result = html.find(class_="cinfoT")
            table = main_result.find_all('tr')[-1]
            td = table.find_all("td")[1].text.split("-")
            low = td[0].strip()
            high = td[1].replace("kgs", "").strip()

            return_dict = [low, high]
            return return_dict

        return -1


# /calorias?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
class Calorias(Resource):
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade']:

            url = f"https://www.calculator.net/calorie-calculator.html?ctype=metric&cage={args['idade']}&csex={args['genero']}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={args['altura']}&ckg={args['peso']}&cactivity={ACTIVIDADE[args['atividade']][1]}&cmop=0&coutunit=c&cformula=m&cfatpct=20&printit=0&x=75&y=20"
            base_response = requests.get(url)
            html = BeautifulSoup(base_response.content, 'html.parser')
            table = html.find('table')

            table_array = []
            titles  = []
            response = {}
            first_time = True
            for row in table.find_all("tr"):
                helper = row.get_text('/').split(("/"))
                if first_time:
                    titles.append(helper[0])
                    helper[0] = 0
                    helper.pop(2)
                    helper.pop(3)
                    helper.pop(3)
                    first_time = False
                else:

                    titles.append(helper[0])

                    helper.pop(0)
                    helper.pop(1)
                    helper.pop(2)
                    helper.pop(3)
                    helper.pop(3)
                    helper[1] = helper[1] + " Calories"
                    if "1" in helper[0]:
                        helper[0] = 1
                    elif "0.5" in helper[0]:
                        helper[0] = 0.5
                    elif "0.5" in helper[0]:
                        helper[0] = -0.5
                    elif "1" in helper[0]:
                        helper[0] = -1
                    else:
                        helper[0] = 0
                    table_array.append(helper)


            response.update({"titles": titles})
            response.update({"data": table_array})
            response.update({"disclaimer": "Please consult with a doctor when losing 1 kg or more per week since it "
                                           "requires that you consume less than the minimum recommendation of 1, "
                                           "500 calories a day."})
            return response

        return -1

# /gordura?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
class Gordura(Resource):
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade']:

            url = f"https://www.calculator.net/fat-intake-calculator.html?ctype=metric&&cage={args['idade']}&csex={args['genero']}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={args['altura']}&ckg={args['peso']}&cactivity={ACTIVIDADE[args['atividade']][1]}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
            base_response = requests.get(url)
            html = BeautifulSoup(base_response.content, 'html.parser')
            table = html.find('table')

            table_array = []
            response = {}
            first_time = True
            for row in table.find_all("tr"):
                if first_time:
                    response.update({"titles":row.get_text('/').split(("/"))})
                    first_time =False
                else:
                    helper = row.get_text('/').split(("/"))
                    if len(helper)>5:
                        helper.pop(1)

                    if "Gain 1" in helper[0]:
                        helper[0] = 1
                    elif "Gain 0.5"in helper[0]:
                        helper[0] = 0.5
                    elif "Lose 0.5"in helper[0]:
                        helper[0] = -0.5
                    elif "Lose 1"in helper[0]:
                        helper[0] = -1
                    else:
                        helper[0] = 0
                    table_array.append(helper)



            response.update({"data": table_array})

            return response

        return -1


# /hidratos_de_carbono?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
class Hidratos_De_Carbono(Resource):
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade']:

            url = f"https://www.calculator.net/carbohydrate-calculator.html?ctype=metric&&cage={args['idade']}&csex={args['genero']}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={args['altura']}&ckg={args['peso']}&cactivity={ACTIVIDADE[args['atividade']][1]}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
            base_response = requests.get(url)
            html = BeautifulSoup(base_response.content, 'html.parser')
            table = html.find('table')

            table_array = []
            response = {}
            first_time = True
            for row in table.find_all("tr"):
                if first_time:
                    helper = row.get_text('/').split(("/"))

                    response.update({"titles":[helper[0],helper[1],"Min","Sugar","Max","Sugar"]})

                    first_time =False
                else:
                    helper = row.get_text('/').replace('\xa0',' ').split(("/"))
                    if 'week' in helper:
                        helper.pop(1)
                    helper.pop(2)
                    helper.pop(2)
                    helper.pop(4)
                    helper.pop(4)
                    helper[3] = "%.2f grams" % round(int(helper[2][:-6])*0.1, 2)
                    helper[5] = "%.2f grams" % round(int(helper[4][:-6])*0.1, 2)
                    if "Gain 1" in helper[0]:
                        helper[0] = 1
                    elif "Gain 0.5"in helper[0]:
                        helper[0] = 0.5
                    elif "Lose 0.5"in helper[0]:
                        helper[0] = -0.5
                    elif "Lose 1"in helper[0]:
                        helper[0] = -1
                    else:
                        helper[0] = 0
                    table_array.append(helper)

            response.update({"data": table_array})
            response.update({"disclaimer": "The Food and Agriculture Organization and the World Health Organization "
                                           "jointly recommend 55% to 75% of total energy from carbohydrates, "
                                           "but only 10% directly from sugars."})

            return response

        return -1


# /proteina?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
class Proteina(Resource):
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade']:

            url = f"https://www.calculator.net/protein-calculator.html?ctype=metric&&cage={args['idade']}&csex={args['genero']}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={args['altura']}&ckg={args['peso']}&cactivity={ACTIVIDADE[args['atividade']][1]}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
            base_response = requests.get(url)
            html = BeautifulSoup(base_response.content, 'html.parser')

            #CDC based The Centers for Disease Control and Prevention
            paragraph = html.find_all('p')[2]

            data = paragraph.get_text("/").split("/")[1][:-6].split(" - ")
            response = {}

            response.update({"title": "Proteina diaria"})
            response.update({"data": data})
            response.update({"disclaimer": "Opiniao baseada no The Centers for Disease Control and Prevention"})

            return response

        return -1

# /full_model?altura=180&idade=20&genero=m&peso=60&atividade=leve
class Full_Model(Resource):
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade']:
            # Peso_Ideal
            # https://www.calculator.net/ideal-weight-calculator.html
            peso = Peso
            #
            endpoint = LOCAL_HOST + f"/peso?altura={args['altura']}&idade={args['idade']}&genero={args['genero']}"
            base_response = requests.get(endpoint)
            data_peso = base_response.json()

            # Calorias
            # /calorias?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
            # disclaimer:
            # Please consult with a doctor when losing 1 kg or more per week since it requires that you consume less than
            # the minimum recommendation of 1, 500 calories a day.
            calorias = Calorias
            #
            endpoint = LOCAL_HOST + f"/calorias?altura={args['altura']}&idade={args['idade']}&genero={args['genero']}&peso={args['peso']}&atividade={args['atividade']}"
            base_response = requests.get(endpoint)
            data_calorias = base_response.json()

            # Gordura & Gordura Saturada
            # https://www.calculator.net/ideal-weight-calculator.html
            gordura = Gordura
            #
            endpoint = LOCAL_HOST + f"/gordura?altura={args['altura']}&idade={args['idade']}&genero={args['genero']}&peso={args['peso']}&atividade={args['atividade']}"
            base_response = requests.get(endpoint)
            data_gordura = base_response.json()

            # Hidratos de carbono
            # https://www.calculator.net/ideal-weight-calculator.html
            gordura = Hidratos_De_Carbono
            #
            endpoint = LOCAL_HOST + f"/hidratos_de_carbono?altura={args['altura']}&idade={args['idade']}&genero={args['genero']}&peso={args['peso']}&atividade={args['atividade']}"
            base_response = requests.get(endpoint)
            data_hidratos_de_carbono = base_response.json()

            # Proteina
            # https://www.calculator.net/ideal-weight-calculator.html
            # opinion based on CDC based The Centers for Disease Control and Prevention
            gordura = Proteina
            #
            endpoint = LOCAL_HOST + f"/proteina?altura={args['altura']}&idade={args['idade']}&genero={args['genero']}&peso={args['peso']}&atividade={args['atividade']}"
            base_response = requests.get(endpoint)
            data_proteina = base_response.json()


            # return
            #
            full_model = {}

            full_model.update({"data_peso":data_peso})
            full_model.update({"data_calorias":data_calorias})
            full_model.update({"data_gordura":data_gordura})
            full_model.update({"data_hidratos_de_carbono":data_hidratos_de_carbono})
            full_model.update({"data_proteina":data_proteina})

            return full_model

        return -1


# /recipe

##
## Actually setup the Api resource routing here
##


api.add_resource(Peso, '/peso')
api.add_resource(Calorias, '/calorias')
api.add_resource(Gordura, '/gordura')
api.add_resource(Proteina, '/proteina')
api.add_resource(Hidratos_De_Carbono, '/hidratos_de_carbono')
api.add_resource(Full_Model, '/full_model')
api.add_resource(Recipe, '/recipe')
api.add_resource(User, '/user')


if __name__ == '__main__':
    #Database
    conn = DBManager()
    conn.populate_db()
    #main()
    app.run(debug=True,host="0.0.0.0")
