#libraries:
#  adafruit_bitmap_font
#  adafruit_bus_device
#  adafruit_display_shapes
#  adafruit_display_text
#  adafruit_esp32spi
#  adafruit_imageload
#  adafruit_io
#  adafruit_portalbase
#  adafruit_register
#  adafruit_fakerequests.mpy
#  adafruit_requests.mpy
#  neopixel.mpy
#  simpleio.mpy

import gc
import busio
import board
import time
import displayio
import adafruit_imageload
import adafruit_requests as requests
from adafruit_bitmap_font import bitmap_font
from digitalio import DigitalInOut
from adafruit_display_text import label
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
from secrets import secrets
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

METRIC = False  # set to True for metric units
BACKGROUND_BMP = "/weather_bg2.bmp"
ICONS_LARGE_FILE = "/weather_icons_70px.bmp"
ICONS_SMALL_FILE = "/weather_icons_20px.bmp"
ICON_MAP = ("01", "02", "03", "04", "09", "10", "11", "13", "50")
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
font = bitmap_font.load_font("/fonts/Arial-12.bdf")

COLOR_DATE = 0xF1B73F
COLOR_CITY = 0x7877EE

COLOR_TODAY_TEMPS = 0x3EF7BB
COLOR_TODAY_DATA = 0x3CF03A
COLOR_SUN_TIMES = 0x3EF7BB

COLOR_DAYS = 0x38B2F2
COLOR_TEMPS = 0xC778F0

COLOR_FEED_DATA = 0xC778F0

aio_feed0_name = "upstairs"
aio_feed1_name = "downstairs"
aio_feed2_name = "basement"

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "Augsut",
    "September",
    "October",
    "November",
    "December",
)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, DigitalInOut(board.ESP_CS), DigitalInOut(board.ESP_BUSY), DigitalInOut(board.ESP_RESET))
requests.set_socket(socket, esp)

def get_data_source_url(api="onecall", location=None):
    if api.upper() == "FORECAST5":
        URL = "https://api.openweathermap.org/data/2.5/forecast?"
        URL += "q=" + location
    elif api.upper() == "ONECALL":
        URL = "https://api.openweathermap.org/data/2.5/onecall?exclude=minutely,hourly,alerts"
        URL += "&lat={}".format(location[0])
        URL += "&lon={}".format(location[1])
    else:
        raise ValueError("Unknown API type: " + api)
    return URL + "&appid=" + secrets["openweather_token"]

def get_latlon():
    url = get_data_source_url(api="forecast5", location=secrets["openweather_location"])
    try:
        r = requests.get(url)
        raw_data = r.json()
        r.close()
        return raw_data["city"]["coord"]["lat"], raw_data["city"]["coord"]["lon"]
    except:
        return None

def get_feed_data():
    io = IO_HTTP(secrets["aio_username"], secrets["aio_key"], requests)

    feed0 = None
    feed1 = None
    feed2 = None

    if (feed0 is None):
        try:
            feed0 = io.get_feed(aio_feed0_name)
        except:
            print("Can't get " + aio_feed0_name + " feed.")
    if (feed1 is None):
        try:
            feed1 = io.get_feed(aio_feed1_name)
        except:
            print("Can't get " + aio_feed1_name + " feed.")
    if (feed2 is None):
        try:
            feed2 = io.get_feed(aio_feed2_name)
        except:
            print("Can't get " + aio_feed2_name + " feed.")

    try:
        t0 = io.receive_data(feed0["key"])
        t1 = io.receive_data(feed1["key"])
        t2 = io.receive_data(feed2["key"])

        return t0["value"], t1["value"], t2["value"]
    except:
        return None, None, None

def get_forecast(location):
    url = get_data_source_url(api="onecall", location=location)
    try:
        r = requests.get(url)
        raw_data = r.json()
        r.close()
        return raw_data["daily"], raw_data["current"]["dt"], raw_data["timezone_offset"]
    except:
        return None

def temperature_text(tempK):
    if METRIC:
        return "{:3.0f} C".format(tempK - 273.15)
    else:
        return "{:3.0f} F".format(32.0 + 1.8 * (tempK - 273.15))

