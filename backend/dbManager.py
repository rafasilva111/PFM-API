import math
from datetime import datetime
from playhouse.flask_utils import object_list
import mysql
from peewee import *
from passlib.apps import custom_app_context as pwd_context
from backend.dtos import RecipeDTO
from backend.teste import main
from flask_bcrypt import check_password_hash,generate_password_hash
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
             Followers, Tags, Preparation, Nutrition_Information, Ingredients,TokenBlocklist
             ])

        RecipeTags = Recipe.tags.get_through_model()
        RecipeIngridients = Recipe.ingredients.get_through_model()

        db.create_tables([RecipeTags, RecipeIngridients])
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

    def hash_password(self,password):
        return generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Tags(Model):
    title = CharField(null=False)
    verified = BooleanField(null=False, default=0)
    cor = CharField(null=True)

    class Meta:
        database = db


class Ingredients(Model):
    name = CharField()
    quantity = CharField(default="")

    class Meta:
        database = db


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
    tags = ManyToManyField(Tags, backref='recipes')
    ingredients = ManyToManyField(Ingredients, backref='recipes')

    source_rating = FloatField(null=True)
    source_link = CharField(null=True)


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


class Preparation(Model):
    step_number = IntegerField()
    description = CharField()
    recipe = ForeignKeyField(Recipe, backref='preparations')

    class Meta:
        database = db


class Nutrition_Information(Model):
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

    class Meta:
        database = db


class TokenBlocklist(Model):
    jti = CharField()
    energia_perc = DateTimeField()

    class Meta:
        database = db

# ////////////////////////////old////////////////////////////////////


class DBManager_OLD:
    cursor = None

    def __init__(self, database='example', host="db", user="root", password_file='/run/secrets/db-password'):
        self.connection = mysql.connector.connect(
            user=user,
            password="",  # pf.read(),
            host="localhost",  # name of the mysql service as set in the docker compose file
            database=database,
            auth_plugin='mysql_native_password'
        )
        # pf.close()
        self.cursor = self.connection.cursor()

    def populate_db(self):
        self.cursor.execute('DROP TABLE IF EXISTS Recipe')
        # recipe
        self.cursor.execute("CREATE TABLE `Recipe` (	`id` INT NOT NULL AUTO_INCREMENT,	`title` VARCHAR(255) NOT "
                            "NULL,	`company` VARCHAR(255),	`description` VARCHAR(255),	`date_create` VARCHAR(255) NOT "
                            "NULL,	`date_update` VARCHAR(255),	`img_source` VARCHAR(255),	`difficulty` VARCHAR(255) "
                            "NOT NULL,	`portion` VARCHAR(255) NOT NULL,	`time` VARCHAR(255),	`app_rating` "
                            "INT,	`source_rating` INT,	`views` INT NOT NULL DEFAULT '0',		PRIMARY KEY ("
                            "`id`));")
        # followers
        self.cursor.execute(
            "CREATE TABLE `Followers` ( `id` INT NOT NULL AUTO_INCREMENT,	`id_user_sender` INT NOT NULL,	`id_user_reciever` INT NOT "
            "NULL,	PRIMARY KEY (`id`));")
        # last recipes seen
        self.cursor.execute(
            "CREATE TABLE `Last_seen_recipes` (	`id` INT NOT NULL AUTO_INCREMENT,`id_user` INT NOT NULL,	`id_recipe` INT NOT NULL,	"
            "`date_create` VARCHAR(255) NOT NULL,	PRIMARY KEY (`id`));")
        # schedule
        self.cursor.execute(
            "CREATE TABLE `Schedule` (	`id` INT NOT NULL AUTO_INCREMENT,`id_user` INT NOT NULL,	`id_recipe` INT NOT NULL,	`date` "
            "VARCHAR(255) NOT NULL,	`id_goals` INT,	PRIMARY KEY (`id`));")
        # comments
        self.cursor.execute(
            "CREATE TABLE `Comments` (	`id` INT NOT NULL AUTO_INCREMENT, `id_user` INT NOT NULL,	`id_recipe` INT NOT NULL,	`date` "
            "VARCHAR(255) NOT NULL,	`id_goals` INT,	PRIMARY KEY (`id`));")
        # recipes
        self.cursor.execute(
            "CREATE TABLE `Comments` (`id` INT NOT NULL AUTO_INCREMENT,	`id_user` INT NOT NULL,	`id_recipe` INT NOT NULL,	`date` "
            "VARCHAR(255) NOT NULL,	`id_goals` INT,	PRIMARY KEY (`id`));")

        self.connection.commit()

    def query_titles(self):
        self.cursor.execute('SELECT title FROM blog')
        rec = []
        for c in self.cursor:
            rec.append(c[0])
        return rec
