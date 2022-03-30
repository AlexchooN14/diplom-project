import json


def open_web_page(pagename):
    if pagename == "submit":
        file = open("main/wifi_submit.html", "r")
    elif pagename == "goodbye":
        file = open("main/goodbye.html", "r")
    page = file.read()
    file.close()
    return page


def is_file_empty(filename):
    import os
    return True if os.stat(filename)[6] == 0 else False


def check_file_exists(filename):
    try:
        open(filename, 'r').close()
        return True
    except OSError:
        return False


def write_to_file(filename, data):
    if not check_file_exists(filename):
        open(filename, 'w').close()
    if isinstance(data, dict):
        if is_file_empty(filename):
            with open(filename, 'w') as file:
                json.dump(data, file)
                file.close()
        else:
            print('File to which I am writing is not empty')
            with open(filename, 'r') as file:
                dictionary = json.load(file)
                dictionary.update(data)
                file.close()
            with open(filename, 'w') as file:
                json.dump(dictionary, file)
                file.close()
    else:
        with open(filename, 'a') as file:
            file.write(data)
            file.close()


def remove_file(filename):
    import os
    os.remove(filename)


def get_ssid():
    if check_file_exists('passwd.json'):
        with open('passwd.json', 'r') as file:
            dictionary = json.load(file)
            file.close()
            return dictionary.get('ssid')


def get_password():
    if check_file_exists('passwd.json'):
        with open('passwd.json', 'r') as file:
            dictionary = json.load(file)
            file.close()
            return dictionary.get('password')


def get_uuid():
    if check_file_exists('passwd.json'):
        with open('passwd.json', 'r') as file:
            dictionary = json.load(file)
            file.close()
            return dictionary.get('uuid')


def get_mqtt_id():
    if check_file_exists('passwd.json'):
        with open('passwd.json', 'r') as file:
            dictionary = json.load(file)
            file.close()
            return dictionary.get('mqtt-id')


def get_upcoming_irrigation():
    if check_file_exists('config.json'):
        if not is_file_empty('config.json'):
            with open('config.json', 'r') as file:
                dictionary = json.load(file)
                print('File is: ' + str(dictionary))
                file.close()
                return dictionary['schedule-operation'][0]
    return None

def get_wakeup_interval():
    if check_file_exists('config.json'):
        with open('config.json', 'r') as file:
            dictionary = json.load(file)
            file.close()
            return dictionary['wakeup-interval']


def remove_completed_irrigation():
    if check_file_exists('config.json'):
        if not is_file_empty('config.json'):
            with open('config.json', 'r') as file:
                dictionary = json.load(file)
                file.close()
                try:
                    del dictionary['schedule-operation'][0]
                    if not dictionary.get('schedule-operation'):
                        print('No more schedules or no such key. Deleting config')
                        remove_file('config.json')
                        return
                except:
                    print('No more schedules or no such key. Deleting config')
                    remove_file('config.json')
                    return
            with open('config.json', 'w') as file:
                json.dump(dictionary, file)
                file.close()


def get_string_from_date(string):
    (year, month, mday, hour, minute, second, weekday, yearday) = string
    if hour < 10:
        hour = '0' + str(hour)
    if minute < 10:
        minute = '0' + str(minute)
    if second < 10:
        second = '0' + str(second)
    return '%s-%s-%s %s:%s:%s' % (year, month, mday, hour, minute, second)


def get_remaining_time_irrigation(time_irrigation):
    import time
    time_current = list(time.localtime())
    time_current = time_current[:-2]
    split = time_irrigation.split(' ')
    date_split = split[0].split('-')
    time_split = split[1].split(':')
    irrigation_year = int(date_split[0])
    irrigation_month = int(date_split[1])
    irrigation_day = int(date_split[2])

    irrigation_hour = int(time_split[0])
    irrigation_minute = int(time_split[1])
    irrigation_second = int(time_split[2])

    time_irrigation = [irrigation_year, irrigation_month, irrigation_day, irrigation_hour, irrigation_minute, irrigation_second]
    if time_current < time_irrigation:
        result = []
        for current, irrigation in zip(time_current, time_irrigation):
            result.append(irrigation - current)
        sum = (result[0] * 31556926) + (result[1] * 2629743.83) + (result[2] * 86400) + (result[3] * 3600) + (result[4] * 60) + result[5]
        return sum if sum >= 0 else 0
    else:
        return 0
