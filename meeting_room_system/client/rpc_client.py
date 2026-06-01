"""Length-prefixed JSON RPC client."""

import json
import socket
import struct


class RpcClient:
    def __init__(self, host="127.0.0.1", port=8888, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout

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

