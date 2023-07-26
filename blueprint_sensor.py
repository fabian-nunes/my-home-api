from flask import Blueprint, request, jsonify, Response
from utils import validate_user_input, generate_hash, generate_salt, db_write, validate_user, validate_jwt

sensor = Blueprint('sensor', __name__)


@sensor.route('/create', methods=['POST'])
def create():
    name = request.json['name']
    jwt = request.json['token']
    # description = request.json['description']
    # location = request.json['location']
    if validate_jwt(jwt):
        if db_write("INSERT INTO sensors (name) VALUES (%s)", [name]):
            return Response(status=200)
        else:
            return Response(status=409)
    else:
        return Response(status=401)


@sensor.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        name = request.json['name']
        jwt = request.json['token']
        value = request.json['value']
        time = request.json['time']


    else:
        pass
