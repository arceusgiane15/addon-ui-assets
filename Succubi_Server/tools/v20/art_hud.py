"""Succubi HUD v3: four round gauges above the hotbar (health, food | thirst, sanity), like v1.0.x but nicer,
and alive:
  - smooth gradient rings with rounded ends on a dark glass disc, 20 steps, pixel-art icon in the middle
  - lose value  -> red flash, the icon shakes, health leaves a pale "damage trail" of what was lost
  - gain value  -> bright glow in the gauge colour, the icon pops
  - low value   -> slow pulsing glow
  - status      -> regeneration sparkles orbit the heart, poison bubbles / green ring, wither smoke / dark ring,
                   absorption gold halo, burning flames, hunger effect sick-green food ring,
                   blood moon turns the sanity ring blood red
  - health number on a small plate under the heart, armor badge left of it while wearing armor
Data comes from the title "shud:..." (see BP scripts/succubi/hud.js); a hidden control keeps the last value
after the title fades, so the script only sends changes."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from registry import step
from common import wjson, CORE_RP, GUNS_RP
import pixel as px
import hud_icons

TEX = 'textures/ui/succubi_hud/'
S4 = 4                   # texels per GUI unit
G = 22                   # gauge diameter (units)
FX = 36                  # effect canvas around a gauge (units)
ICON = 11                # gauge icons (22 x 22 art px); the armor badge keeps its 9-unit shield
ICON_SMALL = 9
STEPS = 20
R_OUT, R_IN = 10.2, 7.0  # ring radii (units)
INK = (10, 5, 9, 255)

STATS = {
    #                light            main             dark
    'health': ((255, 150, 176), (240, 56, 104), (160, 16, 58)),
    'health_poison': ((180, 240, 120), (96, 184, 46), (44, 110, 22)),
    'health_wither': ((150, 144, 156), (80, 74, 88), (36, 32, 42)),
    'food': ((255, 222, 140), (245, 168, 52), (178, 100, 18)),
    'food_sick': ((214, 222, 120), (150, 164, 48), (86, 100, 22)),
    'thirst': ((160, 234, 255), (48, 178, 242), (18, 100, 176)),
    'sanity': ((236, 190, 255), (178, 104, 244), (104, 46, 176)),
    'sanity_blood': ((255, 150, 150), (214, 36, 52), (110, 8, 22)),
}
GLOW = {'health': (255, 70, 120), 'food': (255, 176, 60), 'thirst': (60, 180, 255), 'sanity': (190, 110, 255)}


# ------------------------------------------------------------------------------------------ drawing helpers (supersampled)
def ss_canvas(units, ss=4):
    n = int(units * S4 * ss)
    return Image.new('RGBA', (n, n)), n


def finish_ss(im, units):
    n = int(units * S4)
    return im.resize((n, n), Image.LANCZOS)


def polar_grid(n, units):
    c = n / 2
    y, x = np.mgrid[0:n, 0:n] + 0.5
    dx, dy = x - c, y - c
    r = np.hypot(dx, dy) / n * units          # radius in units
    ang = (np.degrees(np.arctan2(dx, -dy)) + 360) % 360   # 0 at 12 o'clock, clockwise
    return r, ang


def shadow_layer(units=FX):
    """soft drop shadow under a gauge, so it reads on snow and sand too"""
    im, n = ss_canvas(units, 1)
    r, _ = polar_grid(n, units)
    r = np.hypot(*(np.mgrid[0:n, 0:n] + 0.5 - np.array([n / 2 + 1.2 * S4, n / 2]).reshape(2, 1, 1))) / n * units
    a = np.zeros((n, n, 4))
    a[..., 3] = np.clip(1 - (r - R_OUT) / 3.2, 0, 1) ** 1.5 * 150
    return Image.fromarray(a.astype('uint8'), 'RGBA')


def disc_layer(units=G):
    im, n = ss_canvas(units)
    r, ang = polar_grid(n, units)
    a = np.zeros((n, n, 4))
    inside = r <= R_OUT + 0.55
    t = np.clip(r / (R_OUT + 0.55), 0, 1)
    base = np.array([34, 18, 31]) * (1 - t[..., None]) + np.array([14, 7, 13]) * t[..., None]
    # soft top-left light on the glass
    light = np.clip(1 - np.hypot((r * np.sin(np.radians(ang)) + 4) / 9, (r * -np.cos(np.radians(ang)) + 4) / 9), 0, 1) * 18
    a[..., :3] = base + light[..., None]
    a[..., 3] = np.where(inside, 236, 0)
    rim = (r > R_OUT + 0.15) & (r <= R_OUT + 0.55)
    a[rim, :3] = [8, 4, 7]
    a[rim, 3] = 255
    im = Image.fromarray(a.astype('uint8'), 'RGBA')
    return finish_ss(im, units)


def ring_layer(steps, colors, alpha=255, units=G, track=False, glow_edge=True):
    """arc from 12 o'clock clockwise, gradient along the arc, gloss, rounded ends"""
    light, main, dark = colors
    im, n = ss_canvas(units)
    r, ang = polar_grid(n, units)
    a = np.zeros((n, n, 4))
    band = (r >= R_IN) & (r <= R_OUT)
    if track:
        a[band, :3] = [52, 30, 46]
        a[band, 3] = 235
        # subtle ticks every 2 steps
        for k in range(10):
            tick = band & (np.abs(((ang - k * 36 + 180) % 360) - 180) < 0.9)
            a[tick, :3] = [30, 16, 26]
        return finish_ss(Image.fromarray(a.astype('uint8'), 'RGBA'), units)
    span = 360 * steps / STEPS
    mid = (R_IN + R_OUT) / 2
    half = (R_OUT - R_IN) / 2
    on = band & (ang <= span)
    # rounded caps
    for cap_ang in ([0, span] if steps < STEPS else []):
        cx = mid * math.sin(math.radians(cap_ang))
        cy = -mid * math.cos(math.radians(cap_ang))
        px_ = r * np.sin(np.radians(ang))
        py_ = -r * np.cos(np.radians(ang))
        on |= np.hypot(px_ - cx, py_ - cy) <= half
    signed = np.where(ang > span + (360 - span) / 2, ang - 360, ang)      # the start cap sits just before 0 deg
    t = np.clip(signed / max(span, 1e-6), 0, 1)
    c0 = np.array(dark) * 0.45 + np.array(main) * 0.55
    c1 = np.array(main) * 0.75 + np.array(light) * 0.25
    main_c = c0 * (1 - t[..., None]) + c1 * t[..., None]
    radial = np.clip((r - R_IN) / (R_OUT - R_IN), 0, 1)
    shade = 1.12 - 0.35 * np.abs(radial - 0.35)            # gloss band a little outside the middle
    col = main_c * shade[..., None]
    gloss = on & (np.abs(radial - 0.72) < 0.1)
    col[gloss] = col[gloss] * 0.5 + np.array(light) * 0.5
    a[..., :3] = np.clip(col, 0, 255)
    a[..., 3] = np.where(on, alpha, 0)
    # glowing leading edge
    if glow_edge and 0 < steps < STEPS:
        lead = on & (np.abs(ang - span) < 7) & band
        a[lead, :3] = a[lead, :3] * 0.4 + np.array([255, 255, 255]) * 0.6 * 0.6 + np.array(light) * 0.4 * 0.6
    im = Image.fromarray(a.astype('uint8'), 'RGBA')
    return finish_ss(im, units)


