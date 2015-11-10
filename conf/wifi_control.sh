#!/bin/sh
exec_path="python `python -c "import site; print site.getsitepackages()[0]"`/wifi_control/main.py"
eval ${exec_path}