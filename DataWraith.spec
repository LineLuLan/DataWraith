# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the secondary DataWraith executable.

Primary distribution remains `pip install datawraith`; this spec is for Phase 2
local executable smoke builds and CI artifacts.
"""

from PyInstaller.utils.hooks import collect_submodules


hiddenimports = collect_submodules("datawraith")

a = Analysis(
    ["datawraith/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="sdb",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
