import math
from datetime import timezone

import peewee
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource
from marshmallow import ValidationError
from playhouse.shortcuts import model_to_dict

from ...classes.functions import normalize_quantity, block_user_session_id
from ...classes.models import Recipe as RecipeDB, \
    RecipeTagThrough as RecipeTagThroughDB, Tag as TagDB, User as UserDB, RecipeBackground as RecipeBackgroundDB, \
    NutritionInformation as NutritionInformationDB
from ...classes.schemas import *
from ...ext.logger import log

# Create name space
api = Namespace("Recipes", description="Here are all Recipes endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The recipe id to be search.')
parser.add_argument('string', type=str, help='The string to be search.')
parser.add_argument('user_id', type=int, help='The user id to be search.')
parser.add_argument('by', type=str, help='Type of background sort type.')

ENDPOINT = "/recipe"


## Measuring constants

class RECIPES_SORTING_TYPE(Enum):
    DATE = "DATE"
    LIKES = "LIKES"
    SAVES = "SAVES"
    RANDOM = "RANDOM"


RECIPES_SORTING_TYPE_SET = RECIPES_SORTING_TYPE._value2member_map_


# Create resources
@api.route("/list")
@api.doc("get_recipe_list", model=RecipeDB)
class RecipeListResource(Resource):

    @api.expect(parser)
    def get(self):
        """List recipes by string search and all"""
        # logging
        log.info("GET /recipe/list")

        # Get args
        args = parser.parse_args()

        page = args['page'] if args['page'] else 1
        page_size = args['page_size'] if args['page_size'] else 5
        by = str(args['by']) if args['by'] and args['by'] in RECIPES_SORTING_TYPE_SET else None

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # declare response holder

        response_holder = {}

        # query building

        # Pesquisa por String
        if args['string']:

            query = RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB) \
                .where(TagDB.title.contains(args['string']) | RecipeDB.title.contains(args['string']))
        elif args['user_id']:

            # validate if client profile is public
            try:
                user = UserDB.get_by_id(args['user_id'])
            except peewee.DoesNotExist:
                return Response(status=400, response="There is no user whit that id.")

            query = RecipeDB.select().where(RecipeDB.created_by == user)
        else:
            # pesquisa normal
            query = RecipeDB.select()

        # Check if sorted

        if by:
            if by == RECIPES_SORTING_TYPE.DATE.value:

                query = query.order_by(RecipeDB.created_date)

            elif by == RECIPES_SORTING_TYPE.RANDOM.value:

                query = query.order_by(peewee.fn.Rand())
            elif by == RECIPES_SORTING_TYPE.LIKES.value and args['string']:

                likes_subquery = (RecipeBackground
                                  .select(peewee.fn.COUNT(RecipeBackground.id))
                                  .where((RecipeBackground.recipe == RecipeDB.id) &
                                         (RecipeBackground.type == RECIPES_BACKGROUND_TYPE.LIKED.value))
                                  .alias('likes'))

                query = (RecipeDB
                         .select(RecipeDB, likes_subquery)
                         .order_by(peewee.SQL('likes').desc()))
            elif by == RECIPES_SORTING_TYPE.LIKES.value:

                likes_subquery = (RecipeBackground
                                  .select(peewee.fn.COUNT(RecipeBackground.id))
                                  .where((RecipeBackground.recipe == RecipeDB.id) &
                                         (RecipeBackground.type == RECIPES_BACKGROUND_TYPE.LIKED.value))
                                  .alias('likes'))

                query = (RecipeDB
                         .select(RecipeDB, likes_subquery)
                         .order_by(peewee.SQL('likes').desc()))
            elif by == RECIPES_SORTING_TYPE.SAVES.value and args['string']:

                likes_subquery = (RecipeBackground
                                  .select(peewee.fn.COUNT(RecipeBackground.id))
                                  .where((RecipeBackground.recipe == RecipeDB.id) &
                                         (RecipeBackground.type == RECIPES_BACKGROUND_TYPE.LIKED.value))
                                  .alias('saves'))

                query = RecipeDB.select(RecipeDB, likes_subquery).distinct().join(RecipeTagThroughDB).join(TagDB) \
                    .where(TagDB.title.contains(args['string']) | RecipeDB.title.contains(args['string'])).order_by(
                    peewee.SQL('saves').desc())

            elif by == RECIPES_SORTING_TYPE.SAVES.value:

                saves_subquery = (RecipeBackground
                                  .select(peewee.fn.COUNT(RecipeBackground.id))
                                  .where((RecipeBackground.recipe == RecipeDB.id) &
                                         (RecipeBackground.type == RECIPES_BACKGROUND_TYPE.SAVED.value))
                                  .alias('saves'))

                query = (RecipeDB
                         .select(RecipeDB, saves_subquery)
                         .order_by(peewee.SQL('saves').desc()))

        # metadata

        total_recipes = int(query.count())
        total_pages = math.ceil(total_recipes / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_recipes, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        recipes = []
        for recipe in query.paginate(page, page_size):
            recipe_schema = RecipeSchema().dump(recipe)
            recipes.append(recipe_schema)

        response_holder["result"] = recipes
        log.info("Finished GET /recipe/list")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


@api.route("")
class RecipeResource(Resource):

    def get(self):
        """ Get a recipe with ID """

        # logging
        log.info("GET /recipe")

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

            recipe_schema = RecipeSchema().dump(recipe_model)

        except peewee.DoesNotExist:
            log.error("Recipe does not exist...")
            return Response(status=400, response="Recipe does not exist...")

        log.info("Finished GET /recipe")
        return Response(status=200, response=json.dumps(recipe_schema), mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post a recipe by user """
        # logging
        log.info("POST /recipe")

        json_data = request.get_json()

        # gets user auth id

        user_id = get_jwt_identity()

        # Validate args by loading it into schema

        try:
            recipe_validated = RecipeSchema().load(json_data)
        except ValidationError as err:
            log.error("Invalid arguments...")
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
            log.error("User does not exist...")
            return Response(status=400, response="Client couln't be found by this id.")

        # Change get or create needed objects
        # removing because the must be transformed before entity building
        nutrition_table = recipe_validated.pop('nutrition_information')
        preparation = recipe_validated.pop('preparation')
        ingredients = recipe_validated.pop('ingredients')
        tags = recipe_validated.pop('tags')

        # fills recipe object
        recipe = RecipeDB(**recipe_validated)
        recipe.preparation = pickle.dumps(preparation)
        # use .decode() to decode

        # set created by user
        recipe.created_by = user

        # build relation to nutrition_table

        try:
            if nutrition_table and nutrition_table != {}:
                nutrition_information = NutritionInformationDB(**nutrition_table)
                nutrition_information.save()
                recipe.nutrition_information = nutrition_information

        except Exception as e:
            recipe.delete_instance(recursive=True)
            log.error("Nutrition Table has some error...")
            return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

        ## recipe needs to be saved after foreign key's but before multiple to multiple relations
        # because to build these last one recipe needs to already have an id, wich is done by save()
        recipe.save()

        # build multi to multi relation to tags

        try:
            if tags and tags != {}:
                for t in tags:
                    tag, created = TagDB.get_or_create(title=t)
                    tag.save()
                    recipe.tags.add(tag)


        except Exception as e:
            recipe.delete_instance(recursive=True)
            log.error("Tags Table has some error...")
            return Response(status=400, response="Tags Table has some error.\n" + str(e))

        # build multi to multi relation to Ingredient Quantity
        try:
            if ingredients and ingredients != {}:
                for i in ingredients:
                    ingredient, created = Ingredient.get_or_create(name=i['ingredient']['name'])
                    quantity_normalized = float(0)
                    units_normalized = UNITS_TYPE.GRAMS.value
                    extra_quantity_normalized = None
                    extra_units = None
                    if created:
                        ingredient.save()
                    if i['quantity_original']:
                        try:
                            units_normalized, quantity_normalized,extra_quantity_normalized,extra_units = normalize_quantity(i['quantity_original'])
                        except Exception as e:
                            recipe.delete_instance(recursive=True)
                            log.error("Tags Table has some error...")
                            return Response(status=400, response="Ingredients Table has some error.\n" + str(e))

                    ingredient_quantity = RecipeIngredientQuantity(quantity_original=i['quantity_original'],
                                                                   quantity_normalized=quantity_normalized,
                                                                   units_normalized=units_normalized,
                                                                   extra_quantity_normalized=extra_quantity_normalized,
                                                                   extra_units=extra_units)
                    ingredient_quantity.ingredient = ingredient
                    ingredient_quantity.recipe = recipe
                    ingredient_quantity.save()

        except Exception as e:
            recipe.delete_instance(recursive=True)
            log.error("Ingredients Table has some error...")
            return Response(status=400, response="Ingredients Table has some error.\n" + str(e))

        # finally build full object

        recipe.save()

        return Response(status=201)

    @jwt_required()
    def delete(self):
        """Delete a recipe by ID"""

        # logging
        log.info("DELETE /recipe")

        # gets user auth id
        user_id = get_jwt_identity()
        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User does not exist...")
            return Response(status=400, response="Client couldn't be found by this id.")

        # Get args
        args = parser.parse_args()

        # gets recipe id
        recipe_id = args["id"]

        # Validate args

        if not recipe_id:
            log.error("Invalid arguments...")
            return Response(status=400, response="Invalid arguments...")
        # todo validar se a recipe pertence ao user (middle)
        try:
            recipe = RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            log.error("Recipe does not exist...")
            return Response(status=400, response="Recipe does not exist...")

        try:
            recipe.delete_instance(recursive=True)
        except Exception as e:
            log.error("Recipe could not be deleted...")
            return Response(status=400, response="Recipe could not be deleted.\n" + str(e))

        log.info("Finished DELETE /recipe")
        return Response(status=200, response="Recipe was successfully deleted.")

    # method to update recipe

    @jwt_required()
    def put(self):
        """ Update a recipe by recipe id """

        # logging
        log.info("PUT /recipe")

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
            log.error("Invalid arguments...")
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        try:
            recipe = RecipeDB.get(id=recipe_id)
        except peewee.DoesNotExist:
            log.error("Recipe couldn't be found by this id.")
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
            log.error("User does not exist...")
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
                log.error("Tags Table has some error...")
                return Response(status=400, response="Tags Table has some error.\n" + str(e))

            try:
                if nutrition_table and nutrition_table != {}:
                    NutritionInformationDB.update(**nutrition_table).where(
                        NutritionInformationDB.recipe == recipe)
            except Exception as e:
                log.error("Nutrition Table has some error...")
                return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

            # finally build full object
            tag.save()
            recipe.save()
            log.info("Finished PUT /recipe")
            return Response(status=200, response="Recipe was successfully updated")
        except Exception as e:
            log.error("Recipe couldn't be updated...")
            return Response(status=400, response="Recipe couldn't be updated.\n" + str(e))


"""
    Sorting
"""


@api.route("/list/background/sort")
@api.doc("get_recipe_list", model=RecipeDB)
class RecipeListBackgroundSortResource(Resource):

    @api.expect(parser)
    def get(self):
        """List recipes by string search and all"""
        # logging
        log.info("GET /recipe/list")

        # Get args
        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5
        by = f"'{str(args['by'])}'" if args['by'] and args['by'] in RECIPES_BACKGROUND_TYPE_SET else None

        # validate args

        if not by:
            return Response(status=400, response="Parameter by is invalid.")
        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # declare response holder

        response_holder = {}

        # query building

        # Pesquisa por String
        if args['string']:
            query = (RecipeDB
                     .select(RecipeDB, peewee.fn.COUNT(peewee.Case(RecipeBackground.type, [(peewee.SQL(by), 1)]))
                             .alias('like_count'))
                     .distinct()
                     .join(RecipeBackground, peewee.JOIN.LEFT_OUTER)
                     .switch(RecipeDB)
                     .join(RecipeTagThroughDB).join(TagDB)
                     .where(TagDB.title.contains(args['string']) | RecipeDB.title.contains(args['string']))
                     .group_by(RecipeDB.id, RecipeDB.title)
                     .order_by(peewee.SQL('like_count').desc()))


        else:

            query = (RecipeDB
                     .select(RecipeDB, peewee.fn.COUNT(peewee.Case(RecipeBackground.type, [(peewee.SQL(by), 1)]))
                             .alias('like_count'))
                     .distinct()
                     .join(RecipeBackground, peewee.JOIN.LEFT_OUTER)
                     .group_by(RecipeDB.id, RecipeDB.title)
                     .order_by(peewee.SQL('like_count').desc()))

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
            recipes.append(recipe_schema)

        response_holder["result"] = recipes
        log.info("Finished GET /recipe/list")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


"""
    Functionality
"""


@api.route("/like")
class RecipeLikeResource(Resource):
    @jwt_required()
    def get(self):
        """ Get a like with ID """
        # todo esta rota ainda não sei se faz sentido, mas é para fazer na mesma

        return Response(status=200, response="Not implemented yet.")

    @jwt_required()
    def post(self):
        """ Post a like by user on a recipe """

        # logging
        log.info("POST /like")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        recipe_to_be_liked_id = args['id']

        # Validate args

        if not args["id"]:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # Verify existence of the requested ids model's

        try:
            recipe_to_be_liked = RecipeDB.get(recipe_to_be_liked_id)
        except peewee.DoesNotExist:
            log.error("Recipe to be liked, couln't be found.")
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
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        # fills comment object

        # add like

        recipe_background, created = RecipeBackgroundDB.get_or_create(user=user, recipe=recipe_to_be_liked,
                                                                      type=RECIPES_BACKGROUND_TYPE.LIKED.value)

        if not created:
            log.error("User already liked this recipe.")
            return Response(status=400, response="User already liked this recipe.")

        recipe_background.save()

        log.info("Finished POST /like")
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

        # logging
        log.info("DELETE /like")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        like_to_be_deleted_id = args['id']

        # Validate args

        if not args["id"]:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # query

        query = RecipeBackgroundDB.delete() \
            .where(
            ((RecipeBackgroundDB.recipe == like_to_be_deleted_id) & (RecipeBackgroundDB.user == user_id)) & (
                    RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE.LIKED.value)).execute()

        if query != 1:
            log.error("User does not like this recipe.")
            return Response(status=400, response="User does not like this recipe.")

        log.info("Finished DELETE /like")
        return Response(status=204)


@api.route("/likes")
class RecipeLikesResource(Resource):
    @jwt_required()
    @api.expect(parser)
    def get(self):
        """List creates by user"""

        # logging
        log.info("GET /likes")

        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # gets user auth id

        user_id = get_jwt_identity()

        # declare response holder

        response_holder = {}

        # query
        RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB)

        query = RecipeDB.select(RecipeDB).distinct().join(RecipeBackgroundDB).join(UserDB) \
            .where(UserDB.id == user_id, RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE.LIKED.value)

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

        log.info("Finished GET /likes")
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

        # logging
        log.info("POST /save")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        recipe_to_be_saved_id = args['id']

        # Validate args

        if not args["id"]:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # Verify existence of the requested ids model's

        try:
            recipe_to_be_liked = RecipeDB.get(recipe_to_be_saved_id)
        except peewee.DoesNotExist:
            log.error("Recipe to be saved, couln't be found.")
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
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        # fills comment object

        recipe_background, created = RecipeBackgroundDB.get_or_create(user=user, recipe=recipe_to_be_liked,
                                                                      type=RECIPES_BACKGROUND_TYPE.SAVED.value)

        if not created:
            log.error("User already saved this recipe.")
            return Response(status=200, response="User already saved this recipe.")

        recipe_background.save()

        log.info("Finished POST /save")
        return Response(status=201)

    @jwt_required()
    def delete(self):
        """Delete save"""

        # logging
        log.info("DELETE /save")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        like_to_be_deleted_id = args['id']

        # Validate args

        if not args["id"]:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # query

        RecipeBackgroundDB.delete() \
            .where(
            ((RecipeBackgroundDB.recipe == like_to_be_deleted_id) & (RecipeBackgroundDB.user == user_id)) & (
                    RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE.SAVED.value)).execute()

        log.info("Finished DELETE /save")
        return Response(status=204)


@api.route("/saves")
class RecipeSavesResource(Resource):
    @jwt_required()
    @api.expect(parser)
    def get(self):
        """List creates by user"""

        # logging
        log.info("GET /saves")

        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # gets user auth id

        user_id = get_jwt_identity()

        # declare response holder

        response_holder = {}

        # query
        RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB)

        query = RecipeDB.select(RecipeDB).distinct().join(RecipeBackgroundDB).join(UserDB) \
            .where(UserDB.id == user_id, RecipeBackgroundDB.type == RECIPES_BACKGROUND_TYPE.SAVED.value)

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

        log.info("Finished GET /saves")
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

        # logging
        log.info("GET /creates")

        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # gets user auth id

        user_id = get_jwt_identity()

        # declare response holder

        response_holder = {}

        # query
        RecipeDB.select(RecipeDB).distinct().join(RecipeTagThroughDB).join(TagDB)

        query = RecipeDB.select(RecipeDB).distinct().where(RecipeDB.created_by == user_id)

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

        log.info("Finished GET /creates")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


# como não existe backend os admins são alterados diretamente na bd ou então por alguem que já
# o seja

@api.route("/company")
class RecipeListResource(Resource):

    @jwt_required()
    def post(self):
        """Create a new recipe by admin"""
        """This shall be used to create company recipes"""

        # logging
        log.info("POST /recipe/admin")

        json_data = request.get_json()

        ## verify user

        user_id = get_jwt_identity()

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db, so in prod this wont happen
            block_user_session_id()
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        if user.user_type != USER_TYPE.COMPANY.value:
            return Response(status=403, response="User is not a company.")

        # Validate args by loading it into schema

        nutrition_table = json_data.pop('nutrition_information')

        try:
            recipe_validated = RecipeSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        # Change get or create needed objects
        # removing because the must be transformed before entity building
        ingredients = recipe_validated.pop('ingredients')
        preparation = recipe_validated.pop('preparation')

        tags = recipe_validated.pop('tags')

        # fills recipe object
        recipe = RecipeDB(**recipe_validated)
        recipe.preparation = pickle.dumps(preparation)
        recipe.created_by = user

        # build relation to nutrition_table
        if nutrition_table:
            try:
                if 'id' in nutrition_table:
                    nutrition_table.pop('id')

                nutrition_information = NutritionInformationDB(**nutrition_table)
                nutrition_information.save()
                recipe.nutrition_information = nutrition_information
            except Exception as e:
                nutrition_information.delete()
                recipe.delete_instance(recursive=True)
                return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

        recipe.save()
        ## recipe needs to be saved after foreign key's but before multiple to multiple relations
        # because to build these last one recipe needs to already have an id, wich is done by save()

        # build multi to multi relation to tags

        try:
            if tags and tags != {}:
                for t in tags:
                    tag, created = TagDB.get_or_create(title=t['title'])
                    tag.save()
                    recipe.tags.add(tag)


        except Exception as e:

            recipe.delete_instance(recursive=True)
            return Response(status=400, response="Tags Table has some error.\n" + str(e))

        # build multi to multi relation to Ingredient Quantity
        try:
            if ingredients and ingredients != {}:
                for i in ingredients:
                    ingredient, created = Ingredient.get_or_create(name=i['ingredient']['name'])
                    quantity_normalized = float(0)
                    units_normalized = UNITS_TYPE.GRAMS.value
                    extra_quantity_normalized = None
                    extra_units = None
                    if created:
                        ingredient.save()
                    if i['quantity_original']:
                        try:
                            units_normalized, quantity_normalized, extra_quantity_normalized, extra_units = normalize_quantity(
                                i['quantity_original'])
                        except Exception as e:
                            recipe.delete_instance(recursive=True)
                            log.error("Tags Table has some error...")
                            return Response(status=400, response="Ingredients Table has some error.\n" + str(e))

                    ingredient_quantity = RecipeIngredientQuantity(quantity_original=i['quantity_original'],
                                                                   quantity_normalized=quantity_normalized,
                                                                   units_normalized=units_normalized,
                                                                   extra_quantity_normalized=extra_quantity_normalized,
                                                                   extra_units=extra_units)
                    ingredient_quantity.ingredient = ingredient
                    ingredient_quantity.recipe = recipe
                    ingredient_quantity.save()

        except Exception as e:
            recipe.delete_instance(recursive=True)
            log.error("Ingredients Table has some error...")
            return Response(status=400, response="Ingredients Table has some error.\n" + str(e))

        recipe.save()

        log.info("Finished POST /recipe/list")
        return Response(status=201)
