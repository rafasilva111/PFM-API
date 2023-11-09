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
    ShoppingIngredient as ShoppingIngredientDB, Ingredient as IngredientDB, USER_TYPE, Notification
from ...classes.schemas import ShoppingListSchema, build_metadata, ShoppingListPatchSchema, NotificationSchema
from ...ext.logger import log

api = Namespace("calendar", description="Here are all comment endpoints")

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument("id", type=int, help="ID of the calendar to delete")

ENDPOINT = "/notification"


@api.route("/list")
class ShoppingListResource(Resource):
    @jwt_required()
    def get(self):
        """
        Retrieve user's notifications.
        """
        log.info("Entering GET /notification endpoint")
        args = parser.parse_args()
        user_id = get_jwt_identity()
        page = args['page'] if args['page'] else 1
        page_size = args['page_size'] if args['page_size'] else 5

        try:
            user = UserDB.get(UserDB.id == user_id)
        except peewee.DoesNotExist:
            block_user_session_id()
            log.error("User couldn't be found.")
            return Response(status=400, response="User couldn't be found.")

        response_holder = {}

        query = Notification.select().where((Notification.user == user)).order_by(Notification.created_date)
        total_shopping_lists = int(query.count())
        total_pages = math.ceil(total_shopping_lists / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_shopping_lists, ENDPOINT)
        response_holder["_metadata"] = metadata

        response_holder["result"] = []
        for notification in query.paginate(page, page_size):
            response_holder["result"].append(NotificationSchema().dump(notification))

        log.info("Exiting GET /notification endpoint")

        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

@api.route("")
class ShoppingListResource(Resource):

    @jwt_required()
    def get(self):
        """
        Retrieve user's notifications.
        """
        log.info("Entering GET /notification endpoint")
        args = parser.parse_args()
        user_id = get_jwt_identity()
        page = args['page'] if args['page'] else 1
        page_size = args['page_size'] if args['page_size'] else 5
        page_size = args['id'] if args['page_size'] else 5

        # gets recipe id
        notification_id = args["id"]

        if not notification_id:
            return Response(status=400, response="Invalid arguments...")

        try:
            user = UserDB.get(UserDB.id == user_id)
        except peewee.DoesNotExist:
            block_user_session_id()
            log.error("User couldn't be found.")
            return Response(status=400, response="User couldn't be found.")


        try:
            query = Notification.get((Notification.user == user) & (Notification.id == notification_id))
        except peewee.DoesNotExist:
            log.error("Notification couldn't be found.")
            return Response(status=400, response="Notification couldn't be found.")


        log.info("Exiting GET /notification endpoint")

        return Response(status=200, response=json.dumps(NotificationSchema().dump(query)), mimetype="application/json")

    @jwt_required()
    def put(self):
        """
        Update user's notifications.
        """
        log.info("PUT /notification")
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
            notification = Notification.get(
                (Notification.id == args["id"]) & (Notification.user == user_query))
        except peewee.DoesNotExist:
            log.error("Shopping list couldn't be found by this id.")
            return Response(status=400, response=f'Shopping list couldnt be found by this id: {args["id"]}')


        try:
            notification_schema = NotificationSchema().load(request.get_json())
        except Exception as e:
            log.error("Error validating user: " + str(e))
            return Response(status=400, response="Error patching user: " + str(e))

        notification.seen = notification_schema["seen"]

        notification.save()

        log.info("Exiting PUT /notification endpoint")

        return Response(status=200)

    @jwt_required()
    def delete(self):
        """
        Delete a user's notification.
        """
        log.info("DELETE /notification")
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
            notification_model = Notification.get(id=args["id"], user=user_model.id)
        except peewee.DoesNotExist:
            log.error("Notification does not exist.")
            return Response(status=400, response="Shopping list does not exist.")

        notification_model.delete_instance()

        log.info("Finish DELETE /shopping_list")

        return Response(status=204)



