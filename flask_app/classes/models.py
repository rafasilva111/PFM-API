import os
from abc import ABC
from datetime import datetime
from enum import Enum

from playhouse.shortcuts import ReconnectMixin

from peewee import TextField, FloatField, CharField, DateTimeField, BooleanField, IntegerField, BlobField, \
    ForeignKeyField, ManyToManyField
from flask_bcrypt import generate_password_hash, check_password_hash
from peewee import Model, MySQLDatabase

db_user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
db_password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"

RECIPES_BACKGROUND_TYPE_LIKED = "LIKED"
RECIPES_BACKGROUND_TYPE_SAVED = "SAVED"
RECIPES_BACKGROUND_TYPE_CREATED = "CREATED"


class ReconectMySQLDatabase(ReconnectMixin, MySQLDatabase, ABC):
    pass


db = ReconectMySQLDatabase(database=database, user=db_user, password=db_password,
                           host=host)


class UNITS_TYPE(Enum):
    GRAMS = "G"
    UNITS = "U"


USER_TYPE_SET = UNITS_TYPE._value2member_map_


class USER_TYPE(Enum):
    NORMAL = "N"
    COMPANY = "C"
    VIP = "V"
    ADMIN = "A"  # (normal, company, vip, admin)


USER_TYPE_SET = USER_TYPE._value2member_map_


class CALENDER_ENTRY_TAG(Enum):
    PEQUENO_ALMOCO = "PEQUENO ALMOÇO"
    LANCHE_DA_MANHA = "LANCHE DA MANHÃ"
    ALMOCO = "ALMOÇO"
    LANCHE_DA_TARDE = "LANCHE DA TARDE"  # (normal, company, vip, admin)
    JANTAR = "JANTAR"  # (normal, company, vip, admin)
    CEIA = "CEIA"  # (normal, company, vip, admin)


CALENDER_ENTRY_TAG_SET = CALENDER_ENTRY_TAG._value2member_map_


class PROFILE_TYPE(Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


PROFILE_TYPE_SET = PROFILE_TYPE._value2member_map_


class BaseModel(Model):
    class Meta:
        database = db


''' User '''


class User(BaseModel):
    # __tablename__ = "user"
    name = CharField(null=False)
    birth_date = DateTimeField(null=False)
    email = CharField(unique=True, null=False)
    password = CharField(null=False)

    description = CharField(default="")  # max length 255

    profile_type = CharField(default="PRIVATE")  # (protect, private, public)
    verified = BooleanField(default=False)
    user_type = CharField(default="N")  # (normal, company, vip, admin)
    img_source = CharField(default="")
    rating = FloatField(default=0.0)

    activity_level = FloatField(default=-1)
    height = FloatField(default=-1)
    sex = CharField(default="NA")
    weight = FloatField(default=-1)
    age = CharField(null=False)

    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())

    def hash_password(self, password):
        return generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class FollowRequest(BaseModel):
    follower = ForeignKeyField(User, backref='followers')
    followed = ForeignKeyField(User, backref='followeds')
    state = BooleanField(default=False)

    class Meta:
        db_table = 'follow_request'


class Follow(BaseModel):
    follower = ForeignKeyField(User, backref='followers')
    followed = ForeignKeyField(User, backref='followeds')


''' Recipe '''


class NutritionInformation(BaseModel):
    energia = CharField()
    energia_perc = CharField()
    gordura = CharField()
    gordura_perc = CharField()
    gordura_saturada = CharField()
    gordura_saturada_perc = CharField()
    hidratos_carbonos = CharField()
    hidratos_carbonos_perc = CharField(
        null=True)  ## TODO depois de o hugo fazer os calculos automaticos remover null=True
    hidratos_carbonos_acucares = CharField()
    hidratos_carbonos_acucares_perc = CharField(
        null=True)  ## TODO depois de o hugo fazer os calculos automaticos remover null=True
    fibra = CharField()
    fibra_perc = CharField()
    proteina = CharField()
    proteina_perc = CharField(null=True)  ## TODO depois de o hugo fazer os calculos automaticos remover null=True

    class Meta:
        db_table = 'nutrition_information'


class Recipe(BaseModel):
    title = CharField(null=False)
    description = CharField(null=False)
    img_source = CharField(null=True)
    verified = BooleanField(default=False)

    difficulty = CharField(null=True)
    portion = CharField(null=True)
    time = CharField(null=True)

    views = IntegerField(default=0, null=False)
    preparation = BlobField(null=False)

    created_by = ForeignKeyField(User, backref="created_recipes")
    nutrition_information = ForeignKeyField(NutritionInformation, backref='recipe', null=True, on_delete='CASCADE')

    rating = FloatField(default=0.0)
    source_rating = FloatField(null=True)
    source_link = CharField(null=True)

    created_date = DateTimeField(default=datetime.now(), null=False)
    updated_date = DateTimeField(default=datetime.now(), null=False)


class RecipeBackground(BaseModel):
    user = ForeignKeyField(User, backref="recipes")
    recipe = ForeignKeyField(Recipe, backref="backgrounds")
    type = CharField(null=False)  # (liked, saved)

    class Meta:
        db_table = 'recipe_background'


class Tag(BaseModel):
    title = CharField(null=False, unique=True)
    recipes = ManyToManyField(Recipe, backref='tags')


RecipeTagThrough = Recipe.tags.get_through_model()


class Ingredient(BaseModel):
    name = CharField(null=False, unique=True)


class IngredientQuantity(BaseModel):
    ingredient = ForeignKeyField(Ingredient, backref="ingredient_base")
    recipe = ForeignKeyField(Recipe, backref="ingredients")
    quantity_original = CharField(null=False)
    quantity_normalized = FloatField(null=True)
    units_normalized = CharField(default="G")

    class Meta:
        db_table = 'recipe_ingredient_quantity'


class Comment(BaseModel):
    text = CharField(null=False)
    recipe = ForeignKeyField(Recipe, backref='comments')
    user = ForeignKeyField(User, backref='comments')
    created_date = DateTimeField(default=datetime.now, null=False)
    updated_date = DateTimeField(default=datetime.now, null=False)


""" Calendar """


class CalendarEntry(BaseModel):
    recipe = ForeignKeyField(Recipe, backref='recipe')
    user = ForeignKeyField(User, backref='user')
    tag = CharField(null=False)  # Pequeno almoço, Lanche da manhã, Almoço, Lanche da tarde ,Jantar , Ceia
    created_date = DateTimeField(default=datetime.now, null=False)
    realization_date = DateTimeField(null=False)
    checked_done = BooleanField(default=False)

    class Meta:
        db_table = 'calendar_entrys'


''' Miscellanius '''


class TokenBlocklist(BaseModel):
    jti = CharField()
    created_at = DateTimeField(default=datetime.now())

    class Meta:
        db_table = 'token_block_list'
