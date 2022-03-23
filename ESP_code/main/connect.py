try:
    import usocket as socket
except:
    import socket

import network
from machine import Timer
from Blink import blink
import gc


def is_wifi_connected():
    station = network.WLAN(network.STA_IF)
    return station.active()


def is_ap_connected():
    ap = network.WLAN(network.AP_IF)
    return ap.active()


def deactivate_connections():
    station = network.WLAN(network.STA_IF)
    ap = network.WLAN(network.AP_IF)
    station.active(False)
    ap.active(False)


def retry_wifi_connect(station, timer):
    if retry_wifi_connect.reset_counter >= 3:
        print('Too many unsuccessful attempts. Submit data again!')
        import os
        os.remove('passwd.txt')
        timer.deinit()
        gc.collect()
        connect()
    else:
        retry_wifi_connect.reset_counter += 1


retry_wifi_connect.reset_counter = 0

ssid = None
password = None

def connect():
    deactivate_connections()
    global password, ssid
    print('Start connection process')

    from FileManager import get_ssid, get_password, get_uuid
    ssid = get_ssid()
    password = get_password()
    if ssid is not None and password is not None:
        print('Entering connect wifi mode...')
        print('Read values are ssid: ' + repr(str(ssid)) + ' and password: ' + repr(str(password)))

        blink(0.5, 3)  # Blinking 3   times fast - Device is in connect mode

        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(ssid, password)

        timer_reset = Timer(1)
        timer_reset.init(period=2000, mode=Timer.PERIODIC, callback=retry_wifi_connect(station, timer_reset))
        while not station.isconnected():
            pass

        print('Connection successful')
        print(station.ifconfig())
        gc.collect()
        return

    else:
        print('Entering connect AP mode...')
        ssid = 'MicroPython-AP'
        password = 'MyPocketParadise'

        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=ssid, password=password)

        blink(0.5, 3)  # Blinking 3   times fast - Device is in connect mode

        while not ap.active():
            pass

        print('Connection successful')
        print(ap.ifconfig())
        gc.collect()
        return
