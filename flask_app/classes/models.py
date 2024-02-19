import os
from abc import ABC
from datetime import datetime

from flask_bcrypt import generate_password_hash, check_password_hash
from peewee import FloatField, CharField, DateTimeField, BooleanField, IntegerField, BlobField, \
    ForeignKeyField, ManyToManyField
from peewee import Model, MySQLDatabase
from playhouse.shortcuts import ReconnectMixin

db_user = os.environ.get('MYSQL_ROOT') if os.environ.get('MYSQL_ROOT') else "root"
db_password = os.environ.get('MYSQL_ROOT_PASSWORD') if os.environ.get('MYSQL_ROOT_PASSWORD') else ""
database = os.environ.get('MYSQL_DATABASE') if os.environ.get('MYSQL_DATABASE') else "flask_api"
host = os.environ.get('MYSQL_HOST') if os.environ.get('MYSQL_HOST') else "localhost"


class ReconectMySQLDatabase(ReconnectMixin, MySQLDatabase, ABC):
    pass


db = ReconectMySQLDatabase(database=database, user=db_user, password=db_password,
                           host=host)



class BaseModel(Model):
    class Meta:
        database = db


''' User '''


class User(BaseModel):
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

    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())

    def hash_password(self, password):
        return generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class FollowRequest(BaseModel):
    follower = ForeignKeyField(User, backref='followers_request')
    followed = ForeignKeyField(User, backref='followeds_request')
    created_date = DateTimeField(default=datetime.now())

    class Meta:
        db_table = 'follow_request'


class Follow(BaseModel):
    follower = ForeignKeyField(User, backref='followeds')
    followed = ForeignKeyField(User, backref='followers')


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
    recipe = ForeignKeyField(Recipe, backref="backgrounds", on_delete="CASCADE")
    type = CharField(null=False)  # (liked, saved)

    class Meta:
        db_table = 'recipe_background'


class Tag(BaseModel):
    title = CharField(null=False, unique=True)
    recipes = ManyToManyField(Recipe, backref='tags', on_delete="CASCADE")


RecipeTagThrough = Recipe.tags.get_through_model()


class Ingredient(BaseModel):
    name = CharField(null=False, unique=True)


class RecipeIngredientQuantity(BaseModel):
    ingredient = ForeignKeyField(Ingredient, backref="ingredient_base")
    recipe = ForeignKeyField(Recipe, backref="ingredients", on_delete="CASCADE", null=False)
    quantity_original = CharField(null=False)
    quantity_normalized = FloatField(null=True)
    units_normalized = CharField(default="G")
    extra_quantity = FloatField(null=True)
    extra_units = CharField(null=True)

    class Meta:
        db_table = 'recipe_ingredient_quantity'


class Comment(BaseModel):
    text = CharField(null=False)
    recipe = ForeignKeyField(Recipe, backref='comments', on_delete="CASCADE")
    user = ForeignKeyField(User, backref='comments')
    created_date = DateTimeField(default=datetime.now, null=False)
    updated_date = DateTimeField(default=datetime.now, null=False)


class RecipeReport(BaseModel):
    title = CharField(null=False)
    message = CharField(null=False)
    recipe = ForeignKeyField(Recipe, backref='reports', on_delete="CASCADE")
    user = ForeignKeyField(User, backref='recipe_reports')
    created_date = DateTimeField(default=datetime.now, null=False)

    class Meta:
        db_table = 'recipe_report'


""" Calendar """


class CalendarEntry(BaseModel):
    recipe = ForeignKeyField(Recipe, backref='recipe', on_delete="CASCADE")
    user = ForeignKeyField(User, backref='user', on_delete="CASCADE")
    tag = CharField(null=False)  # Pequeno almoço, Lanche da manhã, Almoço, Lanche da tarde ,Jantar , Ceia
    created_date = DateTimeField(default=datetime.now, null=False)
    realization_date = DateTimeField(null=False)
    checked_done = BooleanField(default=False)

    class Meta:
        db_table = 'calendar_entrys'


""" Shopping List """


class ShoppingList(BaseModel):
    name = CharField(null=False)
    user = ForeignKeyField(User, backref='user', on_delete="CASCADE")
    updated_date = DateTimeField(default=datetime.now, null=False)
    created_date = DateTimeField(default=datetime.now, null=False)
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
    created_date = DateTimeField(default=datetime.now, null=False)
    seen = BooleanField(default=False)
    type = IntegerField(default=-1)


class ApplicationReport(BaseModel):
    title = CharField(null=False)
    message = CharField(null=False)
    user = ForeignKeyField(User, backref='aplication_reports')
    archived = BooleanField(default=False)
    created_date = DateTimeField(default=datetime.now, null=False)

    class Meta:
        db_table = "application_report"


class TokenBlocklist(BaseModel):
    jti = CharField()
    created_date = DateTimeField(default=datetime.now())

    class Meta:
        db_table = 'token_block_list'
