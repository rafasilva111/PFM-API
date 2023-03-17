from flask_app.ext.database import db
from flask_app.ext.schema import ma
from datetime import datetime



def get_user_schema():
    return UserSchema


class User(db.Model):
    """
    The "person" model is a OneToMany relationship,
    since each person has an assigned school,
    but a school has many people.
    """

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.Integer, nullable=False)

    profile_type = db.Column(db.Integer, nullable=False, default="PRIVATE")
    verified = db.Column(db.Boolean, nullable=False, default=False)
    user_type = db.Column(db.String(50), nullable=False, default="NORMAL")
    img_source = db.Column(db.String(50), nullable=True)

    created_date = db.Column(db.DateTime, nullable=False)
    updated_date = db.Column(db.DateTime, nullable=False)

    activity_level = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    sex = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.Float, nullable=True)




class UserSchema(ma.Schema):
    class Meta:
        model = User
        include_fk = True
        fields = ('__all__',)
