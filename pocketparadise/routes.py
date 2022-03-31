from flask import Response
from pocketparadise import app, db, bcrypt
from pocketparadise.models import Country, City, User, Zone, Plant, Device, ZonesPlants, IrrigationSchedule
from flask_login import login_user, current_user, logout_user, login_required

from flask import request, abort, jsonify


@app.route('/countries', methods=['GET', 'POST'])
def add_country():
    if not request.method == 'POST' and not request.method == 'GET':
        return abort(403)
    if request.method == 'POST':
        data = request.get_json()
        country_name = data.get('country-name')
        country_code = data.get('country-code')
        country = Country.query.filter_by(name=country_name, country_code=country_code).first()
        if country:
            return Response(f'Country with name {country_name} and code {country_code} already exists', 400)
        country = Country(name=country_name, country_code=country_code)
        db.session.add(country)
        db.session.commit()
        return Response(f'Country {country_name},{country_code} added', 200)
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
            return Response(f'City with name {city_name} already exists', 400)
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

@app.route('/users', methods=['GET', 'POST', 'PUT'])
def user():
    if request.method == 'POST' or request.method == 'PUT':
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        city_name = data.get('city-name')
    if request.method == 'POST':
        if current_user.is_authenticated:
            return Response('You should Log out first...', 404)

        user = User.query.filter_by(email=email).first()
        if user:
            return Response(f'User with that email already exists', 400)

        if first_name and last_name and email and password and city_name:
            city = City.query.filter_by(name=city_name).first()
            if not city:
                return Response(f'Try with other city names. We didn\'t find this one', 404)
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(first_name=first_name, last_name=last_name, email=email, password=hashed_password, city=city)
            db.session.add(user)
            db.session.commit()
            return Response(f'{first_name}\'s account was created successfully, Log In', 200)
        else:
            return Response('Missing submit data', 400)

    elif request.method == 'GET':
        if not current_user.is_authenticated:
            return Response('You can\'t view your information without logging in...', 404)
        user = User.query.get_or_404(current_user.id)
        user_dict = {
            "firstname": user.first_name,
            "lastname": user.last_name,
            "email": user.email,
            "password": user.password,
            "city": user.city.name
        }
        return jsonify(user_dict)
    elif request.method == 'PUT':
        if not current_user.is_authenticated:
            return Response('You can\'t edit your information without logging in...', 404)
        user = User.query.get_or_404(current_user.id)
        if first_name:
            user.first_name = first_name
        if last_name:
            user.first_name = last_name
        if city_name:
            new_city = City.query.filter_by(name=city_name).first()
            if new_city:
                user.city = new_city
            else:
                return Response(f'Try with other city names. We didn\'t find this one', 404)
        db.session.commit()
        return Response(f'Your information has been updated! Check it via GET method.', 404)
    else:
        return abort(403)


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
            return Response('Wrong credentials.', 400)
    else:
        return Response('Missing submit data.', 400)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return Response('You logged out. Bye for now.', 200)

