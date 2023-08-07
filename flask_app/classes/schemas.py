import json
import re

import peewee
from flask_bcrypt import generate_password_hash
from marshmallow import fields, validates, pre_dump, pre_load, EXCLUDE
from enum import Enum

from marshmallow_sqlalchemy import ModelConverter

from flask_app.ext.schema import ma

from flask_app.classes.models import *

SEXES = {"M", "F", "NA"}

# Schemas

''' Schemas '''

_metadata_template = {

    "current_page": 0,
    "total_pages": 0,
    "total_items": 0,
    "items_per_page": 0,
    "next": None,
    "previous": None
}


def build_metadata(page, page_size, total_pages, total_units, ENDPOINT):
    _metadata = _metadata_template.copy()
    _metadata['next'] = None
    _metadata['previous'] = None

    if page < total_pages:
        next_link = page + 1
        _metadata['next'] = f"/api/v1{ENDPOINT}?page={next_link}&page_size={page_size}"
    else:
        _metadata.pop('next')
    if page > 1:
        previous_link = page - 1
        _metadata['previous'] = f"/api/v1{ENDPOINT}?page={previous_link}&page_size={page_size}"
    else:
        _metadata.pop('previous')
    _metadata['current_page'] = page
    _metadata['items_per_page'] = page_size
    _metadata['total_pages'] = total_pages
    _metadata['total_items'] = total_units

    return _metadata


class MetadataSchema(ma.Schema):
    page = fields.Integer(required=True)
    page_count = fields.Integer(required=True)
    per_page = fields.Integer(required=True)
    total_count = fields.Integer(required=True)
    links = fields.List(fields.Dict(), required=True)


''' Recipe '''


class IngredientSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class IngredientQuantitySchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    ingredient = fields.Nested(IngredientSchema, required=True)
    quantity_original = fields.String(required=True)
    quantity_normalized = fields.Float(required=False, default=None, allow_none=True)
    units_normalized = fields.String(validate=lambda x: x in USER_TYPE_SET)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class PreparationSchema(ma.Schema):
    step = fields.Integer(required=True)
    description = fields.String(required=True)


class RecipeListSchema(ma.Schema):
    metadata = fields.Nested(MetadataSchema, required=True)
    results = fields.List(fields.Nested(lambda: MetadataSchema()))


class UserSimpleSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    email = fields.Email(required=True)

    description = fields.String(required=False)

    profile_type = fields.String(validate=lambda x: x in PROFILE_TYPE_SET)
    verified = fields.Boolean()
    user_type = fields.String(validate=lambda x: x in USER_TYPE_SET)
    img_source = fields.String(default="")

    class Meta:
        ordered = True
        unknown = EXCLUDE


class RecipeBackgroundSimplifiedSchema(ma.Schema):
    id = fields.Integer(required=True)
    user = fields.Nested(UserSimpleSchema, required=True)
    type = fields.String(required=True)

    class Meta:
        ordered = True


class StringOrEmpty(fields.String):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return super()._serialize(value, attr, obj, **kwargs)


class NutritionInformationSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    energia = fields.String(required=True)
    energia_perc = fields.String(allow_none=True)
    gordura = fields.String(required=True)
    gordura_perc = fields.String(allow_none=True)
    gordura_saturada = fields.String(required=True)
    gordura_saturada_perc = fields.String(allow_none=True)
    hidratos_carbonos = fields.String(required=True)
    hidratos_carbonos_perc = StringOrEmpty()
    hidratos_carbonos_acucares = fields.String(required=True)
    hidratos_carbonos_acucares_perc = StringOrEmpty()
    fibra = fields.String(required=True)
    fibra_perc = fields.String(allow_none=True)
    proteina = fields.String(required=True)
    proteina_perc = StringOrEmpty()

    class Meta:
        ordered = True
        unknown = EXCLUDE


class RecipeSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    img_source = fields.String(required=False, default="")
    verified = fields.Boolean(required=False)

    difficulty = fields.String(required=False)
    portion = fields.String(required=False)
    time = fields.String(required=False)

    likes = fields.Integer(default=0, required=False)
    views = fields.Integer(default=0, required=False)
    comments = fields.Integer(default=0, required=False)

    ingredients = fields.Nested(IngredientQuantitySchema, required=True, many=True)
    preparation = fields.Nested(PreparationSchema, required=True, many=True)
    nutrition_information = fields.Nested(NutritionInformationSchema)
    backgrounds = fields.Nested(RecipeBackgroundSimplifiedSchema, required=True, many=True, dump_only=True)
    tags = fields.List(fields.String(), required=True)
    created_by = fields.Nested(UserSimpleSchema, dump_only=True)

    rating = fields.Float(default=0.0)
    source_rating = fields.String(required=False)
    source_link = fields.String(required=False)
    company = fields.String(required=False)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')

    class Meta:
        ordered = True
        unknown = EXCLUDE

    @pre_dump
    def unlist(self, data, **kwargs):
        # decode blob
        if 'preparation' in data:
            data['preparation'] = json.loads(data['preparation'].decode().replace("\'", "\""))

        data['likes'] = RecipeBackground.select().where(
            (RecipeBackground.recipe == data['id']) & (RecipeBackground.type == RECIPES_BACKGROUND_TYPE_LIKED)).count()

        if 'tags' in data:
            data['tags'] = [a['title'] for a in data['tags']]
        if 'comments' in data and data['comments'] != []:
            data['comments'] = len(data['comments'])
        else:
            data['comments'] = 0
        return data


class RecipeSimpleSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    img_source = fields.String(required=False, default="")

    difficulty = fields.String(required=False)
    portion = fields.String(required=False)
    time = fields.String(required=False)

    likes = fields.Integer(default=0, required=False)
    views = fields.Integer(default=0, required=False)

    rating = fields.String(required=False)
    source_rating = fields.String(required=False)
    source_link = fields.String(required=False)
    company = fields.String(required=False)

    tags = fields.List(fields.String(), required=True)
    created_by = fields.Nested(UserSimpleSchema, dump_only=True)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')

    class Meta:
        ordered = True


class RecipeBackgroundSchema(ma.Schema):
    class Meta:
        model = RecipeBackground
        include_fk = True
        fields = ('__all__',)


class TagSchema(ma.Schema):
    class Meta:
        model = Tag
        include_fk = True
        fields = ('__all__',)


''' User '''


class UserSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    birth_date = fields.DateTime(format='%d/%m/%Y', required=True)
    email = fields.Email(required=True)
    password = fields.String(load_only=True)

    followers = fields.Integer(dump_only=True, default=0)
    followeds = fields.Integer(dump_only=True, default=0)

    followers_request = fields.Integer(dump_only=True, default=0)
    followeds_request = fields.Integer(dump_only=True, default=0)

    description = fields.String(required=False)
    rating = fields.Float(default=0.0)

    profile_type = fields.String(validate=lambda x: x in PROFILE_TYPE_SET)
    verified = fields.Boolean()
    user_type = fields.String(validate=lambda x: x in USER_TYPE_SET)
    img_source = fields.String(default="")
    activity_level = fields.Float(default=-1)
    height = fields.Float(default=-1)
    sex = fields.String(validate=lambda x: x in SEXES)
    weight = fields.Float(default=-1)
    age = fields.Integer(dump_only=True)

    liked_recipes = fields.Nested(RecipeSchema, many=True, dump_only=True)
    saved_recipes = fields.Nested(RecipeSchema, many=True, dump_only=True)
    created_recipes = fields.Nested(RecipeSchema, many=True, dump_only=True)
    # todo apply this to schema like previous ones
    commented_recipes = fields.Nested(RecipeSchema, many=True, dump_only=True)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')

    class Meta:
        ordered = True

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

    @pre_dump()
    def recipes(self, data, **kwargs):

        data['followers'] = len(data['followers'])
        data['followeds'] = len(data['followeds'])

        data['followers_request'] = len(data['followers_request'])
        data['followeds_request'] = len(data['followeds_request'])

        if 'recipes' in data:
            data['liked_recipes'] = []
            data['saved_recipes'] = []
            for r in data['recipes']:
                if r['type'] == RECIPES_BACKGROUND_TYPE_LIKED:
                    data['liked_recipes'].append(r['recipe'])
                elif r['type'] == RECIPES_BACKGROUND_TYPE_SAVED:
                    data['saved_recipes'].append(r['recipe'])
            data.pop('recipes')

        return data


class UserPatchSchema(ma.Schema):
    first_name = fields.String(required=False)
    last_name = fields.String(required=False)
    password = fields.String(load_only=True)
    img_source = fields.String(required=False)
    description = fields.String(required=False)
    activity_level = fields.Float(required=False)
    height = fields.Float(required=False)
    weight = fields.Float(required=False)
    age = fields.Integer(dump_only=False, required=False)
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')
    # patch by admin
    profile_type = fields.String(validate=lambda x: x in PROFILE_TYPE_SET, required=False)
    verified = fields.Boolean(required=False)
    user_type = fields.String(validate=lambda x: x in USER_TYPE_SET, required=False)

    @pre_load
    def hash_password(self, data, **kwargs):
        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])
        return data





class UserPerfilSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    email = fields.Email(required=True)

    followers = fields.Integer(dump_only=True, default=0)
    followeds = fields.Integer(dump_only=True, default=0)

    description = fields.String(required=False)

    profile_type = fields.String(validate=lambda x: x in PROFILE_TYPE_SET)
    verified = fields.Boolean()
    user_type = fields.String(validate=lambda x: x in USER_TYPE_SET)
    img_source = fields.String(default="")
    followed_state = fields.String(validate=lambda x: x in FOLLOWED_STATE_SET)

    class Meta:
        ordered = True
        unknown = EXCLUDE

    @pre_dump()
    def follows(self, data, **kwargs):

        data['followers'] = len(data['followers'])
        data['followeds'] = len(data['followeds'])

        return data


class CommentSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    text = fields.String(required=True, null=False)
    user = fields.Dict(required=True, dump_only=True)
    recipe = fields.Dict(required=True, dump_only=True)
    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S+00:00')
    updated_date = fields.DateTime(dump_only=False, format='%d/%m/%YT%H:%M:%S+00:00')

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


class CalendarEntrySchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    user = fields.Nested(UserSimpleSchema, required=True, dump_only=True)
    recipe = fields.Nested(RecipeSchema, required=True, dump_only=True)
    tag = fields.String(validate=lambda x: x in CALENDER_ENTRY_TAG_SET, required=True)
    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')
    realization_date = fields.DateTime(format='%d/%m/%YT%H:%M:%S', required=True)
    checked_done = fields.Boolean(default=False, dump_only=True)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class CalendarEntryPacthSchema(ma.Schema):
    tag = fields.String(validate=lambda x: x in CALENDER_ENTRY_TAG_SET, allow_none=True, required=False)
    realization_date = fields.DateTime(format='%d/%m/%YT%H:%M:%S', allow_none=True, required=False)
    checked_done = fields.Boolean(allow_none=True, required=False)

    class Meta:
        ordered = True
        unknown = EXCLUDE


''' Miscellanius '''


class LoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE


class CalenderIngredient(ma.Schema):
    name = fields.Str(required=True)
    quantity = fields.Integer(required=True)
    units = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE
