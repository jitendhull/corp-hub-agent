"""Network connections collector via psutil."""
from __future__ import annotations
import socket

import psutil

from .base import Collector, utcnow_iso

MAX_CONNECTIONS = 1000


class NetworkCollector(Collector):
    name = "network"

    def collect(self) -> dict:
        items = []
        for conn in psutil.net_connections(kind="inet"):
            try:
                proc_name = psutil.Process(conn.pid).name() if conn.pid else None
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = None
            items.append({
                "ts": utcnow_iso(),
                "protocol": _protocol(conn),
                "local_addr": _addr(conn.laddr),
                "local_port": _port(conn.laddr),
                "remote_addr": _addr(conn.raddr),
                "remote_port": _port(conn.raddr),
                "state": conn.status,
                "pid": conn.pid,
                "process_name": proc_name,
            })
            if len(items) >= MAX_CONNECTIONS:
                break
        return {"items": items}


def _protocol(conn) -> str:
    if conn.type == socket.SOCK_STREAM:
        return "tcp4" if conn.family == socket.AF_INET else "tcp6"
    if conn.type == socket.SOCK_DGRAM:
        return "udp4" if conn.family == socket.AF_INET else "udp6"
    return str(conn.type)


def _addr(addr) -> str | None:
    if addr is None:
        return None
    if isinstance(addr, tuple):
        return addr[0] if addr else None
    return getattr(addr, "ip", None)


def _port(addr) -> int | None:
    if addr is None:
        return None
    if isinstance(addr, tuple):
        return addr[1] if len(addr) > 1 else None
    return getattr(addr, "port", None)
