"""Title screen, main menu, options, how-to-play, credits, dialogs and the chapter map."""
import math
import pygame

from .app import Screen
from .levels import CHAPTERS, DIFFICULTY
from .storage import NUM_CHAPTERS
from .ui import (COL, W, H, Button, Slider, Toggle, dim, draw_panel, draw_paragraph, draw_star, draw_text,
                 draw_check, render_text)
from .version import APP_NAME, VERSION


def backdrop(app, name="pumpkin_patch", blur=True, tint=(255, 226, 180), tint_alpha=70):
    key = ("backdrop", name, blur, tint, tint_alpha)
    cache = app.assets._img
    if key not in cache:
        src = app.assets.scene(name)
        s = src
        if blur:
            small = pygame.transform.smoothscale(src, (W // 6, H // 6))
            s = pygame.transform.smoothscale(small, (W, H))
        s = s.copy()
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((*tint, tint_alpha))
        s.blit(ov, (0, 0))
        cache[key] = s
    return cache[key]


def logo(app, size):
    key = ("logo", size)
    cache = app.assets._img
    if key not in cache:
        cache[key] = pygame.transform.smoothscale(app.assets.image("logo.png"), (size, size))
    return cache[key]


def title_text(app, surf, center, kind="title"):
    f = app.fonts.fit(kind, APP_NAME, 900)
    draw_text(surf, APP_NAME, f, (255, 244, 220), center, shadow=(80, 40, 16))


# ====================================================================== dialogs
class Dialog(Screen):
    opaque = False

    def __init__(self, app, title, body, buttons, width=1000):
        super().__init__(app)
        self.title = title
        self.body = body
        self.button_specs = buttons  # list of (label, callback, style)
        self.width = width

    def layout(self):
        f = self.app.fonts.get("body")
        from .ui import wrap
        lines = wrap(self.body, f, self.width - 120) if self.body else []
        lh = int(f.get_linesize() * 1.18)
        th = self.app.fonts.get("h1").get_height()
        bh = 96
        h = 70 + th + 30 + len(lines) * lh + 50 + bh + 60
        self.rect = pygame.Rect(0, 0, self.width, h)
        self.rect.center = (W // 2, H // 2)
        n = len(self.button_specs)
        gap = 30
        bw = min(380, (self.width - 120 - gap * (n - 1)) // max(1, n))
        total = bw * n + gap * (n - 1)
        x = self.rect.centerx - total // 2
        self.widgets = []
        for label, cb, style in self.button_specs:
            self.widgets.append(Button(self.app, (x, self.rect.bottom - 60 - bh, bw, bh), label, cb, style=style))
            x += bw + gap

    def close(self):
        if self.app.top is self:
            self.app.pop()

    def draw(self, surf):
        dim(surf, 120)
        draw_panel(surf, self.rect)
        f = self.app.fonts.fit("h1", self.title, self.width - 80)
        draw_text(surf, self.title, f, COL["ink"], (self.rect.centerx, self.rect.top + 70), "midtop")
        if self.body:
            r = pygame.Rect(self.rect.x + 60, self.rect.top + 70 + f.get_height() + 30, self.width - 120, 400)
            draw_paragraph(surf, self.body, self.app.fonts.get("body"), COL["ink_soft"], r)
        super().draw(surf)

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        super().handle(event)
        return True  # modal


class UpdateDialog(Dialog):
    """Check for updates / show what's new / ask before installing. Never updates silently."""

    def __init__(self, app, start_check=True):
        super().__init__(app, "Check for Updates", "", [], width=1120)
        if start_check:
            app.updater.check(manual=True)
        self.shown_state = None
        self._texts()

    def _texts(self):
        u = self.app.updater
        st = u.state
        self.shown_state = st
        close = ("OK", self.close, "primary")
        if st in (u.CHECKING, u.IDLE):
            self.title, self.body, self.button_specs = "Checking for updates...", "Just a moment.", [("Cancel", self.close, "normal")]
        elif st == u.UP_TO_DATE:
            self.title = "You're up to date!"
            self.body = f"You have the newest version of {APP_NAME} (v{VERSION})."
            self.button_specs = [close]
        elif st == u.FAILED:
            self.title = "Couldn't check for updates"
            self.body = ("We couldn't reach the update server. That's okay! You might be offline. "
                         "You can keep playing, and try again any time from the main menu.")
            self.button_specs = [close]
        elif st == u.AVAILABLE:
            info = u.info
            self.title = f"Version {info.version} is available!"
            changes = "\n".join("- " + c for c in info.changelog) or "- Improvements and fixes"
            self.body = f"You have v{VERSION}. What's new:\n{changes}\n\nYour progress and settings will be kept."
            if u.can_install():
                self.button_specs = [("Not Now", self.close, "normal"), ("Download & Install", u.install, "primary")]
            else:
                self.body += "\n\n(Automatic install works in the installed Windows game.)"
                self.button_specs = [close]
        elif st == u.DOWNLOADING:
            self.title = "Downloading update..."
            self.body = "Please wait. This can take a minute on slower connections."
            self.button_specs = []
        elif st == u.INSTALLING:
            self.title = "Installing update..."
            self.body = "Your old version has been backed up. The game will close, update, and open again by itself."
            self.button_specs = []
        else:  # ERROR
            self.title = "The update didn't finish"
            self.body = f"Nothing was changed, so you can keep playing your current version.\n({u.message})"
            self.button_specs = [close]

    def update(self, dt):
        if self.app.updater.state != self.shown_state:
            self._texts()
            self.layout()
        super().update(dt)

    def draw(self, surf):
        super().draw(surf)
        u = self.app.updater
        if u.state in (u.CHECKING, u.DOWNLOADING, u.INSTALLING):
            cx, cy = self.rect.centerx, self.rect.bottom - 110
            if u.state == u.DOWNLOADING and u.progress > 0:
                bar = pygame.Rect(0, 0, 700, 34)
                bar.center = (cx, cy)
                pygame.draw.rect(surf, (226, 210, 186), bar, border_radius=17)
                pygame.draw.rect(surf, COL["orange"], (bar.x, bar.y, int(bar.width * u.progress), bar.height), border_radius=17)
                draw_text(surf, f"{int(u.progress * 100)}%", self.app.fonts.get("small"), COL["ink"], bar.center)
            else:
                for i in range(8):
                    a = self.app.time * 4 + i * math.tau / 8
                    r = 12 if i == 0 else 9
                    col = COL["orange"] if i < 3 else (230, 200, 160)
                    pygame.draw.circle(surf, col, (int(cx + math.cos(a) * 46), int(cy + math.sin(a) * 46)), r)


# ====================================================================== title & menu
class TitleScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONUP or (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE)):
            self.app.audio.play("click")
            self.app.replace(MainMenu(self.app))
            return True
        return False

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        surf.blit(self.app.assets.scene("pumpkin_patch"), (0, 0))
        dim(surf, 60, (255, 210, 150))
        bob = math.sin(self.t * 1.6) * 8
        lg = logo(self.app, 520)
        surf.blit(lg, lg.get_rect(center=(W // 2, 400 + bob)))
        title_text(self.app, surf, (W // 2, 740))
        a = 0.55 + 0.45 * math.sin(self.t * 3)
        f = self.app.fonts.get("h2")
        txt = render_text(f, "Click anywhere to begin", (255, 248, 230), (80, 40, 16)).copy()
        txt.set_alpha(int(255 * a))
        surf.blit(txt, txt.get_rect(center=(W // 2, 880)))


class MainMenu(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.announced = False
        if app.updater.state == app.updater.IDLE:
            app.updater.check(manual=False)  # quiet launch check - result shown below, never installs silently

    def layout(self):
        a = self.app
        labels = [("Play", self.play, "primary"), ("How to Play", lambda: a.push(HowToPlay(a)), "normal"),
                  ("Options", lambda: a.push(OptionsScreen(a)), "normal"), ("Credits", lambda: a.push(Credits(a)), "normal"),
                  ("Check for Updates", lambda: a.push(UpdateDialog(a)), "normal"), ("Quit", self.ask_quit, "normal")]
        bw, bh, gap = 600, 104, 22
        x = 1170
        y0 = (H - (len(labels) * bh + (len(labels) - 1) * gap)) // 2 + 10
        self.widgets = [Button(a, (x, y0 + i * (bh + gap), bw, bh), l, cb, style=st) for i, (l, cb, st) in enumerate(labels)]

    def play(self):
        self.app.push(ChapterMap(self.app))

    def ask_quit(self):
        self.app.push(Dialog(self.app, "Leave Maple Lane?", "Your progress is saved. Come back any time!",
                             [("Stay", lambda: self.app.pop(), "normal"), ("Quit", self.app.quit, "primary")]))

    def update(self, dt):
        super().update(dt)
        u = self.app.updater
        if not self.announced and not u.manual and self.app.top is self:
            if u.state == u.AVAILABLE:
                self.announced = True
                self.app.push(UpdateDialog(self.app, start_check=False))
            elif u.state == u.FAILED:
                self.announced = True
                self.app.toast("Couldn't check for updates right now. You can keep playing!")
            elif u.state == u.UP_TO_DATE:
                self.announced = True

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.ask_quit()
            return True
        return super().handle(event)

    def draw(self, surf):
        surf.blit(backdrop(self.app), (0, 0))
        lg = logo(self.app, 470)
        surf.blit(lg, lg.get_rect(center=(560, 420)))
        title_text(self.app, surf, (560, 740), "h1")
        f = self.app.fonts.get("small")
        draw_text(surf, "A cozy autumn hidden-object adventure", f, (255, 246, 226), (560, 820), shadow=(80, 40, 16))
        super().draw(surf)
        draw_text(surf, f"v{VERSION}", self.app.fonts.get("small"), (255, 246, 226), (W - 40, H - 30), "bottomright",
                  shadow=(60, 30, 10))


# ====================================================================== options
class OptionsScreen(Screen):
    def layout(self):
        a = self.app
        s = a.settings
        self.panel = pygame.Rect(260, 50, 1400, 980)
        cx = self.panel.x + 560
        cw = self.panel.right - 70 - cx
        ys = {"music": 205, "sfx": 315, "mute": 425, "screen": 535, "diff": 645, "text": 835}
        row = lambda key: (cx, self.panel.y + ys[key] - 46, cw, 92)
        self.music = Slider(a, row("music"), s["music_volume"], self.set_music)
        self.sfx = Slider(a, row("sfx"), s["sfx_volume"], self.set_sfx)
        self.mute = Toggle(a, row("mute"), [(False, "Sound On"), (True, "Mute All")], s["muted"], self.set_mute)
        self.screen_mode = Toggle(a, row("screen"), [(False, "Windowed"), (True, "Fullscreen")], s["fullscreen"], a.set_fullscreen)
        self.diff = Toggle(a, row("diff"), [(k, DIFFICULTY[k]["label"]) for k in ("relaxed", "normal", "challenge")],
                           s["difficulty"], self.set_diff)
        self.text = Toggle(a, row("text"), [("normal", "Normal"), ("large", "Large"), ("xlarge", "Extra Large")],
                           s["text_size"], self.set_text)
        self.back = Button(a, (self.panel.centerx - 170, self.panel.bottom - 118, 340, 96), "Back", self.app.pop, style="primary")
        self.widgets = [self.music, self.sfx, self.mute, self.screen_mode, self.diff, self.text, self.back]

    def set_music(self, v):
        self.app.settings.set("music_volume", round(v, 2))
        self.app.audio.apply_volumes()

    def set_sfx(self, v):
        self.app.settings.set("sfx_volume", round(v, 2))
        self.app.audio.play("found", 0.6)

    def set_mute(self, v):
        self.app.settings.set("muted", bool(v))
        self.app.audio.apply_volumes()

    def set_diff(self, v):
        self.app.settings.set("difficulty", v)

    def set_text(self, v):
        self.app.set_text_size(v)

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return True
        return super().handle(event)

    def draw(self, surf):
        surf.blit(backdrop(self.app, "autumn_bakery"), (0, 0))
        draw_panel(surf, self.panel)
        f = self.app.fonts.get("h1")
        draw_text(surf, "Options", f, COL["ink"], (self.panel.centerx, self.panel.y + 18), "midtop")
        # fix label rows to widget centres
        rowmap = {"Music Volume": self.music.rect, "Sound Effects": self.sfx.rect, "Sound": self.mute.rect,
                  "Display": self.screen_mode.rect, "Difficulty": self.diff.rect, "Text Size": self.text.rect}
        lf = self.app.fonts.fit("h2", "Sound Effects", 470)
        for label, r in rowmap.items():
            draw_text(surf, label, lf, COL["ink"], (self.panel.x + 70, r.centery), "midleft")
        # percentages
        sf = self.app.fonts.get("small")
        for sl in (self.music, self.sfx):
            draw_text(surf, f"{int(round(sl.value * 100))}%", sf, COL["ink_soft"], (sl.track.centerx, sl.track.y - 24), "midbottom")
        desc = DIFFICULTY[self.app.settings["difficulty"]]["desc"]
        r = pygame.Rect(self.panel.x + 70, self.diff.rect.bottom + 16, self.panel.width - 140, 90)
        draw_paragraph(surf, desc, self.app.fonts.get("small"), COL["ink_soft"], r)
        super().draw(surf)


# ====================================================================== how to play
PAGES = [
    ("Find the hidden items", ["maple_leaf", "acorn", "sunflower"],
     "Each picture hides 10 items. Their names and pictures are listed at the bottom of the screen. "
     "When you spot one, click it! Tip: click a name in the list to see a bigger picture of what to look for."),
    ("Need a little help?", ["lantern"],
     "Press the Hint button and a glowing circle will show you where an item is. The button refills after a "
     "short wait. In Relaxed mode there's no timer, so take all the time you like."),
    ("Puzzles and stars", ["pie", "candy_corn", "pumpkin"],
     "After each picture there's a puzzle: matching cards, spotting differences, sliding a picture together, "
     "a corn maze, and a pattern game. Earn up to 3 stars per picture by using fewer hints. "
     "Your progress saves automatically."),
]


class HowToPlay(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.page = 0

    def layout(self):
        a = self.app
        self.panel = pygame.Rect(260, 90, 1400, 900)
        self.prev = Button(a, (self.panel.x + 60, self.panel.bottom - 140, 300, 100), "Back a page", self.go_prev)
        self.next = Button(a, (self.panel.right - 360, self.panel.bottom - 140, 300, 100), "Next page", self.go_next, style="primary")
        self.tut = Button(a, (self.panel.centerx - 260, self.panel.bottom - 140, 520, 100), "Show the tutorial again", self.reset_tut)
        self.done = Button(a, (W - 330, H - 140 + 40, 280, 90), "Done", self.app.pop, style="green")
        self.widgets = [self.prev, self.next, self.tut, self.done]
        self._sync()

    def _sync(self):
        self.prev.enabled = self.page > 0
        self.next.enabled = self.page < len(PAGES) - 1

    def go_prev(self):
        self.page = max(0, self.page - 1)
        self._sync()

    def go_next(self):
        self.page = min(len(PAGES) - 1, self.page + 1)
        self._sync()

    def reset_tut(self):
        self.app.progress.set_tutorial_done(False)
        self.app.toast("The tutorial will play next time you open the Pumpkin Patch.")

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return True
        return super().handle(event)

    def draw(self, surf):
        surf.blit(backdrop(self.app, "harvest_barn"), (0, 0))
        draw_panel(surf, self.panel)
        title, icons, text = PAGES[self.page]
        draw_text(surf, "How to Play", self.app.fonts.get("h2"), COL["ink_soft"], (self.panel.centerx, self.panel.y + 30), "midtop")
        draw_text(surf, title, self.app.fonts.fit("h1", title, 1200), COL["ink"], (self.panel.centerx, self.panel.y + 110), "midtop")
        n = len(icons)
        for i, nm in enumerate(icons):
            img = self.app.assets.obj_scaled(nm, 200)
            x = self.panel.centerx + (i - (n - 1) / 2) * 240
            surf.blit(img, img.get_rect(center=(x, self.panel.y + 330)))
        r = pygame.Rect(self.panel.x + 110, self.panel.y + 460, self.panel.width - 220, 300)
        draw_paragraph(surf, text, self.app.fonts.get("body"), COL["ink"], r)
        draw_text(surf, f"Page {self.page + 1} of {len(PAGES)}", self.app.fonts.get("tiny"), COL["ink_soft"],
                  (self.panel.centerx, self.panel.bottom - 175))
        super().draw(surf)


# ====================================================================== credits
CREDITS = [
    ("h1", APP_NAME),
    ("body", f"Version {VERSION}"),
    ("gap", ""),
    ("h2", "Made by Ironite"),
    ("body", "Game design, programming, art, music and sound"),
    ("gap", ""),
    ("h2", "Art"),
    ("body", "Every picture was painted by code written for this game. No outside images."),
    ("h2", "Music & Sound"),
    ("body", "Original folk tune and sound effects, synthesized live by the game itself."),
    ("h2", "Built with"),
    ("body", "Python, pygame-ce (LGPL) and NumPy (BSD). Fonts: Georgia and Segoe UI from Windows."),
    ("gap", ""),
    ("small", "Copyright 2026 Ironite. Thank you for playing!"),
]


class Credits(Screen):
    def layout(self):
        self.panel = pygame.Rect(310, 70, 1300, 940)
        self.widgets = [Button(self.app, (W - 330, H - 140, 280, 100), "Back", self.app.pop, style="primary")]

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return True
        return super().handle(event)

    def draw(self, surf):
        surf.blit(backdrop(self.app, "fall_fair"), (0, 0))
        draw_panel(surf, self.panel)
        y = self.panel.y + 50
        for kind, text in CREDITS:
            if kind == "gap":
                y += 22
                continue
            f = self.app.fonts.fit(kind, text, self.panel.width - 120)
            color = COL["ink"] if kind in ("h1", "h2") else COL["ink_soft"]
            draw_text(surf, text, f, color, (self.panel.centerx, y), "midtop")
            y += int(f.get_linesize() * 1.15)
        super().draw(surf)


# ====================================================================== chapter map
class ChapterMap(Screen):
    def layout(self):
        a = self.app
        self.cards = []
        cw, ch, gap = 336, 600, 22
        x0 = (W - (cw * 5 + gap * 4)) // 2
        for i, c in enumerate(CHAPTERS):
            self.cards.append((pygame.Rect(x0 + i * (cw + gap), 250, cw, ch), c))
        self.widgets = [Button(a, (50, 40, 300, 96), "Main Menu", a.pop)]
        self.hover_card = None

    def thumb(self, scene, w, h):
        key = ("thumb", scene, w, h)
        cache = self.app.assets._img
        if key not in cache:
            src = self.app.assets.scene(scene)
            cache[key] = pygame.transform.smoothscale(src.subsurface(pygame.Rect(240, 0, 1440, 1080)), (w, int(w * 1080 / 1440)))
        return cache[key]

    def handle(self, event):
        if super().handle(event):
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for r, c in self.cards:
                if r.collidepoint(event.pos):
                    self.open(c["n"])
                    return True
        return False

    def open(self, n):
        a = self.app
        if not a.progress.unlocked(n):
            a.audio.play("wrong")
            a.toast(f"Finish {CHAPTERS[n - 2]['title']} first to open this chapter.")
            return
        a.audio.play("click")
        if a.progress.chapter(n)["scene_done"]:
            a.push(ChapterChoice(a, n))
        else:
            start_scene(a, n)

    def hovering(self):
        return super().hovering() or any(r.collidepoint(self.app.mouse) and self.app.progress.unlocked(c["n"]) for r, c in self.cards)

    def draw(self, surf):
        a = self.app
        surf.blit(backdrop(a, "corn_maze"), (0, 0))
        draw_text(surf, "Choose a Chapter", a.fonts.get("h1"), (255, 246, 226), (W // 2, 90), shadow=(80, 40, 16))
        stars = a.progress.total_stars()
        draw_text(surf, f"Stars collected: {stars} of {NUM_CHAPTERS * 3}", a.fonts.get("small"), (255, 246, 226),
                  (W // 2, 175), shadow=(80, 40, 16))
        for r, c in self.cards:
            n = c["n"]
            p = a.progress.chapter(n)
            unlocked = a.progress.unlocked(n)
            hover = r.collidepoint(a.mouse) and unlocked
            rr = r.move(0, -10 if hover else 0)
            draw_panel(surf, rr, color=(255, 248, 232) if unlocked else (226, 216, 200))
            th = self.thumb(c["scene"], rr.width - 36, 0)
            surf.blit(th, (rr.x + 18, rr.y + 18))
            if not unlocked:
                ov = pygame.Surface(th.get_size(), pygame.SRCALPHA)
                ov.fill((60, 40, 20, 150))
                surf.blit(ov, (rr.x + 18, rr.y + 18))
                lock_c = (rr.centerx, rr.y + 18 + th.get_height() // 2)
                pygame.draw.rect(surf, (250, 236, 210), (lock_c[0] - 40, lock_c[1] - 10, 80, 64), border_radius=10)
                pygame.draw.arc(surf, (250, 236, 210), (lock_c[0] - 28, lock_c[1] - 52, 56, 80), 0, math.pi, 10)
            y = rr.y + 36 + th.get_height()
            draw_text(surf, f"Chapter {n}", a.fonts.get("tiny"), COL["ink_soft"], (rr.centerx, y), "midtop")
            y += 40
            f = a.fonts.fit("h2", c["title"], rr.width - 30)
            draw_text(surf, c["title"], f, COL["ink"], (rr.centerx, y), "midtop")
            y += f.get_height() + 40
            for k in range(3):
                draw_star(surf, (rr.centerx + (k - 1) * 78, y), 32, filled=k < p["stars"])
            y += 70
            pf = a.fonts.fit("tiny", "Puzzle: " + c["puzzle_title"], rr.width - 80)
            if p["puzzle_done"]:
                draw_check(surf, (rr.x + 40, y + 16), 30)
            draw_text(surf, c["puzzle_title"], pf, COL["ink_soft"], (rr.centerx + (16 if p["puzzle_done"] else 0), y + 16))
            y += 60
            if unlocked:
                state = "Play again" if p["scene_done"] else ("Continue" if a.progress.get_scene_state(n) else "Start")
                draw_text(surf, state, a.fonts.get("small"), COL["orange_dk"], (rr.centerx, rr.bottom - 40))
            else:
                draw_text(surf, "Locked", a.fonts.get("small"), (150, 130, 110), (rr.centerx, rr.bottom - 40))
        super().draw(surf)


class ChapterChoice(Dialog):
    def __init__(self, app, n):
        c = CHAPTERS[n - 1]
        super().__init__(app, c["title"], "What would you like to do?",
                         [("Find Items", lambda: self.go_scene(n), "primary"),
                          (c["puzzle_title"], lambda: self.go_puzzle(n), "green"),
                          ("Back", lambda: self.app.pop(), "normal")], width=1300)

    def go_scene(self, n):
        self.app.pop()
        start_scene(self.app, n)

    def go_puzzle(self, n):
        self.app.pop()
        start_puzzle(self.app, n)


def start_scene(app, n):
    from .hidden import HiddenScene
    app.push(HiddenScene(app, n))
    app.fade = 1.0


def start_puzzle(app, n):
    from .puzzles import make_puzzle
    app.push(make_puzzle(app, n))
    app.fade = 1.0
