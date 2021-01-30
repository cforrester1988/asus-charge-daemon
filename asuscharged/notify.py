import logging
import os
import pwd
import subprocess
from typing import List, Optional

log = logging.getLogger(__name__)


class AllNotifier:
    def __init__(self, app_name: str) -> None:
        self._app_name = app_name

    @staticmethod
    def _get_users() -> List[int]:
        users = [int(user) for user in os.listdir("/run/user")]
        log.debug(f"Got users: {users}")
        return users

    def notify(
        self, summary: str, body: Optional[str] = None, icon: Optional[str] = None
    ) -> None:
        for user in self._get_users():
            log.debug(f"Notifying {pwd.getpwuid(user).pw_name}: '{summary}', '{body}'")
            command = [
                "sudo",
                "-u",
                f"{pwd.getpwuid(user).pw_name}",
                f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user}/bus",
                "notify-send",
                "-c",
                "device",
                "-a",
                f"{self._app_name}",
            ]
            if icon:
                command.append("-i")
                command.append(f"{icon}")
            command.append(f"{summary}")
            if body:
                command.append(f"{body}")
            subprocess.run(command)
