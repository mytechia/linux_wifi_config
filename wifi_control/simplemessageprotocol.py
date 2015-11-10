"""
This module handles how to receive Luminare Simple Message Protocol messages.
Currently supports Configuration messages.
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
import time
import threading

import wificonfiguration

__author__ = 'victor'


LUMINARE_PROTOCOL_UDP_PORT = 29000              # default port used for Simple Message Protocol communications
LUMINARE_PROTOCOL_CONFIGURATION_MSG_TYPE = 9    # value for Luminare Configuration Message type
LUMINARE_PROTOCOL_COMMAND_HEADER_SIZE = 8       # size of Simple Message Protocol header

OK = "OK"


def process_unidentified_message(something):
    """
    Dumb function used to debug the processing of messages.
    :param something: chunk of data to process.
    :return: an OK String.
    """
    print something
    return OK


def process_luminare_360_config_message(msg_data):
    """
    Process a Simple Message Protocol message.
    Only valid for LUMINARE PROTOCOL CONFIGURATION messages.
    :param msg_data: a chunk of data bytes, the full Luminare Configuration message.
    :return: a data map with SSID and PSK for the received network configuration.
    """
    index = LUMINARE_PROTOCOL_COMMAND_HEADER_SIZE
    ssid_len = ord(msg_data[index])
    index += 2  # ssid_len 2 bytes
    ssid_bytes = msg_data[index:index + ssid_len]
    index += ssid_len
    index += 1  # ssid_escape character
    password_len = ord(msg_data[index])
    index += 2  # password len 2 bytes
    password_bytes = msg_data[index:index + password_len]
    return {wificonfiguration.SSID: ssid_bytes.decode("utf-8"),
            wificonfiguration.PSK: password_bytes.decode("utf-8")}


def message_is_smp(msg_data):
    """
    :param msg_data: chunk of bytes for a received message.
    :return: True if the data is recognized as a Simple Message Protocol Message.
    """
    return (msg_data[0] == 'E') and (len(msg_data) > LUMINARE_PROTOCOL_COMMAND_HEADER_SIZE)


LUMINARE_PROTOCOL_MSG_TYPE_SWITCHER = {
    # Map with the functions that process the different LUMINARE PROTOCOL messages
    LUMINARE_PROTOCOL_CONFIGURATION_MSG_TYPE: process_luminare_360_config_message
}


class WifiConfigurationMessageListener(threading.Thread):
    """
    An object of this class has its own thread and listens to Simple Message Protocol messages.
    The messages are received as UDP universal broadcast.
    Each message that is identified as Simple Message Protocol Message is processed by a function that handles its type.
    A callback function is used to send the processed data that comes as output of the handler function.
    """

    def __init__(self, ip, callback):
        threading.Thread.__init__(self)
        self.ip = ip
        self.callback = callback
        self.stopped = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def stop(self):
        self.sock.shutdown
        self.stopped = True

    def run(self):
        self.sock.bind(('', LUMINARE_PROTOCOL_UDP_PORT))
        while not self.stopped:
            data = self.sock.recvfrom(512)
            print "Received raw message:", data
            if message_is_smp(data[0]):
                self._process_message(data[0])
            time.sleep(1)

    def _process_message(self, msg_data):
        print "Processing SMP message"
        process_func = \
            LUMINARE_PROTOCOL_MSG_TYPE_SWITCHER.get(ord(msg_data[1]), process_unidentified_message)
        self.callback(process_func(msg_data))


