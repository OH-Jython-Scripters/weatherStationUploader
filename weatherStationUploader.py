import os, time, math
import org.joda.time.DateTime as DateTime
import org.joda.time.DateTimeZone as DateTimeZone
from org.joda.time.format import DateTimeFormat
from org.eclipse.smarthome.model.persistence.extensions import PersistenceExtensions


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

        SCRIPT_VERSION = '2.2'
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

        def getTheSensor(lbl, never_assume_dead=False, getHighest=False):
            # Each sensor entry in the configuration file can be a a single item name or a python list where you can
            # define multiple sensor names. The first sensor in that list that has reported within the value set in
            # sensor_dead_after_mins will be used. (Unless never_assume_dead is set to True)
            # When "getHighest" argument is set to True, the sensor name with the highest value is picked.

            def isSensorAlive(sName):
                if getLastUpdate(PersistenceExtensions, ir.getItem(sName)).isAfter(DateTime.now().minusMinutes(sensor_dead_after_mins)):
                    return True
                else:
                    self.log.warning('Sensor device ' + unicode(sName) + ' has not reported since: ' + str(getLastUpdate(PersistenceExtensions, ir.getItem(sName))))
                    return False

            sensorName = None
            if lbl in self.config.wunderground['sensors'] and self.config.wunderground['sensors'][lbl] is not None:
                tSens = self.config.wunderground['sensors'][lbl]
                if isinstance(tSens, list):
                    _highestValue = 0
                    for s in tSens:
                        if s is None:
                            break
                        # Get the first sensor that is not dead and find the sensor with the highest value if specified
                        if never_assume_dead or isSensorAlive(s):
                            if getHighest:
                                _itemValue = getItemValue(s, 0)
                                if _itemValue > _highestValue:
                                    _highestValue = _itemValue
                                    sensorName = s
                            else:
                                sensorName = s
                                break
                else:
                    if never_assume_dead or isSensorAlive(tSens):
                        sensorName = tSens

            if sensorName is not None:
                self.log.debug("Device used for " + unicode(lbl) + ": " + sensorName)
            return sensorName

        self.log.setLevel(self.config.wunderground['logLevel'])

        global wu_loop_count
        sensor_dead_after_mins = self.config.wunderground['sensor_dead_after_mins'] # The time after which a sensor is presumed to be dead
        if (not self.config.wunderground['stationdata']['weather_upload']) \
        or (self.config.wunderground['stationdata']['weather_upload'] and wu_loop_count%self.config.wunderground['stationdata']['upload_frequency'] == 0):
            if self.config.wunderground['stationdata']['weather_upload']:
                self.log.debug('Uploading data to Weather Underground')
            else:
                self.log.debug('No data to will be upladed to Weather Underground')

            sdf = DateTimeFormat.forPattern("yyyy-MM-dd HH:mm:ss")
            dateutc = sdf.print(DateTime.now((DateTimeZone.UTC)))

            tempf = None
            temp = None
            sensorName = getTheSensor('tempc')
            if sensorName is not None:
                temp = Temp(getItemValue(sensorName, 0.0), 'c') # Outdoor temp, c - celsius, f - fahrenheit, k - kelvin
                tempf = str(round(temp.f, 1))

            soiltempf = None
            sensorName = getTheSensor('soiltempc')
            if sensorName is not None:
                _temp = Temp(getItemValue(sensorName, 0.0), 'c') # Soil temp, c - celsius, f - fahrenheit, k - kelvin
                soiltempf = str(round(_temp.f, 1))

            humidity = None
            sensorName = getTheSensor('humidity')
            if sensorName is not None:
                humidity = getItemValue(sensorName, 0.0)

            dewptf = None
            heatidxf = None
            if humidity is not None and temp is not None:
                dewptf = str(round(dew_point(temperature=temp, humidity=humidity).f, 1)) # calculate Dew Point
                heatidxf = str(round(heat_index(temperature=temp, humidity=humidity).f, 1)) # calculate Heat Index

            pressure = None
            sensorName = getTheSensor('pressurembar')
            if sensorName is not None:
                pressure = str(mbar_to_inches_mercury(getItemValue(sensorName, 0)))

            rainin = None
            sensorName = getTheSensor('rainhour', never_assume_dead=True)
            if sensorName is not None:
                rainin = str(mm_to_inch(getItemValue(sensorName, 0.0)))

            dailyrainin = None
            sensorName = getTheSensor('raintoday', never_assume_dead=True)
            if sensorName is not None:
                dailyrainin = str(mm_to_inch(getItemValue(sensorName, 0.0)))

            soilmoisture = None
            sensorName = getTheSensor('soilmoisture')
            if sensorName is not None:
                soilmoisture = str(int(round(getItemValue(sensorName, 0.0) * 100 / 1023)))

            winddir = None
            sensorName = getTheSensor('winddir')
            if sensorName is not None:
                winddir = str(getItemValue(sensorName, 0))

            windspeedmph = None
            sensorName = getTheSensor('windspeedms')
            if sensorName is not None:
                windspeedmph = str(ms_to_mph(getItemValue(sensorName, 0.0)))

            windgustmph = None
            sensorName = getTheSensor('windgustms')
            if sensorName is not None:
                windgustmph = str(ms_to_mph(getItemValue(sensorName, 0.0)))

            windgustdir = None
            sensorName = getTheSensor('windgustdir')
            if sensorName is not None:
                windgustdir = str(getItemValue(sensorName, 0))

            windspdmph_avg2m = None
            sensorName = getTheSensor('windspeedms_avg2m')
            if sensorName is not None:
                windspdmph_avg2m = str(ms_to_mph(getItemValue(sensorName, 0.0)))

            winddir_avg2m = None
            sensorName = getTheSensor('winddir_avg2m')
            if sensorName is not None:
                winddir_avg2m = str(getItemValue(sensorName, 0))

            windgustmph_10m = None
            sensorName = getTheSensor('windgustms_10m')
            if sensorName is not None:
                windgustmph_10m = str(ms_to_mph(getItemValue(sensorName, 0.0)))

            windgustdir_10m = None
            sensorName = getTheSensor('windgustdir_10m')
            if sensorName is not None:
                windgustdir_10m = str(getItemValue(sensorName, 0))

            solarradiation = None
            sensorName = getTheSensor('solarradiation', getHighest=True)
            if sensorName is not None:
                solarradiation = str(lux_to_watts_m2(getItemValue(sensorName, 0)))

            # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol

            cmd = 'curl -s -G "' + WU_URL + '" ' \
                + '--data-urlencode "action=updateraw" ' \
                + '--data-urlencode "ID='+self.config.wunderground['stationdata']['station_id']+'" ' \
                + '--data-urlencode "PASSWORD='+self.config.wunderground['stationdata']['station_key']+'" ' \
                + '--data-urlencode "dateutc='+dateutc+'" ' \
                + '--data-urlencode "softwaretype=openHAB" '
            self.log.debug("")

            if self.config.wunderground['stationdata']['weather_upload']:
                self.log.debug("Below is the weather data that we will send:")
            else:
                self.log.debug("Below is the weather data that we would send (if weather_upload was enabled):")

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

            if self.config.wunderground['stationdata']['weather_upload']:
                self.log.debug('WeatherUpload version ' + SCRIPT_VERSION +', performing an upload. (loop count is: ' + str(wu_loop_count) + ')')
                self.log.debug('cmd: ' + cmd)
                os.system(cmd)
        else:
            self.log.debug('WeatherUpload version ' + SCRIPT_VERSION +', skipping upload. (loop count is: ' + str(wu_loop_count) + ')')

        if (wu_loop_count%self.config.wunderground['stationdata']['upload_frequency'] == 0):
            wu_loop_count = 0
        wu_loop_count = wu_loop_count + 1

addRule(WeatherUpload())
