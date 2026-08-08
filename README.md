# Corp-Hub Agent

Lightweight push agent for Corp-Hub. Collects system info, network
connections, and log lines from a host and pushes them to the Corp-Hub
backend. Linux first; Windows support structured but not yet built.

## How it works

```
host ── POST /api/agents/register ──► backend (one-time, mints token)
host ── POST /api/agents/{id}/sysinfo ──► backend (every 5m)
host ── POST /api/agents/{id}/network ──► backend (every 1m)
host ── POST /api/agents/{id}/logs    ──► backend (every 1m)
```

- Auth: `X-Agent-Token` header, per-host 64-char hex token minted by the
  backend at registration. Token stored at `/etc/corp-hub-agent/token`
  (Linux, chmod 600) or `%PROGRAMDATA%\CorpHubAgent\token` (Windows).
- Push model only. The agent never accepts inbound connections in v1
  (endpoint URL advertised at registration is reserved for future pull).

## Install (Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/jitendhull/corp-hub-agent/main/install/install.sh | \
  sudo bash -s -- --backend-url http://hermes:8000
```

Creates `/usr/local/bin/corp-hub-agent`, writes config + token, installs
and starts a systemd unit. Token is minted on first run.

## Run from source

```bash
pip install -e .
corp-hub-agent --config /etc/corp-hub-agent/agent.conf
```

## Config

See `conf/agent.conf.example`. Key fields:

| key | default | meaning |
|-----|---------|---------|
| `backend_url` | (required) | Corp-Hub backend base URL |
| `listen_host` / `listen_port` | `0.0.0.0` / `9500` | advertised pull endpoint (unused in v1) |
| `sysinfo_interval_seconds` | 300 | sysinfo push interval |
| `network_interval_seconds` | 60 | network push interval |
| `logs_interval_seconds` | 60 | logs push interval |
| `logs.sources` | `journald, syslog, auth.log` | which log sources to collect |

## Development

```bash
python -m pytest tests/
```

## Packaging

```bash
# Linux (PyInstaller)
pyinstaller packaging/linux.spec
# output: dist/corp-hub-agent
```

Windows packaging stubbed (`packaging/windows.spec`), not built yet.
