from peewee import CharField, IntegerField, ManyToManyField, BooleanField

from flask_app.ext.schema import ma
from flask_app.models.model_recipe import Recipe
from flask_app.models.base_model import BaseModel


# Database

class Tag(BaseModel):
    title = CharField(null=False, unique=True)
    recipes = ManyToManyField(Recipe, backref='tags')


RecipeTagThrough = Recipe.tags.get_through_model()


# Schema

def get_tag_schema():
    return TagSchema


class TagSchema(ma.Schema):
    class Meta:
        model = Tag
        include_fk = True
        fields = ('__all__',)
