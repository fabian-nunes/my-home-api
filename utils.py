import os
import re
import time
from datetime import datetime
from hashlib import pbkdf2_hmac

import jwt
import pytesseract
from flask import render_template
from flask_mail import Message
from flask_mysqldb import MySQLdb

from settings import mysql as db, JW, MAIL_USERNAME, mail, ALLOWED_EXTENSIONS, MAX_IMAGE_SIZE, UPLOAD_FOLDER

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def validate_user_input(input_type, **kwargs):
    if input_type == "authentication":
        if len(kwargs["email"]) <= 255 and len(kwargs["password"]) <= 255:
            return True
        else:
            return False


def generate_salt():
    salt = os.urandom(16)
    return salt.hex()


def generate_hash(plain_password, password_salt):
    password_hash = pbkdf2_hmac(
        "sha256",
        b"%b" % bytes(plain_password, "utf-8"),
        b"%b" % bytes(password_salt, "utf-8"),
        10000,
    )
    return password_hash.hex()


def db_write(query, params):
    cursor = db.connection.cursor()
    try:
        cursor.execute(query, params)
        db.connection.commit()
        cursor.close()

        return True

    except MySQLdb._exceptions.IntegrityError:
        cursor.close()
        return False


def db_read(query, params=None):
    cursor = db.connection.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    entries = cursor.fetchall()
    cursor.close()

    content = []

    for entry in entries:
        content.append(entry)

    return content


def validate_user(email, password):
    current_user = db_read("""SELECT * FROM users WHERE email = %s and confirmed = 1""", (email,))

    if len(current_user) == 1:
        saved_password_hash = current_user[0]["password_hash"]
        saved_password_salt = current_user[0]["password_salt"]
        password_hash = generate_hash(password, saved_password_salt)

        if password_hash == saved_password_hash:
            return True
        else:
            return False

    else:
        return False


def process_image(image, user):
    # text dictionary
    text_lan = ["Weight", "BMI", "Body fat rate", "Subcutaneous fat", "Visceral fat", "Body water",
                "Skeletal muscle rate",
                "Muscle mass", "Bone mass", "Protein", "BMR", "Body age"]
    # Save the image to a temporary location
    image_path = 'temp_image.jpg'
    image.save(image_path)

    # Extract text from the image using OCR
    extracted_text = pytesseract.image_to_string(image_path)

    weight = 0
    bmi = 0
    body_fate_rate = 0
    sub_fat = 0
    visc_fat = 0
    body_water = 0
    skel_rate = 0
    muscle_mass = 0
    bone_mass = 0
    protein = 0
    bmr = 0
    body_age = 23
    alert = "Normal"
    # user = int(user)

    for line in extracted_text.split("\n"):
        # check if line contains date
        match = re.search(r"\d{2}:\d{2}\s\w{3}\.\d{2},\d{4}", line)
        if match:
            date_str = match.group()

            # Convert the original date string to a datetime object
            datetime_obj = datetime.strptime(date_str, "%H:%M %b.%d,%Y")

            # Format the datetime object to the desired format
            formatted_date = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

            current_date = db_read("""SELECT * FROM scale WHERE createdAt = %s""", (formatted_date,))
            if len(current_date) > 0:
                os.remove(image_path)
                return False

        i = 1

        for label in text_lan:
            if label in line:
                value = re.search(r"\d+(\.\d+)?", line)

                if value:
                    if label == "Weight":
                        weight = float(value.group())

                    elif label == "Body fat rate":
                        body_fate_rate = float(value.group())

                    elif label == "BMI":
                        bmi = float(value.group())
                        bmi = bmi / 10
                        bmi = round(bmi, 2)
                        if bmi < 18.5:
                            alert = "Underweight"
                        elif 18.5 <= bmi < 25:
                            alert = "Normal"
                        elif 25 <= bmi < 30:
                            alert = "Overweight"

                    elif label == "Subcutaneous fat":
                        sub_fat = float(value.group())

                    elif label == "Visceral fat":
                        visc_fat = float(value.group())

                    elif label == "Body water":
                        body_water = float(value.group())
                        body_water = body_water / 10
                        body_water = round(body_water, 2)

                    elif label == "Skeletal muscle rate":
                        skel_rate = float(value.group())

                    elif label == "Muscle mass":
                        muscle_mass = float(value.group())
                        muscle_mass = muscle_mass / 10
                        muscle_mass = round(muscle_mass, 2)

                    elif label == "Bone mass":
                        bone_mass = float(value.group())

                    elif label == "Protein":
                        protein = float(value.group())

                    elif label == "BMR":
                        bmr = int(value.group())

                    i += 1

    # Insert the values into the database
    db_write("INSERT INTO scale (createdAt, weight, bmi, fat, sub_fat, visc_fat, water,"
             "muscle_skeleton, mass_muscle, bone_mass, protein, tmb, age, id_user, alert) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
             "%s, %s, %s, %s)", (formatted_date, weight, bmi, body_fate_rate, sub_fat,
                                 visc_fat, body_water, skel_rate, muscle_mass,
                                 bone_mass, protein, bmr, body_age, user, alert))
    # Remove the temporary image
    os.remove(image_path)
    return True


def generate_jwt_token(content):
    encoded_content = jwt.encode(content, JW, algorithm="HS256")
    token = str(encoded_content)
    return token


def validate_jwt(jwt_token):
    try:
        decoded_token = jwt.decode(jwt_token, JW, algorithms=["HS256"])
        return decoded_token
    except jwt.exceptions.DecodeError:
        return False


def send_email(subject, body, recipient):
    message = Message(subject=subject, sender=MAIL_USERNAME, recipients=[recipient])
    message.body = body
    message.html = render_template("mail.html", subject=subject, body=body)

    try:
        mail.send(message)
        print("Email sent")
        return True
    except Exception as e:
        print(e)
        return False


def cleanup_user():
    # get users that are not confirmed and older than 1 day
    users = db_read("""SELECT * FROM users where confirmed = 0 and createdAt > DATE_SUB(NOW(), INTERVAL 1 DAY)""")
    if len(users) == 0:
        return
    for user in users:
        db_write("""DELETE FROM users WHERE id = %s""", (user["id"],))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image(image):
    if image.filename == '':
        return False
    if not image or not allowed_file(image.filename):
        return False

    if len(image.read()) > MAX_IMAGE_SIZE:
        return False

    return True


def store_image(image):
    timestamp = int(time.time())
    image_filename = f"{timestamp}.jpg"

    user_home = os.path.expanduser("~")
    image_path = os.path.join(user_home, UPLOAD_FOLDER, image_filename)
    image.seek(0)  # Reset file pointer before saving
    image.save(image_path)
    return image_path


def change_password(password, current_user):
    password_salt = generate_salt()
    password_hash = generate_hash(password, password_salt)

    if db_write(
            """UPDATE users SET password_salt = %s, password_hash = %s WHERE email = %s""",
            (password_salt, password_hash, current_user)
    ):
        return True
    return False


def change_name(new_name, current_user):
    if db_write(
            """UPDATE users SET name = %s WHERE email = %s""",
            (new_name, current_user)
    ):
        return True
    return False


def clean_forgot_password():
    # get users that are not confirmed and older than 1 day
    users = db_read("""SELECT * FROM forgot_password where createdAt > DATE_SUB(NOW(), INTERVAL 1 DAY)""")
    if len(users) == 0:
        return
    for user in users:
        db_write("""DELETE FROM forgot_password WHERE id = %s""", (user["id"],))
