import ubinascii
from machine import unique_id
import network
from time import sleep
import gc
import json
from main.Blink import blink_error, blink_sleep

gc.collect()
TEST = False

if TEST:
    mqtt_server = '95.43.222.199'
else:
    mqtt_server = '192.168.1.47'

username = 'sasho'
password = 'A1403lex'
client_id = ubinascii.hexlify(unique_id())
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
client = None
DEFAULT_SLEEPTIME = 10000

del ubinascii, unique_id, network

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
            sleep(0.5)
    _thread.start_new_thread(message_checker, ())

def connect(callback_function):
    from umqttsimple import MQTTClient
    from main.Blink import blink_connect_broker
    global client, client_id, mqtt_server, username, password, message_checker_bool

    for i in range(3):
        try:
            client = MQTTClient(client_id, mqtt_server, 1883, username, password)
            client.set_callback(callback_function)
            client.connect()
            blink_connect_broker()
            message_checker_bool = True
            print('Connected to broker')
            start_message_checker()  # Start thread for message checking
            return client
        except OSError:
            if i == 2:
                message_checker_bool = False
                restart_and_reconnect()
            else:
                continue

    else:
        blink_error()
        print('Too many unsuccessful attempts. Could not connect to broker')
        restart_and_reconnect()
    del MQTTClient

def discovery_sub_cb(topic, msg):
    from FileManager import write_to_file
    from main.Blink import blink_mqtt_receive
    blink_mqtt_receive()
    if topic.decode('utf-8') == 'discover/response':
        global message_checker_sleep
        message_checker_sleep = 4
        msg = str(msg.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        write_to_file('passwd.json', dictionary)
        restart_and_reconnect()


def discovery():
    global client, message_checker_bool, message_checker_sleep

    topic_sub = 'discover/response'
    topic_pub = 'discover/request'

    client = connect(discovery_sub_cb)
    gc.collect()
    message_checker_sleep = 2
    # Subscribe to discover/response
    client.subscribe(topic_sub)

    # Get MAC, UUID of system
    from FileManager import get_uuid, get_mqtt_id
    dictionary = {
        "mac-address": mac,
        "uuid": get_uuid()
    }
    data = json.dumps(dictionary)
    gc.collect()

    # Send them as json to topic discover/request
    print('Sending discover request data')
    for i in range(3):
        try:
            client.publish(topic_pub, data)
            while get_mqtt_id() is None:
                sleep(1)
            break
        except OSError:
            if i == 2:
                blink_error()
                restart_and_reconnect()
            else:
                continue

    del get_uuid, get_mqtt_id
    message_checker_bool = False
    client.disconnect()
    gc.collect()


def normal_operation_sub_cb(topic, msg):
    from FileManager import get_mqtt_id
    from main.Blink import blink_mqtt_receive
    blink_mqtt_receive()
    mqtt_id = get_mqtt_id()
    if topic.decode('utf-8') == 'devices/' + mqtt_id + '/configure':
        global message_checker_sleep
        from FileManager import write_to_file
        message_checker_sleep = 4
        print('Configuration received')
        msg = str(msg.decode("utf-8", "ignore"))
        dictionary = json.loads(msg)  # decode json data
        write_to_file('config.json', dictionary)
        del write_to_file
    del get_mqtt_id
    gc.collect()


def normal_operation():
    from FileManager import get_mqtt_id, get_uuid, check_file_exists
    from machine import Timer
    from ReadSensors import return_all_sensors
    global client, message_checker_bool, message_checker_sleep
    from time import sleep
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
    message_checker_sleep = 2
    client.subscribe(topic_configure)
    gc.collect()

    for i in range(3):
        try:
            # Send ping
            print('Telling App that am awake.')
            client.publish(topic_ping, json.dumps(
                {"mac-address": mac, "uuid": uuid, "config-present": check_file_exists('config.json')}), qos=1)
            break
        except OSError:
            if i == 2:
                blink_error()
                restart_and_reconnect()
            else:
                continue
    gc.collect()
    # --------------------------------

    for i in range(3):
        try:
            client.publish(topic_readings, json.dumps(return_all_sensors()), qos=1)
            break
        except OSError:
            if i == 2:
                blink_error()
                restart_and_reconnect()
            else:
                continue
    gc.collect()
    # -----------------------------------------

    # -------- Check Config File procedure --------
    from FileManager import is_file_empty
    sleep_flag = False
    if not check_file_exists('config.json') or is_file_empty('config.json'):
        print('Config file does not exist')

        def stop_wait_msg(t):
            print('ESP did not receive response for 20s.')
            timer_reset.deinit()
            nonlocal sleep_flag
            global message_checker_bool
            sleep_flag = True
            message_checker_bool = False

        try:
            timer_reset = Timer(1)
            timer_reset.init(period=20000, mode=Timer.ONE_SHOT, callback=stop_wait_msg)
            while not check_file_exists('config.json') or is_file_empty('config.json'):
                if sleep_flag:
                    break
            timer_reset.deinit()
        except OSError:
            blink_error()
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

        print('There are ' + str(remaining_seconds) + ' seconds remaining till next irrigation')
        if remaining_seconds > 0:
            if remaining_seconds < wakeup_interval:
                # sleep for remaining seconds
                print('Im awake, but Im going to sleep for ' + str(remaining_seconds) + ' seconds')
                message_checker_bool = False
                blink_sleep()
                sleep(5)
                gc.collect()
                deepsleep(int(remaining_seconds) * 1000)
            else:
                # sleep for wakeup_interval seconds
                print('Im awake, but Im going to sleep for ' + str(wakeup_interval) + ' wakeup interval')
                message_checker_bool = False
                blink_sleep()
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
            timer_reset = Timer(1)
            if duration > wakeup_interval:
                print('Will wait for wakeup interval')
                timer_reset.init(period=wakeup_interval*1000, mode=Timer.PERIODIC, callback=get_sensors_during_irrigation)
            else:
                timer_reset.deinit()
                print('Will wait for duration period')
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
            from main.Blink import blink_begin_irrigation, blink_stop_irrigation
            blink_begin_irrigation()
            relay.off()
            gc.collect()
            while not stop_irrigation_flag:
                sleep(1)
                pass
            relay.on()
            blink_stop_irrigation()

            # Remove completed irrigation
            from FileManager import remove_completed_irrigation
            print('Removing completed irrigation...')
            remove_completed_irrigation()

            # Start thread for message checking again
            message_checker_bool = True
            start_message_checker()

            # Send sensor data again
            client.publish(topic_readings, json.dumps(return_all_sensors()), qos=1)
            # Send irrigation data
            client.publish(topic_irrigations, json.dumps(irrigation_dictionary))
            gc.collect()
            print('Going to sleep after irrigation with wakeup interval: ' + str(wakeup_interval))
            message_checker_bool = False
            blink_sleep()
            sleep(5)
            deepsleep(int(wakeup_interval)*1000)
    else:
        # Go to sleep for default time
        print('Im awake, but Im going to sleep for some time. No config received.')
        blink_sleep()
        sleep(5)
        gc.collect()
        deepsleep(DEFAULT_SLEEPTIME)
    gc.collect()


def restart_and_reconnect():
    from machine import reset
    global message_checker_bool
    message_checker_bool = False
    sleep(2)
    reset()
