"""Regenerates every image asset in assets/ (all drawn by code - 100% original art).

    python tools/make_art.py            # everything
    python tools/make_art.py objects    # just one group: objects | scenes | logo | puzzles

Requires numpy and Pillow. The generated files are committed, so building the game
does NOT need to run this.
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from artkit import Canvas  # noqa: E402
import sprites  # noqa: E402
import scenes  # noqa: E402

ASSETS = os.path.join(os.path.dirname(HERE), "assets")


def out(*parts):
    p = os.path.join(ASSETS, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def make_objects():
    for name in sprites.SPRITES:
        sprites.render(name, 384).save(out("objects", f"{name}.png"), optimize=True)
        print("object", name)


def make_scenes():
    for name, fn in scenes.SCENES.items():
        fn().convert("RGB").save(out("scenes", f"{name}.jpg"), quality=92, subsampling=0)
        print("scene", name)


def magnifier(c, cx, cy, r, ang_handle=45):
    import math
    a = math.radians(ang_handle)
    hx0, hy0 = cx + (r + 10) * math.cos(a), cy + (r + 10) * math.sin(a)
    hx1, hy1 = cx + (r + 330) * math.cos(a), cy + (r + 330) * math.sin(a)
    handle = c.L([(hx0, hy0), (hx1, hy1)], 95)
    c.shadow(handle, dx=16, dy=24, blur=24, opacity=0.4)
    c.paint(handle, (120, 64, 34), shade=0.7, soft=30, spec=0.4, tex=0.3, tex_stretch=(0.3, 3))
    c.paint(c.L([(hx0, hy0), (cx + (r + 70) * math.cos(a), cy + (r + 70) * math.sin(a))], 110), (196, 150, 60),
            shade=0.7, soft=20, spec=0.6)
    lens = c.E(cx, cy, r)
    c.paint(lens, (220, 236, 240), shade=0.3, soft=r * 0.4, alpha=0.2)
    c.paint(c.E(cx - r * 0.35, cy - r * 0.35, r * 0.32, r * 0.2), (255, 255, 255), shade=0, edge=0, alpha=0.55, blur=14)
    rim = c.S(c.E(cx, cy, r + 38), c.E(cx, cy, r))
    c.shadow(rim, dx=12, dy=18, blur=18, opacity=0.35)
    c.paint(rim, (206, 160, 64), shade=0.8, soft=22, spec=0.8, edge=0.3)


def make_logo():
    c = Canvas(1024, ss=2)
    badge = c.E(500, 500, 470)
    c.paint(badge, (255, 214, 140), shade=0.35, soft=160, edge=0.15, grad=(236, 140, 60), grad_dir=(0, 1))
    ring = c.S(c.E(500, 500, 470), c.E(500, 500, 440))
    c.paint(ring, (150, 70, 30), shade=0.6, soft=20, spec=0.3)
    for (x, y, ang, col) in [(250, 260, -30, (214, 64, 30)), (760, 250, 35, (236, 170, 40)), (220, 700, 200, (196, 90, 30))]:
        c.paste(sprites.render("maple_leaf", 384), x, y, 230, rot=ang)
    sprites.pumpkin(c, (232, 120, 30), cx=420, cy=590, s=0.6)
    magnifier(c, 650, 400, 145, 50)
    logo = c.image(drop_shadow=False)
    logo.save(out("logo.png"), optimize=True)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    logo.save(out("icon.ico"), sizes=sizes)
    logo.resize((256, 256), Image.LANCZOS).save(out("icon_256.png"))
    print("logo + icon")


def make_puzzles():
    # Sliding-puzzle picture: a warm pie still life
    c = Canvas(900, 900, ss=2, units=None)
    c.fill((246, 236, 216))
    for i in range(0, 900, 90):  # gingham cloth
        c.paint(c.R(i, 0, i + 45, 900), (214, 80, 64), shade=0, edge=0, alpha=0.45)
        c.paint(c.R(0, i, 900, i + 45), (214, 80, 64), shade=0, edge=0, alpha=0.45)
    c.paint(c.R(0, 0, 900, 900), (255, 230, 190), shade=0, edge=0, alpha=0.12)
    for name, x, y, w, rot in [("maple_leaf", 140, 150, 220, -20), ("oak_leaf", 760, 130, 200, 25),
                               ("maple_leaf", 780, 760, 210, 150), ("acorn", 140, 760, 170, -10),
                               ("cider_mug", 720, 440, 260, 0), ("apple", 160, 470, 200, 0),
                               ("pie", 450, 520, 560, 0), ("pumpkin", 450, 180, 260, 0)]:
        c.paste(sprites.render(name, 384), x, y, w, rot=rot)
    c.vignette(0.2)
    c.image().convert("RGB").save(out("puzzles", "slider_picture.jpg"), quality=92)

    # Memory card back
    b = Canvas(320, 400, ss=2, units=None)
    b.paint(b.R(4, 4, 316, 396, 30), (214, 96, 40), shade=0.4, soft=40, edge=0.2, grad=(186, 70, 34), grad_dir=(0, 1))
    b.paint(b.S(b.R(22, 22, 298, 378, 20), b.R(32, 32, 288, 368, 16)), (250, 214, 140), shade=0.4, soft=8)
    b.paste(sprites.render("maple_leaf", 384), 160, 200, 200)
    b.image().save(out("puzzles", "card_back.png"), optimize=True)
    print("puzzles")


if __name__ == "__main__":
    groups = sys.argv[1:] or ["objects", "logo", "puzzles", "scenes"]
    for g in groups:
        {"objects": make_objects, "scenes": make_scenes, "logo": make_logo, "puzzles": make_puzzles}[g]()