@app.route('/zones', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def zones():
    # name, city, user, source_flowrate, area_size, irrigation_method, watering_amount
    if request.method == 'POST' or request.method == 'PUT' or request.method == 'DELETE':
        data = request.get_json()
        name = data.get('name')
        city_name = data.get('city-name')
        if city_name:
            city = City.query.filter_by(name=city_name).first_or_404()
        source_flowrate = data.get('source-flowrate')
        area_size = data.get('area-size')
        irrigation_method = data.get('irrigation-method')  # METHOD
        watering_amount = data.get('watering-amount')  # AMOUNT

        if request.method == 'POST':
            if name and city_name and source_flowrate\
                    and area_size and irrigation_method and watering_amount:
                zone = Zone.query.filter_by(name=name, user=current_user).first()
                if not zone:
                    zone = Zone(name=name, city=city, user=current_user, source_flowrate=source_flowrate,
                                area_size=area_size, irrigation_method=irrigation_method,
                                watering_amount=watering_amount)
                    db.session.add(zone)
                    db.session.commit()
                    return Response(f'{name} zone created successfully! Try and add a device.', 200)
                else:
                    return Response('You have a zone with the same name. Change it up a little.', 400)
            else:
                return Response('Missing submit data', 400)

        elif request.method == 'PUT':
            new_name = data.get('new-name')
            zone = None
            if name:
                zone = Zone.query.filter_by(user=current_user, name=name).first()
                if zone:
                    if new_name:
                        zone.name = new_name
                    if city_name:
                        new_city = City.query.filter_by(name=city_name)
                        if new_city:
                            zone.city = new_city
                        else:
                            return Response(f'We don\'t support the city {city_name} yet..', 400)
                    if source_flowrate:
                        zone.source_flowrate = source_flowrate
                    if area_size:
                        zone.area_size = area_size
                    if irrigation_method:
                        zone.irrigation_method = irrigation_method
                    if watering_amount:
                        zone.watering_amount = watering_amount
                    db.session.commit()
                    return Response(f'Data for {zone.name} changed', 200)
                else:
                    return Response('Sadly you dont have such zone. Go create one with POST on /zones', 400)
            else:
                return Response('Missing submit data', 400)

        elif request.method == 'DELETE':
            zone = Zone.query.filter_by(user=current_user, name=name).first_or_404()
            db.session.remove(zone)
            db.session.commit()
            return Response(f'You successfully removed {name} zone. Don\'t be late to create a new one.', 200)

    elif request.method == 'GET':
        zones = Zone.query.filter_by(user=current_user).all()
        if zones:
            l = []
            #  irrigation_method, watering_amount
            for zone in zones:
                zones_dict = {
                    "name": zone.name,
                    "area-size": zone.area_size,
                    "city-name": zone.city.name,
                    "belongs-to": zone.user.first_name + ' ' + zone.user.last_name,
                    "source-flowrate": zone.source_flowrate,
                    "irrigation-method": zone.irrigation_method.name,
                    "watering-amount": zone.watering_amount.name
                }
                l.append(zones_dict)
            return jsonify(l)
        else:
            return Response(f'Currently you do not have any zones. Why not create one?', 200)

    else:
        return abort(403)

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
            "area-size": zone.area_size,
            "city-name": zone.city.name,
            "belongs-to": zone.user.first_name + ' ' + zone.user.last_name,
            "source-flowrate": zone.source_flowrate,
            "irrigation-method": zone.irrigation_method.name,
            "watering-amount": zone.watering_amount.name
        }
        return jsonify(zone_dict)


@app.route('/devices', methods=['GET', 'PUT'])
@login_required
def device():
    if request.method == 'GET':
        if request.data:
            # GET specific device
            data = request.get_json()
            name = data.get('name')
            zones = Zone.query.filter_by(user=current_user).all()
            for zone in zones:
                device = Device.query.filter_by(name=name, zone=zone).first()
                if device:
                    device_dict = {
                        "mqtt-id": device.id,
                        "mac-address": device.mac_address,
                        "pp-uuid": device.pp_uuid,
                        "device-name": device.name,
                        "zone-name": device.zone.name,
                        "actuator": device.actuator_present
                    }
                    return jsonify(device_dict)
            return Response('Such device was not found in any of your zones. This doesn\'t stop you to create one '
                            'though.')

        else:
            # GET all devices
            zones = Zone.query.filter_by(user=current_user).all()
            return_list = []
            for zone in zones:
                devices = Device.query.filter_by(zone=zone).all()
                for device in devices:
                    device_dict = {
                        "mqtt-id": device.id,
                        "mac-address": device.mac_address,
                        "pp-uuid": device.pp_uuid,
                        "device-name": device.name,
                        "zone-name": device.zone.name,
                        "actuator": device.actuator_present
                    }
                    l = []
                    for reading in device.readings:
                        readings_dict = {
                            "sensor": reading.sensor_type,
                            "read-at": reading.read_at,
                            "reading": reading.reading
                        }
                        l.append(readings_dict)
                    device_dict.update({"readings": l})
                    return_list.append(device_dict)
            return jsonify(return_list)
    elif request.method == 'PUT':
        if request.data:
            data = request.get_json()
            pp_uuid = data.get('pp-uuid')
            device_name = data.get('device-name')
            zone_name = data.get('zone-name')
            actuator_present = data.get('actuator-present')
            zone = Zone.query.filter_by(name=zone_name).first_or_404()
            device = Device.query.filter_by(pp_uuid=pp_uuid).first_or_404()

            for d in zone.devices:
                if d.pp_uuid == pp_uuid:
                    return Response(f'This device is already in {zone_name} zone.', 400)

            if device_name and zone_name and actuator_present and zone and device:
                device.name = device_name
                device.actuator_present = actuator_present
                zone.devices.append(device)
                db.session.commit()
                return Response(f'You successfully connected {device_name} device with {zone_name} zone. Time to start irrigating!', 400)
            else:
                return Response('Missing submit data', 400)
        else:
            return Response('Missing submit data', 400)
    else:
        return abort(403)


