"""
Utilities class for cross-script functionality
"""
import json


def load_config_data():
    with open('config.json', 'r') as config_file:
        json_data = config_file.read()

    return json.loads(json_data)