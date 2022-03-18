import time

import machine
import ubinascii

from umqttsimple import MQTTClient

mqtt_server = '192.168.1.9'
username = 'sasho'
password = 'A1403lex'
client_id = ubinascii.hexlify(machine.unique_id())

topic_pub = b'discover/request'
topic_sub = b'discover/response'

last_message = 0
message_interval = 5
counter = 0


def sub_cb(topic, msg):
    print((topic, msg))
    global topic_sub
    if topic == topic_sub and msg == b'received':
        print('ESP received hello message')


def connect_and_subscribe():
    global client_id, mqtt_server, topic_sub, username, password
    client = MQTTClient(client_id, mqtt_server, 1883, username, password)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(topic_sub)
    print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
    return client


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(5)
    machine.reset()
