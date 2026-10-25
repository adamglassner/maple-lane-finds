"""Hand-coded painterly object sprites for Maple Lane Finds (all original artwork).
Each function paints one object into a Canvas using a 0..1000 unit space."""
import math
from artkit import Canvas, mix, shade_col

BROWN = (112, 74, 40)
DARKBROWN = (70, 42, 22)
LEAF_GREEN = (88, 128, 46)


def _stem(c, pts, w=60, color=BROWN):
    m = c.L(pts, w)
    c.paint(m, color, shade=0.5, soft=14, tex=0.25, tex_scale=6, tex_stretch=(0.3, 3))
    return m


def _leaf(c, cx, cy, length, width, ang, color=LEAF_GREEN, vein=True):
    m = c.RE(cx, cy, length, width, ang)
    c.paint(m, color, shade=0.55, soft=30, spec=0.15, tex=0.08)
    if vein:
        a = math.radians(ang)
        c.lines(c.L([(cx - length * 0.85 * math.cos(a), cy - length * 0.85 * math.sin(a)),
                     (cx + length * 0.85 * math.cos(a), cy + length * 0.85 * math.sin(a))], 9),
                shade_col(color, 0.7), alpha=0.6)
    return m


# ------------------------------------------------------------------ produce
def pumpkin(c, base=(230, 118, 30), cx=500, cy=580, s=1.0, stem=True):
    E = lambda dx, dy, rx, ry: c.E(cx + dx * s, cy + dy * s, rx * s, ry * s)
    body = c.U(E(-250, 0, 220, 290), E(250, 0, 220, 290), E(-125, 5, 235, 315), E(125, 5, 235, 315), E(0, 10, 215, 320))
    c.shadow(body)
    for dx, rx, ry, f in [(-250, 220, 290, 0.86), (250, 220, 290, 0.86), (-125, 235, 315, 0.95), (125, 235, 315, 0.95)]:
        c.paint(E(dx, 0 if abs(dx) > 200 else 5, rx, ry), shade_col(base, f), shade=0.7, soft=70, edge=0.35, tex=0.06)
    c.paint(E(0, 10, 215, 320), shade_col(base, 1.05), shade=0.7, soft=70, edge=0.35, spec=0.35, tex=0.06)
    if stem:
        _stem(c, [(cx - 5 * s, cy - 270 * s), (cx + 15 * s, cy - 360 * s), (cx + 80 * s, cy - 410 * s)], 70 * s, (104, 92, 46))
        c.paint(c.RE(cx - 120 * s, cy - 330 * s, 95 * s, 45 * s, -25), LEAF_GREEN, shade=0.5, soft=25)
    return body


def jackolantern(c):
    pumpkin(c, (236, 126, 34))
    glow = (255, 196, 70)
    # happy closed eyes (upturned crescents) and a big friendly smile
    for ex in (380, 620):
        eye = c.S(c.E(ex, 480, 75, 60), c.E(ex, 520, 80, 55))
        c.paint(eye, glow, shade=0.6, soft=20, light=(0, 0.9), edge=0.1)
    smile = c.S(c.E(500, 590, 230, 170), c.E(500, 540, 250, 150))
    c.paint(smile, glow, shade=0.6, soft=20, light=(0, 0.9), edge=0.1)
    c.paint(c.E(500, 640, 26, 28), (255, 230, 150), shade=0, edge=0, alpha=0.0)
    for cx in (330, 670):  # rosy cheeks
        c.paint(c.E(cx, 600, 55, 40), (255, 150, 90), shade=0, edge=0, alpha=0.35, blur=18)


def apple(c, base=(196, 32, 30), cx=500, cy=560):
    body = c.U(c.E(cx - 110, cy, 230, 270), c.E(cx + 110, cy, 230, 270), c.E(cx, cy + 70, 250, 240))
    c.shadow(body)
    c.paint(body, base, shade=0.8, soft=90, spec=0.55, edge=0.3, tex=0.05)
    c.paint(c.E(cx + 120, cy + 80, 130, 120), (240, 170, 60), shade=0, edge=0, alpha=0.25, blur=60)
    c.paint(c.E(cx, cy - 245, 50, 25), (110, 30, 25), shade=0, edge=0, alpha=0.6, blur=10)
    _stem(c, [(cx, cy - 240), (cx + 10, cy - 330), (cx + 35, cy - 390)], 34)
    _leaf(c, cx + 140, cy - 320, 120, 50, -20)


def pear(c):
    body = c.U(c.E(500, 380, 150, 170), c.E(500, 640, 260, 250), c.P([(360, 400), (640, 400), (740, 600), (260, 600)]))
    c.shadow(body)
    c.paint(body, (196, 196, 60), shade=0.8, soft=90, spec=0.4, edge=0.3, tex=0.06, grad=(170, 190, 50), grad_dir=(0.7, 0.7))
    c.paint(c.E(570, 680, 120, 110), (230, 120, 60), shade=0, edge=0, alpha=0.3, blur=60)
    _stem(c, [(500, 225), (515, 150), (550, 100)], 34)
    _leaf(c, 610, 170, 100, 40, -30)


