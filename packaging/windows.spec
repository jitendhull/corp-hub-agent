# PyInstaller spec for corp-hub-agent (Windows) — STUB for v1.
# Build on Windows: pyinstaller packaging/windows.spec
# Output: dist/corp-hub-agent-windows-x86_64.exe
import sys
import platform
from PyInstaller.utils.hooks import collect_submodules

arch = platform.machine().lower()
if arch in ['amd64', 'x86_64']:
    arch_str = 'x86_64'
elif arch in ['x86', 'i386']:
    arch_str = 'x86'
else:
    arch_str = arch

asset_name = f"corp-hub-agent-windows-{arch_str}"

a = Analysis(
    ['..\\corp_hub_agent\\__main__.py'],
    pathex=['..'],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules('corp_hub_agent') + ['win32evtlog', 'win32security'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=asset_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
