import json
import math
from datetime import datetime, timezone, timedelta

import peewee
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource, fields, reqparse
from flask import Response, request
from playhouse.shortcuts import model_to_dict
from marshmallow import ValidationError

from flask_app.ext.database import db
from .errors import return_error_sql, student_no_exists
from ...models import TokenBlocklist
from ...models.model_metadata import build_metadata

from ...models.model_user import User as UserDB, UserSchema
from ...models.model_recipe import Recipe as RecipeDB, RecipeSchema
from ...models.model_comment import Comment as CommentDB, CommentSchema

# Create name space
api = Namespace("Comments", description="Here are all comment endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The id to be search.')
parser.add_argument('recipe_id', type=int, help='The recipe id to be search.')
parser.add_argument('user_id', type=int, help='The user id to be search.')

ENDPOINT = "/comment"


# Create resources
@api.route("/list")
class CommentsListResource(Resource):

    def get(self):
        """List all comments"""
        # Get args

        args = parser.parse_args()

        recipe_id = args['recipe_id']
        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        ## Pesquisa comments from a recipe id

        if recipe_id:

            # declare response holder

            response_holder = {}

            # build query

            query = CommentDB.select().where(CommentDB.recipe == recipe_id)

            # metadata

            total_comments = int(query.count())
            total_pages = math.ceil(total_comments / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_comments, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            comments = []
            for item in query.paginate(page, page_size):
                recipe = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                comments.append(CommentSchema().dump(recipe))

            response_holder["result"] = comments

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
        else:

            # declare response holder

            response_holder = {}

            # metadata

            total_comments = int(CommentDB.select().count())
            total_pages = math.ceil(total_comments / page_size)
            metadata = build_metadata(page, page_size, total_pages, total_comments, ENDPOINT)
            response_holder["_metadata"] = metadata

            # response data

            comments = []
            for item in CommentDB.select().paginate(page, page_size):
                comment = model_to_dict(item, backrefs=True, recurse=True, manytomany=True)
                comments.append(CommentSchema().dump(comment))

            response_holder["result"] = comments

            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

@api.route("")
class CommentResource(Resource):

    @jwt_required()
    def get(self):
        """ Get a comment with ID """
        # Get args

        args = parser.parse_args()

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Invalid arguments...")

        # Get and Serialize db model

        try:
            comment_record = CommentDB.get(id=args["id"])
            comment_model = model_to_dict(comment_record, backrefs=True, recurse=True, manytomany=True)
            comment_schema = CommentSchema().dump(comment_model)
        except peewee.DoesNotExist:
            return Response(status=400, response="Recipe does not exist...")

        return Response(status=200, response=json.dumps(comment_schema), mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post a comment by user """

        # Parse json body

        json_data = request.get_json()

        # Get args

        args = parser.parse_args()

        recipe_id = args['recipe_id']

        # Validate args

        if not args["recipe_id"]:
            return Response(status=400, response="Missing arguments...")

        # gets user auth id

        user_id = get_jwt_identity()

        # Validate args by loading it into schema

        try:
            comment_validated = CommentSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        # Verify existence of the requested ids model's

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="Client couldn't be found.")

        try:
            recipe = RecipeDB.get(recipe_id)
        except peewee.DoesNotExist:
            # this only occurs when accounts are not in db
            return Response(status=400, response="Recipe couldn't be found.")

        # fills comment object

        comment = CommentDB(**comment_validated)
        comment.recipe = recipe
        comment.user = user
        comment.save()

        return Response(status=201)

    @jwt_required()
    def patch(self):
        """Patch a comment by ID"""

        # Parse json body

        json_data = request.get_json()

        # Get args

        args = parser.parse_args()

        id = args['id']
        user_id = args['user_id']

        # Validate args

        if not args["id"]:
            return Response(status=400, response="Missing id argument...")

        # if not args["user_id"]:
        #     return Response(status=400, response="Missing user_id argument...")

        # Validate args by loading it into schema

        try:
            comment_validated = CommentSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        # Verify existence of the requested ids model's

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="Client couldn't be found.")

        try:
            comment = CommentDB.get(id=id)
        except peewee.DoesNotExist:
            # this only occurs when accounts are not in db
            return Response(status=400, response="Comment couldn't be found.")

        # fills comment object

        try:
            # check if comment was created in less than 12 hours
            if comment.created_date > datetime.now() - timedelta(hours=12):
                comment.text = comment_validated["text"]
                comment.updated_date = datetime.now()
                comment.save()
                return Response(status=202)
            else:
                return Response(status=400, response="Comment can't be updated after 12 hours.")
        except peewee.DoesNotExist:
            return Response(status=400, response="Comment couldn't be updated.")

    @jwt_required()
    def delete(self):
        """Delete a comment by ID"""

        # gets user auth id
        user_auth_id = get_jwt_identity()
        try:
            user = UserDB.get(user_auth_id)
        except peewee.DoesNotExist:
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            return Response(status=400, response="No user found by this id.")

        # Get args
        args = parser.parse_args()

        id = args['id']
        user_id = args['user_id']

        # Validate args
        if not args["id"]:
            return Response(status=400, response="Missing id argument...")

        if not args["user_id"]:
            return Response(status=400, response="Missing user_id argument...")

        # get comment by id
        try:
            comment = CommentDB.get(id=id, user_id=user_id)
        except peewee.DoesNotExist:
            return Response(status=400, response="No comment found by this id.")

        # checks if user is admin or the one who created the comment and deletes the comment

        if user.user_type == "A" or user.id == comment.user.id:
            try:
                comment.delete_instance()
                return Response(status=200, response="Comment deleted successfully.")
            except peewee.DoesNotExist:
                return Response(status=400, response="No comment found by this id.")
        else:
            return Response(status=400, response="You are not authorized to delete this comment.")

