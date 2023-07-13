import json
from datetime import datetime

from marshmallow import fields, pre_load, pre_dump
from peewee import CharField, DateTimeField, IntegerField, FloatField, ManyToManyField
from playhouse.postgres_ext import *

from flask_app.ext.schema import ma
from flask_app.models.base_model import BaseModel

# Database
from flask_app.models.model_metadata import MetadataSchema


class Ingredient(BaseModel):
    name = CharField(null=False,unique=True)


