import json
from enum import Enum

import requests
from flask import Blueprint, Response
from flask_jwt_extended import jwt_required

from flask_restful import reqparse, Resource
from bs4 import *

ACTIVIDADE = {
    'absolutamente_nenhum': ['Taxa metabólica basal', 1],
    'sedentario': ['Pouco ou nenhum execício', 1.2],
    'leve': ['Execício de 1 a 3 vezes', 1.375],
    'moderado': ['Execício 4-5 vezes/semana', 1.465],
    'ativo': ['Execício diario ou exercícios intensos 3-4 vezes/semana', 1.55],
    'muito_ativo': ['Exercícios intensos 6-7 vezes/semana', 1.725],
    'extra_ativo': ['Execício intesso diário, ou te um trabalho muito fisico', 1.9]
}

class GENDER(Enum):
    MALE = "male"
    FEMALE = "female"


CALENDER_FITNESS_SET = GENDER._value2member_map_



parser = reqparse.RequestParser()
parser.add_argument('altura', location='args')
parser.add_argument('peso', location='args')
parser.add_argument('idade', location='args')
parser.add_argument('genero', location='args')
parser.add_argument('atividade', location='args')
parser.add_argument('task', location='args')

fitness_blueprint = Blueprint('fitness', __name__, url_prefix="/api/v1/fitness")

""" Functions """


def get_peso(altura, idade, genero):
    url = f"https://www.calculator.net/ideal-weight-calculator.html?ctype=metric&cage={idade}&csex={genero}&cheightmeter={altura} "
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')
    main_result = html.find(class_="cinfoT")
    table = main_result.find_all('tr')[-1]
    td = table.find_all("td")[1].text.split("-")
    low = td[0].strip()
    high = td[1].replace("kgs", "").strip()

    return_dict = [low, high]
    return return_dict


def get_calories(altura, idade, genero, peso, atividade):
    url = f"https://www.calculator.net/calorie-calculator.html?ctype=metric&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={ACTIVIDADE[atividade][1]}&cmop=0&coutunit=c&cformula=m&cfatpct=20&printit=0&x=75&y=20"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')
    table = html.find('table')

    table_array = []
    titles = []
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


def get_fat(altura, idade, genero, peso, atividade):
    url = f"https://www.calculator.net/fat-intake-calculator.html?ctype=metric&&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={ACTIVIDADE[atividade][1]}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')
    table = html.find('table')

    table_array = []
    response = {}
    first_time = True
    for row in table.find_all("tr"):
        if first_time:
            response.update({"titles": row.get_text('/').split("/")})
            first_time = False
        else:
            helper = row.get_text('/').split("/")
            if len(helper) > 5:
                helper.pop(1)

            if "Gain 1" in helper[0]:
                helper[0] = 1
            elif "Gain 0.5" in helper[0]:
                helper[0] = 0.5
            elif "Lose 0.5" in helper[0]:
                helper[0] = -0.5
            elif "Lose 1" in helper[0]:
                helper[0] = -1
            else:
                helper[0] = 0
            table_array.append(helper)

    response.update({"data": table_array})

    return response


def get_carbohydrates(altura, idade, genero, peso, atividade):


    url = f"https://www.calculator.net/carbohydrate-calculator.html?ctype=metric&&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={ACTIVIDADE[atividade][1]}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')
    table = html.find('table')

    table_array = []
    response = {}
    first_time = True
    for row in table.find_all("tr"):
        if first_time:
            helper = row.get_text('/').split(("/"))

            response.update({"titles": [helper[0], helper[1], "Min", "Sugar", "Max", "Sugar"]})

            first_time = False
        else:
            helper = row.get_text('/').replace('\xa0', ' ').split(("/"))
            if 'week' in helper:
                helper.pop(1)
            helper.pop(2)
            helper.pop(2)
            helper.pop(4)
            helper.pop(4)
            helper[3] = "%.2f grams" % round(int(helper[2][:-6]) * 0.1, 2)
            helper[5] = "%.2f grams" % round(int(helper[4][:-6]) * 0.1, 2)
            if "Gain 1" in helper[0]:
                helper[0] = 1
            elif "Gain 0.5" in helper[0]:
                helper[0] = 0.5
            elif "Lose 0.5" in helper[0]:
                helper[0] = -0.5
            elif "Lose 1" in helper[0]:
                helper[0] = -1
            else:
                helper[0] = 0
            table_array.append(helper)

    response.update({"data": table_array})
    response.update({"disclaimer": "The Food and Agriculture Organization and the World Health Organization "
                                   "jointly recommend 55% to 75% of total energy from carbohydrates, "
                                   "but only 10% directly from sugars."})

    return response


