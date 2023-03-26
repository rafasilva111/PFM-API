import json
import math
from datetime import datetime, timezone

import peewee
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource, fields, abort, reqparse
from flask import Response, request
from marshmallow import ValidationError
from playhouse.shortcuts import model_to_dict

from ...models import TokenBlocklist
from ...models.model_metadata import MetadataSchema, build_metadata
from ...models.model_recipe import Recipe as RecipeDB, RecipeSchema
from ...models.model_tag import Tag as TagDB, RecipeTagThrough as RecipeTagThroughDB
from ...models.model_user import User as UserDB
from ...models.model_recipe_background import RecipeBackground as RecipeBackgroundDB
from ...models.model_nutrition_information import NutritionInformation as NutritionInformationDB
from .errors import return_error_sql, school_no_exists

# Create name space
api = Namespace("Schools", description="Here are all School endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=str, help='The string to be search.')
parser.add_argument('string', type=str, help='The string to be search.')

RECIPE_ENDPOINT = "/recipe"

# School API Model
school_api_full_model = api.model("School model", {
    "id": fields.Integer(requred=False, description="The ID of school"),
    "name": fields.String(required=True, description="The first name of school", min_length=3, max_length=20),
    "address": fields.String(required=True, description="The last name of school", min_length=3, max_length=20),
    "email": fields.String(required=True, description="The email of school", min_length=10, max_length=30),
    "phone": fields.Integer(required=True, description="The age of school", min=1, max=100, allow_null=False),
    "students": fields.List(
        fields.String(required=True, description="Students attending this school", allow_null=False))
})

school_api_model = api.model("School model", {
    "name": fields.String(required=True, description="The first name of school", min_length=3, max_length=20),
    "address": fields.String(required=True, description="The last name of school", min_length=3, max_length=20),
    "email": fields.String(required=True, description="The email of school", min_length=10, max_length=30),
    "phone": fields.Integer(required=True, description="The age of school", min=1, max=100, allow_null=False),
    "students": fields.List(
        fields.String(required=True, description="Students attending this school", allow_null=False))
})


# Create resources
@api.route("/list")
@api.doc("get_recipe_list", model=school_api_full_model)
class RecipeListResource(Resource):

    @api.expect(parser)
    def get(self):
        """List all schools"""
        # Get args

        args = parser.parse_args()

        string_to_search = args['string']
        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        ## Pesquisa por String

        if string_to_search:

            # declare response holder

            response_holder = {}

            # build query

            # respons data

            query = RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB) \
                .where(TagDB.title.contains(string_to_search) | RecipeDB.title.contains(string_to_search))

            # metadata

            total_recipes = int(query.count())
            total_pages = math.ceil(total_recipes / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_recipes, RECIPE_ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for item in query.paginate(page, page_size):
                recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                recipes.append(RecipeSchema().dump(recipe))

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
        else:

            # declare response holder

            response_holder = {}

            # metadata

            total_recipes = int(RecipeDB.select().count())
            total_pages = math.ceil(total_recipes / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_recipes, RECIPE_ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for item in RecipeDB.select().paginate(page, page_size):
                recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                recipes.append(RecipeSchema().dump(recipe))

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    def post(self):
        # TODO bulk import method, will only be used by admin to populate company's recipe

        Response(status=200, response="Not implemented yet.")


@api.route("")
class RecipeResource(Resource):

    def get(self):
        """ Get a recipe with ID """

        # Get args

        args = parser.parse_args()

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Invalid arguments...")

        try:
            recipe_record = RecipeDB.get(id=args["id"])
            schema = RecipeSchema().dump(recipe_record)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe does not exist...")

        return Response(status=200, response=schema, mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post a recipe by user """

        json_data = request.get_json()

        # gets user auth id

        user_id = get_jwt_identity()

        # Validate args by loading it into schema

        try:
            recipe_validated = RecipeSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        # Verify existence of the requested ids model's

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:

            # Otherwise block user token (user cant be logged in and stil reach this far)
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="Client couln't be found by this id.")

        # Change get or create needed objects
        # removing because the must be transformed before entity building
        nutrition_table = recipe_validated.pop('nutrition_informations')
        preparation = recipe_validated.pop('preparation')
        ingredients = recipe_validated.pop('ingredients')
        tags = recipe_validated.pop('tags')

        # fills recipe object
        recipe = RecipeDB(**recipe_validated)
        recipe.preparation = str(preparation).encode()
        recipe.ingredients = str(ingredients).encode()
        # use .decode() to decode
        recipe.save()

        # build relation to nutrition_table

        try:
            if nutrition_table and nutrition_table != {}:
                nutrition_information = NutritionInformationDB(**nutrition_table)
                nutrition_information.recipe = recipe
                nutrition_information.save()
                recipe.nutrition_informations = nutrition_information

        except Exception as e:
            recipe.delete_instance(recursive=True)
            return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

        # build relation to recipe_background

        try:
            recipe_background = RecipeBackgroundDB()
            recipe_background.user = user
            recipe_background.recipe = recipe
            recipe_background.type = "CREATED"
            recipe_background.save()
        except Exception as e:
            recipe.delete_instance(recursive=True)
            return Response(status=400, response="Tags Table has some error.\n" + str(e))

        # build multi to multi relation to tags

        try:
            if tags and tags != {}:
                for t in tags:
                    tag, created = TagDB.get_or_create(title=t)
                    tag.save()
                    recipe.tags.add(tag)


        except Exception as e:
            recipe.delete_instance(recursive=True)
            return Response(status=400, response="Tags Table has some error.\n" + str(e))

        # finally build full object

        recipe.save()

        return Response(status=201)

    # def delete(self, id):
        # """Delete a recipe by ID"""
        # try:
        #     recipe = School.query.get(id)
        #     if recipe is not None:
        #         db.session.delete(recipe)
        #         db.session.commit()
        #         schema = SchoolSchema()
        #         return {"message": "School was successfully added", "content": [schema.jsonify(school)]}
        #     return school_no_exists(id)
        # except Exception as e:
        #     return return_error_sql(e)



    #create method to update recipe

    @jwt_required()
    def put(self):
        """ Update a recipe by user """

        # gets user auth id
        user_id = get_jwt_identity()
        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="Client couldn't be found by this id.")

        # Get args
        args = parser.parse_args()

        # gets recipe id
        recipe_id = args["id"]

        # Validate args

        if not recipe_id:
            return Response(status=400, response="Invalid arguments...")

        json_data = request.get_json()

        try:
            recipe_validated = RecipeSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        try:
            recipe = RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe couln't be found by this id.")
        try:
            recipe.title = recipe_validated['title']
            recipe.description = recipe_validated['description']
            recipe.preparation = recipe_validated['preparation']
            recipe.ingredients = recipe_validated['ingredients']
            recipe.portion = recipe_validated['portion']

            # Change get or create needed objects
            # removing because the must be transformed before entity building
            nutrition_table = recipe_validated.pop('nutrition_informations')
            preparation = recipe_validated.pop('preparation')
            ingredients = recipe_validated.pop('ingredients')
            tags = recipe_validated.pop('tags')

            # fills recipe object
            recipe.preparation = str(preparation).encode()
            recipe.ingredients = str(ingredients).encode()  # acho que é isto que torna o plob
            # use .decode() to decode

            # build relation to nutrition_table

            try:
                if nutrition_table and nutrition_table != {}:
                    nutrition_information = NutritionInformationDB.get(recipe=recipe)
                    nutrition_information.recipe = recipe
                    recipe.nutrition_informations = nutrition_table

            except Exception as e:
                return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

            # build relation to recipe_background

            try:
                recipe_background = RecipeBackgroundDB()
                recipe_background.user = user
                recipe_background.recipe = recipe
                recipe_background.type = "SAVED"    #TODO no post estava a ser criado com CREATED, mas aqui não sei se é o caso

            except Exception as e:
                return Response(status=400, response="Tags Table has some error.\n" + str(e))

            # build multi to multi relation to tags
            try:
                rows_deleted = TagDB.recipes.get_through_model().delete().where(TagDB.recipes.get_through_model().recipe_id == recipe.get_id()).execute()

                if tags and tags != {} and rows_deleted:
                    for t in tags:
                        tag, created = TagDB.get_or_create(title=t)
                        recipe.tags.add(tag)


            except Exception as e:
                return Response(status=400, response="Tags Table has some error.\n" + str(e))

            # finally build full object
            tag.save()
            nutrition_information.save()
            recipe_background.save()
            recipe.save()
            return Response(status=200, response="Recipe was successfully updated")
        except Exception as e:
            return Response(status=400, response="Recipe couldn't be updated.\n" + str(e))


    @api.expect(school_api_model)
    def patch(self, id):
        """Patch a recipe by ID"""
        try:
            if api.payload:
                recipe = School.query.filter_by(id=id).update(dict(**api.payload))
                if recipe:
                    db.session.commit()
                    return {"message": "Updated successfully"}
                return school_no_exists(id)
            return {
                       "message": f"You must have at least one of all of the following fields: {set(school_api_model.keys())}"}, 400
        except Exception as e:
            return return_error_sql(e)
