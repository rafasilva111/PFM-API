from datetime import datetime
from peewee import CharField, DateTimeField, IntegerField, FloatField

from flask_app.ext.schema import ma
from flask_app.models.base_model import BaseModel


# Database


class Recipe(BaseModel):
    title = CharField(null=False)
    description = CharField(null=False)
    created_date = DateTimeField(default=datetime.now(), null=False)
    updated_date = DateTimeField(default=datetime.now(), null=False)
    img_source = CharField(null=True)

    difficulty = CharField(null=True)
    portion = CharField(null=True)
    time = CharField(null=True)

    likes = IntegerField(default=0, null=False)
    views = IntegerField(default=0, null=False)
    ingredients = CharField(null=False)

    source_rating = FloatField(null=True)
    source_link = CharField(null=True)
    company = CharField(null=True)


# Schemas

def get_recipe_schema():
    return RecipeSchema


class RecipeSchema(ma.Schema):
    class Meta:
        model = Recipe
        include_fk = True
        fields = ('__all__',)
