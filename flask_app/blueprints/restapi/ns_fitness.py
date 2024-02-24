import json
import re
from datetime import datetime, timezone
from enum import Enum

import peewee
import requests
from bs4 import *
from flask import Response
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import reqparse
from flask_restx import Namespace, Resource
from typing import List, Tuple

from ...classes.enums import USER_SEXES_TYPE
from ...classes.models import User as UserDB, TokenBlocklist
from ...classes.schemas import GenericReport, CarboHydrateReportSchema, CarboHydrateReportRowSchema, \
    ProteinReportSchema, LimitsSchema
from ...ext.logger import log

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

api = Namespace("Fitness", description="Here are all fitness endpoints")

ENDPOINT = "/fitness"

parser = reqparse.RequestParser()
parser.add_argument('altura', location='args')
parser.add_argument('peso', location='args')
parser.add_argument('idade', location='args')
parser.add_argument('genero', location='args')
parser.add_argument('atividade', location='args')
parser.add_argument('task', location='args')

""" Functions """


def get_peso(altura, idade, genero):
    """
        www.calculator.net can return or a table or a string

    """

    url = f"https://www.calculator.net/ideal-weight-calculator.html?ctype=metric&cage={idade}&csex={genero}&cheightmeter={altura} "
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')

    """ returns a String """

    result = html.find('p', class_='bigtext')

    if result:
        # Define the regex pattern to match decimal numbers
        pattern = r'(\d+\.\d+)\s*-\s*(\d+\.\d+)\s*kgs?'

        # Find all matches in the text
        matches = re.findall(pattern, result.text)

        if not matches:
            log.error(f"[{get_peso.__name__}] : None matches were found. (string : {result.text})")
            return -1, []



    else:
        """ returns a Table """
        main_result = html.find(class_="cinfoT")

        if not main_result:
            log.error(
                f"[{get_peso.__name__}] : Unable to find matches in neither string or table responses. ( Responses may have change)")
            return -1, []

        result_string = main_result.find_all('tr')[-1].text

        # Define the regex pattern to match decimal numbers
        pattern = r'(\d+\.\d+)\s*-\s*(\d+\.\d+)\s*kgs?'

        # Find all matches in the text
        matches = re.findall(pattern, result_string)

        if not matches:
            log.error(f"[{get_peso.__name__}] : None matches were found. (string : {result_string})")
            return -1, []

    return LimitsSchema().load({
        "upper_limit": matches[0][1],
        "lower_limit": matches[0][0]
    })


def get_calories_fat(altura, idade, genero, peso, atividade):
    url = f"https://www.calculator.net/fat-intake-calculator.html?ctype=metric&&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={atividade}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')
    table = html.find('table')

    table_array = []
    titles = {}
    first_time = True
    for row in table.find_all("tr"):
        if first_time:
            titles = row.get_text('/').split("/")
            first_time = False
        else:
            helper = row.get_text('/').split("/")
            if len(helper) > 5:
                helper.pop(1)

            if "Gain 1" in helper[0]:
                helper[0] = "1"
            elif "Gain 0.5" in helper[0]:
                helper[0] = "0.5"
            elif "Lose 0.5" in helper[0]:
                helper[0] = "-0.5"
            elif "Lose 1" in helper[0]:
                helper[0] = "-1"
            else:
                helper[0] = "0"
            table_array.append(helper)

    return GenericReport().load({"titles": titles, "data": sorted(table_array, key=lambda x: x[0])})


def get_carbohydrates(altura, idade, genero, peso, atividade):
    """
        www.calculator.net is bugged somethings is multiple strings other times is an array wtv

    """
    url = f"https://www.calculator.net/carbohydrate-calculator.html?cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={atividade}&cmop=0&cformula=m&cfatpct=20&printit=0&ctype=metric&x=Calculate"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')

    table_array = []
    titles = []
    first_time = True

    """ returns a Table """

    table = html.find(class_="cinfoT")

    if table:

        table_array = []
        for row in table.find_all('tr'):

            if first_time:
                row_data = []
                for cell in row:
                    row_data.append(cell.get_text(strip=True).replace('\xa0', ' '))
                titles = row_data
                first_time = False
            else:
                row_data = []
                rows = row.find_all(['td', 'th'])

                goal = rows[0].get_text(strip=True)
                if "Gain 1" in goal:
                    row_data.append("1")
                elif "Gain 0.5" in goal:
                    row_data.append("0.5")
                elif "Lose 0.5" in goal:
                    row_data.append("-0.5")
                elif "Lose 1" in goal:
                    row_data.append("-1")
                else:
                    row_data.append("0")

                for cell in rows[1:]:
                    row_data.append(cell.get_text(strip=True).replace('\xa0', ' '))
                table_array.append(row_data)

    else:

        """ returns a String  """

        paragraphs = html.find_all('p', limit=6)[1:]
        titles = ['Goal', 'Daily Calorie Allowance', '40%*', '55%*', '65%*', '75%*']
        table_array = []

        for row in paragraphs:

            string = row.text

            if "lose 0.5" in string:
                goal = -0.5

            elif "lose 1" in string:
                goal = -1

            elif "gain 0.5" in string:
                goal = 0.5

            elif "gain 1" in string:
                goal = 1

            else:
                goal = 0

            # Remove all characters except numbers, commas, and hyphens

            # Split the string into an array using commas as separators
            values_array = re.findall(r'-?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b', string)

            if len(values_array) == 3:
                table_array.append({
                    "goal": goal,
                    "daily_calorie_allowance": values_array[0],
                    "only_option": values_array[2],
                })
            elif len(values_array) == 8:
                table_array.append({
                    "goal": goal,
                    "daily_calorie_allowance": float(values_array[0].replace(',', '')),
                    "forty_perc": values_array[1],
                    "fifty_perc": values_array[2],
                    "sixty_five_perc": values_array[5],
                    "seventy_five_perc": values_array[7],
                })

            elif len(values_array) == 10:
                table_array.append({
                    "goal": goal,
                    "daily_calorie_allowance": float(values_array[0].replace(',', '')),
                    "forty_perc": values_array[2],
                    "fifty_perc": values_array[4],
                    "sixty_five_perc": values_array[7],
                    "seventy_five_perc": values_array[9],
                })

    return CarboHydrateReportSchema().load({"titles": titles, "data": table_array})


