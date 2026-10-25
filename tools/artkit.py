"""artkit - a tiny painterly rendering kit used to draw all of Maple Lane Finds' art.

Everything in the game is drawn by code (no outside images), so the art is 100% original.
Shapes are built as masks with PIL, then "painted" with numpy: soft directional lighting,
rim shading, specular highlights, texture and proper alpha compositing. Canvases are
supersampled and box-filtered down for clean HD edges.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

LIGHT = (-0.55, -0.83)  # light comes from the upper left


def mix(c1, c2, t):
    return tuple(int(round(c1[i] * (1 - t) + c2[i] * t)) for i in range(3))


def shade_col(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c[:3])


class Canvas:
    def __init__(self, W, H=None, ss=2, units=1000):
        self.W, self.H, self.ss = W, (H or W), ss
        self.w, self.h = self.W * ss, self.H * ss
        # unit scale: sprites use a 0..1000 space across the width; scenes use final pixels
        self.k = (self.w / units) if units else ss
        self.rgb = np.zeros((self.h, self.w, 3), np.float32)
        self.a = np.zeros((self.h, self.w), np.float32)
        self.rng = np.random.default_rng(7)

    # ------------------------------------------------------------ geometry
    def u(self, v):
        return v * self.k

    def _m(self):
        m = Image.new("L", (self.w, self.h), 0)
        return m, ImageDraw.Draw(m)

    def E(self, cx, cy, rx, ry=None):
        ry = rx if ry is None else ry
        m, d = self._m()
        d.ellipse([self.u(cx - rx), self.u(cy - ry), self.u(cx + rx), self.u(cy + ry)], fill=255)
        return m

    def RE(self, cx, cy, rx, ry, ang, n=72):
        a = math.radians(ang)
        pts = []
        for i in range(n):
            t = 2 * math.pi * i / n
            x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
        return self.P(pts)

    def P(self, pts):
        m, d = self._m()
        d.polygon([(self.u(x), self.u(y)) for x, y in pts], fill=255)
        return m

    def R(self, x0, y0, x1, y1, r=0):
        m, d = self._m()
        d.rounded_rectangle([self.u(x0), self.u(y0), self.u(x1), self.u(y1)], radius=self.u(r), fill=255)
        return m

    def L(self, pts, w):
        m, d = self._m()
        p = [(self.u(x), self.u(y)) for x, y in pts]
        d.line(p, fill=255, width=max(1, int(self.u(w))), joint="curve")
        r = self.u(w) / 2
        for x, y in (p[0], p[-1]):
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        return m

    def ARC(self, cx, cy, rx, ry, a0, a1, w, n=60):
        pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
        return self.L(pts, w)

    def CURVE(self, p0, p1, p2, w, n=40):
        pts = []
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            pts.append((x, y))
        return self.L(pts, w)

    def TAPER(self, p0, p1, p2, w, n=30):
        """A leaf-like tapered stroke along a quadratic curve (wide in the middle, pointed ends)."""
        pts = []
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            pts.append((x, y))
        left, right = [], []
        for i, (x, y) in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(n, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            t = i / n
            hw = w / 2 * math.sin(math.pi * t) ** 0.7
            left.append((x + nx * hw, y + ny * hw))
            right.append((x - nx * hw, y - ny * hw))
        return self.P(left + right[::-1])

    def vignette(self, strength=0.28, warm=(255, 210, 160)):
        ys, xs = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        d = np.sqrt(((xs / self.w) - 0.5) ** 2 * 1.2 + ((ys / self.h) - 0.48) ** 2)
        v = np.clip((d - 0.32) / 0.5, 0, 1) ** 1.6
        self.rgb *= (1 - strength * v)[..., None]
        glow = np.clip(1 - d / 0.6, 0, 1) ** 2 * 0.06
        self.rgb = np.clip(self.rgb * (1 - glow[..., None]) + np.array(warm, np.float32) * glow[..., None], 0, 255)

    @staticmethod
    def U(*ms):
        out = ms[0]
        for m in ms[1:]:
            out = ImageChops.lighter(out, m)
        return out

    @staticmethod
    def S(a, b):
        return ImageChops.subtract(a, b)

    @staticmethod
    def I(a, b):
        return ImageChops.darker(a, b)

    def star(self, cx, cy, r_out, r_in, n=5, rot=-90):
        pts = []
        for i in range(n * 2):
            r = r_out if i % 2 == 0 else r_in
            t = math.radians(rot + i * 180 / n)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        return self.P(pts)

    # ------------------------------------------------------------ textures
    def noise(self, shape, scale=1.0, stretch=(1, 1), seed=None):
        rng = np.random.default_rng(seed) if seed is not None else self.rng
        h, w = shape
        sh = max(2, int(h / (scale * stretch[1])))
        sw = max(2, int(w / (scale * stretch[0])))
        n = rng.random((sh, sw)).astype(np.float32)
        img = Image.fromarray((n * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
        return np.asarray(img, np.float32) / 255.0 - 0.5

    # ------------------------------------------------------------ painting
    def paint(self, mask, color, shade=0.55, soft=40, light=LIGHT, spec=0.0, edge=0.25,
              tex=0.0, tex_scale=3.0, tex_stretch=(1, 1), alpha=1.0, blur=0, grad=None,
              grad_dir=(0, 1), glow=False):
        """Paint a mask with a lit, textured colour.
        grad: second colour for a linear gradient along grad_dir (unit vector)."""
        if blur:
            mask = mask.filter(ImageFilter.GaussianBlur(self.u(blur)))
        bb = mask.getbbox()
        if not bb:
            return
        r = max(1.0, self.u(soft))
        pad = int(r * 1.6) + 6
        x0, y0 = max(0, bb[0] - pad), max(0, bb[1] - pad)
        x1, y1 = min(self.w, bb[2] + pad), min(self.h, bb[3] + pad)
        mc = mask.crop((x0, y0, x1, y1))
        m = np.asarray(mc, np.float32) / 255.0
        hh, ww = m.shape
        base = np.array(color[:3], np.float32)
        if grad is not None:
            ys, xs = np.mgrid[0:hh, 0:ww].astype(np.float32)
            gx, gy = grad_dir
            proj = xs * gx + ys * gy
            bx0, by0, bx1, by1 = bb[0] - x0, bb[1] - y0, bb[2] - x0, bb[3] - y0
            corners = [bx0 * gx + by0 * gy, bx1 * gx + by0 * gy, bx0 * gx + by1 * gy, bx1 * gx + by1 * gy]
            lo, hi = min(corners), max(corners)
            t = np.clip((proj - lo) / max(1e-3, hi - lo), 0, 1)[..., None]
            col = base[None, None, :] * (1 - t) + np.array(grad[:3], np.float32)[None, None, :] * t
        else:
            col = np.broadcast_to(base, (hh, ww, 3)).astype(np.float32).copy()
        if shade > 0 or edge > 0 or spec > 0:
            n = np.asarray(mc.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0
            k = max(1, int(r * 0.6))
            sx, sy = int(round(light[0] * k)), int(round(light[1] * k))
            g = np.roll(n, (sy, sx), (0, 1)) - np.roll(n, (-sy, -sx), (0, 1))
            lum = 1.0 + shade * 1.6 * g - edge * (1.0 - n)
            col *= lum[..., None]
            if spec > 0:
                s = (np.clip((g - 0.10) / 0.22, 0, 1) ** 2) * spec
                col = col * (1 - s[..., None]) + np.array([255, 250, 236], np.float32) * s[..., None]
        if tex:
            nz = self.noise((hh, ww), self.u(tex_scale), tex_stretch)
            col *= (1.0 + tex * nz)[..., None]
        col = np.clip(col, 0, 255)
        an = m * alpha
        if glow:  # additive light
            self.rgb[y0:y1, x0:x1] = np.clip(self.rgb[y0:y1, x0:x1] + col * an[..., None], 0, 255)
            self.a[y0:y1, x0:x1] = np.maximum(self.a[y0:y1, x0:x1], an * 0.0)
            return
        a_old = self.a[y0:y1, x0:x1]
        out_a = an + a_old * (1 - an)
        safe = np.maximum(out_a, 1e-6)[..., None]
        self.rgb[y0:y1, x0:x1] = (col * an[..., None] + self.rgb[y0:y1, x0:x1] * (a_old * (1 - an))[..., None]) / safe
        self.a[y0:y1, x0:x1] = out_a

    def shadow(self, mask, dx=14, dy=22, blur=26, opacity=0.35, color=(40, 22, 10)):
        m = mask.filter(ImageFilter.GaussianBlur(self.u(blur)))
        m = ImageChops.offset(m, int(self.u(dx)), int(self.u(dy)))
        self.paint(m, color, shade=0, edge=0, alpha=opacity)

    def lines(self, mask, color, alpha=1.0):
        self.paint(mask, color, shade=0, edge=0, alpha=alpha)

    def paste(self, img, cx, cy, w, rot=0, alpha=1.0, flip=False):
        """Composite a straight-alpha RGBA image centred at (cx, cy), w units wide."""
        if flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if rot:
            img = img.rotate(rot, Image.BICUBIC, expand=True)
        pw = max(1, int(self.u(w)))
        ph = max(1, int(img.height * pw / img.width))
        im = img.resize((pw, ph), Image.LANCZOS)
        x0, y0 = int(self.u(cx) - pw / 2), int(self.u(cy) - ph / 2)
        sx0, sy0 = max(0, -x0), max(0, -y0)
        x0c, y0c = max(0, x0), max(0, y0)
        x1c, y1c = min(self.w, x0 + pw), min(self.h, y0 + ph)
        if x1c <= x0c or y1c <= y0c:
            return
        arr = np.asarray(im, np.float32)[sy0:sy0 + (y1c - y0c), sx0:sx0 + (x1c - x0c)]
        col, an = arr[..., :3], arr[..., 3] / 255.0 * alpha
        a_old = self.a[y0c:y1c, x0c:x1c]
        out_a = an + a_old * (1 - an)
        safe = np.maximum(out_a, 1e-6)[..., None]
        self.rgb[y0c:y1c, x0c:x1c] = (col * an[..., None] + self.rgb[y0c:y1c, x0c:x1c] * (a_old * (1 - an))[..., None]) / safe
        self.a[y0c:y1c, x0c:x1c] = out_a

    def fill(self, color, grad=None, grad_dir=(0, 1)):
        m = Image.new("L", (self.w, self.h), 255)
        self.paint(m, color, shade=0, edge=0, grad=grad, grad_dir=grad_dir)

    def blur_all(self, radius):
        """Soften everything painted so far (used for depth-of-field on far layers)."""
        r = self.u(radius)
        chans = [Image.fromarray(np.clip(self.rgb[..., i], 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
                 for i in range(3)]
        self.rgb = np.dstack([np.asarray(ch, np.float32) for ch in chans])

    # ------------------------------------------------------------ output
    def image(self, drop_shadow=False):
        rgb, a = self.rgb, self.a
        if drop_shadow:
            am = Image.fromarray((a * 255).astype(np.uint8), "L")
            sh = am.filter(ImageFilter.GaussianBlur(self.w * 0.018))
            sh = np.asarray(ImageChops.offset(sh, int(self.w * 0.012), int(self.w * 0.022)), np.float32) / 255 * 0.42
            out_a = a + sh * (1 - a)
            safe = np.maximum(out_a, 1e-6)[..., None]
            rgb = (rgb * a[..., None] + np.array([45, 25, 12], np.float32) * (sh * (1 - a))[..., None]) / safe
            a = out_a
        # premultiply, box-downsample, un-premultiply (clean edges, no dark fringes)
        pm = rgb * a[..., None]
        s = self.ss
        h, w = self.H, self.W
        pm = pm[:h * s, :w * s].reshape(h, s, w, s, 3).mean(axis=(1, 3))
        aa = a[:h * s, :w * s].reshape(h, s, w, s).mean(axis=(1, 3))
        col = pm / np.maximum(aa, 1e-6)[..., None]
        out = np.dstack([np.clip(col, 0, 255), np.clip(aa * 255, 0, 255)]).astype(np.uint8)
        return Image.fromarray(out, "RGBA")
