try:
    import usocket as socket
except:
    import socket

import network
from machine import Timer
from Blink import blink
import gc


def is_wifi_enabled():  # TODO check if works
    station = network.WLAN(network.STA_IF)
    return station.active() if station is not None else False


def is_wifi_connected():
    print('in is wifi connected')
    station = network.WLAN(network.STA_IF)
    print(station.isconnected() if station is not None else False)
    return station.isconnected() if station is not None else False


def is_ap_enabled():  # TODO check if works
    ap = network.WLAN(network.AP_IF)
    return ap.active() if ap is not None else False


def deactivate_connections():
    station = network.WLAN(network.STA_IF)
    ap = network.WLAN(network.AP_IF)
    station.active(False)
    ap.active(False)


reset_counter = 0


ssid = None
password = None


def connect():
    deactivate_connections()
    global password, ssid
    print('Start connection process')

    from FileManager import get_ssid, get_password
    ssid = get_ssid()
    password = get_password()
    if ssid is not None and password is not None:
        print('Entering connect wifi mode...')
        print('Read values are ssid: ' + repr(str(ssid)) + ' and password: ' + repr(str(password)))

        blink(0.5, 3)  # Blinking 3   times fast - Device is in connect mode

        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(ssid, password)


        def retry_wifi_connect(timer):  # TODO to be implementing timer for connection timeout
            print('in retry wifi connect')
            global reset_counter
            if not is_wifi_connected():
                print('in retry wifi connect if statement')
                print("reset counter is %d" % reset_counter)
                if reset_counter >= 4:
                    import machine
                    import os

                    print('Too many unsuccessful attempts. Submit data again!')
                    os.remove('passwd.txt')
                    timer.deinit()
                    machine.reset()
                else:
                    print('going to add to reset counter')
                    reset_counter += 1

        timer_reset = Timer(1)  # TODO to be implementing timer for connection timeout
        timer_reset.init(period=20000, mode=Timer.PERIODIC, callback=retry_wifi_connect(timer_reset))


        while not station.isconnected():
            pass
        timer_reset.deinit()
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
