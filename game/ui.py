"""UI toolkit: fonts that honour the Text Size option, big friendly buttons, sliders, panels, stars."""
import math
import pygame

W, H = 1920, 1080

COL = {
    "cream": (252, 244, 228), "cream2": (244, 230, 204), "paper": (250, 240, 220),
    "ink": (72, 42, 24), "ink_soft": (122, 86, 58), "orange": (228, 122, 42), "orange_dk": (180, 84, 30),
    "gold": (244, 190, 64), "gold_dk": (190, 130, 30), "green": (92, 150, 70), "green_dk": (60, 110, 46),
    "red": (196, 70, 50), "white": (255, 255, 255), "shadow": (40, 22, 10), "disabled": (190, 178, 160),
}

TEXT_SCALE = {"normal": 1.0, "large": 1.18, "xlarge": 1.36}


class Fonts:
    BASE = {"title": 112, "h1": 70, "h2": 52, "button": 44, "body": 38, "small": 31, "tiny": 26}
    HEADING = ("title", "h1", "h2")

    def __init__(self):
        pygame.font.init()
        self.scale = 1.0
        self.cache = {}
        self.serif = self._find(["georgia", "cambria", "dejavuserif", "liberationserif", "timesnewroman"])
        self.sans = self._find(["segoeui", "segoeuisemibold", "calibri", "arial", "dejavusans", "liberationsans"])

    @staticmethod
    def _find(names):
        for n in names:
            try:
                path = pygame.font.match_font(n, bold=True)
            except Exception:
                path = None
            if path:
                return path
        return None

    def set_scale(self, key):
        self.scale = TEXT_SCALE.get(key, 1.0)
        self.cache.clear()

    def px(self, kind):
        return max(12, int(self.BASE[kind] * self.scale))

    def sized(self, kind, px):
        key = (kind in self.HEADING, px)
        f = self.cache.get(key)
        if f is None:
            path = self.serif if kind in self.HEADING else self.sans
            try:
                f = pygame.font.Font(path, px) if path else pygame.font.Font(None, int(px * 1.3))
            except Exception:
                f = pygame.font.Font(None, int(px * 1.3))
            if path:
                f.set_bold(kind in self.HEADING or kind == "button")
            self.cache[key] = f
        return f

    def get(self, kind):
        return self.sized(kind, self.px(kind))

    def fit(self, kind, text, max_w):
        """Largest font of this kind (up to the user's text size) that fits max_w."""
        px = self.px(kind)
        f = self.sized(kind, px)
        while px > 14 and f.size(text)[0] > max_w:
            px = int(px * 0.92)
            f = self.sized(kind, px)
        return f


_text_cache = {}


def render_text(font, text, color, shadow=None):
    key = (id(font), text, color, shadow)
    s = _text_cache.get(key)
    if s is None:
        main = font.render(text, True, color)
        if shadow:
            s = pygame.Surface((main.get_width() + 3, main.get_height() + 3), pygame.SRCALPHA)
            sh = font.render(text, True, shadow)
            sh.set_alpha(110)
            s.blit(sh, (3, 3))
            s.blit(main, (0, 0))
        else:
            s = main
        if len(_text_cache) > 1500:
            _text_cache.clear()
        _text_cache[key] = s
    return s


def draw_text(surf, text, font, color, pos, anchor="center", shadow=None):
    s = render_text(font, text, color, shadow)
    r = s.get_rect(**{anchor: pos})
    surf.blit(s, r)
    return r


def wrap(text, font, width):
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= width or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_paragraph(surf, text, font, color, rect, align="center", line_gap=1.18):
    lines = wrap(text, font, rect.width)
    lh = int(font.get_linesize() * line_gap)
    total = lh * len(lines)
    y = rect.top
    for ln in lines:
        if align == "center":
            draw_text(surf, ln, font, color, (rect.centerx, y), "midtop")
        else:
            draw_text(surf, ln, font, color, (rect.left, y), "topleft")
        y += lh
    return total


# ---------------------------------------------------------------------- panels
_panel_cache = {}


