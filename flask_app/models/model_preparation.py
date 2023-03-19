from peewee import CharField, IntegerField, ForeignKeyField
from flask_app.ext.schema import ma

from flask_app.models.base_model import BaseModel
from flask_app.models.model_recipe import Recipe


# Database

class Preparation(BaseModel):
    step_number = IntegerField()
    description = CharField()
    recipe = ForeignKeyField(Recipe, backref='preparations')


# Schemas

def get_preparation_schema():
    return PreparationSchema


class PreparationSchema(ma.Schema):
    class Meta:
        model = Preparation
        include_fk = True
        fields = ('__all__',)
