"""Prints the CHANGELOG.md section for a version (used for GitHub release notes and version.json)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bullets(version):
    out, on = [], False
    with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("## "):
                on = s[3:].strip().lstrip("vV") == version.lstrip("vV")
                continue
            if on and s.startswith("- "):
                out.append(s[2:])
    return out


if __name__ == "__main__":
    v = sys.argv[1]
    items = bullets(v) or ["Improvements and fixes."]
    print(f"## What's new in v{v.lstrip('vV')}\n")
    for b in items:
        print(f"- {b}")
    print("\n**Download:** `MapleLaneFinds-Setup-" + v.lstrip("vV") + ".exe` below. Players who already have the game "
          "will be offered this update automatically the next time they start it.")
