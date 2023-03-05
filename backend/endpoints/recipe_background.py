import datetime
import json
import math

import peewee
from flask import request, Response, jsonify
from flask_restful import reqparse, Resource, abort
from playhouse.shortcuts import model_to_dict, dict_to_model
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.dbManager import Recipe as RecipeDB, Preparation, Nutrition_Information, Tags, User as UserDB, \
    RecipesBackground
from backend.dtos import RecipeDTO

parser = reqparse.RequestParser()
parser.add_argument('page')
parser.add_argument('page_size')
parser.add_argument('recipe_id')
parser.add_argument('type')

RECIPE_BACKGROUND_LIKES_ENDPOINT = "/recipe_background/likes"
RECIPE_BACKGROUND_SAVES_ENDPOINT = "/recipe_background/saves"
RECIPE_BACKGROUND_CREATES_ENDPOINT = "/recipe_background/creates"

TYPE_LIKE = "LIKE"
TYPE_CREATED = "CREATED"
TYPE_SAVED = "SAVED"
TYPE = [TYPE_LIKE, TYPE_CREATED, TYPE_SAVED]


class Recipe_Background_Likes(Resource):

    @jwt_required()
    def get(self):
        # Nota não precisa de paginação

        # gets user auth id
        user_id = get_jwt_identity()

        # Get user's liked recipes by id

        try:
            user_record = UserDB.get(id=user_id)

        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        try:
            liked_recipes = RecipesBackground.select().where(RecipesBackground.user == user_record,
                                                             RecipesBackground.type == TYPE_LIKE)
        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        body = [{"type": TYPE_LIKE,"client_id": user_id}]

        recipes = []
        for item in liked_recipes:
            recipe_record = model_to_dict(item.recipe)
            recipe_record['created_date'] = recipe_record['created_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipe_record['updated_date'] = recipe_record['updated_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipes.append(recipe_record)

        body.append(recipes)


        return Response(status=200, response=json.dumps(body), mimetype="application/json")

    @jwt_required()
    def post(self):
        # Get json body

        data = request.get_json()

        # gets user auth id

        user_id = get_jwt_identity()

        # Validate args

        try:
            if data['recipe_id'] and data['recipe_id'] != "":
                recipe_id = str(data['recipe_id']).strip()
            else:
                return Response(status=400, response="Recipe id is missing.")
        except Exception as e:
            return Response(status=400, response="Recipe id is missing." + str(e))

        # Verify existence of the requested ids model's

        try:
            recipe = RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe id couln't be found")


        # Verifiyng inexistence of previous record

        recipe_background, created = RecipesBackground.get_or_create(user_id=user_id, recipe_id=recipe.id,
                                                                     type=TYPE_LIKE)

        # Filling like record

        if created:
            recipe_background.save()
            return Response(status=201, mimetype="application/json")
        else:
            return Response(status=400, response="This recipe have been already liked.")

    @jwt_required()
    def delete(self):
        # Get args

        args = parser.parse_args()

        # Validate args

        try:
            if args['recipe_id'] and args['recipe_id'] != "":
                recipe_id = str(args['recipe_id']).strip()
            else:
                return Response(status=400, response="Recipe id is missing.")
        except Exception as e:
            return Response(status=400, response="Recipe id is missing." + str(e))

        # gets user auth id

        user_id = get_jwt_identity()

        # Delete like record

        try:
            like_record = RecipesBackground.get(user_id=user_id, recipe_id=recipe_id, type=TYPE_LIKE)
            like_record.delete_instance()
        except peewee.DoesNotExist:
            return Response(status=400, response="Like couln't be found.")
        return Response(status=204)


class Recipe_Background_Saves(Resource):

    @jwt_required()
    def get(self):
        # Nota não precisa de paginação

        # gets user auth id

        user_id = get_jwt_identity()

        # Get user's liked recipes by id

        try:
            user_record = UserDB.get(id=user_id)

        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        # Get user's liked recipes by id

        try:
            saved_recipe = RecipesBackground.select().where(RecipesBackground.user == user_record,
                                                            RecipesBackground.type == TYPE_SAVED)
        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        body = [{"type": TYPE_SAVED, "client_id": user_id}]

        recipes = []

        for item in saved_recipe:
            recipe_record = model_to_dict(item.recipe)
            recipe_record['created_date'] = recipe_record['created_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipe_record['updated_date'] = recipe_record['updated_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipes.append(recipe_record)

        body.append(recipes)

        return Response(status=200, response=json.dumps(body), mimetype="application/json")

    @jwt_required()
    def post(self):
        # Get json body

        data = request.get_json()

        # gets user auth id

        user_id = get_jwt_identity()

        # Validate args

        try:
            if data['recipe_id'] and data['recipe_id'] != "":
                recipe_id = str(data['recipe_id']).strip()
            else:
                return Response(status=400, response="Recipe id is missing.")
        except Exception as e:
            return Response(status=400, response="Recipe id is missing." + str(e))

        # Verify existence of the requested ids model's

        try:
            recipe = RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe id couln't be found")

        # Verifiyng inexistence of previous record

        recipe_background, created = RecipesBackground.get_or_create(user_id=user_id, recipe_id=recipe.id,
                                                                     type=TYPE_SAVED)

        # Filling save record

        if created:
            recipe_background.save()
            return Response(status=201)
        else:
            return Response(status=400, response="This recipe have been already liked.")

    @jwt_required()
    def delete(self):
        # Get args

        args = parser.parse_args()

        # gets user auth id

        user_id = get_jwt_identity()

        # Validate args

        try:
            if args['recipe_id'] and args['recipe_id'] != "":
                recipe_id = str(args['recipe_id']).strip()
            else:
                return Response(status=400, response="Recipe id is missing.")
        except Exception as e:
            return Response(status=400, response="Recipe id is missing." + str(e))

        # Verify existence of the requested ids model's

        try:
            RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe couln't be found")

        # Delete save record

        try:
            save_record = RecipesBackground.get(user_id=user_id, recipe_id=recipe_id, type=TYPE_SAVED)
            save_record.delete_instance()
        except peewee.DoesNotExist:
            return Response(status=400, response="Like couln't be found")

        return Response(status=204)


class Recipe_Background_Creates(Resource):
    response_placeholder = {
        "_metadata":
            {
                "page": 5,
                "page_count": 20,
                "per_page": 20,
                "total_count": 521,
                "Links": [
                    {"self": f"/{RECIPE_BACKGROUND_CREATES_ENDPOINT}?page=5&per_page=20"},
                    {"first": f"/{RECIPE_BACKGROUND_CREATES_ENDPOINT}?page=0&per_page=20"},
                    {"previous": f"/{RECIPE_BACKGROUND_CREATES_ENDPOINT}?page=4&per_page=20"},
                    {"next": f"/{RECIPE_BACKGROUND_CREATES_ENDPOINT}?page=6&per_page=20"},
                    {"last": f"/{RECIPE_BACKGROUND_CREATES_ENDPOINT}?page=26&per_page=20"},
                ]
            },
        "results": []
    }

    @jwt_required()
    def get(self):
        # Nota não precisa de paginação

        # gets user auth id

        user_id = get_jwt_identity()

        # Get user's created recipes by uuid

        try:
            user_record = UserDB.get(id=user_id)

        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        try:
            saved_recipe = RecipesBackground.select().where(RecipesBackground.user == user_record,
                                                            RecipesBackground.type == TYPE_CREATED)
        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        body = [{"type": TYPE_CREATED, "user_id": user_id}]
        recipes = []

        for item in saved_recipe:
            recipe_record = model_to_dict(item.recipe)
            recipe_record['created_date'] = recipe_record['created_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipe_record['updated_date'] = recipe_record['updated_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipes.append(recipe_record)

        body.append(recipes)

        return Response(status=200, response=json.dumps(recipes), mimetype="application/json")
