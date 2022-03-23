import time
import gc
import machine
import ubinascii
import json
from umqttsimple import MQTTClient
from Blink import blink
from FileManager import get_uuid, write_to_file
gc.collect()

mqtt_server = '192.168.1.9'
username = 'sasho'
password = 'A1403lex'
client_id = ubinascii.hexlify(machine.unique_id())
client = None


def connect(callback_function):
    global client, client_id, mqtt_server, username, password
    client = MQTTClient(client_id, mqtt_server, 1883, username, password)
    client.set_callback(callback_function)
    client.connect()
    print('Connected to %s MQTT broker' % mqtt_server)
    gc.collect()
    return client


# def sub_cb(topic, msg):
#     print((topic, msg))
#     print('ESP received hello message')
#     print(type(msg))


def discovery_sub_cb(topic, msg):
    print((topic, msg))
    blink(0.5, 1, True)  # Pulsing  2   times fast  - MQTT message
    if topic.decode('utf-8') == 'discover/response':
        print('ESP received configuration message')
        print(type(msg))
        msg = str(msg.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        print(type(dictionary))
        print(dictionary)
        write_to_file('config.txt', dictionary)


def discovery():
    import network
    global client

    topic_sub = 'discover/response'
    topic_pub = 'discover/request'

    try:
        client = connect(discovery_sub_cb)
        blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker
    except OSError as e:
        restart_and_reconnect()
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
    while True:
        try:
            client.check_msg()
            client.publish(topic_pub, data)
        except OSError:
            restart_and_reconnect()


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(2)
    machine.reset()
