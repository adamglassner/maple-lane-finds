"""Painted 1920x1080 scene backgrounds for Maple Lane Finds (all original, drawn in code)."""
import math
import random
from PIL import Image
from artkit import Canvas, mix, shade_col
import sprites

W, H = 1920, 1080
_cache = {}


def spr(name, size=320):
    key = (name, size)
    if key not in _cache:
        _cache[key] = sprites.render(name, size)
    return _cache[key]


def new_canvas():
    return Canvas(W, H, ss=2, units=None)


# ------------------------------------------------------------------ building blocks
def sky(c, top=(128, 182, 226), bottom=(255, 214, 160)):
    c.fill(top, grad=bottom, grad_dir=(0, 1))


def sun(c, x, y, r=90):
    c.paint(c.E(x, y, r * 5), (255, 200, 120), shade=0, edge=0, alpha=0.35, blur=r * 2.2, glow=True)
    c.paint(c.E(x, y, r * 1.6), (255, 236, 180), shade=0, edge=0, alpha=0.6, blur=r * 0.6, glow=True)
    c.paint(c.E(x, y, r), (255, 248, 222), shade=0, edge=0, blur=4)


def clouds(c, rng, n=5, y0=90, y1=300, alpha=0.75):
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(y0, y1)
        s = rng.uniform(0.6, 1.3)
        m = Canvas.U(*[c.E(x + dx * s, y + dy * s, r * s, r * 0.7 * s) for dx, dy, r in
                       [(-90, 10, 70), (-20, -20, 90), (70, 0, 75), (140, 15, 55), (-150, 20, 45)]])
        c.paint(m, (255, 246, 236), shade=0.35, soft=40, light=(-0.3, -0.95), edge=0.05, alpha=alpha, blur=6)


def ridge(c, y, amp, color, blur=0, seed=1, color2=None, shade=0.0):
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(4)]
    fr = [rng.uniform(0.002, 0.004), rng.uniform(0.005, 0.009), rng.uniform(0.012, 0.02), rng.uniform(0.03, 0.05)]
    am = [amp, amp * 0.5, amp * 0.22, amp * 0.08]
    pts = [(x, y - sum(a * math.sin(f * x + p) for a, f, p in zip(am, fr, ph))) for x in range(-20, W + 40, 16)]
    pts += [(W + 40, H + 20), (-20, H + 20)]
    c.paint(c.P(pts), color, shade=shade, soft=60, edge=0, blur=blur, grad=color2, grad_dir=(0, 1), tex=0.04, tex_scale=8)


def tree(c, x, y, s, rng, palette, blur=0, trunk=(92, 62, 40)):
    c.paint(c.P([(x - 14 * s, y), (x + 14 * s, y), (x + 9 * s, y - 150 * s), (x - 9 * s, y - 150 * s)]), trunk,
            shade=0.4, soft=10 * s, blur=blur, tex=0.2)
    blobs = []
    for _ in range(14):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0, 70 * s)
        blobs.append((x + math.cos(a) * r * 1.1, y - 190 * s + math.sin(a) * r * 0.9, rng.uniform(45, 75) * s))
    for bx, by, br in sorted(blobs, key=lambda b: b[1]):
        col = rng.choice(palette)
        c.paint(c.E(bx, by, br, br * 0.9), col, shade=0.55, soft=br * 0.6, edge=0.2, blur=blur, tex=0.12, tex_scale=4)


AUTUMN = [(214, 92, 34), (230, 140, 40), (196, 60, 34), (236, 182, 56), (176, 120, 40), (150, 140, 60)]


def tree_line(c, y, rng, s=0.6, n=30, blur=2, fade=0.0, haze=(220, 190, 160)):
    pal = [mix(p, haze, fade) for p in AUTUMN]
    xs = sorted(rng.uniform(-60, W + 60) for _ in range(n))
    for x in xs:
        tree(c, x, y + rng.uniform(-10, 14), s * rng.uniform(0.8, 1.2), rng, pal, blur=blur, trunk=mix((92, 62, 40), haze, fade))


def grass_tufts(c, rng, y0, y1, n, cols=((120, 130, 50), (150, 150, 60), (176, 150, 70)), h=(14, 34), w=4):
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(y0, y1)
        s = 0.6 + 0.8 * (y - y0) / max(1, (y1 - y0))
        col = rng.choice(cols)
        for k in range(3):
            dx = rng.uniform(-10, 10) * s
            c.lines(c.L([(x, y), (x + dx, y - rng.uniform(*h) * s)], w * s), shade_col(col, rng.uniform(0.8, 1.15)), 0.9)


