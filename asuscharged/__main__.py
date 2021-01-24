# type: ignore
import asyncio
import logging
import os
import platform
from argparse import ArgumentParser
from shutil import copyfile

import asuscharge
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType
from dbus_next.service import ServiceInterface, dbus_property

from . import APP_NAME, DBUS_NAME, DBUS_PATH, STATE_PATH
from .config import Config

# dbus-next uses string literal type hints to determine the D-Bus type.
TUInt = "u"

log = logging.getLogger(__name__)


class ChargeDaemon(ServiceInterface):
    def __init__(self):
        log.debug("Initializing daemon...")
        self.config = Config()
        log.debug("Loaded config module.")
        self.controller = asuscharge.ChargeThresholdController()
        log.debug(f"Acquired ChargeThresholdController: {repr(self.controller)}")
        super().__init__(DBUS_NAME)
        log.debug(f"D-Bus service interface '{DBUS_NAME}' initialized.")
        if self.config["restore_on_start"]:
            try:
                threshold = int(open(STATE_PATH, "r").read().strip())
                log.debug(f"Found previous threshold state: {threshold}%.")
                if self.controller.end_threshold != threshold:
                    self.controller.end_threshold = threshold
                    self.emit_properties_changed(
                        {"ChargeEndThreshold": self.controller.end_threshold}
                    )
            except FileNotFoundError:
                log.warning(
                    f"Previous threshold state not found. Using default: {self.controller.end_threshold}%."
                )
        else:
            try:
                os.remove(STATE_PATH)
                log.debug("Deleted stale threshold state file.")
            except FileNotFoundError:
                pass

    @dbus_property()
    def ChargeEndThreshold(self) -> TUInt:
        return self.controller.end_threshold

    @ChargeEndThreshold.setter
    def ChargeEndThreshold(self, value: TUInt) -> None:
        if self.controller.end_threshold == value:
            log.debug(
                f"Not updating ChargeEndThreshold: value matches current threshold."
            )
            return
        else:
            log.debug(
                f"Updating ChargeEndThreshold from {self.controller.end_threshold}% to {value}%."
            )
            self.controller.end_threshold = value
            if self.config["restore_on_start"]:
                copyfile(self.controller.bat_path, STATE_PATH)
            self.emit_properties_changed(
                {"ChargeEndThreshold": self.controller.end_threshold}
            )


async def run_daemon() -> None:
    log.debug("Connecting to D-Bus system bus.")
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    interface = ChargeDaemon()
    log.debug(f"Exporting interface '{DBUS_NAME}' to path '{DBUS_PATH}'")
    bus.export(DBUS_PATH, interface)
    await bus.request_name(DBUS_NAME)
    log.debug("Daemon running...")
    await bus.wait_for_disconnect()


def main() -> None:
    if not asuscharge.supported_platform():
        raise SystemExit(
            f"{APP_NAME} only runs on Linux systems. Detected {platform.system()}."
        )
    if not asuscharge.supported_kernel():
        raise SystemExit(
            f"{APP_NAME} requires a Linux kernel version >= 5.4 to run. Detected {platform.release()}."
        )
    if not asuscharge.module_loaded():
        raise SystemExit(
            f"Required kernel module 'asus_nb_wmi' is not loaded. Try 'sudo modprobe asus_nb_wmi'."
        )
    parser = ArgumentParser(APP_NAME)
    parser.add_argument("--bat-path", action="store_true")
    args = parser.parse_args()
    if args.bat_path:
        print(asuscharge.ChargeThresholdController().bat_path)
        raise SystemExit(0)
    else:
        try:
            asyncio.get_event_loop().run_until_complete(run_daemon())
        except Exception:
            log.exception("Daemon encountered a fatal exception.")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
