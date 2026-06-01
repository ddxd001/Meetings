"""Length-prefixed JSON RPC server."""

import json
import socket
import struct
import threading

from .service import fail


class RpcServer:
    def __init__(self, service, host="127.0.0.1", port=8888):
        self.service = service
        self.host = host
        self.port = port

    def serve_forever(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen(5)
            print(f"服务器启动，监听 {self.host}:{self.port}")
            while True:
                conn, addr = server.accept()
                thread = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
                thread.start()

    def _handle_client(self, conn, addr):
        with conn:
            try:
                request = self._recv_json(conn)
                action = request.get("action")
                data = request.get("data", {})
                response = self.service.dispatch(action, data)
            except json.JSONDecodeError:
                response = fail("BAD_JSON", "请求不是合法JSON")
            except Exception as exc:
                response = fail("SERVER_ERROR", f"服务器错误: {exc}")
            self._send_json(conn, response)

    def _recv_json(self, conn):
        header = self._recv_exact(conn, 4)
        if not header:
            return {}
        length = struct.unpack("!I", header)[0]
        payload = self._recv_exact(conn, length)
        return json.loads(payload.decode("utf-8"))

    def _send_json(self, conn, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        conn.sendall(struct.pack("!I", len(raw)) + raw)

    def _recv_exact(self, conn, length):
        chunks = []
        remaining = length
        while remaining > 0:
            chunk = conn.recv(remaining)
            if not chunk:
                raise ConnectionError("连接已断开")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

