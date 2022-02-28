from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, DATETIME
# from sqlalchemy.orm import relationship
from pocketparadise import Base
import datetime


class Readings(Base):
    __tablename__ = "Readings"
    id = Column(Integer, primary_key=True)
    # sensor type can be 'SM', 'AM', 'AT', 'AB', 'AP'
    sensor_type = Column(String(2), default='SM')
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    reading = Column(Integer, nullable=False)

    def __init__(self, sensor_type, reading):
        self.sensor_type = sensor_type
        self.reading = reading


# class User(Model):
#     __tablename__ = "User"
#     id = Column(Integer, primary_key=True)
#     username = Column(String(40), unique=True)
#     email = Column(String(80), unique=True, nullable=False)
#     password = Column(String(80), nullable=False)
#     # login_id = Column(String(36), nullable=True)
#
#
# class Device(Model):
#     __tablename__ = "Device"
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('User.id'))
