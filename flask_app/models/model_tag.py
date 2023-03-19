from peewee import CharField, IntegerField, ManyToManyField

from flask_app.ext.schema import ma
from flask_app.models.base_model import BaseModel
from flask_app.models.model_recipe import Recipe


# Database

class Tag(BaseModel):
    step_number = IntegerField()
    description = CharField()
    recipe = ManyToManyField(Recipe, backref='tags')


# Schema

def get_tag_schema():
    return TagSchema


class TagSchema(ma.Schema):
    class Meta:
        model = Tag
        include_fk = True
        fields = ('__all__',)
