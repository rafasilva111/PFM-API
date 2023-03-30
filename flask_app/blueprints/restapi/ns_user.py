import json
import math

from flask_restx import Namespace, Resource, fields, reqparse
from flask import Response, request
from playhouse.shortcuts import model_to_dict

from flask_app.ext.database import db
from .errors import return_error_sql, student_no_exists
from ...models.model_metadata import build_metadata

from ...models.model_user import User as UserDB, UserSchema

# Create name space
api = Namespace("Users", description="Here are all user endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=str, help='The string to be search.')
parser.add_argument('string', type=str, help='The string to be search.')

ENDPOINT = "/user"


# Create resources
@api.route("/list")
class UserListResource(Resource):

    def get(self):
        """List all users"""
        # Get args

        args = parser.parse_args()

        string_to_search = args['string']
        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        ## Pesquisa por String

        if string_to_search:

            # declare response holder

            response_holder = {}

            # build query

            query = UserDB.select().where(UserDB.first_name.contains(string_to_search) |
                                          UserDB.last_name.contains(string_to_search) |
                                          UserDB.email.contains(string_to_search))

            # metadata

            total_users = int(query.count())
            total_pages = math.ceil(total_users / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_users, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for item in query.paginate(page, page_size):
                recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                recipes.append(UserSchema().dump(recipe))

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
        else:

            # declare response holder

            response_holder = {}

            # metadata

            total_users = int(UserDB.select().count())
            total_pages = math.ceil(total_users / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_users, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            recipes = []
            for item in UserDB.select().paginate(page, page_size):
                recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                recipes.append(UserSchema().dump(recipe))

            response_holder["result"] = recipes

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

    def post(self):
        """Add new student"""
        try:
            new_student = Student(**api.payload)
            db.session.add(new_student)
            db.session.commit()
            return {"message": "Student was successfully added", "content": [api.payload]}, 200
        except Exception as e:
            return return_error_sql(e)


@api.route("/<int:id>")
@api.param('id')
@api.doc("Student partial")
class StudentResource(Resource):

    def get(self, id):
        """ Get a student with ID """
        student = Student.query.get(id)
        if student is not None:
            schema = StudentSchema()
            return schema.dump(student), 200
        return student_no_exists(id)

    def delete(self, id):
        """Delete a student by ID"""
        try:
            student = Student.query.get(id)
            if student is not None:
                db.session.delete(student)
                db.session.commit()
                schema = StudentSchema()
                return {"message": "Student was successfully deleted", "content": [schema.dump(student)]}, 200
            return student_no_exists(id)
        except Exception as e:
            return return_error_sql(e)

    def put(self, id):
        """Put a student by ID"""
        try:
            if len(dict(**api.payload)) == len(student_api_model.keys()):
                student = Student.query.filter_by(id=id).update(dict(**api.payload))
                if student:
                    db.session.commit()
                    return {"message": "Updated successfully"}, 200
                return student_no_exists(id)
            else:
                intersection = set(student_api_model.keys()).difference(set(api.payload.keys()))
                return {
                           "message": f"You are missing the following fields to be able to perform the PUT method: {intersection}"}, 400
        except Exception as e:
            return return_error_sql(e)

    def patch(self, id):
        """Patch a student by ID"""
        try:
            if api.payload:
                student = Student.query.filter_by(id=id).update(dict(**api.payload))
                if student:
                    db.session.commit()
                    return {"message": "Updated successfully"}
                return student_no_exists(id)
            return {
                       "message": f"You must have at least one of all of the following fields: {set(student_api_model.keys())}"}, 400
        except Exception as e:
            return return_error_sql(e)
