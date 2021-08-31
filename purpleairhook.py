"""
Class to interface with the PurpleAir API
"""
import utilities
import requests
import json

# Config keys
purpleair_read_config_key = 'purpleair-read-key'
purpleair_write_config_key = 'purpleair-write-key'
purpleair_nwlat_config_key = 'purpleair-nwlat'
purpleair_nwlng_config_key = 'purpleair-nwlng'
purpleair_selat_config_key = 'purpleair-selat'
purpleair_selng_config_key = 'purpleair-selng'

# Endpoints
purpleair_sensors_endpoint = 'https://api.purpleair.com/v1/sensors'

# Breakpoint map for pollutant type
# Maps pollutant to the AQI breakpoint chart as defined in
# https://forum.airnowtech.org/t/the-aqi-equation/169
# Each tuple is (Conc_low, Conc_hi, AQI_low, AQI_hi) for the category
breakpoint_map = {
    "pm2.5": [(0.0, 12.0, 0, 50),
              (12.1, 35.4, 51, 100),
              (35.5, 55.4, 101, 150),
              (55.5, 150.4, 151, 200),
              (150.5, 250.4, 201, 300),
              (250.5, 500.4, 301, 500)],
    "pm10.0": [(0, 54, 0, 50),
             (55, 154, 51, 100),
             (155, 254, 101, 150),
             (255, 354, 151, 200),
             (355, 424, 201, 300),
             (425, 604, 301, 500)],
    "o3": [(0.000, 0.054, 0, 50),
           (0.055, 0.070, 51, 100),
           (0.071, 0.085, 101, 150),
           (0.086, 0.105, 151, 200),
           (0.106, 0.200, 201, 300)]
}


def get_aqi_value(pollutant_type, conc_input):
    """
    Formula for each pollutant type is
       AQI_input = [(AQI_hi - AQI_low)/(Conc_hi - Conc_low)]*(Conc_input - Conc_low) + AQI_low
       Where
       AQI_input is the AQI of the input pollutant type
       Conc_input is the concentration value currently being measured
       Conc_hi is the concentration value at a breakpoint above the input concentration
       Conc_low is the concentration value at the breakpoint below the input concentration
       AQI_high is the AQI value corresponding to the high breakpoint
       AQI_low is the AQI value corresponding to the low breakpoint
    """
    aqi_value = None
    if pollutant_type in breakpoint_map:
        pollutant_table = breakpoint_map[pollutant_type]
        for conc_low, conc_high, aqi_low, aqi_hi in pollutant_table:
            if conc_low <= conc_input <= conc_high:
                aqi_value = ((aqi_hi - aqi_low)/(conc_high - conc_low))*(conc_input - conc_low) + aqi_low
                break
    else:
        print("Pollutant isn't present")
        aqi_value = 0

    if aqi_value is None:
        # We went beyond the scale, peg to the highest AQI
        if pollutant_type == 'o3':
            aqi_value = 300
        else:
            aqi_value = 500

    return aqi_value


class PurpleAirHook:
    def __init__(self, config_dict=None):
        self.config_dict = config_dict
        if config_dict is None:
            self.config_dict = utilities.load_config_data()
        self.read_key = self.config_dict[purpleair_read_config_key]
        self.write_key = self.config_dict[purpleair_write_config_key]

    ''' https://api.purpleair.com/v1/sensors '''
    def get_bounded_sensors_data(self):
        request_payload = {'fields': 'name,pm2.5',
                           'nwlng': self.config_dict[purpleair_nwlng_config_key],
                           'nwlat': self.config_dict[purpleair_nwlat_config_key],
                           'selng': self.config_dict[purpleair_selng_config_key],
                           'selat': self.config_dict[purpleair_selat_config_key]}
        request_header = {'X-API-Key': self.config_dict[purpleair_read_config_key]}
        return requests.get(purpleair_sensors_endpoint, headers=request_header, params=request_payload)


if __name__ == '__main__':
    purple_air_hook = PurpleAirHook()
    response = purple_air_hook.get_bounded_sensors_data()
    json_response = json.loads(response.text)
    print(json_response)
    response_data = json_response["data"]
    aqi_values = []
    for item in response_data:
        aqi = get_aqi_value('pm2.5', item[2])
        print(aqi)
        aqi_values.append(aqi)

    aqi_values.sort()
    print(aqi_values)
    filter_values = aqi_values[1:-1]
    print(filter_values)
    averaged_aqi = sum(filter_values)/len(filter_values)
    print(averaged_aqi)

