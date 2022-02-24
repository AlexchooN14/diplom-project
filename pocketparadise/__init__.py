from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__, template_folder='../templates')
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
db = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(db)
session = Session()
