import re
from datetime import datetime
from marshmallow import fields, Schema, validates, pre_load, EXCLUDE
from peewee import CharField, DateTimeField
from flask_bcrypt import generate_password_hash
from flask_app.models.base_model import BaseModel
from flask_app.ext.schema import ma


# Schemas

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE


# Database

class TokenBlocklist(BaseModel):

    jti = CharField()
    created_at = DateTimeField(default=datetime.now())

    class Meta:
        db_table = 'token_block_list'
