#!/usr/bin/env bash
# Corp-Hub Agent installer (Linux).
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/<ORG>/corp-hub-agent/main/install/install.sh | \
#     sudo bash -s -- --backend-url http://192.168.1.10:8000
set -euo pipefail

ORG="jitendhull"   # GitHub org/user for release download
REPO="corp-hub-agent"
CONF_DIR="/etc/corp-hub-agent"
BIN="/usr/local/bin/corp-hub-agent"
SERVICE="corp-hub-agent.service"
SERVICE_DIR="/etc/systemd/system"

BACKEND_URL=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend-url) BACKEND_URL="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --org) ORG="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$BACKEND_URL" ]]; then
  echo "ERROR: --backend-url is required (e.g. http://192.168.1.10:8000)" >&2
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run as root (sudo)" >&2
  exit 1
fi

echo "==> Corp-Hub Agent installer (org=$ORG, backend=$BACKEND_URL)"

# 1. Detect distro + package manager
PKG=""
if command -v apt-get >/dev/null 2>&1; then PKG=apt
elif command -v dnf >/dev/null 2>&1; then PKG=dnf
elif command -v apk >/dev/null 2>&1; then PKG=apk
else
  echo "ERROR: unsupported package manager (apt/dnf/apk)" >&2
  exit 1
fi
echo "==> Package manager: $PKG"

# 2. Ensure Python 3.11+ (for binary distribution this is optional;
#    PyInstaller bundles the interpreter. Only needed when running from source.)
PY_OK=0
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
  PY_OK=1
fi

# 3. Download release binary from GitHub
VERSION="${VERSION:-latest}"
ARCH=$(uname -m)
case "$ARCH" in
  x86_64) ASSET="corp-hub-agent-linux-x86_64" ;;
  aarch64) ASSET="corp-hub-agent-linux-aarch64" ;;
  *) echo "ERROR: unsupported arch $ARCH" >&2; exit 1 ;;
esac

if [[ "$VERSION" == "latest" ]]; then
  URL="https://github.com/${ORG}/${REPO}/releases/latest/download/${ASSET}"
else
  URL="https://github.com/${ORG}/${REPO}/releases/download/${VERSION}/${ASSET}"
fi
echo "==> Downloading ${URL}"
curl -fsSL "$URL" -o "${BIN}.tmp"
chmod 755 "${BIN}.tmp"
mv "${BIN}.tmp" "$BIN"
echo "==> Installed $BIN"

# 4. Write config
mkdir -p "$CONF_DIR"
if [[ ! -f "$CONF_DIR/agent.conf" ]]; then
  cat > "$CONF_DIR/agent.conf" <<EOF
backend_url = "${BACKEND_URL}"
listen_host = "0.0.0.0"
listen_port = 9500

[collectors]
sysinfo_interval_seconds = 300
network_interval_seconds = 60
logs_interval_seconds = 60

[logs]
sources = ["journald", "syslog", "auth.log"]
syslog_path = "/var/log/syslog"
auth_log_path = "/var/log/auth.log"
max_lines_per_push = 500
max_backlog = 5000
EOF
  echo "==> Wrote $CONF_DIR/agent.conf"
else
  echo "==> $CONF_DIR/agent.conf exists, keeping"
fi

# 5. Register (mints token on first run)
echo "==> Registering with backend"
"$BIN" register --config "$CONF_DIR/agent.conf" || \
  "$BIN" --config "$CONF_DIR/agent.conf" --register-once || true

# 6. systemd unit
echo "==> Installing systemd unit"
cp "$(dirname "$0")/corp-hub-agent.service" "$SERVICE_DIR/$SERVICE" 2>/dev/null || {
  cat > "$SERVICE_DIR/$SERVICE" <<'UNIT'
[Unit]
Description=Corp-Hub Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/corp-hub-agent --config /etc/corp-hub-agent/agent.conf
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
}

systemctl daemon-reload
systemctl enable --now "$SERVICE"

echo "==> Done. Status:"
systemctl --no-pager --lines=5 status "$SERVICE"
