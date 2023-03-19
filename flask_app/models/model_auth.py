import re
from datetime import datetime
from marshmallow import fields, Schema, validates, pre_load
from peewee import CharField, DateTimeField
from flask_bcrypt import generate_password_hash
from flask_app.models.base_model import BaseModel
from flask_app.ext.schema import ma

# Schemas

class LoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)

    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @validates('email')
    def validate_email(self, value):
        if not self.email_regex.match(value):
            raise ma.ValidationError('Invalid email address.')




# Database

class TokenBlocklist(BaseModel):
    jti = CharField()
    created_at = DateTimeField(default=datetime.now())
