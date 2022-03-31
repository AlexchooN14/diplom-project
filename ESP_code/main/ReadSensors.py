from machine import ADC, Pin
import gc
import time
from Blink import blink_error
from FileManager import get_string_from_date
from bme680 import BME680_I2C

# A = Pin(13, Pin.OUT)
# B = Pin(12, Pin.OUT)
# C = Pin(14, Pin.OUT)


soil_moisture_reset_counter = 0

def read_soil_moisture():
    global soil_moisture_reset_counter

    sensor_sum = 0
    if not soil_moisture_reset_counter >= 3:
        try:
            # Soil Moisture Sensor is on 2nd analog input of multiplexer - A - 0; B - 1; C - 0
            # A.off()
            # B.on()
            # C.off()

            soil_moisture = ADC(Pin(34))

            for i in range(3):
                sensor_sum += soil_moisture.read()
        except:
            soil_moisture_reset_counter += 1
            time.sleep(5)
            read_soil_moisture()
    else:
        print('Could not read soil moisture. Check SM sensor connection')
        blink_error()
        return None

    dictionary = {
        'sensor-id': 1,
        'sensor-type': 'SM',
        'reading-data': sensor_sum/3,
        'reading-time': get_string_from_date(time.localtime())
    }
    return dictionary


illumination_reset_counter = 0

def read_illumination():
    global illumination_reset_counter

    sensor_sum = 0
    if not illumination_reset_counter >= 3:
        try:
            # Soil Illumination Sensor is on 1st analog input of multiplexer - A - 1; B - 0; C - 0
            # A.on()
            # B.off()
            # C.off()

            illumination = ADC(Pin(32))

            for i in range(3):
                sensor_sum += illumination.read()
        except:
            illumination_reset_counter += 1
            time.sleep(5)
            read_illumination()
    else:
        print('Could not read illumination. Check Illumination sensor connection')
        blink_error()
        return None

    dictionary = {
        'sensor-id': 2,
        'sensor-type': 'AL',
        'reading-data': sensor_sum / 3,
        'reading-time': get_string_from_date(time.localtime())
    }
    return dictionary


bme_reset_counter = 0

def read_bme_sensor():
    from machine import I2C
    gc.collect()
    print('---------')
    global bme_reset_counter
    print('In bme read')
    temp_sum = 0
    hum_sum = 0
    pres_sum = 0

    if not bme_reset_counter >= 3:
        try:
            # i2c = I2C(scl=Pin(5), sda=Pin(4))
            # ESP32 - Pin assignment
            i2c = I2C(1, scl=Pin(22), sda=Pin(21))
            bme = BME680_I2C(i2c=i2c)

            for i in range(3):
                temp_sum += round(bme.temperature, 2)
                hum_sum += round(bme.humidity, 2)
                pres_sum += round(bme.pressure, 2)
                # gas = str(round(bme.gas / 1000, 2)) + ' KOhms'

        except OSError:
            bme_reset_counter += 1
            time.sleep(5)
            read_bme_sensor()
    else:
        print('Could not read BME. Check BME sensor connection')
        blink_error()
        return None

    dictionary = {
        'sensor-id': 3,
        'sensor-type': 'BME',
        'reading-data': {
            'temperature': temp_sum / 3,
            'humidity': hum_sum / 3,
            'pressure': pres_sum / 3
        },
        'reading-time': get_string_from_date(time.localtime())
    }
    return dictionary


def return_all_sensors():
    from main.Blink import blink_check_sensors
    blink_check_sensors()
    sm = read_soil_moisture()
    bme = read_bme_sensor()
    gc.collect()
    illumination = read_illumination()
    return [sm, bme, illumination] if sm and bme and illumination else None
