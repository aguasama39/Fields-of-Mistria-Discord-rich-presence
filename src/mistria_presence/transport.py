"""Discord local IPC transport and a no-op transport for tests/headless use."""

from __future__ import annotations

import json
import os
import socket
import struct
import time
from typing import Any, Protocol


class PresenceTransport(Protocol):
    def connect(self, client_id: str) -> None: ...
    def set_activity(self, payload: dict[str, Any]) -> None: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...


class DiscordIPC:
    def __init__(self, timeout: float = 1.5) -> None:
        self.timeout = timeout
        self.socket: socket.socket | None = None
        self.pipe: str | None = None

    def connect(self, client_id: str) -> None:
        last_error: OSError | None = None
        for number in range(10):
            path = f"{os.environ.get('XDG_RUNTIME_DIR', '/tmp')}/discord-ipc-{number}"
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect(path)
                self.socket, self.pipe = sock, path
                self._command(0, {"v": 1, "client_id": client_id})
                return
            except OSError as error:
                last_error = error
                try:
                    sock.close()
                except UnboundLocalError:
                    pass
        raise ConnectionError("Discord local IPC is unavailable") from last_error

    def _command(self, opcode: int, data: dict[str, Any]) -> dict[str, Any]:
        if self.socket is None:
            raise ConnectionError("Discord IPC is not connected")
        encoded = json.dumps(data, separators=(",", ":")).encode()
        self.socket.sendall(struct.pack("<II", opcode, len(encoded)) + encoded)
        header = self.socket.recv(8)
        if len(header) != 8:
            raise ConnectionError("Discord IPC closed the connection")
        _, length = struct.unpack("<II", header)
        response = json.loads(self.socket.recv(length).decode())
        if response.get("evt") == "ERROR":
            raise ConnectionError(response.get("data", {}).get("message", "Discord IPC error"))
        return response

    def set_activity(self, payload: dict[str, Any]) -> None:
        self._command(1, {"cmd": "SET_ACTIVITY", "args": {"pid": os.getpid(), "activity": payload}, "nonce": str(time.time_ns())})

    def clear(self) -> None:
        self._command(1, {"cmd": "SET_ACTIVITY", "args": {"pid": os.getpid(), "activity": None}, "nonce": str(time.time_ns())})

    def close(self) -> None:
        if self.socket:
            self.socket.close()
        self.socket = None


class MemoryTransport:
    """Useful for tests and installations where Discord is intentionally absent."""
    def __init__(self) -> None:
        self.connected = False
        self.last_payload: dict[str, Any] | None = None

    def connect(self, client_id: str) -> None:
        self.connected = True

    def set_activity(self, payload: dict[str, Any]) -> None:
        self.last_payload = payload

    def clear(self) -> None:
        self.last_payload = None

    def close(self) -> None:
        self.connected = False
