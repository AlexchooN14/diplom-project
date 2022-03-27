import esp
import gc
import sys
esp.osdebug(None)
gc.enable()
gc.collect()

sys.path.append('/main')

from main.connect import connect, is_ap_enabled, is_wifi_enabled

print('Initial Memory')
print(gc.mem_free())
print('---------')
connect()  # Connect to either AP or to Wi-Fi
print('Memory After connect')
print(gc.mem_free())
print('---------')
gc.collect()
print('Memory After connect gc collect')
print(gc.mem_free())
print('---------')
print('ap enabled? ' + str(is_ap_enabled()))
print('wifi enabled? ' + str(is_wifi_enabled()))

if is_ap_enabled() and not is_wifi_enabled():  # Check if AP connection
    from main.AccessPoint import create_ap
    create_ap()
print('Memory After AP')
print(gc.mem_free())
print('---------')
from main.FileManager import get_mqtt_id
if get_mqtt_id() is None:
    from main.MQTT import discovery
    discovery()
gc.collect()
print('Memory')
print(gc.mem_free())
print('---------')
from main.MQTT import normal_operation
normal_operation()
gc.collect()


