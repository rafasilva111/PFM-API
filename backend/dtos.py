import json


class TagDTO:
    id = None
    title = None

    def __init__(self, id, title):
        self.id = id
        self.title = title


class IngredientsDTO:
    id = None
    name = None
    quantity = None

    def __init__(self, id="", name="", quantity=""):
        self.id = id
        self.name = name
        self.quantity = quantity


class RecipeDTO():
    id = None
    title = None
    company = None
    description = None
    created_date = None
    updated_date = None
    img_source = None

    difficulty = None
    portion = None
    time = None

    likes = None
    source_rating = None
    views = None

    tags = []
    ingredients = []
    nutrition_information = {}
    preparation = []

    def __init__(self, id="", title="", company="", description="", created_date="", updated_date="", img_source=""
                 , difficulty="", portion="", time="", likes="", source_rating="", views="", tags=[], ingredients=[],
                 nutrition_informations=[], preparations=[]):
        self.id = id
        self.title = title
        self.company = company
        self.description = description
        self.created_date = created_date
        self.updated_date = updated_date
        self.img_source = img_source
        self.difficulty = difficulty
        self.portion = portion
        self.time = time
        self.likes = likes
        self.source_rating = source_rating
        self.views = views

        for tag in tags:
            self.tags.append(TagDTO(id=tag.id, title=tag.title).__dict__)
        self.tags = json.dumps(self.tags)

        for ingredient in ingredients:
            self.ingredients.append(
                {"id":ingredient.id, "name":ingredient.name, "quantity":ingredient.quantity})
        self.ingredients = json.dumps(self.ingredients)

        for preparation in preparations:
            self.preparation.append(
                {preparation.step_number: {"id": preparation.id, "description": preparation.description}})
        self.preparation = json.dumps(self.preparation)

        for nt in nutrition_informations:
            self.nutrition_information ={"energia": nt.energia, "energia_perc": nt.energia_perc, "gordura": nt.gordura,
                         "gordura_perc": nt.gordura_perc, "gordura_saturada": nt.gordura_saturada,
                         "gordura_saturada_perc": nt.gordura_saturada_perc, "hidratos_carbonos": nt.hidratos_carbonos,
                         "hidratos_carbonos_acucares": nt.hidratos_carbonos_acucares,
                         "hidratos_carbonos_acucares_perc": nt.hidratos_carbonos_acucares_perc, "fibra": nt.fibra,
                         "fibra_perc": nt.fibra_perc, "proteina": nt.proteina}


class UserDTO():
    first_name = None
    last_name =None
    birth_date =None
    email =None

    profile_type = None  # (protect, private, public)
    verified = None
    user_type = None  # (normal, vip, admin)
    img_source = None

    created_date = None
    updated_date = None

    nivel_de_atividade = None
    altura = None
    sexo = None
    peso = None

    

