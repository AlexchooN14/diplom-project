from time import sleep
import gc
import machine
import network
import ubinascii
import json
from umqttsimple import MQTTClient
from Blink import blink
from FileManager import get_uuid, write_to_file, get_mqtt_id

gc.collect()

mqtt_server = '192.168.1.7'
username = 'sasho'
password = 'A1403lex'
client_id = ubinascii.hexlify(machine.unique_id())
client = None


connect_reset_counter = 0

def connect(callback_function):
    global client, client_id, mqtt_server, username, password, connect_reset_counter
    if not connect_reset_counter >= 3:
        try:
            client = MQTTClient(client_id, mqtt_server, 1883, username, password)
            client.set_callback(callback_function)
            client.connect()
            print('Connected to %s MQTT broker' % mqtt_server)
            gc.collect()
            return client
        except OSError:
            connect_reset_counter += 1
            restart_and_reconnect()
    else:
        print('Too many unsuccessful attempts. Could not connect to broker')


def discovery_sub_cb(topic, msg):
    print((topic, msg))
    blink(0.5, 1, True)  # Pulsing  2   times fast  - MQTT message
    if topic.decode('utf-8') == 'discover/response':
        print('ESP received mqtt id message')
        print(type(msg))
        msg = str(msg.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        print(type(dictionary))
        print(dictionary)
        write_to_file('passwd.json', dictionary)
        return  # TODO should it be restart_and_reconnect


def discovery():
    global client

    topic_sub = 'discover/response'
    topic_pub = 'discover/request'

    client = connect(discovery_sub_cb)
    blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker
    gc.collect()

    # Subscribe to discover/response
    client.subscribe(topic_sub)
    print('Subscribed to %s topic' % topic_sub)

    # Get MAC, UUID of system
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    uuid = get_uuid()
    dictionary = {
        "mac-address": mac,
        "uuid": uuid
    }
    data = json.dumps(dictionary)
    print(data)
    gc.collect()

    # Send them as json to topic discover/request
    try:
        client.publish(topic_pub, data)
        sleep(5)
        client.wait_msg()
    except OSError:
        restart_and_reconnect()


def normal_operation_sub_cb(topic, msg):
    mqtt_id = get_mqtt_id()
    if topic.decode('utf-8') == 'devices/' + mqtt_id + '/configure':
        print('ESP received configuration message')
        print(type(msg))
        msg = str(msg.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        print(type(dictionary))
        print(dictionary)
        write_to_file('config.json', dictionary)


def normal_operation():
    global client
    mqtt_id = get_mqtt_id()
    topic_configure = 'devices/' + mqtt_id + '/configure'  # Should subscribe to
    topic_ping = 'devices/' + mqtt_id + '/ping'  # Should publish to
    topic_readings = 'devices/' + mqtt_id + '/data/readings'  # Should publish to
    topic_irrigations = 'devices/' + mqtt_id + '/data/irrigations'  # Should publish to

    client = connect(normal_operation_sub_cb)
    blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker
    gc.collect()

    from FileManager import check_file_exists, get_upcoming_irrigation
    if check_file_exists('config.json'):
        irrigation_dictionary = get_upcoming_irrigation()

    client.subscribe(topic_configure)
    print('Subscribed to %s topic' % topic_configure)

    try:
        client.publish(topic_ping, {'mqtt-id': mqtt_id})  # Ping mqtt id of system to inform web app
        sleep(10)  # TODO try an implementation with a Timer
        client.check_msg()
    except OSError:
        restart_and_reconnect()

    # Save data from message to config file
    # TODO how will component scan be implemented
    # Read sensor data
    # Publish sensor data
    from ReadSensors import read_soil_moisture, read_illumination, read_bme_sensor
    bme_reading = read_bme_sensor()
    if bme_reading is not None:  # TODO edit after implementing sleep for fixing sensors
        try:
            client.publish(topic_readings, bme_reading)
            sleep(5)
        except OSError:
            restart_and_reconnect()


    # Make a checker for the most soon irrigation
    # If there is one and the time has come --> irrigation
    # Else if there is one and the time hasn't come --> new timer, съобразен с starting period
    #

    # try:
    #     client.check_msg()
    #     client.publish(topic_pub, data)
    # except OSError:
    #     restart_and_reconnect()


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    sleep(2)
    machine.reset()
