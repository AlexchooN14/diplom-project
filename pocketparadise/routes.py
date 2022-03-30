from flask import Response

from pocketparadise import app, db, bcrypt, mail
from pocketparadise.functionalities.mqtt_connect import connect_mqtt
from pocketparadise.functionalities.mqtt_discovery import discovery_subscribe
from pocketparadise.functionalities.forecast import get_weather_forecast
from pocketparadise.models import (Country, City, User, Zone, Plant, Device, IrrigationData, METHOD, AMOUNT)
from pocketparadise.forms import (RegistrationForm, LoginForm, UpdateAccountForm, ZoneForm)
from flask_login import login_user, current_user, logout_user, login_required

from flask import render_template, url_for, flash, redirect, request, abort, jsonify

def setup_cities():
    france = Country(name='France')
    paris = City(name='Paris', country=france)
    cannes = City(name='Cannes', country=france)
    lion = City(name='Lion', country=france)
    bulgaria = Country(name='Bulgaria')
    sofia = City(name='Sofia', country=bulgaria)
    plovdiv = City(name='Plovdiv', country=bulgaria)
    varna = City(name='Varna', country=bulgaria)
    db.session.add(france)
    db.session.add(bulgaria)
    db.session.commit()
    db.session.add(paris)
    db.session.add(cannes)
    db.session.add(lion)
    db.session.add(sofia)
    db.session.add(plovdiv)
    db.session.add(varna)
    db.session.commit()

@app.route('/countries', methods=['GET', 'POST'])
def add_country():
    if not request.method == 'POST' and not request.method == 'GET':
        return abort(403)
    if request.method == 'POST':
        data = request.get_json()
        country_name = data.get('country-name')
        country = Country.query.filter_by(name=country_name).first()
        if country:
            return Response(f'Country with name {country_name} already exists', 403)
        country = Country(name=country_name)
        db.session.add(country)
        db.session.commit()
        return Response(f'Country with name {country_name} added', 200)
    elif request.method == 'GET':
        countries = Country.query.all()
        country_list = {}
        for country in countries:
            country_list.update({country.id: Country.__repr__(country)})
        return country_list

@app.route('/cities', methods=['GET', 'POST'])
def add_city():
    if not request.method == 'POST' and not request.method == 'GET':
        return abort(403)
    if request.method == 'POST':
        data = request.get_json()
        city_name = data.get('city-name')
        country_name = data.get('country-name')
        country = Country.query.filter_by(name=country_name).first()

        city = City.query.filter_by(name=city_name).first()
        if city:
            return Response(f'City with name {city_name} already exists', 403)
        city = City(name=city_name, country=country)
        db.session.add(city)
        db.session.commit()
        return Response(f'City with name {city_name} added', 200)
    elif request.method == 'GET':
        cities = City.query.all()
        city_list = {}
        for city in cities:
            city_list.update({city.id: City.__repr__(city)})
        return city_list

@app.route('/users', methods=['POST'])
def create_user():
    # setup_cities()
    if not request.method == 'POST':
        return abort(403)
    elif current_user.is_authenticated:
        return Response('You should Log out first...', 404)
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        return Response(f'User with that email already exists', 403)
    password = data.get('password')
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    city_name = data.get('city-name')

    if first_name and last_name and email and password and city_name:
        city = City.query.filter_by(name=city_name).first_or_404()
        user = User(first_name=first_name, last_name=last_name, email=email, password=hashed_password, city=city)
    else:
        return Response('Missing submit data', 400)
    db.session.add(user)
    db.session.commit()
    return Response(f'{first_name}\'s account was created successfully, Log In', 200)

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return Response('Already Logged in', 404)

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    remember = data.get('remember')
    if email and password:
        user = User.query.filter_by(email=email).first_or_404()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember if remember else False)
            return Response('You have successfully logged in! Time to create a zone...', 200)
        else:
            return Response('Wrong credentials.', 401)
    else:
        return Response('Missing submit data.', 400)

@app.route('/logout')
def logout():
    logout_user()
    return Response('You logged out. Bye for now.', 200)

@app.route('/users/<int:user_id>')
@login_required
def user(user_id):
    if not request.method == 'GET':
        return abort(403)
    user = User.query.get_or_404(user_id)
    user_dict = {
        "firstname": user.first_name,
        "lastname": user.last_name,
        "email": user.email,
        "password": user.password,
        "city": user.city.name
    }
    return jsonify(user_dict)


