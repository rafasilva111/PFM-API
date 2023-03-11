import datetime
import json
import math

import peewee
from flask import request, Response, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import reqparse, Resource, abort
from playhouse.shortcuts import model_to_dict

from backend.dbManager import Recipe as RecipeDB, Preparation as PreparationDB, \
    Nutrition_Information as Nutrition_InformationDB, Tags as TagsDB, \
    RecipesBackground as RecipesBackgroundDB, User as UserDB, RecipeTag as RecipeTagDB

from backend.dtos import RecipeDTO
from backend.endpoints.recipe_background import TYPE_CREATED

parser = reqparse.RequestParser()
parser.add_argument('page')
parser.add_argument('page_size')
parser.add_argument('id')
parser.add_argument('string')

RECIPE_ENDPOINT = "/recipe"

response_placeholder = {
    "_metadata":
        {
            "page": 5,
            "page_count": 20,
            "per_page": 20,
            "total_count": 521,
            "Links": [
                {"next": f"/{RECIPE_ENDPOINT}?page=6&per_page=20"},
                {"previous": f"/{RECIPE_ENDPOINT}?page=4&per_page=20"},

            ]
        },
    "results": []
}


class DataDTO:
    key = ''
    value = ""

    def __init__(self, key, value):
        self.key = key
        self.value = value


