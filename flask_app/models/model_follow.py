from peewee import CharField, IntegerField, ManyToManyField, BooleanField, ForeignKeyField

from flask_app.ext.schema import ma
from flask_app.models.model_recipe import Recipe
from flask_app.models.base_model import BaseModel
from marshmallow import fields

# Database

class Follow(BaseModel):
    follower = ForeignKeyField(Recipe, backref='followers')
    followed = ForeignKeyField(Recipe, backref='followeds')


# Schema


class FollowSchema(ma.Schema):
    first_name = fields.String(required=True)

    created_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')