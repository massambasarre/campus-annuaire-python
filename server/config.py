import os
import configparser
from pathlib import Path

_cfg = configparser.ConfigParser()
_cfg.read(["config/settings.example.ini", "config/settings.ini"])

HOST = _cfg.get("network", "host", fallback="127.0.0.1")
PORT = _cfg.getint("network", "port", fallback=5055)
MAX_CLIENTS = _cfg.getint("network", "max_clients", fallback=20)

ADMIN_PASSWORD = _cfg.get("auth", "admin_password", fallback=os.environ.get("CAMPUS_ADMIN_PASSWORD", ""))

DATA_FILE = Path(_cfg.get("storage", "data_file", fallback="server/data/data.json"))
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
