from flask_restx import Namespace, Resource, fields, abort
from flask_app.ext.database import db
from .errors import return_error_sql, school_no_exists

# Create name space
api = Namespace("Schools", description="Here are all School endpoints")

BASE_RECIPE_PREFIX = "/recipe"

# School API Model
school_api_full_model = api.model("School model", {
    "id": fields.Integer(requred=False, description="The ID of school"),
    "name": fields.String(required=True, description="The first name of school", min_length=3, max_length=20),
    "address": fields.String(required=True, description="The last name of school", min_length=3, max_length=20),
    "email": fields.String(required=True, description="The email of school", min_length=10, max_length=30),
    "phone": fields.Integer(required=True, description="The age of school", min=1, max=100, allow_null=False),
    "students": fields.List(
        fields.String(required=True, description="Students attending this school", allow_null=False))
})

school_api_model = api.model("School model", {
    "name": fields.String(required=True, description="The first name of school", min_length=3, max_length=20),
    "address": fields.String(required=True, description="The last name of school", min_length=3, max_length=20),
    "email": fields.String(required=True, description="The email of school", min_length=10, max_length=30),
    "phone": fields.Integer(required=True, description="The age of school", min=1, max=100, allow_null=False),
    "students": fields.List(
        fields.String(required=True, description="Students attending this school", allow_null=False))
})


# Create resources
@api.route("/")
@api.doc("get_school", model=school_api_full_model)
class RecipeListResource(Resource):

    def get(self):
        """List all schools"""
        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        ##Pesquisa por String

        if args['string']:

            # parse arguments

            string_to_search = args['string']

            # get recipes

            query = RecipeDB.select(RecipeDB).distinct().join(RecipeTagDB).join(TagsDB) \
                .where(TagsDB.title.contains(string_to_search) | RecipeDB.title.contains(string_to_search))

            recipes = []
            for item in query.paginate(page, page_size):
                recipes.append(RecipeDTO(id=item.id, title=item.title, description=item.description,
                                         created_date=item.created_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         updated_date=item.updated_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         img_source=item.img_source,
                                         difficulty=item.difficulty, portion=item.portion, time=item.time,
                                         likes=item.likes,
                                         source_rating=item.source_rating, source_link=item.source_link,
                                         views=item.views, tags=item.recipeTag_recipe, ingredients=item.ingredients,
                                         preparations=item.preparations,
                                         nutrition_informations=item.nutrition_informations
                                         ).__dict__)

            # Metadata

            response_holder = self.response_placeholder
            response_holder["recipe_result"] = recipes

            total_recipes = int(query.count())
            total_pages = math.ceil(total_recipes / page_size)
            if total_pages != 1:
                response_holder['_metadata']['Links'] = []

                if page < total_pages:
                    next_link = page + 1
                    response_holder['_metadata']['Links'].append(
                        {"next": f"/{RECIPE_ENDPOINT}?page={next_link}&page_size={page_size}"},
                    )
                if page > 1:
                    previous_link = page - 1
                    response_holder['_metadata']['Links'].append(
                        {"previous": f"/{RECIPE_ENDPOINT}?page={previous_link}&page_size={page_size}"})
            else:
                try:
                    response_holder['_metadata'].pop('Links')
                except Exception as a:
                    # log
                    pass
            response_holder['_metadata']['page'] = page
            response_holder['_metadata']['per_page'] = page_size
            response_holder['_metadata']['page_count'] = total_pages
            response_holder['_metadata']['recipes_total'] = total_recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
        else:

            # metadata

            response_holder = self.response_placeholder
            total_recipes = int(RecipeDB.select().count())
            total_pages = math.ceil(total_recipes / page_size)
            if total_pages != 1:
                response_holder['_metadata']['Links'] = []

                if page < total_pages:
                    next_link = page + 1
                    response_holder['_metadata']['Links'].append(
                        {"next": f"/{RECIPE_ENDPOINT}?page={next_link}&page_size={page_size}"},
                    )
                if page > 1:
                    previous_link = page - 1
                    response_holder['_metadata']['Links'].append(
                        {"previous": f"/{RECIPE_ENDPOINT}?page={previous_link}&page_size={page_size}"})
            else:
                response_holder['_metadata'].pop('Links')
            response_holder['_metadata']['page'] = page
            response_holder['_metadata']['per_page'] = page_size
            response_holder['_metadata']['page_count'] = total_pages
            response_holder['_metadata']['recipes_total'] = total_recipes

            recipes = []
            for item in RecipeDB.select().paginate(page, page_size):
                recipes.append(RecipeDTO(id=item.id, title=item.title, description=item.description,
                                         created_date=item.created_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         updated_date=item.updated_date.strftime("%d/%m/%Y, %H:%M:%S"),
                                         img_source=item.img_source,
                                         difficulty=item.difficulty, portion=item.portion, time=item.time,
                                         likes=item.likes,
                                         source_rating=item.source_rating, source_link=item.source_link,
                                         views=item.views, tags=item.recipeTag_recipe, ingredients=item.ingredients,
                                         preparations=item.preparations,
                                         nutrition_informations=item.nutrition_informations
                                         ).__dict__)

            response_holder["recipe_result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    @api.expect(school_api_full_model)
    def post(self):
        """Add new school"""
        try:
            api.payload["students"] = list(map(int, api.payload["students"]))
            students = Student.query.filter(Student.id.in_(set(api.payload["students"]))).all()
            api.payload["students"] = students
            new_school = School(**api.payload)
            db.session.add(new_school)
            db.session.commit()
            schema = SchoolSchema(many=True)
            return {"message": "School was successfully added", "content": [schema.dump(api.payload)]}, 200
        except Exception as e:
            return return_error_sql(e)

# @api.route("/<int:id>")
# @api.param('id', 'the ID of the school you want to obtain')
# class SchoolResource(Resource):
#
#     def get(self, id):
#         """ Get a school with ID """
#         school = School.query.get(id)
#         if school is not None:
#             schema = SchoolSchema()
#             return schema.dump(school)
#         return school_no_exists(id)
#
#     def delete(self, id):
#         """Delete a school by ID"""
#         try:
#             school = School.query.get(id)
#             if school is not None:
#                 db.session.delete(school)
#                 db.session.commit()
#                 schema = SchoolSchema()
#                 return {"message": "School was successfully added", "content": [schema.jsonify(school)]}
#             return school_no_exists(id)
#         except Exception as e:
#             return return_error_sql(e)
#
#     @api.expect(school_api_model)
#     def put(self, id):
#         """Put a school by ID"""
#         try:
#             if len(dict(**api.payload)) == len(school_api_model.keys()):
#                 school = School.query.filter_by(id=id).update(dict(**api.payload))
#                 if school:
#                     db.session.commit()
#                     return {"message": "Updated successfully"}
#                 return school_no_exists(id)
#             else:
#                 intersection = set(school_api_model.keys()).difference(set(api.payload.keys()))
#                 return {
#                            "message": f"You are missing the following fields to be able to perform the PUT method: {intersection}"}, 400
#         except Exception as e:
#             return return_error_sql(e)
#
#     @api.expect(school_api_model)
#     def patch(self, id):
#         """Patch a school by ID"""
#         try:
#             if api.payload:
#                 school = School.query.filter_by(id=id).update(dict(**api.payload))
#                 if school:
#                     db.session.commit()
#                     return {"message": "Updated successfully"}
#                 return school_no_exists(id)
#             return {
#                        "message": f"You must have at least one of all of the following fields: {set(school_api_model.keys())}"}, 400
#         except Exception as e:
#             return return_error_sql(e)
