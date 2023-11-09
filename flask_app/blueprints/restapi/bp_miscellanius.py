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

admin_blueprint = Blueprint('miscellanius_blueprint', __name__, url_prefix="/api/v1")
from ...ext.logger import log


api = Namespace("Miscellanius", description="Here are all company endpoints")

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The id to be search.')

ENDPOINT_COMPANY = "/miscellanius"

@api.route("")
class ApplicationReportResource(Resource):
    @jwt_required()
    def post(self):
        """ Used to post a report on a recipe"""

        # logging
        log.info("POST /recipe/admin")

        # Get args

        args = parser.parse_args()

        # validate args
        if args['id'] is None:
            log.error("Id must be supplied.")
            return Response(status=400, response="Id must be supplied.")

        json_data = request.get_json()

        ## validate entities

        user_id = get_jwt_identity()

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db, so in prod this wont happen
            block_user_session_id()
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        try:
            recipe = Recipe.get(args['id'])
        except peewee.DoesNotExist:
            log.error("Recipe couln't be found.")
            return Response(status=400, response="User couln't be found.")

        # Validate args by loading it into schema

        try:
            recipe_report_validated = RecipeReportSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        recipe_report = RecipeReport(**recipe_report_validated)

        recipe_report.user = user
        recipe_report.recipe = recipe

        recipe_report.save()

        log.info("Finished POST /recipe/list")
        return Response(status=201)