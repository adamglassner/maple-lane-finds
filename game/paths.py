"""Where things live: bundled assets (inside the .exe) and the player's save folder
(%APPDATA%\\MapleLaneFinds on Windows - outside the install folder, so updates never touch it)."""
import os
import sys

from .version import APP_ID


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def resource_root():
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset(*parts):
    return os.path.join(resource_root(), "assets", *parts)


def data_dir():
    override = os.environ.get("MLF_DATA_DIR")
    if override:
        base = override
    elif sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_ID)
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~/Library/Application Support"), APP_ID)
    else:
        base = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"), APP_ID)
    os.makedirs(base, exist_ok=True)
    return base


def data_file(*parts):
    p = os.path.join(data_dir(), *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def install_dir():
    """Folder the running .exe lives in (only meaningful when frozen)."""
    return os.path.dirname(os.path.abspath(sys.executable)) if is_frozen() else resource_root()
