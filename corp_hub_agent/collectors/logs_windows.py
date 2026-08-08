"""Windows Event Log collector — STUB for v1 (Linux first).

Structure ready: uses win32evtlog when built on Windows. Returns empty
items until implemented (user has few Windows machines for test).
"""
from __future__ import annotations
import logging

from .base import Collector, utcnow_iso

log = logging.getLogger("corp_hub_agent")


class LogsWindowsCollector(Collector):
    name = "logs"

    def __init__(self, sources=None):
        self.sources = sources or ["application", "system", "security"]

    def collect(self) -> dict:
        log.info("Windows log collector not implemented in v1 (Linux first)")
        return {"items": []}