def glow_ring(color, units=FX, r0=R_IN - 1.5, r1=R_OUT + 3.5, strength=210):
    im, n = ss_canvas(units, 1)
    r, _ = polar_grid(n, units)
    mid, half = (r0 + r1) / 2, (r1 - r0) / 2
    a = np.zeros((n, n, 4))
    k = np.clip(1 - np.abs(r - mid) / half, 0, 1) ** 1.6
    a[..., :3] = color
    a[..., 3] = k * strength
    return Image.fromarray(a.astype('uint8'), 'RGBA')


def halo(color, units=FX, radius=R_OUT + 2.2, width=0.9):
    im, n = ss_canvas(units)
    r, ang = polar_grid(n, units)
    a = np.zeros((n, n, 4))
    k = np.clip(1 - np.abs(r - radius) / width, 0, 1)
    a[..., :3] = color
    a[..., 3] = k * 255
    # soft outer bloom
    b = np.clip(1 - np.abs(r - radius) / (width * 4), 0, 1) ** 2 * 90
    a[..., 3] = np.maximum(a[..., 3], b)
    return finish_ss(Image.fromarray(a.astype('uint8'), 'RGBA'), units)


# ------------------------------------------------------------------------------------------ flip books (horizontal strips)
def strip(frames):
    w, h = frames[0].size
    out = Image.new('RGBA', (w * len(frames), h))
    for i, f in enumerate(frames):
        out.alpha_composite(f, (i * w, 0))
    return out


def star(d, cx, cy, s, col):
    d.polygon([(cx, cy - s), (cx + s * 0.28, cy - s * 0.28), (cx + s, cy), (cx + s * 0.28, cy + s * 0.28),
               (cx, cy + s), (cx - s * 0.28, cy + s * 0.28), (cx - s, cy), (cx - s * 0.28, cy - s * 0.28)], fill=col)


def fb_sparkles(n=12):
    """regeneration: four sparkles orbiting the ring"""
    frames = []
    size = FX * S4
    c = size / 2
    for f in range(n):
        im = Image.new('RGBA', (size * 2, size * 2))
        d = ImageDraw.Draw(im)
        for i in range(4):
            a = math.radians(f * 360 / n / 2 + i * 90)
            rr = (R_OUT + 1.6) * S4 * 2
            x, y = c * 2 + rr * math.sin(a), c * 2 - rr * math.cos(a)
            tw = 0.6 + 0.4 * math.sin((f + i * 3) / n * 2 * math.pi)
            star(d, x, y, 2.6 * S4 * 2 * tw, (255, 236, 246, 255))
            star(d, x, y, 1.2 * S4 * 2 * tw, (255, 120, 180, 255))
            for k in range(1, 4):                          # trail
                b = a - math.radians(k * 7)
                tx, ty = c * 2 + rr * math.sin(b), c * 2 - rr * math.cos(b)
                s = (3 - k) * 0.35 * S4 * 2
                d.ellipse([tx - s, ty - s, tx + s, ty + s], fill=(255, 170, 210, 200 - k * 50))
        frames.append(im.resize((size, size), Image.LANCZOS))
    return strip(frames)


def fb_bubbles(color, n=10, seed=3):
    """poison / hunger: little bubbles rising over the gauge"""
    rng = np.random.RandomState(seed)
    bubbles = [(rng.uniform(-7, 7), rng.uniform(0, 1), rng.uniform(0.7, 1.6)) for _ in range(9)]
    size = FX * S4
    frames = []
    for f in range(n):
        im = Image.new('RGBA', (size * 2, size * 2))
        d = ImageDraw.Draw(im)
        for bx, phase, br in bubbles:
            t = (phase + f / n) % 1.0
            x = size + bx * S4 * 2 + math.sin(t * 6 + bx) * 1.5 * S4
            y = size + (9 - t * 20) * S4 * 2
            rr = br * S4 * 2 * (0.6 + 0.4 * t)
            alpha = int(230 * math.sin(t * math.pi))
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=color + (alpha,), width=max(2, int(S4 * 0.8)))
            d.ellipse([x - rr * 0.35 - rr * 0.3, y - rr * 0.6, x - rr * 0.3 + rr * 0.1, y - rr * 0.2], fill=(255, 255, 255, alpha))
        frames.append(im.resize((size, size), Image.LANCZOS))
    return strip(frames)


def fb_smoke(n=10, seed=5):
    """wither: dark wisps rising"""
    rng = np.random.RandomState(seed)
    puffs = [(rng.uniform(-8, 8), rng.uniform(0, 1), rng.uniform(1.8, 3.2)) for _ in range(8)]
    size = FX * S4
    frames = []
    for f in range(n):
        im = Image.new('RGBA', (size, size))
        d = ImageDraw.Draw(im)
        for bx, phase, br in puffs:
            t = (phase + f / n) % 1.0
            x = size / 2 + (bx + math.sin(t * 5 + bx) * 1.2) * S4
            y = size / 2 + (8 - t * 18) * S4
            rr = br * S4 * (0.5 + t)
            alpha = int(170 * math.sin(t * math.pi))
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(24, 18, 28, alpha))
        frames.append(im.filter(ImageFilter.GaussianBlur(S4 * 0.8)))
    return strip(frames)


