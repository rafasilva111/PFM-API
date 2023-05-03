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
from ...models.model_recipe import Recipe as RecipeDB, RecipeSchema, RECIPES_BACKGROUND_TYPE_CREATED, \
    RECIPES_BACKGROUND_TYPE_LIKED, RECIPES_BACKGROUND_TYPE_SAVED
from ...models.model_tag import Tag as TagDB, RecipeTagThrough as RecipeTagThroughDB
from ...models.model_user import User as UserDB
from ...models.model_recipe_background import RecipeBackground as RecipeBackgroundDB, RecipeBackground
from ...models.model_nutrition_information import NutritionInformation as NutritionInformationDB
from ...models.model_comment import Comment as CommentDB
from .errors import return_error_sql, school_no_exists

# Create name space
api = Namespace("Recipes", description="Here are all Recipes endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The recipe id to be search.')
parser.add_argument('string', type=str, help='The string to be search.')
parser.add_argument('user_id', type=int, help='The user id to be search.')

ENDPOINT = "/recipe"


# TODO get recipes by user?

# Create resources
@api.route("/list")
@api.doc("get_recipe_list", model=RecipeDB)
class RecipeListResource(Resource):

    @api.expect(parser)
    def get(self):
        """List recipes by string search and all"""
        # Get args

        args = parser.parse_args()

        string_to_search = args['string']
        user_id = args['user_id']  # todo falta procura por user_id
        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # Pesquisa por String

        if string_to_search:

            # declare response holder

            response_holder = {}

            # build query

            query = RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB) \
                .where(TagDB.title.contains(string_to_search) | RecipeDB.title.contains(string_to_search))

            # metadata

            total_recipes = int(query.count())
            total_pages = math.ceil(total_recipes / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_recipes, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for recipe in query.paginate(page, page_size):
                recipe_model = model_to_dict(recipe, backrefs=True, recurse=True, manytomany=True)
                recipe_schema = RecipeSchema().dump(recipe_model)
                ## add likes to recipe model
                # Todo isto devia de ser adicionado no RecipeSchema num pre-dump, mas não estou a conseguir importar as classes sem imports circulares

                recipe_schema['likes'] = RecipeBackgroundDB.select().where(
                    RecipeBackgroundDB.recipe == recipe).count()

                recipes.append(recipe_schema)

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
        else:

            # declare response holder

            response_holder = {}

            # metadata

            total_recipes = int(RecipeDB.select().count())
            total_pages = math.ceil(total_recipes / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_recipes, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for recipe in RecipeDB.select().paginate(page, page_size):
                recipe_model = model_to_dict(recipe, backrefs=True, recurse=True, manytomany=True)
                recipe_schema = RecipeSchema().dump(recipe_model)
                ## add likes to recipe model
                # Todo isto devia de ser adicionado no RecipeSchema num pre-dump, mas não estou a conseguir importar as classes sem imports circulares

                recipe_schema['likes'] = RecipeBackgroundDB.select().where(
                    RecipeBackgroundDB.recipe == recipe).count()
                recipe_schema['comments'] = CommentDB.select().where(CommentDB.recipe == recipe).count()

                recipes.append(recipe_schema)

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    def post(self):
        json_data = request.get_json()

        # Validate args by loading it into schema

        try:
            recipe_validated = RecipeSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

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
            if 'id' in nutrition_table:
                nutrition_table.pop('id')

            nutrition_information = NutritionInformationDB(**nutrition_table)
            nutrition_information.recipe = recipe
            nutrition_information.save()
            recipe.nutrition_informations = nutrition_information
        except Exception as e:
            recipe.delete_instance(recursive=True)
            return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

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


@api.route("")
class RecipeResource(Resource):

    def get(self):
        """ Get a recipe with ID """

        # Get args

        args = parser.parse_args()

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Invalid arguments...")

        # Get and Serialize db model

        try:
            recipe_record = RecipeDB.get(id=args["id"])
            recipe_model = model_to_dict(recipe_record, backrefs=True, recurse=True, manytomany=True)
            ## add likes to recipe model
            # Todo isto devia de ser adicionado no RecipeSchema num pre-dump, mas não estou a conseguir importar as classes sem imports circulares
            recipe_schema = RecipeSchema().dump(recipe_model)

            recipe_schema['likes'] = RecipeBackgroundDB.select().where(
                RecipeBackgroundDB.recipe == recipe_record).count()

            recipe_schema['comments'] = CommentDB.select().where(CommentDB.recipe == recipe_record).count()


        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe does not exist...")

        return Response(status=200, response=json.dumps(recipe_schema), mimetype="application/json")

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
            # should not reach prod (seria muito mau sinal se for preciso)
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

    @jwt_required()
    def delete(self):
        """Delete a recipe by ID"""

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
        # todo validar se a recipe pertence ao user (middle)
        try:
            recipe = RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe does not exist...")

        try:
            recipe.delete_instance(recursive=True)
        except Exception as e:
            return Response(status=400, response="Recipe could not be deleted.\n" + str(e))

        return Response(status=200, response="Recipe was successfully deleted.")

    # method to update recipe

    @jwt_required()
    def put(self):
        """ Update a recipe by recipe id """

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
            return Response(status=400, response="Recipe couldn't be found by this id.")

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
            recipe.ingredients = str(ingredients).encode()
            # use .decode() to decode

            # build multi to multi relation to tags
            try:
                rows_deleted = TagDB.recipes.get_through_model().delete().where(
                    TagDB.recipes.get_through_model().recipe_id == recipe.get_id()).execute()

                if tags and tags != {} and rows_deleted:
                    for t in tags:
                        tag, created = TagDB.get_or_create(title=t)
                        recipe.tags.add(tag)


            except Exception as e:
                return Response(status=400, response="Tags Table has some error.\n" + str(e))

            try:
                if nutrition_table and nutrition_table != {}:
                    NutritionInformationDB.update(**nutrition_table).where(
                        NutritionInformationDB.recipe == recipe)
            except Exception as e:
                return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

            # finally build full object
            tag.save()
            recipe_background.save()

            recipe.save()
            return Response(status=200, response="Recipe was successfully updated")
        except Exception as e:
            return Response(status=400, response="Recipe couldn't be updated.\n" + str(e))


"""
    Functionality
"""


@api.route("/like")
class RecipeLikeResource(Resource):
    @jwt_required()
    def get(self):
        """ Get a like whit ID """
        # todo esta rota ainda não sei se faz sentido, mas é para fazer na mesma

        return Response(status=200, response="Not implemented yet.")

    @jwt_required()
    def post(self):
        """ Post a like by user on a recipe """

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        recipe_to_be_liked_id = args['id']

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Missing arguments...")

        # Verify existence of the requested ids model's

        try:
            recipe_to_be_liked = RecipeDB.get(recipe_to_be_liked_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe to be liked, couln't be found.")

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="User couln't be found.")

        # fills comment object

        # add like

        recipe_to_be_liked

        recipe_background, created = RecipeBackgroundDB.get_or_create(user=user, recipe=recipe_to_be_liked,
                                                                      type=RECIPES_BACKGROUND_TYPE_LIKED)

        if not created:
            return Response(status=400, response="User already liked this recipe.")

        recipe_background.save()

        return Response(status=201)

    @jwt_required()
    def delete(self):
        """Delete like ( by background id ) """

        # todo isto temos de criar uma var (args['recipe_background']) (median)

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        like_to_be_deleted_id = args['id']

    @jwt_required()
    def delete(self):
        """Delete like ( by recipe id, etc)"""

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        like_to_be_deleted_id = args['id']

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Missing arguments...")

        # query

        query = RecipeBackgroundDB.delete() \
            .where(
            ((RecipeBackgroundDB.recipe == like_to_be_deleted_id) & (RecipeBackgroundDB.user == user_id)) & (
                        RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE_LIKED)).execute()

        if query != 1:
            return Response(status=400, response="User does not like this recipe.")

        return Response(status=204)


@api.route("/likes")
class RecipeLikesResource(Resource):
    @jwt_required()
    @api.expect(parser)
    def get(self):
        """List creates by user"""
        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # gets user auth id

        user_id = get_jwt_identity()

        # declare response holder

        response_holder = {}

        # query
        RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB)

        query = RecipeDB.select(RecipeDB).distinct().join(RecipeBackgroundDB).join(UserDB) \
            .where(UserDB.id == user_id, RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE_LIKED)

        # metadata

        total_recipes = int(query.count())
        total_pages = math.ceil(total_recipes / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_recipes, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        recipes = []
        for item in query.paginate(page, page_size):
            recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
            recipes.append(RecipeSchema().dump(recipe))

        response_holder["result"] = recipes

        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post multiple likes by user on a recipe """
        # todo não sei se faz sentido mas pode ser importante para importar recipes a partir da metada (low)

        return Response(status=200, response="Not implemented yet.")

    @jwt_required()
    def delete(self):
        """Delete multiple likes by user on a recipe"""
        # todo não sei se faz sentido mas pode ser importante para remover recipes a partir da metada (low)

        return Response(status=200, response="Not implemented yet.")


@api.route("/save")
class RecipeSaveResource(Resource):
    @jwt_required()
    def get(self):
        """ Get a save whit ID """
        # todo esta rota ainda não sei se faz sentido, mas é para fazer na mesma (low)

        return Response(status=200, response="Not implemented yet.")

    @jwt_required()
    def post(self):
        """ Post a save by user on a recipe """

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        recipe_to_be_saved_id = args['id']

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Missing arguments...")

        # Verify existence of the requested ids model's

        try:
            recipe_to_be_liked = RecipeDB.get(recipe_to_be_saved_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe to be liked, couln't be found.")

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="User couln't be found.")

        # fills comment object

        recipe_background, created = RecipeBackgroundDB.get_or_create(user=user, recipe=recipe_to_be_liked,
                                                                      type=RECIPES_BACKGROUND_TYPE_SAVED)

        if not created:
            return Response(status=200, response="User already saved this recipe.")

        recipe_background.save()

        return Response(status=201)

    @jwt_required()
    def delete(self):
        """Delete save"""

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        like_to_be_deleted_id = args['id']

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Missing arguments...")

        # query

        RecipeBackgroundDB.delete() \
            .where(
            RecipeBackgroundDB == like_to_be_deleted_id & RecipeBackgroundDB.user == user_id & RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE_SAVED) \
            .execute()

        return Response(status=204)


@api.route("/saves")
class RecipeSavesResource(Resource):
    @jwt_required()
    @api.expect(parser)
    def get(self):
        """List creates by user"""
        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # gets user auth id

        user_id = get_jwt_identity()

        # declare response holder

        response_holder = {}

        # query
        RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB)

        query = RecipeDB.select(RecipeDB).distinct().join(RecipeBackgroundDB).join(UserDB) \
            .where(UserDB.id == user_id, RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE_SAVED)

        # metadata

        total_recipes = int(query.count())
        total_pages = math.ceil(total_recipes / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_recipes, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        recipes = []
        for item in query.paginate(page, page_size):
            recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
            recipes.append(RecipeSchema().dump(recipe))

        response_holder["result"] = recipes

        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post multiple saves by user on a recipe """
        # todo não sei se faz sentido mas pode ser importante para importar recipes a partir da metada (low)

        return Response(status=200, response="Not implemented yet.")

    @jwt_required()
    def delete(self):
        """Delete multiple saves by user on a recipe"""
        # todo não sei se faz sentido mas pode ser importante para remover recipes a partir da metada (low)

        return Response(status=200, response="Not implemented yet.")


@api.route("/create")
class RecipeCreateResource(Resource):
    @jwt_required()
    @api.expect(parser)
    def get(self):
        """Get recipe created by user on id"""
        # todo (median)

        return Response(status=200, response="Not implemented yet.")


@api.route("/creates")
class RecipeCreatesResource(Resource):
    @jwt_required()
    @api.expect(parser)
    def get(self):
        """List creates by user"""
        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # gets user auth id

        user_id = get_jwt_identity()

        # declare response holder

        response_holder = {}

        # query
        RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB)

        query = RecipeDB.select(RecipeDB).distinct().join(RecipeBackgroundDB).join(UserDB) \
            .where(UserDB.id == user_id, RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE_CREATED)

        # metadata

        total_recipes = int(query.count())
        total_pages = math.ceil(total_recipes / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_recipes, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        recipes = []
        for item in query.paginate(page, page_size):
            recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
            recipes.append(RecipeSchema().dump(recipe))

        response_holder["result"] = recipes

        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
