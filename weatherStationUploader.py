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
from logging import DEBUG, INFO, WARNING, ERROR
from lucid.rules import rule, addRule
from lucid.triggers import CronTrigger

from lucid.utils import getEvent, isActive, getItemValue, getLastUpdate
wu_loop_count = 1 # Loop counter

import lucid.config as config

@rule
class WeatherUpload(object):
    def getEventTriggers(self):
        return [
            CronTrigger('0 0/1 * 1/1 * ? *'), # Runs every minute
        ]
    def execute(self, modules, inputs):

        SCRIPT_VERSION = '1.0'
        WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

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

        def windvec(u, D):
            '''
            NEW FUNCTION, Still not in use.
            Function to calculate the wind vector from time series of wind
            speed and direction.
            
            Parameters:
                - u: array of wind speeds [m s-1].
                - D: array of wind directions [degrees from North].
                
            Returns:
                - uv: Vector wind speed [m s-1].
                - Dv: Vector wind direction [degrees from North].
                
            Examples
            --------
            
                >>> u = [3, 7.5, 2.1]
                >>> D = [340, 356, 2]
                >>> uv, Dv = windvec(u,D)
                >>> uv
                4.162354202836905
                >>> Dv
                array([ 353.2118882])
            '''

            ve = 0.0 # define east component of wind speed
            vn = 0.0 # define north component of wind speed
            D = D * math.pi / 180.0 # convert wind direction degrees to radians
            for i in range(0, len(u)):
                ve = ve + u[i] * math.sin(D[i]) # calculate sum east speed components
                vn = vn + u[i] * math.cos(D[i]) # calculate sum north speed components
            ve = - ve / len(u) # determine average east speed component
            vn = - vn / len(u) # determine average north speed component
            uv = math.sqrt(ve * ve + vn * vn) # calculate wind speed vector magnitude
            # Calculate wind speed vector direction
            vdir = math.atan2(ve, vn) # ORIGINALLY scipy.arctan2(ve, vn) # Funkar nog...
            vdir = vdir * 180.0 / math.pi # Convert radians to degrees
            if vdir < 180:
                Dv = vdir + 180.0
            else:
                if vdir > 180.0:
                    Dv = vdir - 180
                else:
                    Dv = vdir
            return uv, Dv # uv in m/s, Dv in dgerees from North


        self.log.setLevel(DEBUG)
        event = getEvent(inputs)

        global wu_loop_count

        if (config.wunderground['stationdata']['weather_upload'] and wu_loop_count%config.wunderground['stationdata']['upload_frequency'] == 0):
            self.log.info('Uploading data to Weather Underground')

            sdf = DateTimeFormat.forPattern("yyyy-MM-dd HH:mm:ss")
            dateutc = sdf.print(DateTime.now((DateTimeZone.UTC)))

            temp = None
            tempf = None
            if 'tempc' in config.wunderground['sensors']:
                temp = Temp(getItemValue(config.wunderground['sensors']['tempc'], 0.0), 'c') # Outdoor temp, c - celsius, f - fahrenheit, k - kelvin
                tempf = str(round(temp.f, 1))

            soiltempf = None
            if 'soiltempc' in config.wunderground['sensors']:
                _temp = Temp(getItemValue(config.wunderground['sensors']['soiltempc'], 0.0), 'c') # Soil temp, c - celsius, f - fahrenheit, k - kelvin
                soiltempf = str(round(_temp.f, 1))

            humidity = None
            if 'humidity' in config.wunderground['sensors']:
                humidity = getItemValue(config.wunderground['sensors']['humidity'], 0.0)

            dewptf = None
            heatidxf = None
            if 'tempc' in config.wunderground['sensors'] and 'humidity' in config.wunderground['sensors']:
                dewptf = str(round(dew_point(temperature=temp, humidity=humidity).f, 1)) # calculate Dew Point
                heatidxf = str(round(heat_index(temperature=temp, humidity=humidity).f, 1)) # calculate Heat Index

            pressure = None
            if 'pressurembar' in config.wunderground['sensors']:
                pressure = str(mbar_to_inches_mercury(getItemValue(config.wunderground['sensors']['pressurembar'], 0)))

            soilmoisture = None
            if 'soilmoisture' in config.wunderground['sensors']:
                soilmoisture = str(int(round(getItemValue(config.wunderground['sensors']['soilmoisture'], 0.0) * 100 / 1023)))

            winddir = None
            if 'winddir' in config.wunderground['sensors']:
                winddir = str(getItemValue(config.wunderground['sensors']['winddir'], 0))

            windspeedmph = None
            if 'windspeedms' in config.wunderground['sensors']:
                windspeedmph = str(ms_to_mph(getItemValue(config.wunderground['sensors']['windspeedms'], 0.0)))

            windgustmph = None
            if 'windgustms' in config.wunderground['sensors']:
                windgustmph = str(ms_to_mph(getItemValue(config.wunderground['sensors']['windgustms'], 0.0)))

            solarradiation = None
            if 'solarradiation' in config.wunderground['sensors']:
                solarradiation = str(getItemValue(config.wunderground['sensors']['solarradiation'], 0))

            # TODO:
            #windgustdir = 
            #windspdmph_avg2m = 
            #winddir_avg2m = 
            #windgustmph_10m = 
            #windgustdir_10m = 

            # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol

            cmd = 'curl -s -G "' + WU_URL + '" ' \
                + '--data-urlencode "action=updateraw" ' \
                + '--data-urlencode "ID='+config.wunderground['stationdata']['station_id']+'" ' \
                + '--data-urlencode "PASSWORD='+config.wunderground['stationdata']['station_key']+'" ' \
                + '--data-urlencode "dateutc='+dateutc+'" ' \
                + '--data-urlencode "softwaretype=openHAB" '
            if tempf is not None: cmd += '--data-urlencode "tempf='+tempf+'" '
            if humidity is not None: cmd += '--data-urlencode "humidity='+str(humidity)+'" '
            if dewptf is not None: cmd += '--data-urlencode "dewptf='+dewptf+'" '
            if heatidxf is not None: cmd += '--data-urlencode "heatidxf='+heatidxf+'" '
            if soiltempf is not None: cmd += '--data-urlencode "soiltempf='+soiltempf+'" '
            if soilmoisture is not None: cmd += '--data-urlencode "soilmoisture='+soilmoisture+'" '
            if pressure is not None: cmd += '--data-urlencode "baromin='+pressure+'" '
            if winddir is not None: cmd += '--data-urlencode "winddir='+winddir+'" '
            if windspeedmph is not None: cmd += '--data-urlencode "windspeedmph='+windspeedmph+'" '
            if windgustmph is not None: cmd += '--data-urlencode "windgustmph='+windgustmph+'" '
            if solarradiation is not None: cmd += '--data-urlencode "solarradiation='+solarradiation+'" '
            cmd += ' > /dev/null'

            self.log.debug('WeatherUpload version ' + SCRIPT_VERSION +', performing an upload. (loop count is: ' + str(wu_loop_count) + ')')
            self.log.debug('cmd: ' + cmd)

            os.system(cmd)
        else:
            self.log.debug('WeatherUpload version ' + SCRIPT_VERSION +', skipping upload. (loop count is: ' + str(wu_loop_count) + ')')

        if (wu_loop_count%config.wunderground['stationdata']['upload_frequency'] == 0):
            wu_loop_count = 0
        wu_loop_count = wu_loop_count + 1

addRule(WeatherUpload())
