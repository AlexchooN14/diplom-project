from pocketparadise import app

with app.app_context():
    from pocketparadise.functionalities.MQTT import run
    run()

if __name__ == '__main__':
    app.run(debug=True)

