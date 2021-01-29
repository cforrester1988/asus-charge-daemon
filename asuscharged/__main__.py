# type: ignore
import asyncio
import logging
import os
import platform
from argparse import ArgumentParser
from os import path
from shutil import copyfile

import asuscharge
from asyncinotify import Inotify, Mask
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType, RequestNameReply
from dbus_next.service import ServiceInterface, dbus_property

from . import APP_NAME, DBUS_NAME, DBUS_PATH, STATE_PATH
from .config import config

# dbus-next uses string literal type hints to determine the D-Bus type.
TUInt = "u"

log = logging.getLogger("asuscharged")


class ChargeDaemon(ServiceInterface):
    def __init__(self) -> None:
        log.debug("Initializing daemon...")
        super().__init__(DBUS_NAME)
        log.debug(f"D-Bus service interface '{DBUS_NAME}' initialized.")
        self.controller = asuscharge.ChargeThresholdController()
        log.debug(f"Acquired ChargeThresholdController: {repr(self.controller)}")
        if config["daemon"].getboolean("restore_on_start"):
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
            if config["daemon"].getboolean("restore_on_start"):
                # Shadow the charge end threshold file
                copyfile(self.controller.bat_path, STATE_PATH)
            # The properties changed signal is emitted when the threshold
            # file itself is modified. This tracks external changes too.
            # self.emit_properties_changed(
            #     {"ChargeEndThreshold": self.controller.end_threshold}
            # )


async def iterate_threshold_events(inotify: Inotify, interface: ChargeDaemon) -> None:
    async for event in inotify:
        if event.path.as_posix() == interface.controller.bat_path:
            log.debug(f"Threshold file modified, signalling property change.")
            interface.emit_properties_changed(
                {"ChargeEndThreshold": interface.controller.end_threshold}
            )


async def run_daemon() -> None:
    log.debug("Running daemon on D-Bus system bus.")
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    interface = ChargeDaemon()
    log.debug(f"Exporting interface '{DBUS_NAME}' to path '{DBUS_PATH}'")
    bus.export(DBUS_PATH, interface)
    if (
        not (reply := await bus.request_name(DBUS_NAME))
        == RequestNameReply.PRIMARY_OWNER
    ):
        log.critical(
            f"Unable to acquire primary ownership of bus name '{DBUS_NAME}'. In state: {reply.name}"
        )
        raise SystemExit(1)
    log.debug("Daemon running...")
    inotify = Inotify()
    inotify.add_watch(path.dirname(interface.controller.bat_path), Mask.CLOSE_WRITE)
    asyncio.gather(
        bus.wait_for_disconnect(), iterate_threshold_events(inotify, interface)
    )


async def run_client(value: int) -> None:
    log.debug("Running client on D-Bus system bus.")
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    introspection = await bus.introspect(DBUS_NAME, DBUS_PATH)
    daemon_proxy = bus.get_proxy_object(DBUS_NAME, DBUS_PATH, introspection)
    daemon_interface = daemon_proxy.get_interface(DBUS_NAME)
    log.debug(f"Acquired client interface {repr(daemon_interface)}.")
    if await daemon_interface.get_charge_end_threshold() != value:
        await daemon_interface.set_charge_end_threshold(value)
        log.debug(
            f"Set ChargeEndThreshold to {await daemon_interface.get_charge_end_threshold()}. Closing client."
        )
    else:
        log.debug(
            f"Input matches existing ChargeEndThreshold, not changing. Closing client."
        )


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
    parser.add_argument("-s", "--set", action="store", type=int)
    args = parser.parse_args()
    if args.bat_path:
        print(asuscharge.ChargeThresholdController().bat_path)
        raise SystemExit(0)
    elif args.set is not None:
        if 1 <= args.set <= 100:
            asyncio.get_event_loop().run_until_complete(run_client(args.set))
            raise SystemExit(0)
        else:
            log.critical(f"Tried to set an invalid value: {args.set}%.")
            raise SystemExit(1)
    else:
        try:
            asyncio.get_event_loop().create_task(run_daemon())
            asyncio.get_event_loop().run_forever()
        except Exception:
            log.exception("Daemon encountered a fatal exception.")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
