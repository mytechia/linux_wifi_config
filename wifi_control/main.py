#!/usr/bin/env python
# coding: utf-8


"""
Launcher for the WiFiConfig component. Based on wpa_supplicant service, and DBUS.
The main loop handles:
    * checking existing database (handler in a single binary file) for network configurations data.
    * cleaning the network configurations previously handled by wpa_supplicant.
    * connects to a network whose configuration is provided by the network configurations data.
    * launches a DBUS service that offers simple access to the current running network configuration.
    * launches a worker thread that listens via UDP for Luminare Configuration messages
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


import socket
import fcntl
import struct
import time

from dbus.mainloop.glib import DBusGMainLoop

if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    print "Default main loop set"

import wifiwpadbus, simplemessageprotocol, wificonfiguration

__author__ = 'victor'


FILE_NAME = "/tmp/wifi_data.p"   # name for the file used to persist configuration data


def process_configuration(wifi_configuration):
    """
    Connects to the provided network configuration.
    And stores that network configuration in the network configuration data handled.
    :param wifi_configuration:
    :return:
    """
    print "Processing new network configuration: " + str(wifi_configuration)
    wifi_configurations = wificonfiguration.load_wifi_configuration_from(FILE_NAME)
    if wifi_configuration[wificonfiguration.SSID] != (wifi_configurations.get_running_config())[wificonfiguration.SSID]:
        wifi_configurations.set_current_config(wifi_configuration)
        new_network_object_path = \
            wifiwpadbus.add_new_network(
                wifiwpadbus.create_new_network_properties_map(
                    wifi_configuration[wificonfiguration.SSID],
                    wifi_configuration[wificonfiguration.PSK]))
        wifiwpadbus.connect_to_network(new_network_object_path)
        wificonfiguration.save_wifi_configuration_to(FILE_NAME, wifi_configurations)


def connect():
    """
    Connects to the previously set network configuration.
    Assumption: the network configurations data has already been persisted.
    :return: nothing.
    """
    wifi_configuration = wificonfiguration.load_wifi_configuration_from(FILE_NAME)
    running_configuration = wifi_configuration.get_running_config()
    new_network_object_path = \
        wifiwpadbus.add_new_network(
            wifiwpadbus.create_new_network_properties_map(
                running_configuration[wificonfiguration.SSID],
                running_configuration[wificonfiguration.PSK]))
    wifiwpadbus.connect_to_network(new_network_object_path)


def get_ip_address(ifname):
    """
    Simple (ahem) method to obtain the assigned IP address for a given network interface.
    :param ifname: name of a used network interface (i.e. "wlan0")
    :return: an IP address, as a String
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


if __name__ == '__main__':
    wificonfiguration.check_wifi_configurations_file(FILE_NAME)
    print "Configurations checked"
    wifiwpadbus.clean_configured_networks()
    print "Rebooting current network configurations"
    connect()
    print "Network interface has been configured"
    while "completed" != wifiwpadbus.get_managed_network_property('State'):
        print "Waiting to complete connection..."
        time.sleep(1)
    print "Connection completed"
    service = wifiwpadbus.WiFiConfigurationDBUSService()
    print "WiFiConfigurationDBUSService initialized"
    ip = get_ip_address(wifiwpadbus.get_managed_network_property('Ifname').__str__())
    configurator_listener = simplemessageprotocol.WifiConfigurationMessageListener(ip, process_configuration)
    print "Launching listener for ip: " + ip
    configurator_listener.start()
