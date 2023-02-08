import datetime
import json
import math

from flask import request, Response, jsonify
from flask_restful import reqparse, Resource, abort
from playhouse.shortcuts import model_to_dict, dict_to_model
from backend.dbManager import Recipe as RecipeDB, Preparation, Nutrition_Information, Tags, Ingredients, User as UserDB
from backend.dtos import RecipeDTO

parser = reqparse.RequestParser()
parser.add_argument('page')
parser.add_argument('page_size')
parser.add_argument('id')
parser.add_argument('userUUID')

PROFILE_TYPE = {"NORMAL", "VIP", "ADMIN"}
SEXES = {"F", "M"}

USER_ENDPOINT = "user"


class User(Resource):
    response_placeholder = {
        "_metadata":
            {
                "page": 5,
                "page_count": 20,
                "per_page": 20,
                "total_count": 521,
                "Links": [
                    {"self": f"/{USER_ENDPOINT}?page=5&per_page=20"},
                    {"first": f"/{USER_ENDPOINT}?page=0&per_page=20"},
                    {"previous": f"/{USER_ENDPOINT}?page=4&per_page=20"},
                    {"next": f"/{USER_ENDPOINT}?page=6&per_page=20"},
                    {"last": f"/{USER_ENDPOINT}?page=26&per_page=20"},
                ]
            },
        "results": []
    }

    # /recipe
    def get(self):
        args = parser.parse_args()
        # single record
        if args['userUUID']:
            user_record = UserDB.get(uuid=args['userUUID'])
            userResponse = model_to_dict(user_record)

            userResponse['created_date'] = userResponse['created_date'].strftime("%d/%m/%Y, %H:%M:%S")
            userResponse['updated_date'] = userResponse['updated_date'].strftime("%d/%m/%Y, %H:%M:%S")
            userResponse['birth_date'] = userResponse['birth_date'].strftime("%d/%m/%Y")

            return Response(status=200, response=json.dumps(userResponse), mimetype="application/json")
        # all records
        else:
            args = parser.parse_args()
            page = args['page'] if args['page'] else 0
            page_size = int(args['page_size']) if args['page_size'] else 20

            if page_size not in [5, 10, 20, 40]:
                return Response(status=400, response="page_size not in [5, 10, 20, 40]")

            response_holder = self.response_placeholder

            # metadata

            total_recipes = int(UserDB.select().count())
            total_pages = math.ceil(total_recipes / page_size)
            response_holder['_metadata']['Links'] = []

            if page < total_pages:
                next_link = page + 1
                response_holder['_metadata']['Links'].append(
                    {"next": f"/{USER_ENDPOINT}?page={next_link}&page_size={page_size}"},
                    )
            if page > total_pages:
                previous_link = page - 1
                response_holder['_metadata']['Links'].append(
                    {"previous": f"/{USER_ENDPOINT}?page={previous_link}&page_size={page_size}"})

            response_holder['_metadata']['Links'].append({"first": f"/{USER_ENDPOINT}?page=1&page_size={page_size}"})
            response_holder['_metadata']['Links'].append(
                {"last": f"/{USER_ENDPOINT}?page={total_pages}&page_size={page_size}"})

            response_holder['_metadata']['page'] = page
            response_holder['_metadata']['per_page'] = page_size
            response_holder['_metadata']['page_count'] = total_pages
            response_holder['_metadata']['total_count'] = total_recipes

            user = []
            for item in UserDB.select().paginate(page, page_size):
                user.append(User(id=item.id, title=item.title, description=item.description,
                                         created_date=item.created_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         updated_date=item.updated_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         img_source=item.img_source,
                                         difficulty=item.difficulty, portion=item.portion, time=item.time,
                                         likes=item.likes,
                                         source_rating=item.source_rating,
                                         views=item.views, tags=item.tags, ingredients=item.ingredients,
                                         preparations=item.preparations,
                                         nutrition_informations=item.nutrition_informations
                                         ).__dict__)

            response_holder["results"] = user

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    def post(self):
        data = request.get_json()

        try:
            if data['uuid'] and data['uuid'] != "":
                uuid = str(data['uuid']).strip()
            else:
                return Response(status=400, response="UUID is missing.\n")
        except Exception as e:
            return Response(status=400, response="UUID is missing.\n" + str(e))

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
            if data['birth_date'] and data['birth_date'] != '':
                birth_date = str(data['birth_date']).strip()
            else:
                return Response(status=400, response="Birthday is missing.\n")
        except Exception as e:
            return Response(status=400, response="Birthday is missing.\n" + str(e))

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
            return Response(status=400, response="Sexo is missing or not in {\n" + str(e))

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
        userDB.uuid = uuid
        userDB.first_name = first_name
        userDB.last_name = last_name
        userDB.birth_date = datetime.datetime.strptime(birth_date, "%d/%m/%Y")
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

    def put(self):
        data = request.get_json()[0]
        args = parser.parse_args()

        # validate parameters

        try:
            id = args['id']
        except:
            return Response(status=409, response="You must supply id.")

        try:
            recipe = RecipeDB.get(id=id)
        except:
            return Response(status=409, response="This id doesnt correspond to any object.")

        # validate json

        title = None
        try:
            if data['title'] and data['title'] != '':
                recipe.title = str(data['title']).strip()
        except:
            pass

        description = None
        try:
            if data['description'] and data['description'] != '':
                recipe.description = str(data['description']).strip()
        except:
            pass

        try:
            company = None
            if data['company'] and data['company'] != '':
                recipe.company = str(data['company']).strip()
        except:
            pass

        try:
            img_source = None
            if data['img_source'] and data['img_source'] != '':
                recipe.img_source = str(data['img_source']).strip()
        except:
            pass

        try:
            difficulty = None
            if data['difficulty'] and data['difficulty'] != '':
                recipe.difficulty = str(data['difficulty']).strip()
        except:
            pass

        try:
            portion = None
            if data['portion'] and data['portion'] != '':
                recipe.portion = str(data['portion']).strip()
        except:
            pass

        try:
            time = None
            if data['time'] and data['time'] != '':
                recipe.time = str(data['time']).strip()
        except:
            pass
        try:
            source_rating = None
            if data['source_rating'] and data['source_rating'] != '':
                recipe.source_rating = float(data['source_rating'])
        except:
            pass

        recipe.updated_date = datetime.datetime.now()

        recipe.save()

        return

    def delete(self):
        args = parser.parse_args()

        # conn = DBManager(password_file='/run/secrets/db-password')

        return
