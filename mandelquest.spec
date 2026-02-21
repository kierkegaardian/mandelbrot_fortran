# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


project_root = Path(__file__).resolve().parent
entry_script = project_root / "explorer.py"

binary_name = "mandelbrot_gen.exe" if sys.platform.startswith("win") else "mandelbrot_gen"
binary_path = project_root / binary_name
if not binary_path.exists():
    raise SystemExit(f"Missing renderer binary for packaging: {binary_path}")

datas = [
    (str(project_root / "assets"), "assets"),
]
binaries = [
    (str(binary_path), "."),
]


a = Analysis(
    [str(entry_script)],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MandelQuest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MandelQuest",
)
