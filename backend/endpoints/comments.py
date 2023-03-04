import peewee
from flask import request, Response
from flask_restful import Resource, reqparse
from flask_restful.representations import json
from playhouse.shortcuts import model_to_dict

from backend.dbManager import Recipe as RecipeDB, Preparation, Nutrition_Information, Tags, Ingredients, User as UserDB, \
    RecipesBackground

parser = reqparse.RequestParser()
parser.add_argument('page')
parser.add_argument('page_size')

TYPE_LIKE = "LIKE"

COMMENTS_ENDPOINT = "/comments/"

class Comments(Resource):

    def get(self):
        # Nota não precisa de paginação
        # Get args

        args = parser.parse_args()

        # Validate args

        try:
            if args['userUUID'] and args['userUUID'] != "":
                client_uuid = str(args['userUUID']).strip()
            else:
                return Response(status=400, response="Client UUID is missing.")
        except Exception as e:
            return Response(status=400, response="Client UUID is missing." + str(e))

        # Get user's liked recipes by uuid

        try:
            user_record = UserDB.get(uuid=client_uuid)

        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        try:
            liked_recipes = RecipesBackground.select().where(RecipesBackground.user == user_record,
                                                             RecipesBackground.type == TYPE_LIKE)
        except peewee.DoesNotExist:
            return Response(status=400, response="User does not exist...")

        body = [{"type": TYPE_LIKE,"client_uuid": client_uuid}]

        recipes = []
        for item in liked_recipes:
            recipe_record = model_to_dict(item.recipe)
            recipe_record['created_date'] = recipe_record['created_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipe_record['updated_date'] = recipe_record['updated_date'].strftime("%d/%m/%Y, %H:%M:%S")
            recipes.append(recipe_record)

        body.append(recipes)

        return Response(status=200, response=json.dumps(body), mimetype="application/json")

    def post(self):
        # Get json body

        data = request.get_json()

        # Validate args

        try:
            if data['client_uuid'] and data['client_uuid'] != "":
                client_uuid = str(data['client_uuid']).strip()
            else:
                return Response(status=400, response="Client UUID is missing.")
        except Exception as e:
            return Response(status=400, response="Client UUID is missing." + str(e))

        try:
            if data['recipe_id'] and data['recipe_id'] != "":
                recipe_id = str(data['recipe_id']).strip()
            else:
                return Response(status=400, response="Recipe id is missing.")
        except Exception as e:
            return Response(status=400, response="Recipe id is missing." + str(e))

        # Verify existence of the requested ids model's todo this will be later removed and be directly called by the user id

        try:
            user = UserDB.get(uuid=client_uuid)
        except peewee.DoesNotExist:
            return Response(status=400, response="Client uuid couln't be found")

        try:
            recipe = RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe id couln't be found")

        # Verifiyng inexistence of previous record

        recipe_background, created = RecipesBackground.get_or_create(user_id=user.id, recipe_id=recipe.id,
                                                                     type=TYPE_LIKE)

        # Filling like record

        if created:
            recipe_background.save()
            return Response(status=201, mimetype="application/json")
        else:
            return Response(status=400, response="This recipe have been already liked.")

    def delete(self):
        # Get args

        args = parser.parse_args()

        # Validate args

        try:
            if args['userUUID'] and args['userUUID'] != "":
                client_uuid = str(args['userUUID']).strip()
            else:
                return Response(status=400, response="Client UUID is missing.")
        except Exception as e:
            return Response(status=400, response="Client UUID is missing." + str(e))

        try:
            if args['recipe_id'] and args['recipe_id'] != "":
                recipe_id = str(args['recipe_id']).strip()
            else:
                return Response(status=400, response="Recipe id is missing.")
        except Exception as e:
            return Response(status=400, response="Recipe id is missing." + str(e))

        # Verify existence of the requested ids model's todo this will be later removed and be directly called by the user id

        try:
            user = UserDB.get(uuid=client_uuid)
        except peewee.DoesNotExist:
            return Response(status=400, response="Client uuid couln't be found.")

        # Delete like record

        try:
            like_record = RecipesBackground.get(user_id=user.id, recipe_id=recipe_id, type=TYPE_LIKE)
            like_record.delete_instance()
        except peewee.DoesNotExist:
            return Response(status=400, response="Like couln't be found.")
        return Response(status=204)