class Recipe(Resource):
    response_placeholder = {
        "_metadata":
            {
                "page": 1,
                "page_count": 10,
                "per_page": 20,
                "recipes_total": 521,
                "Links": [
                    {"next": f"/{RECIPE_ENDPOINT}?page=6&per_page=20"},
                    {"previous": f"/{RECIPE_ENDPOINT}?page=4&per_page=20"},

                ]
            },
        "recipe_result": []
    }

    # /recipe
    def get(self):

        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        ##Pesquisa por String

        if args['string']:

            # parse arguments

            string_to_search = args['string']

            # get recipes

            query = RecipeDB.select(RecipeDB).distinct().join(RecipeTagDB).join(TagsDB) \
                .where(TagsDB.title.contains(string_to_search) | RecipeDB.title.contains(string_to_search))

            recipes = []
            for item in query.paginate(page, page_size):
                recipes.append(RecipeDTO(id=item.id, title=item.title, description=item.description,
                                         created_date=item.created_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         updated_date=item.updated_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         img_source=item.img_source,
                                         difficulty=item.difficulty, portion=item.portion, time=item.time,
                                         likes=item.likes,
                                         source_rating=item.source_rating,source_link=item.source_link,
                                         views=item.views, tags=item.recipeTag_recipe, ingredients=item.ingredients,
                                         preparations=item.preparations,
                                         nutrition_informations=item.nutrition_informations
                                         ).__dict__)


            # Metadata

            response_holder = self.response_placeholder
            response_holder["recipe_result"] = recipes

            total_recipes = int(query.count())
            total_pages = math.ceil(total_recipes / page_size)
            if total_pages != 1:
                response_holder['_metadata']['Links'] = []

                if page < total_pages:
                    next_link = page + 1
                    response_holder['_metadata']['Links'].append(
                        {"next": f"/{RECIPE_ENDPOINT}?page={next_link}&page_size={page_size}"},
                    )
                if page > 1:
                    previous_link = page - 1
                    response_holder['_metadata']['Links'].append(
                        {"previous": f"/{RECIPE_ENDPOINT}?page={previous_link}&page_size={page_size}"})
            else:
                try:
                    response_holder['_metadata'].pop('Links')
                except Exception as a:
                    #log
                    pass
            response_holder['_metadata']['page'] = page
            response_holder['_metadata']['per_page'] = page_size
            response_holder['_metadata']['page_count'] = total_pages
            response_holder['_metadata']['recipes_total'] = total_recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
        else:

            # metadata

            response_holder = self.response_placeholder
            total_recipes = int(RecipeDB.select().count())
            total_pages = math.ceil(total_recipes / page_size)
            if total_pages != 1:
                response_holder['_metadata']['Links'] = []

                if page < total_pages:
                    next_link = page + 1
                    response_holder['_metadata']['Links'].append(
                        {"next": f"/{RECIPE_ENDPOINT}?page={next_link}&page_size={page_size}"},
                    )
                if page > 1:
                    previous_link = page - 1
                    response_holder['_metadata']['Links'].append(
                        {"previous": f"/{RECIPE_ENDPOINT}?page={previous_link}&page_size={page_size}"})
            else:
                response_holder['_metadata'].pop('Links')
            response_holder['_metadata']['page'] = page
            response_holder['_metadata']['per_page'] = page_size
            response_holder['_metadata']['page_count'] = total_pages
            response_holder['_metadata']['recipes_total'] = total_recipes

            recipes = []
            for item in RecipeDB.select().paginate(page, page_size):
                recipes.append(RecipeDTO(id=item.id, title=item.title, description=item.description,
                                         created_date=item.created_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         updated_date=item.updated_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         img_source=item.img_source,
                                         difficulty=item.difficulty, portion=item.portion, time=item.time,
                                         likes=item.likes,
                                         source_rating=item.source_rating,source_link=item.source_link,
                                         views=item.views, tags=item.recipeTag_recipe, ingredients=item.ingredients,
                                         preparations=item.preparations,
                                         nutrition_informations=item.nutrition_informations
                                         ).__dict__)

            response_holder["recipe_result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    @jwt_required()
    def post(self):
        # Get json body

        data = request.get_json()

        # gets user auth id

        # user_id = get_jwt_identity()

        # Parse body

        title = None
        try:
            if data['title'] and data['title'] != '':
                title = str(data['title']).strip()
        except Exception as e:
            return Response(status=400, response="Title missing.\n" + str(e))

        description = None
        try:
            if data['description'] and data['description'] != '':
                description = str(data['description']).strip()
        except Exception as e:
            return Response(status=400, response="Description missing.\n" + str(e))

        try:
            img_source = None
            if data['img_source'] and data['img_source'] != '':
                img_source = str(data['img_source']).strip()
        except:
            pass

        try:
            difficulty = None
            if data['difficulty'] and data['difficulty'] != '':
                difficulty = str(data['difficulty']).strip()
        except:
            pass

        try:
            portion = None
            if data['portion'] and data['portion'] != '':
                portion = str(data['portion']).strip()
        except:
            pass

        try:
            time = None
            if data['time'] and data['time'] != '':
                time = str(data['time']).strip()
        except:
            pass
        try:
            source_rating = None
            if data['rate'] and data['rate'] != '':
                source_rating = float(data['rate'])
        except:
            pass

        try:
            source_link = None
            if data['source_link'] and data['source_link'] != '':
                source_link = data['source_link']
        except:
            pass
        try:
            RecipeDB.get(title=title, description=description)
            return Response(status=409, response="An object whit the same title and description already exists...")
        except:
            pass

        # Verify existence of the requested ids model's

        try:
            pass
        # user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="Client uuid couln't be found")

        recipeDB = RecipeDB()
        recipeDB.title = title
        recipeDB.description = description
        recipeDB.img_source = img_source
        recipeDB.difficulty = difficulty
        recipeDB.portion = portion
        recipeDB.time = time
        recipeDB.source_rating = source_rating if source_rating else None
        recipeDB.source_link = source_link if source_link else None  # TODO WHEN RECREATING BD PUT THIS TO NULLABLE
        recipeDB.save()

        preparations = []

        try:
            if data['preparation'] and data['preparation'] != {}:
                for k in data['preparation']:
                    preparation = PreparationDB()
                    preparation.step_number = k
                    preparation.description = data['preparation'][k]
                    preparation.recipe = recipeDB
                    preparations.append(preparation)
        except Exception as e:
            recipeDB.delete()
            for a in preparations:
                a.delete()
            return Response(status=400, response="Preparation has some error.\n" + str(e))

        nutrition_informations = []
        try:
            if data['nutrition_table'] and data['nutrition_table'] != {}:
                nutrition_information = Nutrition_InformationDB()
                nutrition_information.energia = data['nutrition_table']['energia']
                nutrition_information.energia_perc = data['nutrition_table']['energia_perc']
                nutrition_information.gordura = data['nutrition_table']['gordura']
                nutrition_information.gordura_perc = data['nutrition_table']['gordura_perc']
                nutrition_information.gordura_saturada = data['nutrition_table']['gordura_saturada']
                nutrition_information.gordura_saturada_perc = data['nutrition_table']['gordura_saturada_perc']
                nutrition_information.hidratos_carbonos = data['nutrition_table']['hidratos_carbonos']
                nutrition_information.hidratos_carbonos_acucares = data['nutrition_table']['hidratos_carbonos_acucares']
                nutrition_information.hidratos_carbonos_acucares_perc = data['nutrition_table'][
                    'hidratos_carbonos_acucares_perc']
                nutrition_information.fibra = data['nutrition_table']['fibra']
                nutrition_information.fibra_perc = data['nutrition_table']['fibra_perc']
                nutrition_information.proteina = data['nutrition_table']['proteina']
                nutrition_information.recipe = recipeDB
                nutrition_informations.append(nutrition_information)
        except Exception as e:
            recipeDB.delete()
            for a in preparations:
                a.delete()
            for a in nutrition_informations:
                a.delete()
            return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

        tags = []
        try:
            if data['tags'] and data['tags'] != {}:
                for t in data['tags']:
                    tag, created = TagsDB.get_or_create(title=t)
                    if created:
                        tag.save()
                        tags.append(tag)  # se for criada caso aja um erro entra na lista dos deletes
                    tag.save()
                    recipe_tag = RecipeTagDB.create(recipe_id=recipeDB.id, tag_id=tag.id)
                    recipe_tag.save()

        except Exception as e:

            for a in preparations:
                a.delete()
            for a in nutrition_informations:
                a.delete()
            for a in tags:
                a.delete()
            recipeDB.delete()
            return Response(status=400, response="Tags Table has some error.\n" + str(e))

        ingredients = ""
        try:
            if data['ingredients'] and data['ingredients'] != {}:
                for t in data['ingredients']:
                    ingredient = f"{t}:{data['ingredients'][t]}//"
                    ingredients = ingredients + ingredient
        except Exception as e:
            recipeDB.delete()
            for a in preparations:
                a.delete()
            for a in tags:
                a.delete()
            for a in nutrition_informations:
                a.delete()
            return Response(status=400, response="Ingridients Table has some error.\n" + str(e))

        recipeDB.ingredients = ingredients
        recipeDB.save()

        for a in preparations:
            a.save()

        for a in nutrition_informations:
            a.save()

        for a in tags:
            a.save()

        # recipe_background_created = RecipesBackgroundDB()
        # recipe_background_created.user = user
        # recipe_background_created.recipe = recipeDB
        # recipe_background_created.type = TYPE_CREATED
        # recipe_background_created.save()

        return Response(status=201)

    @jwt_required()
    def put(self):
        data = request.get_json()
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
            if data['img'] and data['img'] != '':
                recipe.img_source = str(data['img']).strip()
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
            if data['rate'] and data['rate'] != '':
                recipe.source_rating = float(data['rate'])
                # TODO condition < 5 rating?
        except:
            pass
        try:
            img_source = None
            if data['img'] and data['img'] != '':
                recipe.img_source = str(data['img'])
        except:
            pass
        try:
            source_link = None
            if data['source'] and data['source'] != '':
                recipe.source_link = str(data['source'])
        except:
            pass

        preparations = []

        try:
            if data['preparation'] and data['preparation'] != {}:
                for k in data['preparation']:
                    preparation, created = PreparationDB.get_or_create(step_number=int(k), recipe_id=id)
                    preparation.step_number = k
                    preparation.description = data['preparation'][k]
                    preparation.recipe = recipe
                    # preparation.id
                    preparations.append(preparation)
        except Exception as e:
            return Response(status=400, response="Preparation has some error.\n" + str(e))

        nutrition_informations = []
        try:
            if data['nutrition_table'] and data['nutrition_table'] != {}:
                nutrition_information = Nutrition_InformationDB.get(recipe_id=id)
                nutrition_information.energia = data['nutrition_table']['energia']
                nutrition_information.energia_perc = data['nutrition_table']['energia_perc']
                nutrition_information.gordura = data['nutrition_table']['gordura']
                nutrition_information.gordura_perc = data['nutrition_table']['gordura_perc']
                nutrition_information.gordura_saturada = data['nutrition_table']['gordura_saturada']
                nutrition_information.gordura_saturada_perc = data['nutrition_table']['gordura_saturada_perc']
                nutrition_information.hidratos_carbonos = data['nutrition_table']['hidratos_carbonos']
                nutrition_information.hidratos_carbonos_acucares = data['nutrition_table']['hidratos_carbonos_acucares']
                nutrition_information.hidratos_carbonos_acucares_perc = data['nutrition_table'][
                    'hidratos_carbonos_acucares_perc']
                nutrition_information.fibra = data['nutrition_table']['fibra']
                nutrition_information.fibra_perc = data['nutrition_table']['fibra_perc']
                nutrition_information.proteina = data['nutrition_table']['proteina']
                nutrition_information.recipe = recipe
                nutrition_informations.append(nutrition_information)
        except Exception as e:
            return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

        tags = []
        # TODO tags update not working
        try:
            if data['tags'] and data['tags'] != {}:
                for t in data['tags']:

                    tag, created = TagsDB.get_or_create(title=t)
                    if created:
                        tag.save()
                        tags.append(tag)  # se for criada caso aja um erro entra na lista dos deletes
                    tag.recipes.add(recipe)
                    tag.save()

        except Exception as e:
            return Response(status=400, response="Tags Table has some error.\n" + str(e))

        ingredients = []
        # TODO ingredients update not working
        try:
            if data['ingredients'] and data['ingredients'] != {}:
                for t in data['ingredients']:
                    ingredient = f"{t}:{data['ingredients'][t]}//"
                    ingredients = ingredients + ingredient
        except Exception as e:
            return Response(status=400, response="Ingridients Table has some error.\n" + str(e))

        recipe.updated_date = datetime.datetime.now()

        recipe.save()

        for a in preparations:
            a.save()

        for a in nutrition_informations:
            a.save()

        for a in tags:
            a.save()

        for a in ingredients:
            a.save()

        return Response(status=200)

    @jwt_required()
    def delete(self):
        args = parser.parse_args()

        # conn = DBManager(password_file='/run/secrets/db-password')

        return


recipe_blueprint = Blueprint('recipe_blueprint', __name__)


@recipe_blueprint.route('/recipe/bulk', methods=['POST'])
def recipe_bulk_insert():
    # Get json body

    data = request.get_json()

    # Parse body

    title = None
    try:
        if data['title'] and data['title'] != '':
            title = str(data['title']).strip()
    except Exception as e:
        return Response(status=400, response="Title missing.\n" + str(e))

    description = None
    try:
        if data['description'] and data['description'] != '':
            description = str(data['description']).strip()
    except Exception as e:
        return Response(status=400, response="Description missing.\n" + str(e))

    try:
        company = None
        if data['company'] and data['company'] != '':
            company = str(data['company']).strip()
    except:
        pass

    try:
        img_source = None
        if data['img_source'] and data['img_source'] != '':
            img_source = str(data['img_source']).strip()
    except:
        pass

    try:
        difficulty = None
        if data['difficulty'] and data['difficulty'] != '':
            difficulty = str(data['difficulty']).strip()
    except:
        pass

    try:
        portion = None
        if data['portion'] and data['portion'] != '':
            portion = str(data['portion']).strip()
    except:
        pass

    try:
        time = None
        if data['time'] and data['time'] != '':
            time = str(data['time']).strip()
    except:
        pass
    try:
        source_rating = None
        if data['rate'] and data['rate'] != '':
            source_rating = float(data['rate'])
    except:
        pass

    try:
        source_link = None
        if data['source_link'] and data['source_link'] != '':
            source_link = data['source_link']
    except:
        pass
    try:
        RecipeDB.get(title=title, description=description)
        return Response(status=409, response="An object whit the same title and description already exists...")
    except:
        pass

    recipeDB = RecipeDB()
    recipeDB.title = title
    recipeDB.description = description
    recipeDB.company = company
    recipeDB.img_source = img_source
    recipeDB.difficulty = difficulty
    recipeDB.portion = portion
    recipeDB.time = time
    recipeDB.source_rating = source_rating if source_rating else None
    recipeDB.source_link = source_link if source_link else None  # TODO WHEN RECREATING BD PUT THIS TO NULLABLE
    recipeDB.save()

    preparations = []

    try:
        if data['preparation'] and data['preparation'] != {}:
            for k in data['preparation']:
                preparation = PreparationDB()
                preparation.step_number = k
                preparation.description = data['preparation'][k]
                preparation.recipe = recipeDB
                preparations.append(preparation)
    except Exception as e:
        recipeDB.delete()
        for a in preparations:
            a.delete()
        return Response(status=400, response="Preparation has some error.\n" + str(e))

    nutrition_informations = []
    try:
        if data['nutrition_table'] and data['nutrition_table'] != {}:
            nutrition_information = Nutrition_InformationDB()
            nutrition_information.energia = data['nutrition_table']['energia']
            nutrition_information.energia_perc = data['nutrition_table']['energia_perc']
            nutrition_information.gordura = data['nutrition_table']['gordura']
            nutrition_information.gordura_perc = data['nutrition_table']['gordura_perc']
            nutrition_information.gordura_saturada = data['nutrition_table']['gordura_saturada']
            nutrition_information.gordura_saturada_perc = data['nutrition_table']['gordura_saturada_perc']
            nutrition_information.hidratos_carbonos = data['nutrition_table']['hidratos_carbonos']
            nutrition_information.hidratos_carbonos_acucares = data['nutrition_table']['hidratos_carbonos_acucares']
            nutrition_information.hidratos_carbonos_acucares_perc = data['nutrition_table'][
                'hidratos_carbonos_acucares_perc']
            nutrition_information.fibra = data['nutrition_table']['fibra']
            nutrition_information.fibra_perc = data['nutrition_table']['fibra_perc']
            nutrition_information.proteina = data['nutrition_table']['proteina']
            nutrition_information.recipe = recipeDB
            nutrition_informations.append(nutrition_information)
    except Exception as e:
        recipeDB.delete()
        for a in preparations:
            a.delete()
        for a in nutrition_informations:
            a.delete()
        return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

    tags = []
    try:
        if data['tags'] and data['tags'] != {}:
            for t in data['tags']:
                tag, created = TagsDB.get_or_create(title=t)
                if created:
                    tag.save()
                    tags.append(tag)  # se for criada caso aja um erro entra na lista dos deletes
                tag.save()
                recipe_tag = RecipeTagDB.create(recipe_id=recipeDB.id, tag_id=tag.id)
                recipe_tag.save()

    except Exception as e:

        for a in preparations:
            a.delete()
        for a in nutrition_informations:
            a.delete()
        for a in tags:
            a.delete()
        recipeDB.delete()
        return Response(status=400, response="Tags Table has some error.\n" + str(e))

    ingredients = ""
    try:
        if data['ingredients'] and data['ingredients'] != {}:
            for t in data['ingredients']:
                ingredient = f"{t}:{data['ingredients'][t]}//"
                ingredients = ingredients + ingredient
    except Exception as e:
        recipeDB.delete()
        for a in preparations:
            a.delete()
        for a in tags:
            a.delete()
        for a in nutrition_informations:
            a.delete()
        return Response(status=400, response="Ingridients Table has some error.\n" + str(e))

    recipeDB.ingredients = ingredients
    recipeDB.save()

    for a in preparations:
        a.save()

    for a in nutrition_informations:
        a.save()

    for a in tags:
        a.save()

    return Response(status=201)
