import ubinascii
from machine import unique_id
import network
from time import sleep
import gc
import json
from Blink import blink

gc.collect()

mqtt_server = '192.168.1.47'
username = 'sasho'
password = 'A1403lex'
client_id = ubinascii.hexlify(unique_id())
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
client = None

del ubinascii, unique_id, network


connect_reset_counter = 0
message_checker_bool = False
message_checker_sleep = 0

def start_message_checker():
    import _thread
    def message_checker():
        global message_checker_sleep
        while message_checker_bool:
            if message_checker_sleep != 0:
                sleep(message_checker_sleep)
                message_checker_sleep = 0
            client.check_msg()
            print('Message checker')
            sleep(1)
    _thread.start_new_thread(message_checker, ())

def connect(callback_function):
    from umqttsimple import MQTTClient
    global client, client_id, mqtt_server, username, password, connect_reset_counter, message_checker_bool

    if not connect_reset_counter >= 3:
        try:
            client = MQTTClient(client_id, mqtt_server, 1883, username, password)
            del MQTTClient
            client.set_callback(callback_function)
            client.connect()
            message_checker_bool = True
            print('Connected to %s MQTT broker' % mqtt_server)
            start_message_checker()  # Start thread for message checking
            gc.collect()
            return client
        except OSError:
            connect_reset_counter += 1
            message_checker_bool = False
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
        global message_checker_sleep
        message_checker_sleep = 4
        print('ESP received mqtt id message')
        print(type(msg))
        msg = str(msg.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        print(type(dictionary))
        print(dictionary)
        write_to_file('passwd.json', dictionary)
        restart_and_reconnect()


def discovery():
    global client, message_checker_bool, message_checker_sleep
    topic_sub = 'discover/response'
    topic_pub = 'discover/request'

    client = connect(discovery_sub_cb)
    blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker
    gc.collect()
    message_checker_sleep = 2
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
        while get_mqtt_id() is None:
            sleep(1)
            pass
    except OSError:
        restart_and_reconnect()
    del get_uuid, get_mqtt_id
    message_checker_bool = False
    client.disconnect()
    gc.collect()


def normal_operation_sub_cb(topic, msg):
    from FileManager import get_mqtt_id
    blink(0.5, 1, True)  # Pulsing  2   times fast  - MQTT message
    mqtt_id = get_mqtt_id()
    if topic.decode('utf-8') == 'devices/' + mqtt_id + '/configure':
        global message_checker_sleep
        from FileManager import write_to_file
        message_checker_sleep = 4
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
    from machine import Timer
    from ReadSensors import return_all_sensors
    global client, message_checker_bool, message_checker_sleep
    start_time = 0
    duration = 0
    mqtt_id = get_mqtt_id()
    uuid = get_uuid()
    del get_mqtt_id, get_uuid

    topic_configure = 'devices/' + mqtt_id + '/configure'  # Should subscribe to
    topic_ping = 'devices/' + mqtt_id + '/ping'  # Should publish to
    topic_readings = 'devices/' + mqtt_id + '/data/readings'  # Should publish to
    topic_irrigations = 'devices/' + mqtt_id + '/data/irrigations'  # Should publish to

    client = connect(normal_operation_sub_cb)
    blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker
    message_checker_sleep = 2
    client.subscribe(topic_configure)
    print('Subscribed to %s topic' % topic_configure)
    gc.collect()

    # -------- PING procedure --------
    try:
        client.publish(topic_ping, json.dumps({"mac-address": mac, "uuid": uuid}))
    except OSError:
        restart_and_reconnect()
    gc.collect()
    # --------------------------------

    # -------- Send Readings procedure --------
    try:
        client.publish(topic_readings, json.dumps(return_all_sensors()), qos=1)
    except:
        restart_and_reconnect()
    gc.collect()
    # -----------------------------------------

    # -------- Check Config File procedure --------
    from FileManager import check_file_exists, is_file_empty
    sleep_flag = False
    if not check_file_exists('config.json') or is_file_empty('config.json'):
        print('Config file does not exist')

        def stop_wait_msg(t):
            print('ESP did not receive mqtt id for 20s. Going to sleep...')
            timer_reset.deinit()
            nonlocal sleep_flag
            global message_checker_bool
            sleep_flag = True
            message_checker_bool = False

        try:
            timer_reset = Timer(1)
            timer_reset.init(period=20000, mode=Timer.ONE_SHOT, callback=stop_wait_msg)
            # print('Before wait msg from client')
            print('Before while loop for config checker')
            while not check_file_exists('config.json') or is_file_empty('config.json'):
                if sleep_flag:
                    break
            timer_reset.deinit()
        except OSError:
            restart_and_reconnect()
    gc.collect()
    # ---------------------------------------------

    # -------- Check Time For Irrigation procedure --------
    from FileManager import get_upcoming_irrigation, get_remaining_time_irrigation, get_wakeup_interval
    from machine import deepsleep
    from time import sleep
    # next_irrigation = None
    if check_file_exists('config.json') and not is_file_empty('config.json'):
        from time import localtime

        next_irrigation = get_upcoming_irrigation()
        print(next_irrigation)

        start_time = next_irrigation.get('start-time')
        duration = next_irrigation.get('duration')
        wakeup_interval = get_wakeup_interval()
        remaining_seconds = get_remaining_time_irrigation(start_time)

        print('Start time is ' + str(start_time))
        print('Current time is ' + str(localtime()))
        print('There are ' + str(remaining_seconds) + ' seconds remaining till next irrigation')
        if remaining_seconds > 0:
            if remaining_seconds < wakeup_interval:
                # sleep for remaining seconds
                print('Im awake, but Im going to sleep for ' + str(remaining_seconds) + ' seconds')
                message_checker_bool = False
                sleep(5)
                gc.collect()
                deepsleep(int(remaining_seconds) * 1000)
            else:
                # sleep for wakeup_interval seconds
                print('Im awake, but Im going to sleep for ' + str(wakeup_interval) + ' wakeup interval')
                message_checker_bool = False
                sleep(5)
                gc.collect()
                deepsleep(int(wakeup_interval) * 1000)
        else:
            stop_irrigation_flag = False

            def get_sensors_during_irrigation(t):
                nonlocal stop_irrigation_flag, duration
                duration -= wakeup_interval
                client.publish(topic_irrigations, json.dumps(return_all_sensors()))
                if duration < wakeup_interval:
                    if duration <= 0:
                        timer_reset.deinit()
                        stop_irrigation_flag = True
                    else:
                        timer_reset.deinit()
                        timer_reset.init(period=duration*1000, mode=Timer.PERIODIC, callback=stop_irrigation)
            def stop_irrigation(t):
                nonlocal stop_irrigation_flag, duration
                duration = 0
                timer_reset.deinit()
                stop_irrigation_flag = True

            message_checker_bool = False
            from machine import Pin
            relay = Pin(18, Pin.OUT)  # Relay Pin for water pump
            print('Initializing Relay Pin')
            timer_reset = Timer(1)
            if duration > wakeup_interval:
                print('Timer with wakeup interval')
                timer_reset.init(period=wakeup_interval*1000, mode=Timer.PERIODIC, callback=get_sensors_during_irrigation)
            else:
                timer_reset.deinit()
                print('Timer with duration period')
                timer_reset.init(period=duration*1000, mode=Timer.PERIODIC, callback=stop_irrigation)

            from FileManager import get_string_from_date
            irrigation_dictionary = {
                'last-irrigation': {
                    'duration': duration,
                    'start-time': get_string_from_date(localtime()),
                    'working-actuator': 1
                }
            }
            # Start irrigation
            print('Relay On')
            relay.off()
            gc.collect()
            while not stop_irrigation_flag:
                sleep(1)
                pass
            relay.on()
            print('Relay Off')
            # Remove completed irrigation
            from FileManager import remove_completed_irrigation
            print('Removing completed irrigation...')
            remove_completed_irrigation()
            # Start thread for message checking again
            message_checker_bool = True
            start_message_checker()

            # Send sensor data again
            print('Publish last sensors after irrigation')
            client.publish(topic_readings, json.dumps(return_all_sensors()), qos=1)
            print('Publish irrigation data')
            client.publish(topic_irrigations, json.dumps(irrigation_dictionary))
            gc.collect()
            print('Going to sleep after irrigation with wakeup_interval: ' + str(wakeup_interval))
            message_checker_bool = False
            sleep(5)
            deepsleep(int(wakeup_interval)*1000)
    else:
        # Go to sleep for default time
        print('Im awake, but Im going to sleep for some time. No config received')
        sleep(5)
        gc.collect()
        deepsleep(10000)
    gc.collect()


def restart_and_reconnect():
    from machine import reset
    global message_checker_bool
    print('MQTT Reconnecting...')
    message_checker_bool = False
    sleep(2)
    reset()
