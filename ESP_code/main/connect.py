import gc


def is_wifi_enabled():
    import network
    station = network.WLAN(network.STA_IF)
    del network
    gc.collect()
    return station.active() if station is not None else False


def is_wifi_connected():
    import network
    station = network.WLAN(network.STA_IF)
    del network
    gc.collect()
    return station.isconnected() if station is not None else False


def is_ap_enabled():
    import network
    ap = network.WLAN(network.AP_IF)
    del network
    gc.collect()
    return ap.active() if ap is not None else False


def deactivate_connections():
    import network
    station = network.WLAN(network.STA_IF)
    ap = network.WLAN(network.AP_IF)
    station.active(False)
    ap.active(False)
    del network, station, ap
    gc.collect()


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
        from machine import reset
        reset()  # Rebooting ESP
    del ntptime, time
    gc.collect()


reset_counter_wifi = 0

def connect():
    import network
    from FileManager import get_ssid, get_password
    from Blink import blink
    deactivate_connections()
    print('Start connection process')
    ssid = get_ssid()
    password = get_password()

    if ssid is not None and password is not None:
        from machine import Timer
        print('Entering connect wifi mode...')
        print('Read values are ssid: ' + repr(str(ssid)) + ' and password: ' + repr(str(password)))

        blink(0.5, 3)  # Blinking 3   times fast - Device is in connect mode
        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(ssid, password)

        def retry_wifi_connect(t):
            global reset_counter_wifi
            print('in retry wifi connect')
            if not is_wifi_connected():
                print('in retry wifi connect if statement')
                print("reset counter is %d" % reset_counter_wifi)
                if reset_counter_wifi >= 3:
                    from FileManager import remove_file
                    from machine import reset
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
        del Timer, station, timer_reset
        gc.collect()

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
        del ap
        gc.collect()

    del network, ssid, password, get_ssid, get_password, blink
    gc.collect()
