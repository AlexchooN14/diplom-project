import gc
gc.enable()
gc.collect()

import esp
import sys
esp.osdebug(None)

sys.path.append('/main')

from main.connect import connect, is_ap_enabled, is_wifi_enabled
connect()  # Connect to either AP or to Wi-Fi

print('ap enabled? ' + str(is_ap_enabled()))
print('wifi enabled? ' + str(is_wifi_enabled()))

if is_ap_enabled() and not is_wifi_enabled():  # Check if AP connection
    from main.AccessPoint import create_ap
    create_ap()
from main.FileManager import get_mqtt_id
if get_mqtt_id() is None:
    from main.MQTT import discovery
    discovery()

gc.collect()

from main.MQTT import normal_operation
normal_operation()
gc.collect()