def caramel_apple(c):
    apple(c, (170, 28, 26), cy=600)
    car = c.U(c.E(500, 470, 270, 150), c.E(330, 560, 60, 90), c.E(470, 590, 60, 90), c.E(640, 570, 55, 85))
    c.paint(car, (196, 120, 48), shade=0.8, soft=40, spec=0.6, edge=0.25)
    for i, (x, y) in enumerate([(380, 440), (450, 480), (560, 450), (620, 500), (510, 420), (420, 520), (600, 420)]):
        c.paint(c.E(x, y, 16, 12), [(250, 240, 220), (220, 60, 40), (250, 200, 60)][i % 3], shade=0.4, soft=6)
    stick = c.R(470, 70, 530, 420, 20)
    c.paint(stick, (226, 196, 150), shade=0.5, soft=20, tex=0.2, tex_stretch=(0.3, 3))


def gourd(c):
    body = c.U(c.E(500, 330, 140, 170), c.E(500, 640, 250, 250), c.P([(380, 360), (620, 360), (700, 560), (300, 560)]))
    c.shadow(body)
    c.paint(body, (226, 196, 60), shade=0.8, soft=90, spec=0.35, edge=0.3, tex=0.06)
    for x in (400, 500, 600):  # green stripes
        c.paint(c.CURVE((x, 200), (x + (x - 500) * 0.7, 560), (x + (x - 500) * 0.2, 860), 34),
                (96, 140, 50), shade=0.3, soft=15, alpha=0.75)
    _stem(c, [(500, 170), (490, 100), (520, 60)], 46, (120, 104, 54))


def acorn(c):
    nut = c.E(500, 600, 220, 270)
    c.shadow(nut)
    c.paint(nut, (186, 128, 62), shade=0.8, soft=80, spec=0.5, edge=0.3, tex=0.05)
    c.paint(c.E(500, 845, 30, 22), (110, 70, 34), shade=0, edge=0)
    cap = c.U(c.E(500, 400, 260, 150))
    c.paint(cap, (120, 82, 44), shade=0.7, soft=50, edge=0.3, tex=0.35, tex_scale=10)
    for i in range(-3, 4):  # crosshatch
        c.lines(c.I(c.L([(500 + i * 70 - 100, 300), (500 + i * 70 + 100, 500)], 8), cap), (80, 52, 26), 0.5)
        c.lines(c.I(c.L([(500 + i * 70 + 100, 300), (500 + i * 70 - 100, 500)], 8), cap), (80, 52, 26), 0.5)
    _stem(c, [(500, 260), (510, 200), (540, 170)], 40, (92, 60, 30))


def maple_leaf(c, base=(214, 64, 30), tip=(244, 170, 40)):
    pts = []
    spikes = [(0, 430), (22, 250), (40, 380), (62, 230), (88, 400), (115, 170), (135, 260), (160, 140), (180, 330),
              (200, 140), (225, 260), (245, 170), (272, 400), (298, 230), (320, 380), (338, 250), (360, 430)]
    # build a symmetric maple outline around the center
    outline = [(500, 120), (560, 300), (640, 250), (620, 400), (780, 300), (760, 380), (880, 400), (800, 520),
               (850, 560), (650, 660), (680, 740), (530, 700), (520, 900), (480, 900), (470, 700), (320, 740),
               (350, 660), (150, 560), (200, 520), (120, 400), (240, 380), (220, 300), (380, 400), (360, 250), (440, 300)]
    m = c.P(outline)
    c.shadow(m)
    c.paint(m, base, shade=0.6, soft=40, spec=0.2, edge=0.25, tex=0.1, grad=tip, grad_dir=(0, -1))
    for end in [(500, 160), (790, 330), (840, 530), (210, 330), (160, 530)]:
        c.lines(c.L([(500, 680), end], 10), shade_col(base, 0.72), 0.55)
    c.lines(c.L([(500, 680), (500, 890)], 16), (120, 50, 24), 0.9)


def oak_leaf(c):
    m = c.U(c.RE(500, 500, 150, 360, 0), *[c.E(500 + side * 140, y, 95, 75) for side in (-1, 1) for y in (260, 420, 580)],
            c.E(500, 170, 80, 80))
    m = c.S(m, c.E(500, 900, 60, 60))
    c.shadow(m)
    c.paint(m, (224, 170, 46), shade=0.6, soft=40, spec=0.2, edge=0.25, tex=0.1, grad=(196, 110, 34), grad_dir=(0, 1))
    c.lines(c.L([(500, 160), (500, 900)], 14), (150, 96, 30), 0.8)
    for y in (280, 440, 600):
        for side in (-1, 1):
            c.lines(c.L([(500, y + 40), (500 + side * 170, y)], 8), (160, 104, 32), 0.5)


def corn(c):
    for ang, col, off in [(-14, (196, 174, 104), -60), (14, (186, 166, 98), 60)]:
        husk = c.RE(500 + off, 600, 140, 360, ang)
        c.paint(husk, col, shade=0.5, soft=40, tex=0.25, tex_stretch=(0.2, 3), tex_scale=6)
    cob = c.RE(500, 470, 140, 330, 0)
    c.paint(cob, (240, 196, 60), shade=0.75, soft=60, spec=0.25, edge=0.3)
    for row in range(-3, 4):
        for k in range(14):
            y = 180 + k * 42
            half = 125 * math.sqrt(max(0, 1 - ((y - 470) / 330) ** 2))
            x = 500 + row * 34
            if abs(x - 500) < half - 10:
                c.paint(c.E(x, y, 15, 19), (250, 214, 84), shade=0.6, soft=6, spec=0.4, edge=0.4)
    for ang, off in [(-6, -40), (8, 50)]:
        c.paint(c.RE(500 + off, 760, 70, 230, ang), (176, 160, 92), shade=0.5, soft=30, tex=0.2, tex_stretch=(0.2, 3))


def sunflower(c):
    _stem(c, [(500, 600), (520, 800), (500, 960)], 46, (92, 130, 50))
    _leaf(c, 620, 820, 110, 45, -30)
    petals = []
    for i in range(20):
        a = i * 18
        rad = math.radians(a)
        petals.append(c.RE(500 + 210 * math.cos(rad), 420 + 210 * math.sin(rad), 120, 48, a))
    allp = Canvas.U(*petals)
    c.shadow(allp)
    for i, p in enumerate(petals):
        c.paint(p, (250, 196, 30) if i % 2 else (240, 176, 26), shade=0.6, soft=25, spec=0.2, edge=0.2)
    centre = c.E(500, 420, 150)
    c.paint(centre, (110, 66, 30), shade=0.7, soft=50, edge=0.3, tex=0.5, tex_scale=7)
    for i in range(60):
        r = 130 * math.sqrt(i / 60)
        t = i * 2.4
        c.paint(c.E(500 + r * math.cos(t), 420 + r * math.sin(t), 10), (60, 34, 16), shade=0, edge=0, alpha=0.6)


def mushroom(c):
    stem = c.U(c.R(400, 470, 600, 860, 70), c.E(500, 860, 120, 40))
    c.shadow(stem)
    c.paint(stem, (240, 228, 200), shade=0.7, soft=60, edge=0.3, tex=0.06)
    cap = c.U(c.E(500, 420, 330, 230))
    cap = c.S(cap, c.R(100, 470, 900, 900))
    cap = c.U(cap, c.E(500, 470, 330, 50))
    c.paint(cap, (210, 60, 40), shade=0.8, soft=80, spec=0.45, edge=0.3, tex=0.05)
    for x, y, r in [(380, 330, 45), (540, 270, 38), (650, 380, 40), (450, 440, 30), (300, 440, 26), (600, 450, 25)]:
        c.paint(c.E(x, y, r, r * 0.8), (250, 244, 226), shade=0.4, soft=10)


def pinecone(c):
    rows = [(260, 70, 3), (330, 110, 4), (410, 145, 5), (490, 170, 5), (570, 175, 6), (650, 160, 5), (720, 130, 4), (790, 90, 3)]
    all_m = []
    for y, half, n in rows:
        for i in range(n):
            x = 500 - half + (2 * half) * (i + 0.5) / n
            all_m.append((c.E(x, y, half * 1.1 / n + 26, 52), y))
    c.shadow(Canvas.U(*[m for m, _ in all_m]))
    for m, y in all_m:
        c.paint(m, mix((150, 98, 52), (104, 66, 34), (y - 260) / 530), shade=0.7, soft=22, edge=0.4, spec=0.2, tex=0.15)
    _stem(c, [(500, 200), (505, 140)], 40, (96, 64, 34))


def honey_jar(c):
    jar = c.R(290, 330, 710, 860, 90)
    c.shadow(jar)
    c.paint(jar, (226, 150, 30), shade=0.7, soft=70, spec=0.6, edge=0.2, grad=(196, 110, 20), grad_dir=(0, 1))
    c.paint(c.R(330, 360, 400, 820, 30), (255, 230, 150), shade=0, edge=0, alpha=0.35, blur=10)
    label = c.R(340, 520, 660, 700, 30)
    c.paint(label, (246, 236, 210), shade=0.4, soft=20)
    c.paint(c.E(500, 610, 60, 45), (226, 150, 30), shade=0.4, soft=12)
    lid = c.U(c.E(500, 320, 260, 60), c.P([(250, 320), (750, 320), (790, 420), (210, 420)]))
    c.paint(lid, (200, 60, 50), shade=0.6, soft=30, edge=0.2)
    for x in range(230, 780, 60):
        c.lines(c.R(x, 300, x + 22, 420, 2), (250, 240, 230), 0.55)
    c.paint(c.R(240, 395, 760, 425, 10), (150, 110, 60), shade=0.4, soft=8)


def wrapped_candy(c):
    for side in (-1, 1):
        tw = c.P([(500 + side * 170, 500), (500 + side * 400, 360), (500 + side * 360, 500), (500 + side * 400, 640)])
        c.paint(tw, (150, 70, 170), shade=0.6, soft=30, spec=0.3, tex=0.15, tex_stretch=(3, 0.3))
    body = c.E(500, 500, 210, 150)
    c.shadow(body)
    c.paint(body, (166, 80, 186), shade=0.8, soft=60, spec=0.7, edge=0.25)
    for dx in (-90, 0, 90):
        c.paint(c.RE(500 + dx, 500, 22, 150, 15), (250, 220, 240), shade=0.3, soft=12, alpha=0.8)


