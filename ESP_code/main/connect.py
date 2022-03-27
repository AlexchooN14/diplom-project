try:
    import usocket as socket
except:
    import socket

import network
from machine import Timer, reset
from Blink import blink
import gc


def is_wifi_enabled():
    station = network.WLAN(network.STA_IF)
    return station.active() if station is not None else False


def is_wifi_connected():
    station = network.WLAN(network.STA_IF)
    return station.isconnected() if station is not None else False


def is_ap_enabled():
    ap = network.WLAN(network.AP_IF)
    return ap.active() if ap is not None else False


def deactivate_connections():
    station = network.WLAN(network.STA_IF)
    ap = network.WLAN(network.AP_IF)
    station.active(False)
    ap.active(False)


reset_counter_time = 0

def set_current_time():
    global reset_counter_time
    import ntptime
    import time
    ntptime.host = "1.europe.pool.ntp.org"
    if not reset_counter_time >= 3:
        try:
            print("Local time before synchronization: %s" % str(time.localtime()))
            ntptime.settime()
            print("Local time after synchronization: %s" % str(time.localtime()))
        except:
            print("Error syncing time")
            reset_counter_time += 1
            set_current_time()
    else:
        print('Too many unsuccessful attempts. Could not set time. Reset')
        reset()  # Rebooting ESP


reset_counter_wifi = 0
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

        def retry_wifi_connect(t):
            print('in retry wifi connect')
            global reset_counter_wifi
            if not is_wifi_connected():
                print('in retry wifi connect if statement')
                print("reset counter is %d" % reset_counter_wifi)
                if reset_counter_wifi >= 3:
                    from FileManager import remove_file

                    print('Too many unsuccessful attempts. Submit data again!')
                    remove_file('passwd.json')
                    timer_reset.deinit()
                    reset()  # Rebooting ESP
                else:
                    print('going to add to reset counter')
                    reset_counter_wifi += 1

        timer_reset = Timer(1)
        timer_reset.init(period=20000, mode=Timer.PERIODIC, callback=retry_wifi_connect)

        while not station.isconnected():
            pass
        timer_reset.deinit()
        gc.collect()
        print('Connection successful')
        set_current_time()  # Setting time of ESP to current UTC time
        gc.collect()
        print(station.ifconfig())
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
