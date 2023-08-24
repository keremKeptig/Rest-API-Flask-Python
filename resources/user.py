import os

import requests
from flask import current_app
from sqlalchemy import or_
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt
import redis
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from blocklist import BLOCKLIST
from db import db
from schemas import UserSchema, UserRegisterSchema
from models import UserModel
from tasks import send_user_registration_email
from rq import Queue
import jinja2



blp = Blueprint("Users", "users", description="Operations on users")
template_loader = jinja2.FileSystemLoader("templates")
template_env = jinja2.Environment(loader=template_loader)
def render_template(template_filename, **context):
    return template_env.get_template(template_filename).render(**context)

def send_simple_message(to, subject, body, html):
    DOMAIN = os.getenv("MAILGUN_DOMAIN")
    return requests.post(
        f"https://api.mailgun.net/v3/{DOMAIN}/messages",
        auth=("api", os.getenv("MAILGUN_API_KEY")),
        data={
            "from": f"Kerem Keptiğ <mailgun@{DOMAIN}>",
            "to": [to],
            "subject": subject,
            "text": body,
            "html": html,
        },
    )
@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        if UserModel.query.filter(or_(UserModel.username == user_data["username"],
                                      UserModel.email == user_data["email"])).first():
            abort(409, message="Given username or email is already exist")

        user = UserModel(username=user_data["username"], email=user_data["email"],password=pbkdf2_sha256.hash(user_data["password"]))

        db.session.add(user)
        db.session.commit()

        send_simple_message(to=user.email, subject="Successfully signed up"
                            , body=f"Hi {user.username} You have successfully signed up to the stores REST API.",
                            html=render_template("email/action.html", username=user.username))

        return {"message": "User created successfully"}, 201


@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(UserModel.username == user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}

        abort(401, message="Invalid credentials")


@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        # Make it clear that when to add the refresh token to the blocklist will depend on the app design
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}, 200


@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}


@blp.route("/user/<string:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return {"message": "User deleted"}, 200
