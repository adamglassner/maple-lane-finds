"""Used by the GitHub Action: create the draft release for this version, or refresh it.
A published release is never touched. Accidental duplicate drafts for the same tag are removed."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from release_notes import bullets  # noqa: E402


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        print("gh", *args, "\n", r.stdout, r.stderr, file=sys.stderr)
        raise SystemExit(r.returncode)
    return r.stdout


def main():
    v = sys.argv[1].lstrip("vV")
    tag = f"v{v}"
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = os.environ.get("GITHUB_SHA", "main")
    setup = os.path.join("dist", f"MapleLaneFinds-Setup-{v}.exe")
    notes = "## What's new in v%s\n\n%s\n\n**Download:** `MapleLaneFinds-Setup-%s.exe` below. Players who already have " \
            "the game will be offered this update automatically the next time they start it." % (
                v, "\n".join("- " + b for b in (bullets(v) or ["Improvements and fixes."])), v)
    with open("notes.md", "w", encoding="utf-8") as f:
        f.write(notes)
    rels = [r for r in json.loads(gh("api", f"repos/{repo}/releases?per_page=100")) if r.get("tag_name") == tag]
    if any(not r["draft"] for r in rels):
        print(f"Release {tag} is already published, so it is left alone. Bump VERSION in game/version.py for a new one.")
        return
    if not rels:
        gh("release", "create", tag, setup, "--draft", "--title", f"Maple Lane Finds {tag}", "--notes-file", "notes.md",
           "--target", sha)
        print(f"Created draft release {tag}")
        return
    rels.sort(key=lambda r: r["created_at"], reverse=True)
    keep = rels[0]
    for r in rels[1:]:
        gh("api", "-X", "DELETE", f"repos/{repo}/releases/{r['id']}")
        print("Removed duplicate draft", r["id"])
    gh("api", "-X", "PATCH", f"repos/{repo}/releases/{keep['id']}", "-F", "body=@notes.md", "-f", f"target_commitish={sha}")
    gh("release", "upload", tag, setup, "--clobber", "--repo", repo)
    print(f"Refreshed draft release {tag}")


if __name__ == "__main__":
    main()
