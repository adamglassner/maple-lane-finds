"""The hidden-object scene: find 10 items, hints, progress, tutorial, stars."""
import math
import random

import pygame

from .app import Screen
from .levels import ALL_OBJECTS, CHAPTERS, DIFFICULTY, OBJECT_NAMES, ZONES, stars_for
from .ui import COL, W, H, Button, Particles, dim, draw_check, draw_panel, draw_paragraph, draw_star, draw_text

TOP_H = 104
PANEL_Y = 858
FIELD = pygame.Rect(40, TOP_H + 26, W - 80, PANEL_Y - TOP_H - 40)


class Placed:
    def __init__(self, kind, x, y, size, rot, flip):
        self.kind, self.x, self.y, self.size, self.rot, self.flip = kind, x, y, size, rot, flip

    @property
    def pos(self):
        return (self.x, self.y)


def _pick_point(rng, zones, size):
    total = sum(z[4] for z in zones)
    r = rng.uniform(0, total)
    for x0, y0, x1, y1, wgt in zones:
        r -= wgt
        if r <= 0:
            break
    x = rng.uniform(max(x0, FIELD.left + size * 0.55), min(x1, FIELD.right - size * 0.55))
    y = rng.uniform(max(y0, FIELD.top + size * 0.55), min(y1, FIELD.bottom - size * 0.45))
    return x, y


def depth_scale(y):
    """Things further back (higher up) are drawn a little smaller, like a real photo."""
    t = (y - FIELD.top) / FIELD.height
    return 0.8 + 0.32 * max(0.0, min(1.0, t))


def generate_layout(chapter, difficulty, seed):
    cfg = DIFFICULTY[difficulty]
    rng = random.Random(seed * 7919 + chapter["n"])
    zones = ZONES[chapter["scene"]]["zones"]
    base = cfg["size"]
    targets = []
    for kind in chapter["targets"]:
        best = None
        for attempt in range(400):
            x, y = _pick_point(rng, zones, base)
            size = base * depth_scale(y) * rng.uniform(0.94, 1.06)
            dmin = min([math.hypot(x - t.x, y - t.y) - (size + t.size) * 0.55 for t in targets] or [9999])
            if best is None or dmin > best[0]:
                best = (dmin, x, y, size)
            if dmin > size * 0.35:
                break
        _, x, y, size = best
        rot = rng.uniform(-22, 22) if rng.random() < 0.65 else 0
        targets.append(Placed(kind, x, y, size, rot, rng.random() < 0.4))
    pool = [k for k in ALL_OBJECTS if k not in chapter["targets"] and k not in chapter.get("avoid", [])]
    rng.shuffle(pool)
    clutter = []
    for i in range(cfg["clutter"]):
        kind = pool[i % len(pool)]
        for attempt in range(200):
            x, y = _pick_point(rng, zones, base)
            size = base * depth_scale(y) * rng.uniform(0.85, 1.15)
            if all(math.hypot(x - t.x, y - t.y) > (t.size + size) * 0.45 for t in targets) and \
                    all(math.hypot(x - c.x, y - c.y) > (c.size + size) * 0.38 for c in clutter):
                clutter.append(Placed(kind, x, y, size, rng.uniform(-28, 28), rng.random() < 0.5))
                break
    # little drifts of fallen leaves that partly tuck some items in (purely decorative, clicks go through)
    share = {"relaxed": 0.25, "normal": 0.45, "challenge": 0.65}[difficulty]
    cover = []
    for t in targets:
        if rng.random() < share:
            a = rng.uniform(0, math.tau)
            d = t.size * rng.uniform(0.28, 0.4)
            cover.append((t.x + math.cos(a) * d, t.y + abs(math.sin(a)) * d * 0.8, t.size * rng.uniform(0.18, 0.26), rng.random()))
    return targets, clutter, cover


