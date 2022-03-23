from machine import ADC
import time


soil_moisture_reset_counter = 0


# TODO make a checker for connected pins to sensor or just rely on try/catch
def read_soil_moisture():
    global soil_moisture_reset_counter

    soil_moisture = ADC(0)
    if not soil_moisture_reset_counter >= 3:
        try:
            soil_moisture.read()
        except:
            soil_moisture_reset_counter += 1
            time.sleep(5)
            read_soil_moisture()
    else:
        print('Too many unsuccessful attempts. Check SM sensor connection')
        return


def read_illumination():
    pass


bme_reset_counter = 0


def read_bme_sensor():
    from machine import I2C, Pin
    import bme680
    import gc
    gc.collect()

    global bme_reset_counter
    # ESP8266 - Pin assignment
    i2c = I2C(scl=Pin(5), sda=Pin(4))
    bme = bme680.BME680_I2C(i2c=i2c)

    if not bme_reset_counter >= 3:
        try:
            temp = str(round(bme.temperature, 2)) + ' C'

            hum = str(round(bme.humidity, 2)) + ' %'

            pres = str(round(bme.pressure, 2)) + ' hPa'

            gas = str(round(bme.gas / 1000, 2)) + ' KOhms'

            print('Temperature:', temp)
            print('Humidity:', hum)
            print('Pressure:', pres)
            print('Gas:', gas)
            print('-------')
        except OSError as e:
            print('Failed to read sensor.')
            bme_reset_counter += 1
            time.sleep(5)
            read_bme_sensor()
    else:
        print('Too many unsuccessful attempts. Check AIR sensor connection')
        return
