import random
import string
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, Response
from utils import validate_user_input, generate_hash, generate_salt, db_write, validate_user, send_email, db_read
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
    user_email = request.form['email']
    user_password = request.form['password']
    user_password_confirm = request.form['password_confirm']
    user_username = request.form['username']

    if user_password == user_password_confirm and validate_user_input(
            "authentication", email=user_email, password=user_password):
        password_salt = generate_salt()
        password_hash = generate_hash(user_password, password_salt)

        # generate random string
        random_string = ''.join(random.choice(string.ascii_letters) for i in range(10))
        created_at = datetime.now()

        if db_write(
                """INSERT INTO users (email, name, password_salt, password_hash, createdAt, confirmToken) VALUES (%s, 
                %s, %s, %s, %s, %s)""",
                (user_email, user_username, password_salt, password_hash, created_at, random_string)
        ):
            # Assuming you have a function send_email(subject, body, recipient_email) to send the email

            # Registration Successful
            subject = "Welcome " + user_username + " to My Home!"

            registration_link = "http://192.168.1.200/confirm/" + random_string

            # Email body
            body = "Dear " + user_username + ",\n\n" + "Welcome to My Home!\n\n" + "We're excited to have you as part of our community. With My Home, you're now on the path to a smarter and more connected home environment.\n\n" + "Your registration was successful, and you're almost there! To complete the process and start enjoying the benefits of a smarter home, please click the following link to confirm your registration:\n\n" + registration_link + "\n\n" + "This link is valid for 24 hours. Once you've completed this step, you can log in to your account and explore the possibilities:\n\n" + "Username: " + user_username + "\n\n" + "Log in now: [Insert Login Link]\n\n" + "If you have any questions or need assistance, please don't hesitate to reach out. Our support team is here to help.\n\n" + "Thank you for choosing My Home. Let's make your home smarter, together!\n\n" + "Best regards,\nThe My Home Team"

            # Sending the email
            send_email(subject, body, user_email)

            return Response(status=201, response="User created")
        else:
            # Registration Failed
            return Response(status=409, response="User already exists")
    else:
        # Registration Failed
        return Response(status=400, response="Invalid input")


@auth.route('/confirm', methods=['POST'])
def confirm_registration():
    confirm_token = request.form['token']

    current_user = db_read("""SELECT * FROM users WHERE confirmToken = %s""", (confirm_token,))
    if len(current_user) == 1:
        created_at = current_user[0]['createdAt']
        # transform datetime object to string
        #created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
        confirmed = current_user[0]['confirmed']
        if created_at < datetime.now() - timedelta(hours=24):
            return Response(status=400, response="Token expired")
        elif confirmed == 1:
            return Response(status=400, response="User already confirmed")
        db_write("""UPDATE users SET confirmed = %s WHERE confirmToken = %s""", (True, confirm_token))
        return Response(status=200, response="User confirmed")
    else:
        return Response(status=400, response="Invalid token")
