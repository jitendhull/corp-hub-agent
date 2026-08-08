#!/usr/bin/env bash
# Cross-platform build script for Corp-Hub Agent PyInstaller binaries.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Cleaning old build artifacts"
rm -rf build dist

echo "==> Ensuring venv & dependencies"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q pyinstaller psutil httpx

OS="$(uname -s)"
case "$OS" in
    Linux*)
        echo "==> Building Linux binary"
        pyinstaller --clean packaging/linux.spec
        echo "==> Built: dist/corp-hub-agent-linux-$(uname -m)"
        ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
        echo "==> Building Windows binary"
        pyinstaller --clean packaging/windows.spec
        echo "==> Built: dist/corp-hub-agent-windows-x86_64.exe"
        ;;
    *)
        echo "ERROR: Unsupported OS $OS" >&2
        exit 1
        ;;
esac

echo "==> Build complete! Output files:"
ls -lh dist/