def get_protein(altura, idade, genero, peso, atividade):
    url = f"https://www.calculator.net/protein-calculator.html?ctype=metric&&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={atividade}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')

    # CDC based The Centers for Disease Control and Prevention
    paragraph = html.find_all('p')[2]

    data = paragraph.get_text("/").split("/")[1][:-6].split(" - ")
    response = {}

    response.update({"title": "Proteina diaria"})
    response.update({"data": data})
    response.update({"disclaimer": "Opiniao baseada no The Centers for Disease Control and Prevention"})

    return ProteinReportSchema().load({
        "titles": ["Proteina diaria"],
        "data":
            {"upper_limit": data[0],
             "lower_limit": data[1]},
        "disclaimer": "Opiniao baseada no The Centers for Disease Control and Prevention"

    })


""" Endpoints """


@api.route('/weight', methods=['GET'])
class Weight(Resource):

    @jwt_required()
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero']:
            ## maybe we need some kinda of validation here
            return Response(status=200, response=json.dumps(get_peso(args['altura'], args['idade'], args['genero'])))

        return Response(status=400)


# /gordura?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
@api.route('/calories', methods=['GET'])
class Calories(Resource):

    @jwt_required()
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade'] and args[
            'atividade'] in ACTIVIDADE:
            response = json.dumps(
                get_calories_fat(args['altura'], args['idade'], args['genero'], args['peso'], args['atividade']))
            return Response(status=200, response=response)

        return Response(status=400)


# /hidratos_de_carbono?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
@api.route('/carbohydrates', methods=['GET'])
class Carbohydrates(Resource):
    @jwt_required()
    def get(self):
        args = parser.parse_args()

        if args['altura'] and args['idade'] and args['genero'] and args['peso'] and args['atividade'] and args[
            'atividade'] in ACTIVIDADE:
            response = json.dumps(
                get_carbohydrates(args['altura'], args['idade'], args['genero'], args['peso'], args['atividade']))
            return Response(status=200, response=response)

        return Response(status=400)


# /proteina?altura=180&idade=20&peso=80&genero=m&atividade=extra_ativo
@api.route('/protein', methods=['GET'])
class Protein(Resource):
    @jwt_required()
    def get(self):
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


@api.route('/full_model', methods=['GET'])
class FullModel(Resource):

    @jwt_required()
    def get(self):

        user_logged_id = get_jwt_identity()

        # check if user exists
        try:
            user_logged = UserDB.get(user_logged_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and still reach this far)
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couldn't be found by this id.")
            return Response(status=400, response="User couldn't be found by this id.")

        if user_logged.weight != -1 and user_logged.height != -1 and user_logged.activity_level != -1 \
                and user_logged.sex != USER_SEXES_TYPE.NOT_ASSIGN.value:
            height = user_logged.height
            weight = user_logged.weight
            activity_level = user_logged.activity_level
            gender = user_logged.sex.lower()
            current_date = datetime.now()
            age = current_date.year - user_logged.birth_date.year - ((current_date.month, current_date.day) < (
                user_logged.birth_date.month, user_logged.birth_date.day))

            full_model_response = {}

            full_model_response.update({"data_peso": get_peso(height, age, gender)})
            full_model_response.update({"data_gordura": get_calories_fat(height, age, gender,
                                                                         weight, activity_level)})
            full_model_response.update({"data_hidratos_de_carbono": get_carbohydrates(height, age, gender,
                                                                                      weight, activity_level)})
            full_model_response.update({"data_proteina": get_protein(height, age, gender,
                                                                     weight, activity_level)})

            return Response(status=200, response=json.dumps(full_model_response), mimetype="application/json")

        return Response(status=400)
