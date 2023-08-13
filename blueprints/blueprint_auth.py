from flask import Blueprint, request, jsonify, Response
from utils import validate_user_input, generate_hash, generate_salt, db_write, validate_user, send_email
from flask_jwt_extended import create_access_token

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST'])
def login():
    user_email = request.form["email"]
    user_password = request.form["password"]

    if validate_user(user_email, user_password):
        access_token = create_access_token(identity=user_email)
        return jsonify(access_token=access_token)
    else:
        return Response(status=401, response="Invalid credentials")


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
            # Assuming you have a function send_email(subject, body, recipient_email) to send the email

            # Registration Successful
            subject = "Welcome " + user_username + " to My Home!"

            # Email body
            body = "Dear " + user_username + ",\n\n" + "Welcome to My Home!\n\n" + ("We're excited to have you as part "
                                                                                    "of our community. With My Home, "
                                                                                    "you're now on the path to a "
                                                                                    "smarter and more connected home "
                                                                                    "environment.\n\n") + ("Your "
                                                                                                           "registration was successful, and you can start enjoying the benefits of a smarter home. Log in to your account and explore the possibilities:\n\n") + "Username: " + user_username + "\n\n" + "Log in now by clicking the button below \n\n" + "If you have any questions or need assistance, please don't hesitate to reach out. Our support team is here to help.\n\n" + "Thank you for choosing My Home. Let's make your home smarter, together!\n\n" + "Best regards,\nThe My Home Team"

            # Sending the email
            send_email(subject, body, user_email)

            return Response(status=201, response="User created")
        else:
            # Registration Failed
            return Response(status=409, response="User already exists")
    else:
        # Registration Failed
        return Response(status=400, response="Invalid input")
