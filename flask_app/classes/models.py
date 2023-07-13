import os
from abc import ABC
from datetime import datetime
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

    profile_type = CharField(default="PRIVATE")  # (protect, private, public)
    verified = BooleanField(default=False)
    user_type = CharField(default="N")  # (normal, company, vip, admin)
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
    hidratos_carbonos_perc = CharField()
    hidratos_carbonos_acucares = CharField()
    hidratos_carbonos_acucares_perc = CharField()
    fibra = CharField()
    fibra_perc = CharField()
    proteina = CharField()
    proteina_perc = CharField()

    class Meta:
        db_table = 'nutrition_information'


class Recipe(BaseModel):
    title = CharField(null=False)
    description = CharField(null=False)
    img_source = CharField(null=True)

    difficulty = CharField(null=True)
    portion = CharField(null=True)
    time = CharField(null=True)

    views = IntegerField(default=0, null=False)
    preparation = BlobField(null=False)

    created_by = ForeignKeyField(User, backref="created_by")
    nutrional_table = ForeignKeyField(NutritionInformation, backref='recipe')

    source_rating = FloatField(null=True)
    source_link = CharField(null=True)
    company = CharField(null=True)

    created_date = DateTimeField(default=datetime.now(), null=False)
    updated_date = DateTimeField(default=datetime.now(), null=False)


class RecipeBackground(BaseModel):
    user = ForeignKeyField(User, backref="recipes")
    recipe = ForeignKeyField(Recipe, backref="backgrounds")
    type = CharField(null=False)  # (liked, saved, created)

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

    class Meta:
        db_table = 'recipe_ingredient_quantity'


class Comment(BaseModel):
    text = CharField(null=False)
    recipe = ForeignKeyField(Recipe, backref='comments')
    user = ForeignKeyField(User, backref='comments')
    created_date = DateTimeField(default=datetime.now, null=False)
    updated_date = DateTimeField(default=datetime.now, null=False)


''' Miscellanius '''


class TokenBlocklist(BaseModel):
    jti = CharField()
    created_at = DateTimeField(default=datetime.now())

    class Meta:
        db_table = 'token_block_list'
