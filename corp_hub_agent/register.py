"""Registration: POST /api/agents/register, persist returned token."""
from __future__ import annotations
import platform
import socket

import httpx

from .auth import write_token
from .config import Config


def _hostname() -> str:
    return socket.gethostname()


def _os_name() -> str:
    return platform.system()


def _kernel() -> str:
    return platform.release()


def _arch() -> str:
    return platform.machine()


def _agent_version() -> str:
    from . import __version__
    return __version__


def register(config: Config, token_path: str) -> tuple[str, str]:
    """Register with backend, persist token, return (host_id, token)."""
    payload = {
        "hostname": _hostname(),
        "os": _os_name(),
        "kernel": _kernel(),
        "arch": _arch(),
        "agent_version": _agent_version(),
        "endpoint_url": f"http://{config.listen_host}:{config.listen_port}",
        "endpoint_port": config.listen_port,
    }
    url = config.backend_url.rstrip("/") + "/api/agents/register"
    resp = httpx.post(url, json=payload, timeout=15.0)
    resp.raise_for_status()
    data = resp.json()
    token = data["token"]
    write_token(token_path, token)
    return data["host_id"], token