def fb_flames(n=8, seed=9):
    """burning: flames licking around the ring"""
    rng = np.random.RandomState(seed)
    size = FX * S4
    tongues = [(i * 360 / 14 + rng.uniform(-8, 8), rng.uniform(0, 1), rng.uniform(2.2, 4.2)) for i in range(14)]
    frames = []
    for f in range(n):
        im = Image.new('RGBA', (size * 2, size * 2))
        d = ImageDraw.Draw(im)
        c = size
        for a0, phase, ln in tongues:
            t = (phase + f / n) % 1.0
            h = ln * (0.55 + 0.45 * math.sin(t * 2 * math.pi)) * S4 * 2
            a = math.radians(a0)
            base_r = (R_OUT + 0.3) * S4 * 2
            bx, by = c + base_r * math.sin(a), c - base_r * math.cos(a)
            tipx, tipy = c + (base_r + h) * math.sin(a), c - (base_r + h) * math.cos(a) - h * 0.35
            w = 1.3 * S4 * 2
            nx, ny = math.cos(a) * w, math.sin(a) * w
            for scale, col in ((1.0, (255, 110, 30, 220)), (0.55, (255, 220, 90, 240))):
                d.polygon([(bx - nx * scale, by - ny * scale), (bx + (tipx - bx) * scale, by + (tipy - by) * scale),
                           (bx + nx * scale, by + ny * scale)], fill=col)
        frames.append(im.resize((size, size), Image.LANCZOS))
    return strip(frames)


def fb_drip(n=10):
    """heart almost gone: blood drops falling from the tip"""
    size = FX * S4
    frames = []
    for f in range(n):
        im = Image.new('RGBA', (size, size))
        d = ImageDraw.Draw(im)
        for k, (dx, phase) in enumerate(((-0.6, 0.0), (0.7, 0.5))):
            t = (phase + f / n) % 1.0
            x = size / 2 + dx * S4
            y = size / 2 + (4.5 + t * 9) * S4
            rr = (0.55 + 0.25 * (1 - t)) * S4
            a = int(255 * (1 - t) ** 0.6)
            d.ellipse([x - rr, y - rr * 1.4, x + rr, y + rr], fill=(170, 10, 30, a))
            d.ellipse([x - rr * 0.4, y - rr * 0.9, x, y - rr * 0.3], fill=(255, 120, 130, a))
        frames.append(im)
    return strip(frames)


def fb_steam(n=10, seed=4):
    """water almost gone: heat haze rising from the dry drop"""
    rng = np.random.RandomState(seed)
    wisps = [(rng.uniform(-3.5, 3.5), rng.uniform(0, 1)) for _ in range(4)]
    size = FX * S4
    frames = []
    for f in range(n):
        im = Image.new('RGBA', (size, size))
        d = ImageDraw.Draw(im)
        for wx, phase in wisps:
            t = (phase + f / n) % 1.0
            pts = []
            for k in range(6):
                yy = size / 2 + (-3 - t * 10 - k * 0.9) * S4
                xx = size / 2 + (wx + math.sin(t * 6 + k * 0.9) * 0.9) * S4
                pts.append((xx, yy))
            d.line(pts, fill=(255, 236, 210, int(150 * math.sin(t * math.pi))), width=int(S4 * 0.6))
        frames.append(im.filter(ImageFilter.GaussianBlur(S4 * 0.25)))
    return strip(frames)


def fb_tendrils(n=12, seed=6):
    """sanity almost gone: shadow hands creeping over the ring from outside"""
    rng = np.random.RandomState(seed)
    arms = [(i * 90 + 45 + rng.uniform(-15, 15), rng.uniform(0, 1)) for i in range(4)]
    size = FX * S4
    frames = []
    for f in range(n):
        im = Image.new('RGBA', (size * 2, size * 2))
        d = ImageDraw.Draw(im)
        c = size
        for a0, phase in arms:
            t = (phase + f / n) % 1.0
            reach = 0.5 + 0.5 * math.sin(t * 2 * math.pi)             # creeps in and pulls back
            a = math.radians(a0 + math.sin(t * 4) * 6)
            r_out, r_in = (R_OUT + 3.2) * S4 * 2, (R_IN + 0.8 + (1 - reach) * 3.2) * S4 * 2
            pts = []
            for k in range(9):
                u = k / 8
                rr = r_out + (r_in - r_out) * u
                wob = math.sin(u * 7 + t * 9) * 0.12
                pts.append((c + rr * math.sin(a + wob), c - rr * math.cos(a + wob)))
            for k in range(len(pts) - 1):
                w = int((1.3 - 0.9 * k / 8) * S4 * 2)
                d.line([pts[k], pts[k + 1]], fill=(14, 2, 20, 215), width=max(2, w))
            tip = pts[-1]
            for fdeg in (-40, 0, 40):                                  # claw fingers
                fa = a + math.radians(180 + fdeg)
                d.line([tip, (tip[0] + math.sin(fa) * S4 * 1.6, tip[1] - math.cos(fa) * S4 * 1.6)], fill=(14, 2, 20, 215), width=int(S4 * 0.6))
        frames.append(im.resize((size, size), Image.LANCZOS))
    return strip(frames)


def fb_flies(n=12):
    """food gone: two flies buzzing round the bare bone"""
    size = FX * S4
    frames = []
    for f in range(n):
        im = Image.new('RGBA', (size, size))
        d = ImageDraw.Draw(im)
        for k in range(2):
            a = f / n * 2 * math.pi * (1 if k == 0 else -1) + k * 2.2
            x = size / 2 + math.cos(a) * 6.5 * S4
            y = size / 2 + math.sin(a * 2) * 3.5 * S4 - 2 * S4
            d.ellipse([x - S4 * 0.7, y - S4 * 0.6, x + S4 * 0.7, y + S4 * 0.6], fill=(20, 20, 26, 255))
            wing = S4 * (0.9 if f % 2 else 0.5)
            d.ellipse([x - wing, y - S4 * 1.5, x + wing * 0.3, y - S4 * 0.3], fill=(220, 236, 255, 170))
        frames.append(im)
    return strip(frames)


