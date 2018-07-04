# weatherStationUploader
Share your openHAB weather sensors data with the world!  It’s fun, rewarding, and can help others planning out their day or weekend!

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## About
This is a simple jsr223 jython script for openHAB to be used together with [Jython scripting for openHAB 2.x](https://github.com/OH-Jython-Scripters/openhab2-jython).

**weatherStationUploader** enables personal weather station owners to UPLOAD weather data in real time to Weather Underground. Every openHAB system is different so be prepared to the fact that the [weatherStationUploader.py](https://raw.githubusercontent.com/OH-Jython-Scripters/weatherStationUploader/master/weatherStationUploader.py) script will need your customization.

## openHAB Jython Scripting on Slack
OH-Jython-Scripters now has a Slack channel! It will help us to make sense of our work, and drive our efforts in Jython scripting forward. So if you are just curious, got questions, need support or just like to hang around, do not hesitate, join [**openHAB Jython Scripting on Slack**](https://join.slack.com/t/besynnerlig/shared_invite/enQtMzI3NzIyNTAzMjM1LTdmOGRhOTAwMmIwZWQ0MTNiZTU0MTY0MDk3OTVkYmYxYjE4NDE4MjcxMjg1YzAzNTJmZDM3NzJkYWU2ZDkwZmY) <--- Click link!

#### Prerequisits
* [openHAB](https://docs.openhab.org/index.html) version **2.2** or later
* [Jython scripting for openHAB 2.x](https://github.com/OH-Jython-Scripters/openhab2-jython)
* [The mylib openHAB jsr223 Jython helper library](https://github.com/OH-Jython-Scripters/mylib)
* [meteocalc](https://github.com/OH-Jython-Scripters/weatherStationUploader/blob/master/README.md#about#meteocalc%20Installation)

## meteocalc Installation
* The [meteocalc library](https://pypi.org/project/meteocalc/) is used for some calculations in the script. It must be installed and accessible from within the openHAB jsr223 environment. There might be other ways but the following was done on a ubuntu installation to achieve that. It might look different on your system.

* `sudo pip install meteocalc`
* Now, openHAB jsr223 jython must be configured to find your downloaded python libraries. There are several ways to do this. You can add a -Dpython.path=mypath1:mypath2 to the OH2 script `/etc/default/openhab2`. For example `-Dpython.path=/etc/openhab2/automation/lib/python:/usr/local/lib/python2.7/dist-packages` You can also modify the sys.path list in a Jython script that loads early (like a component script). Or as an alternative you can create a symlink like `sudo ln -s /usr/local/lib/python2.7/dist-packages/meteocalc /etc/openhab2/automation/lib/python/meteocalc` (In this example, the directory /etc/openhab2/automation/lib/python is already defined as openHAB's python library search path)
* Edit classutils.py, change line 5 to: `PYTHON2 = 2#sys.version_info.major`

## Installation
After the prerequisits are met:
* Register a new PWS (Personal Weather Station) at [Weather Underground](https://www.wunderground.com/personal-weather-station/signup). Note your station ID and station password.

* Download [lib/python/example_weatherStationConfig.json](https://raw.githubusercontent.com/OH-Jython-Scripters/weatherStationUploader/master/lib/python/example_weatherStationConfig.json), rename it and put in your python library search path. Typically the final name will be something like /etc/openhab2/automation/lib/python/weatherStationConfig.py
Edit The configuration file to reflect your own credentials and your own sensor names. Remove any sensors in the code that might be irrelevant for your site.
* Download [weatherStationUploader.py](https://raw.githubusercontent.com/OH-Jython-Scripters/weatherStationUploader/master/weatherStationUploader.py) and put it among your other jython scripts. Watch the debug output.


## Disclaimer
THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
