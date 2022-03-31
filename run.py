from pocketparadise import app
import threading
from pocketparadise.functionalities.MQTT import run

with app.app_context():
    thread = threading.Thread(target=run)
    thread.start()


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

