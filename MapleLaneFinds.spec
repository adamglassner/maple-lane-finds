# PyInstaller recipe for a single-file, windowed Windows .exe.  Used by build_windows.bat.
# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
here = os.path.abspath(SPECPATH)

a = Analysis(
    ["main.py"],
    pathex=[here],
    binaries=[],
    datas=[(os.path.join(here, "assets"), "assets")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc", "PIL", "matplotlib", "scipy", "IPython", "pytest"],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MapleLaneFinds",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join(here, "assets", "icon.ico"),
    version=os.path.join(here, "build", "version_info.txt"),
)
