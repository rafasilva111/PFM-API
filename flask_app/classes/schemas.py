import json
import pickle
import re
from datetime import timedelta

from marshmallow import fields, validates, pre_dump, pre_load, ValidationError

from flask_app.classes.models import *
from flask_app.ext.schema import ma

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
    id = fields.Integer(required=False)
    name = fields.String(required=True)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class RecipeIngredientQuantitySchema(ma.Schema):
    id = fields.Integer(required=False)
    ingredient = fields.Nested(IngredientSchema, required=True)
    quantity_original = fields.String(required=True)
    quantity_normalized = fields.Float(required=False, default=None, allow_none=True)
    units_normalized = fields.String(required=False)  ## this required should be absolute

    class Meta:
        ordered = True
        unknown = EXCLUDE


class TagSchema(ma.Schema):
    id = fields.Integer(required=True, dump_only=True)
    title = fields.String(required=True)


class PreparationSchema(ma.Schema):
    step = fields.Integer(required=True)
    description = fields.String(required=True)


class RecipeListSchema(ma.Schema):
    metadata = fields.Nested(MetadataSchema, required=True)
    results = fields.List(fields.Nested(lambda: MetadataSchema()))


class UserSimpleSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    username = fields.String(required=True)
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
    type = fields.String(validate=lambda x: x in RECIPES_BACKGROUND_TYPE_SET)

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

    ingredients = fields.Nested(RecipeIngredientQuantitySchema, required=True, many=True)
    preparation = fields.Nested(PreparationSchema, required=True, many=True)
    nutrition_information = fields.Nested(NutritionInformationSchema)
    tags = fields.Nested(TagSchema, many=True)
    created_by = fields.Nested(UserSimpleSchema, dump_only=True)

    rating = fields.Float(default=0.0)
    source_rating = fields.String(required=False)
    source_link = fields.String(required=False)
    company = fields.String(required=False)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')

    class Meta:
        ordered = True
        unknown = EXCLUDE

    @pre_dump
    def unlist(self, data, **kwargs):
        # decode blob

        if data.preparation:
            data.preparation = pickle.loads(data.preparation)

        data.likes = RecipeBackground.select().where(
            (RecipeBackground.recipe == data.id) & (
                    RecipeBackground.type == RECIPES_BACKGROUND_TYPE.LIKED.value)).count()

        data.comments = data.comments.count()
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

    tags = fields.Nested(TagSchema, required=True, many=True)
    created_by = fields.Nested(UserSimpleSchema, dump_only=True)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')

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


class RecipeReportSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True)
    message = fields.String(required=True)

    recipe = fields.Nested(RecipeSchema, dump_only=True)
    user = fields.Nested(UserSimpleSchema, dump_only=True)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')

    class Meta:
        unknown = EXCLUDE
        ordered = True


''' User '''


class UserSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    username = fields.String(required=True)
    birth_date = fields.DateTime(format='%d/%m/%Y', required=True)
    email = fields.Email(required=True)
    password = fields.String(load_only=True)

    fmc_token = fields.String(required=False)

    followers = fields.Integer(dump_only=True, default=0)
    followeds = fields.Integer(dump_only=True, default=0)

    followers_request = fields.Integer(dump_only=True, default=0)
    followeds_request = fields.Integer(dump_only=True, default=0)

    description = fields.String(required=False)
    rating = fields.Float(default=0.0)

    user_portion = fields.Integer(default=-1)

    profile_type = fields.String(validate=lambda x: x in PROFILE_TYPE_SET)
    verified = fields.Boolean()
    user_type = fields.String(validate=lambda x: x in USER_TYPE_SET)
    img_source = fields.String(default="")
    activity_level = fields.Float(default=-1)
    height = fields.Float(default=-1)
    sex = fields.String(validate=lambda x: x in SEXES)
    weight = fields.Float(default=-1)
    age = fields.Integer(dump_only=True, default=0)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')

    class Meta:
        ordered = True

    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @validates('birth_date')
    def validate_birth_date(self, value):
        age = (datetime.now() - value) // timedelta(days=365.25)
        if not age >= 12:
            raise ValidationError('You must be at least 12 years old')

    @validates('height')
    def validate_height(self, value):
        if not (300 > value > 100):
            raise ValidationError('You must be between 100 cm and 300 cm')

    @validates('weight')
    def validate_weight(self, value):
        if not (200 > value > 30):
            raise ValidationError('You must be between 30 kg and 200 kg')

    @pre_load
    def hash_password(self, data, **kwargs):
        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])
        return data

    @pre_dump()
    def recipes(self, data, **kwargs):

        data.followers = data.followers.count()
        data.followeds = data.followeds.count()

        data.followers_request = data.followers_request.count()
        data.followeds_request = data.followeds_request.count()

        return data


class UserPatchSchema(ma.Schema):
    name = fields.String(required=False)

    sex = fields.String(validate=lambda x: x in SEXES)
    username = fields.String(required=False)
    password = fields.String(required=False,load_only=False)
    old_password = fields.String(required=False,load_only=False)
    img_source = fields.String(required=False)
    fmc_token = fields.String(required=False)
    description = fields.String(required=False)

    birth_date = fields.DateTime(format='%d/%m/%Y', required=False)
    user_portion = fields.Integer(required=False)

    activity_level = fields.Float(required=False)
    height = fields.Float(required=False)
    weight = fields.Float(required=False)


    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')
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
    username = fields.String(required=True)
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
        data.followers = data.followers.count()
        data.followeds = data.followeds.count()

        return data


class CommentSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    text = fields.String(required=True, null=False)
    user = fields.Nested(UserSchema, dump_only=True)
    recipe = fields.Nested(RecipeSimpleSchema, dump_only=True)
    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')

    class Meta:
        ordered = True
        unknown = EXCLUDE


class CalenderEntryRecipeSchema(ma.Schema):
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

    ingredients = fields.Nested(RecipeIngredientQuantitySchema, required=True, many=True)
    preparation = fields.Nested(PreparationSchema, required=True, many=True)
    nutrition_information = fields.Nested(NutritionInformationSchema)
    tags = fields.List(fields.String(), required=True)
    created_by = fields.Nested(UserSimpleSchema, dump_only=True)

    rating = fields.Float(default=0.0)
    source_rating = fields.String(required=False)
    source_link = fields.String(required=False)
    company = fields.String(required=False)

    created_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')
    updated_date = fields.DateTime(dump_only=True, format='%d/%m/%YT%H:%M:%S')

    class Meta:
        ordered = True
        unknown = EXCLUDE

    @pre_dump
    def unlist(self, data, **kwargs):
        # decode blob
        if 'preparation' in data:
            data['preparation'] = json.loads(data['preparation'].decode().replace("\'", "\""))

        data['likes'] = RecipeBackground.select().where(
            (RecipeBackground.recipe == data['id']) & (
                    RecipeBackground.type == RECIPES_BACKGROUND_TYPE.LIKED.value)).count()

        if 'tags' in data:
            data['tags'] = [a['title'] for a in data['tags']]
        if 'comments' in data and data['comments'] != []:
            data['comments'] = len(data['comments'])
        else:
            data['comments'] = 0
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


## check multiple calender entrys

class CalenderEntryUpdateSchema(ma.Schema):
    id = fields.Integer(required=True)
    state = fields.Boolean(required=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class CalenderEntryListUpdateSchema(ma.Schema):
    calender_entry_state_list = fields.List(fields.Nested(CalenderEntryUpdateSchema, required=True))

    class Meta:
        unknown = EXCLUDE
        ordered = True


class CalendarEntrySimpleSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    tag = fields.String(validate=lambda x: x in CALENDER_ENTRY_TAG_SET, allow_none=True, required=False)
    recipe = fields.Nested(RecipeSchema, many=False, dump_only=True)
    realization_date = fields.DateTime(format='%d/%m/%YT%H:%M:%S', allow_none=True, required=False)
    checked_done = fields.Boolean(allow_none=True, required=False)

    class Meta:
        ordered = True
        unknown = EXCLUDE


""" Shopping List"""


class ShoppingIngredientSchema(ma.Schema):
    id = fields.Integer(required=False)
    ingredient = fields.Nested(IngredientSchema, required=True)
    checked = fields.Boolean(default=False)
    quantity = fields.Float(required=True)
    extra_quantity = fields.Float(required=False, default=None, allow_none=True)
    units = fields.String(required=True)
    extra_units = fields.String(required=False, default=None, allow_none=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class ShoppingListPatchSchema(ma.Schema):
    name = fields.String(required=False)
    archived = fields.Boolean(required=False)
    shopping_ingredients = fields.List(fields.Nested(ShoppingIngredientSchema, required=True), required=False)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class ShoppingListSchema(ma.Schema):
    id = fields.Integer(required=False, dump_only=True)
    name = fields.String(required=False, allow_none=True)
    updated_date = fields.DateTime(format='%d/%m/%YT%H:%M:%S', required=False, dump_only=True, allow_none=True)
    created_date = fields.DateTime(format='%d/%m/%YT%H:%M:%S', required=False, dump_only=True)
    shopping_ingredients = fields.List(fields.Nested(ShoppingIngredientSchema, required=True))
    archived = fields.Boolean(default=False)

    class Meta:
        unknown = EXCLUDE
        ordered = True


class UserToFollow(ma.Schema):
    request_sent = fields.Boolean(default=False)
    user = fields.Nested(UserSimpleSchema, required=True)

    class Meta:
        unknown = EXCLUDE
        ordered = True


''' Miscellanius '''


class NotificationSchema(ma.Schema):
    id = fields.Integer(required=False)
    title = fields.String(required=False, allow_none=True)
    message = fields.String(required=False, allow_none=True)
    user = fields.String(required=False, allow_none=True)
    created_date = fields.DateTime(format='%d/%m/%YT%H:%M:%S', required=False, dump_only=True)
    seen = fields.Boolean(default=False)
    type = fields.Integer(required=False)

    class Meta:
        unknown = EXCLUDE


class ApplicationReport(BaseModel):
    title = CharField(null=False)
    message = CharField(null=False)
    user = ForeignKeyField(User, backref='aplication_report')
    created_date = DateTimeField(default=datetime.now, null=False)


class ApplicationReportSchema(ma.Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True)
    message = fields.String(required=True)
    archived = fields.Boolean(dump_only=True)
    user = fields.Nested(UserSimpleSchema, dump_only=True)
    created_date = fields.DateTime(format='%d/%m/%YT%H:%M:%S', dump_only=True)


class LoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

    class Meta:
        unknown = EXCLUDE
