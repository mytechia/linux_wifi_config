#!/bin/sh
#exec_path="python `python -c "import site; print site.getsitepackages()[0]"`/wifi_control/__main__.py"
#eval ${exec_path}
python -m wifi_control.__main__ &> /tmp/wificonfig.log
