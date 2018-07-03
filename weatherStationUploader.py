import os, time
import org.joda.time.DateTime as DateTime
import org.joda.time.DateTimeZone as DateTimeZone
from org.joda.time.format import DateTimeFormat
from meteocalc import Temp, dew_point, heat_index

from logging import DEBUG, INFO, WARNING, ERROR
from openhab.rules import rule, addRule
from openhab.triggers import CronTrigger

from mylib.utils import getEvent, isActive, getItemValue, getLastUpdate
wu_loop_count = 1 # Loop counter

@rule
class WeatherUpload(object):
    def getEventTriggers(self):
        return [
            CronTrigger('0 0/1 * 1/1 * ? *'), # Runs every minute
        ]
    def execute(self, modules, inputs):

        wu_station_id = 'XXXX' # Put your own station ID here
        wu_station_key = 'xxxxxxxxx' # Put your station key here
        wu_upload_frequency = 5 # Upload to WU every n minutes
        WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
        WEATHER_UPLOAD = True

        def ms_to_mph(input_speed):
            # convert input_speed from meter per second to miles per hour
            return round(input_speed / 0.44704, 2)

        def mbar_to_inches_mercury(input_pressure):
            # convert mbar to inches mercury
            return round(input_pressure * 0.02953, 2)

        def lux_to_watts_m2(lux):
            # Convert lux [lx] to watt/m² (at 555 nm)
            # Should typically be around 800-900 watt/m² at mid summer full sun radiation at 13.00 h
            # return int(round(float(lux) * 0.01464128843))
            return int(round(float(lux) * 0.015454545))

        self.log.setLevel(DEBUG)
        event = getEvent(inputs)


        global wu_loop_count
        # TODO: Do some wind data smoothening here, see http://python.hydrology-amsterdam.nl/modules/meteolib.py

        if (WEATHER_UPLOAD and wu_loop_count%wu_upload_frequency == 0):
            self.log.info('Uploading data to Weather Underground')

            sdf = DateTimeFormat.forPattern("yyyy-MM-dd HH:mm:ss")
            dateutc = sdf.print(DateTime.now((DateTimeZone.UTC)))

            t = Temp(getItemValue('YOUR_TEMP_SENSOR_ITEM_NAME', 0.0), 'c') # Outdoor temp, c - celsius, f - fahrenheit, k - kelvin
            t2 = Temp(getItemValue('YOUR_SOIL_TEMP_SENSOR_ITEM_NAME', 0.0), 'c') # Soil temp, c - celsius, f - fahrenheit, k - kelvin
            tempf = str(round(t.f, 1))
            humidity = getItemValue('YOUR_HUM_SENSOR_ITEM_NAME', 0.0)
            dewptf = str(round(dew_point(temperature=t, humidity=humidity).f, 1)) # calculate Dew Point
            heatidxf = str(round(heat_index(temperature=t, humidity=humidity).f, 1)) # calculate Heat Index
            pressure = str(mbar_to_inches_mercury(getItemValue('YOUR_BAR_SENSOR_ITEM_NAME', 0)))
            soiltempf = str(round(t2.f, 1))
            soilmoisture = str(int(round(getItemValue('YOUR_PLANT_MOISTURE_SENSOR_ITEM_NAME', 0.0) * 100 / 1023)))
            winddir = str(getItemValue('YOUR_WIND_DIRECTION_SENSOR_ITEM_NAME', 0))
            windspeedmph = str(ms_to_mph(getItemValue('YOUR_WIND_SPEED_SENSOR_ITEM_NAME', 0.0)))
            windgustmph = str(ms_to_mph(getItemValue('YOUR_WIND_GUST_SENSOR_ITEM_NAME', 0.0)))

            maxLux = max(getItemValue('YOUR_LUX_SENSOR_ITEM_NAME_1', 0), getItemValue('YOUR_LUX_SENSOR_ITEM_NAME_2', 0))
            solarradiation = str(lux_to_watts_m2(maxLux))

            #windgustdir = getItemValue('YOUR_WIND_GUST_SENSOR_ITEM_NAME', 0)
            #windspdmph_avg2m = getItemValue('YOUR_WIND_SPEED_AVG2M_SENSOR_ITEM_NAME', 0.0)
            #winddir_avg2m = getItemValue('YOUR_WIND_DIR_AVG2M_SENSOR_ITEM_NAME', 0.0)
            #windgustmph_10m = getItemValue('YOUR_WIND_GUST_AVG10M_SENSOR_ITEM_NAME', 0.0)
            #windgustdir_10m = getItemValue('YOUR_WIND_DIR_AVG10M_SENSOR_ITEM_NAME', 0.0)

            # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol

            # Adjust the command below to use only the sensor data that you have in your system

            cmd = 'curl -s -G "' + WU_URL + '" ' \
                + '--data-urlencode "action=updateraw" ' \
                + '--data-urlencode "ID='+wu_station_id+'" ' \
                + '--data-urlencode "PASSWORD='+wu_station_key+'" ' \
                + '--data-urlencode "dateutc='+dateutc+'" ' \
                + '--data-urlencode "softwaretype=openHAB" ' \
                + '--data-urlencode "tempf='+tempf+'" ' \
                + '--data-urlencode "humidity='+str(humidity)+'" ' \
                + '--data-urlencode "dewptf='+dewptf+'" ' \
                + '--data-urlencode "heatidxf='+heatidxf+'" ' \
                + '--data-urlencode "soiltempf='+soiltempf+'" ' \
                + '--data-urlencode "soilmoisture='+soilmoisture+'" ' \
                + '--data-urlencode "baromin='+pressure+'" ' \
                + '--data-urlencode "winddir='+winddir+'" ' \
                + '--data-urlencode "windspeedmph='+windspeedmph+'" ' \
                + '--data-urlencode "windgustmph='+windgustmph+'" ' \
                + '--data-urlencode "solarradiation='+solarradiation+'" ' \
                + ' > /dev/null'

            self.log.debug('cmd: ' + cmd)

            os.system(cmd)
        else:
            self.log.debug('Skipping Weather Underground upload. (loop count is: ' + str(wu_loop_count) + ')')

        if (wu_loop_count%wu_upload_frequency == 0):
            wu_loop_count = 0
        wu_loop_count = wu_loop_count + 1

addRule(WeatherUpload())
