"""Config loading for the agent. TOML via stdlib tomllib (3.11+)."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import os
import tomllib

DEFAULT_CONFIG_PATH = Path("/etc/corp-hub-agent/agent.conf")
DEFAULT_TOKEN_PATH = Path("/etc/corp-hub-agent/token")


def _default_sources() -> list[str]:
    return ["journald", "syslog", "auth.log"]


@dataclass
class LogsConfig:
    sources: list[str] = field(default_factory=_default_sources)
    syslog_path: str = "/var/log/syslog"
    auth_log_path: str = "/var/log/auth.log"
    max_lines_per_push: int = 500
    max_backlog: int = 5000


@dataclass
class Config:
    backend_url: str
    listen_host: str = "0.0.0.0"
    listen_port: int = 9500
    sysinfo_interval_seconds: int = 300
    network_interval_seconds: int = 60
    logs_interval_seconds: int = 60
    token_path: str = str(DEFAULT_TOKEN_PATH)
    logs: LogsConfig = field(default_factory=LogsConfig)


def load_config(path: str | Path | None = None) -> Config:
    """Load agent.conf. Path from arg, env CORP_HUB_AGENT_CONF, or default."""
    if path is None:
        env_path = os.environ.get("CORP_HUB_AGENT_CONF")
        if env_path:
            path = Path(env_path)
        else:
            path = DEFAULT_CONFIG_PATH

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    logs_raw = raw.get("logs", {})
    logs_cfg = LogsConfig(
        sources=logs_raw.get("sources", _default_sources()),
        syslog_path=logs_raw.get("syslog_path", LogsConfig.syslog_path),
        auth_log_path=logs_raw.get("auth_log_path", LogsConfig.auth_log_path),
        max_lines_per_push=int(logs_raw.get("max_lines_per_push", 500)),
        max_backlog=int(logs_raw.get("max_backlog", 5000)),
    )

    collectors = raw.get("collectors", {})
    return Config(
        backend_url=raw["backend_url"],
        listen_host=raw.get("listen_host", "0.0.0.0"),
        listen_port=int(raw.get("listen_port", 9500)),
        sysinfo_interval_seconds=int(collectors.get("sysinfo_interval_seconds", 300)),
        network_interval_seconds=int(collectors.get("network_interval_seconds", 60)),
        logs_interval_seconds=int(collectors.get("logs_interval_seconds", 60)),
        token_path=str(Path(path).parent / "token"),
        logs=logs_cfg,
    )
