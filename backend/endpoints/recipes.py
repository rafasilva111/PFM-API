import datetime
import json
import math

from flask import request, Response, jsonify
from flask_restful import reqparse, Resource, abort

from backend.dbManager import Recipe as RecipeDB, Preparation, Nutrition_Information, Tags, Ingredients
from backend.dtos import RecipeDTO

parser = reqparse.RequestParser()
parser.add_argument('page')
parser.add_argument('page_size')
parser.add_argument('id')


class Recipe(Resource):
    response_placeholder = {
        "_metadata":
            {
                "page": 5,
                "page_count": 20,
                "per_page": 20,
                "total_count": 521,
                "Links": [
                    {"self": "/products?page=5&per_page=20"},
                    {"first": "/products?page=0&per_page=20"},
                    {"previous": "/products?page=4&per_page=20"},
                    {"next": "/products?page=6&per_page=20"},
                    {"last": "/products?page=26&per_page=20"},
                ]
            },
        "results": []
    }

    # /recipe
    def get(self):
        args = parser.parse_args()
        page = args['page'] if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 20

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        response_holder = self.response_placeholder

        # metadata

        total_recipes = int(RecipeDB.select().count())
        total_pages = math.ceil(total_recipes / page_size)
        response_holder['_metadata']['Links'] = []

        if page < total_pages:
            next_link = page + 1
            response_holder['_metadata']['Links'].append({"next": f"/products?page={next_link}&page_size={page_size}"},
                                                         )
        if page > total_pages:
            previous_link = page - 1
            response_holder['_metadata']['Links'].append(
                {"previous": f"/products?page={previous_link}&page_size={page_size}"})

        response_holder['_metadata']['Links'].append({"first": f"/products?page=1&page_size={page_size}"})
        response_holder['_metadata']['Links'].append({"last": f"/products?page={total_pages}&page_size={page_size}"})

        response_holder['_metadata']['page'] = page
        response_holder['_metadata']['per_page'] = page_size
        response_holder['_metadata']['page_count'] = total_pages
        response_holder['_metadata']['total_count'] = total_recipes

        recipes = []
        for item in RecipeDB.select().paginate(page, page_size):
            recipes.append(RecipeDTO(id=item.id, title=item.title, description=item.description,
                                     created_date=item.created_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                     updated_date=item.updated_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                     img_source=item.img_source,
                                     difficulty=item.difficulty, portion=item.portion, time=item.time, likes=item.likes,
                                     source_rating=item.source_rating,
                                     views=item.views, tags=item.tags, ingredients=item.ingredients,
                                     preparations=item.preparations, nutrition_informations=item.nutrition_informations
                                     ).__dict__)

        response_holder["results"] = recipes

        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    def post(self):
        data = request.get_json()

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
            if data['source_rating'] and data['source_rating'] != '':
                source_rating = float(data['source_rating'])
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
        recipeDB.source_rating = source_rating
        recipeDB.save()

        preparations = []

        try:
            if data['preparation'] and data['preparation'] != {}:
                for k in data['preparation']:
                    preparation = Preparation()
                    preparation.step_number = k
                    preparation.description = data['preparation'][k]
                    preparation.recipe = recipeDB
                    preparations.append(preparation)
        except Exception as e:
            recipeDB.delete()
            return Response(status=400, response="Preparation has some error.\n" + str(e))

        nutrition_informations = []
        try:
            if data['nutrition_table'] and data['nutrition_table'] != {}:
                nutrition_information = Nutrition_Information()
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
            return Response(status=400, response="Nutrition Table has some error.\n" + str(e))

        tags = []
        try:
            if data['tags'] and data['tags'] != {}:
                for t in data['tags']:
                    tag = Tags()
                    tag.title = t
                    tag.save()
                    tag.recipes.add(recipeDB)
                    tag.save()
                    tags.append(tag)

        except Exception as e:
            recipeDB.delete()
            for a in tags:
                a.delete()
            return Response(status=400, response="Tags Table has some error.\n" + str(e))

        ingredients = []
        try:
            if data['ingredients'] and data['ingredients'] != {}:
                for t in data['ingredients']:
                    ingridient = Ingredients()
                    ingridient.name = t
                    ingridient.quantity = data['ingredients'][t]
                    ingridient.save()
                    ingridient.recipes.add(recipeDB)
                    ingridient.save()
                    ingredients.append(ingridient)
        except Exception as e:
            recipeDB.delete()
            for a in tags:
                a.delete()
            for a in ingredients:
                a.delete()
            return Response(status=400, response="Ingridients Table has some error.\n" + str(e))

        for a in nutrition_informations:
            a.save()

        for a in preparations:
            a.save()

        return Response(status=201)

    def put(self):
        data = request.get_json()[0]
        args = parser.parse_args()

        #validate parameters

        try:
            id = args['id']
        except:
            return Response(status=409, response="You must supply id.")

        try:
            recipe = RecipeDB.get(id=id)
        except:
            return Response(status=409, response="This id doesnt correspond to any object.")


        #validate json

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
