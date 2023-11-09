import json
from datetime import date

import peewee
from flask import Response, Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from flask_app.ext.database import db
from flask_restx import Resource, Namespace

from ...classes.functions import block_user_session_id
from ...classes.schemas import UserSchema

from ...classes.models import User as UserDB, USER_TYPE, PROFILE_TYPE

admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix="/api/v1")
from ...ext.logger import log


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

