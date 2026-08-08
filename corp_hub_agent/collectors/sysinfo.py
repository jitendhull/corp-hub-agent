"""System info collector: psutil + platform. Cross-platform (Linux first)."""
from __future__ import annotations
import platform
import socket
import time

import psutil

from .base import Collector, utcnow_iso


class SysinfoCollector(Collector):
    name = "sysinfo"

    def __init__(self, agent_version: str = "0.1.0"):
        self.agent_version = agent_version

    def collect(self) -> dict:
        boot_time = psutil.boot_time()  # epoch seconds
        load = getattr(psutil, "getloadavg", lambda: (0.0, 0.0, 0.0))()
        disk = psutil.disk_usage("/")
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "ts": utcnow_iso(),
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "os_name": platform.system(),
            "os_version": platform.version(),
            "kernel": platform.release(),
            "arch": platform.machine(),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_model": _cpu_model(),
            "mem_total": mem.total,
            "mem_available": mem.available,
            "swap_total": swap.total,
            "disk_total": disk.total,
            "disk_free": disk.free,
            "uptime_seconds": int(time.time() - boot_time),
            "boot_time": _iso_from_epoch(boot_time),
            "python_version": platform.python_version(),
            "agent_version": self.agent_version,
            "load_avg_1m": round(load[0], 2),
            "load_avg_5m": round(load[1], 2),
            "load_avg_15m": round(load[2], 2),
        }


def _cpu_model() -> str | None:
    try:
        if platform.system() == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def _iso_from_epoch(epoch: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
