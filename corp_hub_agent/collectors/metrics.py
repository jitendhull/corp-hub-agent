"""Metrics collector: CPU/RAM/disk usage for /api/metrics/ingest."""
from __future__ import annotations
import platform
import socket
import time
import psutil

from .base import Collector


class MetricsCollector(Collector):
    name = "metrics"

    def __init__(self, agent_version: str = "0.1.0"):
        self.agent_version = agent_version

    def collect(self) -> dict:
        boot_time = psutil.boot_time()
        uptime = int(time.time() - boot_time)

        disk = psutil.disk_usage("/")
        mem = psutil.virtual_memory()

        return {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "cpu_percent": psutil.cpu_percent(interval=None),
            "mem_percent": mem.percent,
            "disk_percent": disk.percent,
            "uptime_seconds": uptime,
            "kernel": platform.release(),
            "arch": platform.machine(),
            "cpu_count": psutil.cpu_count(logical=True),
            "mem_total": mem.total,
            "disk_total": disk.total,
            "disk_free": disk.free,
            "agent_version": self.agent_version,
        }