def fallen_leaves(c, rng, y0, y1, n, alpha=0.8):
    n = int(n * 0.45)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(y0, y1)
        s = 7 + 12 * (y - y0) / max(1, (y1 - y0))
        col = mix(rng.choice(AUTUMN), (150, 110, 60), 0.25)
        a = rng.uniform(0, 180)
        c.paint(c.RE(x, y, s * 1.3, s * 0.55, a), col, shade=0.4, soft=s, edge=0.1, alpha=alpha)


def wood_plank(c, x0, y0, x1, y1, col, vertical=True, r=4, shade=0.4):
    c.paint(c.R(x0, y0, x1, y1, r), col, shade=shade, soft=10, edge=0.15, tex=0.35, tex_scale=3,
            tex_stretch=(0.15, 6) if vertical else (6, 0.15))


def hay_bale(c, x, y, w, h):
    body = c.R(x - w / 2, y - h / 2, x + w / 2, y + h / 2, h * 0.18)
    c.shadow(body, dx=18, dy=16, blur=18, opacity=0.4)
    c.paint(body, (222, 186, 100), shade=0.6, soft=h * 0.4, edge=0.25, tex=0.45, tex_scale=2.5, tex_stretch=(4, 0.3))
    for f in (0.3, 0.7):
        c.lines(c.R(x - w / 2 + w * f - 5, y - h / 2, x - w / 2 + w * f + 5, y + h / 2), (150, 110, 50), 0.7)
    rng = random.Random(int(x * 7 + y))
    for _ in range(int(w / 6)):
        px = rng.uniform(x - w / 2, x + w / 2)
        c.lines(c.L([(px, y - h / 2 + 4), (px + rng.uniform(-14, 14), y - h / 2 - rng.uniform(4, 18))], 3), (226, 196, 120), 0.8)


def fence(c, x0, x1, y, h=120, gap=150, col=(150, 106, 66)):
    for x in range(int(x0), int(x1) + 1, gap):
        wood_plank(c, x - 12, y - h, x + 12, y + 12, shade_col(col, 0.9))
        c.paint(c.P([(x - 12, y - h), (x, y - h - 18), (x + 12, y - h)]), shade_col(col, 0.9), shade=0.3, soft=6)
    for yy in (y - h * 0.75, y - h * 0.3):
        wood_plank(c, x0 - 20, yy - 10, x1 + 20, yy + 10, col, vertical=False)


def bulbs(c, pts, rng):
    for i, (x, y) in enumerate(pts):
        col = [(255, 220, 140), (255, 190, 110), (255, 236, 180)][i % 3]
        c.paint(c.E(x, y, 34), col, shade=0, edge=0, alpha=0.45, blur=16, glow=True)
        c.paint(c.E(x, y, 9, 11), (255, 246, 210), shade=0.3, soft=4)


def catenary(x0, y0, x1, y1, sag, n=40):
    return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n + sag * 4 * (i / n) * (1 - i / n)) for i in range(n + 1)]