def candy_corn(c):
    tri = c.P([(500, 140), (760, 800), (720, 860), (280, 860), (240, 800)])
    tri = c.I(tri, c.E(500, 560, 330, 420))
    c.shadow(tri)
    c.paint(c.I(tri, c.R(0, 640, 1000, 1000)), (250, 210, 56), shade=0.7, soft=60, spec=0.4)
    c.paint(c.I(tri, c.R(0, 380, 1000, 640)), (240, 128, 30), shade=0.7, soft=60, spec=0.4)
    c.paint(c.I(tri, c.R(0, 0, 1000, 380)), (250, 246, 232), shade=0.7, soft=60, spec=0.4)


def lollipop(c):
    stick = c.R(470, 520, 530, 940, 24)
    c.paint(stick, (246, 240, 228), shade=0.6, soft=20)
    disk = c.E(500, 380, 260)
    c.shadow(disk)
    c.paint(disk, (250, 240, 220), shade=0.7, soft=70, spec=0.5)
    pts = []
    for i in range(400):
        t = i / 400 * 7 * math.pi
        r = 20 + 230 * i / 400
        pts.append((500 + r * math.cos(t), 380 + r * math.sin(t)))
    c.paint(c.I(c.L(pts, 46), disk), (230, 90, 40), shade=0.6, soft=30, spec=0.5)
    c.paint(c.E(420, 290, 70, 40), (255, 255, 255), shade=0, edge=0, alpha=0.35, blur=14)
    c.paint(c.R(440, 600, 560, 650, 10), (240, 200, 60), shade=0.4, soft=10)


def candy_bucket(c):
    handle = c.ARC(500, 380, 300, 260, 180, 360, 34)
    c.paint(handle, (90, 70, 60), shade=0.5, soft=12, spec=0.4)
    for x, y, col in [(400, 330, (166, 80, 186)), (520, 300, (250, 210, 56)), (610, 340, (60, 160, 200))]:
        c.paint(c.E(x, y, 70, 55), col, shade=0.7, soft=25, spec=0.5)
    body = c.U(c.E(500, 620, 330, 270), c.R(170, 380, 830, 600, 60))
    body = c.S(body, c.R(0, 0, 1000, 380))
    c.shadow(body)
    c.paint(body, (236, 124, 32), shade=0.75, soft=80, spec=0.45, edge=0.3)
    c.paint(c.E(500, 385, 330, 40), (196, 92, 22), shade=0.5, soft=20)
    for ex in (390, 610):
        c.paint(c.E(ex, 580, 40, 55), (70, 40, 20), shade=0.3, soft=10)
        c.paint(c.E(ex - 12, 562, 12), (255, 255, 255), shade=0, edge=0)
    c.paint(c.S(c.E(500, 680, 140, 90), c.E(500, 640, 160, 80)), (70, 40, 20), shade=0.3, soft=10)


# ------------------------------------------------------------------ home & baking
def pie(c):
    dish = c.U(c.E(500, 600, 420, 190), c.R(80, 600, 920, 700, 30), c.E(500, 700, 420, 160))
    c.shadow(dish)
    c.paint(dish, (186, 70, 50), shade=0.6, soft=50, spec=0.3, edge=0.3)
    crust = c.E(500, 560, 400, 180)
    c.paint(crust, (226, 168, 92), shade=0.6, soft=40, edge=0.2, tex=0.15)
    fill = c.E(500, 560, 330, 140)
    c.paint(fill, (196, 92, 30), shade=0.5, soft=40, spec=0.3)
    for i in range(-2, 3):
        c.paint(c.I(c.R(470 + i * 120, 400, 530 + i * 120, 720, 20), fill), (236, 186, 110), shade=0.6, soft=14, tex=0.15)
        c.paint(c.I(c.R(150, 535 + i * 52, 850, 565 + i * 52, 14), fill), (236, 186, 110), shade=0.6, soft=14, tex=0.15)
    for i in range(16):
        t = i / 16 * 2 * math.pi
        c.paint(c.E(500 + 380 * math.cos(t), 560 + 165 * math.sin(t), 46, 30), (236, 180, 104), shade=0.6, soft=14)


def cupcake(c):
    wrap = c.P([(300, 560), (700, 560), (650, 880), (350, 880)])
    c.shadow(wrap)
    c.paint(wrap, (220, 120, 60), shade=0.6, soft=40, edge=0.25)
    for i in range(7):
        x = 320 + i * 60
        c.lines(c.L([(x, 570), (x + (500 - x) * 0.12, 870)], 12), (180, 86, 40), 0.6)
    for y, rx in [(540, 250), (440, 200), (350, 140), (280, 70)]:
        c.paint(c.E(500, y, rx, 85 if rx > 100 else 60), (250, 236, 214), shade=0.7, soft=40, spec=0.3, edge=0.3)
    c.paint(c.E(500, 200, 55), (196, 32, 30), shade=0.8, soft=25, spec=0.7)
    _stem(c, [(505, 150), (540, 90)], 14, (90, 60, 30))
    for i, (x, y) in enumerate([(380, 500), (450, 410), (560, 470), (620, 520), (500, 330), (420, 560), (590, 380)]):
        c.paint(c.RE(x, y, 22, 8, i * 40), [(240, 128, 30), (250, 210, 56), (190, 60, 50)][i % 3], shade=0.3, soft=6)


