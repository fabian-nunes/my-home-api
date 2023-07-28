from flask import Flask
from flask_mysqldb import MySQL
from flask_cors import CORS

from settings import MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

app = Flask(__name__)
cors = CORS(app)

# MySQL configurations
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

db = MySQL(app)

from blueprint_auth import auth
from blueprint_sensor import sensor
from blueprint_scale import scale

# Register blueprints
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(sensor, url_prefix='/api/sensor')
app.register_blueprint(scale, url_prefix='/api/scale')
