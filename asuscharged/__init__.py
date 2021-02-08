"""A daemon exposing D-Bus services for managing the charge level of recent
ASUS notebooks.
"""

import logging
import sys
from os import path

__version__ = "0.3.1"

APP_NAME = "asuscharged"
FRIENDLY_NAME = "ASUS Battery Charge Control Daemon"
PACKAGE_NAME = "asus-charge-daemon"
STATE_DIR = "/var/lib/asuscharged"
STATE_FILE = "charge_control_end_threshold"
STATE_PATH = path.join(STATE_DIR, STATE_FILE)
CONFIG_DIR = "/etc/asuscharged"
CONFIG_FILE = "asuscharged.conf"
CONFIG_PATH = path.join(CONFIG_DIR, CONFIG_FILE)
DEV_CONFIG_DIR = path.join(path.dirname(path.dirname(__file__)), "dev")
DEV_CONFIG_PATH = path.join(DEV_CONFIG_DIR, CONFIG_FILE)
DBUS_NAME = "ca.cforrester.AsusChargeDaemon1"
DBUS_PATH = "/ca/cforrester/AsusChargeDaemon1"
NOTIFICATION_ICON = "battery-charging-good"

if __debug__:
    log_level = logging.DEBUG
    log_format = "%(asctime)s [%(levelname)s] %(name)s(%(lineno)d) - %(message)s"
else:
    log_level = logging.WARNING
    log_format = "[%(levelname)s] %(message)s"

logging.basicConfig(stream=sys.stdout, level=log_level, format=log_format)
