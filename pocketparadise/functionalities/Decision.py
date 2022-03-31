import math

from pocketparadise.functionalities.forecast import get_weather
from pocketparadise.models import Device, Zone, IrrigationData, Reading, SENSOR, ZonesPlants, AMOUNT, METHOD
import datetime
from datetime import timedelta
from pocketparadise import IRRIGATION_OFFSET, CONFIG_SEND_OFFSET


def is_irrigation_too_recent(irrigations):  # Tested - working
    if not irrigations:
        return False
    current_time = datetime.datetime.now()
    recent_irrigation = IrrigationData.query.order_by(IrrigationData.id.desc()).first()
    difference = current_time - recent_irrigation.at
    return difference < timedelta(minutes=IRRIGATION_OFFSET)


# Return None if no readings, dict with most recent readings if readings
def get_recent_readings(device):
    reading_sm = Reading.query.filter_by(device=device, sensor_type=SENSOR.SOIL_MOISTURE).order_by(
        Reading.id.desc()).first()
    reading_at = Reading.query.filter_by(device=device, sensor_type=SENSOR.AIR_TEMPERATURE).order_by(
        Reading.id.desc()).first()
    reading_ah = Reading.query.filter_by(device=device, sensor_type=SENSOR.AIR_HUMIDITY).order_by(
        Reading.id.desc()).first()
    reading_ap = Reading.query.filter_by(device=device, sensor_type=SENSOR.AIR_PRESSURE).order_by(
        Reading.id.desc()).first()

    if reading_sm and reading_at and reading_ah and reading_ap:
        return {
            "soil-moisture": reading_sm.reading,
            "air-temperature": reading_at.reading,
            "air-humidity": reading_ah.reading,
            "air-pressure": reading_ap.reading
        }
    else:
        return None

# Return None if no irrigations, dict with most recent irrigation if irrigations
def get_recent_irrigation(zone, irrigations_to_return):

    if irrigations_to_return <= 0:
        return None
    else:
        irrigations = IrrigationData.query.filter_by(zone=zone)\
            .order_by(IrrigationData.id.desc()).limit(irrigations_to_return)

    if irrigations:
        l = []
        d = {}

        for irrigation in irrigations:
            d.update({'at': irrigation.at, 'duration': irrigation.duration})
            l.append(d)
        return l
    else:
        return None


# Get list of id's for every weather entry
def get_weather_id_list(weather):
    l = []
    for current in weather:
        l.append(str(current.get('weather')[0].get('id')))

    return l


def is_in_schedule_time(schedule):
    current_time = datetime.datetime.now()
    current_time = current_time.time()
    if schedule.start_time < current_time < schedule.end_time:
        return True
    return False


# Return None if no plants added, AVG needs if plants added
def get_zone_moisture_needs(zone):
    plants = zone.plants
    if not plants:
        return None
    sum_high, sum_mid, sum_low = 0, 0, 0

    for plant in plants:
        if plant.humidity_preference == AMOUNT.MOST:
            sum_high += 1
        elif plant.humidity_preference == AMOUNT.MEDIUM:
            sum_mid += 1
        else:
            sum_low += 1

    if sum_high > sum_mid and sum_high > sum_low:
        return AMOUNT.MOST
    elif sum_mid > sum_high and sum_mid > sum_low:
        return AMOUNT.MEDIUM
    else:
        return AMOUNT.LEAST


def is_direct_sunlight(timezone_offset, current, hourly_ids):
    hours_offset = 7200  # In seconds
    datetime = current.get('dt') + timezone_offset
    sunrise = current.get('sunrise')
    sunset = current.get('sunset')
    current_weather = current.get('weather')[0]

    if current_weather == '802' or current_weather == '803' or current_weather == '804' or \
            current.get('clouds') >= 35:
        # Current weather cloudy
        print('Current weather is cloudy. Checking clearance of weather without direct sunlight.')

        for i in range(3):
            if not (hourly_ids[i] == '802' or hourly_ids[i] == '803' or hourly_ids[i] == '804' or current.get('clouds') >= 35):
                print('No enough clearance of weather without direct sunlight.')
                return False

        print(f'Enough clearance of weather without direct sunlight.')
        return True

    elif datetime <= sunrise - hours_offset:
        print('Datetime not before the first hours of sunrise.')
        return False
    elif datetime >= sunset - hours_offset:
        print('Datetime not after the last hours of sunset.')
        return False
    else:
        print('Datetime is good for irrigation.')
        return True


