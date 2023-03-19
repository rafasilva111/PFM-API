import json
from datetime import timedelta, datetime, timezone
from flask import Response, Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace
from marshmallow import ValidationError
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from flask_app.ext.database import db
from ...models.model_auth import LoginSchema, TokenBlocklist
from ...models.model_user import User as UserDB, UserSchema

# Create blue print

auth_blueprint = Blueprint('auth_blueprint', __name__, url_prefix="/api/v1/auth")

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


@auth_blueprint.route('/login', methods=['POST'])
def login_user():
    # Get json data

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
        return Response(status=400, response="There is no user whit that email.")

    authorized = user.check_password(data['password'])
    if not authorized:
        return Response(status=400, response={'Password incorrect.'})

    # revoke old access token todo

    # create new

    expires = timedelta(days=7)
    access_token = create_access_token(identity=str(user.id), expires_delta=expires)
    response = {'token': access_token}
    return Response(status=200, response=json.dumps(response), mimetype="application/json")


@auth_blueprint.route('/register', methods=['POST'])
def register_user():
    # Get json data

    json_data = request.get_json()

    # Validate args by loading it into schema

    try:
        data = UserSchema().load(json_data)
    except ValidationError as err:
        return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

    # search for and existing email

    try:
        UserDB.get(email=data['email'])
        return Response(status=409, response="An object whit the same email already exist...")
    except:
        pass

    # fills db objects

    try:
        new_user = UserDB(**data)
    except Exception as e:
        return Response(status=400, response=json.dumps(e), mimetype="application/json")

    # commit them
    new_user.save()

    return Response(status=201, response="Object created.", mimetype="application/json")



@auth_blueprint.route('/', methods=['GET'])
@jwt_required()
def get_user_session():
    # gets user auth id

    user_id = get_jwt_identity()

    user_record = UserDB.get(user_id)

    userResponse = model_to_dict(user_record)

    userResponse['created_date'] = userResponse['created_date'].strftime("%d/%m/%Y, %H:%M:%S")
    userResponse['updated_date'] = userResponse['updated_date'].strftime("%d/%m/%Y, %H:%M:%S")
    userResponse['birth_date'] = userResponse['birth_date'].strftime("%d/%m/%Y")

    return Response(status=200, response=json.dumps(userResponse), mimetype="application/json")



@auth_blueprint.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    token_block_record = TokenBlocklist(jti=jti, created_at=now)
    token_block_record.save()
    return Response(status=200, response=json.dumps("User logged out sucessfully."))