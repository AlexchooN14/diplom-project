import enum
from pocketparadise import db, login_manager, app
from datetime import datetime
from flask_login import UserMixin


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
    country_id = db.Column(db.Integer, db.ForeignKey('Country.id'))
    users = db.relationship('User', backref='city', lazy=True)

    def __repr__(self):
        return f'| {self.country} | {self.name}'


class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(35), nullable=True, default='/default/default.jpg')  # need to set default pics
    password = db.Column(db.String(60), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, unique=True, default=datetime.now())
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'), nullable=False)
    zones = db.relationship('Zone', backref='user')  # what lazy tag should I add


class Device(db.Model):
    __tablename__ = "Device"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    mac_address = db.Column(db.String(18), nullable=False)
    pp_uuid = db.Column(db.String(10), nullable=False)
    mqtt_uuid = db.Column(db.String(12))
    name = db.Column(db.String(40), nullable=False)
    address = db.Column(db.String(40), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), nullable=True)  # TODO Will it work?
    actuator_present = db.Column(db.Boolean, nullable=False, default=False)
    readings = db.relationship('Reading', backref='device')


# class UniqueID(db.Model):
#     __tablename__ = "UniqueID"
#     id = db.Column(db.Integer, primary_key=True, unique=True)
#     unique_key = db.Column(db.String(40), nullable=False)


ZonesPlants = db.Table('ZonesPlants',
    db.Column('zone_id', db.Integer, db.ForeignKey('Zone.id')),
    db.Column('plant_id', db.Integer, db.ForeignKey('Plant.id'))
)


class Zone(db.Model):
    __tablename__ = "Zone"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(40), nullable=False)
    devices = db.relationship('Device', backref='zone')  # what lazy tag should I add
    address = db.Column(db.String(100), nullable=False)
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

    def __repr__(self):
        return self.name


class IrrigationSchedule(db.Model):
    __tablename__ = "Schedule"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('Zone.id'), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)  # should it stay like this?

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
    read_at = db.Column(db.DateTime, nullable=False)
    device_id = db.Column(db.ForeignKey('Device.id'), nullable=False)
