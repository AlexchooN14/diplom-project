import requests
# import tkinter
# import math

API_KEY = '42a3f0d8a9dc5520e3a6a1b08e93e056'


def get_weather_forecast(city_name):
    # url = f"http://api.openweathermap.org/data/2.5/weather?q={name}&appid={API_KEY}"
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city_name}&units=metric&lang=bg&appid={API_KEY}'
    print(url)

    response = requests.get(url).json()
    return response


def get_temperature():
    pass
