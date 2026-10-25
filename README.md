# Maple Lane Finds

A cozy autumn hidden-object game for Windows 10 and 11, made by **Ironite**.

Wander through a pumpkin patch, a sunny harvest barn, a little bakery, a corn maze garden and a fall fair.
Find ten hidden items in each picture, then relax with a puzzle. No timers in Relaxed mode, no ads,
no accounts, no internet needed. Family-friendly harvest fun.

## Features

- 5 hand-painted HD scenes (1920x1080), 10 items to find in each, 40 different objects
- 5 puzzles: Pumpkin Pairs (memory match), Barn Differences (spot the difference), Pie Picture Slide
  (sliding picture), Corn Maze Path (maze) and Harvest Code (patterns)
- Big buttons, big text (3 text sizes), a friendly tutorial, hints with a short refill timer
- Relaxed / Normal / Challenge difficulty, up to 3 stars per scene, progress saves automatically
- Gentle folk-style music and sound effects with separate volume controls and mute
- Windowed or fullscreen (F11 also toggles)
- Built-in updater that checks this GitHub repo and always asks before installing

Every picture, sound and song is created by code written for this game, so there are no outside or
copyrighted assets.

## For players

Download `MapleLaneFinds-Setup-x.y.z.exe` from the [Releases page](https://github.com/adamglassner/maple-lane-finds/releases)
and run it. It installs for your user account (no admin password needed), adds a Start Menu shortcut,
offers a Desktop shortcut, and can be removed from Windows Settings > Apps like any other program.

Windows SmartScreen may say "Windows protected your PC" because the game isn't code-signed.
Click **More info** then **Run anyway**.

**Your saves** live in `%APPDATA%\MapleLaneFinds\` (settings.json and progress.json). Updates and
uninstalling never delete them.

## Building the game yourself

You need, on a Windows PC:

1. **Python 3.12** from https://www.python.org/downloads/ (tick *Add python.exe to PATH* when installing)
2. **Inno Setup 6** from https://jrsoftware.org/isdl.php (only needed for the installer)

Then double-click **`build_windows.bat`** (or run it in a Command Prompt from the repo folder).
The first run takes a few minutes while it sets up. When it finishes you'll have:

| File | What it is |
| --- | --- |
| `dist\MapleLaneFinds.exe` | The whole game in one file. Runs on any Windows 10/11 PC without Python. |
| `dist\MapleLaneFinds-Setup-1.0.0.exe` | The installer to share with players. |

To just run the game from source while developing: `pip install -r requirements.txt` then `python main.py`.

### Automatic cloud builds

You don't even need to build locally. Every push to `main` makes GitHub Actions
(`.github/workflows/build.yml`) build the .exe and installer on a Windows machine, run the
automated play-through test on the real .exe, and create or refresh a **draft release** with the
installer attached. Drafts are only visible to you.

## Releasing an update (how the updater gets new versions)

1. Change `VERSION` in `game/version.py` (for example `"1.1.0"`).
2. Add a `## v1.1.0` section with a few friendly bullet points to the top of `CHANGELOG.md`.
   Players see these bullets in the "update available" window.
3. Commit and push to `main`. GitHub builds and tests it and makes a draft release `v1.1.0`.
4. On GitHub, open **Releases**, check the draft, and click **Publish release**.
5. That's it. Publishing automatically updates `version.json` on `main` (new version number,
   changelog, download link and SHA-256 checksum). The next time anyone starts the game it offers
   the update.

**Doing it by hand instead:** build with `build_windows.bat`, create a release named `v1.1.0` and upload
`dist\MapleLaneFinds-Setup-1.1.0.exe` to it, publish it, then run
`python tools\prepare_release.py --installer dist\MapleLaneFinds-Setup-1.1.0.exe` and commit + push the
updated `version.json`. Always publish the release *before* pushing `version.json`.

### How the updater works

- On launch (quietly, in the background) and from **Check for Updates**, the game reads
  `https://raw.githubusercontent.com/adamglassner/maple-lane-finds/main/version.json`.
- If that version is newer, it shows the version number and changelog and asks. It never updates silently.
- If the player says yes it downloads the installer, checks its SHA-256, backs up the current game to
  `%APPDATA%\MapleLaneFinds\backups\v<old version>\`, runs the installer, and the game restarts itself.
- No internet or GitHub unreachable? The game opens and plays normally and just says it couldn't check.

`version.json` format:

```json
{
  "latest_version": "1.1.0",
  "release_date": "2026-11-20",
  "changelog": ["New thing one", "New thing two"],
  "windows_installer_url": "https://github.com/adamglassner/maple-lane-finds/releases/download/v1.1.0/MapleLaneFinds-Setup-1.1.0.exe",
  "sha256": "checksum of that installer (tools/prepare_release.py fills this in)"
}
```

## Testing

`python main.py --selftest` plays through the whole game by itself in a throwaway save folder: title
and menu, version check, offline update check, options (volumes, mute, difficulty, text size), the
tutorial, finding items, a hint, winning a scene, all five puzzles, and the "update available" prompt.
It prints PASS/FAIL for each step. Add `--headless` to run without a window, and set `MLF_SHOT_DIR` to a
folder to save screenshots. The cloud build runs this same test on the finished .exe.

## Project layout

```
main.py                 starts the game (and the --selftest mode)
game/                   all game code
  version.py            version number and update settings  <- change VERSION here
  app.py                window, main loop, screen stack
  menus.py              title, main menu, options, how to play, credits, chapter map, dialogs
  hidden.py             hidden-object scenes, hints, tutorial, stars
  puzzles.py            the five puzzles
  levels.py             chapters, item lists, difficulty settings
  synth.py / audio.py   procedurally generated music and sound
  updater.py            GitHub update checker / installer
  storage.py, paths.py  saves in %APPDATA%\MapleLaneFinds
  selftest.py           automated play-through test
assets/                 generated art (scenes, objects, logo, icon)
tools/                  art generator (make_art.py), release helpers
installer/              Inno Setup script
build_windows.bat       one-click Windows build
MapleLaneFinds.spec     PyInstaller recipe
version.json            what the in-game updater reads
```

To redraw the artwork: `pip install -r requirements-art.txt` then `python tools/make_art.py`.

## Credits

Game design, programming, art, music and sound: Ironite. Built with Python,
[pygame-ce](https://pyga.me) (LGPL) and [NumPy](https://numpy.org) (BSD). Fonts: Georgia and Segoe UI,
which come with Windows.

Copyright 2026 Ironite. All rights reserved.
