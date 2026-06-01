"""Deploy the meeting room server package to a Linux host over SSH."""

import os
import posixpath
import sys
from pathlib import Path

import paramiko


REMOTE_APP_DIR = "/home/ddxd/meeting-room-server"
REMOTE_PACKAGE = posixpath.join(REMOTE_APP_DIR, "meeting-server-linux.zip")
SERVICE_NAME = "meeting-server.service"


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing environment variable: {name}")
    return value


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        require_env("DEPLOY_HOST"),
        username=require_env("DEPLOY_USER"),
        password=require_env("DEPLOY_PASS"),
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
        look_for_keys=False,
        allow_agent=False,
    )
    return client


def run(client, command, sudo=False, input_text=None):
    if sudo:
        command = f"sudo -S {command}"
        input_text = require_env("DEPLOY_PASS") + "\n" + (input_text or "")
    stdin, stdout, stderr = client.exec_command(command)
    if input_text:
        stdin.write(input_text)
        stdin.flush()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if code != 0:
        raise RuntimeError(f"Command failed ({code}): {command}\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    return out, err


def upload(client, local_path, remote_path):
    sftp = client.open_sftp()
    try:
        sftp.put(str(local_path), remote_path)
    finally:
        sftp.close()


def main():
    package = Path("build/meeting-server-linux.zip").resolve()
    if not package.exists():
        raise SystemExit(f"Package not found: {package}")

    service = f"""[Unit]
Description=Meeting Room RPC Server
After=network.target

[Service]
Type=simple
User={require_env("DEPLOY_USER")}
WorkingDirectory={REMOTE_APP_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -m meeting_room_system.server.app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

    client = connect()
    try:
        run(client, f"mkdir -p {REMOTE_APP_DIR}/data")
        upload(client, package, REMOTE_PACKAGE)
        run(
            client,
            "set -e; "
            f"cd {REMOTE_APP_DIR}; "
            "if [ -d meeting_room_system ]; then "
            "mv meeting_room_system meeting_room_system.bak.$(date +%Y%m%d%H%M%S); "
            "fi; "
            f"python3 -m zipfile -e {REMOTE_PACKAGE} {REMOTE_APP_DIR}; "
            "cat > config.ini <<'EOF'\n"
            "[server]\n"
            "host = 0.0.0.0\n"
            "port = 8888\n"
            "db_path = data/meetings.db\n"
            "EOF\n",
        )
        run(client, f"cat > {REMOTE_APP_DIR}/{SERVICE_NAME} <<'EOF'\n{service}EOF\n")
        run(client, f"cp {REMOTE_APP_DIR}/{SERVICE_NAME} /etc/systemd/system/{SERVICE_NAME}", sudo=True)
        run(client, "systemctl daemon-reload", sudo=True)
        run(client, f"systemctl enable --now {SERVICE_NAME}", sudo=True)
        run(client, f"systemctl restart {SERVICE_NAME}", sudo=True)
        run(client, "ufw allow 8888/tcp || true", sudo=True)
        active, _ = run(client, f"systemctl is-active {SERVICE_NAME}")
        print(f"service={active.strip()}")
        local_check, _ = run(
            client,
            "python3 - <<'PY'\n"
            "import json, socket, struct\n"
            "payload=json.dumps({'action':'listRooms','data':{}},ensure_ascii=False).encode('utf-8')\n"
            "s=socket.create_connection(('127.0.0.1',8888),timeout=5)\n"
            "s.sendall(struct.pack('!I',len(payload))+payload)\n"
            "header=s.recv(4)\n"
            "length=struct.unpack('!I',header)[0]\n"
            "data=b''\n"
            "while len(data)<length:\n"
            "    data+=s.recv(length-len(data))\n"
            "response=json.loads(data.decode('utf-8'))\n"
            "print(response['success'], len(response['data']['rooms']))\n"
            "s.close()\n"
            "PY\n",
        )
        print(f"local_rpc={local_check.strip()}")
    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
