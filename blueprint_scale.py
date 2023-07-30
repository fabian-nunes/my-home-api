from flask import Blueprint, request, Response, jsonify

from utils import db_write, validate_jwt, db_read, process_image

scale = Blueprint('scale', __name__)


@scale.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'GET':
        current_scale = db_read("SELECT weight as value, createdAt from scale order by createdAt DESC limit 1")
        if len(current_scale) == 1:
            return jsonify(current_scale[0])
        return Response(status=409, response="No data stored")
    elif request.method == 'POST':
        image = request.files['img']
        user = request.form['user']

        values = process_image(image, user)
        if values:
            return Response(status=200, response="Data stored")
        return Response(status=409, response="No data stored")
