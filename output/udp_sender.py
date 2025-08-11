from __future__ import annotations

import json
import socket
from typing import Any, Dict, List


class UdpSender:
    def __init__(self, host: str, port: int, logger=None) -> None:
        self.host = host
        self.port = port
        self.logger = logger
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self._sock.sendto(data, (self.host, self.port))
        if self.logger:
            self.logger.debug(f"UDP sent {len(data)} bytes to {self.host}:{self.port}")


