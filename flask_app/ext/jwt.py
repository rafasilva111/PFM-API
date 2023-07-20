from datetime import timedelta

from flask_jwt_extended import JWTManager
from peewee import DoesNotExist

from flask_app.classes.models import TokenBlocklist

ACCESS_EXPIRES = timedelta(hours=1)

jwt = JWTManager()


# Callback function to check if a JWT exists in the database blocklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    try:
        TokenBlocklist.get(jti=jti)
    except DoesNotExist:
        return False
    return True


def init_app(app):
    jwt.init_app(app)
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
    app.config["JWT_SECRET_KEY"] = 'super-secret'  # Change this to a secure secret key in production
