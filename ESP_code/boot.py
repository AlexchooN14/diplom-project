import esp
import gc
import time
import sys
import network
esp.osdebug(None)
gc.collect()

sys.path.append('/main')

from main.connect import connect

station = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
station.active(False)
ap.active(False)


connect()  # Connect to either AP or to Wi-Fi
gc.collect()
station = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
print('ap enabled? ' + str(ap.active()))
print('wifi enabled? ' + str(station.active()))
print('config: ' + str(station.ifconfig()))

if ap.active() and not station.active():
    print('in ap if in boot')
    from main.AccessPoint import create_ap
    create_ap(ap, station)

from main.MQTT import last_message, message_interval, client_id, topic_pub, counter, restart_and_reconnect, connect_and_subscribe
from main.Blink import blink

try:
    client = connect_and_subscribe()
    blink(0.5, 2, True)  # Pulsing  2+2 times fast  - Connected to MQTT broker
except OSError as e:
    restart_and_reconnect()

import ubinascii
while True:
    try:
        client.check_msg()
        if (time.time() - last_message) > message_interval:
            mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
            msg = b'Hello, my MAC is %s ' % mac
            client.publish(topic_pub, msg)
            last_message = time.time()
            counter += 1
    except OSError as e:
        restart_and_reconnect()

