try:
    import usocket as socket
except:
    import socket

import network
import machine
from Blink import blink
import gc


ssid = None
password = None


def connect():
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
