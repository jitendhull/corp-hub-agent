"""Processes collector: top processes by CPU and memory usage."""
from __future__ import annotations
import logging
import psutil

from .base import Collector, utcnow_iso

log = logging.getLogger("corp_hub_agent")


class ProcessesCollector(Collector):
    name = "processes"

    def __init__(self, limit: int = 15):
        self.limit = limit

    def collect(self) -> dict:
        items = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'create_time']):
            try:
                info = proc.info
                mem_rss = info['memory_info'].rss if info.get('memory_info') else 0
                items.append({
                    "ts": utcnow_iso(),
                    "pid": info['pid'],
                    "name": info['name'] or "unknown",
                    "username": info['username'] or "unknown",
                    "cpu_percent": round(info['cpu_percent'] or 0.0, 1),
                    "mem_percent": round(info['memory_percent'] or 0.0, 1),
                    "mem_rss_bytes": mem_rss,
                    "status": info['status'] or "running",
                    "create_time": info['create_time'] or 0.0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by CPU percent descending, pick top limit
        items.sort(key=lambda x: (x['cpu_percent'], x['mem_percent']), reverse=True)
        return {"items": items[:self.limit]}
