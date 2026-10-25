"""The game application: window, main loop, screen stack, shared assets."""
import os
import sys

import pygame

from . import paths
from .audio import Audio
from .storage import Progress, Settings
from .ui import COL, W, H, Fonts, draw_panel, draw_text
from .updater import UpdateManager
from .version import APP_NAME, VERSION


class Assets:
    def __init__(self):
        self._objects = {}
        self._scenes = {}
        self._img = {}

    def image(self, *parts, alpha=True):
        key = parts
        if key not in self._img:
            surf = pygame.image.load(paths.asset(*parts))
            self._img[key] = surf.convert_alpha() if alpha else surf.convert()
        return self._img[key]

    def obj(self, name):
        if name not in self._objects:
            self._objects[name] = self.image("objects", f"{name}.png")
        return self._objects[name]

    def obj_scaled(self, name, size, rot=0.0, flip=False):
        key = ("s", name, int(size), int(rot), flip)
        if key not in self._img:
            src = self.obj(name)
            s = src
            if flip:
                s = pygame.transform.flip(s, True, False)
            if rot:
                s = pygame.transform.rotozoom(s, rot, size / src.get_width())
            else:
                s = pygame.transform.smoothscale(s, (int(size), int(size)))
            self._img[key] = s
        return self._img[key]

    def scene(self, name):
        if name not in self._scenes:
            self._scenes[name] = self.image("scenes", f"{name}.jpg", alpha=False)
        return self._scenes[name]


class Screen:
    """Base class for screens. Screens keep a list of widgets for convenience."""
    opaque = True

    def __init__(self, app):
        self.app = app
        self.widgets = []

    def on_enter(self):
        pass

    def layout(self):
        """Rebuild widgets (called on enter and when the text size changes)."""

    def handle(self, event):
        for w in reversed(self.widgets):
            if w.handle(event):
                return True
        return False

    def update(self, dt):
        for w in self.widgets:
            w.update(dt)

    def draw(self, surf):
        for w in self.widgets:
            w.draw(surf)

    def hovering(self):
        return any(w.hovered() for w in self.widgets)


