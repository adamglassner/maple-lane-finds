"""Writes build/version_info.txt so the .exe's Properties > Details shows the game's name and version."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from game.version import APP_NAME, PUBLISHER, VERSION  # noqa: E402

major, minor, patch = (list(map(int, VERSION.split("."))) + [0, 0, 0])[:3]
text = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({major}, {minor}, {patch}, 0), prodvers=({major}, {minor}, {patch}, 0),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', '{PUBLISHER}'),
      StringStruct('FileDescription', '{APP_NAME}'),
      StringStruct('FileVersion', '{VERSION}'),
      StringStruct('InternalName', 'MapleLaneFinds'),
      StringStruct('LegalCopyright', 'Copyright 2026 {PUBLISHER}'),
      StringStruct('OriginalFilename', 'MapleLaneFinds.exe'),
      StringStruct('ProductName', '{APP_NAME}'),
      StringStruct('ProductVersion', '{VERSION}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
with open(os.path.join(ROOT, "build", "version_info.txt"), "w", encoding="utf-8") as f:
    f.write(text)
print("version info for", VERSION)
