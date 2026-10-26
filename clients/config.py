import os
import configparser
from pathlib import Path

_cfg = configparser.ConfigParser()
_cfg.read(["config/settings.example.ini", "config/settings.ini"])

HOST = _cfg.get("server", "host", fallback="127.0.0.1")
PORT = _cfg.getint("server", "port", fallback=5055)
ADMIN_PASSWORD = _cfg.get("server", "admin_password", fallback=os.environ.get("CAMPUS_ADMIN_PASSWORD", ""))
DATA_FILE = Path(_cfg.get("server", "data_file", fallback="server/data/data.json"))
