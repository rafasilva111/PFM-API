import json
import math

import peewee
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Namespace, Resource

from ...classes.functions import block_user_session_id
from ...classes.models import User as UserDB, Notification as NotificationDB
from ...classes.schemas import build_metadata, NotificationSchema
from ...ext.logger import log

api = Namespace("calendar", description="Here are all comment endpoints")

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument("id", type=int, help="ID of the calendar to delete")

ENDPOINT = "/notification"


@api.route("/list")
class NotificationResource(Resource):
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

        query = NotificationDB.select().where((NotificationDB.user == user)).order_by(
            NotificationDB.created_date.desc())
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
class NotificationResource(Resource):

    @jwt_required()
    def get(self):
        """
        Retrieve user's notifications.
        """
        log.info("Entering GET /notification endpoint")
        args = parser.parse_args()
        user_id = get_jwt_identity()

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
            query = NotificationDB.get((NotificationDB.user == user) & (NotificationDB.id == notification_id))
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
            notification = NotificationDB.get(
                (NotificationDB.id == args["id"]) & (NotificationDB.user == user_query))
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
            notification_model = NotificationDB.get(id=args["id"], user=user_model.id)
        except peewee.DoesNotExist:
            log.error("Notification does not exist.")
            return Response(status=400, response="Shopping list does not exist.")

        notification_model.delete_instance()

        log.info("Finish DELETE /shopping_list")

        return Response(status=204)


@api.route('/list/delete')
class NotificationResource(Resource):

    @jwt_required()
    def post(self):
        """ Used to delete a notification's list """

        # Get json data

        log.info("POST /notification/delete")

        json_data = request.get_json()

        # validate body

        if json_data['id_list'] is None:
            log.error("Id_list must be supplied.")
            return Response(status=400, response="Id_list must be supplied.")

        # gets user auth id

        user_id = get_jwt_identity()

        # delete

        try:
            query = NotificationDB.delete().where(
                NotificationDB.id.in_(json_data['id_list']) & (NotificationDB.user == user_id))
            query.execute()
        except peewee.DoesNotExist:

            return Response(status=400, response="Unable to delete this notifications...")

        log.info("POST /notification/delete")
        return Response(status=204)


@api.route('/list/seen')
class NotificationResource(Resource):

    @jwt_required()
    def post(self):

        """ Used to update state seen of a notification's list """
        # Get json data

        log.info("POST /auth/login")

        json_data = request.get_json()

        # validate body

        if json_data['id_list'] is None:
            log.error("Id_list must be supplied.")
            return Response(status=400, response="Id_list must be supplied.")

        # gets user auth id

        user_id = get_jwt_identity()

        # delete

        try:
            query = NotificationDB.update(seen=True).where(
                (NotificationDB.id.in_(json_data['id_list'])) & (NotificationDB.user == user_id))
            query.execute()
        except peewee.DoesNotExist:
            return Response(status=400, response="Unable to update this notifications...")

        log.info("DELETE /notification/seen")
        return Response(status=200)
