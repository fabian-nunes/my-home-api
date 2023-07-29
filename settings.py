from dotenv import load_dotenv
from flask_mysqldb import MySQL

import os

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")
mysql = MySQL()

JW = os.getenv("JWT_SECRET_KEY")