def panel_surface(w, h, color=COL["paper"], border=COL["ink_soft"], radius=30, alpha=245, shadow=True):
    key = (w, h, color, border, radius, alpha, shadow)
    s = _panel_cache.get(key)
    if s is None:
        pad = 24 if shadow else 0
        s = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        if shadow:
            for i in range(10, 0, -1):
                a = int(9 * (11 - i) * alpha / 255)
                pygame.draw.rect(s, (*COL["shadow"], a), pygame.Rect(pad - i + 6, pad - i + 12, w + i * 2, h + i * 2),
                                 border_radius=radius + i)
        body = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(body, (*color, alpha), body.get_rect(), border_radius=radius)
        # soft top highlight
        hl = pygame.Surface((w, h // 2), pygame.SRCALPHA)
        pygame.draw.rect(hl, (255, 255, 255, 34), hl.get_rect(), border_radius=radius)
        body.blit(hl, (0, 0))
        if border:
            pygame.draw.rect(body, (*border, min(255, alpha)), body.get_rect(), width=4, border_radius=radius)
        s.blit(body, (pad, pad))
        _panel_cache[key] = s
    return s


def draw_panel(surf, rect, **kw):
    shadow = kw.get("shadow", True)
    s = panel_surface(rect.width, rect.height, **kw)
    pad = 24 if shadow else 0
    surf.blit(s, (rect.x - pad, rect.y - pad))


def dim(surf, alpha=140, color=(30, 18, 8)):
    ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    ov.fill((*color, alpha))
    surf.blit(ov, (0, 0))


# ---------------------------------------------------------------------- stars
def star_points(cx, cy, r_out, r_in=None, rot=-90):
    r_in = r_in or r_out * 0.48
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 36)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def draw_star(surf, center, r, filled=True, scale=1.0):
    r = r * scale
    if r < 2:
        return
    pts = star_points(center[0], center[1] + r * 0.06, r)
    sh = [(x + r * 0.06, y + r * 0.1) for x, y in pts]
    pygame.draw.polygon(surf, (90, 50, 20), sh)
    if filled:
        pygame.draw.polygon(surf, COL["gold"], pts)
        inner = star_points(center[0] - r * 0.05, center[1] - r * 0.02, r * 0.62)
        pygame.draw.polygon(surf, (255, 222, 120), inner)
        pygame.draw.polygon(surf, COL["gold_dk"], pts, width=max(2, int(r * 0.08)))
    else:
        pygame.draw.polygon(surf, (226, 210, 186), pts)
        pygame.draw.polygon(surf, (160, 136, 110), pts, width=max(2, int(r * 0.08)))


def draw_check(surf, center, size, color=COL["green"]):
    x, y = center
    s = size
    pts = [(x - s * 0.5, y), (x - s * 0.15, y + s * 0.35), (x + s * 0.55, y - s * 0.4)]
    pygame.draw.lines(surf, (40, 70, 30), False, [(px + 2, py + 3) for px, py in pts], max(3, int(s * 0.22)))
    pygame.draw.lines(surf, color, False, pts, max(3, int(s * 0.2)))


# ---------------------------------------------------------------------- widgets
_btn_cache = {}

STYLES = {
    "normal": ((255, 248, 232), (238, 218, 184), COL["ink"]),
    "primary": ((246, 160, 70), (214, 104, 34), (255, 255, 255)),
    "green": ((132, 186, 96), (82, 138, 60), (255, 255, 255)),
    "selected": ((250, 206, 100), (226, 156, 50), COL["ink"]),
    "quiet": ((240, 228, 206), (220, 200, 170), COL["ink"]),
}


def button_skin(w, h, style, state, radius):
    key = (w, h, style, state, radius)
    s = _btn_cache.get(key)
    if s is None:
        top, bot, _ = STYLES[style]
        if state == "hover":
            top = tuple(min(255, c + 16) for c in top)
            bot = tuple(min(255, c + 16) for c in bot)
        elif state == "disabled":
            top, bot = (226, 218, 204), (206, 196, 180)
        s = pygame.Surface((w, h + 8), pygame.SRCALPHA)
        pygame.draw.rect(s, (90, 56, 30, 150 if state != "disabled" else 70), pygame.Rect(0, 8, w, h), border_radius=radius)
        body = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            t = y / max(1, h - 1)
            c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
            pygame.draw.line(body, c, (0, y), (w, y))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        hl = pygame.Surface((w - 12, max(4, h // 3)), pygame.SRCALPHA)
        pygame.draw.rect(hl, (255, 255, 255, 60), hl.get_rect(), border_radius=max(4, radius - 6))
        body.blit(hl, (6, 4))
        border = (120, 76, 40) if state != "disabled" else (170, 156, 136)
        pygame.draw.rect(body, border, body.get_rect(), width=3, border_radius=radius)
        s.blit(body, (0, 0))
        _btn_cache[key] = s
    return s


class Widget:
    enabled = True
    visible = True

    def handle(self, event):
        return False

    def update(self, dt):
        pass

    def draw(self, surf):
        pass

    def hovered(self):
        return False


class Button(Widget):
    def __init__(self, app, rect, label, on_click, style="normal", font="button", enabled=True, icon=None, sublabel=None):
        self.app = app
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.style = style
        self.font = font
        self.enabled = enabled
        self.icon = icon
        self.sublabel = sublabel
        self.down = False
        self.radius = min(30, self.rect.height // 2)
        self.pulse = 0.0

    def hovered(self):
        return self.visible and self.enabled and self.rect.collidepoint(self.app.mouse)

    def handle(self, event):
        if not (self.visible and self.enabled):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.down = True
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was = self.down
            self.down = False
            if was and self.rect.collidepoint(event.pos):
                self.app.audio.play("click")
                if self.on_click:
                    self.on_click()
                return True
        return False

    def update(self, dt):
        self.pulse += dt

    def draw(self, surf):
        if not self.visible:
            return
        state = "disabled" if not self.enabled else ("hover" if self.hovered() else "normal")
        skin = button_skin(self.rect.width, self.rect.height, self.style, state, self.radius)
        off = 5 if (self.down and self.hovered()) else 0
        surf.blit(skin, (self.rect.x, self.rect.y + off))
        color = STYLES[self.style][2] if self.enabled else (150, 136, 118)
        x_text = self.rect.centerx
        avail = self.rect.width - 36
        if self.icon is not None:
            ic = self.icon
            ir = ic.get_rect(midleft=(self.rect.x + 18, self.rect.centery + off))
            surf.blit(ic, ir)
            avail -= ic.get_width() + 10
            x_text = self.rect.x + 18 + ic.get_width() + 10 + avail // 2
        if self.sublabel:
            f = self.app.fonts.fit(self.font, self.label, avail)
            draw_text(surf, self.label, f, color, (x_text, self.rect.centery - f.get_height() * 0.32 + off))
            f2 = self.app.fonts.fit("tiny", self.sublabel, avail)
            draw_text(surf, self.sublabel, f2, color, (x_text, self.rect.centery + f.get_height() * 0.42 + off))
        else:
            f = self.app.fonts.fit(self.font, self.label, avail)
            draw_text(surf, self.label, f, color, (x_text, self.rect.centery + off))


class Slider(Widget):
    """Big slider with - and + buttons either side for easy adjusting."""

    def __init__(self, app, rect, value, on_change, step=0.1):
        self.app = app
        self.rect = pygame.Rect(rect)
        self.value = value
        self.on_change = on_change
        self.step = step
        bw = self.rect.height
        self.minus = Button(app, (self.rect.x, self.rect.y, bw, bw), "-", lambda: self.nudge(-step), font="h2")
        self.plus = Button(app, (self.rect.right - bw, self.rect.y, bw, bw), "+", lambda: self.nudge(step), font="h2")
        self.track = pygame.Rect(self.rect.x + bw + 34, self.rect.centery - 9, self.rect.width - 2 * bw - 68, 18)
        self.dragging = False

    def nudge(self, d):
        self.set(round(self.value + d, 2))

    def set(self, v):
        v = min(1.0, max(0.0, v))
        if abs(v - self.value) > 1e-6:
            self.value = v
            self.on_change(v)

    def _from_x(self, x):
        return (x - self.track.x) / max(1, self.track.width)

    def hovered(self):
        return self.minus.hovered() or self.plus.hovered() or self.track.inflate(40, 60).collidepoint(self.app.mouse)

    def handle(self, event):
        if self.minus.handle(event) or self.plus.handle(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.track.inflate(40, 60).collidepoint(event.pos):
            self.dragging = True
            self.set(self._from_x(event.pos[0]))
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.set(self._from_x(event.pos[0]))
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            self.app.audio.play("click")
            return True
        return False

    def draw(self, surf):
        self.minus.draw(surf)
        self.plus.draw(surf)
        t = self.track
        pygame.draw.rect(surf, (200, 180, 150), t.move(0, 3), border_radius=9)
        pygame.draw.rect(surf, (236, 222, 196), t, border_radius=9)
        fill = pygame.Rect(t.x, t.y, int(t.width * self.value), t.height)
        if fill.width > 0:
            pygame.draw.rect(surf, COL["orange"], fill, border_radius=9)
        kx = t.x + int(t.width * self.value)
        pygame.draw.circle(surf, (110, 66, 34), (kx + 2, t.centery + 4), 26)
        pygame.draw.circle(surf, (255, 246, 228), (kx, t.centery), 26)
        pygame.draw.circle(surf, COL["orange_dk"], (kx, t.centery), 26, 4)


class Toggle(Widget):
    """A row of option buttons where one is selected (e.g. Relaxed / Normal / Challenge)."""

    def __init__(self, app, rect, options, current, on_change, font="button"):
        self.app = app
        self.rect = pygame.Rect(rect)
        self.options = options  # list of (value, label)
        self.current = current
        self.on_change = on_change
        n = len(options)
        gap = 16
        bw = (self.rect.width - gap * (n - 1)) // n
        self.buttons = []
        for i, (val, label) in enumerate(options):
            r = (self.rect.x + i * (bw + gap), self.rect.y, bw, self.rect.height)
            self.buttons.append(Button(app, r, label, (lambda v=val: self.choose(v)), font=font))
        self._sync()

    def _sync(self):
        for (val, _), b in zip(self.options, self.buttons):
            b.style = "selected" if val == self.current else "normal"

    def choose(self, v):
        if v != self.current:
            self.current = v
            self._sync()
            self.on_change(v)

    def hovered(self):
        return any(b.hovered() for b in self.buttons)

    def handle(self, event):
        return any(b.handle(event) for b in self.buttons)

    def draw(self, surf):
        for b in self.buttons:
            b.draw(surf)


class Particles:
    """Sparkles and leaf bursts."""

    def __init__(self):
        self.items = []

    def burst(self, pos, n=22, colors=((255, 230, 120), (255, 255, 255), (255, 190, 80)), speed=380, life=0.9, size=7):
        import random
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * speed
            self.items.append([pos[0], pos[1], math.cos(a) * v, math.sin(a) * v - 80, life * random.uniform(0.6, 1.0),
                               life, random.choice(colors), size * random.uniform(0.6, 1.3)])

    def update(self, dt):
        alive = []
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.94
            p[3] = p[3] * 0.94 + 260 * dt
            p[4] -= dt
            if p[4] > 0:
                alive.append(p)
        self.items = alive

    def draw(self, surf):
        for x, y, _vx, _vy, t, life, col, size in self.items:
            k = max(0.0, t / life)
            r = max(1, int(size * (0.4 + 0.6 * k)))
            if r > 3:
                pts = star_points(x, y, r * 1.6, r * 0.55, rot=-90 + (1 - k) * 120)
                pygame.draw.polygon(surf, col, pts)
            else:
                pygame.draw.circle(surf, col, (int(x), int(y)), r)
