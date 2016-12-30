"""
This module offers an API built on top of dbus-python.
Also contains WiFiConfigurationDBUSService, a DBUS service that handles:
    * reconnect, method
    * disconnect, method
    * network configuration state change, signal
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


import dbus
import dbus.service
import wificonfiglogger


__author__ = 'victor'


def get_wpa_proxy():
    """
    Returns a proxy object for the wpa_supplicant1 *manager* object.
    """
    return dbus.SystemBus().get_object('fi.w1.wpa_supplicant1', '/fi/w1/wpa_supplicant1')


def get_wpa_instance():
    """
    Returns a wpa_supplicant1 interface instance for wpa_supplicant1.
    """
    return dbus.Interface(get_wpa_proxy(), 'fi.w1.wpa_supplicant1')


def get_wpa_properties_instance():
    """
    Returns a Properties interface instance for wpa_supplicant1.
    """
    return dbus.Interface(get_wpa_proxy(), 'org.freedesktop.DBus.Properties')


def get_network_interfaces():
    """
    Returns the managed network interfaces.
    """
    return get_wpa_properties_instance().Get('fi.w1.wpa_supplicant1', 'Interfaces')


def get_first_network_interface_proxy():
    """
    Returns the first managed wlan interface.
    """
    wlan_interface_object_path = get_network_interfaces().pop()
    return dbus.SystemBus().get_object('fi.w1.wpa_supplicant1', wlan_interface_object_path)


def get_managed_network_interface_proxy():
    """
    Returns a proxy object for the managed network interface.
    """
    return get_first_network_interface_proxy()


def get_managed_network_interface_instance():
    """
    Returns an instance of the managed network interface.
    """
    return dbus.Interface(get_managed_network_interface_proxy(), 'fi.w1.wpa_supplicant1.Interface')


def get_managed_network_interface_properties():
    """
    Returns an instance of the managed network interface.
    """
    return dbus.Interface(get_managed_network_interface_proxy(), 'org.freedesktop.DBus.Properties')


def get_managed_network_property(property_name):
    """
    Returns the value for a given property in the currently managed network interface.
    """
    return get_managed_network_interface_properties().Get('fi.w1.wpa_supplicant1.Interface', property_name)


def get_list_of_existing_networks():
    """
    Returns a list with the object paths of the existing configured networks.
    """
    return get_managed_network_property('Networks')


def get_current_network_proxy():
    """
    Returns the current active network (a network being a network configuration as used in wpa_supplicant.conf).
    """
    current_network_object_path = get_managed_network_property('CurrentNetwork')
    return dbus.SystemBus().get_object('fi.w1.wpa_supplicant1', current_network_object_path)


def get_current_network_properties():
    """
    Returns a Properties interface instance for the current active network.
    """
    return dbus.Interface(get_current_network_proxy(), 'org.freedesktop.DBus.Properties')


def get_current_network_properties_properties():
    """
    Returns the properties map for the current active network.
    """
    return dbus.Interface(
        get_current_network_proxy(),
        'org.freedesktop.DBus.Properties').Get('fi.w1.wpa_supplicant1.Network', 'Properties')


def create_new_network_properties_map(ssid, psk):
    """
    Builds a map for a new network, with the given properties.
    """
    return dbus.Dictionary({"ssid": dbus.ByteArray(ssid), "psk": dbus.String(psk)}, signature="sv")


def add_new_network(properties_map):
    """
    Adds a new network configuration and returns its assigned object path.
    """
    return get_managed_network_interface_instance().AddNetwork(properties_map)


def connect_to_network(network_object_path):
    """
    Connect to the given configured network.
    """
    get_managed_network_interface_instance().SelectNetwork(dbus.ObjectPath(network_object_path))


def disconnect():
    """
    Disconnect from current network interface.
    """
    get_managed_network_interface_instance().Disconnect()


def reconnect():
    """
    Reconnect current network interface.
    """
    get_managed_network_interface_instance().Reassociate()


def clean_configured_networks():
    """
    Remove all network configurations from current network interface.
    """
    get_managed_network_interface_instance().RemoveAllNetworks()


class WiFiConfigurationDBUSService(dbus.service.Object):
    """
    Encapsulates a DBUS service whose API handles connections to an already configured network configuration.
    It uses wpa_supplicant, as handled by the API of this module.
    """

    def __init__(self):
        bus_name = dbus.service.BusName('com.mytechia.wificonfig', bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, '/com/mytechia/wificonfig')

    @dbus.service.method('com.mytechia.wificonfig')
    def disconnect(self):
        """
        Disconnects from the currently running network configuration, handled by wpa_supplicant.
        :return:
        """
        self.signal_state_change('disconnect')
        disconnect()

    @dbus.service.method('com.mytechia.wificonfig')
    def reconnect(self):
        """
        Reattaches to the current network configuration, handled by wpa_supplicant.
        :return:
        """
        self.signal_state_change('reconnect')
        reconnect()

    @dbus.service.signal('com.mytechia.wificonfig')
    def signal_state_change(self, message):
        """
        Signals via DBUS a change in the current network configuration, as handled by wpa_supplicant.
        Signal is emitted when this method exits
        :param message:
        :return:
        """
        wificonfiglogger.get_logger().info("Signal sent: " + message)
