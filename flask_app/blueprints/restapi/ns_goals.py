import json
import re
from datetime import datetime, timezone
from enum import Enum

import peewee
import requests
from bs4 import *
from flask import Response, request
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import reqparse
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from ...classes.constants import ERROR_BIODATA_WEIGHT, ERROR_BIODATA_HEIGHT, ERROR_BIODATA_SEX, \
    ERROR_BIODATA_ACTIVITY_LEVEL
from ...classes.enums import USER_SEXES_TYPE
from ...classes.functions import calculate_age
from ...classes.models import User as UserDB, TokenBlocklist, Goal as GoalDB
from ...classes.schemas import LimitsSchema, GoalSchema, FitnessReport
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

api = Namespace("Goals", description="Here are all fitness endpoints")

ENDPOINT = "/goals"

parser = reqparse.RequestParser()
parser.add_argument('altura', location='args')
parser.add_argument('peso', location='args')
parser.add_argument('idade', location='args')
parser.add_argument('genero', location='args')
parser.add_argument('atividade', location='args')
parser.add_argument('task', location='args')

""" General """


@api.route('', methods=['POST', 'DELETE'])
class Goal(Resource):

    @jwt_required()
    def post(self):

        # Get json data
        log.info("POST /auth")

        # body
        json_data = request.get_json()

        # Validate args by loading it into schema

        try:
            goal_data = GoalSchema().load(json_data)
        except ValidationError as err:
            log.error(err.messages)

            return Response(status=400, response=json.dumps({"errors": err.messages}), mimetype="application/json")

        # Get auth User

        try:
            user = UserDB.get(get_jwt_identity())
        except peewee.DoesNotExist as e:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        # Check if user dont have any current goal
        # if he does delete it

        # Fill db object

        try:
            goal = GoalDB(**goal_data)
            goal.user = user
            goal.save()
        except Exception as e:
            log.error(e)
            return Response(status=400, response=json.dumps(e), mimetype="application/json")

        log.info("Finished POST /auth")
        return Response(status=201, response=json.dumps(GoalSchema().dump(goal)), mimetype="application/json")

    @jwt_required()
    def delete(self):
        """Delete a goal"""

        log.info("DELETE /comment")

        """ Get Auth User"""
        try:
            user = UserDB.get(get_jwt_identity())
        except peewee.DoesNotExist:
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("Client couldn't be found.")
            return Response(status=400, response="No user found by this id.")

        goal = user.goal

        user.goal = None
        user.save()

        goal.delete_instance()

        log.info("Finished DELETE /comment")
        return Response(status=200)


""" Calculations """

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


def get_calories_fat(altura, idade, genero, peso, atividade, fitness_report):
    url = f"https://www.calculator.net/fat-intake-calculator.html?ctype=metric&&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={atividade}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')
    table = html.find('table')

    for row in table.find_all("tr")[1:]:

        helper = row.get_text('/').split("/")
        if len(helper) > 5:
            helper.pop(1)

        """ Initial """

        generic_report = {
            "calories": None,
            "fat": None
        }

        """ Calories """

        calories = helper[1].strip()

        # Removing "Calories" from string
        calories = calories.split(" ")[0]

        # Replace "," to "."
        calories = calories.replace(",", "")

        if "-" in calories:
            calories = None

        generic_report.update({
            "calories": calories
        })

        """ Fat and Saturated Fat"""

        fat_twenty_thirty = helper[2]
        fat_twenty_thirty = fat_twenty_thirty.replace(" grams", "")
        fat_twenty_thirty = fat_twenty_thirty.split(" - ")
        fat_twenty_thirty = {
            "upper_limit": fat_twenty_thirty[1],
            "lower_limit": fat_twenty_thirty[0]
        }
        saturated_fat_ten = helper[3]
        saturated_fat_ten = saturated_fat_ten.replace(" grams", "")
        saturated_fat_ten = saturated_fat_ten.replace("<", "")

        saturated_fat_seven = helper[4]
        saturated_fat_seven = saturated_fat_seven.replace(" grams", "")
        saturated_fat_seven = saturated_fat_seven.replace("<", "")

        fat_report = {
            "fat_twenty_thirty": fat_twenty_thirty,
            "saturated_fat_ten": saturated_fat_ten,
            "saturated_fat_seven": saturated_fat_seven
        }

        generic_report.update({
            "fat": fat_report
        })

        """ Goals """

        if "Gain 1" in helper[0]:
            fitness_report.update({"plus": generic_report})
        elif "Gain 0.5" in helper[0]:
            fitness_report.update({"plus_half": generic_report})
        elif "Lose 0.5" in helper[0]:
            fitness_report.update({"minus_half": generic_report})
        elif "Lose 1" in helper[0]:
            fitness_report.update({"minus": generic_report})
        else:
            fitness_report.update({"maintain": generic_report})

    return fitness_report


