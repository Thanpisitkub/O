#!/usr/bin/env python3
"""Procedural generator for the Pain Origin particle textures (original artwork, CC0).

Usage: gen_textures.py <particle_out_dir> <gui_out_dir>

Every texture is true RGBA.  The colour field is defined for every pixel (also the
fully transparent ones) so bilinear filtering / mipmapping can never produce a
dark or white halo, and every texture is windowed so the outer pixels are alpha 0
(no rectangular frame).
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

PART_DIR = sys.argv[1]
GUI_DIR = sys.argv[2]
os.makedirs(PART_DIR, exist_ok=True)
os.makedirs(GUI_DIR, exist_ok=True)

WHITE = np.array([1.0, 1.0, 1.0], np.float32)
LBLUE = np.array([0.55, 0.82, 1.00], np.float32)
VIOLET = np.array([0.66, 0.44, 1.00], np.float32)
DVIOLET = np.array([0.36, 0.14, 0.72], np.float32)
BLACKV = np.array([0.04, 0.01, 0.09], np.float32)


# ----------------------------------------------------------------- helpers
def grid(n):
    ax = (np.arange(n, dtype=np.float32) + 0.5) / n * 2.0 - 1.0
    x, y = np.meshgrid(ax, ax)
    return x, y, np.hypot(x, y), np.arctan2(y, x)


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gauss(v, s):
    return np.exp(-((v / s) ** 2))


def mix(c0, c1, t):
    t = np.asarray(t, np.float32)[..., None]
    return np.asarray(c0, np.float32) * (1.0 - t) + np.asarray(c1, np.float32) * t


def wrap_pi(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def fbm(n, scale, seed, octaves=4):
    g = np.random.default_rng(seed)
    out = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        a = g.random((n, n)).astype(np.float32)
        a = ndi.gaussian_filter(a, max(scale / (2 ** o), 0.6), mode="wrap")
        a = (a - a.min()) / (a.max() - a.min() + 1e-9)
        out += a * amp
        tot += amp
        amp *= 0.55
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-9)


def angular_noise(th, seed, freqs=(3, 5, 8, 13, 21), base=1.0):
    g = np.random.default_rng(seed)
    v = np.zeros_like(th)
    amp = base
    tot = 0.0
    for f in freqs:
        v += amp * np.cos(f * th + g.uniform(0, 2 * np.pi))
        tot += amp
        amp *= 0.8
    v /= tot
    return (v - v.min()) / (v.max() - v.min() + 1e-9)


def polar_streaks(r, th, n, seed, sig_r=18.0, sig_a=1.4):
    """Noise that varies quickly with angle and slowly with radius (radial streaks)."""
    g = np.random.default_rng(seed)
    pn = g.random((2 * n, n)).astype(np.float32)
    pn = ndi.gaussian_filter(pn, sigma=(sig_r, sig_a), mode=("nearest", "wrap"))
    pn = (pn - pn.min()) / (pn.max() - pn.min() + 1e-9)
    u = (th + np.pi) / (2 * np.pi) * n
    v = np.clip(r, 0, 1.99) * n
    return ndi.map_coordinates(pn, [v, u], order=1, mode="grid-wrap")


def over(base_rgb, base_a, rgb, a):
    """Straight-alpha 'over' compositing; colour stays defined where alpha is 0."""
    a = np.clip(a, 0.0, 1.0)
    out_a = a + base_a * (1.0 - a)
    prem = rgb * a[..., None] + base_rgb * (base_a * (1.0 - a))[..., None]
    safe = np.maximum(out_a, 1e-5)[..., None]
    out_rgb = np.where((out_a > 1e-4)[..., None], prem / safe, rgb)
    return out_rgb.astype(np.float32), out_a.astype(np.float32)


def save_rgba(rgb, a, path):
    a = np.clip(a, 0.0, 1.0)
    rgb = np.clip(rgb, 0.0, 1.0)
    arr = np.dstack([rgb, a])
    Image.fromarray((arr * 255.0 + 0.5).astype(np.uint8), "RGBA").save(path, optimize=True)
    print("wrote", path)


# ----------------------------------------------------------------- 1. wave
RING_FRACTION = 0.86  # radius of the bright ring as a fraction of the half-width (used by the Java side)


def make_wave(n=256):
    x, y, r, th = grid(n)
    d = r - RING_FRACTION
    ang = angular_noise(th, 11)
    streak = polar_streaks(r, th, n, 12)
    core = gauss(d, 0.014)
    inner = 0.55 * gauss(d + 0.040, 0.080)
    outer = 0.42 * gauss(d - 0.030, 0.045)
    ring2 = 0.34 * gauss(r - 0.705, 0.010)
    ring3 = 0.20 * gauss(r - 0.585, 0.008)
    ring4 = 0.12 * gauss(r - 0.47, 0.007)
    a_main = np.clip(core + inner + outer, 0, 1) * (0.72 + 0.28 * streak) * (0.88 + 0.12 * ang)
    a_rings = 1 - (1 - ring2) * (1 - ring3) * (1 - ring4)
    a = 1 - (1 - a_main) * (1 - a_rings * (0.8 + 0.2 * streak))
    a *= 1.0 - smooth(0.93, 0.985, r)
    col = np.broadcast_to(WHITE, (n, n, 3)).copy()
    col = mix(col, LBLUE, smooth(0.008, 0.10, -d))
    col = mix(col, VIOLET, smooth(0.008, 0.075, d))
    col = mix(col, 0.7 * LBLUE + 0.3 * VIOLET, np.clip(a_rings / (a_main + a_rings + 1e-4), 0, 1) * 0.8)
    return col, a


# ----------------------------------------------------------------- 2. burst
def make_burst(n=256):
    x, y, r, th = grid(n)
    g = np.random.default_rng(23)
    a = 1.0 - np.exp(-((r / 0.20) ** 2)) * 0  # start at zero
    a = np.zeros((n, n), np.float32)
    col = np.broadcast_to(WHITE, (n, n, 3)).copy()
    tint = np.zeros((n, n), np.float32)
    nsp = 17
    prod = np.ones((n, n), np.float32)
    for i in range(nsp):
        ang = (i + g.uniform(-0.35, 0.35)) * 2 * np.pi / nsp
        length = g.uniform(0.50, 0.98)
        w0 = g.uniform(0.030, 0.075)
        strength = g.uniform(0.65, 1.0)
        dth = wrap_pi(th - ang)
        perp = np.abs(np.sin(dth)) * r
        along = np.cos(dth) * r
        frac = np.clip(along / length, 0.0, 1.0)
        wlin = w0 * (1.0 - frac) + 0.004
        spike = np.exp(-((perp / wlin) ** 2)) * np.clip(1.0 - frac, 0, 1) ** 1.1 * (along > 0) * strength
        prod *= 1.0 - spike
        tint = np.maximum(tint, spike * g.uniform(0.0, 1.0))
    spikes = 1.0 - prod
    glow = 0.95 * np.exp(-((r / 0.17) ** 2)) + 0.45 * np.exp(-((r / 0.42) ** 2))
    flare = 0.22 * gauss(r - 0.52, 0.012) * (0.4 + 0.6 * angular_noise(th, 31))
    a = 1 - (1 - spikes) * (1 - np.clip(glow, 0, 1)) * (1 - flare)
    a *= 1.0 - smooth(0.93, 0.985, r)
    col = mix(WHITE, LBLUE, smooth(0.08, 0.30, r))
    col = mix(col, VIOLET, smooth(0.34, 0.80, r) * (0.55 + 0.45 * tint))
    return col, a


# ----------------------------------------------------------------- 3. bansho tenin aura (spiral)
def make_aura(n=256):
    x, y, r, th = grid(n)
    rr = np.maximum(r, 1e-3)
    arms = 3
    k = 2.3
    rgb = np.broadcast_to(BLACKV, (n, n, 3)).copy()
    a = np.zeros((n, n), np.float32)
    env = smooth(0.05, 0.20, r) * (1.0 - smooth(0.78, 0.96, r))
    # dark core (singularity)
    hole = np.clip(1.15 * np.exp(-((r / 0.20) ** 2)), 0, 0.92)
    rgb, a = over(rgb, a, np.broadcast_to(BLACKV, (n, n, 3)), hole)
    for i in range(arms):
        phase = i * 2 * np.pi / arms
        dth = wrap_pi(th - (k * np.log(rr) + phase))
        perp = dth * r
        wid = 0.020 + 0.055 * r
        dark = np.exp(-((perp / (wid * 1.9)) ** 2)) * env * 0.80
        body = np.exp(-((perp / wid) ** 2)) * env * 0.92
        hi = np.exp(-((perp / (wid * 0.30)) ** 2)) * env
        rgb, a = over(rgb, a, np.broadcast_to(np.array([0.05, 0.0, 0.11], np.float32), (n, n, 3)), dark)
        rgb, a = over(rgb, a, mix(DVIOLET, VIOLET * 0.92, smooth(0.15, 0.8, r)), body)
        rgb, a = over(rgb, a, mix(VIOLET, WHITE, 0.70 + 0.3 * smooth(0.15, 0.7, r)), hi * 0.95)
    # faint outer swirl dust
    dust = polar_streaks(r, th, n, 41, sig_r=10, sig_a=2.2)
    dust_a = (dust > 0.62) * (dust - 0.62) * 1.6 * env * 0.45
    rgb, a = over(rgb, a, np.broadcast_to(VIOLET * 0.8, (n, n, 3)), dust_a)
    a *= 1.0 - smooth(0.92, 0.985, r)
    return rgb, a


# ----------------------------------------------------------------- 4. chibaku tensei core
def make_core(n=256):
    x, y, r, th = grid(n)
    R = 0.89
    inside = smooth(R + 0.012, R - 0.012, r)
    z = np.sqrt(np.clip(1.0 - (r / R) ** 2, 0.0, 1.0))
    # swirled fbm surface
    swirl = 3.2 * np.clip(1.0 - r, 0, 1) ** 1.6
    xs = x * np.cos(swirl) - y * np.sin(swirl)
    ys = x * np.sin(swirl) + y * np.cos(swirl)
    nz = fbm(n, 7.0, 51, 5)
    surf = ndi.map_coordinates(nz, [(ys + 1) / 2 * (n - 1), (xs + 1) / 2 * (n - 1)], order=1, mode="mirror")
    crag = fbm(n, 2.2, 52, 3)
    crag = ndi.map_coordinates(crag, [(ys + 1) / 2 * (n - 1), (xs + 1) / 2 * (n - 1)], order=1, mode="mirror")
    base = mix(BLACKV, np.array([0.24, 0.06, 0.44], np.float32), np.clip(surf ** 1.6 * 1.15, 0, 1) * 0.95)
    base = base * (0.78 + 0.45 * crag[..., None])
    # directional light (upper-left), keeps the sphere readable but dark
    light = np.clip(0.55 - 0.45 * (x * 0.55 + y * 0.65) / np.maximum(R, 1e-3), 0.15, 1.0)
    base = base * (0.55 + 0.75 * light[..., None] * z[..., None] ** 0.5)
    # gravitational lensing rings
    rings = 0.16 * gauss(r - 0.42, 0.008) + 0.12 * gauss(r - 0.62, 0.007) + 0.10 * gauss(r - 0.77, 0.006)
    base = base + rings[..., None] * np.array([0.60, 0.30, 1.0], np.float32)
    # fresnel rim glow
    rim = (1.0 - z) ** 3.0
    base = base + (rim * 0.95)[..., None] * np.array([0.72, 0.42, 1.0], np.float32)
    rim_hot = gauss(r - (R - 0.012), 0.012) * 0.85
    base = base + rim_hot[..., None] * np.array([0.92, 0.80, 1.0], np.float32)
    # bright specks
    g = np.random.default_rng(53)
    for _ in range(26):
        px, py = g.uniform(-0.7, 0.7, 2)
        if math.hypot(px, py) > 0.78:
            continue
        sp = gauss(np.hypot(x - px, y - py), g.uniform(0.006, 0.014)) * g.uniform(0.35, 0.9)
        base = base + sp[..., None] * np.array([0.85, 0.7, 1.0], np.float32)
    # outer halo
    halo = np.exp(-(((r - R) / 0.040) ** 2)) * 0.62 * (r >= R - 0.015)
    halo_col = mix(VIOLET, DVIOLET, smooth(R, 0.97, r))
    a = np.maximum(inside, halo)
    rgb = np.where((inside > 0.5)[..., None], base, halo_col)
    # smooth blend at the edge
    rgb = mix(halo_col, np.clip(base, 0, 1), inside)
    a = 1 - (1 - inside) * (1 - halo)
    a *= 1.0 - smooth(0.95, 0.99, r)
    return np.clip(rgb, 0, 1), a


# ----------------------------------------------------------------- 5. debris sheet (2x2 frames, 64 px each)
def debris_frame(seed, size=64, ss=4):
    g = np.random.default_rng(seed)
    S = size * ss
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pal = [(104, 96, 88), (88, 82, 76), (118, 108, 96), (76, 72, 70), (96, 86, 74)]
    # soft dust first
    dust = Image.new("L", (S, S), 0)
    dd = ImageDraw.Draw(dust)
    for _ in range(g.integers(3, 6)):
        cx, cy = g.uniform(18, 46) * ss, g.uniform(18, 46) * ss
        rad = g.uniform(6, 12) * ss
        dd.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=int(g.uniform(40, 80)))
    dust = dust.filter(ImageFilter.GaussianBlur(5 * ss / 2))
    dust_rgba = Image.merge("RGBA", (
        Image.new("L", (S, S), 150), Image.new("L", (S, S), 138), Image.new("L", (S, S), 124), dust))
    canvas.alpha_composite(dust_rgba)
    nrocks = int(g.integers(3, 7))
    for _ in range(nrocks):
        rad = g.uniform(4.0, 10.5)
        cx = g.uniform(5 + rad, 59 - rad)
        cy = g.uniform(5 + rad, 59 - rad)
        nv = int(g.integers(7, 11))
        angs = np.sort(g.uniform(0, 2 * np.pi, nv))
        pts = [(cx + math.cos(a) * rad * g.uniform(0.62, 1.0), cy + math.sin(a) * rad * g.uniform(0.62, 1.0)) for a in angs]
        base = pal[int(g.integers(0, len(pal)))]
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        sp = [(px * ss, py * ss) for px, py in pts]
        ld.polygon(sp, fill=base + (255,))
        mask = layer.split()[3]
        # lit facet (upper left) and shadow facet (lower right)
        lit = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(lit).polygon([(px * ss - 1.4 * ss, py * ss - 1.4 * ss) for px, py in pts],
                                    fill=tuple(min(255, c + 38) for c in base) + (255,))
        lit.putalpha(Image.fromarray(np.minimum(np.array(lit.split()[3]), np.array(mask))))
        shade = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(shade).polygon([(px * ss + 1.6 * ss, py * ss + 1.6 * ss) for px, py in pts],
                                      fill=tuple(max(0, c - 34) for c in base) + (255,))
        shade.putalpha(Image.fromarray(np.minimum(np.array(shade.split()[3]), np.array(mask))))
        layer.alpha_composite(shade)
        # re-clip shade to polygon, then draw the lit facet at ~60% to keep a soft look
        layer2 = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        layer2.paste(layer, (0, 0), mask)
        lit_a = np.array(lit.split()[3]).astype(np.float32) * 0.62
        lit.putalpha(Image.fromarray(lit_a.astype(np.uint8)))
        layer2.alpha_composite(lit)
        ImageDraw.Draw(layer2).line(sp + [sp[0]], fill=(52, 48, 46, 255), width=max(1, int(ss * 0.7)))
        # speckles
        arr = np.array(layer2)
        ys, xs = np.nonzero(arr[..., 3] > 200)
        if len(xs):
            for _ in range(int(rad * 2)):
                k = int(g.integers(0, len(xs)))
                dx, dy = xs[k], ys[k]
                dark = g.random() < 0.6
                col = (60, 56, 54) if dark else (140, 130, 118)
                ImageDraw.Draw(layer2).ellipse([dx - ss * 0.35, dy - ss * 0.35, dx + ss * 0.35, dy + ss * 0.35], fill=col + (255,))
        canvas.alpha_composite(layer2)
    small = canvas.resize((size, size), Image.LANCZOS)
    arr = np.array(small).astype(np.float32)
    # hard 3 px transparent margin so frame sampling never bleeds
    m = 3
    arr[:m, :, 3] = 0
    arr[-m:, :, 3] = 0
    arr[:, :m, 3] = 0
    arr[:, -m:, 3] = 0
    return arr


def make_debris():
    sheet = np.zeros((128, 128, 4), np.float32)
    for i, (ox, oy) in enumerate([(0, 0), (64, 0), (0, 64), (64, 64)]):
        sheet[oy:oy + 64, ox:ox + 64] = debris_frame(100 + i * 7)
    # keep a plausible colour under fully transparent pixels (no black/white fringe)
    a = sheet[..., 3] / 255.0
    rgb = sheet[..., :3] / 255.0
    fill = np.array([0.40, 0.37, 0.33], np.float32)
    rgb = np.where((a < 0.02)[..., None], fill, rgb)
    return rgb, a


# ----------------------------------------------------------------- 6. rinnegan energy
def make_energy(n=256, ss=3):
    S = n * ss
    g = np.random.default_rng(61)
    layers = [
        ((22, 0, 44), 0.55, 15),
        ((120, 50, 215), 0.80, 8),
        ((178, 112, 250), 0.95, 4),
        ((236, 214, 255), 1.00, 2),
    ]
    imgs = [Image.new("RGBA", (S, S), (0, 0, 0, 0)) for _ in layers]
    draws = [ImageDraw.Draw(i) for i in imgs]
    for f in range(5):
        ang = g.uniform(0, 2 * np.pi)
        p0 = np.array([0.5, 0.5]) + 0.42 * np.array([math.cos(ang), math.sin(ang)])
        p1 = np.array([0.5, 0.5]) - 0.42 * np.array([math.cos(ang), math.sin(ang)]) + g.uniform(-0.08, 0.08, 2)
        perp = np.array([-(p1 - p0)[1], (p1 - p0)[0]])
        perp /= np.linalg.norm(perp) + 1e-9
        amp = g.uniform(0.06, 0.15)
        freq = g.uniform(1.0, 2.2)
        ph = g.uniform(0, 2 * np.pi)
        steps = 90
        pts = []
        for i in range(steps + 1):
            t = i / steps
            env = math.sin(math.pi * t)
            p = p0 + (p1 - p0) * t + perp * amp * math.sin(freq * 2 * math.pi * t + ph) * env
            pts.append((p[0] * S, p[1] * S))
        for li, (colr, alpha, width) in enumerate(layers):
            for i in range(steps):
                t = (i + 0.5) / steps
                w = max(1, int(width * ss / 3.0 * (0.25 + 0.75 * math.sin(math.pi * t))))
                draws[li].line([pts[i], pts[i + 1]], fill=colr + (int(255 * alpha * (0.2 + 0.8 * math.sin(math.pi * t))),), width=w)
    # motes
    for _ in range(22):
        px, py = g.uniform(0.15, 0.85, 2)
        rad = g.uniform(0.004, 0.011) * S
        for li, (colr, alpha, _w) in enumerate(layers[1:], start=1):
            rr = rad * (1.6 - 0.35 * li)
            draws[li].ellipse([px * S - rr, py * S - rr, px * S + rr, py * S + rr], fill=colr + (int(255 * alpha * 0.9),))
    # faint Rinnegan ripple rings around the centre
    for rad, al in [(0.16, 70), (0.26, 55), (0.36, 40)]:
        draws[1].ellipse([S * (0.5 - rad), S * (0.5 - rad), S * (0.5 + rad), S * (0.5 + rad)],
                         outline=(150, 80, 235, al), width=max(1, int(ss * 0.8)))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for im, (colr, alpha, width) in zip(imgs, layers):
        blur = im.filter(ImageFilter.GaussianBlur(ss * (0.5 + width / 12.0)))
        out.alpha_composite(blur)
    out = out.resize((n, n), Image.LANCZOS)
    arr = np.array(out).astype(np.float32) / 255.0
    x, y, r, th = grid(n)
    arr[..., 3] *= 1.0 - smooth(0.90, 0.975, r)
    rgb = arr[..., :3]
    a = arr[..., 3]
    # colour under transparent pixels = soft violet (prevents dark fringe)
    rgb = np.where((a < 0.02)[..., None], np.array([0.45, 0.22, 0.80], np.float32), rgb)
    return rgb, a


# ----------------------------------------------------------------- HUD sprite for the origin bars
def make_hud():
    img = np.zeros((256, 256, 4), np.uint8)

    def put(x0, y0, w, h, col, a=255):
        img[y0:y0 + h, x0:x0 + w] = (*col, a)

    # background bar (71 x 5)
    put(0, 0, 71, 5, (8, 6, 14))
    put(1, 1, 69, 3, (40, 34, 56))
    bars = [
        ((150, 80, 235), (214, 168, 255)),   # 0 chakra
        ((110, 190, 255), (220, 242, 255)),  # 1 shinra tensei
        ((190, 80, 225), (240, 170, 255)),   # 2 bansho ten'in
        ((88, 40, 160), (170, 110, 235)),    # 3 chibaku tensei
        ((236, 236, 252), (255, 255, 255)),  # 4 massive shinra tensei
        ((70, 224, 214), (190, 255, 248)),   # 5 universal defense
    ]
    for idx, (c, hi) in enumerate(bars):
        v = 8 + idx * 10
        # rows 2..6 inside the 8 px tile are aligned with the 5 px background bar
        put(0, v + 2, 71, 5, (8, 6, 14))
        for x in range(71):
            tick = (x % 7 == 6)
            col = tuple(int(ch * (0.62 if tick else 1.0)) for ch in c)
            put(x, v + 3, 1, 3, col)
            put(x, v + 3, 1, 1, tuple(int(h * (0.7 if tick else 1.0)) for h in hi))
        # icon (8x8) at x=73: a tiny Rinnegan-like ring
        for yy in range(8):
            for xx in range(8):
                d = math.hypot(xx - 3.5, yy - 3.5)
                if 2.6 <= d <= 3.9 or d <= 0.9:
                    img[v + yy, 73 + xx] = (*hi, 255)
                elif 1.7 <= d < 2.6:
                    img[v + yy, 73 + xx] = (*c, 255)
    path = os.path.join(GUI_DIR, "resource_bar.png")
    Image.fromarray(img, "RGBA").save(path, optimize=True)
    print("wrote", path)


if __name__ == "__main__":
    for name, fn in [
        ("shinra_tensei_wave.png", make_wave),
        ("shinra_tensei_burst.png", make_burst),
        ("bansho_tenin_aura.png", make_aura),
        ("chibaku_tensei_core.png", make_core),
        ("chibaku_tensei_debris.png", make_debris),
        ("rinnegan_energy.png", make_energy),
    ]:
        rgb, a = fn()
        save_rgba(rgb, a, os.path.join(PART_DIR, name))
    make_hud()
