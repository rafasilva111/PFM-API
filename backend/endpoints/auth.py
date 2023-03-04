from datetime import timedelta,datetime,timezone

import peewee
import redis as redis
from flask import request, Response, Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_restful import Resource, reqparse
from flask_restful.representations import json
from playhouse.shortcuts import model_to_dict
from backend.dbManager import Recipe as RecipeDB, Preparation, Nutrition_Information, Tags, Ingredients, User as UserDB, \
    HOST, TokenBlocklist
from backend.endpoints.user import PROFILE_TYPE, SEXES

parser = reqparse.RequestParser()

auth_blueprint = Blueprint('auth_blueprint', __name__)

jwt_redis_blocklist = redis.StrictRedis(
    host=HOST, port=6379, db=0, decode_responses=True
)
ACCESS_EXPIRES = timedelta(hours=1)

@auth_blueprint.route('/user/register', methods=['POST'])
def register_user():
    data = request.get_json()
    try:
        if data['first_name'] and data['first_name'] != "":
            first_name = str(data['first_name']).strip()
        else:
            return Response(status=400, response="First name is missing.\n")
    except Exception as e:
        return Response(status=400, response="First name is missing.\n" + str(e))

    try:
        if data['last_name'] and data['last_name'] != '':
            last_name = str(data['last_name']).strip()
        else:
            return Response(status=400, response="Last name is missing.\n")
    except Exception as e:
        return Response(status=400, response="Last name missing.\n" + str(e))

    try:
        if data['password'] and data['password'] != '':
            password = str(data['password']).strip()
        else:
            return Response(status=400, response="Password is missing.\n")
    except Exception as e:
        return Response(status=400, response="Password missing.\n" + str(e))

    try:
        if data['birth_date'] and data['birth_date'] != '':
            birth_date = str(data['birth_date']).strip()
        else:
            return Response(status=400, response="Birthday is missing.\n")
    except Exception as e:
        return Response(status=400, response="Birthday is missing.\n" + str(e))

    try:
        birth_date = datetime.strptime(birth_date, "%d/%m/%Y")
    except Exception as e:
        return Response(status=400, response="Birthday format is invalid.\n" + str(e))

    try:
        if data['email'] and data['email'] != '':
            email = str(data['email']).strip()
        else:
            return Response(status=400, response="Email is missing.\n")
    except Exception as e:
        return Response(status=400, response="Email is missing.\n" + str(e))

    try:
        profile_type = None
        if data['profile_type'] and data['profile_type'] != '':
            # check if protect in existing groups
            if data['profile_type'] in PROFILE_TYPE:
                profile_type = str(data['profile_type']).strip()
            else:
                # todo security log for inspection
                return Response(status=400, response="Profile type incorrect...")
    except:
        pass

    try:
        verified = None
        if data['verified'] and data['verified'] != '':
            verified = str(data['verified']).strip()
    except:
        verified = False

    try:
        user_type = None
        if data['user_type'] and data['user_type'] != '':
            user_type = str(data['user_type']).strip()
    except:
        user_type = "NORMAL"

    try:
        img_source = None
        if data['img_source'] and data['img_source'] != '':
            img_source = float(data['img_source'])
    except:
        pass

    try:
        activity_level = None
        if data['activity_level'] and data['activity_level'] != '':
            activity_level = float(data['activity_level'])
    except:
        pass

    try:
        height = None
        if data['height'] and data['height'] != '':
            height = float(data['height'])
    except:
        pass

    try:
        if data['sex'] and data['sex'] != '' and data['sex'] in SEXES:
            sex = str(data['sex'])
        else:
            return Response(status=400, response="Sex is missing")
    except Exception as e:
        return Response(status=400, response=f"Sexo is missing or not in {[a for a in SEXES]}")

    try:
        weight = None
        if data['weight'] and data['weight'] != '':
            weight = float(data['weight'])
    except:
        pass

    try:
        UserDB.get(email=email)
        return Response(status=409, response="An object whit the same email already exist...")
    except:
        pass

    userDB = UserDB()
    userDB.uuid = "uuid"
    userDB.first_name = first_name
    userDB.last_name = last_name
    userDB.password = userDB.hash_password(password)
    userDB.birth_date = birth_date
    userDB.age = int(datetime.datetime.now().year) - int(userDB.birth_date.year)
    userDB.email = email
    userDB.profile_type = profile_type if profile_type is not None else userDB.profile_type
    userDB.verified = verified
    userDB.user_type = user_type
    userDB.img_source = img_source
    userDB.activity_level = activity_level
    userDB.height = height
    userDB.sex = sex
    userDB.weight = weight
    userDB.save()

    userResponse = model_to_dict(userDB)

    userResponse['created_date'] = userResponse['created_date'].strftime("%d/%m/%Y, %H:%M:%S")
    userResponse['updated_date'] = userResponse['updated_date'].strftime("%d/%m/%Y, %H:%M:%S")
    userResponse['birth_date'] = userResponse['birth_date'].strftime("%d/%m/%Y")

    return Response(status=201, response=json.dumps(userResponse), mimetype="application/json")


@auth_blueprint.route('/user/login', methods=['POST'])
def login_user():

    # Get json body

    data = request.get_json()

    # Validate args

    try:
        if data['email'] and data['email'] != '':
            email = str(data['email']).strip()
        else:
            return Response(status=400, response="Email is missing.\n")
    except Exception as e:
        return Response(status=400, response="Email is missing.\n" + str(e))

    try:
        if data['password'] and data['password'] != '':
            password = str(data['password']).strip()
        else:
            return Response(status=400, response="Password is missing.\n")
    except Exception as e:
        return Response(status=400, response="Password is missing.\n" + str(e))

    # Verify existence of the requested ids model's

    try:
        user = UserDB.get(email=email)
    except peewee.DoesNotExist:
        return Response(status=400, response="There is no user whit that email.")

    authorized = user.check_password(password)
    if not authorized:
        return Response(status=400, response={'Email or password invalid.'})

    expires = timedelta(days=7)
    access_token = create_access_token(identity=str(user.id), expires_delta=expires)
    response = {'token': access_token}
    return Response(status=200, response=json.dumps(response), mimetype="application/json")


@auth_blueprint.route('/user/auth', methods=['GET'])
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



@auth_blueprint.route("/user/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)
    token_block_record = TokenBlocklist(jti=jti, created_at=now)
    token_block_record.save()
    return Response(status=200, response="User logged out sucessfully.")