def scarecrow(c, x, y):
    # a friendly, smiling scarecrow (drawn at ~70% scale around its base)
    wood_plank(c, x - 10, y - 420, x + 10, y + 60, (130, 92, 56))
    wood_plank(c, x - 190, y - 330, x + 190, y - 312, (130, 92, 56), vertical=False)
    shirt = c.U(c.P([(x - 110, y - 340), (x + 110, y - 340), (x + 95, y - 120), (x - 95, y - 120)]),
                c.R(x - 200, y - 345, x + 200, y - 290, 20))
    c.shadow(shirt)
    c.paint(shirt, (196, 60, 48), shade=0.6, soft=40, edge=0.2, tex=0.12)
    for k in range(-4, 5):  # plaid
        c.lines(c.I(c.R(x + k * 45 - 6, y - 345, x + k * 45 + 6, y - 120), shirt), (150, 40, 34), 0.6)
    for yy in (y - 300, y - 230, y - 160):
        c.lines(c.I(c.R(x - 210, yy - 6, x + 210, yy + 6), shirt), (240, 200, 90), 0.6)
    pants = c.U(c.P([(x - 90, y - 130), (x + 90, y - 130), (x + 85, y - 20), (x + 10, y - 20), (x, y - 80),
                     (x - 10, y - 20), (x - 85, y - 20)]))
    c.paint(pants, (70, 100, 150), shade=0.6, soft=30, edge=0.2, tex=0.15)
    c.paint(c.R(x - 40, y - 115, x + 40, y - 80, 8), (196, 140, 60), shade=0.4, soft=8)
    for sx in (-1, 1):
        for k in range(5):
            c.lines(c.L([(x + sx * 200, y - 320 + k * 6), (x + sx * (230 + k * 6), y - 300 + k * 10)], 6), (226, 190, 100), 0.9)
    head = c.E(x, y - 410, 78, 84)
    c.paint(head, (214, 184, 132), shade=0.6, soft=40, edge=0.2, tex=0.35, tex_scale=2)
    for ex in (-28, 28):
        c.paint(c.E(x + ex, y - 425, 11), (60, 40, 30), shade=0.3, soft=4)
    c.paint(c.ARC(x, y - 405, 34, 24, 20, 160, 7), (120, 60, 40), shade=0, edge=0)
    for cx in (-46, 46):
        c.paint(c.E(x + cx, y - 395, 16, 11), (236, 130, 110), shade=0, edge=0, alpha=0.5, blur=4)
    c.paste(spr("straw_hat", 384), x, y - 485, 230)


def mums(c, x, y, s, col, rng):
    pot = c.P([(x - 60 * s, y), (x + 60 * s, y), (x + 45 * s, y + 80 * s), (x - 45 * s, y + 80 * s)])
    c.paint(pot, (170, 92, 56), shade=0.6, soft=20 * s, edge=0.2, tex=0.1)
    c.paint(c.E(x, y - 30 * s, 80 * s, 50 * s), (70, 100, 40), shade=0.5, soft=20 * s)
    for _ in range(40):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0, 70 * s)
        c.paint(c.E(x + math.cos(a) * r, y - 40 * s + math.sin(a) * r * 0.55, 10 * s), shade_col(col, rng.uniform(0.85, 1.15)),
                shade=0.5, soft=6 * s, edge=0.2)


def awning_stall(c, x, y, w, col1, col2, rng, goods):
    h = 330
    for px in (x - w / 2 + 14, x + w / 2 - 14):
        wood_plank(c, px - 12, y - h, px + 12, y + 30, (140, 98, 60))
    back = c.R(x - w / 2 + 20, y - h + 40, x + w / 2 - 20, y - 60, 6)
    c.paint(back, (226, 206, 170), shade=0.2, soft=40, edge=0.2, tex=0.1)
    stripes = int(w / 60)
    for i in range(stripes):
        sx0 = x - w / 2 - 20 + i * (w + 40) / stripes
        sx1 = sx0 + (w + 40) / stripes
        pts = [(sx0 + 20, y - h - 70), (sx1 + 20, y - h - 70), (sx1, y - h + 30), (sx0, y - h + 30)]
        c.paint(c.P(pts), col1 if i % 2 == 0 else col2, shade=0.3, soft=20, edge=0.1, tex=0.06)
        c.paint(c.E((sx0 + sx1) / 2, y - h + 30, (sx1 - sx0) / 2, 26), col1 if i % 2 == 0 else col2, shade=0.4, soft=14)
    table = c.R(x - w / 2 + 10, y - 70, x + w / 2 - 10, y + 40, 8)
    c.shadow(table, dx=10, dy=18, blur=16, opacity=0.35)
    c.paint(table, (236, 226, 204), shade=0.4, soft=20, edge=0.2, tex=0.06)
    c.paint(c.R(x - w / 2 + 10, y - 70, x + w / 2 - 10, y - 50, 4), (196, 60, 48), shade=0.3, soft=6)
    n = len(goods)
    for i, g in enumerate(goods):
        gx = x - w / 2 + 60 + i * (w - 120) / max(1, n - 1)
        c.paste(spr(g, 256), gx, y - 105, 86 + rng.uniform(-8, 8))


