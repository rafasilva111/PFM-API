import json
from datetime import date

import peewee
from flask import Response, Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from flask_app.ext.database import db
from flask_restx import Resource, Namespace

from ...classes.schemas import UserSchema

from ...classes.models import User as UserDB, USER_TYPE, PROFILE_TYPE

admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix="/api/v1")
from ...ext.logger import log

from flask_app.ext.database import models


# Admin API Model

@admin_blueprint.route("/create_tables", methods=["GET"])
def teste():
    db.create_tables(models)
    db.close()
    return Response(status=200, response=json.dumps("Tables successfully created."))


api = Namespace("Company", description="Here are all company endpoints")

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The id to be search.')

ENDPOINT_COMPANY = "/admin/company"


@api.route("")
class CompanyUserResource(Resource):

    @jwt_required()
    def post(self):
        """ Register a new user """

        log.info("POST /auth")

        # Get json data

        json_data = request.get_json()

        # gets user auth id

        user_id = get_jwt_identity()

        # Validate args by loading it into schema

        try:
            data = UserSchema().load(json_data)
        except ValidationError as err:
            log.error(err.messages)
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        # search for and existing email

        try:
            UserDB.get(email=data['email'])
            log.error("An object whit the same email already exist...")
            return Response(status=409, response="An object whit the same email already exist...")
        except:
            pass

        # Verify existence of the requested ids model's

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Client couldn't be found.")

        # Verify if user is admin

        if user.user_type != USER_TYPE.ADMIN.value:
            return Response(status=403)

        # fills db objects

        try:
            user = UserDB(**data)
            user.user_type = USER_TYPE.COMPANY.value
            user.verified = True
            user.profile_type = PROFILE_TYPE.PUBLIC.value
            # calculate age
            today = date.today()
            user.age = today.year - data['birth_date'].year - (
                    (today.month, today.day) < (data['birth_date'].month, data['birth_date'].day))
        except Exception as e:
            log.error(e)
            return Response(status=400, response=json.dumps(e), mimetype="application/json")

        # commit them
        user.save()

        log.info("Finished POST /auth")
        return Response(status=201)

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
            import pytz  # $ pip install pytz

            user_making_patch.updated_date = datetime.now(timezone.utc)
            user_making_patch.save()

            log.info("Finished PATCH /user")
            return Response(status=200, response=json.dumps(
                UserSchema().dump(model_to_dict(user_making_patch, backrefs=True, recurse=True, manytomany=True))),
                            mimetype="application/json")
        except Exception as e:
            log.error(return_error_sql(e))
            return return_error_sql(e)
