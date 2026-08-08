"""Collector registry — platform-aware."""
from __future__ import annotations
import platform

from .base import Collector
from .sysinfo import SysinfoCollector
from .network import NetworkCollector
from .metrics import MetricsCollector
from .processes import ProcessesCollector

if platform.system() == "Windows":
    from .logs_windows import LogsWindowsCollector as LogsCollector
else:
    from .logs_linux import LogsLinuxCollector as LogsCollector

__all__ = ["Collector", "SysinfoCollector", "NetworkCollector", "MetricsCollector", "ProcessesCollector", "LogsCollector"]