def cookie(c):
    body = c.E(500, 500, 360, 340)
    c.shadow(body)
    c.paint(body, (206, 150, 84), shade=0.6, soft=60, edge=0.3, tex=0.35, tex_scale=12)
    for x, y in [(380, 380), (560, 330), (650, 480), (450, 560), (330, 560), (560, 650), (420, 450), (690, 620), (520, 470)]:
        c.paint(c.RE(x, y, 34, 28, x), (80, 46, 24), shade=0.6, soft=10, spec=0.3)


def cider_mug(c):
    handle = c.U(c.E(720, 560, 140, 170))
    handle = c.S(handle, c.E(720, 560, 80, 110))
    c.paint(handle, (238, 226, 200), shade=0.6, soft=30, spec=0.3)
    body = c.R(260, 360, 720, 860, 70)
    c.shadow(body)
    c.paint(body, (240, 228, 204), shade=0.7, soft=70, spec=0.4, edge=0.25)
    c.paint(c.R(260, 560, 720, 640, 0), (196, 70, 50), shade=0.4, soft=20, alpha=0.9)
    c.paint(c.E(490, 370, 220, 50), (150, 80, 30), shade=0.4, soft=20)
    c.paint(c.R(540, 180, 580, 420, 16), (140, 80, 40), shade=0.5, soft=10, tex=0.3, tex_stretch=(0.3, 3))
    for x in (400, 470):
        c.paint(c.CURVE((x, 320), (x - 60, 220), (x + 10, 120), 22), (255, 255, 255), shade=0, edge=0, alpha=0.5, blur=8)


def rolling_pin(c):
    for x0 in (90, 770):
        c.paint(c.R(x0, 460, x0 + 140, 540, 40), (166, 110, 60), shade=0.6, soft=20, tex=0.25, tex_stretch=(3, 0.3))
    body = c.R(200, 400, 800, 600, 60)
    c.shadow(body)
    c.paint(body, (214, 166, 104), shade=0.7, soft=50, spec=0.3, edge=0.3, tex=0.3, tex_scale=6, tex_stretch=(4, 0.25))
    c.paint(c.R(240, 420, 760, 450, 14), (255, 240, 210), shade=0, edge=0, alpha=0.3, blur=6)


def teapot(c):
    spout = c.P([(690, 560), (760, 520), (880, 380), (910, 400), (800, 600), (700, 680)])
    c.paint(spout, (54, 120, 130), shade=0.6, soft=30)
    handle = c.S(c.E(250, 560, 140, 160), c.E(250, 560, 80, 100))
    c.paint(handle, (54, 120, 130), shade=0.6, soft=30, spec=0.3)
    body = c.U(c.E(500, 600, 260, 230), c.R(260, 650, 740, 820, 60))
    c.shadow(body)
    c.paint(body, (60, 136, 146), shade=0.8, soft=80, spec=0.6, edge=0.3)
    c.paint(c.E(500, 390, 170, 45), (50, 112, 120), shade=0.5, soft=20)
    c.paint(c.E(500, 345, 50, 40), (226, 186, 90), shade=0.6, soft=14, spec=0.5)
    for x, y in [(420, 580), (520, 640), (600, 560)]:
        c.paint(c.E(x, y, 34), (250, 240, 220), shade=0.3, soft=8, alpha=0.9)


def basket(c):
    handle = c.ARC(500, 470, 300, 330, 180, 360, 44)
    c.paint(handle, (166, 112, 58), shade=0.5, soft=14, tex=0.3)
    for x, y in [(400, 440), (520, 420), (620, 460)]:
        c.paint(c.E(x, y, 90, 85), (196, 32, 30) if x != 520 else (210, 150, 40), shade=0.8, soft=40, spec=0.5)
    body = c.P([(180, 470), (820, 470), (740, 860), (260, 860)])
    c.shadow(body)
    c.paint(body, (186, 128, 66), shade=0.6, soft=50, edge=0.25, tex=0.15)
    for i in range(6):
        y = 500 + i * 62
        c.lines(c.L([(190 + i * 13, y), (810 - i * 13, y)], 10), (126, 80, 36), 0.7)
    for i in range(9):
        x = 230 + i * 68
        c.lines(c.L([(x, 480), (x + (500 - x) * 0.15, 850)], 9), (140, 92, 44), 0.5)
    c.paint(c.R(160, 450, 840, 510, 25), (166, 110, 56), shade=0.6, soft=14, tex=0.3)