def get_protein(altura, idade, genero, peso, atividade):
    url = f"https://www.calculator.net/protein-calculator.html?ctype=metric&&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={ACTIVIDADE[atividade][1]}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')

    # CDC based The Centers for Disease Control and Prevention
    paragraph = html.find_all('p')[2]

    data = paragraph.get_text("/").split("/")[1][:-6].split(" - ")
    response = {}

    response.update({"title": "Proteina diaria"})
    response.update({"data": data})
    response.update({"disclaimer": "Opiniao baseada no The Centers for Disease Control and Prevention"})

    return response


""" Endpoints """


@fitness_blueprint.route('/weight', methods=['GET'])
@jwt_required()
def weight():
    args = parser.parse_args()

    if args['altura'] and args['idade'] and args['genero']:
        ## maybe we need some kinda of validation here

        response = json.dumps(get_peso(args['altura'], args['idade'], args['genero']))
        return Response(status=200, response=response)

    return Response(status=400)


# /calorias?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
@fitness_blueprint.route('/calories', methods=['GET'])
@jwt_required()
def calories():
    args = parser.parse_args()

    if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade'] and args[
        'atividade'] in ACTIVIDADE:

        response = json.dumps(
            get_calories(args['altura'], args['idade'], args['genero'], args['peso'], args['atividade']))
        return Response(status=200, response=response)

    return Response(status=400)


# /gordura?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
@fitness_blueprint.route('/fat', methods=['GET'])
@jwt_required()
def fat():
    args = parser.parse_args()

    if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade'] and args[
        'atividade'] in ACTIVIDADE:
        response= json.dumps(
            get_fat(args['altura'], args['idade'], args['genero'], args['peso'], args['atividade']))
        return Response(status=200, response=response)

    return Response(status=400)


# /hidratos_de_carbono?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
@fitness_blueprint.route('/carbohydrates', methods=['GET'])
@jwt_required()
def carbohydrates():
    args = parser.parse_args()

    if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade'] and args[
        'atividade'] in ACTIVIDADE:
        response = json.dumps(
            get_carbohydrates(args['altura'], args['idade'], args['genero'], args['peso'], args['atividade']))
        return Response(status=200, response=response)

    return Response(status=400)


# /proteina?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
@fitness_blueprint.route('/protein', methods=['GET'])
@jwt_required()
def protein():
    args = parser.parse_args()

    if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade'] and args[
        'atividade'] in ACTIVIDADE:
        response = json.dumps(
            get_protein(args['altura'], args['idade'], args['genero'], args['peso'], args['atividade']))
        return Response(status=200, response=response)

    return Response(status=400)


# /full_model?altura=180&idade=20&genero=m&peso=60&atividade=leve
# condições
# 120 < args['altura'] < 250
# 16 < args['idade'] < 80


@fitness_blueprint.route('/full_model', methods=['GET'])
@jwt_required()
def full_model():
    args = parser.parse_args()

    try:
        altura = float(args['altura'])
        idade = int(args['idade'])
    except:
        return Response(status=400)

    if 1.2 < altura < 2.5:
        altura = altura * 100

    if altura and 120 < altura < 250 and idade and 16 < idade < 80 and args['genero'] and args['genero'] in CALENDER_FITNESS_SET and args['peso'] and args['atividade'] and args[
        'atividade'] in ACTIVIDADE:
        full_model_response = {}



        full_model_response.update({"data_peso":get_peso(altura, idade, args['genero']) })

        full_model_response.update({"data_calorias": get_calories(altura, idade, args['genero'],
                                                                  args['peso'], args['atividade'])})
        full_model_response.update({"data_gordura": get_fat(altura, idade, args['genero'],
                                                                  args['peso'], args['atividade'])})
        full_model_response.update({"data_hidratos_de_carbono": get_carbohydrates(altura, idade, args['genero'],
                                                                  args['peso'], args['atividade'])})
        full_model_response.update({"data_proteina": get_protein(altura, idade, args['genero'],
                                                                  args['peso'], args['atividade'])})

        return Response(status=200, response=json.dumps(full_model_response))

    return Response(status=400)
