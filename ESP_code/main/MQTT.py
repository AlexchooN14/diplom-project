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
        restart_and_reconnect()


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
    dictionary = {
        "mac-address": mac,
        "uuid": get_uuid()
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
    print('Start of NO')
    print(gc.mem_free())
    print('---------')
    global client
    start_time = 0
    duration = 0
    mqtt_id = get_mqtt_id()

    topic_configure = 'devices/' + mqtt_id + '/configure'  # Should subscribe to
    topic_ping = 'devices/' + mqtt_id + '/ping'  # Should publish to
    topic_readings = 'devices/' + mqtt_id + '/data/readings'  # Should publish to
    topic_irrigations = 'devices/' + mqtt_id + '/data/irrigations'  # Should publish to
    print('After NO topics')
    print(gc.mem_free())
    print('---------')
    client = connect(normal_operation_sub_cb)
    blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker
    gc.collect()
    print('Memory after connect gc collect')
    print(gc.mem_free())
    print('---------')

    client.subscribe(topic_configure)
    print('Subscribed to %s topic' % topic_configure)

    # -------- PING procedure --------
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    ping_dict = {
        "mac-address": mac,
        "uuid": get_uuid()
    }
    try:
        client.publish(topic_ping, json.dumps(ping_dict))
        sleep(5)
        client.check_msg()  # TODO should it be wait_msg
    except OSError:
        restart_and_reconnect()
    print('Memory after NO ping')
    print(gc.mem_free())
    print('---------')
    gc.collect()
    print('Memory after NO ping gc collect')
    print(gc.mem_free())
    print('---------')
    # --------------------------------
    print('Memory in NO')
    print(gc.mem_free())
    print('---------')
    # -------- Component Scan procedure --------
    # ------------------------------------------

    # -------- Send Readings procedure --------
    print('Memory in NO before read sensors import')
    print(gc.mem_free())
    print('---------')
    from main.ReadSensors import return_all_sensors
    print('Memory in NO after read sensors import')
    print(gc.mem_free())
    print('---------')
    gc.collect()
    print('Memory in NO after read sensors import gc collect')
    print(gc.mem_free())
    print('---------')
    try:
        client.publish(topic_readings, json.dumps(return_all_sensors()))
    except OSError:
        restart_and_reconnect()
    print('Memory in NO after read sensors')
    print(gc.mem_free())
    print('---------')
    gc.collect()
    print('Memory in NO after read sensors gc collect')
    print(gc.mem_free())
    print('---------')
    # -----------------------------------------

    # -------- Check Config File procedure --------
    from FileManager import check_file_exists
    if not check_file_exists('config.json'):
        print('Config file does not exist')

        def stop_wait_msg(t):
            print('In stop wait message')
            client.check_msg()
            timer_reset.deinit()
            client.disconnect()
            client.connect(normal_operation_sub_cb)

        from machine import Timer
        try:
            timer_reset = Timer(1)
            timer_reset.init(period=20000, mode=Timer.ONE_SHOT, callback=stop_wait_msg)
            print('Before wait msg from client')
            client.wait_msg()
            timer_reset.deinit()
        except OSError:
            restart_and_reconnect()
    gc.collect()
    # ---------------------------------------------

    # -------- Check Time For Irrigation procedure --------
    from main.FileManager import is_file_empty, get_upcoming_irrigation, get_remaining_time_irrigation
    next_irrigation = None
    if not is_file_empty('config.json'):
        next_irrigation = get_upcoming_irrigation()
        print(next_irrigation)
        start_time = next_irrigation.get('start-time')
        duration = next_irrigation.get('duration')

        remaining_seconds = get_remaining_time_irrigation(start_time)
        print('There are ' + str(remaining_seconds) + ' seconds remaining till next irrigation')
    else:
        return
    gc.collect()
    # -----------------------------------------------------

    # TODO schedule operations should have ID's
    # TODO save schedule operation that has been managed currently
    # TODO Sleep function to wait for the remaining_seconds time
    # TODO Awake
    # TODO Repeat Procedure

    # TODO how will component scan be implemented

    # devices/aaaa/configure
    # {
    #     "wakeup-interval": 10,
    #     "schedule-operation": [
    #         {
    #             "id": 1,
    #             "start-time": "2022-03-27 19:45:00",
    #             "duration": 10
    #         },
    #         {
    #             "id": 2,
    #             "start-time": "2022-03-27 12:00:00",
    #             "duration": 20
    #         }
    #     ]
    # }

def restart_and_reconnect():
    print('MQTT Failed. Reconnecting...')
    sleep(2)
    machine.reset()
