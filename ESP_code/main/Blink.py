from machine import Pin
import time
import gc

# start - blink  3  LEDs  fast 1  time (on123, 0.3s, off123) | 3 LED
# any error - blink  3  LEDs  fast  2  times (on123, 0.3s, off123, 0.3, on123, 0.3s, off123) | 3 LED
# wrong wifi credentials - flashing 1st LED fast | 1 LED
# sleep - 1,2,3 and 3,2,1 and 1,2,3 and 3,2,1

# connect wifi - 1+1 blink fast-medium (on, 0.4s, off, 1s, on, 0.4s, off) | 1 LED
# AP mode - 1+1 blink mid-slow (on, 0.7s, off, 0.7s, on, 0.7s, off, 0.7s) | 1 LED

# connect MQTT broker - 2 medium and 2+2 fast (on12, 1s, off12, 1s, on12, 0.3s, off12, 0.3, on12, 0.3s, off12) | 2 LED
# send msg MQTT - 2 fast blink (on12, 0.3s, off12) | 2 LED
# receive msg MQTT - 2+2 fast blink (on12, 0.3s, off12, 0.3s, on12, 0.3s, off12) | 2 LED

# discovery start - 1,2,3,2,pause,1,2,3,2 fast change (1, 0.2s, 2, 0.2s, 1, 0.4s, 3, 0.2s, 2, 0.2s, 3, 0.8s)x2 | 3 LED
# normal operation start - 1,2,3 med and 3 fast (1, 0.3s, 2, 0.3s, 3, 0.3s, off123, 0.4s, on123, 0.3s, off123) | 3 LED
# begin irrigation - 1, 2, 3 mid-slow (1, 0.6s, 2, 0.6s, 3, 0.6s, off1, 0.3, off2, 0.3, off3) | 3 LED
# stop irrigation - 3, 2, 1 mid-slow (3, 0.6s, 2, 0.6s, 1, 0.6s, off3, 0.3, off2, 0.3, off1) | 3 LED
# check sensors - 1 and 3 together slow, 2 fast (on13, 0.9, on2, 0.2, off2) | 3 LED

LED1 = Pin(25, Pin.OUT)
LED2 = Pin(26, Pin.OUT)
LED3 = Pin(27, Pin.OUT)
LEDS = [LED1, LED2, LED3]

def blink(interval, sleep_time, repetitions, led_count, gradual_start=False, gradual_stop=False, reverse=False):
    for i in range(repetitions):
        for j in range(0 if not reverse else led_count-1, led_count if not reverse else -1, 1 if not reverse else -1):
            LEDS[j].value(1)
            if gradual_start:
                time.sleep(interval)
        if not gradual_start:
            time.sleep(interval)

        if not gradual_stop:
            for j in range(led_count):
                LEDS[j].value(0)
            time.sleep(sleep_time)
        else:
            for j in range(0 if not reverse else led_count-1, led_count if not reverse else -1, 1 if not reverse else -1):
                LEDS[j].value(0)
                time.sleep(sleep_time)
        gc.collect()
    return

def blink_start():
    blink(0.3, 0.3, 1, 3)
def blink_error():
    blink(0.4, 0.4, 2, 3)
def blink_connect_wifi():
    blink(0.4, 1, 2, 1)
def blink_create_ap():
    blink(0.8, 1, 2, 1)
def blink_wrong_credentials():
    blink(0.1, 0.1, 5, 1)
def blink_connect_broker():
    blink(1, 1, 1, 2)
    blink(0.3, 0.3, 2, 2)
def blink_mqtt_publish():
    blink(0.3, 0.3, 1, 2)
def blink_mqtt_receive():
    blink(0.3, 0.3, 2, 2)
def blink_discovery():
    for i in range(2):
        LED1.value(1)
        time.sleep(0.1)
        LED1.value(0)
        LED2.value(1)
        time.sleep(0.1)
        LED2.value(0)
        time.sleep(0.4)

        LED3.value(1)
        time.sleep(0.1)
        LED3.value(0)
        LED2.value(1)
        time.sleep(0.1)
        LED2.value(0)
        time.sleep(0.8)
    gc.collect()
def blink_normal_operation():
    blink(0.3, 0.4, 1, 3, True)
    blink(0.2, 0.2, 1, 3)
def blink_begin_irrigation():
    blink(0.6, 0.3, 1, 3, True, True)
def blink_stop_irrigation():
    blink(0.6, 0.3, 1, 3, True, True, True)
def blink_check_sensors():
    LED1.value(1)
    LED3.value(1)
    time.sleep(1)
    LED2.value(1)
    time.sleep(0.3)
    LED1.value(0)
    LED2.value(0)
    LED3.value(0)
    time.sleep(0.3)
    gc.collect()
def blink_sleep():
    blink(0.1, 0.1, 1, 3, True, True)
    blink(0.1, 0.1, 1, 3, True, True, True)
    blink(0.1, 0.1, 1, 3, True, True)
    blink(0.1, 0.1, 1, 3, True, True, True)
    gc.collect()
