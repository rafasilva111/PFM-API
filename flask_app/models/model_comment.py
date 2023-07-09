from datetime import datetime

from peewee import CharField, IntegerField, ManyToManyField, BooleanField, ForeignKeyField, DateTimeField

from flask_app.ext.schema import ma
from flask_app.models.model_recipe import Recipe, RecipeSchema,RecipeSimpleSchema
from flask_app.models.model_user import User, UserSchema
from flask_app.models.base_model import BaseModel
from marshmallow import fields, pre_dump, EXCLUDE


# Database

class Comment(BaseModel):
    text = CharField(null=False)
    recipe = ForeignKeyField(Recipe, backref='comments')
    user = ForeignKeyField(User, backref='comments')
    created_date = DateTimeField(default=datetime.now, null=False)
    updated_date = DateTimeField(default=datetime.now, null=False)

# Schema


class CommentSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    text = fields.String(required=True,null=False)
    user = fields.Dict(required=True,dump_only=True)
    recipe = fields.Dict(required=True,dump_only=True)

    created_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=False, format='%Y-%m-%dT%H:%M:%S+00:00')

    class Meta:
        ordered = True
        unknown = EXCLUDE


    @pre_dump
    def prepare_user_and_recipe(self, data, **kwargs):
        if 'recipe' in data:
            data['recipe'] = RecipeSimpleSchema().dump(data['recipe'])
        if 'user' in data:
            data['user'] = UserSchema().dump(data['user'])
        return data