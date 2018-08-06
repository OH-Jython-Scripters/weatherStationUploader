import os, time, math
import org.joda.time.DateTime as DateTime
import org.joda.time.DateTimeZone as DateTimeZone
from org.joda.time.format import DateTimeFormat

# This project on GitHUB: https://github.com/OH-Jython-Scripters/weatherStationUploader
#
# To install and use meteocalc: https://pypi.org/project/meteocalc/
# sudo pip install meteocalc && sudo ln -s /usr/local/lib/python2.7/dist-packages/meteocalc meteocalc
# Edit classutils.py, change line 5 to: PYTHON2 = 2#sys.version_info.major
from meteocalc import Temp, dew_point, heat_index

#from org.eclipse.smarthome.model.persistence.extensions import PersistenceExtensions
from lucid.rules import rule, addRule
from lucid.triggers import CronTrigger

from lucid.utils import isActive, getItemValue, getLastUpdate
wu_loop_count = 1 # Loop counter

import lucid.config as config
reload(config) # This will reload the config file when this file is saved.

@rule
class WeatherUpload(object):
    def getEventTriggers(self):
        return [
            CronTrigger(EVERY_MINUTE), # Runs every minute
        ]
    def execute(self, modules, inputs):

        SCRIPT_VERSION = '2.1'
        WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

        def ms_to_mph(input_speed):
            # convert input_speed from meter per second to miles per hour
            return round(input_speed / 0.44704, 2)

        def mm_to_inch(mm):
            # convert mm to inches
            return round(mm / 25.4, 2)

        def mbar_to_inches_mercury(input_pressure):
            # convert mbar to inches mercury
            return round(input_pressure * 0.02953, 2)

        def lux_to_watts_m2(lux):
            # Convert lux [lx] to watt/m² (at 555 nm)
            # Should typically be around 800-900 watt/m² at mid summer full sun diation at 13.00 h
            # return int(round(float(lux) * 0.01464128843))
            return int(round(float(lux) * 0.015454545))

        self.log.setLevel(self.config.wunderground['logLevel'])

        global wu_loop_count

        if (self.config.wunderground['stationdata']['weather_upload'] and wu_loop_count%self.config.wunderground['stationdata']['upload_frequency'] == 0):
            self.log.debug('Uploading data to Weather Underground')

            sdf = DateTimeFormat.forPattern("yyyy-MM-dd HH:mm:ss")
            dateutc = sdf.print(DateTime.now((DateTimeZone.UTC)))

            temp = None
            tempf = None
            if 'tempc' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['tempc'] is not None:
                temp = Temp(getItemValue(self.config.wunderground['sensors']['tempc'], 0.0), 'c') # Outdoor temp, c - celsius, f - fahrenheit, k - kelvin
                tempf = str(round(temp.f, 1))

            soiltempf = None
            if 'soiltempc' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['soiltempc'] is not None:
                _temp = Temp(getItemValue(self.config.wunderground['sensors']['soiltempc'], 0.0), 'c') # Soil temp, c - celsius, f - fahrenheit, k - kelvin
                soiltempf = str(round(_temp.f, 1))

            humidity = None
            if 'humidity' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['humidity'] is not None:
                humidity = getItemValue(self.config.wunderground['sensors']['humidity'], 0.0)

            dewptf = None
            heatidxf = None
            if 'tempc' in self.config.wunderground['sensors'] and 'humidity' in self.config.wunderground['sensors'] \
            and self.config.wunderground['sensors']['tempc'] is not None and self.config.wunderground['sensors']['humidity'] is not None:
                dewptf = str(round(dew_point(temperature=temp, humidity=humidity).f, 1)) # calculate Dew Point
                heatidxf = str(round(heat_index(temperature=temp, humidity=humidity).f, 1)) # calculate Heat Index

            pressure = None
            if 'pressurembar' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['pressurembar'] is not None:
                pressure = str(mbar_to_inches_mercury(getItemValue(self.config.wunderground['sensors']['pressurembar'], 0)))

            rainin = None
            if 'rainhour' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['rainhour'] is not None:
                rainin = str(mm_to_inch(getItemValue(self.config.wunderground['sensors']['rainhour'], 0.0)))

            dailyrainin = None
            if 'raintoday' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['raintoday'] is not None:
                dailyrainin = str(mm_to_inch(getItemValue(self.config.wunderground['sensors']['raintoday'], 0.0)))

            soilmoisture = None
            if 'soilmoisture' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['soilmoisture'] is not None:
                soilmoisture = str(int(round(getItemValue(self.config.wunderground['sensors']['soilmoisture'], 0.0) * 100 / 1023)))

            winddir = None
            if 'winddir' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['winddir'] is not None:
                winddir = str(getItemValue(self.config.wunderground['sensors']['winddir'], 0))

            windspeedmph = None
            if 'windspeedms' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['windspeedms'] is not None:
                windspeedmph = str(ms_to_mph(getItemValue(self.config.wunderground['sensors']['windspeedms'], 0.0)))

            windgustmph = None
            if 'windgustms' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['windgustms'] is not None:
                windgustmph = str(ms_to_mph(getItemValue(self.config.wunderground['sensors']['windgustms'], 0.0)))

            windgustdir = None
            if 'windgustdir' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['windgustdir'] is not None:
                windgustdir = str(getItemValue(self.config.wunderground['sensors']['windgustdir'], 0))

            windspdmph_avg2m = None
            if 'windspeedms_avg2m' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['windspeedms_avg2m'] is not None:
                windspdmph_avg2m = str(ms_to_mph(getItemValue(self.config.wunderground['sensors']['windspeedms_avg2m'], 0.0)))

            winddir_avg2m = None
            if 'winddir_avg2m' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['winddir_avg2m'] is not None:
                winddir_avg2m = str(getItemValue(self.config.wunderground['sensors']['winddir_avg2m'], 0))

            windgustmph_10m = None
            if 'windgustms_10m' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['windgustms_10m'] is not None:
                windgustmph_10m = str(ms_to_mph(getItemValue(self.config.wunderground['sensors']['windgustms_10m'], 0.0)))

            windgustdir_10m = None
            if 'windgustdir_10m' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['windgustdir_10m'] is not None:
                windgustdir_10m = str(getItemValue(self.config.wunderground['sensors']['windgustdir_10m'], 0))

            solarradiation = None
            if 'solarradiation' in self.config.wunderground['sensors'] and self.config.wunderground['sensors']['solarradiation'] is not None:
                solarradiation = str(lux_to_watts_m2(getItemValue(self.config.wunderground['sensors']['solarradiation'], 0)))

            # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol

            cmd = 'curl -s -G "' + WU_URL + '" ' \
                + '--data-urlencode "action=updateraw" ' \
                + '--data-urlencode "ID='+self.config.wunderground['stationdata']['station_id']+'" ' \
                + '--data-urlencode "PASSWORD='+self.config.wunderground['stationdata']['station_key']+'" ' \
                + '--data-urlencode "dateutc='+dateutc+'" ' \
                + '--data-urlencode "softwaretype=openHAB" '
            self.log.debug("")
            self.log.debug("Below are the weather data that we will send:")
            if tempf is not None:
                cmd += '--data-urlencode "tempf='+tempf+'" '
                self.log.debug("tempf: "+tempf)
            if humidity is not None:
                cmd += '--data-urlencode "humidity='+str(humidity)+'" '
                self.log.debug("humidity: "+str(humidity))
            if dewptf is not None:
                cmd += '--data-urlencode "dewptf='+dewptf+'" '
                self.log.debug("dewptf: "+dewptf)
            if heatidxf is not None:
                cmd += '--data-urlencode "heatidxf='+heatidxf+'" '
                self.log.debug("heatidxf: "+heatidxf)
            if soiltempf is not None:
                cmd += '--data-urlencode "soiltempf='+soiltempf+'" '
                self.log.debug("soiltempf: "+soiltempf)
            if soilmoisture is not None:
                cmd += '--data-urlencode "soilmoisture='+soilmoisture+'" '
                self.log.debug("soilmoisture: "+soilmoisture)
            if pressure is not None:
                cmd += '--data-urlencode "baromin='+pressure+'" '
                self.log.debug("baromin: "+pressure)
            if rainin is not None:
                cmd += '--data-urlencode "rainin='+rainin+'" '
                self.log.debug("rainin: "+rainin)
            if dailyrainin is not None:
                cmd += '--data-urlencode "dailyrainin='+dailyrainin+'" '
                self.log.debug("dailyrainin: "+dailyrainin)
            if winddir is not None:
                cmd += '--data-urlencode "winddir='+winddir+'" '
                self.log.debug("winddir: "+winddir)
            if windspeedmph is not None:
                cmd += '--data-urlencode "windspeedmph='+windspeedmph+'" '
                self.log.debug("windspeedmph: "+windspeedmph)
            if windgustmph is not None:
                cmd += '--data-urlencode "windgustmph='+windgustmph+'" '
                self.log.debug("windgustmph: "+windgustmph)
            if windgustdir is not None:
                cmd += '--data-urlencode "windgustdir='+windgustdir+'" '
                self.log.debug("windgustdir: "+windgustdir)
            if windspdmph_avg2m is not None:
                cmd += '--data-urlencode "windspdmph_avg2m='+windspdmph_avg2m+'" '
                self.log.debug("windspdmph_avg2m: "+windspdmph_avg2m)
            if winddir_avg2m is not None:
                cmd += '--data-urlencode "winddir_avg2m='+winddir_avg2m+'" '
                self.log.debug("winddir_avg2m: "+winddir_avg2m)
            if windgustmph_10m is not None:
                cmd += '--data-urlencode "windgustmph_10m='+windgustmph_10m+'" '
                self.log.debug("windgustmph_10m: "+windgustmph_10m)
            if windgustdir_10m is not None:
                cmd += '--data-urlencode "windgustdir_10m='+windgustdir_10m+'" '
                self.log.debug("windgustdir_10m: "+windgustdir_10m)
            if solarradiation is not None:
                cmd += '--data-urlencode "solarradiation='+solarradiation+'" '
                self.log.debug("solarradiation: "+solarradiation)
            cmd += ' 1>/dev/null 2>&1 &'
            self.log.debug("")
            self.log.debug('WeatherUpload version ' + SCRIPT_VERSION +', performing an upload. (loop count is: ' + str(wu_loop_count) + ')')
            self.log.debug('cmd: ' + cmd)

            os.system(cmd)
        else:
            self.log.debug('WeatherUpload version ' + SCRIPT_VERSION +', skipping upload. (loop count is: ' + str(wu_loop_count) + ')')

        if (wu_loop_count%self.config.wunderground['stationdata']['upload_frequency'] == 0):
            wu_loop_count = 0
        wu_loop_count = wu_loop_count + 1

addRule(WeatherUpload())
