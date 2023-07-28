from flask import Blueprint, request, Response, jsonify

from utils import db_write, validate_jwt, db_read, process_image

scale = Blueprint('scale', __name__)


@scale.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'GET':
        current_scale = db_read("SELECT weight from scale order by createdAt DESC limit 1")
        if len(current_scale) == 1:
            return jsonify(current_scale[0])
        return Response(status=409, response="No data stored")
    elif request.method == 'POST':
        image = request.files['img']
        #user = request.json['user']
        user = 0
        values = process_image(image, user)
        return jsonify(values)
