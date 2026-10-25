"""Updates version.json for a published release, so installed games offer the update.

    python tools/prepare_release.py --installer dist/MapleLaneFinds-Setup-1.1.0.exe

The GitHub Action runs this automatically when you publish a release. Run it by hand only if you
upload releases yourself (then commit and push version.json AFTER the release is published)."""
import argparse
import datetime
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from game.version import REPO, VERSION  # noqa: E402
from release_notes import bullets  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--installer", required=True)
ap.add_argument("--version", default=VERSION)
args = ap.parse_args()
v = args.version.lstrip("vV")
h = hashlib.sha256()
with open(args.installer, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
data = {
    "latest_version": v,
    "release_date": datetime.date.today().isoformat(),
    "changelog": bullets(v) or ["Improvements and fixes."],
    "windows_installer_url": f"https://github.com/{REPO}/releases/download/v{v}/{os.path.basename(args.installer)}",
    "sha256": h.hexdigest(),
}
with open(os.path.join(ROOT, "version.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
print(json.dumps(data, indent=2))
