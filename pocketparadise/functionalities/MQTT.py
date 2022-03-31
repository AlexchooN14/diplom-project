from pocketparadise import (mqtt_client, MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER, TOPIC_DISCOVER_REQUEST,
                            TOPIC_DISCOVER_RESPONSE)
from pocketparadise.models import Device
from pocketparadise import db
import time
import random
import json


port = 1883
client_id = f'python-mqtt-{random.randint(0, 1000)}'
exception_flag = False

def is_uuid_authentic(uuid):
    with open('pocketparadise/functionalities/uuid.json', 'r') as file:
        dictionary = json.load(file)
        file.close()
        return dictionary.get(uuid)


class MQTTConnectionException(Exception):
    def __init__(self):
        self.message = "MQTT could not connect. Check IP or if broker is available."
        super().__init__(self.message)

class MQTTPublishException(Exception):
    def __init__(self, message='Publish failed'):
        self.message = message
        super().__init__(self.message)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
            global exception_flag
            exception_flag = True
            raise MQTTConnectionException
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, port)
    return client


publish_reset_counter = 0

def publish(client, topic, device_id=None):
    global publish_reset_counter, exception_flag

    if topic == TOPIC_DISCOVER_RESPONSE:
        if device_id:
            device = Device.query.get(device_id)
            if device:
                data = json.dumps({"mqtt-id": str(device.id)})
                publish_result = client.publish(topic, data)
                status = publish_result[0]

                if status == 0:
                    print('Send Success')
                else:
                    print(f"Failed to send message to topic {topic}")

                    while status != 0:
                        if publish_reset_counter >= 3:
                            exception_flag = True
                            raise MQTTPublishException(message='Published failed 3 times consecutively.')
                        publish_reset_counter += 1
                        publish_result = client.publish(topic, data)
                        status = publish_result[0]
                        if status == 0:
                            print('Send Success')
                            break
                        else:
                            print(f"Failed to send message to topic {topic}")


def on_message(client, userdata, msg):
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    if msg.topic == TOPIC_DISCOVER_REQUEST:
        print(type(msg))
        msg = str(msg.payload.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        print(type(dictionary))
        print(dictionary)
        mac_address = dictionary.get("mac-address")
        pp_uuid = dictionary.get("uuid")
        if not mac_address or not pp_uuid:

            return
        elif not is_uuid_authentic(pp_uuid):
            print('The submitted uuid is invalid')

            return

        device = Device.query.filter_by(mac_address=mac_address, pp_uuid=pp_uuid).first()
        if device:
            print("Such device was already created, sending forgotten mqtt-id.")
        else:
            device = Device(mac_address=mac_address, pp_uuid=pp_uuid)
            db.session.add(device)
            db.session.commit()
            device = Device.query.filter_by(mac_address=mac_address, pp_uuid=pp_uuid).first()

        try:
            publish(client, TOPIC_DISCOVER_RESPONSE, device.id)
        except MQTTPublishException as e:
            print(e)
            client.loop_stop()
            client.disconnect()
            return

    # elif msg.topic ==:

def start_subscribe(client: mqtt_client):
    client.subscribe(TOPIC_DISCOVER_REQUEST)

    devices = Device.query.all()
    if devices:
        for device in devices:
            print(f'Device\'s name is: {device.name}')
            mqtt_id = device.id
            client.subscribe('devices/' + str(mqtt_id) + '/ping')
            print(f'Subscribed to topic ping for id {str(mqtt_id)}')
            client.subscribe('devices/' + str(mqtt_id) + '/data/+')
            print(f'Subscribed to topic data/+ for id {str(mqtt_id)}')

def subscribe(client: mqtt_client, topics):
    for topic in topics:
        client.subscribe(topic)
        print(f'Subscribed to topic {topic}')

def run():
    global exception_flag
    while True:
        try:
            client = connect_mqtt()
            break
        except MQTTConnectionException as e:
            print(e)

    client.on_message = on_message
    start_subscribe(client)
    client.loop_forever()
    if exception_flag:
        exception_flag = False
        run()


if __name__ == '__main__':
    run()
