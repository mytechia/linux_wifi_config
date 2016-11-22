#!/bin/sh
#exec_path="python `python -c "import site; print site.getsitepackages()[0]"`/wifi_control/__main__.py"
#eval ${exec_path}
mkdir -p /var/local/tmp
python -m wifi_control.__main__ /var/local/tmp/wificonfig_data.p /var/local/tmp/wificonfig.log