# ------------------------------------------------------------------ scenes
def pumpkin_patch():
    c = new_canvas()
    rng = random.Random(11)
    sky(c, (126, 178, 222), (255, 210, 150))
    sun(c, 1500, 250, 80)
    clouds(c, rng, 6)
    ridge(c, 520, 70, (176, 150, 140), blur=6, seed=3, color2=(200, 170, 140))
    ridge(c, 560, 50, (170, 140, 90), blur=3, seed=5, color2=(150, 126, 70))
    tree_line(c, 585, rng, s=0.55, n=34, blur=1.5, fade=0.35)
    # little red barn in the distance
    barn = c.P([(1180, 600), (1180, 500), (1250, 450), (1320, 500), (1320, 600)])
    c.paint(barn, (176, 54, 40), shade=0.4, soft=20, blur=1)
    c.paint(c.P([(1170, 505), (1250, 440), (1330, 505), (1320, 512), (1250, 456), (1180, 512)]), (236, 226, 204), shade=0.2, soft=6, blur=1)
    c.paint(c.R(1232, 540, 1268, 600, 2), (236, 226, 204), shade=0.2, soft=6, blur=1)
    # field
    field = c.R(-10, 590, W + 10, H + 10)
    c.paint(field, (164, 138, 70), shade=0, edge=0, grad=(120, 90, 46), grad_dir=(0, 1), tex=0.15, tex_scale=10)
    for i in range(-14, 15):  # furrows converging to the horizon
        x_far = 960 + i * 40
        x_near = 960 + i * 260
        c.lines(c.L([(x_far, 600), (x_near, H + 40)], 10), (110, 84, 44), 0.35)
        c.lines(c.L([(x_far + 14, 600), (x_near + 90, H + 40)], 26), (136, 150, 56), 0.35)
    grass_tufts(c, rng, 600, 1080, 500)
    fallen_leaves(c, rng, 620, 1080, 140)
    fence(c, 40, 760, 700, h=110)
    for (x, y, w) in [(170, 760, 300), (420, 770, 260), (290, 680, 240)]:
        hay_bale(c, x, y, w, w * 0.48)
    sc = Canvas(520, 640, ss=2, units=None)
    scarecrow(sc, 260, 620)
    c.paste(sc.image(), 1600, 560, 380)
    # pumpkins in the patch (decor - not on the find list here)
    for x, y, w in [(700, 650, 90), (900, 640, 70), (1120, 660, 100), (1290, 640, 70), (620, 760, 150), (1050, 780, 170),
                    (1350, 900, 220), (860, 900, 200), (240, 950, 210), (1720, 900, 230), (1830, 700, 100), (480, 640, 70)]:
        c.paste(spr("pumpkin", 384), x, y, w, rot=rng.uniform(-8, 8), flip=rng.random() < 0.5)
    c.vignette()
    return c.image()


