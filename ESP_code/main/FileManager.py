
def open_web_page(pagename):
    if pagename == "submit":
        file = open("main/wifi_submit.html", "r")
    elif pagename == "goodbye":
        file = open("main/goodbye.html", "r")
    page = file.read()
    file.close()
    return page


def check_file_exists(filename):
    try:
        open(filename, 'r')
        return True
    except OSError:
        return False


def write_to_file(filename, data):
    file = open(filename, 'w')
    if isinstance(data, dict):
        for key, value in data.items():
            file.write('%s: %s\n' % (key, value))
    elif isinstance(data, list):
        for item in data:
            file.write('%s\n' % item)
    file.close()


def get_ssid():
    if check_file_exists('passwd.txt'):
        file = open('passwd.txt', 'r')
        data = file.read().split('\n')
        for d in data:
            split = d.split(': ')
            if split[0] == 'ssid':
                return split[1]
    else:
        return None


def get_password():
    if check_file_exists('passwd.txt'):
        file = open('passwd.txt', 'r')
        data = file.read().split('\n')
        for d in data:
            split = d.split(': ')
            if split[0] == 'password':
                return split[1]
    else:
        return None


def get_uuid():
    if check_file_exists('passwd.txt'):
        file = open('passwd.txt', 'r')
        data = file.read().split('\n')
        for d in data:
            split = d.split(': ')
            if split[0] == 'uuid':
                return split[1]
    else:
        return None
