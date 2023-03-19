import re
from datetime import datetime
from enum import Enum
from flask_bcrypt import generate_password_hash, check_password_hash
from marshmallow import fields, validates, pre_dump, pre_load
from marshmallow_enum import EnumField
from peewee import TextField, FloatField, CharField, DateTimeField, BooleanField

from flask_app.ext.bycrypt import bcrypt
from flask_app.ext.schema import ma
from flask_app.models.base_model import BaseModel

# Enum

PROFILE_TYPE = {"NORMAL", "VIP", "ADMIN"}
USER_TYPE = {"PUBLIC", "PRIVATE"}
SEXES = {"M", "F", "NA"}


# Database

class User(BaseModel):
    # __tablename__ = "user"
    first_name = TextField(null=False)
    last_name = TextField(null=False)
    birth_date = DateTimeField(null=False)
    email = TextField(unique=True, null=False)
    password = TextField(null=False)

    profile_type = CharField(default="private")  # (protect, private, public)
    verified = BooleanField(default=False)
    user_type = CharField(default="N")  # (normal, vip, admin)
    img_source = CharField(null=True)

    activity_level = FloatField(null=True)
    height = FloatField(null=True)
    sex = CharField(null=True)
    weight = FloatField(null=True)
    age = CharField(null=False)

    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())

    def hash_password(self, password):
        return generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


# Schemas

def get_user_schema():
    return UserSchema


class UserSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    birth_date = fields.DateTime(format='%d/%m/%Y', required=True)
    email = fields.Email(required=True)
    password = fields.String(load_only=True)

    profile_type = fields.String(validate=lambda x: x in PROFILE_TYPE)
    verified = fields.Boolean()
    user_type = fields.String(validate=lambda x: x in USER_TYPE)
    img_source = fields.String()
    activity_level = fields.Float(default=-1)
    height = fields.Float(default=-1)
    sex = fields.String(validate=lambda x: x in SEXES)
    weight = fields.Float(default=-1)
    age = fields.Integer(dump_only=True)

    created_date = fields.DateTime(dump_only=True)
    updated_date = fields.DateTime(dump_only=True)

    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @validates('email')
    def validate_email(self, value):
        if not self.email_regex.match(value):
            raise ma.ValidationError('Invalid email address.')

    @pre_load
    def hash_password(self, data, **kwargs):
        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])
        return data
