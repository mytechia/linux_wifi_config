#!/usr/bin/env python
# coding: utf-8


"""
Launcher for the WiFiConfig component. Based on wpa_supplicant service, and DBUS.
The main loop handles:
    * checking existing database (data stored in a single binary file) for network configurations data.
    * cleaning the network configurations previously handled by wpa_supplicant.
    * connects to a network whose configuration is provided by the network configurations data.
    * launches a DBUS service that offers simple access to the current running network configuration.
    * launches a worker thread that listens via UDP for Luminare Configuration messages.
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
import sys
import wifiwpadbus, simplemessageprotocol, wificonfiguration, wificonfiglogger

__author__ = 'victor'


NUMBER_OF_BOOTSTRAP_CONNECTION_TRIES = 15


def process_configuration(wifi_configuration, data_file_name):
    """
    Connects to the provided network configuration.
    And stores that network configuration in the network configuration data handled.
    :param wifi_configuration:
    :return:
    """
    wificonfiglogger.get_logger().info("Processing network configuration: " + str(wifi_configuration))
    wifi_configurations = wificonfiguration.load_wifi_configuration_from(data_file_name)
    if wifi_configuration[wificonfiguration.SSID] != (wifi_configurations.get_running_config())[wificonfiguration.SSID]:
        wifi_configurations.set_current_config(wifi_configuration)
        wificonfiguration.save_wifi_configuration_to(data_file_name, wifi_configurations)
    new_network_object_path = \
            wifiwpadbus.add_new_network(
                wifiwpadbus.create_new_network_properties_map(
                    wifi_configuration[wificonfiguration.SSID],
                    wifi_configuration[wificonfiguration.PSK]))
    wifiwpadbus.connect_to_network(new_network_object_path)


def connect_to_bootstrap(data_file_name):
    """
    Connects to the bootstrap network configuration.
    Assumption: the network configurations data has already been persisted.
    :return: nothing.
    """
    wifi_configuration = wificonfiguration.load_wifi_configuration_from(data_file_name)
    bootstrap_configuration = wifi_configuration.get_bootstrap_config()
    wificonfiglogger.get_logger().info("Trying to connect to: " + bootstrap_configuration[wificonfiguration.SSID])
    new_network_object_path = \
        wifiwpadbus.add_new_network(
            wifiwpadbus.create_new_network_properties_map(
                bootstrap_configuration[wificonfiguration.SSID],
                bootstrap_configuration[wificonfiguration.PSK]))
    wifiwpadbus.connect_to_network(new_network_object_path)


def connect_to_current(data_file_name):
    """
    Connects to the previously set current network configuration.
    Assumption: the network configurations data has already been persisted.
    :return: nothing.
    """
    wifi_configuration = wificonfiguration.load_wifi_configuration_from(data_file_name)
    running_configuration = wifi_configuration.get_running_config()
    wificonfiglogger.get_logger().info("Trying to connect to: " + running_configuration[wificonfiguration.SSID])
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


def wait_for_connection(number_of_tries):
    connection_try_number = 0
    while "completed" != wifiwpadbus.get_managed_network_property('State') and connection_try_number < number_of_tries:
        connection_try_number += 1
        time.sleep(1)
    if connection_try_number < number_of_tries:
        return True
    else:
        return False


def main():
    if len(sys.argv) != 3:
        print 'This module needs 2 arguments: DATA_FILE_NAME, LOG_FILE_NAME'
    data_file_name = sys.argv[1]
    log_file_name = sys.argv[2]
    logger = wificonfiglogger.initialize_logger(log_file_name)
    wificonfiguration.check_wifi_configurations_file(data_file_name)
    logger.info("Configurations checked")
    wifiwpadbus.clean_configured_networks()
    logger.info("Trying bootstrap network configuration")
    connect_to_current(data_file_name)

    connected = wait_for_connection(NUMBER_OF_BOOTSTRAP_CONNECTION_TRIES)
    if connected:
        logger.info("Connection to last current completed")
    else:
        while not connected:
            logger.info("Trying bootstrap network configuration")
            connect_to_current(data_file_name)
            connected = wait_for_connection(NUMBER_OF_BOOTSTRAP_CONNECTION_TRIES)

    logger.info("Connection to bootstrap completed")
    time.sleep(5)
    service = wifiwpadbus.WiFiConfigurationDBUSService()
    logger.info("WiFiConfigurationDBUSService initialized for: " + wifiwpadbus.get_managed_network_property('Ifname').__str__())
    ip = get_ip_address(wifiwpadbus.get_managed_network_property('Ifname').__str__())
    configurator_listener = simplemessageprotocol.WifiConfigurationMessageListener(ip, process_configuration, data_file_name)
    logger.info("Launching listener for ip: " + ip)
    configurator_listener.start()
