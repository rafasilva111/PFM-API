from peewee import CharField, IntegerField, ManyToManyField, BooleanField, ForeignKeyField

from flask_app.ext.schema import ma
from flask_app.models.model_user import User, UserSchema
from flask_app.models.base_model import BaseModel
from marshmallow import fields, pre_dump


# Database

class Follow(BaseModel):
    follower = ForeignKeyField(User, backref='followers')
    followed = ForeignKeyField(User, backref='followeds')


# Schema


class FollowersSchema(ma.Schema):
    follower = fields.Dict(required=True, dump_only=True)
    created_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')

    @pre_dump
    def prepare_followed(self, data, **kwargs):
        if 'follower' in data:
            data['follower'] = UserSchema().dump(data['follower'])
        return data


class FollowedsSchema(ma.Schema):
    followed = fields.Dict(required=True, dump_only=True)
    created_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S+00:00')

    @pre_dump
    def prepare_user_and_recipe(self, data, **kwargs):
        if 'followed' in data:
            data['followed'] = UserSchema().dump(data['followed'])
        return data
