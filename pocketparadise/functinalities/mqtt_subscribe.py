from paho.mqtt import client as mqtt_client
import random
import json
from pocketparadise import session
from models import Readings

broker = 'localhost'
port = 1883
topic = "test-topic"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
# username = 'Sasho'
# password = '.......'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
            return

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

        # message = msg.payload.decode()
        # print(type(message))
        # message = json.loads(message)
        # print(type(message))
        message = str(msg.payload.decode("utf-8", "ignore"))
        message = json.loads(message)  # decode json data
        print(message)

        sensor_type = message.get('sensor_type')
        print(sensor_type)
        reading = message.get('reading')
        print(reading)
        table_row = Readings(sensor_type=sensor_type, reading=reading)
        session.add(table_row)
        session.commit()

    client.subscribe(topic)
    client.on_message = on_message
