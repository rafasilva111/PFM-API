import json
import math
from datetime import datetime, timezone

import peewee
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from .errors import return_error_sql
from ...classes.functions import block_user_session_id
from ...classes.models import User as UserDB, ShoppingList as ShoppingListDB, \
    ShoppingIngredient as ShoppingIngredientDB, Ingredient as IngredientDB, USER_TYPE
from ...classes.schemas import ShoppingListSchema, build_metadata, ShoppingListPatchSchema
from ...ext.logger import log

api = Namespace("calendar", description="Here are all comment endpoints")

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument("id", type=int, help="ID of the calendar to delete")
parser.add_argument('date', type=str, help='The date.')
parser.add_argument('from_date', type=str, help='The left date delimiter.')
parser.add_argument('to_date', type=str, help='The right date delimiter.')  # 'dd/mm/yyyy'
parser.add_argument('archived', type=int, help='The right date delimiter.')  # 'dd/mm/yyyy'

ENDPOINT = "/shopping_list"

NORMAL_USER_MAX_SHOPPING_LIST = 1
VIP_USER_MAX_SHOPPING_LIST = 8


@api.route("")
class ShoppingListResource(Resource):
    @jwt_required()
    def get(self):
        """
        Retrieve shopping list(s) for the user.
        """
        log.info("Entering GET /shopping_list endpoint")
        args = parser.parse_args()
        user_id = get_jwt_identity()
        page = args['page'] if args['page'] else 1
        page_size = args['page_size'] if args['page_size'] else 5
        id = args['id'] if args['id'] else None
        archived = args['archived'] if args['archived'] and 1 >= args['archived'] >= 0 else None

        try:
            user = UserDB.get(UserDB.id == user_id)
        except peewee.DoesNotExist:
            block_user_session_id()
            log.error("User couldn't be found.")
            return Response(status=400, response="User couldn't be found.")

        response_holder = {}

        if id:
            try:
                query = ShoppingListDB.get((ShoppingListDB.id == args["id"]) & (ShoppingListDB.user == user))
            except peewee.DoesNotExist:
                log.error("Shopping list couldn't be found.")
                return Response(status=400, response="Shopping list couldn't be found.")

            response_holder = ShoppingListSchema().dump(query, backrefs=True, recurse=True, manytomany=True)
        elif archived:
            query = ShoppingListDB.select().where((ShoppingListDB.user == user) & (ShoppingListDB.archived == archived))
            total_shopping_lists = int(query.count())
            total_pages = math.ceil(total_shopping_lists / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_shopping_lists, ENDPOINT)
            response_holder["_metadata"] = metadata

            shopping_list_data = []
            for shopping_list in query.paginate(page, page_size):
                shopping_list_schema = ShoppingListSchema().dump(shopping_list)
                shopping_list_data.append(shopping_list_schema)
        else:
            query = ShoppingListDB.select().where((ShoppingListDB.user == user) & (ShoppingListDB.archived == False))
            total_shopping_lists = int(query.count())
            total_pages = math.ceil(total_shopping_lists / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_shopping_lists, ENDPOINT)
            response_holder["_metadata"] = metadata

            shopping_list_data = []
            for shopping_list in query.paginate(page, page_size):
                shopping_list_schema = ShoppingListSchema().dump(shopping_list)
                shopping_list_data.append(shopping_list_schema)

            response_holder["result"] = shopping_list_data

        log.info("Exiting GET /shopping_list endpoint")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    @jwt_required()
    def post(self):
        """
        Create a new shopping list entry.
        """
        log.info("Entering POST /shopping_list endpoint")
        user_id = get_jwt_identity()
        json_data = request.get_json()

        try:
            shopping_list_validated = ShoppingListSchema().load(json_data)
        except ValidationError as err:
            log.error("Invalid arguments: %s", err.messages)
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            block_user_session_id()
            log.error("User couldn't be found.")
            return Response(status=400, response="User couldn't be found.")

        # check if user is premium

        number_of_active_shopping_list = ShoppingListDB().select().where(
            (ShoppingListDB.user == user) & (ShoppingListDB.archived == False)).count()

        if user.user_type == USER_TYPE.VIP.value and number_of_active_shopping_list >= VIP_USER_MAX_SHOPPING_LIST:
            return Response(status=403, response=f'This user can´t have more shopping list´s.')
        elif user.user_type == USER_TYPE.NORMAL.value and number_of_active_shopping_list >= NORMAL_USER_MAX_SHOPPING_LIST:
            return Response(status=403, response=f'This user can´t have more shopping list´s.')

        shopping_list_query = ShoppingListDB(name=shopping_list_validated["name"], user=user)
        shopping_list_query.save()

        for item in shopping_list_validated['shopping_ingredients'].copy():
            shopping_ingredient_model = ShoppingIngredientDB(**item)

            try:
                ingredient_query = IngredientDB.get(item["ingredient"]["id"])
            except peewee.DoesNotExist:
                log.error("Ingredient quantity ID not found: %s", item["ingredient"]["id"])
                shopping_list_query.delete_instance()
                return Response(status=400,
                                response=f'Ingredient quantity couldnt be found by this id: {item["ingredient"]["id"]}')

            shopping_ingredient_model.ingredient = ingredient_query
            shopping_ingredient_model.shopping_list = shopping_list_query
            shopping_ingredient_model.save()

        log.info("Exiting POST /shopping_list endpoint")
        shopping_list_schema = ShoppingListSchema().dump(shopping_list_query)
        return Response(status=201, response=json.dumps(shopping_list_schema), mimetype="application/json")

    @jwt_required()
    def put(self):
        """
        Patch a user by ID.
        """
        log.info("PATCH /shopping_list")
        user_id = get_jwt_identity()
        args = parser.parse_args()
        id = args['id'] if args['id'] else None

        if not id:
            return Response(status=400, response="Id must be supplied.")

        try:
            user_query = UserDB.get(user_id)
        except peewee.DoesNotExist:
            block_user_session_id()
            log.error("User couldn't be found by this id.")
            return Response(status=400, response=f'User couldnt be found by this id: {user_id}.')

        try:
            shopping_list_query = ShoppingListDB.get(
                (ShoppingListDB.id == args["id"]) & (ShoppingListDB.user == user_query))
        except peewee.DoesNotExist:
            log.error("Shopping list couldn't be found by this id.")
            return Response(status=400, response=f'Shopping list couldnt be found by this id: {args["id"]}')

        data = request.get_json()

        try:
            shopping_list_schema = ShoppingListPatchSchema().load(data)
        except Exception as e:
            log.error("Error validating user: " + str(e))
            return Response(status=400, response="Error patching user: " + str(e))

        try:
            if 'name' in shopping_list_schema:
                shopping_list_query.name = shopping_list_schema['name']
            if 'archived' in shopping_list_schema:
                shopping_list_query.archived = shopping_list_schema['archived']
            if 'shopping_ingredients' in shopping_list_schema:
                for item in shopping_list_query.shopping_ingredients:
                    item.delete_instance()

                for item in shopping_list_schema['shopping_ingredients'].copy():
                    shopping_ingredient_model = ShoppingIngredientDB(**item)

                    try:
                        ingredient_query = IngredientDB.get(item["ingredient"]["id"])
                    except peewee.DoesNotExist:
                        log.error("Ingredient quantity ID not found: %s", item["ingredient"]["id"])
                        shopping_list_query.delete_instance()
                        return Response(status=400,
                                        response=f'Ingredient quantity couldnt be found by this id: {item["ingredient"]["id"]}')

                    shopping_ingredient_model.ingredient = ingredient_query
                    shopping_ingredient_model.shopping_list = shopping_list_query
                    shopping_ingredient_model.save()

            shopping_list_query.updated_date = datetime.now(timezone.utc)
            shopping_list_query.save()

        except Exception as e:
            log.error(return_error_sql(str(e)))
            return return_error_sql(str(e))

        log.info("Finished PATCH /shopping_list")
        return Response(status=200, response=json.dumps(ShoppingListSchema().dump(shopping_list_query)),
                        mimetype="application/json")

    @jwt_required()
    def delete(self):
        """
        Delete a calendar with a specific ID.
        """
        log.info("DELETE /calendar")
        args = parser.parse_args()
        user_id = get_jwt_identity()

        try:
            user_model = UserDB.get(UserDB.id == user_id)
        except peewee.DoesNotExist:
            block_user_session_id()
            log.error("Client couldn't be found.")
            return Response(status=400, response="Client couldn't be found.")

        if not args["id"]:
            log.error("Invalid arguments: 'id' is missing.")
            return Response(status=400, response="Invalid arguments: 'id' is missing.")

        try:
            shopping_list_model = ShoppingListDB.get(id=args["id"], user=user_model.id)
        except peewee.DoesNotExist:
            log.error("Shopping list does not exist.")
            return Response(status=400, response="Shopping list does not exist.")

        shopping_list_model.delete_instance()

        response_data = {"id": args["id"]}

        log.info("Finish DELETE /shopping_list")

        return Response(status=200, response=json.dumps(response_data),
                    mimetype="application/json")
