import json
import math
from datetime import datetime, timezone

import peewee
from flask import Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_restx import Namespace, Resource

from ...classes.functions import push_notification
from ...classes.models import TokenBlocklist, Comment as CommentDB, Follow as FollowDB, User as UserDB, PROFILE_TYPE, \
    FollowRequest as FollowRequestDB, NOTIFICATION_TYPE, USER_TYPE
from ...classes.schemas import CommentSchema, build_metadata, UserSimpleSchema, UserToFollow
from ...ext.logger import log

# Create name space
api = Namespace("Follows", description="Here are all comment endpoints")

# Create params for pagination

parser = api.parser()
parser.add_argument('page', type=int, help='The page number.')
parser.add_argument('page_size', type=int, help='The page size.')
parser.add_argument('id', type=int, help='The id to be search.')
parser.add_argument('searchString', type=str, help='The id to be search.')
parser.add_argument('user_id', type=int, help='The user id to be search.')
parser.add_argument('user_follower_id', type=int, help='The user id to be search.')
parser.add_argument('user_followed_id', type=int, help='The user id to be search.')
parser.add_argument('follow_request_id', type=int, help='The user id to be search.')

ENDPOINT = "/follow"


@api.route("/find")
class FollowsListResource(Resource):

    @jwt_required()
    def get(self):
        """List all comments"""

        log.info("GET /find")

        # gets user auth id

        user_logged_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 10

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # query

        query = UserDB.select().where(((UserDB.user_type != USER_TYPE.ADMIN.value) & (UserDB.id != user_logged_id)))

        if args['searchString'] and args['searchString'] != "":
            query = (query
                     .where((UserDB.name.contains(args['searchString'])) | (UserDB.id == args['searchString'])))

        # query for follow request
        query_helper = FollowRequestDB.select(FollowRequestDB.followed).where(
            FollowRequestDB.follower == user_logged_id)

        follow_requests_ids = [item.followed.id for item in query_helper]

        # query for follows
        query_helper = FollowDB.select().where(
            FollowDB.followed == user_logged_id)

        follows_ids = [item.follower.id for item in query_helper]

        # declare response holder

        response_holder = {}

        # metadata

        total_comments = int(query.count())
        total_pages = math.ceil(total_comments / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_comments, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        response_holder["result"] = []

        for item in query.paginate(page, page_size):
            request_sent = item.id in follow_requests_ids
            follower = item.id in follows_ids

            response_holder["result"].append(
                UserToFollow().dump({"user": item, "request_sent": request_sent, "follower": follower}))

        log.info("Finish GET /find")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


# Create resources
@api.route("/list/followers")
class FollowersResource(Resource):

    @jwt_required()
    def get(self):
        """List all followers"""

        log.info("GET /follow/list/followers")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        user_id = args['user_id'] if args['user_id'] else user_id
        page = args['page'] if args['page'] else 1
        page_size = args['page_size'] if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # declare response holder

        response_holder = {}

        # build query

        query = FollowDB.select().where(FollowDB.followed == user_id)

        # metadata

        total_followers = int(query.count())
        total_pages = math.ceil(total_followers / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_followers, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        followers = []
        for item in query.paginate(page, page_size):
            followers.append(UserSimpleSchema().dump(item.follower))

        response_holder["result"] = followers

        log.info("Finish GET /follow/list/followers")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


@api.route("/list/followeds")
class FollowersResource(Resource):

    @jwt_required()
    def get(self):
        """List all followedss"""
        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        # todo não sei se tem logica haver outra validação prévia antes de ser possivel verifcar os seguidos de outra pesssoa
        # provavelmente era bacano fazer como no insta idk
        user_id = args['user_id'] if args['user_id'] else user_id
        page = int(args['page']) if args['page'] else 1
        page_size = int(args['page_size']) if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")
        if page_size not in [5, 10, 20, 40]:
            log.error("page_size not in [5, 10, 20, 40]")
            return Response(status=400, response="page_size not in [5, 10, 20, 40]")

        # declare response holder

        response_holder = {}

        # build query

        query = FollowDB.select().where(FollowDB.follower == user_id)

        # metadata

        total_followers = int(query.count())
        total_pages = math.ceil(total_followers / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_followers, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        followers = []
        for item in query.paginate(page, page_size):
            followers.append(UserSimpleSchema().dump(item.followed))

        response_holder["result"] = followers

        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")


@api.route("")
@api.doc("Follow partial")
class FollowResource(Resource):

    @jwt_required()
    def get(self):
        """ Get a follow whit ID """

        log.info("GET /follow")
        # todo esta rota ainda não sei se faz sentido, mas é para fazer na mesma
        # Get args

        args = parser.parse_args()

        # Validate args

        if not args["id"]:
            log.error("Invalid arguments...")
            return Response(status=400, response="Invalid arguments...")

        # Get and Serialize db model

        try:
            comment_record = CommentDB.get(id=args["id"])
            comment_schema = CommentSchema().dump(comment_record)
        except peewee.DoesNotExist:
            log.error("Recipe does not exist...")
            return Response(status=400, response="Recipe does not exist...")

        log.info("Finish GET /follow")
        return Response(status=200, response=json.dumps(comment_schema), mimetype="application/json")

    @jwt_required()
    def post(self):
        """ Post a follow by user """

        log.info("POST /follow")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        user_to_be_followed_id = args['user_id']

        # Validate args

        if not args["user_id"]:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        if args["user_id"] == user_id:
            log.error("User can't follow himself...")
            return Response(status=400, response="User can't follow himself...")

        # Verify existence of the requested ids model's

        try:
            user_to_be_followed = UserDB.get(user_to_be_followed_id)
        except peewee.DoesNotExist:
            log.error("User to be followed, couln't be found.")
            return Response(status=400, response="User to be followed, couln't be found.")

        try:
            user = UserDB.get(user_id)
        except peewee.DoesNotExist:
            # Otherwise block user token (user cant be logged in and stil reach this far)
            # this only occurs when accounts are not in db
            jti = get_jwt()["jti"]
            now = datetime.now(timezone.utc)
            token_block_record = TokenBlocklist(jti=jti, created_at=now)
            token_block_record.save()
            log.error("User couln't be found.")
            return Response(status=400, response="User couln't be found.")

        # fills comment object

        if user_to_be_followed.profile_type == PROFILE_TYPE.PRIVATE.value:
            follow_request, created = FollowRequestDB.get_or_create(follower=user, followed=user_to_be_followed)
            if not created:
                log.error("User already follows this account.")
                return Response(status=400, response="User already follows this account.")

            # send new follow request notification to recipient
            push_notification(reciever_user=user_to_be_followed,
                              notification_type=NOTIFICATION_TYPE.FOLLOW_REQUEST.value)

            log.info("Finish POST /follow")
            return Response(status=200, response="REQUEST_SENDED")

        else:
            follow, created = FollowDB.get_or_create(follower=user, followed=user_to_be_followed)

            # send new follow notification to recipient
            push_notification(reciever_user=user_to_be_followed,
                              notification_type=NOTIFICATION_TYPE.FOLLOWED_USER.value)

            if not created:
                log.error("User already follows this account.")
                return Response(status=400, response="User already follows this account.")

            return Response(status=201, response="FOLLOWED")

    @jwt_required()
    def delete(self):
        """Delete a follow by ID"""

        log.info("DELETE /follow")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        user_follower_id = args['user_follower_id'] if args['user_follower_id'] else None
        user_followed_id = args['user_followed_id'] if args['user_followed_id'] else None

        # Validate args

        if (not user_follower_id and not user_followed_id) or (user_follower_id and user_followed_id):
            log.error("Invalid arguments...")
            return Response(status=400, response="Invalid arguments...")

        # delete follower
        if user_follower_id:
            try:
                follow = FollowDB.get((FollowDB.followed == user_id) & (FollowDB.follower == user_follower_id))
            except peewee.DoesNotExist:
                log.error("User does not follow referenced account.")
                return Response(status=400, response="User does not follow referenced account.")

            follow.delete_instance()

        # delete followed
        else:
            try:
                follow = FollowDB.get((FollowDB.followed == user_followed_id) & (FollowDB.follower == user_id))
            except peewee.DoesNotExist:
                log.error("User does not follow referenced account.")
                return Response(status=400, response="User does not follow referenced account.")

            follow.delete_instance()

        log.info("Finish DELETE /follow")
        return Response(status=200)


@api.route("/requests")
@api.doc("Follow partial")
class FollowAcceptResource(Resource):

    @jwt_required()
    def post(self):
        """ Accept a follow request by user """

        log.info("POST /requests")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        user_follower_id = args['user_follower_id'] if args['user_follower_id'] else None

        # Validate args

        if not user_follower_id:
            log.error("Missing arguments...")
            return Response(status=400, response="Missing arguments...")

        # Verify existence of the requested ids model's

        try:
            follow_request = FollowRequestDB.get(
                (FollowRequestDB.followed == user_id) & (FollowRequestDB.follower == user_follower_id))
        except peewee.DoesNotExist:
            log.error("Follow request, couln't be found.")
            return Response(status=400, response="User to be followed, couln't be found.")

        # fills comment object

        follow = FollowDB.create(follower=follow_request.follower, followed=follow_request.followed)
        follow.save()

        # send new follow notification to recipient
        push_notification(reciever_user=follow_request.followed,
                          notification_type=NOTIFICATION_TYPE.FOLLOWED_USER.value)

        # delete the request

        follow_request.delete_instance()

        log.info("Finish POST /requests")

        return Response(status=201)

    @jwt_required()
    def delete(self):
        """Delete a follow request by ID"""

        log.info("DELETE /requests")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        user_follower_id = args['user_follower_id'] if args['user_follower_id'] else None
        user_followed_id = args['user_followed_id'] if args['user_followed_id'] else None

        # Validate args

        if (not user_follower_id and not user_followed_id) or (user_follower_id and user_followed_id):
            log.error("Invalid arguments...")
            return Response(status=400, response="Invalid arguments...")

        # delete pedido para seguir

        # delete pedido para ser seguido
        if user_follower_id:
            try:
                follow = FollowRequestDB.get(
                    (FollowRequestDB.followed == user_id) & (FollowRequestDB.follower == user_follower_id))
            except peewee.DoesNotExist:
                log.error("User does not follow referenced account.")
                return Response(status=400, response="User does not follow referenced account.")
        else:
            try:
                follow = FollowRequestDB.get(
                    (FollowRequestDB.followed == user_followed_id) & (FollowRequestDB.follower == user_id))
            except peewee.DoesNotExist:
                log.error("User does not follow referenced account.")
                return Response(status=400, response="User does not follow referenced account.")

        follow.delete_instance()

        log.info("Finish DELETE /requests")
        return Response(status=200)


@api.route("/requests/list")
@api.doc("Follow partial")
class FollowAcceptResource(Resource):

    @jwt_required()
    def get(self):
        """List all follow request"""

        log.info("GET /accept/list")

        # gets user auth id

        user_id = get_jwt_identity()

        # Get args

        args = parser.parse_args()

        page = args['page'] if args['page'] else 1
        page_size = args['page_size'] if args['page_size'] else 5

        # validate args

        if page <= 0:
            log.error("page cant be negative")
            return Response(status=400, response="page cant be negative")

        # declare response holder

        response_holder = {}

        # build query

        query = FollowRequestDB.select().where(FollowRequestDB.followed == user_id)

        # metadata

        total_followers = int(query.count())
        total_pages = math.ceil(total_followers / page_size)
        metadata = build_metadata(page, page_size, total_pages, total_followers, ENDPOINT)
        response_holder["_metadata"] = metadata

        # response data

        followers = []
        for item in query.paginate(page, page_size):
            followers.append(UserSimpleSchema().dump(item.follower))

        response_holder["result"] = followers

        log.info("Finish GET /accept/list")
        return Response(status=200, response=json.dumps(response_holder), mimetype="application/json")
