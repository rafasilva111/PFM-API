import json
import math
from datetime import datetime, timezone, timedelta

import peewee
from flask import Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource
from marshmallow import ValidationError

from ...classes.functions import parse_date, add_days
from ...classes.models import Recipe as RecipeDB, User as UserDB, \
    CalendarEntry, TokenBlocklist, RecipeIngredientQuantity, Recipe
from ...classes.schemas import build_metadata, \
    CalendarEntrySimpleSchema, \
    ShoppingIngredient, CalendarEntrySchema, ShoppingIngredientSchema, CalenderEntryListUpdateSchema
from ...ext.logger import log

# Create name space
api = Namespace("calendar", description="Here are all comment endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The id to be search.')
parser.add_argument('date', type=str, help='The date.')
parser.add_argument('from_date', type=str, help='The left date delimiter.')
parser.add_argument('to_date', type=str, help='The right date delimiter.')  # 'dd/mm/yyyy'
parser.add_argument('user_id', type=int, help='The user id to be search.')
parser.add_argument('recipe_id', type=int, help='The recipe id to be search.')

ENDPOINT = "/calendar"


# Create resources
@api.route("/list")
class CalendarResource(Resource):

    @jwt_required()
    def get(self):
        """List all calender"""

        log.info("GET /calendar/list")

        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5
        date = parse_date(args['date']) if args['date'] else None
        from_date = parse_date(args['from_date']) if args['from_date'] else None
        to_date = parse_date(args['to_date']) if args['to_date'] else None
        recipe_id = args['recipe_id'] if args['recipe_id'] else None

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")
        if from_date and to_date and from_date > to_date:
            return Response(status=400, response="something wrong whit from_date and to_date")

        # declare response holder

        response_holder = {}

        # query

        query = CalendarEntry.select().where(CalendarEntry.user == get_jwt_identity())

        if date:
            next_day = add_days(date, 1)
            query = query.where(
                (CalendarEntry.realization_date >= date) &
                (CalendarEntry.realization_date <= next_day)
            )
        elif from_date and to_date:

            query = query.where(
                (CalendarEntry.realization_date >= from_date) &
                (CalendarEntry.realization_date <= to_date)
            ).order_by(CalendarEntry.realization_date)

            # Use a defaultdict to group entries by date
            from collections import defaultdict
            date_to_entries = defaultdict(list)

            for item in query:
                date_string = item.realization_date.strftime("%d/%m/%Y")
                date_to_entries[date_string].append(CalendarEntrySchema().dump(item))

            # Create a date range and initialize result dictionary with empty arrays
            date_range = [from_date + timedelta(days=i) for i in range((to_date - from_date).days + 1)]
            response_holder["result"] = {date.strftime("%d/%m/%Y"): [] for date in date_range}

            # Fill the result dictionary with grouped entries
            for date_string, entries in date_to_entries.items():
                response_holder["result"][date_string] = entries

            log.info("Finish GET /calender/list")
            return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")

        # metadata

        total_calender_entrys = int(query.count())
        total_pages = math.ceil(total_calender_entrys / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_calender_entrys, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        calendar_entrys = []
        for item in query.paginate(page, page_size):
            calendar_entry = item
            calendar_entrys.append(CalendarEntrySchema().dump(calendar_entry))

        response_holder["result"] = calendar_entrys

        log.info("Finish GET /calender/list")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


@api.route("")
class CalendarResource(Resource):

    @jwt_required()
    def get(self):
        """ Get a calendar whit ID """

        log.info("GET /calendar")
        # Get args

        args = parser.parse_args()

        # Validate args

        if not args["id"]:
            log.error("Invalid arguments...")
            return Response(status=400, response="Invalid arguments...")

        # Get and Serialize db model

        try:
            comment_record = CalendarEntry.get(id=args["id"])
            comment_schema = CalendarEntrySchema().dump(comment_record)
        except peewee.DoesNotExist:
            log.error("Recipe does not exist...")
            return Response(status=400, response="Recipe does not exist...")

        log.info("Finish GET /calendar")
        return Response(status=200, response=json.dumps(comment_schema), mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post a comment by user """

        log.info("POST /calendar")

        # gets user auth id

        user_id = get_jwt_identity()

        # Parse json body

        json_data = request.get_json()

        # Get args

        args = parser.parse_args()

        recipe_id = args['recipe_id']

        # Validate args

        if not args["recipe_id"]:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # Validate json body by loading it into schema

        try:
            calendar_entry_validated = CalendarEntrySimpleSchema().load(json_data)
        except ValidationError as err:
            log.error("Invalid arguments...")
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
            log.error("Client couldn't be found.")
            return Response(status=400, response="Client couldn't be found.")

        try:
            recipe = RecipeDB.get(recipe_id)
        except peewee.DoesNotExist:
            # this only occurs when accounts are not in db
            log.error("Recipe couldn't be found.")
            return Response(status=400, response="Recipe couldn't be found.")

        # fills recipe object
        calendar_model = CalendarEntry(**calendar_entry_validated)
        calendar_model.user = user
        calendar_model.recipe = recipe
        calendar_model.save()

        log.info("Finish POST /calendar")

        return Response(status=201, response=json.dumps(CalendarEntrySchema().dump(calendar_model)),
                        mimetype="application/json")

    @jwt_required()
    def patch(self):
        """Patch a user by ID"""

        log.info("PATCH /user")

        # Get args

        args = parser.parse_args()

        calender_entry_id = args['id']

        # gets user auth id
        user_id = get_jwt_identity()

        # check if user exists
        try:
            calender_entry_patch = CalendarEntry.get(
                (CalendarEntry.id == calender_entry_id) & (CalendarEntry.user == user_id))
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and still reach this far)
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couldn't be found by this id.")
            return Response(status=400, response="User couldn't be found by this id.")

        # get data from json
        data = request.get_json()

        # validate data through user schema
        try:
            calender_entry_validated = CalendarEntrySimpleSchema().load(data)
        except Exception as e:
            log.error("Error validating user: " + str(e))
            return Response(status=400, response="Error patching user: " + str(e))

        for key, value in calender_entry_validated.items():
            if value is not None:
                if key == 'realization_date':
                    if datetime.now() > calender_entry_validated[key]:
                        return Response(status=400, response="Realization date supplied, can't be in the past.")

                    calender_entry_patch.realization_date = calender_entry_validated[key]
                else:
                    setattr(calender_entry_patch, key, value)

        calender_entry_patch.save()

        log.info("Finished PATCH /user")
        return Response(status=200, response=json.dumps(
            CalendarEntrySchema().dump(calender_entry_patch)), mimetype="application/json")

    @jwt_required()
    def delete(self):
        """Delete a comment by ID"""

        log.info("DELETE /calendar")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        id = args['id'] if args['id'] else None

        # Validate args

        if not id:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # delete by referencing the user id
        try:
            calendar_entry = CalendarEntry.get(id, CalendarEntry.user == user_id)
        except peewee.DoesNotExist:
            log.error("User does not follow referenced account.")
            return Response(status=400, response="User does not follow referenced account.")

        calendar_entry.delete_instance()

        log.info("Finish DELETE /calendar")
        return Response(status=200)


@api.route("/ingredients/list")
class CalendarResource(Resource):

    @jwt_required()
    def get(self):
        """List all ingredients on calender """

        log.info("GET /calendar/list")

        # Get args

        args = parser.parse_args()

        from_date = parse_date(args['from_date']) if args['from_date'] else None
        to_date = parse_date(args['to_date']) if args['to_date'] else None

        # gets user auth id

        user_logged_id = get_jwt_identity()

        # check if user exists
        try:
            user_logged = UserDB.get(user_logged_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and still reach this far)
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couldn't be found by this id.")
            return Response(status=400, response="User couldn't be found by this id.")

        # validate args

        if user_logged.user_portion == -1:
            return Response(status=400, response="User can't have default's portion to access this.")

        if from_date is None:
            return Response(status=400, response="From date cant be null")

        if to_date is None:
            return Response(status=400, response="To date cant be null")

        if from_date > to_date:
            return Response(status=400, response="From date cant be after to date.")

        # declare response holder

        response_holder = {}

        # query

        query = (RecipeIngredientQuantity
                 .select()
                 .join(Recipe)
                 .join(CalendarEntry)
                 .where((CalendarEntry.realization_date >= from_date) &
                        (CalendarEntry.realization_date <= to_date)))

        total_ingredients = {}

        for item in query:
            ratio = 1
            if item.recipe.portion and 'pessoas' in item.recipe.portion:
                portion = int(item.recipe.portion.split(" ")[0])
                if user_logged.user_portion >= 1:
                    ratio = user_logged.user_portion / portion

            ingredient_name = item.ingredient.name
            if ingredient_name in total_ingredients:
                total_ingredients[ingredient_name]["quantity"] += float(item.quantity_normalized) * ratio
                if item.extra_quantity:
                    total_ingredients[ingredient_name]["extra_quantity"] += float(item.extra_quantity) * ratio
            else:
                total_ingredients[ingredient_name] = ShoppingIngredientSchema().dump({
                    "ingredient": item.ingredient,
                    "quantity": float(item.quantity_normalized) * ratio,
                    "extra_quantity": float(item.extra_quantity) * ratio if item.extra_quantity else None,
                    "units": item.units_normalized,
                    "extra_units": item.extra_units,
                })

        response_holder["result"] = list(total_ingredients.values())

        # response data

        log.info("Finish GET /ingredients/list")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


@api.route('/list/check')
class CalendarResource(Resource):

    @jwt_required()
    def post(self):
        """ Used to check a notification's list """

        # Get json data

        log.info("POST /list/check")

        json_data = request.get_json()

        # validate body

        try:
            calenderEntryListUpdateSchema = CalenderEntryListUpdateSchema().load(json_data)
        except ValidationError as err:
            return Response(status=400, response=json.dumps(err.messages), mimetype="application/json")

        # gets user auth id

        user_id = get_jwt_identity()

        # delete

        checked_done = []
        checked_removed = []
        for item in calenderEntryListUpdateSchema['calender_entry_state_list']:
            if item['state']:
                checked_done.append(item['id'])
            else:
                checked_removed.append(item['id'])

        try:
            query_done = CalendarEntry.update(checked_done=True).where(
                (CalendarEntry.id.in_(checked_done)) & (CalendarEntry.user == user_id))
            query_removed = CalendarEntry.update(checked_done=False).where(
                (CalendarEntry.id.in_(checked_removed)) & (CalendarEntry.user == user_id))
            query_done.execute()
            query_removed.execute()
        except peewee.DoesNotExist:
            return Response(status=400, response="Unable to update this notifications...")

        log.info("POST /notification/delete")
        return Response(status=200)
