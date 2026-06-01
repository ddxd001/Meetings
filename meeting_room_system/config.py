"""Runtime configuration helpers."""

import configparser
import os
import sys
from pathlib import Path


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def config_path():
    return app_dir() / "config.ini"


def load_config():
    config = configparser.ConfigParser()
    path = config_path()
    if path.exists():
        config.read(path, encoding="utf-8")
    return config


def _get_int(config, section, option, default):
    try:
        return config.getint(section, option, fallback=default)
    except ValueError:
        return default


def default_db_path():
    return app_dir() / "data" / "meetings.db"


def server_settings():
    config = load_config()
    host = os.environ.get("MEETING_HOST") or config.get("server", "host", fallback="127.0.0.1")
    port = int(os.environ.get("MEETING_PORT") or _get_int(config, "server", "port", 8888))
    db_path = os.environ.get("MEETING_DB") or config.get("server", "db_path", fallback=str(default_db_path()))
    return host, port, db_path


def client_settings():
    config = load_config()
    host = os.environ.get("MEETING_SERVER_HOST") or config.get("client", "server_host", fallback="127.0.0.1")
    port = int(os.environ.get("MEETING_SERVER_PORT") or _get_int(config, "client", "server_port", 8888))
    timeout = int(os.environ.get("MEETING_TIMEOUT") or _get_int(config, "client", "timeout", 5))
    return host, port, timeout
