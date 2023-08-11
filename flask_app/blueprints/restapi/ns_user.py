import json
import math
from datetime import datetime, timezone

import peewee
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource
from playhouse.shortcuts import model_to_dict

from .errors import return_error_sql
from ...classes.models import User as UserDB
from ...classes.schemas import *
from ...ext.logger import log

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

        log.info("GET /user/list")
        # Get args

        args = parser.parse_args()

        string_to_search = args['string']
        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
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

            log.info("Finished GET /user/list with string")
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

            log.info("Finished GET /user/list")
            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


@api.route("")
class UserResource(Resource):

    @jwt_required()
    def get(self):
        """ Get a user with ID """

        log.info("GET /user")

        # gets user auth id

        user_logged_id = get_jwt_identity()

        # get args

        args = parser.parse_args()

        id = args['id']

        # Validate args
        if not id:
            log.error("Missing user id argument.")
            return Response(status=400, response="Missing user id argument.")

        try:
            user = UserDB.get(id=id)
            log.info("Finished GET /user")


        except peewee.DoesNotExist:
            log.error("User couldn't be found by this id.")
            return Response(status=400, response="User couldn't be found by this id.")

        user_model = model_to_dict(user, backrefs=True)

        is_following = Follow.select(peewee.fn.COUNT(Follow.id)).where(
            (Follow.follower == user_logged_id) & (Follow.followed == user)
        ).scalar() > 0

        if is_following:
            user_model['followed_state'] = FOLLOWED_STATE_SET.FOLLOWED.value
            return Response(status=200, response=json.dumps(UserPerfilSchema().dump(user_model)),
                            mimetype="application/json")
        is_pending = FollowRequest.select(peewee.fn.COUNT(FollowRequest.id)).where(
            (FollowRequest.follower == user_logged_id) & (FollowRequest.followed == user)
        ).scalar() > 0

        if is_pending:
            user_model['followed_state'] = FOLLOWED_STATE_SET.PENDING_FOLLOWED.value
            return Response(status=200, response=json.dumps(UserPerfilSchema().dump(user_model)),
                            mimetype="application/json")

        user_model['followed_state'] = FOLLOWED_STATE_SET.NOT_FOLLOWED.value

        return Response(status=200, response=json.dumps(UserPerfilSchema().dump(user_model)),
                        mimetype="application/json")

    @jwt_required()
    def delete(self):
        """Delete a user by ID"""

        log.info("DELETE /user")

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
            log.error("User couldn't be found by this id.")
            return Response(status=400, response="User couldn't be found by this id.")

        try:
            user_logged.delete_instance(recursive=True)
            log.info("Finished DELETE /user")
            return Response(status=200, response="User deleted successfully.")
        except peewee.IntegrityError as e:
            log.error(return_error_sql(e))
            return Response(status=400, response=return_error_sql(e))

    @jwt_required()
    def patch(self):
        """Patch a user by ID"""

        log.info("PATCH /user")

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
            log.error("User couldn't be found by this id.")
            return Response(status=400, response="User couldn't be found by this id.")

        # get data from json
        data = request.get_json()

        # validate data through user schema
        try:
            user_validated = UserPatchSchema().load(data)
        except Exception as e:
            log.error("Error validating user: " + str(e))
            return Response(status=400, response="Error patching user: " + str(e))

        try:
            for key, value in user_validated.items():
                setattr(user_making_patch, key, value)

            user_making_patch.updated_date = datetime.now(timezone.utc)
            user_making_patch.save()

            log.info("Finished PATCH /user")
            return Response(status=200, response=json.dumps(
                UserSchema().dump(model_to_dict(user_making_patch, backrefs=True, recurse=True, manytomany=True))),
                            mimetype="application/json")
        except Exception as e:
            log.error(return_error_sql(e))
            return return_error_sql(e)
