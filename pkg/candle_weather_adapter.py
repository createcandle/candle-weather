"""Candle Weather adapter for Candle Controller / WebThings Gateway."""

import os
from os import path
import sys
sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'lib'))

import time
from time import sleep

import json

from gateway_addon import Adapter, Device, Property, Action, Database

from .util import *

import urllib.request

_TIMEOUT = 3

_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))


class CandleWeatherAdapter(Adapter):
    """Adapter for Candle Weather"""

    def __init__(self, verbose=True):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """
        print("Initialising CandleWeather")
        self.pairing = False
        self.name = self.__class__.__name__
        self.addon_name = 'candle-weather'
        Adapter.__init__(self, 'candle-weather', 'candle-weather', verbose=verbose)
        #print("Adapter ID = " + self.get_id())

        self.addon_path = os.path.join(self.user_profile['addonsDir'], self.addon_name)

        self.DEBUG = True
        self.first_request_done = False
        self.running = True
        
        self.interval = 3600 # 1 hour is 3600 seconds
        
        self.metric = True
        self.temperature_unit = 'degree celsius'
        
        self.nearest_city = "Netherlands - Amsterdam (Schiphol)"
        self.nearest_city_code = 144 # De Bilt, NL
        
        try:
            self.add_from_config()
        except Exception as ex:
            print("Error loading config: " + str(ex))

        self.nearest_city_code = get_city_code(self.nearest_city)
        if self.DEBUG:
            print("self.nearest_city_code: " + str(self.nearest_city_code))
            
        
        try:
            candle_weather_device = CandleWeatherDevice(self)
            self.handle_device_added(candle_weather_device)
            self.devices['candle-weather-today'].connected = True
            self.devices['candle-weather-today'].connected_notify(True)
            self.thing = self.get_device("candle-weather-today")
        except Exception as ex:
            print("Error creating thing: " + str(ex))
            
        try:
            candle_tomorrow_device = CandleTomorrowDevice(self)
            self.handle_device_added(candle_tomorrow_device)
            self.devices['candle-weather-tomorrow'].connected = True
            self.devices['candle-weather-tomorrow'].connected_notify(True)
            self.tomorrow_thing = self.get_device("candle-weather-tomorrow")
        except Exception as ex:
            print("Error creating thing: " + str(ex))


        if self.DEBUG:
            print("End of CandleWeatherAdapter init process. Starting while loop.")


        # get intial weather prediction
        self.download_data(self.nearest_city_code)
        
        hour_counter = 0
        while self.running == True:
            
            if hour_counter > self.interval:
                hour_counter = 0
                if self.DEBUG:
                    print("grabbing fresh weather data. Seconds passed: " + str(self.interval))
                self.download_data(self.nearest_city_code)
            
            hour_counter += 1
            time.sleep(1)

        
        


    def download_data(self, city_code):
        
        # get current weather
        
        url = 'https://worldweather.wmo.int/en/json/present.xml'
        response = urllib.request.urlopen(url)
        data = response.read()      # a `bytes` object
        text = data.decode('utf-8') # a `str`; this step can't be used if data is binary
        current_data = json.loads(text)
        if 'present' in current_data:
            for x in current_data['present']:
                #print(x)
                try:
                    if 'cityId' in current_data['present'][x]:
                    
                        if int(current_data['present'][x]['cityId']) == int(city_code):
                            if self.DEBUG:
                                print("Found the city: " + str(current_data['present'][x]))
                
                            city_dict = current_data['present'][x]
                
                            """
                            city['temp']
                            city_dict['rh'] # rain
                            city_dict['sunrise'] # time
                            city_dict['sunset'] # time
                            city_dict['wd'] # wind direction
                            city_dict['ws'] # wind speed
                            city_dict['wxdesc'] # description, e.g. "Mist"
                            """
                
                
                            # todays weather description
                            targetProperty = self.thing.find_property('current_description')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-Today's current description property did not exist yet. Creating it now.")
                                self.thing.properties["current_description"] = CandleWeatherProperty(
                                                self.thing,
                                                "current_direction",
                                                {
                                                    "label": "Description",
                                                    'type': 'string',
                                                    'readOnly': True,
                                                },
                                                str(city_dict['wxdesc']))
                            
                                self.handle_device_added(self.thing)
                                targetProperty = self.thing.find_property('current_description')

                            targetProperty.update(str(city_dict['wxdesc']))
                
                
                            # todays humidity
                            targetProperty = self.thing.find_property('current_humidity')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-Today's current humidity property did not exist yet. Creating it now.")
                            
                                initial_humidity = None
                                if 'rh' in city_dict:
                                    try:
                                        initial_humidity = round(float(city_dict['rh']))
                                    except Exception as ex:
                                        print("error parsing weather humidity: " + str(ex))
                                
                                self.thing.properties["current_humidity"] = CandleWeatherProperty(
                                                self.thing,
                                                "current_humidity",
                                                {
                                                    "label": "Humidity",
                                                    'type': 'integer',
                                                    'unit': 'percent',
                                                    'readOnly': True,
                                                    'multipleOf':1,
                                                },
                                                initial_humidity)
                                            
                                self.handle_device_added(self.thing)
                                targetProperty = self.thing.find_property('current_humidity')

                            targetProperty.update(round(float(city_dict['rh'])))
                        
                        
                            # todays wind direction
                            targetProperty = self.thing.find_property('current_wind_direction')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-Today's current wind direction property did not exist yet. Creating it now.")
                                self.thing.properties["current_wind_direction"] = CandleWeatherProperty(
                                                self.thing,
                                                "current_wind_direction",
                                                {
                                                    "label": "Wind direction",
                                                    'type': 'string',
                                                    'readOnly': True,
                                                },
                                                get_long_compass(city_dict['wd']))
                            
                                self.handle_device_added(self.thing)
                                targetProperty = self.thing.find_property('current_wind_direction')

                            targetProperty.update(get_long_compass(city_dict['wd']))
                
                
                            # todays wind speed
                            targetProperty = self.thing.find_property('current_wind_speed')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-Today's current wind_speed property did not exist yet. Creating it now.")
                                self.thing.properties["current_wind_speed"] = CandleWeatherProperty(
                                                self.thing,
                                                "current_wind_speed",
                                                {
                                                    "label": "Wind speed",
                                                    'type': 'number',
                                                    'readOnly': True,
                                                    'multipleOf':0.1,
                                                },
                                                float(city_dict['ws']))
                                            
                                self.handle_device_added(self.thing)
                                targetProperty = self.thing.find_property('current_wind_speed')

                            targetProperty.update(float(city_dict['ws']))
                        
                
                            if 'sunrise' in city_dict:
                                if ":" in city_dict['sunrise']:
                                    time_parts = city_dict['sunrise'].split(":")
                            
                                    # sunrise hour
                                    targetProperty = self.thing.find_property('current_sunrise_hour')
                                    if targetProperty == None:
                                        if self.DEBUG:
                                            print("-Today's current sunrise hour property did not exist yet. Creating it now.")
                                        self.thing.properties["current_sunrise_hour"] = CandleWeatherProperty(
                                                        self.thing,
                                                        "current_sunrise_hour",
                                                        {
                                                            "label": "Sunrise hour",
                                                            'type': 'integer',
                                                            'readOnly': True,
                                                            'multipleOf':1,
                                                        },
                                                        int(time_parts[0]))
                                            
                                        self.handle_device_added(self.thing)
                                        targetProperty = self.thing.find_property('current_sunrise_hour')

                                    targetProperty.update(int(time_parts[0]))
                            
                                    # sunrise minutes
                                    targetProperty = self.thing.find_property('current_sunrise_minute')
                                    if targetProperty == None:
                                        if self.DEBUG:
                                            print("-Today's current sunrise minute property did not exist yet. Creating it now.")
                                        self.thing.properties["current_sunrise_minute"] = CandleWeatherProperty(
                                                        self.thing,
                                                        "current_sunrise_minute",
                                                        {
                                                            "label": "Sunrise minute",
                                                            'type': 'integer',
                                                            'readOnly': True,
                                                            'multipleOf':1,
                                                        },
                                                        int(time_parts[1]))
                                            
                                        self.handle_device_added(self.thing)
                                        targetProperty = self.thing.find_property('current_sunrise_minute')

                                    targetProperty.update(int(time_parts[1]))
                            
                        
                            if 'sunset' in city_dict:
                                if ":" in city_dict['sunset']:
                                    time_parts = city_dict['sunset'].split(":")
                            
                                    # sunset hour
                                    targetProperty = self.thing.find_property('current_sunset_hour')
                                    if targetProperty == None:
                                        if self.DEBUG:
                                            print("-Today's current sunset hour property did not exist yet. Creating it now.")
                                        self.thing.properties["current_sunset_hour"] = CandleWeatherProperty(
                                                        self.thing,
                                                        "current_sunset_hour",
                                                        {
                                                            "label": "Sunset hour",
                                                            'type': 'integer',
                                                            'readOnly': True,
                                                            'multipleOf':1,
                                                        },
                                                        int(time_parts[0]))
                                            
                                        self.handle_device_added(self.thing)
                                        targetProperty = self.thing.find_property('current_sunset_hour')

                                    targetProperty.update(int(time_parts[0]))
                            
                                    # sunset minutes
                                    targetProperty = self.thing.find_property('current_sunset_minute')
                                    if targetProperty == None:
                                        if self.DEBUG:
                                            print("-Today's current sunset minute property did not exist yet. Creating it now.")
                                        self.thing.properties["current_sunset_minute"] = CandleWeatherProperty(
                                                        self.thing,
                                                        "current_sunset_minute",
                                                        {
                                                            "label": "Sunset minute",
                                                            'type': 'integer',
                                                            'readOnly': True,
                                                            'multipleOf':1,
                                                        },
                                                        int(time_parts[1]))
                                            
                                        self.handle_device_added(self.thing)
                                        targetProperty = self.thing.find_property('current_sunset_minute')

                                    targetProperty.update(int(time_parts[1]))
                            
                            
                            # todays temperature
                        
                            current_temp = float(city_dict['temp'])
                            if self.metric == False:
                                current_temp = round((current_temp * 1.8) + 32 ,1) # convert to Fahrenheit
                        
                            targetProperty = self.thing.find_property('temperature')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-Today's current temperature property did not exist yet. Creating it now.")
                                self.thing.properties["temperature"] = CandleWeatherProperty(
                                                self.thing,
                                                "temperature",
                                                {
                                                    "@type": "TemperatureProperty",
                                                    "label": "Temperature",
                                                    'type': 'number',
                                                    'unit': self.temperature_unit,
                                                    'readOnly': True,
                                                    'multipleOf':0.1,
                                                },
                                                current_temp)

                                self.handle_device_added(self.thing)

                                targetProperty = self.thing.find_property('temperature')
            
                            targetProperty.update(current_temp)
                            
                            break
        
                    else:
                        if self.DEBUG:
                            print("\nno cityId in city: " + str(city_dict))
                
                except Exception as ex:
                    if self.DEBUG:
                        print("Error parsing weather data: " + str(ex))
        else:
            if self.DEBUG:
                print("Error, 'present' was not found in current weather data")
        
        
        
        # get weather predictions
        
        try:
            url = 'https://worldweather.wmo.int/en/json/' + str(city_code) + '_en.json'
            response = urllib.request.urlopen(url)
            data = response.read()      # a `bytes` object
            text = data.decode('utf-8') # a `str`; this step can't be used if data is binary
            prediction_data = json.loads(text)
            if self.DEBUG:
                print("DOWNLOADED PREDICION JSON: " + str(prediction_data))

            if 'city' in prediction_data:
                if 'forecast' in prediction_data['city']:
                    if 'forecastDay' in prediction_data['city']['forecast']:
                        if len(prediction_data['city']['forecast']['forecastDay']) > 0:

                            days_list = prediction_data['city']['forecast']['forecastDay']
        
                            # today prediction
                            today_weather_string = days_list[0]['weather']
                            today_minimum_temperature = float(days_list[0]['minTemp'])
                            today_maximum_temperature = float(days_list[0]['maxTemp'])

                            if self.metric == False:
                                today_minimum_temperature = float(days_list[0]['minTempF'])
                                today_maximum_temperature = float(days_list[0]['maxTempF'])

                            #today_added = today_minimum_temperature + today_maximum_temperature
                            #today_median_temperature = round( today_added * 2 ) / 2

                            # TODAY
        
                            # todays minimum temperature
                            targetProperty = self.thing.find_property('minimum_temperature')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-today's minimum property did not exist yet. Creating it now.")
                                self.thing.properties["minimum_temperature"] = CandleWeatherProperty(
                                                self.thing,
                                                "minimum_temperature",
                                                {
                                                    "label": "Minimum temperature",
                                                    'type': 'number',
                                                    'unit': self.temperature_unit,
                                                    'readOnly': True,
                                                    'multipleOf':0.1,
                                                },
                                                today_minimum_temperature)

                                self.handle_device_added(self.thing)
                                targetProperty = self.thing.find_property('minimum_temperature')
            
                            targetProperty.update(today_minimum_temperature)
        
        
                            # todays maximum temperature
                            targetProperty = self.thing.find_property('maximum_temperature')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-today's maximum property did not exist yet. Creating it now.")
                                self.thing.properties["maximum_temperature"] = CandleWeatherProperty(
                                                self.thing,
                                                "maximum_temperature",
                                                {
                                                    "label": "Maximum temperature",
                                                    'type': 'number',
                                                    'unit': self.temperature_unit,
                                                    'readOnly': True,
                                                    'multipleOf':0.1,
                                                },
                                                today_maximum_temperature)
                            
                                self.handle_device_added(self.thing)
                                targetProperty = self.thing.find_property('maximum_temperature')
            
                            targetProperty.update(today_maximum_temperature)


                            today_weather = "..."
                            if days_list[0]['weather'] != "":
                                today_weather = days_list[1]['weather']
        
                            # today's weather
                            targetProperty = self.thing.find_property('description')
                            if targetProperty == None:
                                if self.DEBUG:
                                    print("-today's weather property did not exist yet. Creating it now.")
                                self.thing.properties["description"] = CandleWeatherProperty(
                                                self.thing,
                                                "description",
                                                {
                                                    "label": "Weather today",
                                                    'type': 'string',
                                                    'readOnly': True
                                                },
                                                today_weather)

                                self.handle_device_added(self.thing)
                                targetProperty = self.thing.find_property('description')
        
                            targetProperty.update(today_weather)




                            if len(prediction_data['city']['forecast']['forecastDay']) > 1:
                            
                            
                                # TOMORROW
                            
                                # tomorrow prediction
                                tomorrow_weather_string = days_list[1]['weather']
                                tomorrow_minimum_temperature = float(days_list[1]['minTemp'])
                                tomorrow_maximum_temperature = float(days_list[1]['maxTemp'])
                            
                                if self.metric == False:
                                    tomorrow_minimum_temperature = float(days_list[1]['minTempF'])
                                    tomorrow_maximum_temperature = float(days_list[1]['maxTempF'])
        
                                #tomorrow_added = tomorrow_minimum_temperature + tomorrow_maximum_temperature
                                #tomorrow_median_temperature = round( tomorrow_added * 2 ) / 2
                            
                                tomorrow_weather = "..."
                                if days_list[1]['weather'] != "":
                                    tomorrow_weather = days_list[1]['weather']
            
                                # tomorrows weather
                                targetProperty = self.tomorrow_thing.find_property('weather')
                                if targetProperty == None:
                                    if self.DEBUG:
                                        print("-tomorrow's weather property did not exist yet. Creating it now.")
                                    self.tomorrow_thing.properties["weather"] = CandleWeatherProperty(
                                                    self.tomorrow_thing,
                                                    "weather",
                                                    {
                                                        "label": "Weather tomorrow",
                                                        'type': 'string',
                                                        'readOnly': True
                                                    },
                                                    tomorrow_weather)

                                    self.handle_device_added(self.tomorrow_thing)
                                    targetProperty = self.tomorrow_thing.find_property('weather')
            
                                targetProperty.update(tomorrow_weather)
                            
            
                                # tomorrows minimum temperature
                                targetProperty = self.tomorrow_thing.find_property('minimum_temperature')
                                if targetProperty == None:
                                    if self.DEBUG:
                                        print("-tomorrow's minimum temperature property did not exist yet. Creating it now.")
                                    self.tomorrow_thing.properties["minimum_temperature"] = CandleWeatherProperty(
                                                    self.tomorrow_thing,
                                                    "minimum_temperature",
                                                    {
                                                        "label": "Minimum temperature",
                                                        'type': 'number',
                                                        'unit': self.temperature_unit,
                                                        'readOnly': True,
                                                        'multipleOf':0.1,
                                                    },
                                                    tomorrow_minimum_temperature)

                                    self.handle_device_added(self.tomorrow_thing)
                                    targetProperty = self.tomorrow_thing.find_property('minimum_temperature')
            
                                targetProperty.update(tomorrow_minimum_temperature)
        
        
                                # tomorrows maximum temperature
                                targetProperty = self.tomorrow_thing.find_property('maximum_temperature')
                                if targetProperty == None:
                                    if self.DEBUG:
                                        print("-tomorrow's maximum temperature property did not exist yet. Creating it now.")
                                    self.tomorrow_thing.properties["maximum_temperature"] = CandleWeatherProperty(
                                                    self.tomorrow_thing,
                                                    "maximum_temperature",
                                                    {
                                                        "@type": "TemperatureProperty",
                                                        "label": "Maximum temperature",
                                                        'type': 'number',
                                                        'unit': self.temperature_unit,
                                                        'readOnly': True,
                                                        'multipleOf':0.1,
                                                    },
                                                    tomorrow_maximum_temperature)
                                                
                                    self.handle_device_added(self.tomorrow_thing)
                                    targetProperty = self.tomorrow_thing.find_property('maximum_temperature')
            
                                targetProperty.update(tomorrow_maximum_temperature)

            
                    else:
                        if self.DEBUG:
                            print("\nError, forecast list missing: " + str(prediction_data))
            
                else:
                    if self.DEBUG:
                        print("\nError, forecast data missing: " + str(prediction_data))
            else:
                if self.DEBUG:
                    print("'nError, city key missing in prediction data: " + str(prediction_data))
        except Exception as ex:
            if self.DEBUG:
                print("Error in second half of getting/parsing weather data: " + str(ex))
        
        if self.DEBUG:
            print("Weather update should be complete")
        
        
                
        
        

    def unload(self):
        print("Shutting down CandleWeather")
        self.running = False
        


    def remove_thing(self, device_id):
        if self.DEBUG:
            print("-----REMOVING:" + str(device_id))
        
        try:
            obj = self.get_device(device_id)        
            self.handle_device_removed(obj)  # Remove from device dictionary
            if self.DEBUG:
                print("Removed device")
        except:
            if self.DEBUG:
                print("Could not remove things from devices")
        
        return



    def add_from_config(self):
        """Attempt to add all configured devices."""
        try:
            database = Database('candle-weather')
            if not database.open():
                return

            config = database.load_config()
            database.close()
        except:
            print("Error! Failed to open settings database.")
            return

        if not config:
            print("Error loading config from database")
            return
        
        
        # Debugging
        try:
            if 'Debugging' in config:
                self.DEBUG = bool(config['Debugging'])
                if self.DEBUG:
                    print("Debugging is set to: " + str(self.DEBUG))
            else:
                self.DEBUG = False
        except:
            print("Error loading debugging preference")
            
        
        # Nearest city from dropdown
        try:
            if 'Nearest city' in config:
                self.nearest_city = str(config['Nearest city'])
                if self.DEBUG:
                    print("selected nearest city: " + str(self.nearest_city))
            else:
                if self.DEBUG:
                    print("Nearest city preference not found in settings")
                
        except Exception as ex:
            if self.DEBUG:
                print("Error with nearest city selection: " + str(ex))
            
        
        # Metric or Imperial
        try:
            if 'Metric' in config:
                self.metric = bool(config['Metric'])
                if self.metric == False:
                    self.temperature_unit = 'degree fahrenheit'
            else:
                if self.DEBUG:
                    print("metric preference was not in config")
        except Exception as ex:
            if self.DEBUG:
                print("Metric/Fahrenheit preference not found error: " + str(ex))
        
        
        # update frequency
        try:
            if 'Update frequency' in config:
                self.interval = 3600 * int(config['Update frequency'])
            else:
                if self.DEBUG:
                    print("Update prequency preference not found")
        except Exception as ex:
            if self.DEBUG:
                print("Update prequency preference not found error: " + str(ex))


#
#  DEVICES
#

class CandleWeatherDevice(Device):
    """CandleWeather device type."""

    def __init__(self, adapter):
        """
        Initialize the object.
        adapter -- the Adapter managing this device
        """

        
        Device.__init__(self, adapter, 'candle-weather-today')
        #print("Creating CandleWeather thing")
        
        self._id = 'candle-weather-today'
        self.id = 'candle-weather-today'
        self.adapter = adapter
        self._type.append('TemperatureSensor')

        self.name = 'candle-weather-today'
        self.title = 'Weather today'
        self.description = 'Candle weather data'


        if self.adapter.DEBUG: 
            print("Empty CandleWeather today thing has been created.")




class CandleTomorrowDevice(Device):
    """CandleWeather device type."""

    def __init__(self, adapter):
        """
        Initialize the object.
        adapter -- the Adapter managing this device
        """

        
        Device.__init__(self, adapter, 'candle-weather-tomorrow')
        #print("Creating CandleWeather thing")
        
        self._id = 'candle-weather-tomorrow'
        self.id = 'candle-weather-tomorrow'
        self.adapter = adapter
        self._type.append('TemperatureSensor')

        self.name = 'candle-weather-tomorrow'
        self.title = 'Weather tomorrow'
        self.description = 'Candle weather prediction'


        if self.adapter.DEBUG: 
            print("Empty CandleWeather tomorrow thing has been created.")



#
#  PROPERTY
#


class CandleWeatherProperty(Property):
    """CandleWeather property type."""

    def __init__(self, device, name, description, value):
        
        #print("incoming thing device at property init is: " + str(device))
        Property.__init__(self, device, name, description)
        
        
        self.device = device
        self.name = name
        self.title = name
        self.description = description # dictionary
        self.value = value
        self.set_cached_value(value)



    def set_value(self, value):
        #print("set_value is called on a CandleWeather property by the UI. This should not be possible in this case?")
        pass


    def update(self, value):
        
        if value != self.value:
            if self.device.adapter.DEBUG: 
                print("candle weather property: "  + str(self.title) + ", -> update to: " + str(value))
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)
        else:
            if self.device.adapter.DEBUG: 
                print("candle weather property: "  + str(self.title) + ", was already this value: " + str(value))

