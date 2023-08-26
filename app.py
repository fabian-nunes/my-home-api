from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from settings import MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, mysql, JWT_SECRET, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, \
    MAIL_PASSWORD, MAIL_USE_TLS, mail

from utils import cleanup_user, clean_forgot_password

app = Flask(__name__)
cors = CORS(app)

# MySQL configurations
app.config['MYSQL_USER'] = MYSQL_USER
app.config['MYSQL_PASSWORD'] = MYSQL_PASSWORD
app.config['MYSQL_DB'] = MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS

mysql.init_app(app)
jwt = JWTManager(app)
mail.init_app(app)

# Start scheduler
scheduler = BackgroundScheduler(daemon=True)
atexit.register(lambda: scheduler.shutdown())
scheduler.add_job(cleanup_user, 'interval', minutes=60)
scheduler.add_job(clean_forgot_password, 'interval', minutes=60)
scheduler.start()

from blueprints.blueprint_auth import auth
from blueprints.blueprint_sensor import sensor
from blueprints.blueprint_scale import scale
from blueprints.blueprint_user import user

# Register blueprints
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(sensor, url_prefix='/api/sensor')
app.register_blueprint(scale, url_prefix='/api/scale')
app.register_blueprint(user, url_prefix='/api/user')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
