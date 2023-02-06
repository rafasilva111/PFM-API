from peewee import *

DATABASE_NAME = 'example'
HOST = 'localhost'
PORT = 3306
USER = "root"
# pf = open(password_file, 'r')
PASSWORD = ''  # in prod pf.read()
# pf.close()

db = MySQLDatabase(DATABASE_NAME, host=HOST, port=PORT, user=USER, password=PASSWORD)

class BaseModel(Model):
    class Meta:
        database = db

class Tags(BaseModel):
    name = CharField()

class Recipe(BaseModel):
    name = CharField()
    tags = ManyToManyField(Tags, backref='recipes')

def main():
    StudentCourse = Recipe.tags.get_through_model()
    db.create_tables([
        Tags,
        Recipe,
        StudentCourse])

    Tags.create(name='Huey')
    Tags.create(name='Charlie')
    Tags.create(name='Zaizee')
    Tags.create(name='Mickey')
    Recipe.create(name='English 101')
    Recipe.create(name='English 101')
    Recipe.create(name='Spanish 101')




    # Get all classes that "huey" is enrolled in:
    huey = Tags.get(Tags.name == 'Huey')
    for course in huey.recipes.order_by(Recipe.name):
        print(course.name)

    # Get all students in "English 101":
    engl_101 = Recipe.get(Recipe.name == 'English 101')
    for student in engl_101.tags:
        print(student.name)

    # When adding objects to a many-to-many relationship, we can pass
    # in either a single model instance, a list of models, or even a
    # query of models:
    huey.recipes.add(Recipe.select().where(Recipe.name.contains('English')))
    engl_101.students.add(Tags.get(Tags.name == 'Mickey'))