def dry_cracks():
    """thirst almost gone: the disc dries out and cracks"""
    im, n = ss_canvas(G)
    r, ang = polar_grid(n, G)
    a = np.zeros((n, n, 4))
    inside = r <= R_IN - 0.2
    a[inside, :3] = [96, 70, 44]
    a[inside, 3] = 120
    out = Image.fromarray(a.astype('uint8'), 'RGBA')
    d = ImageDraw.Draw(out)
    rng = np.random.RandomState(12)
    c = n / 2
    for k in range(7):
        a0 = k * 51 + rng.uniform(-10, 10)
        pts = [(c, c)]
        rr = 0
        while rr < (R_IN - 0.4) * S4 * 4:
            rr += S4 * 4 * rng.uniform(0.8, 1.6)
            aa = math.radians(a0 + rng.uniform(-18, 18))
            pts.append((c + rr * math.sin(aa), c - rr * math.cos(aa)))
        d.line(pts, fill=(40, 26, 16, 220), width=S4 * 2)
    return finish_ss(out, G)


def madness_swirl():
    """sanity almost gone: a dark violet swirl fills the disc"""
    im, n = ss_canvas(G)
    r, ang = polar_grid(n, G)
    a = np.zeros((n, n, 4))
    inside = r <= R_IN - 0.1
    sw = (np.sin(np.radians(ang * 3) + r * 1.4) * 0.5 + 0.5)
    a[..., 0] = 60 * sw + 20
    a[..., 1] = 8
    a[..., 2] = 80 * sw + 30
    a[..., 3] = np.where(inside, 150 + 60 * sw, 0)
    return finish_ss(Image.fromarray(a.astype('uint8'), 'RGBA'), G)


def trail_layer(steps):
    return ring_layer(steps, ((255, 255, 255), (255, 214, 226), (255, 190, 206)), alpha=235, glow_edge=False)


# ------------------------------------------------------------------------------------------ icons (pixel art, 18 art px)
D = 2


def _shade_shape(mask, light, main, dark):
    w, h = mask.size
    im = px.canvas(w, h)
    p, m = im.load(), mask.load()
    for y in range(h):
        for x in range(w):
            if m[x, y][3] > 127:
                t = (x * 0.45 + y * 0.8) / (w * 0.45 + h * 0.8)
                c = px.mix(light, main, min(1, t * 2)) if t < 0.5 else px.mix(main, dark, (t - 0.5) * 2)
                p[x, y] = px.rgba(c)
    return px.outline(im, INK)


def icon_heart(light, main, dark):
    s = ICON * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.ellipse([1, 2, 9, 10], fill=(255, 255, 255, 255))
    d.ellipse([8, 2, 16, 10], fill=(255, 255, 255, 255))
    d.polygon([(1, 7), (16, 7), (8.5, 16)], fill=(255, 255, 255, 255))
    im = _shade_shape(m, light, main, dark)
    q = im.load()
    for (x, y) in ((4, 4), (5, 4), (4, 5)):
        q[x, y] = px.WHITE
    return im


def icon_drumstick():
    s = ICON * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.ellipse([6, 1, 16, 11], fill=(255, 255, 255, 255))
    d.polygon([(7, 8), (10, 11), (5, 13)], fill=(255, 255, 255, 255))
    meat = _shade_shape(m, (255, 196, 120), (205, 110, 45), (120, 56, 20))
    bone = px.canvas(s, s)
    b = ImageDraw.Draw(bone)
    b.line([(3, 14), (7, 10)], fill=(236, 226, 214, 255), width=2)
    b.ellipse([1, 13, 4, 16], fill=(236, 226, 214, 255))
    b.ellipse([2, 14, 5, 17], fill=(236, 226, 214, 255))
    bone = px.outline(bone, INK)
    bone.alpha_composite(meat)
    q = bone.load()
    for (x, y) in ((9, 3), (10, 3), (9, 4)):
        q[x, y] = (255, 236, 200, 255)
    return bone


def icon_drop():
    s = ICON * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.ellipse([3, 6, 14, 17], fill=(255, 255, 255, 255))
    d.polygon([(8.5, 0), (3.2, 10), (13.8, 10)], fill=(255, 255, 255, 255))
    im = _shade_shape(m, (190, 240, 255), (51, 181, 240), (18, 96, 160))
    q = im.load()
    for (x, y) in ((6, 9), (6, 10), (7, 8), (6, 11)):
        q[x, y] = px.WHITE
    return im


def icon_brain():
    rows = [
        "....oooo.oooo.....",
        "..ooLLLLoLLLLoo...",
        ".oLLLMMLoLMMLLLo..",
        "oLLMFFMMoMMFFMMLo.",
        "oLMMMMFMoMFMMMMDo.",
        "oLMFFMMMoMMMFFMDo.",
        "oMMMMFFMoMFFMMMDo.",
        "oMFMMMMMoMMMMMFDo.",
        "oMMFFMMMoMMFFMDDo.",
        ".oMMMMFMoMFMMDDo..",
        ".oDMMMMMoMMMMDDo..",
        "..oDDMMMoMMDDDo...",
        "...ooDDDoDDDoo....",
        ".....ooo.ooo......",
        "..................",
    ]
    pal = {'o': INK, 'L': (255, 206, 240), 'M': (220, 130, 226), 'D': (150, 70, 176), 'F': (130, 52, 158)}
    im = px.from_rows(rows, pal)
    out = px.canvas(18, 18)
    out.alpha_composite(im, (0, 2))
    return out


def icon_shield():
    s = ICON_SMALL * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.polygon([(2, 2), (15, 2), (15, 8), (8.5, 16), (2, 8)], fill=(255, 255, 255, 255))
    im = _shade_shape(m, (236, 240, 248), (160, 170, 188), (86, 94, 112))
    d2 = ImageDraw.Draw(im)
    d2.line([(8, 3), (8, 14)], fill=(236, 240, 248, 255))
    d2.line([(9, 3), (9, 14)], fill=(110, 118, 136, 255))
    return im