def is_forecast_temperature_good(current, hourly, day):
    daily_temperatures = day.get('temp')
    daily_day = daily_temperatures.get('day')
    daily_min = daily_temperatures.get('min')
    daily_max = daily_temperatures.get('max')
    daily_morn = daily_temperatures.get('morn')
    daily_eve = daily_temperatures.get('eve')
    daily_night = daily_temperatures.get('night')

    daily_list = []
    daily_list.extend([daily_day, daily_min, daily_max, daily_morn, daily_eve, daily_night])
    is_daily_good = True
    for temperature in daily_list:
        if temperature <= 4:
            is_daily_good = False
            break

    current_temperature = current.get('feels_like')
    if current_temperature <= 4:
        print('Currently the forecast temperature is low.')
        # Current weather cold

        if not is_daily_good:
            print('The whole day is predicted to be cold.')
            # Daily weather cold
            return False
        else:
            # Daily weather warm
            print('Daily forecast is predicting to be warm though.')

            for i in range(5):
                if hourly[i].get('feels_like') <= 4:
                    print('No enough hour clearance of warmer weather.')
                    return False

            print(f'Enough clearance of warmer weather.')
            return True
    else:
        # Current weather warm
        print('Currently the forecast temperature is good.')
        if not is_daily_good:
            # Daily weather cold
            print('The whole day is predicted to be cold though.')
            for i in range(5):
                if hourly[i].get('feels_like') <= 4:
                    print('No enough hour clearance of warmer weather.')
                    return False

            print(f'Enough clearance of warmer weather.')
            return True
        else:
            # Daily weather warm
            print('Daily forecast is predicting to be warm.')
            return True


def is_rain_stopping_soon(minutely, hourly_ids, daily_ids):
    if daily_ids[0].startswith('8') or daily_ids[0].startswith('7'):
        # Daily weather clear
        print('Daily forecast is for clear weather.')
        if hourly_ids[0].startswith('8') or hourly_ids[0].startswith('7'):
            # First hour clear
            print('Rain could be stopping really soon.')
            minutes = 0
            for minute in minutely:
                precipitation = minute.get('precipitation')
                rain = precipitation > 0
                if rain:
                    minutes += 1

            if minutes > IRRIGATION_OFFSET:
                # Rain isn't stopping sooner than 1 sleep cycle
                print('Rain isn\'t stopping soon enough.')
                return False
            else:
                # Rain is going to stop soon
                print('Rain is going to stop in the close minutes.')
                return True
        else:
            # Rain isn't stopping in the first 1 hour
            print('Rain is not stopping in the first 1 hour.')
            return False
    else:
        # The whole day is a rain day
        print('Daily forecast is predicting rain the whole day.')
        return False


def is_rain_heavier(daily_id):
    if daily_id == '200' or daily_id == '210' or daily_id == '211' or daily_id == '230' or \
            daily_id == '300' or daily_id == '301' or daily_id == '310' or \
            daily_id == '500':
        print('Current rain is a light one.')
        return False
    else:
        print('Current rain is a heavy one.')
        return True


def is_rain_coming_soon(hourly_ids, daily_ids):
    if daily_ids[0].startswith('8') or daily_ids[0].startswith('7'):
        # Daily weather clear
        print('Daily forecast for clear weather.')
        hours_clearance = 0
        for i in range(5):
            if not (hourly_ids[i].startswith('8') or hourly_ids[i].startswith('7')):
                break
            else:
                hours_clearance += 1

        if hours_clearance > 2:
            print('Enough hour clearance of good clear weather.')
            return False
        else:
            # Hourly rain coming too soon
            print('There\'s no enough hour clearance of good clear weather.')
            return True
    else:
        # Daily weather not clear
        print('Daily weather will not be clear.')

        if is_rain_heavier(daily_ids[0]):
            # If rain will be heavy during the day no need to irrigate
            return True

        hours_clearance = 0
        for i in range(5):
            if not (hourly_ids[i].startswith('8') or hourly_ids[i].startswith('7')):
                break
            else:
                hours_clearance += 1

        # More clearance because of daily weather being not clear
        if hours_clearance > 4:
            print('Enough hour clearance of good clear weather.')
            return False
        else:
            # Hourly rain coming too soon
            print('There\'s no enough hour clearance of good clear weather.')
            return True