def lantern(c):
    c.paint(c.ARC(500, 230, 130, 110, 180, 360, 26), (60, 60, 64), shade=0.5, soft=10, spec=0.5)
    c.paint(c.E(500, 560, 330, 330), (255, 200, 90), shade=0, edge=0, alpha=0.35, blur=110, glow=True)
    top = c.P([(330, 330), (670, 330), (620, 240), (380, 240)])
    c.paint(top, (176, 40, 34), shade=0.6, soft=20, spec=0.4)
    glass = c.R(350, 330, 650, 760, 50)
    c.shadow(glass)
    c.paint(glass, (255, 214, 120), shade=0.4, soft=60, light=(0, 0.6), spec=0.3, grad=(250, 170, 60), grad_dir=(0, 1))
    c.paint(c.RE(500, 560, 34, 70, 0), (255, 250, 220), shade=0, edge=0)
    for x in (360, 640):
        c.paint(c.R(x - 18, 330, x + 18, 760, 8), (60, 60, 64), shade=0.5, soft=8, spec=0.4)
    c.paint(c.R(320, 750, 680, 820, 18), (176, 40, 34), shade=0.6, soft=16, spec=0.4)


def watering_can(c):
    spout = c.P([(700, 580), (900, 330), (930, 350), (760, 680)])
    c.paint(spout, (70, 136, 96), shade=0.6, soft=20)
    c.paint(c.RE(905, 330, 50, 30, -40), (60, 120, 86), shade=0.5, soft=14)
    handle = c.S(c.E(470, 420, 230, 170), c.E(470, 440, 170, 120))
    handle = c.S(handle, c.R(0, 480, 1000, 1000))
    c.paint(handle, (60, 126, 90), shade=0.6, soft=20, spec=0.4)
    body = c.R(230, 460, 720, 860, 70)
    c.shadow(body)
    c.paint(body, (80, 150, 106), shade=0.8, soft=70, spec=0.55, edge=0.3)
    c.paint(c.R(230, 540, 720, 580, 6), (60, 120, 86), shade=0.3, soft=10, alpha=0.7)


def birdhouse(c):
    c.paint(c.R(470, 760, 530, 960, 10), (120, 84, 50), shade=0.5, soft=14, tex=0.3)
    body = c.R(290, 420, 710, 800, 20)
    c.shadow(body)
    c.paint(body, (210, 180, 130), shade=0.6, soft=40, edge=0.2, tex=0.2, tex_stretch=(0.2, 4))
    roof = c.P([(220, 450), (500, 200), (780, 450), (740, 480), (500, 270), (260, 480)])
    c.paint(c.U(roof, c.P([(260, 470), (500, 250), (740, 470)])), (176, 60, 40), shade=0.6, soft=30, tex=0.15)
    c.paint(c.E(500, 560, 70), (60, 36, 20), shade=0.4, soft=14, light=(0.5, 0.8))
    c.paint(c.R(470, 660, 530, 690, 10), (120, 84, 50), shade=0.5, soft=8)
    c.paint(c.R(480, 690, 520, 720, 10), (120, 84, 50), shade=0.5, soft=8)


def straw_hat(c):
    brim = c.E(500, 640, 440, 170)
    c.shadow(brim)
    c.paint(brim, (226, 190, 112), shade=0.6, soft=50, edge=0.25, tex=0.35, tex_scale=5, tex_stretch=(3, 0.4))
    crown = c.U(c.E(500, 420, 240, 160), c.R(260, 420, 740, 620, 40))
    c.paint(crown, (230, 196, 120), shade=0.7, soft=60, edge=0.25, tex=0.3, tex_scale=5, tex_stretch=(3, 0.4))
    band = c.I(crown, c.R(0, 540, 1000, 620))
    c.paint(band, (190, 50, 40), shade=0.6, soft=20, spec=0.2)
    for i in range(10):  # straw tufts
        x = 90 + i * 90
        c.lines(c.L([(x, 660 + (i % 3) * 10), (x + 20 * ((i % 2) * 2 - 1), 760)], 10), (210, 170, 90), 0.8)


def scarf(c):
    tail1 = c.R(530, 450, 650, 900, 20)
    tail2 = c.RE(440, 700, 70, 220, 14)
    for t in (tail2, tail1):
        c.paint(t, (196, 54, 44), shade=0.6, soft=30, tex=0.2)
    loop = c.S(c.E(500, 380, 300, 220), c.E(500, 360, 200, 130))
    c.shadow(loop)
    c.paint(loop, (206, 60, 48), shade=0.7, soft=50, edge=0.25, tex=0.15)
    for y in (520, 620, 720, 820):
        c.paint(c.I(c.R(0, y, 1000, y + 40), c.U(tail1, tail2)), (246, 230, 200), shade=0.3, soft=10, alpha=0.9)
    for x in range(540, 650, 22):
        c.lines(c.L([(x, 900), (x, 960)], 9), (196, 54, 44), 0.9)


def mitten(c):
    m = c.U(c.E(500, 460, 200, 260), c.RE(320, 520, 80, 140, -35), c.R(300, 600, 700, 760, 30))
    c.shadow(m)
    c.paint(m, (190, 60, 50), shade=0.7, soft=60, edge=0.3, tex=0.3, tex_scale=4)
    cuff = c.R(290, 720, 710, 880, 40)
    c.paint(cuff, (246, 236, 216), shade=0.6, soft=40, tex=0.3, tex_scale=4, tex_stretch=(0.4, 2))
    for x in range(330, 700, 50):
        c.lines(c.L([(x, 735), (x, 865)], 10), (220, 206, 186), 0.6)
    c.paint(c.star(520, 470, 80, 30, 5), (250, 230, 200), shade=0.3, soft=8)


