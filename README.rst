WiFi Control
============

A component that is based on wpa_supplicant and adds a network configuration management layer. It uses the Simple
Message Protocol to listen for WiFi Configuration messages.

DBUS is used to handle wpa_supplicant and also to provide a small API to handle simple network connection commands.

----

Contents: Python sources.

The main.py launches both a DBUS service and a small Simple Message Protocol server.

It handles three network configurations: "bootstrap", "default" and "current". The configuration data is handled
as a simple binary file. The data model is explained in wificonfiguration.py.

When a valid WiFi Configuration message is received, a new WiFi network configuration is added a set as "current"
via wpa_supplicant.

DBUS API:  ('com.mytechia.wificonfig')
    * [method] disconnect()
    * [method] reconnect()
    * [signal] signal_state_change(msg_info)

----

Contents: Config files.

This package contains all the needed files for a modern Linux distribution. It assumes systemd.

The main.py is wrapped in a small script: wrapped in a small script: wifi_control.

A .service file is needed in order to launch this script: wificonfig.service.

Both a .service file and a .conf file (needed to specify permissions) are used for DBUS integration.