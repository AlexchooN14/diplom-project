from pocketparadise import (mqtt_client, MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER, TOPIC_DISCOVER_REQUEST,
                            TOPIC_DISCOVER_RESPONSE)
from pocketparadise.models import Device, IrrigationData, Reading, SENSOR
from pocketparadise import db
import random
import json
import datetime

port = 1883
client_id = f'python-mqtt-{random.randint(0, 1000)}'

def datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()[:-7]


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
            raise MQTTConnectionException
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, port)
    return client


def publish(client, topic, device_id, message=None):
    if device_id:
        device = Device.query.get(device_id)
    else:
        return

    if not device:
        return

    if topic == TOPIC_DISCOVER_RESPONSE:
        data = json.dumps({"mqtt-id": str(device.id)})
        publish_result = client.publish(topic, data)
        status = publish_result[0]

        if status == 0:
            # Sent successfully
            return
        else:
            # Send failed
            raise MQTTPublishException(message='Discover request publish failed!')
    else:
        # Topic other than discover/request
        if message is None:
            return

        topic_parts = topic.split('/')
        if not topic_parts or len(topic_parts) < 3 or len(topic_parts) > 4:
            return

        elif topic_parts[0] == 'devices':
            if topic_parts[2] == 'configure':
                publish_result = client.publish(topic, json.dumps(message, default=datetime_converter))
                status = publish_result[0]

                if status == 0:
                    # Sent successfully
                    return
                else:
                    # Send failed
                    raise MQTTPublishException(message='Publish failed!')


def on_message(client, userdata, msg):
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    print(type(msg))
    topic = msg.topic
    msg = str(msg.payload.decode("utf-8", "ignore"))
    dictionary = json.loads(msg)  # decode json data
    print(type(dictionary))
    print(dictionary)

    if topic == TOPIC_DISCOVER_REQUEST:
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
            subscribe(client, ['devices/' + str(device.id) + '/ping', 'devices/' + str(device.id) + '/data/+'])
        for i in range(3):
            try:
                publish(client, TOPIC_DISCOVER_RESPONSE, device.id)
                break
            except MQTTPublishException as e:
                if i == 2:
                    print(e)
                    restart_and_reconnect(client)
                else:
                    continue

    else:
        from .Decision import decide
        topic_parts = topic.split('/')

        if not topic_parts or len(topic_parts) < 3 or len(topic_parts) > 4:
            return
        elif topic_parts[0] == 'devices':
            mqtt_id = topic_parts[1]
            device = Device.query.get(mqtt_id)
            if not device:
                print('Such device was not found. No decision will be made.')
                return

            if topic_parts[2] == 'ping':
                mac_address = dictionary.get("mac-address")
                uuid = dictionary.get("uuid")
                config_present = dictionary.get('config-present')

                device.config_present = config_present
                db.session.commit()
                result = decide(device.id)
                print(f'Watering configuration: {result}')

                if result:
                    for i in range(3):
                        try:
                            publish(client, ('devices/' + str(device.id) + '/configure'), device.id, result)
                            break
                        except MQTTPublishException as e:
                            if i == 2:
                                print(e)
                                restart_and_reconnect(client)
                            else:
                                continue
                else:
                    return

            elif topic_parts[2] == 'data':
                if not len(topic_parts) == 4:
                    return
                elif topic_parts[3] == 'readings':
                    for reading in dictionary:
                        sensor_type = reading.get('sensor-type')
                        read_at = reading.get('reading-time')
                        data = reading.get('reading-data')
                        if sensor_type == 'SM':
                            new_reading = Reading(sensor_type=SENSOR.SOIL_MOISTURE, read_at=read_at,
                                                  device=device, reading=data)
                            db.session.add(new_reading)
                            db.session.commit()
                        elif sensor_type == 'BME':
                            for key, value in data.items():
                                new_reading = None
                                if key == 'humidity':
                                    new_reading = Reading(sensor_type=SENSOR.AIR_HUMIDITY, read_at=read_at,
                                                          device=device, reading=value)
                                elif key == 'pressure':
                                    new_reading = Reading(sensor_type=SENSOR.AIR_PRESSURE, read_at=read_at,
                                                          device=device, reading=value)
                                elif key == 'temperature':
                                    new_reading = Reading(sensor_type=SENSOR.AIR_TEMPERATURE, read_at=read_at,
                                                          device=device, reading=value)
                                db.session.add(new_reading)
                                db.session.commit()
                        elif sensor_type == 'AL':
                            new_reading = Reading(sensor_type=SENSOR.LUMINANCE, read_at=read_at,
                                                  device=device, reading=data)
                            db.session.add(new_reading)
                            db.session.commit()

                elif topic_parts[3] == 'irrigations':
                    if dictionary.get('last-irrigation'):
                        start_time = dictionary.get('start-time')
                        duration = dictionary.get('duration')
                        # working_actuator = dictionary.get('working-actuator')
                        zone = device.zone
                        if start_time and duration:
                            irrigation = IrrigationData(zone=zone, at=start_time, duration=duration)  # duration in secs, start_time in UTC
                            db.session.add(irrigation)
                            db.session.commit()
                        else:
                            print("Corrupted irrigation data. Check device!")
        else:
            print("Unhandled topic")


def subscribe(client: mqtt_client, topics):
    for topic in topics:
        client.subscribe(topic)


def start_subscribe(client: mqtt_client):
    client.subscribe(TOPIC_DISCOVER_REQUEST)

    devices = Device.query.all()
    if devices:
        for device in devices:
            mqtt_id = device.id
            subscribe(client, ['devices/' + str(mqtt_id) + '/ping', 'devices/' + str(mqtt_id) + '/data/+'])


def run():
    while True:
        try:
            client = connect_mqtt()
            break
        except MQTTConnectionException as e:
            print(e)

    start_subscribe(client)
    client.on_message = on_message
    client.loop_forever()


def restart_and_reconnect(client):
    client.loop_stop()
    client.disconnect()
    run()


if __name__ == '__main__':
    run()
