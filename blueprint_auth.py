from flask import Blueprint, request, jsonify, Response
from utils import validate_user_input, generate_hash, generate_salt, db_write, validate_user

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST'])
def login():
    user_email = request.json["email"]
    user_password = request.json["password"]

    user_token = validate_user(user_email, user_password)

    if user_token:
        return jsonify({"jwt_token": user_token})
    else:
        Response(status=401)


@auth.route('/register', methods=['POST'])
def register():
    user_email = request.json['email']
    user_password = request.json['password']
    user_password_confirm = request.json['password_confirm']
    user_username = request.json['username']

    if user_password == user_password_confirm and validate_user_input(
            "authentication", email=user_email, password=user_password):
        password_salt = generate_salt()
        password_hash = generate_hash(user_password, password_salt)

        if db_write(
                """INSERT INTO users (email, name, password_salt, password_hash) VALUES (%s, %s, %s, %s)""",
                (user_email, user_username, password_salt, password_hash),
        ):
            # Registration Successful
            return Response(status=201)
        else:
            # Registration Failed
            return Response(status=409)
    else:
        # Registration Failed
        return Response(status=400)