# Check whether weather is even favorable for irrigation
def decide_weather(device):
    zone = device.zone

    forecast = get_weather(zone.city.name, zone.city.country.country_code)
    if forecast.get('cod'):
        print('Something went wrong. Try again later.')
        return None

    current = forecast.get('current')
    current_id = str(current.get('weather')[0].get('id'))
    minutely = forecast.get('minutely')

    hourly = forecast.get('hourly')
    hourly_ids = get_weather_id_list(hourly)

    daily = forecast.get('daily')
    daily_ids = get_weather_id_list(daily)

    # If alerts for extreme weather -> no irrigation should happen such conditions
    if forecast.get('alerts'):
        print('Extreme weather now, not good for irrigation...')
        # return False  # COMMENTED BECAUSE OF THE DEFENSE

    if is_direct_sunlight(forecast.get('timezone_offset'), current, hourly_ids):
        # Direct sunlight time of day -> not good for irrigation
        print('Direct sunlight right now, not good for irrigation...')
        # return False  # COMMENTED BECAUSE OF THE DEFENSE
    else:
        if not is_forecast_temperature_good(current, hourly, daily[0]):
            # Temperature not good -> not good for irrigation
            print('Temperature either extremely high or too low, not good for irrigation...')
            # return False  # COMMENTED BECAUSE OF THE DEFENSE

    # Time of day is not with direct sunlight and forecasted temperature is good

    if current_id.startswith('2'):
        # Thunderstorm
        print('Currently there\'s a thunderstorm.')
        if current_id == '200' or current_id == '210' or current_id == '211' or \
                current_id == '230':
            # Lighter rain thunderstorm
            print('Thunderstorm with light rain only.')
            if is_rain_stopping_soon(minutely, hourly_ids, daily_ids):
                print('It will stop soon.')
                return True
            else:
                print('It will not stop soon.')
                return False

        else:
            # Heavier rain thunderstorm
            print('Thunderstorm with heavy rain.')
            return False

    elif current_id.startswith('3'):
        # Drizzle
        print('Currently there\'s a drizzle.')
        if current_id == '300' or current_id == '301' or current_id == '310':
            # Lighter drizzle
            print('Drizzle with light rain only.')
            if is_rain_stopping_soon(minutely, hourly_ids, daily_ids):
                print('It will stop soon.')
                return True
            else:
                print('It will not stop soon.')
                return False
        else:
            # Heavier drizzle
            print('Drizzle with heavy rain.')
            return False

    elif current_id.startswith('5'):
        # Rain
        print('Currently it is raining.')
        if current_id == '500':
            # Lighter rain
            print('It is a lighter rain.')
            if is_rain_stopping_soon(minutely, hourly_ids, daily_ids):
                print('It will stop soon.')
                return True
            else:
                print('It will not stop soon.')
                return False
        else:
            # Heavier rain or shower rain
            print('It is a heavier rain.')
            return False

    elif current_id.startswith('6'):
        # Snow
        print('Currently it is snowing.')
        return False

    elif current_id.startswith('7'):
        # Atmospheric
        print('Currently there\'s an atmospheric condition.')
        if current_id == '721' or current_id == '762' or current_id == '771' or current_id == '781':
            # Extreme or toxic atmospheric weather
            print('It is an extreme or toxic one.')
            return False
        else:
            print('It is not dangerous.')
            return True

    elif current_id == '800':
        # Clear
        print('Currently the weather is clear')
        if is_rain_coming_soon(hourly_ids, daily_ids):
            print('Rain is coming soon.')
            return False
        else:
            print('Rain is not coming soon.')
            return True
    else:
        # Clouds
        print('Currently the weather is cloudy')
        if is_rain_coming_soon(hourly_ids, daily_ids):
            print('Rain is coming soon.')
            return False
        else:
            print('Rain is not coming soon.')
            return True

def get_difference_in_times(start_time, end_time):
    date = datetime.date(1, 1, 1)
    start_datetime = datetime.datetime.combine(date, start_time)
    end_datetime = datetime.datetime.combine(date, end_time)
    return end_datetime - start_datetime

