from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from settings import MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, mysql, JWT_SECRET
from datetime import timedelta

app = Flask(__name__)
cors = CORS(app)

# MySQL configurations
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

mysql.init_app(app)
jwt = JWTManager(app)


from blueprint_auth import auth
from blueprint_sensor import sensor
from blueprint_scale import scale

# Register blueprints
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(sensor, url_prefix='/api/sensor')
app.register_blueprint(scale, url_prefix='/api/scale')

if __name__ == "__main__":
    app.run(host='0.0.0.0')