def harvest_barn():
    c = new_canvas()
    rng = random.Random(22)
    c.fill((120, 60, 36), grad=(74, 36, 22), grad_dir=(0, -1))
    for i in range(0, W, 96):  # vertical wall planks
        col = shade_col((140, 74, 44), rng.uniform(0.85, 1.1))
        wood_plank(c, i + 3, 0, i + 93, 760, col, shade=0.25)
    # open double door with sunny view
    view = c.R(1180, 220, 1620, 760)
    c.paint(view, (140, 196, 236), shade=0, edge=0, grad=(255, 220, 160), grad_dir=(0, 1))
    c.paint(c.P([(1180, 600), (1300, 540), (1450, 570), (1620, 520), (1620, 760), (1180, 760)]), (170, 150, 80),
            shade=0, edge=0, blur=2)
    for k in range(8):
        tree(c, 1200 + k * 60, 590, 0.32, rng, AUTUMN, blur=1.5)
    c.paint(c.R(1180, 640, 1620, 760), (190, 160, 90), shade=0, edge=0, tex=0.2, blur=1)
    for x0 in (1110, 1620):  # open door panels
        wood_plank(c, x0, 210, x0 + 70, 770, (150, 82, 50))
        c.lines(c.L([(x0 + 10, 230), (x0 + 60, 750)], 12), (236, 220, 200), 0.8)
        c.lines(c.L([(x0 + 60, 230), (x0 + 10, 750)], 12), (236, 220, 200), 0.8)
    wood_plank(c, 1100, 190, 1700, 230, (110, 60, 36), vertical=False)
    # sunbeam
    c.paint(c.P([(1180, 230), (1620, 230), (1500, 1080), (420, 1080)]), (255, 214, 140), shade=0, edge=0, alpha=0.18,
            blur=40, glow=True)
    # loft and beams
    wood_plank(c, -10, 150, W + 10, 200, (96, 52, 30), vertical=False)
    for x in (300, 900, 1840):
        wood_plank(c, x - 26, 150, x + 26, 820, (104, 58, 34))
    wood_plank(c, -10, 330, 760, 360, (96, 52, 30), vertical=False)
    hay = c.U(*[c.E(60 + i * 75, 320 - rng.uniform(0, 50), 80, 60) for i in range(10)])
    c.paint(hay, (226, 188, 100), shade=0.5, soft=40, edge=0.2, tex=0.5, tex_scale=2, tex_stretch=(3, 0.4))
    # window with light
    win = c.R(500, 420, 720, 620, 8)
    c.paint(win, (250, 226, 180), shade=0, edge=0, grad=(190, 220, 236), grad_dir=(0, -1))
    wood_plank(c, 600, 420, 620, 620, (110, 60, 36))
    wood_plank(c, 500, 510, 720, 530, (110, 60, 36), vertical=False)
    c.paint(c.R(480, 400, 740, 640, 10), (255, 220, 160), shade=0, edge=0, alpha=0.18, blur=40, glow=True)
    # floor
    floor = c.P([(-10, 760), (W + 10, 760), (W + 10, H + 10), (-10, H + 10)])
    c.paint(floor, (150, 104, 60), shade=0, edge=0, grad=(110, 74, 42), grad_dir=(0, 1), tex=0.3, tex_scale=3, tex_stretch=(6, 0.2))
    for i in range(-10, 11):
        c.lines(c.L([(960 + i * 70, 760), (960 + i * 260, H + 20)], 4), (90, 60, 34), 0.5)
    for _ in range(420):  # loose straw
        x, y = rng.uniform(0, W), rng.uniform(770, 1080)
        a = rng.uniform(0, 3.14)
        ln = rng.uniform(14, 34)
        c.lines(c.L([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln * 0.4)], 3), (226, 196, 120), 0.8)
    for (x, y, w) in [(180, 820, 300), (470, 840, 280), (320, 730, 260), (160, 650, 240)]:
        hay_bale(c, x, y, w, w * 0.48)
    # barrels
    for x in (1760, 1860):
        b = c.R(x - 60, 640, x + 60, 840, 40)
        c.shadow(b)
        c.paint(b, (150, 92, 50), shade=0.7, soft=40, edge=0.25, tex=0.3, tex_stretch=(0.2, 4))
        for yy in (670, 800):
            c.paint(c.R(x - 62, yy - 8, x + 62, yy + 8, 4), (90, 90, 96), shade=0.5, soft=6, spec=0.4)
    # pumpkins & corn bundles as decor
    for x, y, w, n in [(760, 820, 140, "pumpkin"), (1000, 860, 110, "pumpkin"), (880, 760, 90, "gourd"),
                       (1300, 900, 120, "pumpkin")]:
        c.paste(spr(n, 384), x, y, w)
    for x in (1050, 1700):
        for k in range(5):
            c.paste(spr("corn", 320), x + k * 22 - 44, 680, 110, rot=(k - 2) * 7)
    c.vignette(0.32)
    return c.image()


