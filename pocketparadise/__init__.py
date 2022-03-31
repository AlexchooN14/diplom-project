import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from paho.mqtt import client as mqtt_client

app = Flask(__name__, template_folder='../templates')
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MQTT_USERNAME = os.environ.get('MQTT_USERNAME')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
MQTT_BROKER = '192.168.1.47'
# MQTT_BROKER = os.environ.get('MQTT_BROKER')
TOPIC_DISCOVER_REQUEST = "discover/request"
TOPIC_DISCOVER_RESPONSE = "discover/response"
API_KEY = '42a3f0d8a9dc5520e3a6a1b08e93e056'
IRRIGATION_OFFSET = 60  # In minutes
# WAKEUP_INTERVAL = 60  # In minutes
CONFIG_SEND_OFFSET = 30  # In seconds

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')
mail = Mail(app)

from pocketparadise import routes
