import json
from datetime import datetime

from marshmallow import fields, pre_load, pre_dump
from peewee import CharField, DateTimeField, IntegerField, FloatField, ManyToManyField
from playhouse.postgres_ext import *

from flask_app.ext.schema import ma
from flask_app.models.base_model import BaseModel


# Database
from flask_app.models.model_metadata import MetadataSchema


class Recipe(BaseModel):
    title = CharField(null=False)
    description = CharField(null=False)
    img_source = CharField(null=True)

    difficulty = CharField(null=True)
    portion = CharField(null=True)
    time = CharField(null=True)

    likes = IntegerField(default=0, null=False)
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


class RecipeListSchema(ma.Schema):
    metadata = fields.Nested(MetadataSchema,required=True)
    results = fields.List(fields.Nested(lambda: MetadataSchema()))


class RecipeSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    img_source = fields.String(required=False,default="")

    difficulty = fields.String(required=False)
    portion = fields.String(required=False)
    time = fields.String(required=False)

    likes = fields.Integer(default=0, required=False)
    views = fields.Integer(default=0, required=False)

    ingredients = fields.Dict(required=True)
    nutrition_informations = fields.Dict(required=True)
    preparation = fields.Dict(required=True)
    backgrounds = fields.Dict(required=True,dump_only=True)
    tags = fields.List(fields.String(), required=True)

    source_rating = fields.String(required=False)
    source_link = fields.String(required=False)
    company = fields.String( required=False)

    created_date = fields.DateTime(dump_only=True,format='%Y-%m-%dT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True,format='%Y-%m-%dT%H:%M:%S+00:00')

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
        if 'nutrition_informations' in data:
            data['nutrition_informations'] = data['nutrition_informations'][0]
        if 'backgrounds' in data:
            data['backgrounds'] = data['backgrounds'][0]
            data['backgrounds']['user'] = data['backgrounds']['user']['first_name']+" "+data['backgrounds']['user']['last_name']
        if 'tags' in data:
            data['tags'] = [a['title'] for a in data['tags']]
        return data


    # {
    #     "name": "farinha de amêndoa Pingo Doce Biológico",
    #     "value": "200 g"
    # },
    # {
    #     "name": "farinha de amêndoa Pingo Doce Biológico",
    #     "value": "200 g"
    # },
    # {
    #     "name": "farinha de amêndoa Pingo Doce Biológico",
    #     "value": "200 g"
    # },
    # {
    #     "name": "farinha de amêndoa Pingo Doce Biológico",
    #     "value": "200 g"
    # }