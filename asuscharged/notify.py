# type: ignore

import logging
import subprocess
import os
import pwd
from dataclasses import dataclass
from enum import Enum
from os import path
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from typing import Dict, Optional, Set

import gi

gi.require_version("Notify", "0.7")

from gi.repository import Notify

from . import FRIENDLY_NAME, NOTIFICATION_ICON

log = logging.getLogger(__name__)


class Urgency(Enum):
    Low = 0
    Normal = 1
    Critical = 2


@dataclass
class Notification:
    summary: str
    body: Optional[str] = None
    app_icon: Optional[str] = NOTIFICATION_ICON
    urgency: Optional[Urgency] = Urgency.Normal


class NotificationServer:
    def __init__(self, app_name: str = FRIENDLY_NAME) -> None:
        log.debug("Initializing notification server.")
        Notify.init(app_name)
        self._procs: Dict[pwd.struct_passwd, Process] = {}
        self._pipes: Dict[pwd.struct_passwd, Connection] = {}
        self._update()
        log.debug("Initialized successfully.")

    @staticmethod
    def _get_active_users() -> Set[pwd.struct_passwd]:
        return set(
            pwd.getpwnam(user)
            for user in set(
                name.split()[0]
                for name in subprocess.run(["who"], capture_output=True)
                .stdout.decode()
                .splitlines()
            )
        )

    @staticmethod
    def _run_user_proc(user: pwd.struct_passwd, pipe: Connection) -> None:
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)
        os.environ[
            "DBUS_SESSION_BUS_ADDRESS"
        ] = f"unix:path=/run/user/{user.pw_uid}/bus"
        log.debug(f"Subprocess created with uid={os.getuid()} and gid={os.getgid()}")
        try:
            temp_noti: Notify.Notification = Notify.Notification.new("No message.")
            while not pipe.closed:
                log.debug(
                    f"Blocking for new notifications from {pipe} on subprocess for user {user}"
                )
                try:
                    input = pipe.recv()
                except KeyboardInterrupt:
                    input = "QUIT"
                if isinstance(input, Notification):
                    temp_noti.update(input.summary, input.body, input.app_icon)
                    temp_noti.set_hint_byte("urgency", input.urgency.value)
                    temp_noti.show()
                elif isinstance(input, str) and input == "QUIT":
                    log.debug(f"Quit message received. Shutting down.")
                    pipe.close()
                    break
        except EOFError:
            log.debug(f"Pipe closed {pipe} on subprocess for user {user}")

    def _update(self) -> None:
        log.debug("Running subprocess update.")
        for user in self._get_active_users():
            if user not in self._procs.keys() and path.exists(
                f"/run/user/{user.pw_uid}/bus"
            ):
                # New user found, create a subprocess for them and store
                # the pipe we'll pass notifications through.
                log.debug(f"Creating new subprocess for {user=}.")
                parent_pipe, child_pipe = Pipe()
                self._procs[user] = Process(
                    target=self._run_user_proc, args=(user, child_pipe)
                )
                self._pipes[user] = parent_pipe
                self._procs[user].start()
            elif user in self._procs.keys() and not path.exists(
                f"/run/user/{user.pw_uid}/bus"
            ):
                # User must have logged out. Delete the subprocess and pipe.
                log.debug(f"Deleting stale subprocess for {user=}")
                self._pipes[user].send("QUIT")
                del self._pipes[user]
                del self._procs[user]
        log.debug("Finished subprocess update.")

    def send(self, notification: Notification) -> None:
        self._update()
        for user in self._procs.keys():
            self._pipes[user].send(notification)

    def close(self) -> None:
        for user in self._procs.keys():
            if self._procs[user].is_alive():
                try:
                    self._pipes[user].send("QUIT")
                except BrokenPipeError as e:
                    self._pipes[user].close()
                    self._procs[user].terminate()
