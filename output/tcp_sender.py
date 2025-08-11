from __future__ import annotations

import json
import socket
from typing import Any


class TcpSender:
    def __init__(
        self,
        host: str,
        port: int,
        logger=None,
        connect_timeout_s: float = 1.5,
        send_newline: bool = True,
        reconnect_on_error: bool = True,
    ) -> None:
        self.host = host
        self.port = int(port)
        self.logger = logger
        self.connect_timeout_s = connect_timeout_s
        self.send_newline = send_newline
        self.reconnect_on_error = reconnect_on_error
        self._sock: socket.socket | None = None

    def _connect(self) -> None:
        self._close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.connect_timeout_s)
        s.connect((self.host, self.port))
        self._sock = s
        if self.logger:
            self.logger.info(f"TCP connected to {self.host}:{self.port}")

    def _close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            finally:
                self._sock = None

    def send(self, payload: Any) -> None:
        data_bytes: bytes
        if isinstance(payload, (dict, list)):
            text = json.dumps(payload)
            if self.send_newline:
                text += "\n"
            data_bytes = text.encode("utf-8")
        elif isinstance(payload, (str, bytes)):
            if isinstance(payload, str):
                text = payload + ("\n" if self.send_newline and not payload.endswith("\n") else "")
                data_bytes = text.encode("utf-8")
            else:
                data_bytes = payload
        else:
            raise TypeError("Unsupported payload type for TcpSender")

        try:
            if self._sock is None:
                self._connect()
            assert self._sock is not None
            self._sock.sendall(data_bytes)
            if self.logger:
                self.logger.debug(f"TCP sent {len(data_bytes)} bytes to {self.host}:{self.port}")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"TCP send error: {e}; reconnecting...")
            if self.reconnect_on_error:
                try:
                    self._connect()
                    assert self._sock is not None
                    self._sock.sendall(data_bytes)
                except Exception as e2:
                    if self.logger:
                        self.logger.error(f"TCP resend failed: {e2}")
            else:
                self._close()


