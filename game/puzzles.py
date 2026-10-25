"""The five puzzle types: memory match, spot the difference, sliding picture, corn maze, harvest code."""
import math
import random
from collections import deque

import pygame

from .app import Screen
from .levels import ALL_OBJECTS, CHAPTERS, OBJECT_NAMES
from .ui import COL, W, H, Button, Particles, dim, draw_panel, draw_paragraph, draw_text

TOP_H = 104


class PuzzleScreen(Screen):
    instructions = ""
    backdrop_scene = "pumpkin_patch"

    def __init__(self, app, n):
        super().__init__(app)
        self.n = n
        self.chapter = CHAPTERS[n - 1]
        self.difficulty = app.settings["difficulty"]
        self.solved = False
        self.done_t = 0.0
        self.particles = Particles()
        self.hint_cd = 0.0
        self.hint_cooldown = {"relaxed": 6, "normal": 12, "challenge": 25}[self.difficulty]
        self.done_buttons = []
        self.setup()

    def setup(self):
        pass

    def layout(self):
        a = self.app
        self.menu_btn = Button(a, (24, 14, 230, 78), "Menu", self.pause)
        self.hint_btn = Button(a, (W - 274, 14, 250, 78), "Hint", self.try_hint, style="primary")
        self.widgets = [self.menu_btn, self.hint_btn]

    def pause(self):
        self.app.push(PuzzlePause(self.app, self))

    def try_hint(self):
        if self.hint_cd > 0 or self.solved:
            return
        if self.hint():
            self.hint_cd = self.hint_cooldown
            self.app.audio.play("hint")

    def hint(self):
        return False

    def complete(self):
        if self.solved:
            return
        self.solved = True
        self.done_t = 0.0
        self.app.progress.record_puzzle(self.n)
        self.app.audio.play("puzzle")
        self.particles.burst((W // 2, H // 2), 60, speed=600, life=1.4, size=10)
        a = self.app
        cx = W // 2
        if self.n < len(CHAPTERS):
            nxt = CHAPTERS[self.n]
            self.done_text = f"Next up: {nxt['title']}"
            self.done_buttons = [Button(a, (cx - 470, 700, 450, 110), "Next Chapter", self.next_chapter, style="primary"),
                                 Button(a, (cx + 20, 700, 450, 110), "Chapter Map", self.app.pop)]
        else:
            self.done_text = "You've finished every chapter of Maple Lane. Wonderful job!"
            self.done_buttons = [Button(a, (cx - 225, 700, 450, 110), "Chapter Map", self.app.pop, style="primary")]

    def next_chapter(self):
        from .menus import start_scene
        n = self.n + 1
        self.app.pop()
        start_scene(self.app, n)

    def handle(self, event):
        if self.solved:
            if self.done_t > 0.6:
                for b in self.done_buttons:
                    if b.handle(event):
                        return True
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pause()
            return True
        if super().handle(event):
            return True
        return self.handle_puzzle(event)

    def handle_puzzle(self, event):
        return False

    def hovering(self):
        if self.solved:
            return any(b.hovered() for b in self.done_buttons)
        return super().hovering()

    def update(self, dt):
        super().update(dt)
        self.hint_cd = max(0.0, self.hint_cd - dt)
        self.hint_btn.enabled = self.hint_cd <= 0 and not self.solved
        self.hint_btn.label = "Hint" if self.hint_cd <= 0 else f"Hint ({int(math.ceil(self.hint_cd))})"
        self.particles.update(dt)
        if self.solved:
            self.done_t += dt
        else:
            self.update_puzzle(dt)

    def update_puzzle(self, dt):
        pass

    def draw_frame(self, surf):
        from .menus import backdrop
        surf.blit(backdrop(self.app, self.backdrop_scene, tint=(255, 230, 190), tint_alpha=90), (0, 0))
        bar = pygame.Surface((W, TOP_H), pygame.SRCALPHA)
        for y in range(TOP_H):
            bar.fill((60, 34, 18, int(210 - 120 * y / TOP_H)), pygame.Rect(0, y, W, 1))
        surf.blit(bar, (0, 0))
        f = self.app.fonts.fit("h2", self.chapter["puzzle_title"], 900)
        draw_text(surf, self.chapter["puzzle_title"], f, (255, 244, 222), (W // 2, TOP_H // 2), shadow=(40, 20, 8))
        inst = self.instructions
        f2 = self.app.fonts.fit("body", inst, 1640)
        tw = f2.size(inst)[0] + 70
        pill = pygame.Rect(0, 0, tw, f2.get_height() + 22)
        pill.center = (W // 2, TOP_H + 42)
        draw_panel(surf, pill, color=(255, 248, 232), radius=pill.height // 2, alpha=235)
        draw_text(surf, inst, f2, COL["ink"], pill.center)

    def draw(self, surf):
        self.draw_frame(surf)
        self.draw_puzzle(surf)
        super().draw(surf)
        self.particles.draw(surf)
        if self.solved and self.done_t > 0.6:
            self.draw_done(surf)

    def draw_puzzle(self, surf):
        pass

    def draw_done(self, surf):
        a = self.app
        dim(surf, 110)
        p = pygame.Rect(0, 0, 1100, 560)
        p.center = (W // 2, H // 2 + 20)
        draw_panel(surf, p)
        draw_text(surf, "Puzzle Solved!", a.fonts.get("h1"), COL["ink"], (W // 2, p.y + 70), "midtop")
        draw_paragraph(surf, self.done_text, a.fonts.get("body"), COL["ink_soft"], pygame.Rect(p.x + 80, p.y + 190, p.width - 160, 160))
        for b in self.done_buttons:
            b.draw(surf)


class PuzzlePause(Screen):
    opaque = False

    def __init__(self, app, puzzle):
        super().__init__(app)
        self.puzzle = puzzle

    def layout(self):
        from .menus import OptionsScreen
        a = self.app
        self.panel = pygame.Rect(0, 0, 700, 690)
        self.panel.center = (W // 2, H // 2)
        items = [("Keep Playing", a.pop, "primary"), ("Options", lambda: a.push(OptionsScreen(a)), "normal"),
                 ("Restart Puzzle", self.restart, "normal"), ("Chapter Map", self.to_map, "normal")]
        y = self.panel.y + 150
        self.widgets = []
        for label, cb, st in items:
            self.widgets.append(Button(a, (self.panel.x + 80, y, self.panel.width - 160, 104), label, cb, style=st))
            y += 124

    def on_enter(self):
        self.puzzle.layout()

    def restart(self):
        n = self.puzzle.n
        self.app.pop()
        self.app.pop()
        self.app.push(make_puzzle(self.app, n))

    def to_map(self):
        self.app.pop()
        self.app.pop()

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.pop()
            return True
        super().handle(event)
        return True

    def draw(self, surf):
        dim(surf, 130)
        draw_panel(surf, self.panel)
        draw_text(surf, "Taking a Break", self.app.fonts.fit("h1", "Taking a Break", 620), COL["ink"],
                  (self.panel.centerx, self.panel.y + 50), "midtop")
        super().draw(surf)


# ====================================================================== 1. memory match
class MemoryPuzzle(PuzzleScreen):
    instructions = "Click two cards to flip them. Find all the matching pairs!"
    backdrop_scene = "pumpkin_patch"

    def setup(self):
        pairs = {"relaxed": 6, "normal": 8, "challenge": 10}[self.difficulty]
        self.cols = {6: 4, 8: 4, 10: 5}[pairs]
        self.rows = pairs * 2 // self.cols
        kinds = random.sample(["pumpkin", "apple", "acorn", "maple_leaf", "sunflower", "pie", "candy_corn", "bluebird",
                               "teddy_bear", "lantern", "corn", "mushroom"], pairs)
        deck = kinds * 2
        random.shuffle(deck)
        self.cards = [{"kind": k, "up": False, "matched": False, "flip": 0.0, "glow": 0.0} for k in deck]
        self.open = []
        self.wait = 0.0
        self.moves = 0

    def card_rect(self, i):
        area = pygame.Rect(160, TOP_H + 100, W - 320, H - TOP_H - 140)
        gap = 22
        cw = min((area.width - gap * (self.cols - 1)) // self.cols, int((area.height - gap * (self.rows - 1)) / self.rows / 1.25))
        ch = int(cw * 1.25)
        total_w = cw * self.cols + gap * (self.cols - 1)
        total_h = ch * self.rows + gap * (self.rows - 1)
        x0 = area.centerx - total_w // 2
        y0 = area.centery - total_h // 2
        c, r = i % self.cols, i // self.cols
        return pygame.Rect(x0 + c * (cw + gap), y0 + r * (ch + gap), cw, ch)

    def handle_puzzle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.wait <= 0:
            for i, c in enumerate(self.cards):
                if self.card_rect(i).collidepoint(event.pos) and not c["up"] and not c["matched"]:
                    self.flip(i)
                    return True
        return False

    def flip(self, i):
        c = self.cards[i]
        c["up"] = True
        self.open.append(i)
        self.app.audio.play("flip")
        if len(self.open) == 2:
            self.moves += 1
            a, b = (self.cards[j] for j in self.open)
            if a["kind"] == b["kind"]:
                a["matched"] = b["matched"] = True
                for j in self.open:
                    self.particles.burst(self.card_rect(j).center, 18)
                self.open = []
                self.app.audio.play("found")
                if all(c["matched"] for c in self.cards):
                    self.complete()
            else:
                self.wait = 1.0

    def hint(self):
        hidden = [i for i, c in enumerate(self.cards) if not c["matched"] and not c["up"]]
        if not hidden:
            return False
        kind = self.cards[hidden[0]]["kind"]
        for i, c in enumerate(self.cards):
            if c["kind"] == kind and not c["matched"]:
                c["glow"] = 2.5
        return True

    def update_puzzle(self, dt):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                for j in self.open:
                    self.cards[j]["up"] = False
                self.open = []
                self.app.audio.play("flip", 0.6)
        for c in self.cards:
            target = 1.0 if (c["up"] or c["matched"]) else 0.0
            c["flip"] += (target - c["flip"]) * min(1, dt * 12)
            c["glow"] = max(0.0, c["glow"] - dt)

    def draw_puzzle(self, surf):
        back = self.app.assets.image("puzzles", "card_back.png")
        for i, c in enumerate(self.cards):
            r = self.card_rect(i)
            f = c["flip"]
            showing_face = f > 0.5
            sx = abs(math.cos(f * math.pi))
            w = max(2, int(r.width * sx))
            rr = pygame.Rect(0, 0, w, r.height)
            rr.center = r.center
            if c["glow"] > 0:
                g = pygame.Rect(r).inflate(24, 24)
                pygame.draw.rect(surf, (255, 220, 110), g, border_radius=26, width=8)
            if showing_face:
                face = self._face(c["kind"], r.width, r.height, c["matched"])
                surf.blit(pygame.transform.smoothscale(face, (w, r.height)), rr)
            else:
                key = ("cardback", r.width, r.height)
                cache = self.app.assets._img
                if key not in cache:
                    cache[key] = pygame.transform.smoothscale(back, (r.width, r.height))
                surf.blit(pygame.transform.scale(cache[key], (w, r.height)), rr)

    def _face(self, kind, w, h, matched):
        key = ("cardface", kind, w, h, matched)
        cache = self.app.assets._img
        if key not in cache:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(s, (90, 56, 30, 120), (4, 8, w - 4, h - 8), border_radius=24)
            pygame.draw.rect(s, (255, 250, 238) if not matched else (232, 244, 214), (0, 0, w - 4, h - 8), border_radius=24)
            pygame.draw.rect(s, (200, 160, 110) if not matched else COL["green"], (0, 0, w - 4, h - 8), width=5, border_radius=24)
            img = self.app.assets.obj_scaled(kind, int(min(w, h) * 0.78))
            s.blit(img, img.get_rect(center=(w // 2 - 2, h // 2 - 4)))
            cache[key] = s
        return cache[key]


# ====================================================================== 2. spot the difference
class SpotPuzzle(PuzzleScreen):
    instructions = "The two pictures are almost the same. Click the differences in either picture!"
    backdrop_scene = "harvest_barn"

    def setup(self):
        self.count = {"relaxed": 5, "normal": 6, "challenge": 7}[self.difficulty]
        self.pw, self.ph = 860, 640
        self.left_pos = (W // 2 - self.pw - 20, TOP_H + 110)
        self.right_pos = (W // 2 + 20, TOP_H + 110)
        rng = random.Random()
        kinds = rng.sample([k for k in ALL_OBJECTS if k not in ("corn",)], 12)
        spots = []
        for k in kinds:
            for _ in range(200):
                s = rng.uniform(110, 150)
                x, y = rng.uniform(80, self.pw - 80), rng.uniform(90, self.ph - 80)
                if all(math.hypot(x - o[1], y - o[2]) > (s + o[3]) * 0.6 for o in spots):
                    spots.append([k, x, y, s, rng.uniform(-15, 15), False])
                    break
        self.base_objs = spots[:9]
        extra_pool = spots[9:]
        right = [list(o) for o in self.base_objs]
        types = ["missing", "swap", "bigger", "flip", "extra", "missing", "swap"]
        rng.shuffle(types)
        self.diffs = []  # (x, y, radius)
        used = set()
        for t in types:
            if len(self.diffs) >= self.count:
                break
            if t == "extra":
                if not extra_pool:
                    continue
                o = extra_pool.pop()
                if any(math.hypot(o[1] - d[0], o[2] - d[1]) < 140 for d in self.diffs):
                    continue
                right.append(list(o))
                self.diffs.append((o[1], o[2], o[3] * 0.6))
                continue
            cand = [i for i in range(len(self.base_objs)) if i not in used]
            if not cand:
                break
            i = rng.choice(cand)
            used.add(i)
            o = right[i]
            if t == "missing":
                o[0] = None
            elif t == "swap":
                o[0] = rng.choice([k for k in ALL_OBJECTS if k not in kinds])
            elif t == "bigger":
                o[3] *= 1.45
            elif t == "flip":
                o[5] = not o[5]
                o[4] = -o[4] + (40 if abs(o[4]) < 8 else 0)
            self.diffs.append((o[1], o[2], max(70, o[3] * 0.6)))
        self.right_objs = right
        self.found = [False] * len(self.diffs)
        self.hint_spot = None
        self.misses = []
        self.left_img = self.compose(self.base_objs)
        self.right_img = self.compose(self.right_objs)

    def compose(self, objs):
        src = self.app.assets.scene("harvest_barn")
        crop = src.subsurface(pygame.Rect(60, 120, 1280, 952))
        s = pygame.transform.smoothscale(crop, (self.pw, self.ph))
        for k, x, y, size, rot, flip in sorted(objs, key=lambda o: o[2]):
            if not k:
                continue
            img = self.app.assets.obj_scaled(k, size, rot, flip)
            s.blit(img, img.get_rect(center=(x, y)))
        return s

    def handle_puzzle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for ox, oy in (self.left_pos, self.right_pos):
                r = pygame.Rect(ox, oy, self.pw, self.ph)
                if r.collidepoint(event.pos):
                    lx, ly = event.pos[0] - ox, event.pos[1] - oy
                    for i, (dx, dy, rad) in enumerate(self.diffs):
                        if not self.found[i] and math.hypot(lx - dx, ly - dy) < rad + 26:
                            self.found[i] = True
                            self.app.audio.play("found")
                            for px, py in (self.left_pos, self.right_pos):
                                self.particles.burst((px + dx, py + dy), 16)
                            if self.hint_spot == i:
                                self.hint_spot = None
                            if all(self.found):
                                self.complete()
                            return True
                    self.app.audio.play("wrong", 0.6)
                    self.misses.append([event.pos[0], event.pos[1], 0.0])
                    return True
        return False

    def hint(self):
        rem = [i for i, f in enumerate(self.found) if not f]
        if not rem:
            return False
        self.hint_spot = random.choice(rem)
        self.hint_t = 4.0
        return True

    def update_puzzle(self, dt):
        for m in self.misses:
            m[2] += dt / 0.45
        self.misses = [m for m in self.misses if m[2] < 1]
        if self.hint_spot is not None:
            self.hint_t -= dt
            if self.hint_t <= 0:
                self.hint_spot = None

    def draw_puzzle(self, surf):
        for img, (ox, oy) in ((self.left_img, self.left_pos), (self.right_img, self.right_pos)):
            frame = pygame.Rect(ox, oy, self.pw, self.ph)
            draw_panel(surf, frame.inflate(28, 28), radius=22)
            surf.blit(img, frame)
            for i, (dx, dy, rad) in enumerate(self.diffs):
                if self.found[i]:
                    pygame.draw.circle(surf, (40, 120, 40), (ox + dx + 2, oy + dy + 3), int(rad), 7)
                    pygame.draw.circle(surf, (120, 220, 90), (ox + dx, oy + dy), int(rad), 6)
            if self.hint_spot is not None:
                dx, dy, rad = self.diffs[self.hint_spot]
                pulse = 0.5 + 0.5 * math.sin(self.app.time * 7)
                pygame.draw.circle(surf, (255, 220, 110), (ox + dx, oy + dy), int(rad + 10 + 10 * pulse), 7)
        for x, y, t in self.misses:
            pygame.draw.circle(surf, (255, 250, 236), (int(x), int(y)), int(18 + 30 * t), 4)
        n = sum(self.found)
        q = pygame.Rect(0, 0, 720, 90)
        q.center = (W // 2, H - 84)
        draw_panel(surf, q, color=(255, 248, 232), radius=45)
        txt = f"Differences found: {n} of {len(self.diffs)}"
        draw_text(surf, txt, self.app.fonts.fit("h2", txt, 680), COL["ink"], q.center)


# ====================================================================== 3. sliding picture
class SliderPuzzle(PuzzleScreen):
    instructions = "Click a tile next to the empty space to slide it. Rebuild the picture!"
    backdrop_scene = "autumn_bakery"

    def setup(self):
        self.size = 4 if self.difficulty == "challenge" else 3
        shuffle_moves = {"relaxed": 24, "normal": 50, "challenge": 90}[self.difficulty]
        n = self.size
        self.board = list(range(n * n))  # value at position; n*n-1 is the blank
        self.blank_val = n * n - 1
        self.history = [n * n - 1]  # blank positions; reversing this solves the puzzle
        rng = random.Random()
        prev = None
        while True:
            for _ in range(shuffle_moves):
                b = self.board.index(self.blank_val)
                opts = [p for p in self.neighbors(b) if p != prev]
                p = rng.choice(opts)
                prev = b
                self._swap(b, p, record=True)
            if self.board != sorted(self.board):
                break
        self.anim = {}
        self.show_numbers = 0.0
        self.hint_tile = None
        self.pic = None

    def neighbors(self, p):
        n = self.size
        r, c = divmod(p, n)
        out = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n:
                out.append(rr * n + cc)
        return out

    def _swap(self, blank_pos, tile_pos, record=True):
        self.board[blank_pos], self.board[tile_pos] = self.board[tile_pos], self.board[blank_pos]
        if record:
            if len(self.history) >= 2 and self.history[-2] == tile_pos:
                self.history.pop()
            else:
                self.history.append(tile_pos)

    def board_rect(self):
        side = 720
        return pygame.Rect(W // 2 - side // 2 - 180, TOP_H + 110, side, side)

    def tile_rect(self, pos):
        br = self.board_rect()
        t = br.width // self.size
        r, c = divmod(pos, self.size)
        return pygame.Rect(br.x + c * t, br.y + r * t, t, t)

    def handle_puzzle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for p in range(self.size * self.size):
                if self.tile_rect(p).collidepoint(event.pos):
                    self.move(p)
                    return True
        return False

    def move(self, p):
        b = self.board.index(self.blank_val)
        if p in self.neighbors(b):
            self.anim[self.board[p]] = (self.tile_rect(p).topleft, 0.0)
            self._swap(b, p)
            self.app.audio.play("slide")
            self.hint_tile = None
            if self.board == sorted(self.board):
                self.complete()
        else:
            self.app.audio.play("wrong", 0.5)

    def hint_move(self):
        return self.history[-2] if len(self.history) >= 2 else None

    def hint(self):
        p = self.hint_move()
        if p is None:
            return False
        self.hint_tile = p
        self.show_numbers = 4.0
        return True

    def update_puzzle(self, dt):
        self.show_numbers = max(0.0, self.show_numbers - dt)
        for k in list(self.anim):
            start, t = self.anim[k]
            t += dt / 0.14
            if t >= 1:
                del self.anim[k]
            else:
                self.anim[k] = (start, t)

    def picture(self):
        if self.pic is None:
            src = self.app.assets.image("puzzles", "slider_picture.jpg", alpha=False)
            self.pic = pygame.transform.smoothscale(src, (self.board_rect().width, self.board_rect().width))
        return self.pic

    def draw_puzzle(self, surf):
        br = self.board_rect()
        draw_panel(surf, br.inflate(40, 40), radius=24)
        pygame.draw.rect(surf, (120, 80, 50), br)
        pic = self.picture()
        t = br.width // self.size
        nf = self.app.fonts.get("h2")
        for pos, val in enumerate(self.board):
            if val == self.blank_val and not self.solved:
                continue
            dst = self.tile_rect(pos)
            if val in self.anim:
                (sx, sy), k = self.anim[val]
                k = 1 - (1 - k) ** 2
                dst = dst.move(int((sx - dst.x) * (1 - k)), int((sy - dst.y) * (1 - k)))
            vr, vc = divmod(val, self.size)
            surf.blit(pic, dst, pygame.Rect(vc * t, vr * t, t, t))
            pygame.draw.rect(surf, (90, 56, 30), dst, 3)
            if self.show_numbers > 0:
                ok = val == pos
                pygame.draw.circle(surf, (255, 248, 232), dst.center, 38)
                pygame.draw.circle(surf, COL["green"] if ok else COL["orange"], dst.center, 38, 5)
                draw_text(surf, str(val + 1), nf, COL["ink"], dst.center)
        if self.hint_tile is not None and not self.solved:
            r = self.tile_rect(self.hint_tile)
            pulse = 0.5 + 0.5 * math.sin(self.app.time * 7)
            pygame.draw.rect(surf, (255, 220, 110), r.inflate(int(6 + 8 * pulse), int(6 + 8 * pulse)), 8, border_radius=8)
        # goal picture
        gr = pygame.Rect(br.right + 120, br.y + 60, 360, 360)
        draw_panel(surf, gr.inflate(30, 80).move(0, 18), radius=22)
        draw_text(surf, "The finished picture", self.app.fonts.fit("small", "The finished picture", 380), COL["ink"],
                  (gr.centerx, gr.y - 6), "midbottom")
        surf.blit(pygame.transform.smoothscale(pic, gr.size), gr)
        tip = pygame.Rect(gr.x - 40, gr.bottom + 90, gr.width + 80, 150)
        draw_panel(surf, tip, color=(255, 248, 232), radius=24)
        draw_paragraph(surf, "Tip: press Hint to see which tile to move next.", self.app.fonts.get("small"),
                       COL["ink"], tip.inflate(-40, -36))


# ====================================================================== 4. corn maze
class MazePuzzle(PuzzleScreen):
    instructions = "Guide the bluebird to the pumpkin! Click a spot in a straight line, or use the arrow keys."
    backdrop_scene = "corn_maze"

    def setup(self):
        self.cols, self.rows = {"relaxed": (11, 7), "normal": (15, 9), "challenge": (19, 11)}[self.difficulty]
        self.walls = self.generate(self.cols, self.rows)
        self.pos = (0, 0)
        self.goal = (self.cols - 1, self.rows - 1)
        self.trail = [self.pos]
        self.walk = []
        self.walk_t = 0.0
        self.show_path = 0.0
        self.draw_pos = list(self.pos)
        self.maze_surf = None

    @staticmethod
    def generate(cols, rows):
        # walls[(c, r)] = set of open directions
        rng = random.Random()
        open_ = {(c, r): set() for c in range(cols) for r in range(rows)}
        stack = [(0, 0)]
        seen = {(0, 0)}
        dirs = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
        opp = {"N": "S", "S": "N", "E": "W", "W": "E"}
        while stack:
            c, r = stack[-1]
            opts = [(d, (c + dx, r + dy)) for d, (dx, dy) in dirs.items()
                    if 0 <= c + dx < cols and 0 <= r + dy < rows and (c + dx, r + dy) not in seen]
            if not opts:
                stack.pop()
                continue
            d, nxt = rng.choice(opts)
            open_[(c, r)].add(d)
            open_[nxt].add(opp[d])
            seen.add(nxt)
            stack.append(nxt)
        return open_

    def geometry(self):
        area = pygame.Rect(120, TOP_H + 100, W - 240, H - TOP_H - 140)
        cell = min(area.width // self.cols, area.height // self.rows)
        mw, mh = cell * self.cols, cell * self.rows
        return pygame.Rect(area.centerx - mw // 2, area.centery - mh // 2, mw, mh), cell

    def cell_center(self, c, r):
        rect, cell = self.geometry()
        return (rect.x + c * cell + cell // 2, rect.y + r * cell + cell // 2)

    def can_move(self, c, r, d):
        return d in self.walls[(c, r)]

    def step_dir(self, d):
        dx, dy = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[d]
        c, r = self.walk[-1] if self.walk else self.pos
        if self.can_move(c, r, d):
            self.walk.append((c + dx, r + dy))
            return True
        return False

    def handle_puzzle(self, event):
        if event.type == pygame.KEYDOWN:
            d = {pygame.K_UP: "N", pygame.K_w: "N", pygame.K_DOWN: "S", pygame.K_s: "S",
                 pygame.K_LEFT: "W", pygame.K_a: "W", pygame.K_RIGHT: "E", pygame.K_d: "E"}.get(event.key)
            if d:
                if len(self.walk) < 3 and not self.step_dir(d):
                    self.app.audio.play("wrong", 0.4)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rect, cell = self.geometry()
            if rect.collidepoint(event.pos):
                tc = (event.pos[0] - rect.x) // cell
                tr = (event.pos[1] - rect.y) // cell
                self.walk_to(tc, tr)
                return True
        return False

    def walk_to(self, tc, tr):
        c, r = self.walk[-1] if self.walk else self.pos
        if (tc, tr) == (c, r):
            return
        if tc == c or tr == r:
            d = ("S" if tr > r else "N") if tc == c else ("E" if tc > c else "W")
            steps = abs(tc - c) + abs(tr - r)
            path = []
            cc, rr = c, r
            for _ in range(steps):
                if not self.can_move(cc, rr, d):
                    break
                dx, dy = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[d]
                cc, rr = cc + dx, rr + dy
                path.append((cc, rr))
            if path:
                self.walk.extend(path)
                return
        self.app.audio.play("wrong", 0.4)
        self.app.toast("Click a spot in a straight line from the bluebird, with no corn in the way.", 3)

    def path_to_goal(self):
        start = self.walk[-1] if self.walk else self.pos
        prev = {start: None}
        q = deque([start])
        dirs = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
        while q:
            cur = q.popleft()
            if cur == self.goal:
                break
            for d in self.walls[cur]:
                dx, dy = dirs[d]
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt not in prev:
                    prev[nxt] = cur
                    q.append(nxt)
        path = []
        cur = self.goal
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        return path[::-1]

    def hint(self):
        self.show_path = 3.5
        return True

    def update_puzzle(self, dt):
        self.show_path = max(0.0, self.show_path - dt)
        if self.walk:
            self.walk_t += dt / 0.11
            if self.walk_t >= 1:
                self.walk_t = 0.0
                self.pos = self.walk.pop(0)
                if self.pos not in self.trail[-1:]:
                    self.trail.append(self.pos)
                self.app.audio.play("click", 0.35)
                if self.pos == self.goal:
                    self.walk = []
                    self.complete()
        tx, ty = self.pos
        if self.walk:
            nx, ny = self.walk[0]
            tx, ty = tx + (nx - tx) * self.walk_t, ty + (ny - ty) * self.walk_t
        self.draw_pos = [tx, ty]

    def build_maze(self):
        rect, cell = self.geometry()
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill((214, 184, 130))
        rng = random.Random(4)
        for _ in range(int(rect.width * rect.height / 900)):
            x, y = rng.randrange(rect.width), rng.randrange(rect.height)
            s.fill((196, 164, 112), (x, y, 3, 2))
        wall = max(8, cell // 5)
        col_a, col_b = (126, 150, 58), (176, 160, 70)

        def stalk_line(x0, y0, x1, y1):
            pygame.draw.line(s, (80, 96, 36), (x0 + 2, y0 + 3), (x1 + 2, y1 + 3), wall + 2)
            pygame.draw.line(s, col_a, (x0, y0), (x1, y1), wall)
            n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 14))
            for i in range(n + 1):
                px = x0 + (x1 - x0) * i / n
                py = y0 + (y1 - y0) * i / n
                pygame.draw.circle(s, col_b if i % 2 else (200, 176, 80), (int(px), int(py)), wall // 2 + 2)
        for (c, r), opens in self.walls.items():
            x, y = c * cell, r * cell
            if "N" not in opens:
                stalk_line(x, y, x + cell, y)
            if "W" not in opens:
                stalk_line(x, y, x, y + cell)
            if c == self.cols - 1 and "E" not in opens:
                stalk_line(x + cell, y, x + cell, y + cell)
            if r == self.rows - 1 and "S" not in opens:
                stalk_line(x, y + cell, x + cell, y + cell)
        self.maze_surf = s

    def draw_puzzle(self, surf):
        rect, cell = self.geometry()
        draw_panel(surf, rect.inflate(40, 40), radius=22, color=(196, 170, 110))
        if self.maze_surf is None:
            self.build_maze()
        surf.blit(self.maze_surf, rect)
        for c, r in self.trail:
            pygame.draw.circle(surf, (250, 236, 200), self.cell_center(c, r), max(4, cell // 10))
        if self.show_path > 0:
            pts = [self.cell_center(c, r) for c, r in self.path_to_goal()]
            if len(pts) > 1:
                for i, p in enumerate(pts):
                    if (i + int(self.app.time * 8)) % 2 == 0:
                        pygame.draw.circle(surf, (255, 214, 90), p, max(5, cell // 7))
        g = self.app.assets.obj_scaled("pumpkin", int(cell * 0.95))
        surf.blit(g, g.get_rect(center=self.cell_center(*self.goal)))
        bx, by = self.draw_pos
        rx = rect.x + bx * cell + cell / 2
        ry = rect.y + by * cell + cell / 2 - math.sin(self.app.time * 8) * (3 if self.walk else 1)
        b = self.app.assets.obj_scaled("bluebird", int(cell * 0.95))
        surf.blit(b, b.get_rect(center=(rx, ry)))


# ====================================================================== 5. harvest code (patterns)
class PatternPuzzle(PuzzleScreen):
    instructions = "Look at the pattern. Which picture comes next? Click your answer below."
    backdrop_scene = "fall_fair"

    ICONS = ["apple", "maple_leaf", "pumpkin", "acorn", "sunflower", "candy_corn", "pear", "lollipop", "pie", "corn"]

    def setup(self):
        self.rounds = {"relaxed": 5, "normal": 6, "challenge": 7}[self.difficulty]
        self.n_opts = 3 if self.difficulty == "relaxed" else 4
        self.round = 0
        self.rng = random.Random()
        self.new_round()

    def new_round(self):
        rng = self.rng
        patterns = ["AB", "AAB", "ABB", "ABC", "AABB", "ABCB", "ABAC"]
        level = min(len(patterns), 2 + self.round + (1 if self.difficulty == "challenge" else 0))
        pat = rng.choice(patterns[:level])
        letters = sorted(set(pat))
        icons = rng.sample(self.ICONS, len(letters))
        mapping = dict(zip(letters, icons))
        length = max(6, len(pat) * 2 + 1)
        seq = [mapping[pat[i % len(pat)]] for i in range(length + 1)]
        self.shown = seq[:-1]
        self.answer = seq[-1]
        opts = {self.answer}
        others = [i for i in icons if i != self.answer] + [i for i in self.ICONS if i not in icons]
        for o in others:
            if len(opts) >= self.n_opts:
                break
            opts.add(o)
        self.options = list(opts)
        rng.shuffle(self.options)
        self.disabled = set()
        self.reveal = 0.0

    def seq_rect(self, i):
        n = len(self.shown) + 1
        size = min(170, (W - 200) // n - 16)
        total = n * size + (n - 1) * 16
        x0 = W // 2 - total // 2
        return pygame.Rect(x0 + i * (size + 16), 340, size, size)

    def opt_rect(self, i):
        size = 230
        gap = 50
        total = self.n_opts * size + (self.n_opts - 1) * gap
        x0 = W // 2 - total // 2
        return pygame.Rect(x0 + i * (size + gap), 690, size, size)

    def handle_puzzle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.reveal <= 0:
            for i, o in enumerate(self.options):
                if self.opt_rect(i).collidepoint(event.pos) and o not in self.disabled:
                    if o == self.answer:
                        self.app.audio.play("found")
                        self.particles.burst(self.opt_rect(i).center, 24)
                        self.reveal = 1.0
                    else:
                        self.disabled.add(o)
                        self.app.audio.play("wrong", 0.6)
                        self.app.toast("Not quite. Try another one!", 2)
                    return True
        return False

    def hint(self):
        wrong = [o for o in self.options if o != self.answer and o not in self.disabled]
        if not wrong:
            return False
        self.disabled.add(random.choice(wrong))
        return True

    def update_puzzle(self, dt):
        if self.reveal > 0:
            self.reveal -= dt
            if self.reveal <= 0:
                self.round += 1
                if self.round >= self.rounds:
                    self.complete()
                else:
                    self.new_round()

    def hovering(self):
        return super().hovering() or any(self.opt_rect(i).collidepoint(self.app.mouse) and o not in self.disabled
                                         for i, o in enumerate(self.options))

    def draw_puzzle(self, surf):
        a = self.app
        panel = pygame.Rect(80, 250, W - 160, 300)
        draw_panel(surf, panel)
        for i, k in enumerate(self.shown):
            r = self.seq_rect(i)
            img = a.assets.obj_scaled(k, r.width)
            surf.blit(img, r)
        r = self.seq_rect(len(self.shown))
        if self.reveal > 0 or self.solved:
            img = a.assets.obj_scaled(self.answer, r.width)
            surf.blit(img, r)
        else:
            pygame.draw.rect(surf, (255, 236, 200), r, border_radius=24)
            pygame.draw.rect(surf, COL["orange"], r, 6, border_radius=24)
            draw_text(surf, "?", a.fonts.sized("h1", int(r.height * 0.7)), COL["orange_dk"], r.center)
        q = pygame.Rect(0, 0, 560, 84)
        q.center = (W // 2, 620)
        draw_panel(surf, q, color=(255, 248, 232), radius=42)
        draw_text(surf, "What comes next?", a.fonts.fit("h2", "What comes next?", 520), COL["ink"], q.center)
        for i, o in enumerate(self.options):
            r = self.opt_rect(i)
            off = o in self.disabled
            hover = r.collidepoint(a.mouse) and not off
            draw_panel(surf, r.move(0, -8 if hover else 0), color=(255, 250, 238) if not off else (214, 204, 190),
                       border=COL["orange"] if hover else COL["ink_soft"], radius=26)
            img = a.assets.obj_scaled(o, int(r.width * 0.8))
            if off:
                img = img.copy()
                img.set_alpha(70)
            surf.blit(img, img.get_rect(center=r.move(0, -8 if hover else 0).center))
        # round dots
        for i in range(self.rounds):
            c = (W // 2 + (i - (self.rounds - 1) / 2) * 50, 990)
            pygame.draw.circle(surf, (90, 56, 30), c, 16)
            pygame.draw.circle(surf, COL["gold"] if i < self.round else (240, 228, 206), c, 13)
        draw_text(surf, f"Round {min(self.round + 1, self.rounds)} of {self.rounds}", a.fonts.get("small"), (255, 248, 232),
                  (W // 2, 1040), shadow=(40, 20, 8))


PUZZLES = {"memory": MemoryPuzzle, "spot": SpotPuzzle, "slider": SliderPuzzle, "maze": MazePuzzle, "pattern": PatternPuzzle}


def make_puzzle(app, n):
    return PUZZLES[CHAPTERS[n - 1]["puzzle"]](app, n)