def rubber_boot(c):
    boot = c.U(c.R(330, 200, 600, 820, 40), c.R(330, 640, 800, 860, 90))
    c.shadow(boot)
    c.paint(boot, (236, 186, 30), shade=0.75, soft=60, spec=0.55, edge=0.3)
    c.paint(c.R(320, 820, 810, 880, 20), (90, 70, 50), shade=0.5, soft=14)
    c.paint(c.R(320, 200, 610, 270, 20), (210, 160, 20), shade=0.5, soft=14)


def horseshoe(c):
    shoe = c.S(c.U(c.E(500, 460, 330, 360), c.R(170, 460, 830, 860, 40)), c.U(c.E(500, 460, 200, 230), c.R(300, 460, 700, 900, 10)))
    c.shadow(shoe)
    c.paint(shoe, (150, 150, 156), shade=0.8, soft=40, spec=0.6, edge=0.3, tex=0.08)
    for x, y in [(230, 560), (225, 700), (260, 360), (770, 560), (775, 700), (740, 360)]:
        c.paint(c.E(x, y, 18), (70, 70, 74), shade=0.3, soft=6, light=(0.5, 0.8))


def kite(c):
    tail = [(500, 860), (440, 920), (520, 970)]
    c.paint(c.CURVE((500, 820), (380, 900), (470, 980), 10), (120, 90, 60), shade=0, edge=0)
    for x, y in [(445, 890), (440, 950)]:
        c.paint(c.P([(x - 40, y - 25), (x + 40, y + 25), (x + 40, y - 25), (x - 40, y + 25)]), (230, 70, 50), shade=0.4, soft=8)
    k = c.P([(500, 80), (800, 380), (500, 820), (200, 380)])
    c.shadow(k)
    c.paint(c.I(k, c.P([(500, 80), (500, 380), (200, 380)])), (236, 124, 32), shade=0.4, soft=30, spec=0.3)
    c.paint(c.I(k, c.P([(500, 80), (500, 380), (800, 380)])), (250, 210, 56), shade=0.4, soft=30, spec=0.3)
    c.paint(c.I(k, c.P([(200, 380), (500, 380), (500, 820)])), (196, 54, 44), shade=0.4, soft=30, spec=0.3)
    c.paint(c.I(k, c.P([(800, 380), (500, 380), (500, 820)])), (236, 150, 40), shade=0.4, soft=30, spec=0.3)
    c.lines(c.L([(500, 90), (500, 815)], 10), (120, 90, 60))
    c.lines(c.L([(210, 380), (790, 380)], 10), (120, 90, 60))


def ribbon(c):
    for ang, x in [(-25, 300), (25, 700)]:
        loop = c.S(c.RE(x, 420, 210, 130, ang), c.RE(x + (40 if x < 500 else -40), 420, 110, 50, ang))
        c.paint(loop, (196, 40, 40), shade=0.75, soft=40, spec=0.5, edge=0.3)
    for pts in ([(470, 480), (300, 840), (380, 860), (520, 500)], [(530, 480), (700, 840), (620, 860), (480, 500)]):
        c.paint(c.P(pts), (176, 34, 34), shade=0.6, soft=30, spec=0.4)
    knot = c.E(500, 440, 90, 100)
    c.shadow(knot)
    c.paint(knot, (210, 50, 46), shade=0.8, soft=30, spec=0.6)


def fox_mask(c):
    for side in (-1, 1):
        ear = c.P([(500 + side * 330, 120), (500 + side * 120, 330), (500 + side * 380, 400)])
        c.paint(ear, (220, 110, 40), shade=0.6, soft=30)
        c.paint(c.P([(500 + side * 320, 190), (500 + side * 190, 330), (500 + side * 340, 370)]), (70, 46, 34), shade=0.4, soft=14)
    face = c.U(c.E(500, 470, 330, 260), c.P([(190, 480), (810, 480), (500, 860)]))
    c.shadow(face)
    c.paint(face, (230, 120, 44), shade=0.75, soft=70, spec=0.35, edge=0.3)
    for side in (-1, 1):
        c.paint(c.P([(500 + side * 40, 560), (500 + side * 300, 520), (500 + side * 60, 820)]), (250, 240, 226), shade=0.5, soft=30)
        eye = c.RE(500 + side * 140, 450, 70, 46, side * 12)
        c.paint(eye, (60, 36, 24), shade=0.4, soft=14, light=(0.5, 0.8))
    c.paint(c.E(500, 800, 60, 42), (60, 36, 24), shade=0.6, soft=12, spec=0.5)
    c.paint(c.ARC(500, 470, 380, 60, 160, 380, 10), (120, 80, 50), shade=0, edge=0, alpha=0.0)


