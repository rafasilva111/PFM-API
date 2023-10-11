
from flask_app.ext import schema
from flask_app.ext import commands
from flask_app.ext import application
from flask_app.ext import jwt
from flask_app.ext import bycrypt
from flask_app.ext.database import Database
from flask_app.blueprints import restapi


def create_run():
    app = application.create_app()
    db = Database(app)
    jwt.init_app(app)
    commands.init_app(app,db)
    schema.init_app(app)
    restapi.init_app(app)
    bycrypt.init_app(app)
    return app,db


# Create app and factory app

# Create app and factory app



if __name__ == "__main__":
    app, db = create_run()
    app.run(debug=True, host="0.0.0.0")