@app.route('/plants', methods=['GET', 'POST', 'PUT'])
@login_required
def plants():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        humidity_preference = data.get('h-preference')
        sunlight_preference = data.get('l-preference')
        temperature_preference = data.get('t-preference')
        if Plant.query.filter_by(name=name).first():
            return Response('Such plant already exists. Go and add it in your zone', 400)
        plant = Plant(name=name, humidity_preference=humidity_preference,
                      sunlight_preference=sunlight_preference, temperature_preference=temperature_preference)
        db.session.add(plant)
        db.session.commit()
        return Response(f'Plant with name {name} added', 201)
    elif request.method == 'GET':
        plants = Plant.query.all()
        if plants:
            l = []
            for plant in plants:
                plants_dict = {
                    "name": plant.name,
                    "humidity-preference": plant.humidity_preference.name,
                    "sunlight-preference": plant.sunlight_preference.name,
                    "temperature-preference": plant.temperature_preference.name,
                }
                l.append(plants_dict)
            return jsonify(l)
        else:
            return Response(f'There aren\'t any plants added.', 400)
    elif request.method == 'PUT':
        data = request.get_json()
        name = data.get('name')
        humidity_preference = data.get('h-preference')
        sunlight_preference = data.get('l-preference')
        temperature_preference = data.get('t-preference')
        if name:
            plant = Plant.query.filter_by(name=name).first()
            if plant:
                if humidity_preference:
                    plant.humidity_preference = humidity_preference
                if sunlight_preference:
                    plant.sunlight_preference = sunlight_preference
                if temperature_preference:
                    plant.temperature_preference = temperature_preference
                db.session.commit(plant)
                return Response(f'Data for {plant.name} changed', 200)
            else:
                return Response('There is no such plant. You can create it with POST request', 400)
        else:
            return Response('Missing submit data', 400)
    else:
        return abort(403)

@app.route('/zones/plants', methods=['PUT'])
@login_required
def zone_plant():
    if not request.method == 'PUT':
        return abort(403)
    data = request.get_json()
    zone_name = data.get('zone-name')
    plant_name = data.get('plant-name')
    zone = Zone.query.filter_by(user=current_user, name=zone_name).first()
    plant = Plant.query.filter_by(name=plant_name).first()
    if zone and plant:
        zone.plants.append(plant)
        db.session.commit()
        return Response(f'{plant.name} added to zone {zone.name}. Nice job!', 200)
    else:
        return Response(f'Either zone or plant does not exist. Check twice next time!', 404)

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.data:
        data = request.get_json()
    else:
        return Response('Missing submit data..')
    if request.method == 'GET':
        zone_name = data.get('zone-name')
        if zone_name:
            zone = Zone.query.filter_by(name=zone_name).first()
            if zone:
                schedule = IrrigationSchedule.query.filter_by(zone=zone).first()
                if schedule:
                    schedule_dict = {
                        "start-time": schedule.start_time,
                        "end-time": schedule.end_time
                    }
                    return jsonify(schedule_dict)
                else:
                    return Response('Sadly this zone does not have a schedule yet. Hurry up and add one.', 400)
            else:
                return Response('There is no such zone. You can create it with POST request on /zones', 400)
        else:
            return Response('You should submit a zone name to get it\'s schedule. Go ahead..')

    elif request.method == 'POST':
        zone_name = data.get('zone-name')
        start_time = data.get('start-time')
        end_time = data.get('end-time')
        if zone_name and start_time and end_time:
            zone = Zone.query.filter_by(name=zone_name, user=current_user).first()
            if zone:
                if request.method == 'POST':
                    schedule = IrrigationSchedule.query.filter_by(zone=zone).first()
                    if schedule:
                        schedule.start_time = start_time
                        schedule.end_time = end_time
                        db.session.commit()
                        return Response(f'You changed {zone_name} zone schedule to {start_time}-{end_time}.', 200)
                    else:
                        schedule = IrrigationSchedule(start_time=start_time, end_time=end_time, zone=zone)
                        zone.schedule = schedule
                        db.session.add(schedule)
                        db.session.commit()
                        return Response(f'Okay. Zone schedule was set to {start_time}-{end_time}', 200)
            else:
                return Response('There is no such zone. You can create it with POST request on /zones', 400)
    else:
        return abort(403)

