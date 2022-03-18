from machine import Pin
import time
import gc

# Blinking 3   times fast  - Device is in connect mode
# Blinking 4   times slow - Creating AP socket
# Blinking 1   time  fast  - Got connection to AP
# Pulsing  2+2 times fast  - Connected to MQTT broker
# Pulsing  2   times fast  - MQTT message


def blink(duration, repetitions, pulse=False):
    led = Pin(2, Pin.OUT)
    if pulse:
        for i in range(repetitions):
            led.value(0)
            time.sleep(0.1)
            led.value(1)
            time.sleep(0.1)
            led.value(0)
            time.sleep(0.1)
            led.value(1)
            time.sleep(duration)
        gc.collect()
        return
    else:
        for i in range(repetitions):
            led.value(0)
            time.sleep(duration)
            led.value(1)
            time.sleep(duration)
        gc.collect()
        return
