from peewee import ForeignKeyField, CharField
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from flask_app.ext.schema import ma
from datetime import datetime

from flask_app.models.base_model import BaseModel
from flask_app.models.model_recipe import Recipe
from flask_app.models.model_user import User



# Database

class RecipeBackground(BaseModel):
    user = ForeignKeyField(User, backref="recipes")
    recipe = ForeignKeyField(Recipe, backref="backgrounds")
    type = CharField(null=False)  # (liked, saved, created)

    class Meta:
        db_table = 'recipe_background'


# Schema

def get_recipe_background_schema():
    return RecipeBackgroundSchema


class RecipeBackgroundSchema(ma.Schema):
    class Meta:
        model = RecipeBackground
        include_fk = True
        fields = ('__all__',)