class App:
    def __init__(self, test_driver=None):
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()
        self.settings = Settings()
        self.progress = Progress()
        self.fonts = Fonts()
        self.fonts.set_scale(self.settings["text_size"])
        self.window = None
        self._make_display()
        pygame.display.set_caption(f"{APP_NAME}  v{VERSION}")
        try:
            pygame.display.set_icon(pygame.image.load(paths.asset("icon_256.png")))
        except Exception:
            pass
        self.mouse = (0, 0)
        self._loading_frame("Getting the harvest ready...")
        self.assets = Assets()
        self.audio = Audio(self.settings)
        self.updater = UpdateManager()
        self.stack = []
        self.toasts = []
        self.clock = pygame.time.Clock()
        self.running = True
        self.time = 0.0
        self.test_driver = test_driver
        self._cursor = None
        self.fade = 0.0

    # ------------------------------------------------------------ display
    def _make_display(self):
        flags = pygame.SCALED | pygame.RESIZABLE
        if self.settings["fullscreen"]:
            flags |= pygame.FULLSCREEN
        try:
            self.surface = pygame.display.set_mode((W, H), flags, vsync=1)
        except Exception:
            self.surface = pygame.display.set_mode((W, H), flags)
        if not self.settings["fullscreen"]:
            self._fit_window()

    def _fit_window(self):
        """Make the window a comfortable size for this monitor (the game scales smoothly)."""
        try:
            win = pygame.Window.from_display_module()
            sizes = pygame.display.get_desktop_sizes()
            if sizes:
                dw, dh = sizes[0]
                scale = min(dw * 0.88 / W, dh * 0.85 / H, 1.0)
                win.size = (max(960, int(W * scale)), max(540, int(H * scale)))
                win.position = pygame.WINDOWPOS_CENTERED
            self.window = win
        except Exception:
            self.window = None

    def set_fullscreen(self, on):
        if bool(on) == bool(self.settings["fullscreen"]):
            return
        self.settings.set("fullscreen", bool(on))
        try:
            pygame.display.toggle_fullscreen()
        except Exception:
            self._make_display()
        if not on:
            self._fit_window()

    def set_text_size(self, key):
        self.settings.set("text_size", key)
        self.fonts.set_scale(key)
        for s in self.stack:
            s.layout()

    def _loading_frame(self, text):
        self.surface.fill((250, 226, 186))
        f = self.fonts.get("h2")
        draw_text(self.surface, text, f, COL["ink"], (W // 2, H // 2))
        pygame.display.flip()
        pygame.event.pump()

    # ------------------------------------------------------------ screens
    @property
    def top(self):
        return self.stack[-1] if self.stack else None

    def push(self, screen):
        self.stack.append(screen)
        screen.layout()
        screen.on_enter()

    def pop(self):
        if self.stack:
            self.stack.pop()
        if self.top:
            self.top.layout()
            self.top.on_enter()

    def replace(self, screen):
        self.stack = []
        self.push(screen)
        self.fade = 1.0

    def toast(self, text, secs=4.5):
        self.toasts = [t for t in self.toasts if t[0] != text]
        self.toasts.append([text, secs, secs])

    def quit(self):
        self.running = False

    # ------------------------------------------------------------ loop
    def run(self, first_screen):
        self.push(first_screen)
        self.audio.start_music()
        while self.running:
            if self.test_driver:  # automated test: run as fast as possible with a steady 60 fps timestep
                self.clock.tick(0)
                dt = 1 / 60
            else:
                dt = min(0.05, self.clock.tick(60) / 1000.0)
            self.time += dt
            self.step(dt)
        self.shutdown()

    def step(self, dt):
        self.mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                self.mouse = event.pos
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.set_fullscreen(not self.settings["fullscreen"])
                continue
            if self.top:
                self.top.handle(event)
        if self.test_driver:
            self.test_driver.tick(self, dt)
        if self.updater.ready_to_quit:
            self.running = False
        if self.top:
            self.top.update(dt)
        self.toasts = [[t, s - dt, total] for t, s, total in self.toasts if s - dt > 0]
        self.draw()
        self._update_cursor()

    def draw(self):
        surf = self.surface
        # draw from the last opaque screen upward so overlays show what's beneath
        start = 0
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].opaque:
                start = i
                break
        for s in self.stack[start:]:
            s.draw(surf)
        self._draw_toasts(surf)
        if self.fade > 0:
            ov = pygame.Surface((W, H))
            ov.fill((40, 24, 12))
            ov.set_alpha(int(255 * self.fade))
            surf.blit(ov, (0, 0))
            self.fade = max(0.0, self.fade - 0.08)
        pygame.display.flip()

    def _draw_toasts(self, surf):
        top_area = getattr(self.top, "toast_top", False)
        y = 200 if top_area else H - 90
        for text, left, total in self.toasts[-2:]:
            f = self.fonts.fit("small", text, 1300)
            tw = f.size(text)[0] + 80
            r = pygame.Rect(0, 0, tw, f.get_height() + 40)
            r.center = (W // 2, y)
            a = min(1.0, left / 0.4, (total - left) / 0.25 + 0.01)
            tmp = pygame.Surface((r.width + 60, r.height + 60), pygame.SRCALPHA)
            draw_panel(tmp, pygame.Rect(30, 30, r.width, r.height), color=(255, 246, 226), radius=24)
            draw_text(tmp, text, f, COL["ink"], (30 + r.width // 2, 30 + r.height // 2))
            tmp.set_alpha(int(255 * max(0.0, min(1.0, a))))
            surf.blit(tmp, (r.x - 30, r.y - 30))
            y += (r.height + 20) if top_area else -(r.height + 20)

    def _update_cursor(self):
        want = pygame.SYSTEM_CURSOR_HAND if (self.top and self.top.hovering()) else pygame.SYSTEM_CURSOR_ARROW
        if want != self._cursor:
            try:
                pygame.mouse.set_cursor(want)
            except Exception:
                pass
            self._cursor = want

    def shutdown(self):
        for s in self.stack:
            if hasattr(s, "save_state"):
                try:
                    s.save_state()
                except Exception:
                    pass
        self.settings.save()
        self.progress.save()
        pygame.quit()

    def screenshot(self, path):
        pygame.image.save(self.surface, path)
