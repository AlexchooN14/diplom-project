import enum
from pocketparadise import db, login_manager, app
from datetime import datetime
from flask_login import UserMixin


class AMOUNT(enum.Enum):
    MOST = "MOST"
    MEDIUM = "MEDIUM"
    LEAST = "LEAST"


class METHOD(enum.Enum):
    AT_START = "AT_START"
    AT_END = "AT_END"
    AT_START_AND_END = "AT_START_AND_END"
    SPREAD = "SPREAD"


class Country(db.Model):
    __tablename__ = 'Country'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    cities = db.relationship('City', backref='country')


class City(db.Model):
    __tablename__ = 'City'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    country_id = db.Column(db.Integer, db.ForeignKey('Country.id'))
    users = db.relationship('User', backref='city', lazy=True)


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, unique=True, default=datetime.now())
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    zones = db.relationship('Zone', backref='user')  # what lazy tag should I add


class Device(db.Model):
    __tablename__ = "Device"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(40), nullable=False)
    address = db.Column(db.String(40), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), nullable=False)
    actuator_present = db.Column(db.Boolean, nullable=False, default=False)
    readings = db.relationship('Reading', backref='device')


ZonesPlants = db.Table('ZonesPlants',
    db.Column('zone_id', db.Integer, db.ForeignKey('Zone.id')),
    db.Column('plant_id', db.Integer, db.ForeignKey('Plant.id'))
)


class Zone(db.Model):
    __tablename__ = "Zone"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(40), nullable=False)
    devices = db.relationship('Device', backref='zone')  # what lazy tag should I add
    preferred_watering_amount = db.Column(db.Float, nullable=False)  # per sq. meter per 24h
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    source_flowrate = db.Column(db.Float, nullable=False)
    area_size = db.Column(db.Float, nullable=False)
    algorithm_id = db.Column(db.Integer, db.ForeignKey('Algorithm.id'), nullable=False)
    schedule = db.relationship('IrrigationSchedule', backref='zone', uselist=False)  # what lazy tag should I add
    irrigation_data = db.relationship('IrrigationData', backref='zone')  # what lazy tag should I add
    plants = db.relationship('Plant', secondary=ZonesPlants, backref='zones')


class Plant(db.Model):
    __tablename__ = "Plant"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(40), unique=True)
    humidity_preference = db.Column(db.Enum(AMOUNT), nullable=False)
    sunlight_preference = db.Column(db.Enum(AMOUNT), nullable=False)
    temperature_preference = db.Column(db.Enum(AMOUNT), nullable=False)


class WateringAlgorithm(db.Model):
    __tablename__ = "Algorithm"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(40), nullable=False, unique=True)  # should this be unique
    irrigation_method = db.Column(db.Enum(METHOD), unique=True)  # should this be unique
    zones = db.relationship('Zone', backref='algorithm')  # what lazy tag should I add


class IrrigationSchedule(db.Model):
    __tablename__ = "Schedule"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)  # should it stay like this?


class IrrigationData(db.Model):
    __tablename__ = "IrrigationData"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), nullable=False)
    irrigation_at = db.Column(db.DateTime, nullable=False, unique=True)
    irrigation_duration = db.Column(db.BigInteger, nullable=False)


class Reading(db.Model):
    __tablename__ = "Reading"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    read_at = db.Column(db.DateTime, nullable=False)
    device_id = db.Column(db.ForeignKey('Device.id'), nullable=False)
