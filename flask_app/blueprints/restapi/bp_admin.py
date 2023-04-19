import json

from flask import Response, Blueprint
from flask import current_app as app
admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix="/api/v1")

# Admin API Model


@admin_blueprint.route("/create_tables", methods=["GET"])
def teste():
    app.db.create_tables()
    return Response(status=200, response=json.dumps("Tables successfully created."))

