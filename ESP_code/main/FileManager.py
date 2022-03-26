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
    with open(filename, 'r') as file:
        text = file.read()
        file.close()
    return False if text else True


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
        with open('config.json', 'r') as file:
            dictionary = json.load(file)
            file.close()
            # return dictionary.get('mqtt-id')
            # TODO get by the diagram I created