BIG = {
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['.###.', '#...#', '....#', '..##.', '....#', '#...#', '.###.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['..##.', '.#...', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'],
}


def digit_big(ch):
    im = px.canvas(7, 9)
    q = im.load()
    for y, r in enumerate(BIG[ch]):
        for x, c in enumerate(r):
            if c == '#':
                q[x + 1, y + 1] = px.WHITE
    return px.outline(im, INK)


def plate(w, h):
    im = Image.new('RGBA', (w * S4, h * S4))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S4 - 1, h * S4 - 1], radius=h * S4 // 2, fill=(10, 5, 9, 235))
    d.rounded_rectangle([2, 2, w * S4 - 3, h * S4 - 3], radius=h * S4 // 2 - 2, outline=(90, 40, 70, 255), width=2)
    return im


def draw_all(rp):
    d = os.path.join(rp, TEX)
    os.makedirs(d, exist_ok=True)
    disc_layer().save(os.path.join(d, 'disc.png'))
    shadow_layer().save(os.path.join(d, 'shadow.png'))
    ring_layer(0, STATS['health'], track=True).save(os.path.join(d, 'track.png'))
    for stat, cols in STATS.items():
        for n in range(1, STEPS + 1):
            ring_layer(n, cols).save(os.path.join(d, f'ring_{stat}_{n:02d}.png'))
    for n in range(1, STEPS + 1):
        trail_layer(n).save(os.path.join(d, f'trail_{n:02d}.png'))
    for k, c in GLOW.items():
        glow_ring(c).save(os.path.join(d, f'glow_{k}.png'))
    glow_ring((255, 40, 40), strength=240).save(os.path.join(d, 'glow_hurt.png'))
    glow_ring((255, 255, 255), strength=170).save(os.path.join(d, 'glow_white.png'))
    halo((255, 214, 90)).save(os.path.join(d, 'halo_absorb.png'))
    halo((214, 36, 52)).save(os.path.join(d, 'halo_blood.png'))
    fb_sparkles().save(os.path.join(d, 'fx_sparkles.png'))
    fb_bubbles((150, 235, 80)).save(os.path.join(d, 'fx_bubbles_poison.png'))
    fb_bubbles((200, 214, 90), seed=8).save(os.path.join(d, 'fx_bubbles_hunger.png'))
    fb_smoke().save(os.path.join(d, 'fx_smoke.png'))
    fb_flames().save(os.path.join(d, 'fx_flames.png'))
    for key, tiers in hud_icons.all_icons(STATS).items():
        for t, im in tiers.items():
            px.save(im, os.path.join(d, f'icon_{key}_{t}.png'), 2)
    px.save(icon_shield(), os.path.join(d, 'icon_armor.png'), 2)
    fb_drip().save(os.path.join(d, 'fx_drip.png'))
    fb_steam().save(os.path.join(d, 'fx_steam.png'))
    fb_tendrils().save(os.path.join(d, 'fx_tendrils.png'))
    fb_flies().save(os.path.join(d, 'fx_flies.png'))
    dry_cracks().save(os.path.join(d, 'disc_dry.png'))
    madness_swirl().save(os.path.join(d, 'disc_madness.png'))
    glow_ring((200, 0, 30), r0=0.5, r1=R_IN + 0.5, strength=150).save(os.path.join(d, 'disc_bleed.png'))
    for ch in '0123456789':
        px.save(digit_big(ch), os.path.join(d, f'num_{ch}.png'), 2)
    plate(15, 7).save(os.path.join(d, 'plate_hp.png'))
    plate(19, 9).save(os.path.join(d, 'plate_armor.png'))


FLIPBOOKS = {'fx_sparkles': 12, 'fx_bubbles_poison': 10, 'fx_bubbles_hunger': 10, 'fx_smoke': 10, 'fx_flames': 8,
             'fx_drip': 10, 'fx_steam': 10, 'fx_tendrils': 12, 'fx_flies': 12}


# ------------------------------------------------------------------------------------------ JSON UI
NS = 'succubi_hud'
DATA = 'succubi_hud_data'
P = '#preserved_text'


def has(tok):
    return f"(not (({P} - '{tok}') = {P}))"


def hasnt(tok):
    return f"(({P} - '{tok}') = {P})"


def vis(expr):
    return [{"binding_type": "view", "source_control_name": DATA, "source_property_name": f"({expr})",
             "target_property_name": "#visible"}]


def img(tex, size, offset, layer, expr=None, anchor='center', **kw):
    c = {"type": "image", "texture": TEX + tex, "size": list(size), "offset": list(offset), "layer": layer,
         "anchor_from": anchor, "anchor_to": anchor}
    if expr:
        c["bindings"] = vis(expr)
    c.update(kw)
    return c


def fx(tex, expr, layer, fps=12, alpha=None):
    frames = FLIPBOOKS[tex]
    n = FX * S4
    c = img(tex, (FX, FX), (0, 0), layer, expr, uv_size=[n, n], uv=f"@{NS}.fb_{tex}")
    if alpha:
        c["alpha"] = alpha
    return c


GAUGES = [
    # key, token letter, x (left edge in root), fill variants [(stat key, condition)], icon sets [(icon key, condition)], flag letter
    ('health', 'H', 0, [('health', 'Pn'), ('health_poison', 'Pp'), ('health_wither', 'Pw')],
     [('health', 'Pn'), ('health_poison', 'Pp'), ('health_wither', 'Pw')], 'h'),
    ('food', 'F', 25, [('food', '!Qh'), ('food_sick', 'Qh')], [('food', '!Qh'), ('food_sick', 'Qh')], 'f'),
    ('thirst', 'T', 69, [('thirst', None)], [('thirst', None)], 't'),
    ('sanity', 'S', 94, [('sanity', '!Eb'), ('sanity_blood', 'Eb')], [('sanity', None)], 's'),
]
TIERS = range(5)          # V<flag><tier>: 4 full ... 0 almost gone (sent by hud.js)


def idle_anims(key, tier):
    """the icon's own motion at each stage: the heart beats faster, the stomach growls, the brain twitches"""
    if key == 'health':
        return [f"@{NS}.beat{tier}_a"]
    if key == 'food' and tier <= 1:
        return [f"@{NS}.growl_wait"]
    if key == 'thirst' and tier <= 1:
        return [f"@{NS}.wobble_a"]
    if key == 'sanity' and tier <= 3:
        return [f"@{NS}.mind{tier}_a"]
    return []

ROOT_W = 94 + G


def cond(tok):
    if tok is None:
        return None
    return hasnt(tok[1:]) if tok.startswith('!') else has(tok)


def and_(*xs):
    xs = [x for x in xs if x]
    return ' and '.join(xs) if xs else None


def gauge(key, letter, x, fills, icons, f):
    ctl = [{"shadow": img('shadow', (FX, FX), (0, 0), 0)},
           {"disc": img('disc', (G, G), (0, 0), 1)},
           {"track": img('track', (G, G), (0, 0), 2)}]
    if key == 'health':
        for n in range(1, STEPS + 1):
            ctl.append({f"trail_{n:02d}": img(f'trail_{n:02d}', (G, G), (0, 0), 3, and_(has('-h'), has(f'G{n:02d}')),
                                              alpha=f"@{NS}.trail_fade")})
    for stat, tok in fills:
        for n in range(1, STEPS + 1):
            ctl.append({f"ring_{stat}_{n:02d}": img(f'ring_{stat}_{n:02d}', (G, G), (0, 0), 4, and_(has(f'{letter}{n:02d}'), cond(tok)))})
    # glows (under the disc edge -> layer 0 so they bloom around it)
    ctl.append({"glow_low": img(f'glow_{key}', (FX, FX), (0, 0), 0, has(f'!{f}'), alpha=f"@{NS}.pulse_slow_out")})
    ctl.append({"glow_gain": img(f'glow_{key}', (FX, FX), (0, 0), 0, and_(has(f'+{f}'), hasnt(f'-{f}')), alpha=f"@{NS}.pulse_fast_out")})
    ctl.append({"glow_gain_white": img('glow_white', (FX, FX), (0, 0), 5, and_(has(f'+{f}'), hasnt(f'-{f}')), alpha=f"@{NS}.flash_out")})
    ctl.append({"glow_hurt": img('glow_hurt', (FX, FX), (0, 0), 0, has(f'-{f}'), alpha=f"@{NS}.pulse_fast_out")})
    # status effects
    if key == 'health':
        ctl.append({"halo_absorb": img('halo_absorb', (FX, FX), (0, 0), 1, has('Ea'), alpha=f"@{NS}.pulse_slow_out")})
        ctl.append({"fx_regen": fx('fx_sparkles', has('Er'), 7)})
        ctl.append({"fx_poison": fx('fx_bubbles_poison', has('Pp'), 7)})
        ctl.append({"fx_wither": fx('fx_smoke', has('Pw'), 7)})
        ctl.append({"fx_fire": fx('fx_flames', has('Ef'), 8)})
    if key == 'food':
        ctl.append({"fx_hunger": fx('fx_bubbles_hunger', has('Qh'), 7)})
    if key == 'sanity':
        ctl.append({"halo_blood": img('halo_blood', (FX, FX), (0, 0), 1, has('Eb'), alpha=f"@{NS}.pulse_slow_out")})
    # stage overlays: bleeding heart, dry cracked disc, madness swirl + shadow hands, flies on the bare bone
    low = lambda t: has(f'V{f}{t}')
    if key == 'health':
        ctl.append({"bleed": img('disc_bleed', (FX, FX), (0, 0), 3, f"{low(1)} or {low(0)}", alpha=f"@{NS}.pulse_fast_out")})
        ctl.append({"fx_drip": fx('fx_drip', f"{low(1)} or {low(0)}", 8)})
    if key == 'food':
        ctl.append({"fx_flies": fx('fx_flies', low(0), 8)})
    if key == 'thirst':
        ctl.append({"dry": img('disc_dry', (G, G), (0, 0), 3, f"{low(1)} or {low(0)}")})
        ctl.append({"fx_steam": fx('fx_steam', f"{low(1)} or {low(0)}", 8)})
    if key == 'sanity':
        ctl.append({"swirl": img('disc_madness', (G, G), (0, 0), 3, f"{low(1)} or {low(0)}", alpha=f"@{NS}.pulse_slow_out")})
        ctl.append({"fx_tendrils": fx('fx_tendrils', f"{low(1)} or {low(0)}", 5)})
    # icon for every stage: still (its own idle motion) / shaking (lost value) / popping (gained value)
    for icon_key, tok in icons:
        base = cond(tok)
        for t in TIERS:
            tex = f'icon_{icon_key}_{t}'
            at = and_(base, has(f'V{f}{t}'))
            ctl.append({f"{tex}": img(tex, (ICON, ICON), (0, 0), 6, and_(at, hasnt(f'-{f}'), hasnt(f'+{f}')),
                                      **({"anims": idle_anims(key, t)} if idle_anims(key, t) else {}),
                                      **({"alpha": f"@{NS}.flicker_a"} if key == 'sanity' and t == 0 else {}))})
            ctl.append({f"{tex}_shake": img(tex, (ICON, ICON), (0, 0), 6, and_(at, has(f'-{f}')), anims=[f"@{NS}.shake_a"])})
            ctl.append({f"{tex}_pop": img(tex, (ICON, ICON), (0, 0), 6, and_(at, has(f'+{f}'), hasnt(f'-{f}')), anims=[f"@{NS}.pop_a"])})
    if key == 'health':
        # health number on a plate under the heart: ones / tens / hundreds, leading zeros hidden
        ctl.append({"plate": img('plate_hp', (15, 7), (0, 9.5), 9)})
        # centred on the plate: 3 digits at -3.5 / 0 / +3.5, 2 digits at -1.75 / +1.75, 1 digit at 0
        three, two, one = hasnt('X0'), and_(has('X0'), hasnt('Y0')), and_(has('X0'), has('Y0'))
        slots = [('Z', three, 3.5), ('Z', two, 1.75), ('Z', one, 0), ('Y', three, 0), ('Y', two, -1.75), ('X', three, -3.5)]
        for i, (ld, count, xoff) in enumerate(slots):
            for dgt in range(10):
                if ld == 'X' and dgt == 0:
                    continue
                ctl.append({f"n{i}_{ld}{dgt}": img(f'num_{dgt}', (3.5, 4.5), (xoff, 9.5), 10, and_(has(f'{ld}{dgt}'), count))})
    body = {"type": "panel", "size": [G, G], "offset": [x, 0], "anchor_from": "top_left", "anchor_to": "top_left", "controls": ctl}
    if key == 'thirst':
        body["bindings"] = vis(hasnt('Txx'))
    if key == 'sanity':
        body["bindings"] = vis(hasnt('Sxx'))
    return body


def hud_json():
    root_ctl = [{g[0]: gauge(*g)} for g in GAUGES]
    armor = {"type": "panel", "size": [19, 9], "offset": [-21, 6.5], "anchor_from": "top_left", "anchor_to": "top_left",
             "bindings": vis(has('Ay')),
             "controls": [{"plate": img('plate_armor', (19, 9), (0, 0), 1, anchor='top_left')},
                          {"icon": img('icon_armor', (ICON_SMALL, ICON_SMALL), (0, 0), 3, anchor='top_left')}]}
    for dgt in range(10):
        if dgt:
            armor["controls"].append({f"t{dgt}": img(f'num_{dgt}', (3.5, 4.5), (10, 2.25), 4, has(f'B{dgt}'), anchor='top_left')})
        armor["controls"].append({f"o{dgt}": img(f'num_{dgt}', (3.5, 4.5), (13.5, 2.25), 4, has(f'C{dgt}'), anchor='top_left')})
    root_ctl.append({"armor": armor})
    root = {"type": "panel", "anchor_from": "bottom_middle", "anchor_to": "bottom_middle", "offset": [0, -31],
            "size": [ROOT_W, G], "layer": 30, "controls": root_ctl,
            "bindings": [{"binding_name": "#show_survival_ui", "binding_name_override": "#visible"}]}
    shown = {"type": "panel", "size": ["100%", "100%"], "controls": [{"hud_root": root}], "bindings": vis(hasnt('shud:off'))}
    data = {"type": "panel", "size": [0, 0], "bindings": [
        {"binding_name": "#hud_title_text_string"},
        {"binding_name": "#hud_title_text_string", "binding_name_override": P, "binding_condition": "visibility_changed"},
        {"binding_type": "view",
         "source_property_name": f"((not (#hud_title_text_string = {P})) and (not ((#hud_title_text_string - 'shud:') = #hud_title_text_string)))",
         "target_property_name": "#visible"}]}
    anims = {
        "pulse_slow_out": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.7, "from": 1.0, "to": 0.2, "next": f"@{NS}.pulse_slow_in"},
        "pulse_slow_in": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.7, "from": 0.2, "to": 1.0, "next": f"@{NS}.pulse_slow_out"},
        "pulse_fast_out": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.18, "from": 1.0, "to": 0.35, "next": f"@{NS}.pulse_fast_in"},
        "pulse_fast_in": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.18, "from": 0.35, "to": 1.0, "next": f"@{NS}.pulse_fast_out"},
        "flash_out": {"anim_type": "alpha", "easing": "out_quad", "duration": 0.3, "from": 0.9, "to": 0.0, "next": f"@{NS}.flash_in"},
        "flash_in": {"anim_type": "alpha", "easing": "linear", "duration": 0.3, "from": 0.0, "to": 0.9, "next": f"@{NS}.flash_out"},
        "trail_fade": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.35, "from": 0.95, "to": 0.45, "next": f"@{NS}.trail_back"},
        "trail_back": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.35, "from": 0.45, "to": 0.95, "next": f"@{NS}.trail_fade"},
        # icon shake: left-right jitter around the centre
        "shake_a": {"anim_type": "offset", "easing": "linear", "duration": 0.04, "from": [0, 0], "to": [1.2, -0.4], "next": f"@{NS}.shake_b"},
        "shake_b": {"anim_type": "offset", "easing": "linear", "duration": 0.08, "from": [1.2, -0.4], "to": [-1.2, 0.4], "next": f"@{NS}.shake_c"},
        "shake_c": {"anim_type": "offset", "easing": "linear", "duration": 0.04, "from": [-1.2, 0.4], "to": [0, 0], "next": f"@{NS}.shake_a"},
        # icon pop: grows and settles
        "pop_a": {"anim_type": "size", "easing": "out_back", "duration": 0.22, "from": [ICON, ICON], "to": [ICON * 1.45, ICON * 1.45], "next": f"@{NS}.pop_b"},
        "pop_b": {"anim_type": "size", "easing": "in_out_sine", "duration": 0.3, "from": [ICON * 1.45, ICON * 1.45], "to": [ICON, ICON], "next": f"@{NS}.pop_a"},
    }
    # heart beats: slow and calm when full, racing when almost gone (lub-dub + rest)
    for t, (period, amp) in enumerate(((0.32, 1.7), (0.45, 1.5), (0.6, 1.3), (0.8, 1.1), (1.05, 0.9))):
        big = [ICON + amp, ICON + amp]
        mid = [ICON + amp * 0.55, ICON + amp * 0.55]
        rest = max(0.01, period - 0.26)
        anims[f"beat{t}_a"] = {"anim_type": "size", "easing": "out_quad", "duration": 0.06, "from": [ICON, ICON], "to": big, "next": f"@{NS}.beat{t}_b"}
        anims[f"beat{t}_b"] = {"anim_type": "size", "easing": "in_quad", "duration": 0.08, "from": big, "to": [ICON, ICON], "next": f"@{NS}.beat{t}_c"}
        anims[f"beat{t}_c"] = {"anim_type": "size", "easing": "out_quad", "duration": 0.05, "from": [ICON, ICON], "to": mid, "next": f"@{NS}.beat{t}_d"}
        anims[f"beat{t}_d"] = {"anim_type": "size", "easing": "in_quad", "duration": 0.07, "from": mid, "to": [ICON, ICON], "next": f"@{NS}.beat{t}_e"}
        anims[f"beat{t}_e"] = {"anim_type": "wait", "duration": rest, "next": f"@{NS}.beat{t}_a"}
    # stomach growl: quiet, then a short rumble
    anims["growl_wait"] = {"anim_type": "wait", "duration": 1.3, "next": f"@{NS}.growl_a"}
    for i, (fr, to, nxt) in enumerate((([0, 0], [0.9, 0.3], 'growl_b'), ([0.9, 0.3], [-0.9, -0.3], 'growl_c'), ([-0.9, -0.3], [0.7, 0], 'growl_d'),
                                        ([0.7, 0], [-0.5, 0.2], 'growl_e'), ([-0.5, 0.2], [0, 0], 'growl_wait'))):
        anims["growl_" + "abcde"[i]] = {"anim_type": "offset", "easing": "linear", "duration": 0.06, "from": fr, "to": to, "next": f"@{NS}.{nxt}"}
    # dry drop: heat wobble
    anims["wobble_a"] = {"anim_type": "offset", "easing": "in_out_sine", "duration": 0.5, "from": [0, 0], "to": [0, -0.6], "next": f"@{NS}.wobble_b"}
    anims["wobble_b"] = {"anim_type": "offset", "easing": "in_out_sine", "duration": 0.5, "from": [0, -0.6], "to": [0, 0], "next": f"@{NS}.wobble_a"}
    # mind: a slow sway that turns into twitching as sanity drops
    for t, (amp, dur) in {3: (0.35, 0.9), 2: (0.7, 0.5), 1: (1.0, 0.09), 0: (1.5, 0.05)}.items():
        seq = [[0, 0], [amp, -amp * 0.3], [-amp, amp * 0.2], [amp * 0.6, amp * 0.4], [0, 0]]
        if t <= 1:
            seq = [[0, 0], [amp, 0.2], [-amp * 0.4, -amp], [-amp, amp * 0.5], [amp * 0.3, amp], [0, 0]]
        names = [f"mind{t}_{c}" for c in "abcdef"[:len(seq) - 1]]
        for i in range(len(seq) - 1):
            anims[names[i]] = {"anim_type": "offset", "easing": "in_out_sine" if t >= 2 else "linear", "duration": dur,
                               "from": seq[i], "to": seq[i + 1], "next": f"@{NS}.{names[(i + 1) % len(names)]}"}
    anims["flicker_a"] = {"anim_type": "alpha", "easing": "linear", "duration": 0.07, "from": 1.0, "to": 0.35, "next": f"@{NS}.flicker_b"}
    anims["flicker_b"] = {"anim_type": "alpha", "easing": "linear", "duration": 0.12, "from": 0.35, "to": 1.0, "next": f"@{NS}.flicker_c"}
    anims["flicker_c"] = {"anim_type": "wait", "duration": 0.5, "next": f"@{NS}.flicker_a"}
    for tex, frames in FLIPBOOKS.items():
        anims[f"fb_{tex}"] = {"anim_type": "flip_book", "initial_uv": [0, 0], "frame_count": frames, "frame_step": FX * S4,
                              "fps": 12 if tex != 'fx_flames' else 14, "easing": "linear"}
    out = {"namespace": NS}
    out.update(anims)
    out["hud_layer"] = {"type": "panel", "size": ["100%", "100%"], "controls": [{DATA: data}, {"succubi_hud_shown": shown}]}
    return out


