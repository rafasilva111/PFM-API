from peewee import CharField, IntegerField, ManyToManyField, ForeignKeyField

from flask_app.ext.schema import ma
from flask_app.models.base_model import BaseModel
from flask_app.models.model_recipe import Recipe


# Database

class NutritionInformation(BaseModel):
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

        db_table = 'nutrition_information'


# Schemas

def get_tag_schema():
    return NutritionInformationSchema


class NutritionInformationSchema(ma.Schema):
    class Meta:
        model = NutritionInformation
        include_fk = True
        fields = ('__all__',)
