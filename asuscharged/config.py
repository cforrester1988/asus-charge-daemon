import logging
from os import path
from typing import Any

import toml

from asuscharged import CONFIG_FILE, CONFIG_PATH

log = logging.getLogger(__name__)


class Config:
    DEFAULT = {"restore_on_start": True, "notify_on_restore": True}
    DEFAULT_TOML = """# asuscharged configuration file
#
# The ASUS Battery Charge Daemon loads the default settings if this file has not
# been modified. These defaults have been commented out, below. To restore the
# default settings, delete this file and restart the asuscharged service.

# Restore the last-known threshold when the service starts.
# restore_on_start = true

# Display a system notification when restoring to the last-known threshold.
# notify_on_restore = true
"""

    def __init__(self) -> None:
        self.load()

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if self._config[key] == value:
            log.debug(f"Setting key '{key}' already set to '{str(value)}'.")
            return
        else:
            log.debug(f"Setting key '{key}' to value '{str(value)}'.")
            self._config[key] = value

    def load(self) -> None:
        self._config = self.DEFAULT
        if not path.exists(CONFIG_PATH):
            log.warning(
                f"{CONFIG_FILE} not found. Exporting defaults to: {CONFIG_PATH}"
            )
            with open(CONFIG_PATH, "w") as file:
                file.write(self.DEFAULT_TOML)
                file.flush()
        else:
            self._config = {
                **self._config,
                **toml.load(CONFIG_PATH),
            }
            log.debug(f"Loaded configuration: {repr(self._config)}")
