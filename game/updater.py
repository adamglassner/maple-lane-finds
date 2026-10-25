"""In-game updater.

* Reads version.json from the GitHub repo (see README for its format).
* If a newer version exists, the game shows the version + changelog and ASKS first - never silent.
* On "yes": downloads the new installer, checks its SHA-256 (when provided), backs up the current
  .exe into the save folder, runs the installer, and restarts the game afterwards.
* Saves live in %APPDATA%\\MapleLaneFinds, which the installer never touches, so progress is kept.
* Any failure (no internet, GitHub down, bad file) is caught and reported politely - the game keeps running.
"""
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

from .paths import data_dir, install_dir, is_frozen
from .version import APP_ID, VERSION, VERSION_URL

USER_AGENT = f"{APP_ID}-updater/{VERSION}"


class UpdateError(Exception):
    pass


def parse_version(v):
    v = str(v).strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        num = ""
        for ch in p:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(remote, local=VERSION):
    return parse_version(remote) > parse_version(local)


class UpdateInfo:
    def __init__(self, data):
        if not isinstance(data, dict):
            raise UpdateError("version.json is not an object")
        self.version = str(data.get("latest_version") or data.get("version") or "").strip()
        if not self.version:
            raise UpdateError("version.json has no latest_version")
        cl = data.get("changelog") or []
        if isinstance(cl, str):
            cl = [cl]
        self.changelog = [str(x) for x in cl][:12]
        self.url = str(data.get("windows_installer_url") or data.get("url") or "")
        self.sha256 = str(data.get("sha256") or "").lower().strip()
        self.release_date = str(data.get("release_date") or "")

    @property
    def newer(self):
        return is_newer(self.version)


def _ctx():
    try:
        return ssl.create_default_context()
    except Exception:
        return None


def _open(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
    return urllib.request.urlopen(req, timeout=timeout, context=_ctx()) if url.startswith("https") \
        else urllib.request.urlopen(req, timeout=timeout)


def fetch_latest(url=None, timeout=6):
    url = url or os.environ.get("MLF_UPDATE_URL") or VERSION_URL
    # cache-buster so GitHub's CDN doesn't hand back a stale file
    if url.startswith("http"):
        url += ("&" if "?" in url else "?") + f"t={int(time.time())}"
    try:
        with _open(url, timeout) as r:
            raw = r.read(256 * 1024)
        data = json.loads(raw.decode("utf-8-sig"))
    except UpdateError:
        raise
    except Exception as e:  # network down, DNS failure, timeout, bad JSON...
        raise UpdateError(str(e) or e.__class__.__name__)
    return UpdateInfo(data)


def download(url, dest, progress=None, sha256=None, timeout=20):
    if not url:
        raise UpdateError("No download link in version.json")
    h = hashlib.sha256()
    try:
        with _open(url, timeout) as r, open(dest, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = r.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                h.update(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)
    except Exception as e:
        raise UpdateError(f"Download failed: {e}")
    if sha256 and h.hexdigest().lower() != sha256:
        try:
            os.remove(dest)
        except OSError:
            pass
        raise UpdateError("The downloaded file didn't match its checksum, so it wasn't installed.")
    return dest


def backup_current(keep=2):
    """Copy the currently installed game into the save folder: backups\\v<version>\\."""
    root = os.path.join(data_dir(), "backups")
    dest = os.path.join(root, f"v{VERSION}")
    os.makedirs(dest, exist_ok=True)
    src_dir = install_dir()
    if is_frozen():
        shutil.copy2(sys.executable, os.path.join(dest, os.path.basename(sys.executable)))
    with open(os.path.join(dest, "backup_info.txt"), "w", encoding="utf-8") as f:
        f.write(f"Backup of {APP_ID} v{VERSION}\nInstalled at: {src_dir}\nMade: {time.ctime()}\n"
                f"To roll back, copy the .exe in this folder over the one in the install folder.\n")
    # prune old backups
    try:
        olds = sorted((d for d in os.listdir(root) if d.startswith("v")), key=lambda d: os.path.getmtime(os.path.join(root, d)))
        for d in olds[:-keep]:
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
    except OSError:
        pass
    return dest


def launch_installer(path):
    """Run the Inno Setup installer. /RELAUNCH=1 makes the installer start the game again when done."""
    args = [path, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS", "/RELAUNCH=1"]
    flags = 0
    if sys.platform.startswith("win"):
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(args, close_fds=True, creationflags=flags)


class UpdateManager:
    """Runs checks/downloads on a background thread; the UI polls .state."""

    IDLE, CHECKING, UP_TO_DATE, AVAILABLE, FAILED, DOWNLOADING, INSTALLING, ERROR = (
        "idle", "checking", "up_to_date", "available", "failed", "downloading", "installing", "error")

    def __init__(self):
        self.state = self.IDLE
        self.info = None
        self.message = ""
        self.progress = 0.0
        self.manual = False
        self._lock = threading.Lock()
        self.ready_to_quit = False

    def check(self, manual=False):
        with self._lock:
            if self.state in (self.CHECKING, self.DOWNLOADING, self.INSTALLING):
                return
            self.state = self.CHECKING
            self.manual = manual
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self):
        try:
            info = fetch_latest()
            self.info = info
            self.state = self.AVAILABLE if info.newer else self.UP_TO_DATE
        except Exception as e:
            self.message = str(e)
            self.state = self.FAILED

    def can_install(self):
        return is_frozen() and sys.platform.startswith("win")

    def install(self):
        if not self.info or self.state == self.DOWNLOADING:
            return
        self.state = self.DOWNLOADING
        self.progress = 0.0
        threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"{APP_ID}-update")
            os.makedirs(tmp, exist_ok=True)
            dest = os.path.join(tmp, f"{APP_ID}-Setup-{self.info.version}.exe")

            def prog(done, total):
                self.progress = (done / total) if total else 0.0

            download(self.info.url, dest, prog, self.info.sha256 or None)
            self.state = self.INSTALLING
            backup_current()
            launch_installer(dest)
            self.ready_to_quit = True
        except Exception as e:
            self.message = str(e)
            self.state = self.ERROR
