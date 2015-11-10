"""
This module handles the structured data used to configure a WiFi network.
A simple binary file is used to persist the data.
The data model is quite simple: there are 3 different network configurations (bootstrap, default, current), one of them
us used for the running network, and each network configuration has attributtes (PSK, SSID).
"""


"""
 Copyright (C) 2015 Mytech Ingenieria Aplicada <http://www.mytechia.com>
 Copyright (C) 2015 Victor Sonora Pombo <victor.pombo@mytechia.com>

 This file is part of wifi_control.

 wifi_control is free software: you can redistribute it and/or modify it under the
 terms of the GNU General Public License as published by the Free
 Software Foundation, either version 3 of the License, or (at your option) any
 later version.

 wifi_control is distributed in the hope that it will be useful, but WITHOUT ANY
 WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 A PARTICULAR PURPOSE. See the GNU General Public License for more
 details.

 You should have received a copy of the GNU General Public License
 along with wifi_control. If not, see <http://www.gnu.org/licenses/>.
"""


import pickle
import os.path


__author__ = 'victor'


BOOTSTRAP = "Bootstrap"     # key for the bootstrap network configuration
CURRENT = "Current"         # key for the current network configuration
DEFAULT = "Default"         # key for the default network configuration

RUNNING = "Running"         # key for the running network configuration

PSK = "psk"                 # key for the PSK value
SSID = "ssid"               # key for the SSID value


class WiFiConfiguration:
    """
    Helper class that handles the whole configuration data.
    """

    def __init__(self, data):
        self.data = data

    def get_config(self, name):
        return self.data[name]

    def update_config(self, name, config):
        self.data[name] = config

    def get_running_config(self):
        return self.get_config(self.data[RUNNING])

    def set_current_config(self, config):
        self.update_config(CURRENT, config)
        self.data[RUNNING] = CURRENT


def load_wifi_configuration_from(path):
    """
    Loads the whole configuration data into a WiFiConfiguration instance.
    :param path: full path for the file that contains the persisted data.
    :return: a WiFiConfiguration instance.
    """
    config_map = pickle.load(open(path, "rb"))
    return WiFiConfiguration(config_map)


def save_wifi_configuration_to(path, wifi_configuration):
    """
    Saves the configuration data to a binary file.
    :param path: full path for the file where the data is going to be saved.
    :param wifi_configuration: a WiFiConfiguration instance with the configuration data.
    :return: nothing of consequence.
    """
    pickle.dump(wifi_configuration.data, open(path, "wb"))


def build_dumb_wifi_configurations():
    """
    Builds a map for a basic default configuration data.
    Meant for debugging, or first use.
    :return: a map with the three network configurations, running configuration set to bootstrap.
    """
    return {BOOTSTRAP: {PSK: "IAmSecured", SSID: "Luminare360HotSpot"},
            CURRENT: {PSK: "IAmSecured", SSID: "Luminare360HotSpot"},
            DEFAULT: {PSK: "IAmSecured", SSID: "Luminare360HotSpot"},
            RUNNING: BOOTSTRAP}


def check_wifi_configurations_file(path):
    """
    Checks whether a file to persist network configuration data exists.
    If not, it initializes a default network configuration data and saves it in the given path.
    :param path: full path where network configuration data should exists, or be created.
    :return: nothing.
    """
    if not os.path.exists(path):
        save_wifi_configuration_to(path, WiFiConfiguration(build_dumb_wifi_configurations()))
