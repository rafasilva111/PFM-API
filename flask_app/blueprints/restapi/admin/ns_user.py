from datetime import timezone

import peewee
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource

from ..errors import return_error_sql
from ....classes.models import User as UserDB
from ....classes.schemas import *
from ....ext.logger import log

# Create name space
api = Namespace("Users", description="Here are all user endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The string to be search.')
parser.add_argument('string', type=str, help='The string to be search.')

ENDPOINT = "/user"


@api.route("")
class UserResource(Resource):

    @jwt_required()
    def delete(self):
        """
            Delete user
        """

        log.info("DELETE /user")

        # gets user auth id

        user_logged_id = get_jwt_identity()

        # get args

        args = parser.parse_args()

        id = args['id']

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

        # check if user exists
        try:
            user_to_be_deleted = UserDB.get(id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and still reach this far)
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couldn't be found by this id.")
            return Response(status=400, response="User couldn't be found by this id.")

        if user_logged.user_type == USER_TYPE.ADMIN.value:
            try:
                user_to_be_deleted.delete_instance(recursive=True)
                log.info("Finished DELETE /user")
                return Response(status=200, response="User deleted successfully.")
            except peewee.IntegrityError as e:
                log.error(return_error_sql(e))
                return Response(status=400, response=return_error_sql(e))
        return Response(status=403)

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
                UserSchema().dump(user_making_patch)),
                            mimetype="application/json")
        except Exception as e:
            log.error(return_error_sql(e))
            return return_error_sql(e)
