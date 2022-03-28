import ubinascii
from machine import unique_id
import network
from time import sleep
import gc
import json
from Blink import blink

gc.collect()

mqtt_server = '192.168.1.7'
username = 'sasho'
password = 'A1403lex'
client_id = ubinascii.hexlify(unique_id())
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
client = None

del ubinascii, unique_id, network


connect_reset_counter = 0

def connect(callback_function):
    from umqttsimple import MQTTClient
    global client, client_id, mqtt_server, username, password, connect_reset_counter

    import _thread
    def message_checker():
        while client.get_connected():
            client.check_msg()
            print('Message checker')
            sleep(1)

    if not connect_reset_counter >= 3:
        try:
            client = MQTTClient(client_id, mqtt_server, 1883, username, password)
            del MQTTClient
            client.set_callback(callback_function)
            client.connect()
            print('Connected to %s MQTT broker' % mqtt_server)
            _thread.start_new_thread(message_checker, ())
            gc.collect()
            return client
        except OSError:
            connect_reset_counter += 1
            client.disconnect()
            client.connect(callback_function)
    else:
        print('Too many unsuccessful attempts. Could not connect to broker')
        restart_and_reconnect()


def discovery_sub_cb(topic, msg):
    from FileManager import write_to_file
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
    from FileManager import get_uuid, get_mqtt_id
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
        # sleep(5)
        # client.wait_msg()
        while get_mqtt_id() is None:
            pass
    except OSError:
        restart_and_reconnect()
    del get_uuid, get_mqtt_id
    gc.collect()


def normal_operation_sub_cb(topic, msg):
    from FileManager import get_mqtt_id
    blink(0.5, 1, True)  # Pulsing  2   times fast  - MQTT message
    mqtt_id = get_mqtt_id()
    if topic.decode('utf-8') == 'devices/' + mqtt_id + '/configure':
        from FileManager import write_to_file
        print('ESP received configuration message')
        print(type(msg))
        msg = str(msg.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        print(type(dictionary))
        print(dictionary)
        write_to_file('config.json', dictionary)
        del write_to_file
    del get_mqtt_id
    gc.collect()


def normal_operation():
    from FileManager import get_mqtt_id, get_uuid
    global client
    print('Start of NO')
    print(gc.mem_free())
    print('---------')
    start_time = 0
    duration = 0
    mqtt_id = get_mqtt_id()
    uuid = get_uuid()
    del get_mqtt_id, get_uuid

    topic_configure = 'devices/' + mqtt_id + '/configure'  # Should subscribe to
    topic_ping = 'devices/' + mqtt_id + '/ping'  # Should publish to
    topic_readings = 'devices/' + mqtt_id + '/data/readings'  # Should publish to
    topic_irrigations = 'devices/' + mqtt_id + '/data/irrigations'  # Should publish to
    print('After NO topics')
    print(gc.mem_free())
    print('---------')
    client = connect(normal_operation_sub_cb)
    blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker

    client.subscribe(topic_configure)
    print('Subscribed to %s topic' % topic_configure)
    # client.check_msg()

    # -------- PING procedure --------
    try:
        client.publish(topic_ping, json.dumps({"mac-address": mac, "uuid": uuid}))
    except OSError:
        restart_and_reconnect()
    # --------------------------------

    # -------- Send Readings procedure --------
    from ReadSensors import return_all_sensors
    try:
        client.publish(topic_readings, json.dumps(return_all_sensors()))
    except OSError:
        restart_and_reconnect()
    gc.collect()
    # -----------------------------------------

    # -------- Check Config File procedure --------
    from FileManager import check_file_exists, is_file_empty
    sleep_flag = False
    if not check_file_exists('config.json') or is_file_empty('config.json'):
        print('Config file does not exist')

        def stop_wait_msg(t):
            print('ESP did not receive config for 20s. Going to sleep...')  # TODO implement
            # client.stop_wait_msg()
            timer_reset.deinit()
            nonlocal sleep_flag
            sleep_flag = True

        from machine import Timer
        try:
            timer_reset = Timer(1)
            timer_reset.init(period=20000, mode=Timer.ONE_SHOT, callback=stop_wait_msg)
            # print('Before wait msg from client')
            print('Before while loop for config checker')
            while not check_file_exists('config.json') or is_file_empty('config.json'):
                if sleep_flag:
                    break
                pass
            timer_reset.deinit()
        except OSError:
            restart_and_reconnect()
    gc.collect()
    # ---------------------------------------------

    # -------- Check Time For Irrigation procedure --------
    from FileManager import is_file_empty, get_upcoming_irrigation, get_remaining_time_irrigation, get_wakeup_interval
    from machine import deepsleep
    from time import sleep
    # next_irrigation = None
    if check_file_exists('config.json') and not is_file_empty('config.json'):
        next_irrigation = get_upcoming_irrigation()
        print(next_irrigation)

        # id_irrigation = next_irrigation.get('id')  # TODO save schedule operation that has been managed currently
        start_time = next_irrigation.get('start-time')
        duration = next_irrigation.get('duration')

        remaining_seconds = get_remaining_time_irrigation(start_time)
        wakeup_interval = get_wakeup_interval()
        print('Start time is ' + str(start_time))
        from time import localtime
        print('Current time is ' + str(localtime()))
        print('There are ' + str(remaining_seconds) + ' seconds remaining till next irrigation')
        if remaining_seconds > 0:
            if remaining_seconds < wakeup_interval:
                # TODO sleep for remaining seconds
                print('Im awake, but Im going to sleep for ' + str(remaining_seconds) + ' seconds')
                sleep(5)
                deepsleep(remaining_seconds * 1000)
            else:
                # TODO sleep for wakeup_interval seconds
                print('Im awake, but Im going to sleep for ' + str(wakeup_interval) + ' wakeup interval')
                sleep(5)
                deepsleep(wakeup_interval * 1000)
        else:
            stop_irrigation_flag = False
            def get_sensors_during_irrigation(t):
                nonlocal client, duration, wakeup_interval, stop_irrigation_flag
                client.publish(topic_irrigations, json.dumps(return_all_sensors()))
                if duration <= 0:
                    timer_reset.deinit()
                    stop_irrigation_flag = True

            # begin irrigation
            # disconnect client for 2nd thread to not work
            client.disconnect()
            from machine import Pin
            relay = Pin(26, Pin.OUT)  # Realy Pin for water pump
            timer_reset = Timer(1)
            if duration > wakeup_interval:
                duration -= wakeup_interval
                timer_reset.init(period=wakeup_interval*1000, mode=Timer.PERIODIC, callback=get_sensors_during_irrigation)
            else:
                timer_reset.init(period=duration*1000, mode=Timer.PERIODIC, callback=get_sensors_during_irrigation)
                duration = 0
            relay.on()
            while not stop_irrigation_flag:
                pass
            relay.off()
            # Remove done irrigation
            from FileManager import remove_completed_irrigation
            remove_completed_irrigation()
            deepsleep(wakeup_interval)
    else:
        # TODO go to sleep for default time
        print('Im awake, but Im going to sleep for some time. No config received')
        sleep(5)
        deepsleep(10000)
    gc.collect()

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
    from machine import reset
    print('MQTT Failed. Reconnecting...')
    client.set_connected(False)
    sleep(2)
    reset()
