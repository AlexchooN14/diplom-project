import requests
from pocketparadise import API_KEY

# Get lat, lon by city name and country code
def get_coordinates_by_name(city_name, country_code):
    url = f'http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&appid={API_KEY}'
    response = requests.get(url).json()
    coordinates = [response[0]['lat'], response[0]['lon']]
    return coordinates

# One call api for many current, minute, hourly, daily and alerts
def get_weather(city_name, country_code):
    lat, lon = get_coordinates_by_name(city_name, country_code)
    url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units=metric&appid={API_KEY}'
    response = requests.get(url).json()
    return response


# print(get_weather('Sofia', 'BG'))
