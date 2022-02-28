from pocketparadise import db
from pocketparadise import Base
from pocketparadise import app
from pocketparadise.functinalities.mqtt_subscribe import connect_mqtt, subscribe
from pocketparadise.functinalities.forecast import get_weather_forecast

from flask import render_template

CITY_NAME = 'Sofia'
# COUNTRY_NAME = 'Bulgaria'


@app.route('/')
def hello_world():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


@app.route('/forecast')
def forecast():
    result = get_weather_forecast(CITY_NAME)
    return render_template('test1.html', forecast=result)


if __name__ == '__main__':
    # db.create_all()
    Base.metadata.create_all(db)
    app.run()