def vanilla_bottom_panels():
    """vanilla centered_gui_elements_at_bottom_middle(_touch) without hearts / armor / hunger;
    air bubbles and horse hearts moved up so they sit above the Succubi gauges"""
    def panel(width, binding):
        right = width
        return {
            "type": "panel", "anchor_from": "bottom_middle", "anchor_to": "bottom_middle", "size": [width, 50],
            "controls": [
                {"horse_heart_rend_0@hud.horse_heart_renderer": {"offset": [right, -72], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                                 "bindings": [{"binding_name": "#creative_horse_hearts", "binding_name_override": "#visible"}]}},
                {"horse_heart_rend_1@hud.horse_heart_renderer": {"offset": [right, -66], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                                 "bindings": [{"binding_name": "#survival_horse_hearts", "binding_name_override": "#visible"}]}},
                {"bubbles_rend_0@hud.bubbles_renderer": {"offset": [right, -66], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                          "bindings": [{"binding_name": "#is_not_riding_bubbles", "binding_name_override": "#visible"}]}},
                {"bubbles_rend_1@hud.bubbles_renderer": {"offset": [right, -66], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                          "bindings": [{"binding_name": "#is_riding_bubbles", "binding_name_override": "#visible"}]}},
                {"exp_rend@hud.exp_progress_bar_and_hotbar": {}}],
            "bindings": [{"binding_name": binding, "binding_name_override": "#visible", "binding_type": "global"}]}
    return {"centered_gui_elements_at_bottom_middle": panel(180, "#hud_visible_centered"),
            "centered_gui_elements_at_bottom_middle_touch": panel(200, "#hud_visible_centered_touch")}


