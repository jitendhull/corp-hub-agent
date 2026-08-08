"""Linux log collector: journald (systemd) with /var/log tail fallback.

Uses the `systemd` Python package (journal reader) when available, else
tails /var/log/syslog and /var/log/auth.log. Keeps an in-memory backlog,
capped at max_backlog; each push sends at most max_lines_per_push and
drops the oldest on overflow (per user decision).
"""
from __future__ import annotations
import logging
from pathlib import Path

from .base import Collector, utcnow_iso

log = logging.getLogger("corp_hub_agent")

SEVERITY_MAP = {
    0: "emerg", 1: "alert", 2: "crit", 3: "err",
    4: "warning", 5: "notice", 6: "info", 7: "debug",
}


class LogsLinuxCollector(Collector):
    name = "logs"

    def __init__(self, sources=None, syslog_path="/var/log/syslog",
                 auth_log_path="/var/log/auth.log",
                 max_lines_per_push=500, max_backlog=5000):
        self.sources = sources or ["journald", "syslog", "auth.log"]
        self.syslog_path = syslog_path
        self.auth_log_path = auth_log_path
        self.max_lines_per_push = max_lines_per_push
        self.max_backlog = max_backlog
        self._backlog: list[dict] = []
        self._journal = None
        self._journal_cursor = None
        self._file_positions: dict[str, int] = {}
        self._init()

    def _init(self) -> None:
        if "journald" in self.sources:
            try:
                from systemd import journal  # type: ignore
                self._journal = journal
                log.info("log collector: journald available")
            except ImportError:
                log.warning("log collector: systemd python package not installed; "
                            "falling back to file tail")
        self._init_files()

    def _init_files(self) -> None:
        for path in (self.syslog_path, self.auth_log_path):
            p = Path(path)
            if p.exists():
                # Start from current end (don't replay entire history)
                self._file_positions[path] = p.stat().st_size

    def collect(self) -> dict:
        self._collect_journal()
        self._collect_files()
        out = self._backlog[: self.max_lines_per_push]
        self._backlog = self._backlog[self.max_lines_per_push:]
        return {"items": out}

    # -- journald --

    def _collect_journal(self) -> None:
        if self._journal is None:
            return
        try:
            reader = self._journal.Reader()
            reader.seek_tail()
            if self._journal_cursor:
                reader.seek_cursor(self._journal_cursor)
            reader.get_previous()
            for entry in reader:
                ts = entry.get("__REALTIME_TIMESTAMP")
                if ts:
                    from datetime import datetime, timezone
                    ts_iso = datetime.fromtimestamp(ts / 1e6, tz=timezone.utc).isoformat()
                else:
                    ts_iso = utcnow_iso()
                self._append({
                    "ts": ts_iso,
                    "source": "journald",
                    "facility": entry.get("SYSLOG_FACILITY") or entry.get("_SYSTEMD_UNIT") or "daemon",
                    "severity": SEVERITY_MAP.get(entry.get("PRIORITY"), "info"),
                    "message": (entry.get("MESSAGE") or "")[:20000],
                    "raw": None,
                })
                self._journal_cursor = entry.get("__CURSOR")
        except Exception as e:
            log.warning("journal read failed: %s", e)

    # -- file tail --

    def _collect_files(self) -> None:
        for path in (self.syslog_path, self.auth_log_path):
            if path not in self._file_positions:
                continue
            try:
                p = Path(path)
                size = p.stat().st_size
                start = self._file_positions[path]
                if size < start:
                    # Rotated — restart from beginning
                    start = 0
                if size == start:
                    continue
                with open(path, "rb") as f:
                    f.seek(start)
                    data = f.read(size - start)
                self._file_positions[path] = size
                for raw_line in data.decode("utf-8", errors="replace").splitlines():
                    if not raw_line.strip():
                        continue
                    self._append({
                        "ts": utcnow_iso(),
                        "source": "syslog" if "syslog" in path else "auth.log",
                        "facility": "auth" if "auth" in path else "daemon",
                        "severity": "info",
                        "message": raw_line[:20000],
                        "raw": None,
                    })
            except Exception as e:
                log.warning("tail %s failed: %s", path, e)

    # -- backlog --

    def _append(self, item: dict) -> None:
        self._backlog.append(item)
        if len(self._backlog) > self.max_backlog:
            # Drop oldest (user decision: cap + drop)
            del self._backlog[: len(self._backlog) - self.max_backlog]