def autumn_bakery():
    c = new_canvas()
    rng = random.Random(33)
    c.fill((248, 230, 200), grad=(236, 206, 170), grad_dir=(0, 1))
    for x in range(0, W, 64):  # wallpaper stripes with tiny leaves
        c.paint(c.R(x, 0, x + 26, 640), (244, 214, 176), shade=0, edge=0, alpha=0.6)
    for y in range(60, 640, 120):
        for x in range(32, W, 128):
            c.paint(c.RE(x + (y // 120 % 2) * 64, y, 9, 5, 30), (220, 150, 100), shade=0, edge=0, alpha=0.5)
    # window with autumn tree outside
    view = c.R(720, 120, 1200, 520)
    c.paint(view, (150, 200, 236), shade=0, edge=0, grad=(250, 220, 170), grad_dir=(0, 1))
    tree(c, 900, 600, 1.2, rng, AUTUMN, blur=2)
    tree(c, 1120, 620, 0.9, rng, AUTUMN, blur=2.5)
    frame = c.S(c.R(700, 100, 1220, 540, 8), c.R(728, 128, 1192, 512))
    c.paint(frame, (250, 246, 236), shade=0.5, soft=16, edge=0.2)
    c.paint(c.U(c.R(950, 120, 970, 520), c.R(720, 310, 1200, 330)), (250, 246, 236), shade=0.4, soft=10)
    for side in (-1, 1):  # gingham curtains
        cx = 960 + side * 300
        cur = c.P([(cx - 90, 80), (cx + 90, 80), (cx + 60 * side + 40, 560), (cx + 60 * side - 80, 560)])
        c.paint(cur, (214, 80, 64), shade=0.4, soft=40, edge=0.15, tex=0.08)
        for k in range(8):
            c.lines(c.I(c.R(cx - 120 + k * 32, 80, cx - 108 + k * 32, 560), cur), (250, 236, 220), 0.5)
        for yy in range(100, 560, 34):
            c.lines(c.I(c.R(cx - 140, yy, cx + 140, yy + 12), cur), (250, 236, 220), 0.45)
    wood_plank(c, 640, 70, 1280, 92, (150, 100, 60), vertical=False)
    # shelves with jars and plates
    for sx, sy in [(90, 300), (90, 480), (1400, 300), (1400, 480)]:
        wood_plank(c, sx, sy, sx + 430, sy + 24, (160, 106, 62), vertical=False)
        c.shadow(c.R(sx, sy + 24, sx + 430, sy + 30), dx=0, dy=8, blur=8, opacity=0.3)
    for i, (x, y) in enumerate([(150, 300), (240, 300), (330, 300), (440, 300)]):
        jar = c.R(x - 36, y - 110, x + 36, y, 14)
        c.paint(jar, [(226, 150, 60), (190, 60, 50), (236, 200, 120), (120, 150, 70)][i % 4], shade=0.6, soft=20, spec=0.5)
        c.paint(c.R(x - 40, y - 126, x + 40, y - 104, 6), (200, 180, 150), shade=0.5, soft=6)
    for x in (180, 320, 1500, 1640, 1780):
        p = c.E(x, 420, 62)
        c.paint(p, (246, 242, 232), shade=0.6, soft=20, edge=0.2, spec=0.3)
        c.paint(c.E(x, 420, 44), (226, 220, 206), shade=0.2, soft=10, alpha=0.6)
    # hanging copper pots
    wood_plank(c, 1310, 60, 1900, 80, (110, 80, 60), vertical=False)
    for x in (1420, 1560, 1720, 1840):
        c.lines(c.L([(x, 80), (x, 140)], 5), (80, 70, 60))
        pot = c.U(c.E(x, 190, 62, 58), c.R(x - 8, 130, x + 8, 160))
        c.paint(pot, (196, 110, 70), shade=0.8, soft=30, spec=0.7, edge=0.3)
    # stove on the left
    stove = c.R(60, 560, 470, 1000, 24)
    c.shadow(stove)
    c.paint(stove, (244, 236, 214), shade=0.5, soft=40, edge=0.2, spec=0.3)
    c.paint(c.R(110, 700, 420, 940, 16), (200, 190, 170), shade=0.4, soft=20, light=(0.4, 0.8))
    c.paint(c.R(130, 720, 400, 920, 12), (90, 70, 60), shade=0.3, soft=20, alpha=0.7)
    c.paint(c.R(170, 760, 360, 880, 10), (255, 150, 70), shade=0, edge=0, alpha=0.35, blur=20, glow=True)
    for x in (130, 220, 310, 400):
        c.paint(c.E(x, 620, 26), (120, 110, 100), shade=0.6, soft=8, spec=0.4)
    # counter
    c.paint(c.R(480, 640, W + 10, 700), (196, 140, 86), shade=0.4, soft=16, edge=0.15, tex=0.3, tex_stretch=(6, 0.2))
    c.shadow(c.R(480, 700, W + 10, 712), dx=0, dy=10, blur=10, opacity=0.35)
    for x in range(480, W, 240):
        door = c.R(x + 8, 712, x + 232, 1070, 10)
        c.paint(door, (176, 104, 60), shade=0.4, soft=20, edge=0.2, tex=0.25, tex_stretch=(0.2, 4))
        c.paint(c.R(x + 30, 740, x + 210, 1040, 8), (196, 124, 74), shade=0.4, soft=14, light=(0.5, 0.8), tex=0.2)
        c.paint(c.E(x + 120, 760, 12), (210, 170, 90), shade=0.6, soft=6, spec=0.5)
    # decor on counter (not on the find list here)
    for x, n, w in [(560, "pumpkin", 120), (760, "basket", 150), (1350, "apple", 80), (1420, "apple", 70),
                    (1660, "honey_jar", 90), (1780, "pumpkin", 100)]:
        c.paste(spr(n, 320), x, 640 - w * 0.42, w)
    # checkered floor strip under the stove
    for i in range(0, 480, 60):
        c.paint(c.R(i, 1000, i + 60, 1080), (196, 60, 48) if (i // 60) % 2 else (246, 236, 216), shade=0, edge=0)
    c.vignette(0.25)
    return c.image()


def corn_maze():
    c = new_canvas()
    rng = random.Random(44)
    sky(c, (120, 176, 226), (255, 222, 170))
    sun(c, 380, 200, 70)
    clouds(c, rng, 5, alpha=0.7)
    ridge(c, 470, 60, (170, 150, 140), blur=6, seed=8, color2=(196, 170, 140))
    # path
    path = c.P([(860, 470), (1060, 470), (1500, H + 10), (420, H + 10)])
    c.paint(c.R(-10, 470, W + 10, H + 10), (176, 150, 80), shade=0, edge=0, grad=(150, 120, 60), grad_dir=(0, 1), tex=0.2)
    c.paint(path, (206, 172, 120), shade=0, edge=0, grad=(186, 150, 100), grad_dir=(0, 1), tex=0.25, tex_scale=6)

    def corn_wall(x_far, x_near, side):
        # rows of stalks, far ones small and hazy
        for layer in range(14):
            t = layer / 13
            y = 470 + (H + 80 - 470) * t
            xb = x_far + (x_near - x_far) * t
            hgt = 120 + 640 * t
            for k in range(int(3 + 4 * t)):
                x = xb + side * (k * (30 + 60 * t)) + rng.uniform(-10, 10)
                haze = 0.4 * (1 - t)
                stalk_col = mix((150, 150, 60), (200, 186, 150), haze)
                c.lines(c.L([(x, y), (x + rng.uniform(-10, 10), y - hgt)], 6 + 12 * t), stalk_col, 1.0)
                for j in range(4):
                    ly = y - hgt * (0.25 + 0.18 * j)
                    d = rng.choice((-1, 1))
                    leaf_col = mix(rng.choice([(190, 170, 70), (160, 156, 60), (210, 180, 90), (176, 140, 60)]), (210, 196, 160), haze)
                    c.paint(c.TAPER((x, ly), (x + d * 70 * (0.4 + t), ly - 50 * (0.4 + t)), (x + d * 130 * (0.4 + t), ly + 40 * t),
                                    14 + 30 * t), leaf_col, shade=0.45, soft=6 + 10 * t, edge=0.1, tex=0.1, tex_stretch=(3, 0.3))
                c.lines(c.L([(x, y - hgt), (x + 6, y - hgt - 30 * (0.4 + t))], 4 + 6 * t), mix((226, 196, 110), (210, 196, 160), haze))

    corn_wall(820, 380, -1)
    corn_wall(1100, 1540, 1)
    grass_tufts(c, rng, 520, 1080, 220, cols=((150, 140, 60), (176, 150, 70)))
    fallen_leaves(c, rng, 560, 1080, 110)
    # signpost (arrow) and garden beds
    wood_plank(c, 1500, 520, 1524, 900, (140, 98, 60))
    sign = c.P([(1400, 540), (1640, 540), (1690, 590), (1640, 640), (1400, 640)])
    c.shadow(sign)
    wood_plank(c, 1400, 540, 1640, 640, (186, 140, 90), vertical=False)
    c.paint(c.P([(1640, 540), (1690, 590), (1640, 640)]), (186, 140, 90), shade=0.4, soft=10, tex=0.3)
    c.paint(c.P([(1450, 575), (1580, 575), (1580, 555), (1625, 590), (1580, 625), (1580, 605), (1450, 605)]),
            (196, 60, 48), shade=0.4, soft=8)
    hay_bale(c, 300, 900, 320, 150)
    hay_bale(c, 1680, 960, 300, 140)
    for x, y, s, col in [(560, 980, 1.2, (236, 140, 40)), (1350, 980, 1.2, (150, 70, 150)), (180, 760, 0.9, (240, 196, 60)),
                         (1760, 780, 0.9, (196, 60, 48))]:
        mums(c, x, y, s, col, rng)
    for x, y, w in [(700, 640, 70), (1240, 660, 80)]:
        c.paste(spr("gourd", 320), x, y, w)
    c.vignette()
    return c.image()


def fall_fair():
    c = new_canvas()
    rng = random.Random(55)
    sky(c, (110, 160, 220), (255, 200, 150))
    sun(c, 1650, 300, 70)
    clouds(c, rng, 5, alpha=0.65)
    # ferris wheel
    cx, cy, r = 520, 380, 260
    c.paint(c.P([(cx - 160, 700), (cx, cy), (cx + 160, 700)]), (236, 230, 220), shade=0, edge=0, alpha=0.0)
    for side in (-1, 1):
        c.lines(c.L([(cx, cy), (cx + side * 170, 690)], 14), (220, 210, 196), 0.9)
    rim = c.S(c.E(cx, cy, r), c.E(cx, cy, r - 14))
    c.paint(rim, (226, 216, 200), shade=0.3, soft=10, blur=1)
    for i in range(12):
        a = i * math.pi / 6
        c.lines(c.L([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a))], 5), (220, 210, 196), 0.9)
        gx, gy = cx + r * math.cos(a), cy + r * math.sin(a)
        c.paint(c.R(gx - 24, gy, gx + 24, gy + 40, 10), [(196, 60, 48), (240, 176, 60), (70, 130, 170)][i % 3], shade=0.4, soft=10, blur=1)
    c.paint(c.E(cx, cy, 26), (196, 60, 48), shade=0.6, soft=10)
    ridge(c, 640, 30, (150, 150, 90), blur=3, seed=12, color2=(130, 140, 70))
    tree_line(c, 650, rng, s=0.45, n=24, blur=1.5, fade=0.3)
    ground = c.R(-10, 660, W + 10, H + 10)
    c.paint(ground, (140, 150, 70), shade=0, edge=0, grad=(110, 120, 56), grad_dir=(0, 1), tex=0.2, tex_scale=6)
    # bunting & string lights
    for (x0, y0, x1, y1, sag) in [(-20, 120, 900, 160, 90), (900, 160, 1940, 110, 90)]:
        pts = catenary(x0, y0, x1, y1, sag, 24)
        c.lines(c.L(pts, 4), (110, 90, 70))
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            col = [(196, 60, 48), (240, 176, 60), (236, 124, 32), (120, 150, 70)][i % 4]
            c.paint(c.P([(ax + 4, ay), (bx - 4, by), ((ax + bx) / 2, (ay + by) / 2 + 52)]), col, shade=0.3, soft=8)
    grass_tufts(c, rng, 680, 1080, 300)
    fallen_leaves(c, rng, 700, 1080, 90)
    lp = catenary(-20, 240, 1940, 230, 120, 40)
    c.lines(c.L(lp, 3), (80, 70, 60))
    bulbs(c, lp[1:-1], rng)
    # stalls (goods are decor, not on this scene's find list)
    awning_stall(c, 1180, 720, 420, (196, 60, 48), (246, 236, 216), rng, ["pumpkin", "corn", "pumpkin", "corn"])
    awning_stall(c, 1660, 740, 440, (236, 124, 32), (246, 236, 216), rng, ["pie", "cupcake", "cookie", "pie"])
    awning_stall(c, 260, 760, 460, (90, 140, 120), (246, 236, 216), rng, ["sunflower", "maple_leaf", "sunflower", "basket"])
    # crates and hay
    for x, y in [(700, 900), (820, 940), (760, 820)]:
        cr = c.R(x - 70, y - 60, x + 70, y + 60, 6)
        c.shadow(cr)
        wood_plank(c, x - 70, y - 60, x + 70, y + 60, (176, 126, 76), vertical=False)
        for yy in (y - 25, y + 20):
            c.lines(c.R(x - 70, yy - 3, x + 70, yy + 3), (120, 80, 46), 0.8)
    hay_bale(c, 1000, 960, 300, 140)
    for x, y, w in [(700, 830, 90), (820, 870, 80), (1500, 980, 150), (420, 1000, 160)]:
        c.paste(spr("pumpkin", 320), x, y, w)
    c.vignette()
    return c.image()


SCENES = {
    "pumpkin_patch": pumpkin_patch,
    "harvest_barn": harvest_barn,
    "autumn_bakery": autumn_bakery,
    "corn_maze": corn_maze,
    "fall_fair": fall_fair,
}
