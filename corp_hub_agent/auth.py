"""Token file IO. 64-char hex token, chmod 600 on Linux."""
from __future__ import annotations
from pathlib import Path
import os
import stat
import sys


def read_token(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    token = p.read_text().strip()
    return token or None


def write_token(path: str, token: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(token + "\n")
    if sys.platform != "win32":
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)  # 600


def auth_header(token: str) -> dict:
    return {"X-Agent-Token": token}
