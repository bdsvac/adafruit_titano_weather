# Adafruit Titano Weather
Adafruit [Titano](https://www.adafruit.com/product/4444) Weather is a port of [MagTag](https://www.adafruit.com/product/4800) Weather project: https://learn.adafruit.com/magtag-weather

![Titano Weather Display!](https://github.com/bdsvac/adafruit_titano_weather/blob/main/weather_display.jpg)

The [Unexpected Maker Feather S2](https://www.adafruit.com/product/4769) is connected to a [TMP117](https://www.adafruit.com/product/4821), [Si7021](https://www.adafruit.com/product/3251), or [BME680](https://www.adafruit.com/product/3660) and the data is uploaded to [Adafruit IO](https://io.adafruit.com/). The feed name and Adafruit IO settings are set in secrets.py.

The Titano is then updated every 15 minutes with data from Adafruit IO and [OpenWeather](https://openweathermap.org).
