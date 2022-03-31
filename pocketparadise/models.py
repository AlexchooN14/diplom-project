import enum
from pocketparadise import db, login_manager, app
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.exc import DetachedInstanceError
import uuid
import typing


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AMOUNT(enum.Enum):
    MOST = "MOST"
    MEDIUM = "MEDIUM"
    LEAST = "LEAST"


class METHOD(enum.Enum):
    AT_START = "AT_START"
    AT_END = "AT_END"
    AT_START_AND_END = "AT_START_AND_END"
    SPREAD = "SPREAD"


class SENSOR(enum.Enum):
    SOIL_MOISTURE = "SOIL_MOISTURE"
    AIR_TEMPERATURE = "AIR_TEMPERATURE"
    AIR_HUMIDITY = "AIR_HUMIDITY"
    AIR_PRESSURE = "AIR_PRESSURE"


class Country(db.Model):
    __tablename__ = 'Country'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    cities = db.relationship('City', backref='country')

    def __repr__(self):
        return self.name


class City(db.Model):
    __tablename__ = 'City'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(45), nullable=False, unique=True)
    country_id = db.Column(db.Integer, db.ForeignKey('Country.id'), nullable=False)
    users = db.relationship('User', backref='city', lazy=True)
    zones = db.relationship('Zone', backref='city', lazy=True)

    def __repr__(self):
        return f'| {self.country} | {self.name}'


class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, unique=True, default=datetime.now())
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    zones = db.relationship('Zone', backref='user')

    def __repr__(self):
        return f'{self.first_name} {self.last_name} from {self.city}'

class Device(db.Model):
    __tablename__ = "Device"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mac_address = db.Column(db.String(18), nullable=False, unique=True)
    pp_uuid = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String(40), nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), nullable=True)
    actuator_present = db.Column(db.Boolean, nullable=False, default=False)
    readings = db.relationship('Reading', backref='device')


ZonesPlants = db.Table('ZonesPlants', db.Model.metadata,
    db.Column('zone_id', db.Integer, db.ForeignKey('Zone.id')),
    db.Column('plant_id', db.Integer, db.ForeignKey('Plant.id'))
)


class Zone(db.Model):
    __tablename__ = "Zone"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(40), nullable=False)
    devices = db.relationship('Device', backref='zone')
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    source_flowrate = db.Column(db.Float, nullable=False)
    area_size = db.Column(db.Float, nullable=False)
    irrigation_method = db.Column(db.Enum(METHOD), nullable=False)
    watering_amount = db.Column(db.Enum(AMOUNT), nullable=True)
    schedule = db.relationship('IrrigationSchedule', backref='zone', uselist=False)
    irrigation_data = db.relationship('IrrigationData', backref='zone')
    plants = db.relationship('Plant', secondary=ZonesPlants, backref='zones')


class Plant(db.Model):
    __tablename__ = "Plant"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(40), unique=True)
    humidity_preference = db.Column(db.Enum(AMOUNT), nullable=False)
    sunlight_preference = db.Column(db.Enum(AMOUNT), nullable=False)
    temperature_preference = db.Column(db.Enum(AMOUNT), nullable=False)

    def __repr__(self):
        return f'{self.name} prefers {self.humidity_preference} humidity_preference, {self.sunlight_preference} sunlight_preference and {self.temperature_preference} temperature_preference.'


class IrrigationSchedule(db.Model):
    __tablename__ = "Schedule"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), unique=True, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'{self.start_time} - {self.end_time}'


class IrrigationData(db.Model):
    __tablename__ = "IrrigationData"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), nullable=False)
    at = db.Column(db.DateTime, nullable=False, unique=True)
    duration = db.Column(db.BigInteger, nullable=False)


class Reading(db.Model):
    __tablename__ = "Reading"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    sensor_type = db.Column(db.Enum(SENSOR), nullable=False)
    read_at = db.Column(db.DateTime, nullable=False)
    device_id = db.Column(db.ForeignKey('Device.id'), nullable=False)
    reading = db.Column(db.Float, nullable=False)
