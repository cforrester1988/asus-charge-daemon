"""A daemon exposing D-Bus services for managing the charge level of recent
ASUS notebooks.
"""

import logging
import sys

__version__ = "0.1.0"

APP_NAME = "asuscharged"
PACKAGE_NAME = "asus-charge-daemon"
DBUS_NAME = "ca.cforrester.AsusChargeDaemon1"
DBUS_PATH = "/ca/cforrester/AsusChargeDaemon1"

if __debug__:
    log_level = logging.DEBUG
    log_format = "%(asctime)s [%(levelname)s] %(module)s(%(lineno)d) - %(message)s"
else:
    log_level = logging.WARNING
    log_format = "[%(levelname)s] %(message)s"

logging.basicConfig(stream=sys.stdout, level=log_level, format=log_format)
