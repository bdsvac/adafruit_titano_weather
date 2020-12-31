#libraries: 
#  adafruit_bus_device
#  adafruit_io
#  adafruit_register
#  adafruit_requests.mpy
#  adafruit_bme680.mpy or adafruit_si7021.mpy or adafruit_tmp117.mpy

import time, gc, os
import adafruit_dotstar
import board
import ipaddress
import wifi
import socketpool
import time
import adafruit_requests
import ssl
import espidf
import busio
#import adafruit_bme680
import adafruit_tmp117
#import adafruit_si7021
from secrets import secrets
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

i2c = busio.I2C(board.SCL, board.SDA)
#sensor = adafruit_si7021.SI7021(i2c)
sensor = adafruit_tmp117.TMP117(i2c)
#sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)
#sensor.sea_level_pressure = 1013.25 # for Bme680
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]
aio_feed_name = secrets["aio_feed_name"]
ssid = secrets["ssid"]
ssid_pass = secrets["password"]
dotstar = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=0.5, auto_write=True)
color_index = 0

dotstar[0] = (0, 0, 255, 0.5)
for network in wifi.radio.start_scanning_networks():
    print(network, network.ssid, network.rssi, network.channel)
wifi.radio.stop_scanning_networks()
dotstar[0] = (0, 0, 0, 0.5)

print("try first connect")
dotstar[0] = (0, 255, 0, 0.5)
print(wifi.radio.connect(ssid, ssid_pass))
dotstar[0] = (0, 0, 0, 0.5)
print("wifi connected")
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
io = IO_HTTP(aio_username, aio_key, requests)

dotstar[0] = (255, 0, 0, 0.5)
feed = None
try:
    feed = io.get_feed(aio_feed_name)
except AdafruitIO_RequestError:
    feed = io.create_new_feed(aio_feed_name)

while True:
    try:
        dotstar[0] = (0, 0, 0, 0.5)
        t = sensor.temperature * (9.0/5.0) + 32.0
        temperature = '%.1f'%(t)

        if (wifi.radio.ap_info is None):

            dotstar[0] = (0, 255, 0, 0.5)
            for network in wifi.radio.start_scanning_networks():
                print(network, network.ssid, network.rssi, network.channel)
            wifi.radio.stop_scanning_networks()

            dotstar[0] = (255, 0, 0, 0.5)
            print("reconnecting")
            wifi.radio.connect(ssid, ssid_pass)
            print("wifi connected")

            dotstar[0] = (0, 0, 0, 0.5)
            time.sleep(8)

        if (not feed is None and not wifi.radio.ap_info is None):
            print("\nTemp: %0.1f F" % t)
            dotstar[0] = (0, 0, 255, 0.1)
            try:
                io.send_data(feed["key"], temperature)
            except:
                pass
            dotstar[0] = (0, 0, 0, 0.5)
            time.sleep(28)
    except:
        pass

    time.sleep(2)