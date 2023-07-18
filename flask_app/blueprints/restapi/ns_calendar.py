import json
import math
from datetime import datetime, timezone

import peewee
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource
from marshmallow import ValidationError
from playhouse.shortcuts import model_to_dict

from ...classes.models import Recipe as RecipeDB, Comment as CommentDB, Follow as FollowDB, User as UserDB, \
    CalendarEntry, TokenBlocklist
from ...classes.schemas import CommentSchema, FollowedsSchema, FollowersSchema, build_metadata, CalendarEntrySchema
from ...ext.logger import log

# Create name space
api = Namespace("calendar", description="Here are all comment endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The id to be search.')
parser.add_argument('user_id', type=int, help='The user id to be search.')
parser.add_argument('recipe_id', type=int, help='The recipe id to be search.')

ENDPOINT = "/calendar"


# Create resources
@api.route("/list")
class CalendarListResource(Resource):

    def get(self):
        """List all calender"""

        log.info("GET /calendar/list")

        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # declare response holder

        response_holder = {}

        # metadata

        total_comments = int(CalendarEntry.select().count())
        total_pages = math.ceil(total_comments / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_comments, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        calendar_entrys = []
        for item in CalendarEntry.select().paginate(page, page_size):
            calendar_entry = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
            calendar_entrys.append(CalendarEntrySchema().dump(calendar_entry))

        response_holder["result"] = calendar_entrys

        log.info("Finish GET /follow/list")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


@api.route("")
@api.doc("Follow partial")
class CalendarResource(Resource):

    @jwt_required()
    def get(self):
        """ Get a follow whit ID """

        log.info("GET /calendar")
        # Get args

        args = parser.parse_args()

        # Validate args

        if not args["id"]:
            log.error("Invalid arguments...")
            return Response(status=400, response="Invalid arguments...")

        # Get and Serialize db model

        try:
            comment_record = CalendarEntry.get(id=args["id"])
            comment_model = model_to_dict(comment_record, backrefs=True, recurse=True)
            comment_schema = CalendarEntrySchema().dump(comment_model)
        except peewee.DoesNotExist:
            log.error("Recipe does not exist...")
            return Response(status=400, response="Recipe does not exist...")

        log.info("Finish GET /calendar")
        return Response(status=200, response=json.dumps(comment_schema), mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post a comment by user """

        log.info("POST /calendar")

        # gets user auth id

        user_id = get_jwt_identity()

        # Parse json body

        json_data = request.get_json()

        # Get args

        args = parser.parse_args()

        recipe_id = args['recipe_id']

        # Validate args

        if not args["recipe_id"]:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # Validate json body by loading it into schema

        try:
            calendar_entry_validated = CalendarEntrySchema().load(json_data)
        except ValidationError as err:
            log.error("Invalid arguments...")
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        # Verify existence of the requested ids model's

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("Client couldn't be found.")
            return Response(status=400, response="Client couldn't be found.")

        try:
            recipe = RecipeDB.get(recipe_id)
        except peewee.DoesNotExist:
            # this only occurs when accounts are not in db
            log.error("Recipe couldn't be found.")
            return Response(status=400, response="Recipe couldn't be found.")

        # fills recipe object
        calendar_model = CalendarEntry(**calendar_entry_validated)
        calendar_model.user = user
        calendar_model.recipe = recipe
        calendar_model.save()

        log.info("Finish POST /calendar")

        return Response(status=201)



    @jwt_required()
    def delete(self):
        """Delete a comment by ID"""

        log.info("DELETE /calendar")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        id = args['id'] if args['id'] else None

        # Validate args

        if not id:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # delete by referencing the user id
        try:
            calendar_entry = CalendarEntry.get(id,CalendarEntry.user == user_id)
        except peewee.DoesNotExist:
            log.error("User does not follow referenced account.")
            return Response(status=400, response="User does not follow referenced account.")

        calendar_entry.delete_instance()


        log.info("Finish DELETE /calendar")
        return Response(status=200)