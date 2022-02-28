# python 3.6

import random
import time
import json

from paho.mqtt import client as mqtt_client


broker = 'localhost'
port = 1883
topic = "test-topic"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
# username = 'emqx'
# password = 'public'


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    # msg_count = 0
    # while True:
    #     time.sleep(5)
    #     msg = f"messages: {msg_count}"
    #     result = client.publish(topic, msg)
    #     # result: [0, 1]
    #     status = result[0]
    #     if status == 0:
    #         print(f"Send `{msg}` to topic `{topic}`")
    #     else:
    #         print(f"Failed to send message to topic {topic}")
    #     msg_count += 1

    msg = {}
    while True:
        random_moisture = random.randint(100, 200)
        time.sleep(5)
        msg.update({'sensor_type': 'SM'})
        msg.update(reading=random_moisture)
        result = client.publish(topic, json.dumps(msg))
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)


if __name__ == '__main__':
    run()
