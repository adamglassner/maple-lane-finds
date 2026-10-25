"""Settings and progress, saved as small JSON files in the player's save folder.
Writes are atomic (write to a temp file, then replace) so a crash can't corrupt a save."""
import json
import os

from .paths import data_file

NUM_CHAPTERS = 5


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, type(default)) else default
    except (OSError, ValueError):
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


class Settings:
    DEFAULTS = {
        "music_volume": 0.55,
        "sfx_volume": 0.8,
        "muted": False,
        "fullscreen": False,
        "difficulty": "relaxed",   # relaxed | normal | challenge
        "text_size": "normal",     # normal | large | xlarge
    }
    DIFFICULTIES = ("relaxed", "normal", "challenge")
    TEXT_SIZES = ("normal", "large", "xlarge")

    def __init__(self):
        self.path = data_file("settings.json")
        raw = load_json(self.path, {})
        self.data = dict(self.DEFAULTS)
        for k, v in raw.items():
            if k in self.DEFAULTS and type(v) is type(self.DEFAULTS[k]) or (k in ("music_volume", "sfx_volume") and isinstance(v, (int, float))):
                self.data[k] = v
        self.data["music_volume"] = min(1.0, max(0.0, float(self.data["music_volume"])))
        self.data["sfx_volume"] = min(1.0, max(0.0, float(self.data["sfx_volume"])))
        if self.data["difficulty"] not in self.DIFFICULTIES:
            self.data["difficulty"] = "relaxed"
        if self.data["text_size"] not in self.TEXT_SIZES:
            self.data["text_size"] = "normal"

    def __getitem__(self, k):
        return self.data[k]

    def set(self, k, v):
        self.data[k] = v
        self.save()

    def save(self):
        return save_json(self.path, self.data)


class Progress:
    def __init__(self):
        self.path = data_file("progress.json")
        raw = load_json(self.path, {})
        self.data = {"tutorial_done": False, "chapters": {}, "scene_state": {}}
        if isinstance(raw.get("tutorial_done"), bool):
            self.data["tutorial_done"] = raw["tutorial_done"]
        chapters = raw.get("chapters") if isinstance(raw.get("chapters"), dict) else {}
        for n in range(1, NUM_CHAPTERS + 1):
            c = chapters.get(str(n), {}) if isinstance(chapters.get(str(n)), dict) else {}
            self.data["chapters"][str(n)] = {
                "scene_done": bool(c.get("scene_done", False)),
                "stars": int(c.get("stars", 0)) if isinstance(c.get("stars", 0), int) else 0,
                "best_time": c.get("best_time") if isinstance(c.get("best_time"), (int, float)) else None,
                "puzzle_done": bool(c.get("puzzle_done", False)),
            }
        ss = raw.get("scene_state")
        if isinstance(ss, dict):
            self.data["scene_state"] = {k: v for k, v in ss.items() if isinstance(v, dict)}

    def save(self):
        return save_json(self.path, self.data)

    def chapter(self, n):
        return self.data["chapters"][str(n)]

    def unlocked(self, n):
        return n == 1 or self.chapter(n - 1)["scene_done"]

    def total_stars(self):
        return sum(self.chapter(n)["stars"] for n in range(1, NUM_CHAPTERS + 1))

    def record_scene(self, n, stars, seconds):
        c = self.chapter(n)
        c["scene_done"] = True
        c["stars"] = max(c["stars"], stars)
        if c["best_time"] is None or seconds < c["best_time"]:
            c["best_time"] = round(seconds, 1)
        self.data["scene_state"].pop(str(n), None)
        self.save()

    def record_puzzle(self, n):
        self.chapter(n)["puzzle_done"] = True
        self.save()

    def get_scene_state(self, n):
        return self.data["scene_state"].get(str(n))

    def set_scene_state(self, n, state):
        self.data["scene_state"][str(n)] = state
        self.save()

    def clear_scene_state(self, n):
        self.data["scene_state"].pop(str(n), None)
        self.save()

    @property
    def tutorial_done(self):
        return self.data["tutorial_done"]

    def set_tutorial_done(self, v=True):
        self.data["tutorial_done"] = v
        self.save()
