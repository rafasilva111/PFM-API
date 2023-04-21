import json
import math
from datetime import datetime, timezone
import peewee
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource, fields, reqparse
from flask import Response, request
from playhouse.shortcuts import model_to_dict
from flask_app.ext.database import db
from .errors import return_error_sql, student_no_exists
from ...models import TokenBlocklist
from ...models.model_metadata import build_metadata
from ...models.model_user import User as UserDB, UserSchema, UserPatchSchema

# Create name space
api = Namespace("Users", description="Here are all user endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=str, help='The string to be search.')
parser.add_argument('string', type=str, help='The string to be search.')

ENDPOINT = "/user"


# Create resources
@api.route("/list")
class UserListResource(Resource):

    def get(self):
        """List all users"""
        # Get args

        args = parser.parse_args()

        string_to_search = args['string']
        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        ## Pesquisa por String

        if string_to_search:

            # declare response holder

            response_holder = {}

            # build query

            query = UserDB.select().where(UserDB.first_name.contains(string_to_search) |
                                          UserDB.last_name.contains(string_to_search) |
                                          UserDB.email.contains(string_to_search))

            # metadata

            total_users = int(query.count())
            total_pages = math.ceil(total_users / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_users, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for item in query.paginate(page, page_size):
                recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                recipes.append(UserSchema().dump(recipe))

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
        else:

            # declare response holder

            response_holder = {}

            # metadata

            total_users = int(UserDB.select().count())
            total_pages = math.ceil(total_users / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_users, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for item in UserDB.select().paginate(page, page_size):
                recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                recipes.append(UserSchema().dump(recipe))

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

@api.route("")
class UserResource(Resource):

    def get(self):
        """ Get a user with ID """

        # get args
        args = parser.parse_args()
        id = args['id']

        # Validate args
        if not id:
            return Response(status=400, response="Missing user id argument.")

        try:
            user = UserDB.get(id)
            return Response(status=200, response=json.dumps(UserSchema().dump(user)), mimetype="application/json")
        except peewee.DoesNotExist:
            return Response(status=400, response="User couldn't be found by this id.")


    @jwt_required()
    def delete(self):
        """Delete a user by ID"""

        # gets user auth id
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
            return Response(status=400, response="User couldn't be found by this id.")

        try:
            user_logged.delete_instance(recursive=True)
            return Response(status=200, response="User deleted successfully.")
        except peewee.IntegrityError as e:
            return Response(status=400, response=return_error_sql(e))


    @jwt_required()
    def patch(self):
        """Patch user auth"""

        # gets user auth id
        user_id = get_jwt_identity()

        # check if user exists
        try:
            user_making_patch = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and still reach this far)
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="User couldn't be found by this id.")

        # get data from json
        data = request.get_json()

        # validate data through user schema
        try:
            user_validated = UserPatchSchema().load(data)
        except Exception as e:
            return Response(status=400, response="Error patching user: " + str(e))

        try:
            for key, value in user_validated.items():
                    setattr(user_making_patch, key, value)

            user_making_patch.updated_date = datetime.utcnow()
            user_making_patch.save()

            userResponse = model_to_dict(user_making_patch, backrefs=True, recurse=True, manytomany=True)
            userSchema = UserSchema().dump(userResponse)

            return Response(status=200, response=json.dumps(userSchema), mimetype="application/json")
        except Exception as e:
            return return_error_sql(e)
