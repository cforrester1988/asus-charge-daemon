import configparser
import logging

from asuscharged import CONFIG_PATH, DEV_CONFIG_PATH

_log = logging.getLogger(__name__)

config = configparser.ConfigParser()
config["daemon"] = {
    "restore_on_start": "yes",
    "notify_on_restore": "yes",
    "notify_on_change": "yes",
}

if __debug__:
    _files = (CONFIG_PATH, DEV_CONFIG_PATH)
else:
    _files = CONFIG_PATH
_files_read = config.read(_files)
if _files_read:
    _log.debug(f"Loaded configuration from: {_files_read}")
else:
    _log.debug(
        f"No valid configuration files found. Exporting defaults to {CONFIG_PATH}"
    )
    with open(CONFIG_PATH, "w") as file:
        config.write(file)
