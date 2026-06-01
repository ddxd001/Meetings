"""Length-prefixed JSON RPC client."""

import json
import socket
import struct

from meeting_room_system.config import client_settings


class RpcClient:
    def __init__(self, host=None, port=None, timeout=None):
        default_host, default_port, default_timeout = client_settings()
        self.host = host
        self.port = port if port is not None else default_port
        self.timeout = timeout if timeout is not None else default_timeout
        if self.host is None:
            self.host = default_host

    def request(self, action, data=None):
        payload = {"action": action, "data": data or {}}
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.sendall(struct.pack("!I", len(raw)) + raw)
            header = self._recv_exact(sock, 4)
            length = struct.unpack("!I", header)[0]
            response = self._recv_exact(sock, length)
        return json.loads(response.decode("utf-8"))

    def _recv_exact(self, sock, length):
        chunks = []
        remaining = length
        while remaining > 0:
            chunk = sock.recv(remaining)
            if not chunk:
                raise ConnectionError("服务器连接已断开")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
