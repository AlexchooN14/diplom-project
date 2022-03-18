try:
    import usocket as socket
except:
    import socket

import network
import machine
from Blink import blink
import gc


def check_file_exists():
    try:
        open('passwd.txt', 'r')
        return True
    except OSError:
        return False


ssid = None
password = None


def connect():
    global password, ssid
    print('Start')
    if check_file_exists():
        print('File exists')
        f = open('passwd.txt', 'r')
        ssid = (f.readline())[:-1]
        password = f.readline()[:-1]
        print('Read values are ssid: ' + repr(str(ssid)) + ' and password: ' + repr(str(password)))
        f.close()
        if ssid and password:
            print('entering connect wifi mode')

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
    print('before second if')
    if ssid is None and password is None:
        print('in ap')
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
    machine.reset()
