import json
from datetime import date
from datetime import timedelta, datetime, timezone

from flask import Response, Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource
from marshmallow import ValidationError
from peewee import DoesNotExist, IntegrityError

from ...classes.models import TokenBlocklist, User as UserDB, RECIPES_BACKGROUND_TYPE
from ...classes.schemas import LoginSchema, RecipeSchema, UserSchema
from ...ext.logger import log

# Create blue print
api = Namespace("Auth", description="Here are all auth endpoints")

ENDPOINT = "/auth"

# School API Model

# Validation Schemas

auth_json_schema = {
    "type": "object",
    "properties": {
        "email": {"type": "string",
                  "minLength": 5},
        "password": {
            "type": "string",
            "minLength": 8
        },
    },
    "required": ["email", "password"]
}


@api.route('/login')
class login_user(Resource):

    @staticmethod
    def post():
        # Get json data

        log.info("POST /auth/login")

        json_data = request.get_json()

        # Validate args by loading it into schema

        try:
            data = LoginSchema().load(json_data)
        except ValidationError as err:
            return jsonify(err.messages), 400

        # Verify existence of the requested ids model's

        try:
            user = UserDB.get(email=data['email'])
        except DoesNotExist:
            log.error("There is no user with that email.")
            return Response(status=400, response="There is no user with that email.")

        authorized = user.check_password(data['password'])
        if not authorized:
            log.error("Password incorrect.")
            return Response(status=400, response={'Password incorrect.'})

        # create new

        expires = timedelta(days=7)
        access_token = create_access_token(identity=user.id, expires_delta=expires)
        response = {'token': access_token}
        log.info("Finished POST /auth/login")
        return Response(status=200, response=json.dumps(response), mimetype="application/json")


@api.route('')
class UserAuthResource(Resource):
    @staticmethod
    def post():
        """ Register a new user """
        # Get json data

        log.info("POST /auth")

        json_data = request.get_json()

        # Validate args by loading it into schema

        try:
            data = UserSchema().load(json_data)
        except ValidationError as err:
            log.error(err.messages)

            return Response(status=400, response=json.dumps({"errors":err.messages}), mimetype="application/json")


        # fills db objects

        try:
            user = UserDB(**data)
            # calculate age
            today = date.today()
            user.age = today.year - data['birth_date'].year - (
                    (today.month, today.day) < (data['birth_date'].month, data['birth_date'].day))
        except Exception as e:
            log.error(e)
            return Response(status=400, response=json.dumps(e), mimetype="application/json")

        # commit them
        try:
            user.save()
        except IntegrityError as e:
            msg = {}
            if "username" in e.args[1]:
                msg["username"]=["Username is already being used."]
            elif "email" in e.args[1]:
                msg["email"] = ["Email is already being used."]

            return Response(status=400, response=json.dumps({"errors":msg}), mimetype="application/json")

        log.info("Finished POST /auth")
        return Response(status=201)

    @staticmethod
    @jwt_required()
    def get():
        # gets user auth id

        log.info("GET /auth")
        user_id = get_jwt_identity()

        # query
        try:
            user_record = UserDB.get(user_id)
        except DoesNotExist as e:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        userSchema = UserSchema().dump(user_record)

        log.info("GET /auth")
        return Response(status=200, response=json.dumps(userSchema), mimetype="application/json")


    @staticmethod
    @jwt_required()
    def delete():
        log.info("DELETE /auth/logout")

        jti = get_jwt()["jti"]
        now = datetime.now(timezone.utc)
        token_block_record = TokenBlocklist(jti=jti, created_at=now)
        token_block_record.save()

        log.info("DELETE /auth/logout")
        return Response(status=204)

@api.route('/recipes')
class UserAuthResource(Resource):
    @staticmethod
    @jwt_required()
    def get():
        # gets user auth id

        log.info("GET /auth")
        user_id = get_jwt_identity()

        # query
        try:
            user_record = UserDB.get(user_id)
        except DoesNotExist as e:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        created = []
        liked = []
        saved = []

        recipe_schema = RecipeSchema()

        for item in user_record.recipes:
            if item.type == RECIPES_BACKGROUND_TYPE.LIKED.value:
                liked.append(recipe_schema.dump(item.recipe))
            if item.type == RECIPES_BACKGROUND_TYPE.SAVED.value:
                saved.append(recipe_schema.dump(item.recipe))

        for item in user_record.created_recipes:
            created.append(recipe_schema.dump(item))

        response_holder = {"result": {'recipes_created': created, 'recipes_liked': liked, 'recipes_saved': saved}}

        log.info("GET /auth")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

