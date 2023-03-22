import json

from flask import Response, Blueprint
from flask_restx import Namespace

from flask_app.ext.database import DBManager
admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix="/api/v1")

# Admin API Model


@admin_blueprint.route("/create_tables", methods=["GET"])
def teste():
    DBManager().create_tables()
    return Response(status=200, response=json.dumps("Tables successfully created."))
