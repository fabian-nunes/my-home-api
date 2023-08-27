import datetime
import random

from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils import db_read, change_password, change_name, db_write, send_email

user = Blueprint('user', __name__)


@user.route('/data', methods=['GET'])
@jwt_required()
def data():
    current_user = get_jwt_identity()
    if current_user:
        c_user = db_read("SELECT name FROM users WHERE email = %s", (current_user,))
        if len(c_user) == 1:
            return jsonify(c_user[0])
        return Response(status=409, response="No data stored")
    return Response(status=401, response="Unauthorized")


@user.route('/changeInformation', methods=['POST'])
@jwt_required()
def change_user_password():
    current_user = get_jwt_identity()
    if current_user:
        user = db_read("SELECT name FROM users WHERE email = %s", (current_user,))
        new_password = request.form['password']
        new_password_confirm = request.form['passwordConfirm']
        user_name = request.form['username']

        if new_password is not None and new_password != "":
            if new_password == new_password_confirm:
                if change_password(new_password, current_user) is False:
                    return Response(status=409, response="Something went wrong")
            else:
                return Response(status=400, response="Passwords do not match")

        if user_name is not None:
            if user_name != user[0]['name']:
                if change_name(user_name, current_user) is False:
                    return Response(status=409, response="Something went wrong")

        return Response(status=200, response="Information changed")
    return Response(status=401, response="Unauthorized")


@user.route('/reset', methods=['POST'])
def reset_password():
    token = request.form['token']
    new_password = request.form['password']
    new_password_confirm = request.form['passwordConfirm']

    user = db_read("SELECT id_user FROM forgot_password WHERE token = %s", (token,))
    if len(user) == 0:
        return Response(status=409, response="Token not found")
    user = user[0]['id_user']
    user_data = db_read("SELECT email FROM users WHERE id = %s", (user,))
    if len(user_data) == 0:
        return Response(status=409, response="User not found")
    if new_password is not None:
        if new_password == new_password_confirm:
            if change_password(new_password, user_data[0]['email']) is False:
                return Response(status=409, response="Something went wrong")
            db_write("DELETE FROM forgot_password WHERE token = %s", (token,))
        return Response(status=400, response="Passwords do not match")

    return Response(status=200, response="Password changed")


@user.route('/forgotPassword', methods=['POST'])
def forgot_email():
    email = request.form['email']
    if len(email) == 0:
        return Response(status=400, response="Email cannot be empty")
    # get id from user
    user_id = db_read("SELECT id FROM users WHERE email = %s", (email,))
    if len(user_id) == 0:
        return Response(status=409, response="Email not found")
    user_id = user_id[0]["id"]
    # generate random string
    random_string = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
    created_at = datetime.datetime.now()
    # store random string in database
    if db_write("INSERT INTO forgot_password (id_user, token, createdAt) VALUES (%s, %s, %s)",
                (user_id, random_string, created_at)):
        # send email with link
        subject = "Reset Password"

        reset_link = "http://192.168.1.120/reset/" + random_string

        # Email body
        body = "Dear " + email + ",\n\n" + "You have requested to reset your password.\n\n" + "Please click the following link to reset your password:\n\n" + reset_link + "\n\n" + "This link is valid for 24 hours.\n\n" + "If you have any questions or need assistance, please don't hesitate to reach out. Our support team is here to help.\n\n" + "Thank you for choosing My Home. Let's make your home smarter, together!\n\n" + "Best regards,\nThe My Home Team"

        # Sending the email
        send_email(subject, body, email)
        return Response(status=200, response="Email sent")
    else:
        return Response(status=409, response="Something went wrong")
