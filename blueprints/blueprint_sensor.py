from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils import db_write, db_read, validate_jwt

sensor = Blueprint('sensor', __name__)


@sensor.route('/create', methods=['POST'])
@jwt_required()
def create():
    name = request.json['name']
    min = request.json['min']
    max = request.json['max']
    # description = request.json['description']
    # location = request.json['location']
    current_user = get_jwt_identity()
    if current_user:
        if db_write("INSERT INTO sensors (name, min, max) VALUES (%s, %s, %s)", [name, min, max]):
            return Response(status=200, response="Sensor created")
        else:
            return Response(status=409, response="Sensor already exists")
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
                    return jsonify(sensor_data)
                else:
                    sensor_data = db_read("SELECT * FROM sensor_data WHERE sensor_id = %s order by createdAt DESC limit 1",
                                          [sensor_id])
                    # convert to JSON
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