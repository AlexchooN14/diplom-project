import socket
import time
import gc
import machine
from Blink import blink

ssid = None
password = None
uuid = None


def web_page(pagename):
    if pagename == "submit":
        file = open("main/wifi_submit.html", "r")
    elif pagename == "goodbye":
        file = open("main/goodbye.html", "r")
    page = file.read()
    file.close()
    return page


def create_ap(ap, station):
    print('Creating Access Point...')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    blink(1, 4)  # Blinking 4   times slow - Creating AP socket

    while True:
        gc.collect()
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        blink(0.1, 1)  # Blinking 1   time  fast  - Got connection to AP
        request = conn.recv(1024)
        request = request.decode('utf-8')
        request = request[:-4]

        is_get, chunks = request.split('\r\n', 1)
        chunks = chunks.split('\r\n')  # Here is the received data
        headers = {}  # Dictionary for where it will be stored

        response = None
        exit_flag = False
        route = None

        for header in chunks:
            curr = header.split(': ')
            headers[curr[0]] = curr[1]

        gc.collect()

        if headers:  # if dict is present - request was received
            if is_get.startswith('GET'):
                print('A GET request received')
            print('is_get: ' + str(is_get.find('/?ssid')))
            if is_get.find('/?ssid') < 0:
                if headers.get('Referer'):
                    route = headers.get('Referer')
                    print('route is: ' + str(route))  # Get requested route

                if route == 'http://192.168.4.1/' or route is None:
                    response = web_page("submit")
                    route = None
                    gc.collect()

            else:
                print('We have submitted form data')
                auth_data = (is_get.split('?')[1]).split('&')
                global ssid
                ssid = auth_data[0].split('=')[1]
                global password
                password = auth_data[1].split('=')[1]
                global uuid
                uuid = auth_data[2].split('=')[1]
                uuid = uuid.split(' ')[0]
                print('ssid: ' + ssid + ' pass: ' + password + ' uuid: ' + uuid)
                f = open('passwd.txt', 'w')
                f.write(ssid + '\n')
                f.write(password + '\n')
                f.write(uuid)
                f.close()
                gc.collect()
                response = web_page("goodbye")
                exit_flag = True

        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(response)
        time.sleep(4)
        conn.close()
        if exit_flag:
            machine.reset()
