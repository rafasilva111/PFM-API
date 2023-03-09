import math
from datetime import datetime
from playhouse.flask_utils import object_list
from peewee import *
from passlib.apps import custom_app_context as pwd_context
from backend.dtos import RecipeDTO
from backend.teste import main
from flask_bcrypt import check_password_hash, generate_password_hash

DATABASE_NAME = 'example'
HOST = '127.0.0.1'
PORT = 3306
USER = "root"
# pf = open(password_file, 'r')
PASSWORD = ''  # in prod pf.read()
# pf.close()

db = MySQLDatabase(DATABASE_NAME, host=HOST, port=PORT, user=USER, password=PASSWORD)


class DBManager:

    def __init__(self):
        db.connect()
        self.populate_db()

    def populate_db(self):

        db.create_tables(
            [User, Recipe, RecipesBackground, Comments, Goals, GoalTypeAll, GoalTypeDefault, GoalsTypeMapper, Scheduale,
             Followers, Tags, Preparation, Nutrition_Information, TokenBlocklist,RecipeTag
             ])

        return

    def query_titles(self):
        return

    # RECIPE
    def get_recipes(self, page=0, page_size=20):

        recipes = []
        for item in Recipe.select().paginate(page, page_size):
            recipes.append(RecipeDTO(item.title).__dict__)
        return recipes

    def post_recipes(self):
        try:
            Recipe.create(title="")
        except Exception as err:
            print(err)

        return 1


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    first_name = TextField(null=False)
    last_name = TextField(null=False)
    birth_date = DateTimeField(null=False)
    email = TextField(null=False)
    password = TextField(null=False)

    profile_type = CharField(default="PRIVATE")  # (protect, private, public)
    verified = BooleanField(default=False)
    user_type = CharField(default="NORMAL")  # (normal, vip, admin)
    img_source = CharField(null=True)

    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())

    activity_level = FloatField(null=True)
    height = FloatField(null=True)
    sex = CharField(null=True)
    weight = FloatField(null=True)
    age = CharField(null=False)

    def hash_password(self, password):
        return generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Tags(BaseModel):
    title = CharField(null=False)
    verified = BooleanField(null=False, default=0)
    cor = CharField(null=True)


class GoalTypeAll(BaseModel):
    title = CharField()
    objectivo_cumprido = FloatField(default=0.0)
    objectivo_expectavel = FloatField(default=0.0)
    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())


class GoalTypeDefault(BaseModel):
    objectivo_cumprido = FloatField(default=0.0)
    objectivo_expectavel = FloatField(default=0.0)
    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())


class GoalsTypeMapper(BaseModel):
    type = CharField()
    type_goal = ForeignKeyField(GoalTypeAll)
    type_goal_default = ForeignKeyField(GoalTypeDefault)


class Goals(BaseModel):
    state = CharField(default="STARTED")
    goals_type = ForeignKeyField(GoalsTypeMapper)


class Followers(BaseModel):
    user_sender = ForeignKeyField(User)
    user_reciever = ForeignKeyField(User)
    state = CharField(default="PENDING")


class Recipe(BaseModel):
    title = CharField(null=False)
    description = CharField(null=False)
    created_date = DateTimeField(default=datetime.now(), null=False)
    updated_date = DateTimeField(default=datetime.now(), null=False)
    img_source = CharField(null=True)

    difficulty = CharField(null=True)
    portion = CharField(null=True)
    time = CharField(null=True)

    likes = IntegerField(default=0, null=False)
    views = IntegerField(default=0, null=False)
    ingredients = CharField(null=False)

    source_rating = FloatField(null=True)
    source_link = CharField(null=True)
    company = CharField(null=True)


class Scheduale(BaseModel):
    id_user = ForeignKeyField(User)
    id_recipe = ManyToManyField(Recipe)
    id_goals = ForeignKeyField(Goals)
    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())


class RecipesBackground(BaseModel):
    user = ForeignKeyField(User)
    recipe = ForeignKeyField(Recipe)
    type = CharField()  # (liked, saved, created, commented)


class Comments(BaseModel):
    user = ForeignKeyField(User)
    recipe = ForeignKeyField(Recipe)
    description = CharField()
    created_date = DateTimeField(default=datetime.now())
    updated_date = DateTimeField(default=datetime.now())


class Preparation(BaseModel):
    step_number = IntegerField()
    description = CharField()
    recipe = ForeignKeyField(Recipe, backref='preparations')


class RecipeTag(BaseModel):
    recipe = ForeignKeyField(Recipe, backref='recipeTag_recipe')
    tag = ForeignKeyField(Tags, backref='recipeTag_tag')


class Nutrition_Information(BaseModel):
    energia = CharField()
    energia_perc = CharField()
    gordura = CharField()
    gordura_perc = CharField()
    gordura_saturada = CharField()
    gordura_saturada_perc = CharField()
    hidratos_carbonos = CharField()
    hidratos_carbonos_acucares = CharField()
    hidratos_carbonos_acucares_perc = CharField()
    fibra = CharField()
    fibra_perc = CharField()
    proteina = CharField()
    recipe = ForeignKeyField(Recipe, backref='nutrition_informations')


class TokenBlocklist(BaseModel):
    jti = CharField()
    energia_perc = DateTimeField()


# ////////////////////////////old////////////////////////////////////
