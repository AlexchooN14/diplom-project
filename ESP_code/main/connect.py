import gc
from main.Blink import blink_error

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
    from FileManager import get_string_from_date

    ntptime.host = "1.europe.pool.ntp.org"
    if not reset_counter_time >= 3:
        try:
            # print("Local time before synchronization: %s" % str(time.localtime()))
            ntptime.settime()
            print("Current UTC time: %s" % get_string_from_date(time.localtime()))
        except:
            print("Error syncing time.")
            blink_error()
            time.sleep(0.5)
            reset_counter_time += 1
            set_current_time()
    else:
        print('Too many unsuccessful attempts. Could not set time.')
        from machine import reset
        reset()  # Rebooting ESP
    del ntptime, time
    gc.collect()


reset_counter_wifi = 0

def connect():
    import network
    from FileManager import get_ssid, get_password
    deactivate_connections()
    ssid = get_ssid()
    password = get_password()

    if ssid is not None and password is not None:
        from machine import Timer
        from main.Blink import blink_connect_wifi

        print('Connecting to Wi-Fi...')
        print('Read values are ssid: ' + repr(str(ssid)) + ' and password: ' + repr(str(password)))
        blink_connect_wifi()
        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(ssid, password)

        def retry_wifi_connect(t):
            global reset_counter_wifi
            if not is_wifi_connected():
                blink_error()
                if reset_counter_wifi >= 3:
                    from FileManager import remove_file
                    from machine import reset
                    from main.Blink import blink_wrong_credentials
                    blink_wrong_credentials()
                    print('Too many unsuccessful attempts. Submit Wi-Fi data again!')
                    remove_file('passwd.json')
                    timer_reset.deinit()
                    reset()  # Rebooting ESP
                else:
                    reset_counter_wifi += 1

        timer_reset = Timer(1)
        timer_reset.init(period=20000, mode=Timer.PERIODIC, callback=retry_wifi_connect)
        while not station.isconnected():
            pass
        timer_reset.deinit()
        gc.collect()
        print('Connection to Wi-Fi successful.')
        set_current_time()  # Setting time of ESP to current UTC time
        gc.collect()
        print(station.ifconfig())
        del Timer, station, timer_reset
        gc.collect()

    else:
        print('Connecting in AP mode...')
        ssid = 'MicroPython-AP'
        password = 'MyPocketParadise'

        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=ssid, password=password)

        while not ap.active():
            pass

        print('Connection successful.')
        print(ap.ifconfig())
        del ap
        gc.collect()

    del network, ssid, password, get_ssid, get_password
    gc.collect()