def hud_screen_core():
    d = {
        "namespace": "hud",
        "succubi_bg": {"type": "panel", "size": ["100%", "100%"], "controls": [
            {"succubi_gate": {"type": "panel", "size": ["100%", "100%"], "controls": [{"layer@succubi_hud.hud_layer": {}}],
                              "bindings": [{"binding_name": "#hud_visible", "binding_name_override": "#visible", "binding_type": "global"}]}}]},
        "hud_screen@common.base_screen": {"$screen_bg_content": "hud.succubi_bg"},
        # our data titles never show; any other /title still does
        "hud_title_text": {"bindings": [
            {"binding_name": "#hud_title_text_string", "binding_type": "global"},
            {"binding_type": "view", "source_property_name": "((#hud_title_text_string - 'shud:') = #hud_title_text_string)",
             "target_property_name": "#visible"}]},
        # hearts, hunger and armor are drawn by the Succubi HUD (textures are also blanked as a fallback)
        "heart_renderer": {"ignored": True},
        "hunger_renderer": {"ignored": True},
        "armor_renderer": {"ignored": True},
    }
    d.update(vanilla_bottom_panels())
    return d


def hud_screen_guns():
    """Aplok Guns' own HUD bits (off-screen player renderer for first-person gun animations, item cooldowns)"""
    return {
        "namespace": "hud",
        "cooldown_renderer": {"ignored": False},
        "succubi_guns_extra": {"type": "panel", "size": ["100%", "100%"], "controls": [{"hud_elements@hud_elements.hud_elements": {}}]},
        "hud_screen@common.base_screen": {"$additional_screen_content": "hud.succubi_guns_extra"},
    }


