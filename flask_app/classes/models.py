import os
from abc import ABC
from datetime import datetime
from enum import Enum

from marshmallow import EXCLUDE
from playhouse.shortcuts import ReconnectMixin

from peewee import TextField, FloatField, CharField, DateTimeField, BooleanField, IntegerField, BlobField, \
    ForeignKeyField, ManyToManyField, fn, JOIN
from flask_bcrypt import generate_password_hash, check_password_hash
from peewee import Model, MySQLDatabase

db_user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
db_password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"


class ReconectMySQLDatabase(ReconnectMixin, MySQLDatabase, ABC):
    pass


db = ReconectMySQLDatabase(database=database, user=db_user, password=db_password,
                           host=host)


class NOTIFICATION_TYPE(Enum):
    FOLLOWED_USER = 1
    FOLLOW_REQUEST = 2
    FOLLOW_CREATED_RECIPE = 3


NOTIFICATION_TYPE_SET = NOTIFICATION_TYPE._value2member_map_


class RECIPES_BACKGROUND_TYPE(Enum):
    LIKED = "L"
    SAVED = "S"


RECIPES_BACKGROUND_TYPE_SET = RECIPES_BACKGROUND_TYPE._value2member_map_


class FOLLOWED_STATE_SET(Enum):
    FOLLOWED = "F"
    NOT_FOLLOWED = "NF"
    PENDING_FOLLOWED = "PF"


USER_TYPE_SET = FOLLOWED_STATE_SET._value2member_map_


class UNITS_TYPE(Enum):
    GRAMS = "g"
    UNITS = "U"
    DENTES = "D"
    FOLHA = "F"
    MILILITROS = "ml"
    QB = "QB"


USER_TYPE_SET = UNITS_TYPE._value2member_map_


class USER_TYPE(Enum):
    NORMAL = "N"
    COMPANY = "C"
    VIP = "V"
    ADMIN = "A"


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


class EmptyModel(Model):
    class Meta:
        database = db


class BaseModel(EmptyModel):
    created_date = DateTimeField(default=datetime.now, null=False)


class UpdatableBaseModel(BaseModel):
    updated_date = DateTimeField(default=datetime.now, null=False)


''' User '''


class User(UpdatableBaseModel):
    # __tablename__ = "user"
    name = CharField(null=False)
    username = CharField(null=False, unique=True)
    birth_date = DateTimeField(null=False)
    email = CharField(unique=True, null=False)
    password = CharField(null=False)

    fmc_token = CharField(default="")

    description = CharField(default="")  # max length 255

    user_portion = IntegerField(default=-1)

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

    def hash_password(self, password):
        return generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class FollowRequest(BaseModel):
    follower = ForeignKeyField(User, backref='followers_request')
    followed = ForeignKeyField(User, backref='followeds_request')

    class Meta:
        db_table = 'follow_request'


class Follow(BaseModel):
    follower = ForeignKeyField(User, backref='followeds')
    followed = ForeignKeyField(User, backref='followers')


''' Recipe '''


class NutritionInformation(EmptyModel):
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


class Recipe(UpdatableBaseModel):
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

    source_rating = FloatField(null=True)
    source_link = CharField(null=True)

    def get_average_rating(self):
        avg_rating = RecipeRating.select(fn.AVG(RecipeRating.rating)).where(RecipeRating.recipe == self).scalar()
        return avg_rating or 0.0


    def get_likes(self):
        likes = RecipeBackground.select().where(
            (RecipeBackground.recipe == self) & (
                    RecipeBackground.type == RECIPES_BACKGROUND_TYPE.LIKED.value)).count()

        return likes or 0


class RecipeRating(BaseModel):
    recipe = ForeignKeyField(Recipe, backref="ratings", on_delete="CASCADE")
    user = ForeignKeyField(User, backref="rated_recipes", on_delete="CASCADE")
    rating = IntegerField(null=True)

    class Meta:
        db_table = 'recipe_ratings'


class RecipeBackground(BaseModel):
    user = ForeignKeyField(User, backref="recipes")
    recipe = ForeignKeyField(Recipe, backref="backgrounds", on_delete="CASCADE")
    type = CharField(null=False)  # (liked, saved)

    class Meta:
        db_table = 'recipe_background'


class Tag(BaseModel):
    title = CharField(null=False, unique=True)
    recipes = ManyToManyField(Recipe, backref='tags', on_delete="CASCADE")


RecipeTagThrough = Recipe.tags.get_through_model()


class Ingredient(EmptyModel):
    name = CharField(null=False, unique=True)


class RecipeIngredientQuantity(EmptyModel):
    ingredient = ForeignKeyField(Ingredient, backref="ingredient_base")
    recipe = ForeignKeyField(Recipe, backref="ingredients", on_delete="CASCADE", null=False)
    quantity_original = CharField(null=False)
    quantity_normalized = FloatField(null=True)
    units_normalized = CharField(default="G")
    extra_quantity = FloatField(null=True)
    extra_units = CharField(null=True)

    class Meta:
        db_table = 'recipe_ingredient_quantity'


class Comment(UpdatableBaseModel):
    text = CharField(null=False)
    recipe = ForeignKeyField(Recipe, backref='comments', on_delete="CASCADE")
    user = ForeignKeyField(User, backref='comments')


class RecipeReport(BaseModel):
    title = CharField(null=False)
    message = CharField(null=False)
    recipe = ForeignKeyField(Recipe, backref='reports', on_delete="CASCADE")
    user = ForeignKeyField(User, backref='recipe_reports')

    class Meta:
        db_table = 'recipe_report'


""" Calendar """


class CalendarEntry(BaseModel):
    recipe = ForeignKeyField(Recipe, backref='recipe', on_delete="CASCADE")
    user = ForeignKeyField(User, backref='user', on_delete="CASCADE")
    tag = CharField(null=False)  # Pequeno almoço, Lanche da manhã, Almoço, Lanche da tarde ,Jantar , Ceia
    realization_date = DateTimeField(null=False)
    checked_done = BooleanField(default=False)

    class Meta:
        db_table = 'calendar_entrys'


""" Shopping List """


class ShoppingList(UpdatableBaseModel):
    name = CharField(null=False)
    user = ForeignKeyField(User, backref='user', on_delete="CASCADE")
    archived = BooleanField(default=False)

    class Meta:
        db_table = "shopping_list"


class ShoppingIngredient(BaseModel):
    ingredient = ForeignKeyField(Ingredient, backref='ingredient')
    shopping_list = ForeignKeyField(ShoppingList, backref='shopping_ingredients', on_delete="CASCADE")
    checked = BooleanField(default=False)
    quantity = FloatField(null=False)
    extra_quantity = FloatField(null=True, default=None)
    units = CharField(default="G")
    extra_units = CharField(null=True, default=None)

    class Meta:
        db_table = "shopping_ingredient"


''' Miscellanius '''


class Notification(BaseModel):
    title = CharField(null=False)
    message = CharField(null=False)
    user = ForeignKeyField(User, backref='notifications')
    seen = BooleanField(default=False)
    type = IntegerField(default=-1)


class ApplicationReport(UpdatableBaseModel):
    title = CharField(null=False)
    message = CharField(null=False)
    user = ForeignKeyField(User, backref='aplication_reports')
    archived = BooleanField(default=False)

    class Meta:
        db_table = "application_report"


class TokenBlocklist(BaseModel):
    jti = CharField()

    class Meta:
        db_table = 'token_block_list'