@app.route('/zones', methods=['POST'])
@login_required
def create_zone():
    # name, city, preferred_watering_amount, user, source_flowrate, area_size, irrigation_method, watering_amount
    data = request.get_json()
    name = data.get('name')
    city_name = data.get('city-name')
    city = City.query.filter_by(name=city_name).first_or_404()
    source_flowrate = data.get('source-flowrate')
    area_size = data.get('area-size')
    irrigation_method = data.get('irrigation-method')  # METHOD
    watering_amount = data.get('watering-amount')  # AMOUNT
    print(f'irrigation_method: {irrigation_method}')
    print(f'watering_amount: {watering_amount}')
    method_name = METHOD(irrigation_method).name
    print(type(method_name))
    print(method_name)
    if name and city_name and source_flowrate\
            and area_size and irrigation_method and watering_amount:

        zone = Zone(name=name, city=city, user=current_user, source_flowrate=source_flowrate,
                    area_size=area_size, irrigation_method=irrigation_method,
                    watering_amount=watering_amount)
    else:
        return Response('Missing submit data', 400)
    db.session.add(zone)
    db.session.commit()
    return Response(f'{name} zone created successfully! Try and add a device.', 200)

@app.route('/zones/<int:zone_id>')
@login_required
def zone(zone_id):
    # name, city, user, source_flowrate, area_size, irrigation_method, watering_amount
    if not request.method == 'GET':
        return abort(403)
    zone = Zone.query.get_or_404(zone_id)
    if zone.user == current_user:
        zone_dict = {
            "name": zone.name,
            "city": zone.city.name,
            "user": zone.user.first_name + ' ' + zone.user.last_name,
            "source-flowrate": zone.source_flowrate,
            "area-size": zone.area_size,
            "irrigation-method": zone.irrigation_method.name,
            "watering-amount": zone.watering_amount.name
        }
        return jsonify(zone_dict)

def is_uuid_authentic(uuid):
    import json
    with open('pocketparadise/functionalities/uuid.json', 'r') as file:
        set = json.load(file)
        return uuid in set

@app.route('/devices', methods=['POST'])
@login_required
def device_create():
    # mac_adress - Nullable, pp_uuid, name, zone - nullable, actuator_present - Nullable
    data = request.get_json()
    name = data.get('name')
    pp_uuid = data.get('pp-uuid')
    actuator_present = data.get('actuator-present')
    if pp_uuid and name:
        if is_uuid_authentic(pp_uuid):
            if Device.query.filter_by(pp_uuid=pp_uuid).first():
                return Response(f'Device with this pp-uuid was already created. Go setup your physical one', 400)
            device = Device(pp_uuid=pp_uuid, name=name,
                            actuator_present=actuator_present if actuator_present else False)
            db.session.add(device)
            db.session.commit()
            return Response(f'Your device "{name}" was created! Go setup your physical one and connect it with zone', 200)
        else:
            return Response('UUID is not valid', 400)
    else:
        return Response('Missing submit data', 400)


@app.route('/plants', methods=['GET', 'POST'])
def add_plant():
    if not request.method == 'POST' and not request.method == 'GET':
        return abort(403)
    if request.method == 'POST':
        data = request.get_json()
        name = data['name']
        humidity_preference = data['h-preference']
        sunlight_preference = data['l-preference']
        temperature_preference = data['t-preference']
        if Plant.query.filter_by(name=name, humidity_preference=humidity_preference,
                 sunlight_preference=sunlight_preference, temperature_preference=temperature_preference).first():
            return Response('Such plant already exists. Go and add it in your zone', 400)
        plant = Plant(name=name, humidity_preference=humidity_preference,
                      sunlight_preference=sunlight_preference, temperature_preference=temperature_preference)
        db.session.add(plant)
        db.session.commit()
        return Response(f'Plant with name {name} added', 201)
    elif request.method == 'GET':
        plants = Plant.query.all()
        plant_list = {}
        for plant in plants:
            plant_list.update({plant.id: Plant.__repr__(plant)})
        return plant_list

@app.route('/zones/<int:zone_id>/plants', methods=['PUT'])
def add_plant(zone_id, plant_id):
    if not request.method == 'PUT':
        return abort(403)



# @app.route('/mqtt')
# def mqtt():
#     client = connect_mqtt()
#     subscribe(client)
#     client.loop_forever()


# @app.route('/forecast')
# def forecast():
#     result = get_weather_forecast(CITY_NAME)
#     return render_template('test1.html', forecast=result)