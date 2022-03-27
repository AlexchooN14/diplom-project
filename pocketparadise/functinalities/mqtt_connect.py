from pocketparadise import mqtt_client
import random
# from pocketparadise import MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER

MQTT_USERNAME = 'sasho'
MQTT_PASSWORD = 'A1403lex'
MQTT_BROKER = '192.168.1.9'
port = 1883
topic = "test"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
            return

    client = mqtt_client.Client(client_id)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, port)
    return client
