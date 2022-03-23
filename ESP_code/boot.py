import esp
import gc
import sys
esp.osdebug(None)
gc.collect()

sys.path.append('/main')

from main.connect import connect, is_ap_connected, is_wifi_connected


connect()  # Connect to either AP or to Wi-Fi
gc.collect()
print('ap enabled? ' + is_ap_connected())
print('wifi enabled? ' + is_wifi_connected())

if is_ap_connected() and not is_wifi_connected():  # Check if AP connection
    from main.AccessPoint import create_ap
    create_ap()

from main.FileManager import check_file_exists
if not check_file_exists('config.txt'):
    from main.MQTT import discovery
    discovery()
else:
    # from main.MQTT import normal_operation
    pass


