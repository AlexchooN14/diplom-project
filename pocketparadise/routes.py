from pocketparadise import app, db
from pocketparadise.functinalities.mqtt_subscribe import connect_mqtt, subscribe
from pocketparadise.functinalities.forecast import get_weather_forecast
from pocketparadise.models import (Country, City, User, WateringAlgorithm,
                                   Zone, Plant, Device)

from flask import render_template, url_for, flash, redirect, request, abort
CITY_NAME = 'Sofia'


def setup_cities():
    bulgaria = Country(name='Bulgaria', continent='Europe')
    sofia = City(name='Sofia', country=bulgaria)
    plovdiv = City(name='Plovdiv', country=bulgaria)
    varna = City(name='Varna', country=bulgaria)
    db.session.add(bulgaria)
    db.session.add(sofia)
    db.session.add(plovdiv)
    db.session.add(varna)
    db.session.commit()


@app.route('/')
def home(city):
    setup_cities()
    user = User(first_name='Sasho', last_name='Naumov', email='alexandern003@gmail.com', city=city)


@app.route('/city/add', methods=['POST'])
def add_city():
    if not request.method == 'POST':
        return abort(403)
    data = request.get_json()
    city_name = data['city-name']
    country_name = data['country-name']
    country = Country.query.filter_by(name=country_name).first()
    city = City(name=city_name, country=country)
    db.session.add(city)
    db.session.commit()
    return f'City with name {city_name} added'


@app.route('/country/add', methods=['POST'])
def add_country():
    if not request.method == 'POST':
        return abort(403)
    data = request.get_json()
    country_name = data['country-name']
    country = Country(name=country_name)
    db.session.add(country)
    db.session.commit()
    return f'Country with name {country_name} added'


@app.route('/user/add', methods=['POST'])
def add_user():
    if not request.method == 'POST':
        return abort(403)
    data = request.get_json()
    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    city_name = data['city-name']
    city = City.query.filter_by(name=city_name).first_or_404()
    user = User(first_name=first_name, last_name=last_name, email=email, city=city)
    db.session.add(user)
    db.session.commit()
    return f'User with name {first_name} {last_name} added'


@app.route('/zone/add', methods=['POST'])
def add_zone():
    if not request.method == 'POST':
        return abort(403)
    data = request.get_json()
    name = data['zone-name']
    amount = data['amount']
    user_first_name = data['user-first-name']
    user_last_name = data['user-last-name']
    source_flowrate = data['source-flowrate']
    area_size = data['area-size']
    algorithm_name = data['algorithm-name']
    user = User.query.filter_by(first_name=user_first_name, last_name=user_last_name).first_or_404()
    algorithm = WateringAlgorithm.query.filter_by(name=algorithm_name).first_or_404()

    zone = Zone(name=name, preferred_watering_amount=amount, user=user,
                source_flowrate=source_flowrate, area_size=area_size, algorithm=algorithm)
    db.session.add(zone)
    db.session.commit()
    return f'Zone with name {name} added'


@app.route('/algorithm/add', methods=['POST'])
def add_algorithm():
    if not request.method == 'POST':
        return abort(403)
    data = request.get_json()
    name = data['name']
    method = data['method']
    algorithm = WateringAlgorithm(name=name, irrigation_method=method)
    db.session.add(algorithm)
    db.session.commit()
    return f'Algorithm with name {name} and method {method} added'


@app.route('/plant/add', methods=['POST'])
def add_plant():
    if not request.method == 'POST':
        return abort(403)
    data = request.get_json()
    name = data['name']
    humidity_preference = data['h-preference']
    sunlight_preference = data['l-preference']
    temperature_preference = data['t-preference']
    plant = Plant(name=name, humidity_preference=humidity_preference,
                  sunlight_preference=sunlight_preference, temperature_preference=temperature_preference)
    db.session.add(plant)
    db.session.commit()
    return f'Plant with name {name} added'


@app.route('/device/add', methods=['POST'])
def add_device():
    if not request.method == 'POST':
        return abort(403)
    data = request.get_json()
    name = data['name']
    address = data['address']
    zone_name = data['zone-name']
    actuator= data['actuator-present']
    zone = Zone.query.filter_by(name=zone_name).first_or_404()
    device = Device(name=name, address=address, zone=zone, actuator_present=actuator)
    db.session.add(device)
    db.session.commit()
    return f'Device with name {name} added'


@app.route('/mqtt')
def mqtt():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


@app.route('/forecast')
def forecast():
    result = get_weather_forecast(CITY_NAME)
    return render_template('test1.html', forecast=result)