def wind_text(speedms):
    if METRIC:
        return "{:3.0f} m/s".format(speedms)
    else:
        return "{:3.0f} mph".format(2.23694 * speedms)

icons_large_bmp, icons_large_pal = adafruit_imageload.load(ICONS_LARGE_FILE)
bitmap_file = open(BACKGROUND_BMP, "rb")
bitmap = displayio.OnDiskBitmap(bitmap_file)
icons_small_bmp, icons_small_pal = adafruit_imageload.load(ICONS_SMALL_FILE)

def update_display(data, tz_offset, t0, t1, t2):
    date = time.localtime(data["dt"])
    sunrise = time.localtime(data["sunrise"] + tz_offset)
    sunset = time.localtime(data["sunset"] + tz_offset)

    group = displayio.Group(max_size=19)
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=displayio.ColorConverter(), x=0, y=0)
    group.append(tile_grid)

    today_date = label.Label(font, text="?" * 30, color=COLOR_DATE)
    today_date.anchor_point = (0, 0)
    today_date.anchored_position = (30, 50)
    today_date.text = "{} {} {}, {}".format(
        DAYS[date.tm_wday].upper(),
        MONTHS[date.tm_mon - 1].upper(),
        date.tm_mday,
        date.tm_year,
    )
    group.append(today_date)

    city_name = label.Label(font, text=secrets["openweather_location"], color=COLOR_CITY)
    city_name.anchor_point = (0, 0)
    city_name.anchored_position = (30, 100)
    group.append(city_name)

    today_icon = displayio.TileGrid(
        icons_large_bmp,
        pixel_shader=icons_large_pal,
        x=30,
        y=150,
        width=1,
        height=1,
        tile_width=70,
        tile_height=70,
    )
    if (data is not None):
        today_icon[0] = ICON_MAP.index(data["weather"][0]["icon"][:2])
    group.append(today_icon)

    td_y_pos = 180
    td_x_pos = 155
    td_x_pos_add = 55
    today_morn_temp = label.Label(font, text="+100F", color=COLOR_TODAY_TEMPS)
    today_morn_temp.anchor_point = (0.5, 0)
    today_morn_temp.anchored_position = (td_x_pos, td_y_pos)
    if (data is not None):
        today_morn_temp.text = temperature_text(data["temp"]["morn"])
    group.append(today_morn_temp)

    today_day_temp = label.Label(font, text="+100F", color=COLOR_TODAY_TEMPS)
    today_day_temp.anchor_point = (0.5, 0)
    today_day_temp.anchored_position = (td_x_pos + td_x_pos_add, td_y_pos)
    if (data is not None):
        today_day_temp.text = temperature_text(data["temp"]["day"])
    group.append(today_day_temp)

    today_night_temp = label.Label(font, text="+100F", color=COLOR_TODAY_TEMPS)
    today_night_temp.anchor_point = (0.5, 0)
    today_night_temp.anchored_position = (td_x_pos + td_x_pos_add + td_x_pos_add, td_y_pos)
    if (data is not None):
        today_night_temp.text = temperature_text(data["temp"]["night"])
    group.append(today_night_temp)

    td2_x_pos = 160
    td2_y_pos = 240
    td2_x_pos_add = 70
    today_humidity = label.Label(font, text="100%", color=COLOR_TODAY_DATA)
    today_humidity.anchor_point = (0, 0.5)
    today_humidity.anchored_position = (td2_x_pos, td2_y_pos)
    if (data is not None):
        today_humidity.text = "{:3d} %".format(data["humidity"])
    group.append(today_humidity)

    today_wind = label.Label(font, text="99m/s", color=COLOR_TODAY_DATA)
    today_wind.anchor_point = (0, 0.5)
    today_wind.anchored_position = (td2_x_pos + td2_x_pos_add, td2_y_pos)
    if (data is not None):
        today_wind.text = wind_text(data["wind_speed"])
    group.append(today_wind)

    sun_x_pos = 70
    sun_y_pos = 280
    sun_y_pos_add = 120
    today_sunrise = label.Label(font, text="12:12 PM", color=COLOR_SUN_TIMES)
    today_sunrise.anchor_point = (0, 0.5)
    today_sunrise.anchored_position = (sun_x_pos, sun_y_pos)
    today_sunrise.text = "{:2d}:{:02d} AM".format(sunrise.tm_hour, sunrise.tm_min)
    group.append(today_sunrise)

    today_sunset = label.Label(font, text="12:12 PM", color=COLOR_SUN_TIMES)
    today_sunset.anchor_point = (0, 0.5)
    today_sunset.anchored_position = (sun_x_pos + sun_y_pos_add, sun_y_pos)
    today_sunset.text = "{:2d}:{:02d} PM".format(sunset.tm_hour - 12, sunset.tm_min)
    group.append(today_sunset)

    X_POS = 335
    Y_POS = 25
    Y_POS_OFFSET = 30
    for day, forecast in enumerate(forecast_data[1:6]):
        day_of_week = label.Label(font, text="DAY", color=COLOR_DAYS)
        day_of_week.anchor_point = (0, 0.5)
        day_of_week.anchored_position = (0, 14)
        icon = displayio.TileGrid(
            icons_small_bmp,
            pixel_shader=icons_small_pal,
            x=48,
            y=4,
            width=1,
            height=1,
            tile_width=20,
            tile_height=20,
        )
        day_temp = label.Label(font, text="+100F", color=COLOR_TEMPS)
        day_temp.anchor_point = (0, 0.5)
        day_temp.anchored_position = (75, 14)

        if (forecast is not None):
            day_of_week.text = DAYS[time.localtime(forecast["dt"]).tm_wday][:3].upper()
            icon[0] = ICON_MAP.index(forecast["weather"][0]["icon"][:2])
            day_temp.text = temperature_text(forecast["temp"]["day"])

        group2 = displayio.Group(max_size=3, x=X_POS, y=Y_POS + (Y_POS_OFFSET * day))
        group2.append(day_of_week)
        group2.append(icon)
        group2.append(day_temp)
        group.append(group2)

    FEED_X_POS = 390
    FEED_Y_POS = 225
    FEED_Y_POS_OFFSET = 30
    feed0_label = label.Label(font, text="+100F", color=COLOR_FEED_DATA)
    feed0_label.anchor_point = (0, 0.5)
    feed0_label.anchored_position = (FEED_X_POS, FEED_Y_POS)
    if (t0 is not None):
        feed0_label.text = t0 + " F"
    group.append(feed0_label)

    feed1_label = label.Label(font, text="+100F", color=COLOR_FEED_DATA)
    feed1_label.anchor_point = (0, 0.5)
    feed1_label.anchored_position = (FEED_X_POS, FEED_Y_POS + FEED_Y_POS_OFFSET)
    if (t1 is not None):
        feed1_label.text = t1 + " F"
    group.append(feed1_label)

    feed2_label = label.Label(font, text="+100F", color=COLOR_FEED_DATA)
    feed2_label.anchor_point = (0, 0.5)
    feed2_label.anchored_position = (FEED_X_POS, FEED_Y_POS + FEED_Y_POS_OFFSET + FEED_Y_POS_OFFSET)
    if (t2 is not None):
        feed2_label.text = t2 + " F"
    group.append(feed2_label)

    board.DISPLAY.show(group)

# ===========
#  M A I N
# ===========
while True:
    while not esp.is_connected:
        try:
            print("Connecting to WiFi")
            esp.connect_AP(secrets["ssid"], secrets["password"])
            print("Connected to WiFi: " + secrets["ssid"])
        except RuntimeError as e:
            print("could not connect to AP, retrying: ", e)
            time.sleep(3)
            continue

    print("Getting Lat/Lon...")
    latlon = get_latlon()
    print(secrets["openweather_location"])
    print(latlon)
    gc.collect()
    print("Fetching forecast...")
    forecast_data, utc_time, local_tz_offset = get_forecast(latlon)
    gc.collect()
    print("Fetching sensor data from Adafruit IO...")
    t0, t1, t2 = get_feed_data()
    print(t0)
    print(t1)
    print(t2)
    gc.collect()
    update_display(forecast_data[0], local_tz_offset, t0, t1, t2)
    gc.collect()
    print("Sleeping...")
    #time.sleep(15)
    time.sleep(15 * 60)