def bluebird(c):
    tail = c.P([(220, 560), (60, 470), (90, 640)])
    c.paint(tail, (60, 100, 180), shade=0.5, soft=20)
    body = c.U(c.E(470, 560, 270, 210), c.E(650, 400, 150, 140))
    c.shadow(body)
    c.paint(body, (70, 120, 200), shade=0.8, soft=70, spec=0.4, edge=0.3)
    c.paint(c.I(c.E(560, 650, 230, 140), body), (226, 130, 70), shade=0.6, soft=50)
    wing = c.RE(410, 520, 190, 90, -15)
    c.paint(wing, (52, 92, 170), shade=0.7, soft=30, spec=0.3)
    c.paint(c.P([(780, 390), (880, 420), (780, 440)]), (240, 180, 60), shade=0.5, soft=10)
    c.paint(c.E(700, 370, 26), (30, 24, 20), shade=0.3, soft=6)
    c.paint(c.E(692, 362, 8), (255, 255, 255), shade=0, edge=0)
    for x in (430, 520):
        c.lines(c.L([(x, 760), (x - 10, 840)], 12), (120, 90, 60))


def teddy_bear(c):
    for x in (330, 670):
        c.paint(c.E(x, 230, 80), (150, 100, 56), shade=0.7, soft=30, tex=0.3, tex_scale=3)
        c.paint(c.E(x, 235, 40), (210, 170, 120), shade=0.5, soft=12)
    body = c.E(500, 680, 220, 230)
    c.shadow(body)
    c.paint(body, (156, 104, 58), shade=0.75, soft=70, edge=0.3, tex=0.3, tex_scale=3)
    c.paint(c.E(500, 700, 120, 130), (210, 170, 120), shade=0.5, soft=40, tex=0.2, tex_scale=3)
    for x in (300, 700):
        c.paint(c.E(x, 640, 70, 110), (150, 100, 56), shade=0.7, soft=30, tex=0.3, tex_scale=3)
    head = c.E(500, 380, 220, 200)
    c.paint(head, (162, 110, 62), shade=0.75, soft=70, edge=0.3, tex=0.3, tex_scale=3)
    c.paint(c.E(500, 450, 100, 70), (216, 178, 128), shade=0.5, soft=30)
    c.paint(c.E(500, 420, 36, 26), (50, 30, 20), shade=0.5, soft=8, spec=0.6)
    for x in (420, 580):
        c.paint(c.E(x, 340, 24), (40, 26, 18), shade=0.3, soft=6, spec=0.6)
    c.paint(c.ARC(500, 450, 50, 40, 20, 160, 10), (60, 40, 26), shade=0, edge=0)
    c.paint(c.R(330, 530, 670, 580, 20), (196, 54, 44), shade=0.5, soft=14)  # little scarf


def balloon(c):
    c.paint(c.CURVE((500, 760), (420, 860), (520, 980), 9), (140, 120, 100), shade=0, edge=0)
    b = c.U(c.E(500, 420, 260, 320), c.P([(470, 730), (530, 730), (550, 770), (450, 770)]))
    c.shadow(b)
    c.paint(b, (210, 50, 40), shade=0.8, soft=90, spec=0.75, edge=0.25)
    c.paint(c.RE(400, 300, 50, 90, 25), (255, 255, 255), shade=0, edge=0, alpha=0.45, blur=16)


def ticket(c):
    t = c.R(120, 320, 880, 680, 30)
    for x, y in [(120, 500), (880, 500)]:
        t = c.S(t, c.E(x, y, 60))
    c.shadow(t)
    c.paint(t, (240, 176, 60), shade=0.5, soft=40, edge=0.2, tex=0.06)
    c.paint(c.I(c.R(160, 360, 840, 640, 20), t), (250, 214, 110), shade=0.3, soft=20)
    for y in range(350, 660, 36):
        c.paint(c.E(680, y, 9), (196, 120, 40), shade=0, edge=0)
    c.paint(c.star(400, 500, 110, 46, 5), (206, 70, 40), shade=0.5, soft=14, spec=0.3)


SPRITES = {
    "pumpkin": pumpkin, "jackolantern": jackolantern, "apple": apple, "pear": pear, "acorn": acorn,
    "maple_leaf": maple_leaf, "oak_leaf": oak_leaf, "corn": corn, "candy_corn": candy_corn,
    "wrapped_candy": wrapped_candy, "lollipop": lollipop, "candy_bucket": candy_bucket, "straw_hat": straw_hat,
    "scarf": scarf, "pie": pie, "cupcake": cupcake, "cookie": cookie, "cider_mug": cider_mug,
    "rolling_pin": rolling_pin, "sunflower": sunflower, "watering_can": watering_can, "mushroom": mushroom,
    "basket": basket, "lantern": lantern, "teapot": teapot, "ribbon": ribbon, "honey_jar": honey_jar,
    "pinecone": pinecone, "fox_mask": fox_mask, "bluebird": bluebird, "mitten": mitten, "gourd": gourd,
    "horseshoe": horseshoe, "rubber_boot": rubber_boot, "kite": kite, "birdhouse": birdhouse,
    "caramel_apple": caramel_apple, "balloon": balloon, "ticket": ticket, "teddy_bear": teddy_bear,
}


def render(name, size=384):
    c = Canvas(size, ss=2)
    SPRITES[name](c)
    img = c.image()
    bb = img.getbbox()
    return img
