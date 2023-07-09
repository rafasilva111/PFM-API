import json

from flask import Response, Blueprint
from flask_app.ext.database import db
admin_blueprint = Blueprint('admin_blueprint', __name__, url_prefix="/api/v1")

from flask_app.ext.database import models
# Admin API Model

@admin_blueprint.route("/create_tables", methods=["GET"])
def teste():
    db.create_tables(models)
    db.close()
    return Response(status=200, response=json.dumps("Tables successfully created."))

