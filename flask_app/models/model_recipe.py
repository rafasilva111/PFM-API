import json
from datetime import datetime

from marshmallow import fields, pre_load, pre_dump
from peewee import CharField, DateTimeField, IntegerField, FloatField, ManyToManyField
from playhouse.postgres_ext import *

from flask_app.ext.schema import ma
from flask_app.models.base_model import BaseModel

# Database
from flask_app.models.model_metadata import MetadataSchema




RECIPES_BACKGROUND_TYPE_LIKED = "LIKED"
RECIPES_BACKGROUND_TYPE_SAVED = "SAVED"
RECIPES_BACKGROUND_TYPE_CREATED = "CREATED"

class Recipe(BaseModel):
    title = CharField(null=False)
    description = CharField(null=False)
    img_source = CharField(null=True)

    difficulty = CharField(null=True)
    portion = CharField(null=True)
    time = CharField(null=True)

    views = IntegerField(default=0, null=False)
    ingredients = BlobField(null=False)
    preparation = BlobField(null=False)

    source_rating = FloatField(null=True)
    source_link = CharField(null=True)
    company = CharField(null=True)

    created_date = DateTimeField(default=datetime.now(), null=False)
    updated_date = DateTimeField(default=datetime.now(), null=False)


# Schemas

def get_recipe_schema():
    return RecipeSchema


class IngredientSchema(ma.Schema):
    name = fields.String(required=True)
    quantity = fields.String(required=True)


class PreparationSchema(ma.Schema):
    step = fields.Integer(required=True)
    description = fields.String(required=True)


class RecipeListSchema(ma.Schema):
    metadata = fields.Nested(MetadataSchema, required=True)
    results = fields.List(fields.Nested(lambda: MetadataSchema()))


class RecipeSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    img_source = fields.String(required=False, default="")

    difficulty = fields.String(required=False)
    portion = fields.String(required=False)
    time = fields.String(required=False)

    likes = fields.Integer(default=0, required=False)
    views = fields.Integer(default=0, required=False)
    comments = fields.Integer(default=0, required=False)

    ingredients = fields.Nested(IngredientSchema, required=True, many=True)
    preparation = fields.Nested(PreparationSchema, required=True, many=True)
    nutrition_informations = fields.Dict(required=True)
    backgrounds = fields.List(fields.Dict(), required=True, dump_only=True)
    tags = fields.List(fields.String(), required=True)

    source_rating = fields.String(required=False)
    source_link = fields.String(required=False)
    company = fields.String(required=False)

    created_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')

    class Meta:
        ordered = True

    @pre_dump
    def decode_blobs(self, data, **kwargs):
        if 'ingredients' in data:
            data['ingredients'] = json.loads(data['ingredients'].decode().replace("\'", "\""))
        if 'preparation' in data:
            data['preparation'] = json.loads(data['preparation'].decode().replace("\'", "\""))
        return data

    @pre_dump
    def unlist(self, data, **kwargs):
        data['likes'] = 0
        if 'nutrition_informations' in data:
            data['nutrition_informations'] = data['nutrition_informations'][0]
        if 'backgrounds' in data and data['backgrounds'] != []:
            for background in data['backgrounds']:
                background['user'] = background['user']['first_name'] + " " + background['user']['last_name']

        from flask_app.models import RecipeBackground
        data['likes'] = RecipeBackground.select().where((RecipeBackground.recipe == data['id']) & (RecipeBackground.type == RECIPES_BACKGROUND_TYPE_LIKED)).count()
        if 'tags' in data:
            data['tags'] = [a['title'] for a in data['tags']]
        if 'comments' in data and data['comments'] != []:
            data['comments'] = len(data['comments'])
        else:
            data['comments'] = 0
        return data

    # @pre_dump
    # def unlist(self, data, **kwargs):
    #     if 'nutrition_informations' in data:
    #         data['nutrition_informations'] = data['nutrition_informations'][0]
    #     if 'backgrounds' in data and data['backgrounds'] != []:
    #         data['backgrounds'] = data['backgrounds'][0]
    #         data['backgrounds']['user'] = data['backgrounds']['user']['first_name'] + " " + data['backgrounds']['user'][
    #             'last_name']
    #     if 'tags' in data:
    #         data['tags'] = [a['title'] for a in data['tags']]
    #
    #     if 'comments' in data and data['comments'] != []:
    #         data['comments_count'] = len(data['comments'])
    #
    #     return data

class RecipeSimpleSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    img_source = fields.String(required=False, default="")

    difficulty = fields.String(required=False)
    portion = fields.String(required=False)
    time = fields.String(required=False)

    likes = fields.Integer(default=0, required=False)
    views = fields.Integer(default=0, required=False)

    source_rating = fields.String(required=False)
    source_link = fields.String(required=False)
    company = fields.String(required=False)

    created_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')

    class Meta:
        ordered = True