# decide if irrigation is needed based on previous irrigations and irrigation methodology
def decide_irrigation_method(zone):
    method = zone.irrigation_method
    schedule = zone.schedule

    if method == METHOD.SPREAD:
        print('Zone with SPREAD methodology. OK to irrigate anytime when favorable.')
        return True

    past_irrigations = get_recent_irrigation(zone, 2)
    count = 0

    for irrigation in past_irrigations:
        today = datetime.datetime.today().date()
        if irrigation.get('at').date() == today:
            irrigation_time = irrigation.get('at').strftime('%H:%M:%S')
            if not schedule or schedule.start_time < irrigation_time < schedule.end_time:
                count += 1

    if method == METHOD.AT_START and count == 0:
        print('Zone with AT_START methodology, no irrigations today.')
        return True
    elif method == METHOD.AT_END and count == 0:
        current_time = datetime.datetime.now().time()
        if not schedule or get_difference_in_times(current_time, schedule.end_time) < timedelta(minutes=IRRIGATION_OFFSET):
            print('Zone with AT_END methodology, no irrigations today, close to schedule end.')
            return True

    elif method == METHOD.AT_START_AND_END:
        if count == 0:
            print('Zone with AT_START_AND_END methodology, no irrigations today.')
            return True
        elif count == 1:
            current_time = datetime.datetime.now().time()
            if not schedule or get_difference_in_times(current_time, schedule.end_time) < timedelta(minutes=IRRIGATION_OFFSET):
                print('Zone with AT_START_AND_END methodology, 1 irrigation today, close to schedule end.')
                return True
    return False


def decide_zone(device):
    zone = device.zone
    watering_amount = zone.watering_amount

    if not decide_irrigation_method(zone):
        print('Zone irrigation methodology is not allowing irrigations.')
        return False

    readings = get_recent_readings(device)
    if not readings:
        print('Device hasn\'t submitted any readings.')
        return False

    zone_moisture_needs = get_zone_moisture_needs(zone)

    if readings.get('air-temperature') < 4:
        print('Temperature sensor is measuring too low temperatures.')
        # Cold, water may freeze
        return False
    elif readings.get('air-humidity') == 100:
        print('Air humidity is really high. A lot of water vapor present.')
        # Very humid weather, rain may be incoming
        return False
    elif readings.get('soil-moisture') < 360:
        print('Soil moisture is too high. Irrigation MUST NOT happen.')
        # Overly moist, irrigation MUST not happen
        return False

    if 360 < readings.get('soil-moisture') < 420:
        # Very moist
        print('Soil moisture is relatively high.')
        wakeup_interval = 1800  # 30 min. in seconds

        if zone_moisture_needs:
            if zone_moisture_needs == AMOUNT.MOST:
                if 420 - readings.get('soil-moisture') <= 5:
                    print('OK to irrigate zone with MOST plant water needs.')
                    return build_config(zone, wakeup_interval, AMOUNT.LEAST)
                else:
                    print('Too high to irrigate zone with MOST plant water needs.')
                    return False
            elif zone_moisture_needs == AMOUNT.MEDIUM:
                print('Too high for zone with MEDIUM plant water needs.')
                return False
            elif zone_moisture_needs == AMOUNT.LEAST:
                print('Too high for zone with LEAST plant water needs.')
                return False

        if watering_amount == AMOUNT.MOST:
            if 420 - readings.get('soil-moisture') <= 5:
                print('OK to irrigate zone with MOST watering amount.')
                return build_config(zone, wakeup_interval, AMOUNT.LEAST)
            else:
                print('Too high to irrigate zone with MOST watering amount.')
                return False
        elif watering_amount == AMOUNT.MEDIUM:
            print('Too high for zone with MEDIUM watering amount.')
            return False
        elif watering_amount == AMOUNT.LEAST:
            print('Too high for zone with LEAST watering amount.')
            return False

    elif 420 < readings.get('soil-moisture') < 590:
        # Medium moist
        print('Soil moisture is medium.')
        wakeup_interval = 5400  # 90 min. in seconds
        if zone_moisture_needs:
            if zone_moisture_needs == AMOUNT.MOST:
                print('Too dry for zone with MOST plant water needs.')
                return build_config(zone, wakeup_interval, AMOUNT.MEDIUM)
            elif zone_moisture_needs == AMOUNT.MEDIUM:
                if 590 - readings.get('soil-moisture') <= 10:
                    print('OK to irrigate zone with MEDIUM plant water needs.')
                    return build_config(zone, wakeup_interval, AMOUNT.LEAST)
                else:
                    print('Too high to irrigate zone with MEDIUM plant water needs.')
                    return False
            elif zone_moisture_needs == AMOUNT.LEAST:
                print('Too high for zone with LEAST plant water needs.')
                return False

        if watering_amount == AMOUNT.MOST:
            print('Too dry for zone with MOST watering amount.')
            return build_config(zone, wakeup_interval, AMOUNT.MEDIUM)
        elif watering_amount == AMOUNT.MEDIUM:
            if 590 - readings.get('soil-moisture') <= 10:
                print('OK to irrigate zone with MEDIUM watering amount.')
                return build_config(zone, wakeup_interval, AMOUNT.LEAST)
            else:
                print('Too high to irrigate zone with MEDIUM watering amount.')
                return False
        elif watering_amount == AMOUNT.LEAST:
            print('Too high for zone with LEAST watering amount.')
            return False

    elif 590 < readings.get('soil-moisture') < 630:
        # Dry
        print('Soil moisture is low.')
        wakeup_interval = 7200  # 120 min. in seconds
        if zone_moisture_needs:
            if zone_moisture_needs == AMOUNT.MOST:
                print('Too dry for zone with MOST plant water needs.')
                return build_config(zone, wakeup_interval, AMOUNT.MOST)
            elif zone_moisture_needs == AMOUNT.MEDIUM:
                print('Too dry for zone with MEDIUM plant water needs.')
                return build_config(zone, wakeup_interval, AMOUNT.MEDIUM)
            elif zone_moisture_needs == AMOUNT.LEAST:
                if 630 - readings.get('soil-moisture') <= 10:
                    print('OK to irrigate zone with LEAST plant water needs.')
                    return build_config(zone, wakeup_interval, AMOUNT.MEDIUM)
                else:
                    print('Too high to irrigate zone with LEAST plant water needs.')
                    return False

        if watering_amount == AMOUNT.MOST:
            print('Too dry for zone with MOST watering amount.')
            return build_config(zone, wakeup_interval, AMOUNT.MOST)
        elif watering_amount == AMOUNT.MEDIUM:
            print('Too dry for zone with MEDIUM watering amount.')
            return build_config(zone, wakeup_interval, AMOUNT.MEDIUM)
        elif watering_amount == AMOUNT.LEAST:
            if 630 - readings.get('soil-moisture') <= 10:
                print('OK to irrigate zone with LEAST watering amount.')
                return build_config(zone, wakeup_interval, AMOUNT.LEAST)
            else:
                print('Too high to irrigate zone with LEAST watering amount.')
                return False

    elif readings.get('soil-moisture') >= 630:
        # Extremely dry, irrigation MUST happen
        print('Soil moisture is critically low. Irrigation MUST happen.')
        wakeup_interval = 1800  # 30 min. in seconds
        return build_config(zone, wakeup_interval, AMOUNT.MOST)


