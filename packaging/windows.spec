# PyInstaller spec for corp-hub-agent (Windows) — STUB for v1.
# Build on Windows: pyinstaller packaging/windows.spec
# Output: dist/corp-hub-agent.exe
import sys
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['..\\corp_hub_agent\\agent.py'],
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
    name='corp-hub-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
