"""Automated play-through used to test the game (and the built .exe) without a person.

    MapleLaneFinds.exe --selftest            (or: python main.py --selftest)

It launches from the menu, checks the version, runs the update check offline, changes options,
plays a scene (tutorial, finding items, hint, preview), wins, and solves all five puzzles.
Screenshots go to MLF_SHOT_DIR if set. Results are written to selftest.txt in the save folder."""
import json
import os
import tempfile
import traceback

import pygame

from .version import VERSION


class Driver:
    def __init__(self):
        self.gen = None
        self.wait = 0
        self.results = []
        self.failed = False
        self.done = False
        self.shot_dir = os.environ.get("MLF_SHOT_DIR")
        if self.shot_dir:
            os.makedirs(self.shot_dir, exist_ok=True)

    # ------------------------------------------------------------ helpers
    def check(self, ok, what):
        self.results.append(("PASS" if ok else "FAIL", what))
        if not ok:
            self.failed = True

    def click(self, pos):
        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))

    def key(self, k):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=k, mod=0, unicode="", scancode=0))

    def find_button(self, app, label):
        top = app.top
        cands = list(getattr(top, "widgets", [])) + list(getattr(top, "win_buttons", [])) + list(getattr(top, "done_buttons", []))
        for w in cands:
            if getattr(w, "label", None) == label:
                return w
        return None

    def press(self, app, label):
        b = self.find_button(app, label)
        self.check(b is not None, f"button '{label}' exists on {type(app.top).__name__}")
        if b:
            self.click(b.rect.center)

    def shot(self, app, name):
        if self.shot_dir:
            app.draw()
            app.screenshot(os.path.join(self.shot_dir, f"{name}.png"))

    def tick(self, app, dt):
        if self.done:
            return
        if self.gen is None:
            self.gen = self.script(app)
        if self.wait > 0:
            self.wait -= 1
            return
        try:
            self.wait = next(self.gen) or 0
        except StopIteration:
            self.finish(app)
        except Exception:
            self.check(False, "exception: " + traceback.format_exc())
            self.finish(app)

    def finish(self, app):
        self.done = True
        app.running = False
        from .paths import data_file
        lines = [f"{s}  {w}" for s, w in self.results]
        summary = f"{'FAILED' if self.failed else 'ALL PASSED'}: {sum(1 for s, _ in self.results if s == 'PASS')} passed, " \
                  f"{sum(1 for s, _ in self.results if s == 'FAIL')} failed"
        text = "\n".join(lines + ["", summary])
        try:
            with open(data_file("selftest.txt"), "w", encoding="utf-8") as f:
                f.write(text)
            out = os.environ.get("MLF_SELFTEST_OUT")
            if out:
                with open(out, "w", encoding="utf-8") as f:
                    f.write(text)
        except OSError:
            pass
        print(text)

    # ------------------------------------------------------------ the play-through
    def script(self, app):
        from .hidden import HiddenScene
        from .menus import ChapterMap, MainMenu, OptionsScreen, UpdateDialog, start_puzzle
        from .puzzles import MazePuzzle, MemoryPuzzle, PatternPuzzle, SliderPuzzle, SpotPuzzle
        yield 20
        self.shot(app, "01_title")
        self.click((960, 600))
        yield 10
        self.check(isinstance(app.top, MainMenu), "title screen opens the main menu")
        self.check(f"v{VERSION}" in pygame.display.get_caption()[0], f"window title shows v{VERSION}")
        for _ in range(900):  # wait for the launch update check (expected to fail offline)
            if app.updater.state not in ("idle", "checking"):
                break
            yield 1
        yield 5
        self.check(app.updater.state == "failed", f"offline launch update check fails gracefully (state={app.updater.state})")
        self.check(any("Couldn't check for updates" in t[0] for t in app.toasts), "friendly 'couldn't check' message shown")
        self.shot(app, "02_menu")
        self.press(app, "Check for Updates")
        for _ in range(900):
            yield 1
            if isinstance(app.top, UpdateDialog) and app.updater.state == "failed":
                break
        yield 5
        self.check(isinstance(app.top, UpdateDialog) and app.top.title.startswith("Couldn't"), "manual update check shows friendly failure")
        self.shot(app, "03_update_offline")
        self.press(app, "OK")
        yield 5

        # ---- options
        self.press(app, "Options")
        yield 8
        o = app.top
        self.check(isinstance(o, OptionsScreen), "options screen opens")
        mv = app.settings["music_volume"]
        self.click(o.music.plus.rect.center)
        yield 4
        self.check(app.settings["music_volume"] > mv, f"music volume + works ({mv} -> {app.settings['music_volume']})")
        t = o.sfx.track
        p = (t.x + int(t.width * 0.3), t.centery)
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=p, button=1))
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=p, button=1))
        yield 4
        self.check(abs(app.settings["sfx_volume"] - 0.3) < 0.03, f"sfx slider works ({app.settings['sfx_volume']})")
        saved = json.load(open(app.settings.path))
        self.check(abs(saved["sfx_volume"] - app.settings["sfx_volume"]) < 1e-6, "settings saved to disk")
        self.click(o.diff.buttons[1].rect.center)
        yield 3
        self.check(app.settings["difficulty"] == "normal", "difficulty option works")
        self.click(o.text.buttons[1].rect.center)
        yield 3
        self.check(app.settings["text_size"] == "large", "text size option works")
        self.shot(app, "04_options_large_text")
        o = app.top
        self.click(o.text.buttons[0].rect.center)
        yield 2
        o = app.top
        self.click(o.diff.buttons[0].rect.center)
        yield 2
        self.click(o.mute.buttons[1].rect.center)
        yield 2
        self.check(app.settings["muted"] is True, "mute works")
        self.click(o.mute.buttons[0].rect.center)
        yield 2
        self.shot(app, "05_options")
        self.press(app, "Back")
        yield 5
        self.press(app, "How to Play")
        yield 5
        self.shot(app, "06_how_to_play")
        self.press(app, "Done")
        yield 4
        self.press(app, "Credits")
        yield 5
        self.shot(app, "07_credits")
        self.press(app, "Back")
        yield 4

        # ---- play chapter 1
        self.press(app, "Play")
        yield 8
        cm = app.top
        self.check(isinstance(cm, ChapterMap), "chapter map opens")
        self.shot(app, "08_chapter_map")
        self.click(cm.cards[0][0].center)
        yield 20
        sc = app.top
        self.check(isinstance(sc, HiddenScene), "scene 1 starts")
        self.check(sc.tutorial == 0, "tutorial shows on first level")
        self.shot(app, "09_tutorial")
        for i in range(5):
            if i == 3:
                self.shot(app, "10_tutorial_hint")
            self.click(sc.tut_btn.rect.center)
            yield 6
        self.check(sc.tutorial is None and app.progress.tutorial_done, "tutorial completes")
        yield 30
        self.shot(app, "11_scene")
        for tg in sc.targets[:3]:
            self.click((int(tg.x), int(tg.y)))
            yield 14
        self.check(len(sc.found) == 3, f"found 3 objects ({len(sc.found)})")
        self.click(sc.hint_btn.rect.center)
        yield 25
        self.check(sc.hints_used == 1 and sc.hint_target is not None, "hint button highlights an item")
        self.shot(app, "12_hint")
        rem = sc.remaining()
        self.click(sc.slots[rem[0].kind].center)
        yield 10
        self.shot(app, "13_preview")
        yield 160
        self.click(sc.menu_btn.rect.center)
        yield 6
        self.shot(app, "14_pause")
        self.press(app, "Keep Playing")
        yield 6
        for tg in sc.remaining():
            self.click((int(tg.x), int(tg.y)))
            yield 10
        yield 150
        self.check(bool(sc.win), "scene completes with win panel")
        ch1 = app.progress.chapter(1)
        self.check(ch1["scene_done"] and ch1["stars"] == 2, f"progress + stars saved ({ch1})")
        self.check(app.progress.unlocked(2), "chapter 2 unlocked")
        self.shot(app, "15_win")

        # ---- puzzle 1: memory (from the win screen)
        self.click(sc.win_buttons[0].rect.center)
        yield 20
        pz = app.top
        self.check(isinstance(pz, MemoryPuzzle), "memory puzzle opens from win screen")
        self.shot(app, "16_memory")
        groups = {}
        for i, c in enumerate(pz.cards):
            groups.setdefault(c["kind"], []).append(i)
        first = True
        for kind, (i, j) in groups.items():
            self.click(pz.card_rect(i).center)
            yield 12
            self.click(pz.card_rect(j).center)
            yield 18
            if first:
                self.shot(app, "17_memory_progress")
                first = False
        yield 60
        self.check(pz.solved and app.progress.chapter(1)["puzzle_done"], "memory puzzle solved and saved")
        self.shot(app, "18_puzzle_solved")
        app.pop()
        yield 5

        # ---- puzzle 2: spot the difference
        start_puzzle(app, 2)
        yield 10
        pz = app.top
        self.check(isinstance(pz, SpotPuzzle), "spot-the-difference opens")
        self.shot(app, "19_spot")
        for k, (dx, dy, _r) in enumerate(pz.diffs):
            self.click((int(pz.left_pos[0] + dx), int(pz.left_pos[1] + dy)))
            yield 12
            if k == 1:
                self.shot(app, "20_spot_progress")
        yield 50
        self.check(pz.solved, "spot-the-difference solved")
        app.pop()
        yield 5

        # ---- puzzle 3: sliding picture (uses the hint path)
        start_puzzle(app, 3)
        yield 10
        pz = app.top
        self.check(isinstance(pz, SliderPuzzle), "sliding puzzle opens")
        self.shot(app, "21_slider")
        pz.hint()
        yield 4
        self.shot(app, "22_slider_hint")
        for _ in range(400):
            if pz.solved:
                break
            m = pz.hint_move()
            if m is None:
                break
            self.click(pz.tile_rect(m).center)
            yield 2
        yield 50
        self.check(pz.solved, "sliding puzzle solved")
        app.pop()
        yield 5

        # ---- puzzle 4: corn maze
        start_puzzle(app, 4)
        yield 10
        pz = app.top
        self.check(isinstance(pz, MazePuzzle), "corn maze opens")
        pz.hint()
        yield 3
        self.shot(app, "23_maze_hint")
        path = pz.path_to_goal()
        keys = {(1, 0): pygame.K_RIGHT, (-1, 0): pygame.K_LEFT, (0, 1): pygame.K_DOWN, (0, -1): pygame.K_UP}
        for (c0, r0), (c1, r1) in zip(path, path[1:]):
            self.key(keys[(c1 - c0, r1 - r0)])
            yield 8
        yield 60
        self.check(pz.solved, "corn maze solved")
        app.pop()
        yield 5

        # ---- puzzle 5: harvest code
        start_puzzle(app, 5)
        yield 10
        pz = app.top
        self.check(isinstance(pz, PatternPuzzle), "pattern puzzle opens")
        self.shot(app, "24_pattern")
        first = True
        for _ in range(pz.rounds):
            wrong = [i for i, o in enumerate(pz.options) if o != pz.answer]
            if first and wrong:
                self.click(pz.opt_rect(wrong[0]).center)
                yield 6
                self.shot(app, "25_pattern_wrong")
                first = False
            i = pz.options.index(pz.answer)
            self.click(pz.opt_rect(i).center)
            yield 75
        yield 40
        self.check(pz.solved, "pattern puzzle solved")
        self.shot(app, "26_final")
        app.pop()
        yield 5

        # ---- update available path (local file, nothing is downloaded)
        tmp = os.path.join(tempfile.gettempdir(), "mlf_selftest_version.json")
        with open(tmp, "w") as f:
            json.dump({"latest_version": "9.9.9", "changelog": ["Test entry one", "Test entry two"],
                       "windows_installer_url": "https://example.invalid/setup.exe"}, f)
        old = os.environ.get("MLF_UPDATE_URL")
        os.environ["MLF_UPDATE_URL"] = "file:///" + tmp.replace("\\", "/").lstrip("/")
        while not isinstance(app.top, MainMenu) and len(app.stack) > 1:
            app.pop()
        yield 3
        app.push(UpdateDialog(app))
        for _ in range(300):
            yield 1
            if app.updater.state == "available":
                break
        yield 5
        self.check(app.updater.state == "available" and "9.9.9" in app.top.title, "newer version is offered with changelog (asks first)")
        self.check(app.updater.state != "downloading", "nothing downloads without the player's OK")
        self.shot(app, "27_update_available")
        if old is None:
            os.environ.pop("MLF_UPDATE_URL", None)
        else:
            os.environ["MLF_UPDATE_URL"] = old
        app.pop()
        yield 5
        self.check(isinstance(app.top, MainMenu), "back at main menu at the end")