def build_config(zone, wakeup_interval, amount):
    d = {"wakeup-interval": wakeup_interval}

    liters = zone.area_size * 0.2 * 1000000

    if amount == AMOUNT.LEAST:
        liters = math.floor(liters * 0.1 / 1000)
    elif amount == AMOUNT.MEDIUM:
        liters = math.floor(liters * 0.2 / 1000)
    elif amount == AMOUNT.MOST:
        liters = math.floor(liters * 0.3 / 1000)
    # print(f'liters needed will be {liters}')

    duration = math.ceil(liters / zone.source_flowrate * 60)  # duration in seconds
    time = datetime.datetime.utcnow() + timedelta(seconds=CONFIG_SEND_OFFSET)

    d.update({'schedule-operation': [{'start-time': time, 'duration': duration}]})
    return d

# Return None if error or if no config needed, return config dict if config needed
def decide(mqtt_id):
    device = Device.query.get(mqtt_id)

    if device.config_present:
        print('Config file in device already exists. No decision will be made.')
        return None

    zone = device.zone
    if not zone:
        print('Device is not connected to any zone. No decision will be made.')
        return None

    schedule = zone.schedule
    if schedule:
        if not is_in_schedule_time(schedule):
            print('Currently it is not configuration time. No decision will be made.')
            return None

    irrigations = zone.irrigation_data
    # if irrigation has happened not long ago do not send config
    if is_irrigation_too_recent(irrigations):
        print('Irrigation has happened too recently. No decision will be made.')
        # return None  # COMMENTED BECAUSE OF THE DEFENSE

    result = decide_zone(device)
    if result:
        if decide_weather(device):
            return result
    return None
