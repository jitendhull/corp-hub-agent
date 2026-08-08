# Corp-Hub Agent

Lightweight, cross-platform push agent for **Corp-Hub Corporate Monitoring System**.

The agent runs as a background service on endpoints (Linux or Windows), collecting metrics, system specs, active network sockets, and system logs, then pushing them securely to your central Corp-Hub server.

---

## 🚀 One-Line Installation

### Linux (Ubuntu, Debian, RHEL, Alpine)
Run in terminal as root:
```bash
curl -fsSL https://raw.githubusercontent.com/jitendhull/corp-hub-agent/main/install/install.sh | \
  sudo bash -s -- --backend-url http://YOUR_CORP_HUB_HOST:8000
```

- Installs binary to `/usr/local/bin/corp-hub-agent-linux-x86_64`
- Creates configuration at `/etc/corp-hub-agent/agent.conf`
- Enables and starts `corp-hub-agent` systemd background service.

---

### Windows 10/11 / Windows Server
Run in **Administrator PowerShell**:
```powershell
iex (iwr -UseBasicParsing https://raw.githubusercontent.com/jitendhull/corp-hub-agent/main/install/install.ps1).Content -BackendUrl "http://YOUR_CORP_HUB_HOST:8000"
```

- Installs binary to `C:\Program Files\CorpHubAgent\corp-hub-agent-windows-x86_64.exe`
- Creates configuration at `C:\ProgramData\CorpHubAgent\agent.conf`
- Automatically adds Windows Defender folder exclusion to prevent false positives.
- Registers and starts `CorpHubAgent` Windows background service.

---

## 🛠️ Requirements & System Impact

| Metric | Requirement |
|---|---|
| **OS** | Linux (kernel 3.10+), Windows 10/11/Server 2016+ |
| **RAM usage** | ~15MB to 30MB |
| **CPU usage** | < 0.1% idle / periodic scan spikes |
| **Outbound Ports** | Port 8000 (or your custom HTTP/HTTPS port to Corp-Hub) |
| **Inbound Ports** | **None** (Push-only architecture; no listening ports required) |

---

## 🔒 Security & Data Privacy

1. **Token Authentication**: On first startup, the agent performs a one-time registration with the Corp-Hub backend to mint a unique 64-character token (`X-Agent-Token`).
2. **Minimal Privileges**:
   - On Linux, system logs (`/var/log/auth.log`, `journald`) are read strictly for security audit purposes.
   - On Windows, standard Event Logs (`Application`, `System`, `Security`) are parsed via native Windows APIs (`wevtapi.dll`).
3. **No External Dependencies**: Compiled into zero-dependency standalone binaries via PyInstaller.

---

## 📊 Collected Metrics & Push Schedule

| Collector | Intervals | Data Collected |
|---|---|---|
| **Metrics** | 60s | CPU %, Memory %, Disk %, System Uptime |
| **Network** | 60s | Active TCP sockets (ESTABLISHED, LISTEN), Local/Remote IPs & Ports, PIDs |
| **Logs** | 60s | Tail of syslog, auth.log, journald (Linux) or Event Logs (Windows) |
| **Sysinfo** | 300s (5m) | OS version, Kernel, Architecture, CPU model, total RAM/Disk |

---

## ⚙️ Configuration Reference

File path:
- **Linux**: `/etc/corp-hub-agent/agent.conf`
- **Windows**: `C:\ProgramData\CorpHubAgent\agent.conf`

```toml
backend_url = "http://hermes:8000"
listen_host = "0.0.0.0"
listen_port = 9500

[collectors]
sysinfo_interval_seconds = 300
network_interval_seconds = 60
logs_interval_seconds = 60

[logs]
sources = ["journald", "syslog", "auth.log"] # Linux
# sources = ["Application", "System", "Security"] # Windows
max_lines_per_push = 500
max_backlog = 5000
```

---

## 🛠️ Management Commands

### Linux (Systemd)
```bash
# View service status
sudo systemctl status corp-hub-agent

# View live logs
sudo journalctl -u corp-hub-agent -f

# Restart agent
sudo systemctl restart corp-hub-agent
```

### Windows (PowerShell / Services)
```powershell
# View status
Get-Service CorpHubAgent

# Restart service
Restart-Service CorpHubAgent

# View logs
Get-Content "C:\ProgramData\CorpHubAgent\agent.log" -Tail 50 -Wait
```

---

## 📦 Building from Source (Developers)

```bash
git clone https://github.com/jitendhull/corp-hub-agent.git
cd corp-hub-agent

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -e .

# Run locally
corp-hub-agent --config /etc/corp-hub-agent/agent.conf

# Build Standalone PyInstaller Binaries
pip install pyinstaller
pyinstaller packaging/linux.spec     # Output: dist/corp-hub-agent-linux-x86_64
pyinstaller packaging/windows.spec   # Output: dist/corp-hub-agent-windows-x86_64.exe
```
