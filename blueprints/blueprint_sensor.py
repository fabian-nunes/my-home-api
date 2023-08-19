import os

from flask import Blueprint, request, Response, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils import db_write, db_read, validate_jwt, validate_image, store_image

sensor = Blueprint('sensor', __name__)


@sensor.route('/create', methods=['POST', 'PUT'])
@jwt_required()
def create():
    # description = request.json['description']
    # location = request.json['location']
    current_user = get_jwt_identity()
    if current_user:
        min = request.form['min']
        max = request.form['max']
        color = request.form['color']
        image = request.files['img']

        if request.method == 'PUT':
            name = request.args.get('name')
            if image.filename != '':
                valid_image = validate_image(image)
                if not valid_image:
                    return Response(status=400, response="Invalid Image")

                image_url = store_image(image)
            sensor = db_read("SELECT * FROM sensors WHERE name = %s", [name])
            if len(sensor) == 1:
                if image.filename != '':
                    db_write("UPDATE sensors SET name = %s, min = %s, max = %s, img = %s WHERE name = %s",
                             [name, min, max, image_url, name])
                else:
                    db_write("UPDATE sensors SET name = %s, min = %s, max = %s WHERE name = %s", [name, min, max, name])
                return Response(status=200, response="Sensor updated")
            else:
                return Response(status=404, response="Sensor not found")
        else:
            name = request.form['name']
            if name == '' or name == 'Scale':
                return Response(status=400, response="Invalid name")
            valid_image = validate_image(image)
            if not valid_image:
                return Response(status=400, response="Invalid Image")

            image_url = store_image(image)
            if db_write("INSERT INTO sensors (name, min, max, img, color) VALUES (%s, %s, %s, %s, %s)",
                        [name, min, max, image_url, color]):
                return Response(status=200, response="Sensor created")
            else:
                return Response(status=409, response="Sensor already exists")
    else:
        return Response(status=401, response="Invalid Token")


@sensor.route('/specs', methods=['GET'])
def sensors():
    all_data = request.args.get('all')
    all_data = True if all_data == "true" else False
    if all_data:
        sensors_all = db_read("SELECT name, color FROM sensors")
        # convert to JSON
        return jsonify(sensors_all)
    else:
        name = request.args.get('name')
        current_sensor = db_read("SELECT name, min, max, color  FROM sensors WHERE name = %s", [name])
        if len(current_sensor) == 1:
            return jsonify(current_sensor[0])
        else:
            return Response(status=404, response="Sensor not found")


@sensor.route('/image', methods=['GET'])
def image():
    name = request.args.get('name')
    current_sensor = db_read("SELECT * FROM sensors WHERE name = %s", [name])
    if len(current_sensor) == 1:
        image_url = current_sensor[0]["img"]
        if os.path.exists(image_url):
            return send_file(image_url, mimetype='image/jpg')
        return Response(status=404, response="Image not found")
    else:
        return Response(status=404, response="Sensor not found")


@sensor.route('/delete', methods=['DELETE'])
@jwt_required()
def delete():
    name = request.args.get('name')
    current_user = get_jwt_identity()
    if current_user:
        current_sensor = db_read("SELECT * FROM sensors WHERE name = %s", [name])
        if len(current_sensor) == 1:
            sensor_id = current_sensor[0]["id"]
            img = current_sensor[0]["img"]
            if os.path.exists(img):
                os.remove(img)
            db_write("DELETE FROM sensors WHERE name = %s", [name])
            db_write("DELETE FROM sensor_data WHERE sensor_id = %s", [sensor_id])
            return Response(status=200, response="Sensor deleted")
        else:
            return Response(status=404, response="Sensor not found")
    else:
        return Response(status=401, response="Invalid Token")


@sensor.route('/data', methods=['GET', 'POST'])
@jwt_required(optional=True)
def data():
    if request.method == 'GET':
        name = request.args.get('name')
        all_data = request.args.get('all')
        all_data = True if all_data == "true" else False
        current_user = get_jwt_identity()
        if current_user:
            current_sensor = db_read("SELECT * FROM sensors WHERE name = %s", [name])
            if len(current_sensor) == 1:
                sensor_id = current_sensor[0]["id"]
                if all_data:
                    sensor_data = db_read("SELECT * FROM sensor_data WHERE sensor_id = %s order by createdAt DESC",
                                          [sensor_id])
                    # convert to JSON
                    if len(sensor_data) == 0:
                        return Response(status=404, response="No data found")
                    return jsonify(sensor_data)
                else:
                    sensor_data = db_read(
                        "SELECT * FROM sensor_data WHERE sensor_id = %s order by createdAt DESC limit 1",
                        [sensor_id])
                    # convert to JSON
                    if len(sensor_data) == 0:
                        return Response(status=404, response="No data found")
                    return jsonify(sensor_data[0])
            else:
                return Response(status=404, response="Sensor not found")
        else:
            return Response(status=401, response="Invalid Token")
    elif request.method == 'POST':
        name = request.json['name']
        value = request.json['value']
        time = request.json['update']
        token = request.json['token']

        current_user = validate_jwt(token)

        if current_user:
            current_sensor = db_read("SELECT * FROM sensors WHERE name = %s", [name])
            if len(current_sensor) == 1:
                value = float(value)
                sensor_id = current_sensor[0]["id"]
                sensor_min = current_sensor[0]["min"]
                sensor_min = int(sensor_min)
                sensor_max = current_sensor[0]["max"]
                sensor_max = int(sensor_max)
                if value < sensor_min:
                    alert = 'Low'
                elif value > sensor_max:
                    alert = 'High'
                else:
                    alert = 'Normal'
                if db_write("INSERT INTO sensor_data (sensor_id, value, createdAt, alert) VALUES (%s, %s, %s, %s)",
                            [sensor_id, value, time, alert]):
                    return Response(status=200, response="Data written to database")
                else:
                    return Response(status=409, response="Could not write to database")
            else:
                return Response(status=404, response="Sensor not found")
        else:
            return Response(status=401, response="Invalid Token")
    else:
        return Response(status=405, response="Method not allowed")