def get_carbohydrates(altura, idade, genero, peso, atividade, fitness_report):
    """
        www.calculator.net is bugged somethings is multiple strings other times is an array wtv

    """
    url = f"https://www.calculator.net/carbohydrate-calculator.html?cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={atividade}&cmop=0&cformula=m&cfatpct=20&printit=0&ctype=metric&x=Calculate"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')

    """ Returns a Table """

    table = html.find(class_="cinfoT")

    if table:

        for row in table.find_all('tr')[1:]:

            rows = row.find_all(['td', 'th'])

            """ Initial """

            carbohydrates_report = {
                "forty_perc": None,
                "fifty_perc": None,
                "sixty_five_perc": None,
                "seventy_five_perc": None,
                "only_option": None
            }

            """ Carbohydrates """

            helper = []
            for cell in rows[1:]:
                helper.append(cell.get_text(strip=True).replace('\xa0', ' ').replace(',', '.').split(" ")[0])

            carbohydrates_report.update({
                "forty_perc": int(helper[1]),
                "fifty_perc": int(helper[2]),
                "sixty_five_perc": int(helper[3]),
                "seventy_five_perc": int(helper[4]),
            })

            """ Goals """

            goal = rows[0].get_text(strip=True)

            if "Lose 0.5" in goal:
                fitness_report["minus_half"].update({"carbohydrates": carbohydrates_report})

            elif "Lose 1" in goal:
                fitness_report["minus"].update({"carbohydrates": carbohydrates_report})

            elif "Gain 0.5" in goal:
                fitness_report["plus_half"].update({"carbohydrates": carbohydrates_report})

            elif "Gain 1" in goal:
                fitness_report["plus"].update({"carbohydrates": carbohydrates_report})

            else:
                fitness_report["maintain"].update({"carbohydrates": carbohydrates_report})


    else:

        """ Returns a String  """

        paragraphs = html.find_all('p', limit=6)[1:]

        for row in paragraphs:

            """ Initial """

            carbohydrates_report = {
                "forty_perc": None,
                "fifty_perc": None,
                "sixty_five_perc": None,
                "seventy_five_perc": None,
                "only_option": None
            }

            """ Carbohydrates """

            string = row.text

            # Remove all characters except numbers, commas, and hyphens

            # Split the string into an array using commas as separators
            values_array = re.findall(r'-?\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b', string)

            if len(values_array) == 3:
                carbohydrates_report.update({
                    "only_option": values_array[2],
                })
            elif len(values_array) == 8:
                carbohydrates_report.update({
                    "forty_perc": values_array[1],
                    "fifty_perc": values_array[2],
                    "sixty_five_perc": values_array[5],
                    "seventy_five_perc": values_array[7],
                })

            elif len(values_array) == 10:
                carbohydrates_report.update({
                    "forty_perc": values_array[2],
                    "fifty_perc": values_array[4],
                    "sixty_five_perc": values_array[7],
                    "seventy_five_perc": values_array[9],
                })

            """ Goals """

            if "lose 0.5" in string:
                fitness_report["minus_half"].update({"carbohydrates": carbohydrates_report})

            elif "lose 1" in string:
                fitness_report["minus"].update({"carbohydrates": carbohydrates_report})

            elif "gain 0.5" in string:
                fitness_report["plus_half"].update({"carbohydrates": carbohydrates_report})

            elif "gain 1" in string:
                fitness_report["plus"].update({"carbohydrates": carbohydrates_report})

            else:
                fitness_report["maintain"].update({"carbohydrates": carbohydrates_report})

    return fitness_report


def get_protein(altura, idade, genero, peso, atividade, fitness_report):
    url = f"https://www.calculator.net/protein-calculator.html?ctype=metric&&cage={idade}&csex={genero}&cheightfeet=5&cheightinch=10&cpound=165&cheightmeter={altura}&ckg={peso}&cactivity={atividade}&cmop=0&cformula=m&cfatpct=20&printit=0&x=66&y=11"
    base_response = requests.get(url)
    html = BeautifulSoup(base_response.content, 'html.parser')

    # CDC based The Centers for Disease Control and Prevention
    paragraph = html.find_all('p')[2]
    data = paragraph.get_text("/").split("/")[1][:-6].split(" - ")

    fitness_report["protein"] = {"upper_limit": data[1],
                                 "lower_limit": data[0]}
    return fitness_report


""" Endpoints """


@api.route('/weight', methods=['GET'])
class Weight(Resource):

    @jwt_required()
    def get(self):

        """ gets user auth id """
        user_logged_id = get_jwt_identity()

        """ check if user exist """
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

        return Response(status=200, response=json.dumps(
            get_peso(user_logged.height, calculate_age(user_logged.birth_date), user_logged.sex)),
                        mimetype="application/json")


@api.route('/full_model', methods=['GET'])
class FullModel(Resource):

    @jwt_required()
    def get(self):

        """ gets user auth id """
        user_logged_id = get_jwt_identity()

        """ check if user exist """
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

        height = user_logged.height
        weight = user_logged.weight
        activity_level = user_logged.activity_level

        errors = {}
        if user_logged.weight == -1:
            errors[ERROR_BIODATA_WEIGHT] = "User doesn't have weight set..."
        if user_logged.height == -1:
            errors[ERROR_BIODATA_HEIGHT] = "User doesn't have height set..."
        if user_logged.activity_level == -1:
            errors[ERROR_BIODATA_ACTIVITY_LEVEL] = "User doesn't have activity_level set..."
        if user_logged.sex is None:
            errors[ERROR_BIODATA_SEX] = "User's sex must be either female or male..."

        if errors:
            return Response(status=400, response=json.dumps({"errors":errors}))

        gender = user_logged.sex.lower()
        age = calculate_age(user_logged.birth_date)

        fitness_report = {
            "data_weight": {},
            "maintain": {},
            "minus_half": {},
            "minus": {},
            "plus_half": {},
            "plus": {}
        }

        """ Proccess Data_Weight of FitnessReport  """

        fitness_report.update({
            "ideal_weight": get_peso(height, age, gender)
        })

        """ Proccess Calories, Fat and Saturated fat of GenericReport from  FitnessReport """

        fitness_report = get_calories_fat(height, age, gender, weight, activity_level, fitness_report)

        """ Proccess Carbohydrates of GenericReport from  FitnessReport """

        fitness_report = get_carbohydrates(height, age, gender, weight, activity_level, fitness_report)

        """ Proccess Protein of GenericReport from  FitnessReport """

        fitness_report = get_protein(height, age, gender, weight, activity_level, fitness_report)

        return Response(status=200, response=FitnessReport().dumps(fitness_report), mimetype="application/json")
