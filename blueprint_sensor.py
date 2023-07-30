from flask import Blueprint, request, Response, jsonify

from utils import db_write, validate_jwt, db_read

sensor = Blueprint('sensor', __name__)


@sensor.route('/create', methods=['POST'])
def create():
    name = request.json['name']
    jwt = request.json['token']
    min = request.json['min']
    max = request.json['max']
    # description = request.json['description']
    # location = request.json['location']
    if validate_jwt(jwt):
        if db_write("INSERT INTO sensors (name, min, max) VALUES (%s, %s, %s)", [name, min, max]):
            return Response(status=200, response="Sensor created")
        else:
            return Response(status=409, response="Sensor already exists")
    else:
        return Response(status=401, response="Invalid Token")


@sensor.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'GET':
        name = request.args.get('name')
        current_sensor = db_read("SELECT * FROM sensors WHERE name = %s", [name])
        if len(current_sensor) == 1:
            sensor_id = current_sensor[0]["id"]
            sensor_data = db_read("SELECT * FROM sensor_data WHERE sensor_id = %s order by createdAt DESC limit 1", [sensor_id])
            # convert to JSON
            return jsonify(sensor_data[0])
    elif request.method == 'POST':
        name = request.json['name']
        jwt = request.json['token']
        value = request.json['value']
        time = request.json['update']

        if validate_jwt(jwt):
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
                if db_write("INSERT INTO sensor_data (sensor_id, value, createdAt, alert) VALUES (%s, %s, %s, %s)", [sensor_id, value, time, alert]):
                    return Response(status=200, response="Data written to database")
                else:
                    return Response(status=409, response="Could not write to database")
            else:
                return Response(status=404, response="Sensor not found")
        else:
            return Response(status=401, response="Invalid Token")
    else:
        return Response(status=405, response="Method not allowed")
