from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import db_write, db_read, process_image

scale = Blueprint('scale', __name__)


@scale.route('/data', methods=['GET', 'POST'])
@jwt_required()
def data():
    if request.method == 'GET':
        current_scale = db_read("SELECT weight as value, createdAt, alert from scale order by createdAt DESC limit 1")
        if len(current_scale) == 1:
            return jsonify(current_scale[0])
        return Response(status=409, response="No data stored")
    elif request.method == 'POST':
        image = request.files['img']
        user = request.form['user']
        current_user = get_jwt_identity()
        if current_user:
            if user != current_user:
                return Response(status=401, response="Unauthorized")

            #get id from user
            user_id = db_read("SELECT id FROM user WHERE email = %s", (current_user,))
            values = process_image(image, user_id)
            if values:
                return Response(status=200, response="Data stored")
            return Response(status=409, response="No data stored")
        return Response(status=401, response="Unauthorized")
