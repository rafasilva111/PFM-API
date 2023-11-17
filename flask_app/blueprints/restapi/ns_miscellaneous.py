import json

import peewee
from flask import Response, Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restx import Resource, Namespace
from marshmallow import ValidationError

from ...classes.functions import block_user_session_id
from ...classes.models import User as UserDB, Recipe as RecipeDB, ApplicationReport
from ...classes.schemas import ApplicationReportSchema
from ...ext.logger import log

api = Namespace("Miscellanius", description="Here are all company endpoints")

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The id to be search.')

ENDPOINT = "/app"


@api.route("/report")
class ApplicationReportResource(Resource):
    @jwt_required()
    def post(self):
        """ Used to post an app report"""

        # logging
        log.info("POST /recipe/admin")

        json_data = request.get_json()

        # validate entities

        user_id = get_jwt_identity()

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db, so in prod this wont happen
            block_user_session_id()
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        # Validate args by loading it into schema

        try:
            aplication_report_validated = ApplicationReportSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        aplication_report_ = ApplicationReport(**aplication_report_validated)

        aplication_report_.user = user

        aplication_report_.save()

        log.info("Finished POST /recipe/list")
        return Response(status=201)