@app.route('/readings')
@login_required
def readings():
    if not request.method == 'GET':
        return abort(403)
    if request.data:
        data = request.get_json()
    else:
        return Response('To get sensor readings provide either zone name or device name.')
    device_name = data.get('device-name')
    zone_name = data.get('zone-name')
    if device_name:
        device = Device.query.filter_by(name=device_name).first()
        if device:
            readings = device.readings
            l = []
            for reading in readings:
                readings_dict = {
                    "sensor-type": reading.sensor_type,
                    "read-at": reading.read_at,
                    "reading": reading.reading
                }
                l.append(readings_dict)
            return jsonify(l)
        else:
            return Response('There is no such device. You can create it with POST request on /devices', 400)
    elif zone_name:
        zone = Zone.query.filter_by(name=zone_name).first()
        if zone:
            devices = zone.devices
            d = {}
            for device in devices:
                l = []
                for reading in device.readings:
                    readings_dict = {
                        "sensor-type": reading.sensor_type,
                        "read-at": reading.read_at,
                        "reading": reading.reading
                    }
                    l.append(readings_dict)
                d.update({device.name: l})
            return jsonify(d)
        else:
            return Response('There is no such zone. You can create it with POST request on /zones', 400)

@app.route('/irrigations', methods=['GET'])
@login_required
def irrigations():
    if request.method == 'GET':
        if request.data:
            data = request.get_json()
            zone_name = data.get('zone-name')
            if zone_name:
                zone = Zone.query.filter_by(name=zone_name).first()
                if zone:
                    l = []
                    irrigations = zone.irrigation_data
                    for irrigation in irrigations:
                        irrigation_dict = {
                            "began": irrigation.at,
                            "duration": irrigation.duration
                        }
                        l.append(irrigation_dict)
                    return jsonify(l)
                else:
                    return Response('There is no such zone. You can create it with POST request on /zones', 400)
            else:
                return Response('You should submit zone name to get its irrigations. Try again.', 400)
        else:
            zones = Zone.query.filter_by(user=current_user).all()
            if zones:
                d = {}
                for zone in zones:
                    l = []
                    for irrigation in zone.irrigation_data:
                        irrigation_dict = {
                            "began": irrigation.at,
                            "duration": irrigation.duration
                        }
                        l.append(irrigation_dict)
                    d.update({zone.name: l})
                    return jsonify(d)
            else:
                return Response('Currently you don\'t have any zones. Go create one and see what happens.', 400)

    else:
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

# @app.route('/devices', methods=['POST'])
# @login_required
# def device_create():
#     from .functionalities.MQTT import is_uuid_authentic
#     # mac_adress - Nullable, pp_uuid, name, zone - nullable, actuator_present - Nullable
#     data = request.get_json()
#     name = data.get('name')
#     pp_uuid = data.get('pp-uuid')
#     actuator_present = data.get('actuator-present')
#     zone_name = data.get('zone-name')
#     if pp_uuid and name and zone_name:
#         zone = Zone.query.filter_by(user=current_user, name=zone_name).first()
#         if not zone:
#             return Response('You don\'t have a zone with this name. Check your zones and try again.')
#         if is_uuid_authentic(pp_uuid):
#             if Device.query.filter_by(pp_uuid=pp_uuid).first():
#                 return Response(f'Device with this pp-uuid was already created. Go setup your physical one', 400)
#             device = Device(pp_uuid=pp_uuid, name=name, zone=zone,
#                             actuator_present=bool(actuator_present) if actuator_present else False)
#             db.session.add(device)
#             db.session.commit()
#             return Response(f'Your device "{name}" was created! Go setup your physical one and connect it with zone', 200)
#         else:
#             return Response('UUID is not valid', 400)
#     else:
#         return Response('Missing submit data', 400)

# def setup_cities():
#     france = Country(name='France')
#     paris = City(name='Paris', country=france)
#     cannes = City(name='Cannes', country=france)
#     lion = City(name='Lion', country=france)
#     bulgaria = Country(name='Bulgaria')
#     sofia = City(name='Sofia', country=bulgaria)
#     plovdiv = City(name='Plovdiv', country=bulgaria)
#     varna = City(name='Varna', country=bulgaria)
#     db.session.add(france)
#     db.session.add(bulgaria)
#     db.session.commit()
#     db.session.add(paris)
#     db.session.add(cannes)
#     db.session.add(lion)
#     db.session.add(sofia)
#     db.session.add(plovdiv)
#     db.session.add(varna)
#     db.session.commit()
