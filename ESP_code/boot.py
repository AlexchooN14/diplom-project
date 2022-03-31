import gc
gc.enable()
gc.collect()

import esp
import sys
esp.osdebug(None)

sys.path.append('/main')
from main.Blink import blink_start
blink_start()
del blink_start

from main.connect import connect, is_ap_enabled, is_wifi_enabled
connect()  # Connect to either AP or Wi-Fi

if is_ap_enabled() and not is_wifi_enabled():  # Check if AP connection
    from main.AccessPoint import create_ap
    create_ap()
from main.FileManager import get_mqtt_id
if get_mqtt_id() is None:
    from main.MQTT import discovery
    from main.Blink import blink_discovery
    blink_discovery()
    discovery()

gc.collect()

from main.MQTT import normal_operation
from main.Blink import blink_normal_operation
blink_normal_operation()
normal_operation()
gc.collect()