@step
def build_hud(out, ctx, log):
    rp = os.path.join(out, CORE_RP)
    d = os.path.join(rp, TEX)
    for f in os.listdir(d) if os.path.isdir(d) else []:
        os.remove(os.path.join(d, f))                  # old rings / pills
    draw_all(rp)
    wjson(os.path.join(rp, 'ui/succubi_hud.json'), hud_json())
    wjson(os.path.join(rp, 'ui/hud_screen.json'), hud_screen_core())
    defs = sorted(f'ui/{f}' for f in os.listdir(os.path.join(rp, 'ui')) if f.startswith('succubi_') and f.endswith('.json'))
    wjson(os.path.join(rp, 'ui/_ui_defs.json'), {"ui_defs": defs})
    blank = Image.new('RGBA', (9, 9))
    for n in ('armor_empty', 'armor_half', 'armor_full'):
        blank.save(os.path.join(rp, f'textures/ui/{n}.png'))
    grp = os.path.join(out, GUNS_RP)
    wjson(os.path.join(grp, 'ui/hud_screen.json'), hud_screen_guns())
    wjson(os.path.join(grp, 'ui/_ui_defs.json'), {"ui_defs": ["ui/hud/hud_elements.json"]})
    log(f'HUD: {len(os.listdir(d))} textures, 4 round gauges with change / status effects')
