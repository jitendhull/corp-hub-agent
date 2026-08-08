# PyInstaller spec for corp-hub-agent (Linux x86_64).
# Build: pyinstaller packaging/linux.spec
# Output: dist/corp-hub-agent
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['../corp_hub_agent/agent.py'],
    pathex=['..'],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules('corp_hub_agent'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
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
