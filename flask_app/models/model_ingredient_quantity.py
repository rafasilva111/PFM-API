import json
from datetime import datetime

from marshmallow import fields, pre_load, pre_dump
from peewee import CharField, DateTimeField, IntegerField, FloatField, ManyToManyField
from playhouse.postgres_ext import *

from flask_app.ext.schema import ma
from flask_app.models import Recipe
from flask_app.models.base_model import BaseModel

# Database
from flask_app.models.model_ingredient import Ingredient


class IngredientQuantity(BaseModel):
    ingredient = ForeignKeyField(Ingredient, backref="ingredient_base")
    recipe = ForeignKeyField(Recipe, backref="ingredients")
    quantity_original = CharField(null=False)
    quantity_normalized = FloatField(null=True)

    class Meta:
        db_table = 'recipe_ingredient_quantity'


