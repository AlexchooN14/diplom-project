from pocketparadise import app, db, bcrypt, mail
from pocketparadise.functinalities.mqtt_connect import connect_mqtt
from pocketparadise.functinalities.mqtt_discovery import discovery_subscribe
from pocketparadise.functinalities.forecast import get_weather_forecast
from pocketparadise.models import (Country, City, User, WateringAlgorithm,
                                   Zone, Plant, Device, IrrigationData)
from pocketparadise.forms import (RegistrationForm, LoginForm, UpdateAccountForm, ZoneForm)
from flask_login import login_user, current_user, logout_user, login_required

from flask import render_template, url_for, flash, redirect, request, abort, jsonify

CITY_NAME = 'Sofia'


@app.route('/')
@app.route('/home')
def home():
    # client = connect_mqtt()
    # discovery_subscribe(client)
    # client.loop_forever()
    return render_template('temp.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # setup_cities()
    if current_user.is_authenticated:
        return redirect(url_for('zone_create'))
    form = RegistrationForm()
    form.country.choices = [(country.id, country.name) for country in Country.query.all()]
    if form.validate_on_submit():
        print('there')

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        city = City.query.filter_by(name=form.city.data).first()
        user = User(first_name=form.firstname.data, last_name=form.lastname.data,
                    email=form.email.data, password=hashed_password, city=city)
        db.session.add(user)
        db.session.commit()
        flash(f'{form.firstname.data}\'s account was created successfully, Log In', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/city/<string:country_id>')
def cities(country_id):
    country = Country.query.filter_by(id=country_id).first()
    cities = City.query.filter_by(country=country).all()

    cityArray = []

    for city in cities:
        cityObj = {}
        cityObj['id'] = city.id
        cityObj['name'] = city.name
        cityArray.append(cityObj)
    return jsonify({'cities': cityArray})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Unsuccessful login', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/zone', methods=['GET', 'POST'])
@login_required
def zone_create():
    form = ZoneForm()
    if form.validate_on_submit():
        zone = Zone(name=form.name.data, preferred_watering_amount=form.watering_amount.data,
                    user_id=current_user.id, source_flowrate=form.source_flowrate.data,
                    area_size=form.area_size.data, algorithm_id=WateringAlgorithm.query.filter_by(
                                                   irrigation_method=form.algorithm.data))
        print(form.watering_amount.data)
        db.session.add(zone)
        db.session.commit()
        flash(f'Created {form.name.data} zone', 'success')
        return redirect(url_for('zone'))
    zones = Zone.query.filter_by(user_id=current_user.id).all()
    return render_template('zones.html', form=form, zones=zones)


@app.route('/zone/<int:zone_id>')
@login_required
def zone(zone_id):
    zone = Zone.query.filter_by(id=zone_id).first()
    irrigations = IrrigationData.query.filter_by(zone=zone).all()
    return render_template('zone.html', zone=zone, irrigations=irrigations)


@app.route('/zone/<int:zone_id>/delete', methods=['POST'])
@login_required
def delete_zone(zone_id):
    zone = Zone.query.get_or_404(zone_id)
    if zone.user != current_user:
        abort(403)
    db.session.delete(zone)
    db.session.commit()
    flash('Zone has been deleted', 'success')
    return redirect(url_for('home'))


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
    db.session.add(paris)
    db.session.add(cannes)
    db.session.add(lion)
    db.session.add(bulgaria)
    db.session.add(sofia)
    db.session.add(plovdiv)
    db.session.add(varna)
    db.session.commit()


@app.route('/about')
def about():
    return render_template('about.html')

# @app.route('/home')
# def home(city):
#     setup_cities()
#     user = User(first_name='Sasho', last_name='Naumov', email='alexandern003@gmail.com', city=city)


# @app.route('/')
# def zone():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form = ZoneForm()
#     return render_template('zone.html', form=form)