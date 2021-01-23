#!/usr/bin/env python3
import os
import shutil
import stat
import subprocess
import sys
from typing import List

APP_NAME = "asuscharged"
PACKAGE_NAME = "asus-charge-daemon"
DATADIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SYSTEMD_SYSTEM_UNIT_FILE = "asuscharged.service"
DBUS_INTERFACE_FILE = "ca.cforrester.AsusChargeDaemon1.xml"
DBUS_SYSTEM_SERVICE_FILE = "ca.cforrester.AsusChargeDaemon1.service"
DBUS_SYSTEM_CONF_FILE = "ca.cforrester.AsusChargeDaemon1.conf"

files = {}


def has_systemd() -> bool:
    return os.path.exists("/run/systemd/system")


def systemd_system_unit_dir() -> str:
    return subprocess.run(
        ("pkg-config", "systemd", "--variable=systemdsystemunitdir"),
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def dbus_interfaces_dir() -> str:
    return subprocess.run(
        ("pkg-config", "dbus-1", "--variable=interfaces_dir"),
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def dbus_system_services_dir() -> str:
    return subprocess.run(
        ("pkg-config", "dbus-1", "--variable=system_bus_services_dir"),
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def dbus_system_conf_dir() -> str:
    return (
        subprocess.run(
            ("pkg-config", "dbus-1", "--variable=system_bus_services_dir"),
            text=True,
            stdout=subprocess.PIPE,
        )
        .stdout.replace("-services", ".d")
        .strip()
    )


def files_exist() -> List[str]:
    exists = []
    for file in files.values():
        if os.path.exists(file):
            exists.append(file)
    return exists


def install(install_daemon=True, force=False, local=False) -> None:
    if not force:
        exists = files_exist()
        if exists:
            exists = "\n".join(exists)
            print(f"The following files exist:\n{exists}")
            if not input("Overwrite? [Y/N] ").startswith(("y", "Y")):
                raise SystemExit("Not overwriting.")
    for file in files:
        dest = files[file]
        print(f"Installing {file} to {os.path.dirname(dest)}...", end=" ")
        source = os.path.join(DATADIR, file)
        shutil.copy(source, dest)
        os.chmod(dest, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IROTH)
        print("\033[01m\033[32m✓\033[0m")
    if install_daemon:
        if local:
            print(f"Installing {APP_NAME} package from local directory...")
            subprocess.run((sys.executable, "-m", "pip", "install", os.curdir))
        else:
            print(f"Installing {APP_NAME} package from PyPA...")
            subprocess.run((sys.executable, "-m", "pip", "install", PACKAGE_NAME))
    print("Enabling and running systemd service...")
    subprocess.run(("systemctl", "enable", APP_NAME))
    subprocess.run(("systemctl", "start", APP_NAME))


def uninstall(uninstall_daemon=True) -> None:
    print("Stopping and disabling systemd service...")
    subprocess.run(("systemctl", "stop", APP_NAME))
    subprocess.run(("systemctl", "disable", APP_NAME))
    exists = files_exist()
    if not exists:
        print("No data files found, skipping...")
    else:
        for file in exists:
            print(f"Deleting {file}...", end=" ")
            os.remove(file)
            print("\033[01m\033[32m✓\033[0m")
    if uninstall_daemon:
        subprocess.run((sys.executable, "-m", "pip", "uninstall", "-y", PACKAGE_NAME))


if __name__ == "__main__":
    if os.geteuid() != 0:
        raise SystemExit("Script must be run as root.")
    if not has_systemd():
        raise SystemExit("Script is only compatible with systems running systemd.")
    try:
        files = {
            SYSTEMD_SYSTEM_UNIT_FILE: os.path.join(
                systemd_system_unit_dir(), SYSTEMD_SYSTEM_UNIT_FILE
            ),
            DBUS_INTERFACE_FILE: os.path.join(
                dbus_interfaces_dir(), DBUS_INTERFACE_FILE
            ),
            DBUS_SYSTEM_SERVICE_FILE: os.path.join(
                dbus_system_services_dir(), DBUS_SYSTEM_SERVICE_FILE
            ),
            DBUS_SYSTEM_CONF_FILE: os.path.join(
                dbus_system_conf_dir(), DBUS_SYSTEM_CONF_FILE
            ),
        }
        if sys.argv[1] == "install":
            try:
                if sys.argv[2] == "local":
                    install(local=True)
                else:
                    install()
            except IndexError:
                install()
        elif sys.argv[1] == "uninstall":
            uninstall()
        elif sys.argv[1] == "reinstall":
            uninstall()
            try:
                if sys.argv[2] == "local":
                    install(local=True)
                else:
                    install()
            except IndexError:
                install()
        else:
            raise SystemExit("Missing argument: install or uninstall.")
    except IndexError:
        raise SystemExit("Missing argument: install or uninstall.")