def draw_leaf_drift(surf, x, y, s, seed):
    rng = random.Random(int(seed * 1e6))
    cols = [(196, 92, 34), (214, 140, 40), (176, 70, 30), (226, 176, 60), (150, 104, 44)]
    for _ in range(5):
        cx = x + rng.uniform(-s, s)
        cy = y + rng.uniform(-s * 0.5, s * 0.5)
        w, h = s * rng.uniform(0.9, 1.4), s * rng.uniform(0.45, 0.65)
        leaf = pygame.Surface((int(w * 2) + 6, int(h * 2) + 6), pygame.SRCALPHA)
        col = rng.choice(cols)
        r = leaf.get_rect().inflate(-6, -6)
        pygame.draw.ellipse(leaf, (70, 40, 20, 120), r.move(2, 3))
        pygame.draw.ellipse(leaf, col, r)
        pygame.draw.ellipse(leaf, tuple(min(255, c + 30) for c in col), r.inflate(-r.width // 2, -r.height // 2).move(-r.width // 8, -r.height // 8))
        pygame.draw.line(leaf, tuple(int(c * 0.7) for c in col), (r.left + 3, r.centery), (r.right - 3, r.centery), 2)
        leaf = pygame.transform.rotate(leaf, rng.uniform(0, 180))
        surf.blit(leaf, leaf.get_rect(center=(cx, cy)))


class HiddenScene(Screen):
    toast_top = True
    def __init__(self, app, n):
        super().__init__(app)
        self.n = n
        self.chapter = CHAPTERS[n - 1]
        self.difficulty = app.settings["difficulty"]
        self.cfg = DIFFICULTY[self.difficulty]
        saved = app.progress.get_scene_state(n)
        self.resumed = False
        if saved and isinstance(saved.get("seed"), int):
            self.seed = saved["seed"]
            self.found = [k for k in saved.get("found", []) if k in self.chapter["targets"]]
            self.hints_used = int(saved.get("hints", 0))
            self.elapsed = float(saved.get("elapsed", 0.0))
            self.resumed = bool(self.found)
        else:
            self.seed = random.randint(1, 10 ** 6)
            self.found, self.hints_used, self.elapsed = [], 0, 0.0
        self.targets, self.clutter, self.cover = generate_layout(self.chapter, self.difficulty, self.seed)
        self.particles = Particles()
        self.flying = []      # [kind, (x0,y0), t]
        self.puffs = []       # wrong-click rings [x, y, t]
        self.floaters = []    # floating text [text, x, y, t]
        self.hint_cd = 0.0
        self.hint_target = None
        self.hint_t = 0.0
        self.preview = None   # [kind, t]
        self.win = None       # dict when complete
        self.complete_timer = None
        self.tutorial = None if (app.progress.tutorial_done or n != 1) else 0
        self.intro_t = 0.0 if self.tutorial is None else 99
        self.static = None

    # ------------------------------------------------------------ layout & widgets
    def layout(self):
        a = self.app
        self.menu_btn = Button(a, (24, 14, 230, 78), "Menu", self.pause, font="button")
        self.hint_btn = Button(a, (W - 300, PANEL_Y + 20, 270, 190), "Hint", self.use_hint, style="primary", font="h2")
        self.widgets = [self.menu_btn, self.hint_btn]
        cols, rows = 5, 2
        x0, y0, sw, sh, gx, gy = 30, PANEL_Y + 22, 314, 90, 8, 12
        self.slots = {}
        for i, kind in enumerate(self.chapter["targets"]):
            c, r = i % cols, i // cols
            self.slots[kind] = pygame.Rect(x0 + c * (sw + gx), y0 + r * (sh + gy), sw, sh)
        self.tut_btn = Button(a, (0, 0, 300, 96), "Next", self.tutorial_next, style="primary")
        self.win_buttons = []
        self.static = None

    def on_enter(self):
        if self.resumed:
            self.app.toast("Welcome back! Picking up where you left off.")
            self.resumed = False

    # ------------------------------------------------------------ state
    def save_state(self):
        if self.win:
            return
        self.app.progress.set_scene_state(self.n, {"seed": self.seed, "found": self.found, "hints": self.hints_used,
                                                   "elapsed": round(self.elapsed, 1), "difficulty": self.difficulty})

    def remaining(self):
        return [t for t in self.targets if t.kind not in self.found]

    # ------------------------------------------------------------ actions
    def pause(self):
        self.save_state()
        self.app.push(PauseMenu(self.app, self))

    def use_hint(self):
        rem = self.remaining()
        if not rem or self.hint_cd > 0:
            return
        self.hint_target = random.choice(rem)
        self.hint_t = 4.5
        self.hint_cd = self.cfg["hint_cooldown"]
        self.hints_used += 1
        self.app.audio.play("hint")
        self.particles.burst(self.hint_target.pos, 16, speed=260)

    def collect(self, t):
        self.found.append(t.kind)
        self.flying.append([t.kind, t.pos, 0.0, t.size, t.rot])
        self.particles.burst(t.pos, 28)
        self.app.audio.play("found")
        if self.hint_target is t:
            self.hint_target = None
        self.static = None
        if len(self.found) == len(self.targets):
            self.complete_timer = 1.0
        self.save_state()

    def click_field(self, pos):
        best, bd = None, 1e9
        for t in self.remaining():
            d = math.hypot(pos[0] - t.x, pos[1] - t.y)
            if d < max(t.size * 0.56, 62) and d < bd:
                best, bd = t, d
        if best:
            self.collect(best)
            return
        self.app.audio.play("wrong", 0.7)
        self.puffs.append([pos[0], pos[1], 0.0])
        pen = self.cfg["wrong_penalty"]
        if pen:
            self.elapsed += pen
            self.floaters.append([f"+{pen}s", pos[0], pos[1] - 30, 0.0])

    # ------------------------------------------------------------ tutorial
    TUT = [
        ("Welcome to Maple Lane!", "Each picture hides 10 items. They are listed down here at the bottom.", "list"),
        ("See a bigger picture", "Not sure what something looks like? Click its name in the list to see it up close.", "list"),
        ("Click to collect", "When you spot an item in the picture, just click on it. There's no rush, so take your time!", "field"),
        ("Need help?", "Press Hint and a glowing circle shows you where an item is. It refills after a short wait.", "hint"),
        ("Take a break any time", "Your progress is shown at the top. Press Menu to rest, change options, or leave. "
                                  "Everything saves automatically. Have fun!", "top"),
    ]

    def tutorial_next(self):
        self.tutorial += 1
        if self.tutorial >= len(self.TUT):
            self.tutorial = None
            self.app.progress.set_tutorial_done(True)
            self.intro_t = 0.0

    def tut_rect(self, key):
        return {"list": pygame.Rect(18, PANEL_Y + 10, 1610, 210), "field": FIELD.inflate(-80, -40),
                "hint": self.hint_btn.rect.inflate(24, 24), "top": pygame.Rect(0, 0, W, TOP_H + 8)}[key]

    # ------------------------------------------------------------ events
    def handle(self, event):
        if self.tutorial is not None:
            self.tut_btn.handle(event)
            return True
        if self.win:
            for b in self.win_buttons:
                if b.handle(event):
                    return True
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pause()
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            self.use_hint()
            return True
        if super().handle(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for kind, r in self.slots.items():
                if r.collidepoint(event.pos):
                    self.preview = [kind, 2.8]
                    self.app.audio.play("click")
                    return True
            if FIELD.collidepoint(event.pos) and self.complete_timer is None:
                self.click_field(event.pos)
                return True
        return False

    def hovering(self):
        if self.tutorial is not None:
            return self.tut_btn.hovered()
        if self.win:
            return any(b.hovered() for b in self.win_buttons)
        return super().hovering() or any(r.collidepoint(self.app.mouse) for r in self.slots.values())

    # ------------------------------------------------------------ update
    def update(self, dt):
        super().update(dt)
        if self.tutorial is not None:
            return
        self.intro_t += dt
        if not self.win:
            self.elapsed += dt
        self.hint_cd = max(0.0, self.hint_cd - dt)
        self.hint_btn.enabled = self.hint_cd <= 0 and bool(self.remaining()) and not self.win
        if self.hint_target:
            self.hint_t -= dt
            if self.hint_t <= 0:
                self.hint_target = None
            elif int(self.hint_t * 4) != int((self.hint_t + dt) * 4):
                self.particles.burst(self.hint_target.pos, 4, speed=180, life=0.7, size=6)
        self.particles.update(dt)
        for f in self.flying:
            f[2] += dt / 0.75
        self.flying = [f for f in self.flying if f[2] < 1]
        for p in self.puffs:
            p[2] += dt / 0.45
        self.puffs = [p for p in self.puffs if p[2] < 1]
        for f in self.floaters:
            f[3] += dt
        self.floaters = [f for f in self.floaters if f[3] < 1.2]
        if self.preview:
            self.preview[1] -= dt
            if self.preview[1] <= 0:
                self.preview = None
        if self.complete_timer is not None and not self.win:
            self.complete_timer -= dt
            if self.complete_timer <= 0:
                self.finish()
        if self.win:
            self.win["t"] += dt
            shown = min(self.win["stars"], int(self.win["t"] / 0.45))
            if shown > self.win["sounded"]:
                self.win["sounded"] = shown
                self.app.audio.play("click", 1.0)
                self.particles.burst(self.star_pos(shown - 1), 20)

    def finish(self):
        stars = stars_for(self.hints_used, self.elapsed, self.difficulty)
        self.app.progress.record_scene(self.n, stars, self.elapsed)
        self.win = {"stars": stars, "t": 0.0, "sounded": 0}
        self.app.audio.play("win")
        a = self.app
        cx = W // 2
        self.win_buttons = [
            Button(a, (cx - 470, 720, 450, 110), f"Play: {self.chapter['puzzle_title']}", self.go_puzzle, style="primary"),
            Button(a, (cx + 20, 720, 450, 110), "Chapter Map", self.go_map),
        ]

    def star_pos(self, i):
        return (W // 2 + (i - 1) * 150, 470)

    def go_puzzle(self):
        from .menus import start_puzzle
        n = self.n
        self.app.pop()
        start_puzzle(self.app, n)

    def go_map(self):
        self.app.pop()

    # ------------------------------------------------------------ drawing
    def build_static(self):
        s = self.app.assets.scene(self.chapter["scene"]).copy()
        tint = ZONES[self.chapter["scene"]]["tint"]
        items = [(o, False) for o in self.clutter] + [(t, True) for t in self.targets if t.kind not in self.found]
        for o, _is_target in sorted(items, key=lambda it: it[0].y):  # back to front
            img = self.app.assets.obj_scaled(o.kind, o.size, o.rot, o.flip).copy()
            img.fill(tint, special_flags=pygame.BLEND_RGB_MULT)  # match the scene's lighting
            s.blit(img, img.get_rect(center=o.pos))
        for x, y, size, seed in self.cover:
            draw_leaf_drift(s, x, y, size, seed)
        self.static = s

    def draw(self, surf):
        if self.static is None:
            self.build_static()
        surf.blit(self.static, (0, 0))
        a = self.app
        # wrong-click puffs
        for x, y, t in self.puffs:
            r = int(20 + 40 * t)
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 250, 236, int(200 * (1 - t))), (r + 2, r + 2), r, 5)
            surf.blit(s, (x - r - 2, y - r - 2))
        # hint ring
        if self.hint_target:
            t = self.hint_target
            pulse = 0.5 + 0.5 * math.sin(a.time * 7)
            r = int(t.size * 0.78 + 14 * pulse)
            glow = pygame.Surface((r * 2 + 60, r * 2 + 60), pygame.SRCALPHA)
            c = r + 30
            for i in range(6):
                pygame.draw.circle(glow, (255, 220, 110, 34), (c, c), r + 26 - i * 4, 8)
            pygame.draw.circle(glow, (255, 236, 150, 255), (c, c), r, 7)
            pygame.draw.circle(glow, (255, 255, 255, 200), (c, c), r - 6, 3)
            surf.blit(glow, (t.x - c, t.y - c))
        self.particles.draw(surf)
        for text, x, y, t in self.floaters:
            fs = draw_text(surf, text, a.fonts.get("h2"), (255, 240, 220), (x, y - t * 60), shadow=(80, 30, 10))
        self.draw_hud(surf)
        # flying items to the list
        for kind, (x0, y0), t, size, rot in self.flying:
            slot = self.slots[kind]
            ex, ey = slot.x + 48, slot.centery
            k = 1 - (1 - t) ** 3
            x = x0 + (ex - x0) * k
            y = y0 + (ey - y0) * k - math.sin(math.pi * t) * 140
            sz = max(10, int(size * (1 + 0.35 * math.sin(math.pi * min(1, t * 2))) * (1 - 0.4 * k)))
            img = a.assets.obj_scaled(kind, sz)
            surf.blit(img, img.get_rect(center=(x, y)))
        if self.preview:
            self.draw_preview(surf)
        if self.intro_t < 4.0 and not self.win and self.tutorial is None:
            al = min(1.0, (4.0 - self.intro_t) / 0.6, self.intro_t / 0.3)
            tmp = pygame.Surface((1320, 170), pygame.SRCALPHA)
            draw_panel(tmp, pygame.Rect(24, 24, 1272, 122), color=(255, 248, 232))
            f = a.fonts.fit("body", self.chapter["intro"], 1180)
            draw_text(tmp, self.chapter["intro"], f, COL["ink"], (660, 85))
            tmp.set_alpha(int(255 * al))
            surf.blit(tmp, tmp.get_rect(center=(W // 2, TOP_H + 90)))
        if self.win:
            self.draw_win(surf)
        if self.tutorial is not None:
            self.draw_tutorial(surf)

    def draw_hud(self, surf):
        a = self.app
        bar = pygame.Surface((W, TOP_H), pygame.SRCALPHA)
        for y in range(TOP_H):
            bar.fill((60, 34, 18, int(200 - 120 * y / TOP_H)), pygame.Rect(0, y, W, 1))
        surf.blit(bar, (0, 0))
        self.menu_btn.draw(surf)
        f = a.fonts.fit("h2", self.chapter["title"], 700)
        draw_text(surf, self.chapter["title"], f, (255, 244, 222), (W // 2, TOP_H // 2), shadow=(40, 20, 8))
        # progress
        n = len(self.found)
        tot = len(self.targets)
        pr = pygame.Rect(W - 470, 56, 430, 26)
        pygame.draw.rect(surf, (90, 56, 30), pr.inflate(8, 8), border_radius=17)
        pygame.draw.rect(surf, (236, 222, 196), pr, border_radius=13)
        if n:
            pygame.draw.rect(surf, COL["gold"], (pr.x, pr.y, int(pr.width * n / tot), pr.height), border_radius=13)
        draw_text(surf, f"Found {n} of {tot}", a.fonts.get("small"), (255, 244, 222), (pr.centerx, 32), shadow=(40, 20, 8))
        if self.cfg["timer"]:
            m, s = divmod(int(self.elapsed), 60)
            draw_text(surf, f"Time {m}:{s:02d}", a.fonts.get("small"), (255, 244, 222), (330, TOP_H // 2), "midleft",
                      shadow=(40, 20, 8))
        # bottom list panel
        draw_panel(surf, pygame.Rect(14, PANEL_Y + 8, W - 28, H - PANEL_Y - 20), color=(252, 242, 222), radius=26)
        for kind, r in self.slots.items():
            got = kind in self.found and not any(f[0] == kind for f in self.flying)
            hover = r.collidepoint(a.mouse) and not self.win
            pygame.draw.rect(surf, (255, 250, 238) if not got else (226, 238, 210), r, border_radius=18)
            pygame.draw.rect(surf, (200, 170, 130) if not hover else COL["orange"], r, width=3, border_radius=18)
            icon = a.assets.obj_scaled(kind, 78)
            if got:
                icon = icon.copy()
                icon.set_alpha(110)
            surf.blit(icon, icon.get_rect(center=(r.x + 48, r.centery)))
            name = OBJECT_NAMES[kind]
            nf = a.fonts.fit("small", name, r.width - 110)
            col = COL["ink"] if not got else (120, 140, 100)
            tr = draw_text(surf, name, nf, col, (r.x + 96, r.centery), "midleft")
            if got:
                pygame.draw.line(surf, (110, 130, 90), (tr.left - 4, tr.centery + 2), (tr.right + 4, tr.centery + 2), 4)
                draw_check(surf, (r.right - 30, r.centery), 34)
        # hint button + cooldown
        self.hint_btn.label = "Hint"
        self.hint_btn.sublabel = None if self.hint_cd <= 0 else f"Ready in {int(math.ceil(self.hint_cd))}"
        self.hint_btn.draw(surf)
        if self.hint_cd > 0:
            frac = self.hint_cd / self.cfg["hint_cooldown"]
            r = self.hint_btn.rect
            rect = pygame.Rect(r.right - 62, r.y + 12, 48, 48)
            pygame.draw.circle(surf, (236, 222, 196), rect.center, 24)
            pygame.draw.arc(surf, COL["orange_dk"], rect, math.pi / 2, math.pi / 2 + math.tau * (1 - frac), 8)

    def draw_preview(self, surf):
        kind, t = self.preview
        al = min(1.0, t / 0.3)
        slot = self.slots[kind]
        box = pygame.Rect(0, 0, 360, 380)
        box.midbottom = (min(max(slot.centerx, 200), W - 200), slot.top - 14)
        tmp = pygame.Surface((box.width + 60, box.height + 60), pygame.SRCALPHA)
        draw_panel(tmp, pygame.Rect(30, 30, box.width, box.height), color=(255, 250, 238))
        img = self.app.assets.obj_scaled(kind, 250)
        tmp.blit(img, img.get_rect(center=(30 + box.width // 2, 30 + 160)))
        f = self.app.fonts.fit("body", OBJECT_NAMES[kind], box.width - 30)
        draw_text(tmp, OBJECT_NAMES[kind], f, COL["ink"], (30 + box.width // 2, 30 + 320))
        tmp.set_alpha(int(255 * al))
        surf.blit(tmp, (box.x - 30, box.y - 30))

    def draw_win(self, surf):
        a = self.app
        dim(surf, 110)
        p = pygame.Rect(0, 0, 1100, 700)
        p.center = (W // 2, H // 2 + 20)
        draw_panel(surf, p)
        draw_text(surf, "Scene Complete!", a.fonts.get("h1"), COL["ink"], (W // 2, p.y + 60), "midtop")
        draw_text(surf, f"You found everything in the {self.chapter['title']}.", a.fonts.fit("body", "x" * 40, 980),
                  COL["ink_soft"], (W // 2, p.y + 160), "midtop")
        t = self.win["t"]
        for i in range(3):
            filled = i < self.win["stars"] and t > 0.45 * (i + 1)
            k = 1.0
            if filled:
                dt = t - 0.45 * (i + 1)
                k = 1 + 0.35 * max(0.0, 1 - dt / 0.3)
            draw_star(surf, self.star_pos(i), 62, filled=filled, scale=k)
        stats = f"Hints used: {self.hints_used}"
        if self.cfg["timer"]:
            m, s = divmod(int(self.elapsed), 60)
            stats += f"      Time: {m}:{s:02d}"
        draw_text(surf, stats, a.fonts.get("small"), COL["ink_soft"], (W // 2, 590))
        for b in self.win_buttons:
            b.draw(surf)
        self.particles.draw(surf)

    def draw_tutorial(self, surf):
        a = self.app
        title, text, key = self.TUT[self.tutorial]
        hr = self.tut_rect(key)
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((30, 18, 8, 165))
        ov.fill((0, 0, 0, 0), hr)
        surf.blit(ov, (0, 0))
        pulse = 0.5 + 0.5 * math.sin(a.time * 5)
        pygame.draw.rect(surf, (255, 220, 110), hr.inflate(int(8 + 6 * pulse), int(8 + 6 * pulse)), width=6, border_radius=22)
        box = pygame.Rect(0, 0, 1000, 330)
        if key in ("list", "hint"):
            box.midbottom = (W // 2 if key == "list" else W - 640, PANEL_Y - 40)
        elif key == "top":
            box.midtop = (W // 2, TOP_H + 60)
        else:
            box.center = (W // 2, H // 2 - 40)
        draw_panel(surf, box)
        draw_text(surf, title, a.fonts.fit("h2", title, 900), COL["ink"], (box.centerx, box.y + 30), "midtop")
        draw_paragraph(surf, text, a.fonts.get("body"), COL["ink_soft"], pygame.Rect(box.x + 50, box.y + 105, box.width - 100, 150))
        last = self.tutorial == len(self.TUT) - 1
        self.tut_btn.label = "Let's Play!" if last else "Next"
        self.tut_btn.rect = pygame.Rect(0, 0, 300, 90)
        self.tut_btn.rect.midbottom = (box.centerx, box.bottom - 26)
        self.tut_btn.draw(surf)
        draw_text(surf, f"{self.tutorial + 1} / {len(self.TUT)}", a.fonts.get("tiny"), COL["ink_soft"], (box.right - 40, box.bottom - 30), "bottomright")


class PauseMenu(Screen):
    opaque = False

    def __init__(self, app, scene):
        super().__init__(app)
        self.scene = scene

    def layout(self):
        from .menus import HowToPlay, OptionsScreen
        a = self.app
        self.panel = pygame.Rect(0, 0, 700, 820)
        self.panel.center = (W // 2, H // 2)
        items = [("Keep Playing", self.resume, "primary"), ("How to Play", lambda: a.push(HowToPlay(a)), "normal"),
                 ("Options", lambda: a.push(OptionsScreen(a)), "normal"), ("Chapter Map", self.to_map, "normal"),
                 ("Main Menu", self.to_menu, "normal")]
        y = self.panel.y + 150
        self.widgets = []
        for label, cb, st in items:
            self.widgets.append(Button(a, (self.panel.x + 80, y, self.panel.width - 160, 104), label, cb, style=st))
            y += 124

    def on_enter(self):
        # options may have changed difficulty or text size; rebuild the scene's widgets
        self.scene.layout()

    def resume(self):
        self.app.pop()

    def to_map(self):
        from .menus import ChapterMap
        self.scene.save_state()
        while self.app.top and not isinstance(self.app.top, ChapterMap) and len(self.app.stack) > 1:
            self.app.pop()

    def to_menu(self):
        from .menus import MainMenu
        self.scene.save_state()
        while self.app.top and not isinstance(self.app.top, MainMenu) and len(self.app.stack) > 1:
            self.app.pop()

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.resume()
            return True
        super().handle(event)
        return True

    def draw(self, surf):
        dim(surf, 130)
        draw_panel(surf, self.panel)
        draw_text(surf, "Taking a Break", self.app.fonts.fit("h1", "Taking a Break", 620), COL["ink"],
                  (self.panel.centerx, self.panel.y + 50), "midtop")
        super().draw(surf)
