import os

import requests
from sqlalchemy import or_
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt
from list_block import BLOCKLIST
from database import db
from schemas import UserSchema, UserRegisterSchema
from models import UserTable
import jinja2

# Creating a Flask-Smorest Blueprint
blp = Blueprint("Users", "users", description="Operations on users")

# Loading templates using Jinja2
template_loader = jinja2.FileSystemLoader("templates")
template_env = jinja2.Environment(loader=template_loader)


def render_template(template_filename, **context):
    return template_env.get_template(template_filename).render(**context)


# Using Mailgun API for sending emails
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


# Class for handling user registration at the /register endpoint
@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):
        # Check if the given username or email already exists
        existing_user = UserTable.query.filter(or_(UserTable.username == user_data["username"],UserTable.email == user_data["email"])).first()

        if existing_user:
            abort(409, message="Given username or email is already exist")
        # Create a new user and hash their password
        user = UserTable(username=user_data["username"], email=user_data["email"], password=pbkdf2_sha256.hash(user_data["password"]))

        # Add the user to the database
        db.session.add(user)
        db.session.commit()

        # Send a confirmation email to the user
        subject = "Successfully signed up"
        body = f"Hi {user.username} You have successfully signed up to the stores REST API."
        html_body = render_template("email/action.html", username=user.username)
        send_simple_message(to=user.email, subject=subject, body=body, html=html_body)

        return {"message": "User created successfully"}, 201


# Class for handling user login at the /login endpoint
@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        # Query the user by username
        user = UserTable.query.filter(UserTable.username == user_data["username"]).first()

        # Verify the password and generate tokens if valid
        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}

        # Abort with 401 status if credentials are invalid
        abort(401, message="Invalid credentials")


# Class for handling token refresh at the /refresh endpoint
@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)

        # Add the refreshed token's jti to the blocklist
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}, 200


# Class for handling user logout at the /logout endpoint
@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}


# Class for handling user information at the /user/<string:user_id> endpoint
@blp.route("/user/<string:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserTable.query.get_or_404(user_id)
        return user

    def delete(self, user_id):
        user = UserTable.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()

        return {"message": "User deleted"}, 200
