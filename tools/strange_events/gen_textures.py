# Textures for the strange events (Succubi Server v1.1.15): particle sprites, screen overlays, photos,
# the bloody paper and two item icons. Everything is drawn from code (numpy + Pillow), no outside images.
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RP = sys.argv[1] if len(sys.argv) > 1 else "Succubi Server RP"
PART = os.path.join(RP, "textures/particle/succubi")
UI = os.path.join(RP, "textures/ui/succubi_events")
ITEMS = os.path.join(RP, "textures/items/extra")
for d in (PART, UI, ITEMS):
    os.makedirs(d, exist_ok=True)

FONT_TH = "/usr/share/fonts/opentype/tlwg/Loma-Bold.otf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
rng = np.random.default_rng(3333)
random.seed(3333)


def save(img, *path):
    p = os.path.join(*path)
    img.save(p, optimize=True)
    print("wrote", p, img.size)


def noise(w, h, scale=1.0, octaves=4, seed=None):
    """smooth value noise in 0..1 (sum of upscaled random grids)"""
    g = np.random.default_rng(seed if seed is not None else rng.integers(1 << 30))
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cw = max(2, int(w / (32 * scale) * (2 ** o)) + 2)
        ch = max(2, int(h / (32 * scale) * (2 ** o)) + 2)
        grid = g.random((ch, cw)).astype(np.float32)
        layer = np.array(Image.fromarray((grid * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        out += layer * amp
        total += amp
        amp *= 0.5
    return out / total


def to_img(rgb, a):
    """rgb: HxWx3 floats 0..1 (or a tuple), a: HxW 0..1"""
    h, w = a.shape
    if not isinstance(rgb, np.ndarray):
        rgb = np.ones((h, w, 3), np.float32) * np.array(rgb, np.float32)
    arr = np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])
    return Image.fromarray((arr * 255 + 0.5).astype(np.uint8), "RGBA")


def mask_from(draw_fn, w, h, ss=4, blur=0.0):
    """draw white shapes at ss x resolution, return a smooth HxW 0..1 mask"""
    m = Image.new("L", (w * ss, h * ss), 0)
    draw_fn(ImageDraw.Draw(m), ss)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur * ss))
    m = m.resize((w, h), Image.LANCZOS)
    return np.array(m, np.float32) / 255


def blur_arr(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.array(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


# ================================================================ particles
def foot(d, s, ox, oy, w, h, right, child=False):
    """bare footprint pointing up (toes at the top) inside the box (ox, oy, w, h)"""
    X = lambda v: (ox + (w - v if right else v)) * s
    Y = lambda v: (oy + v) * s
    # heel
    d.ellipse([X(w * 0.30) - w * 0.22 * s, Y(h * 0.70), X(w * 0.30) + w * 0.22 * s, Y(h * 0.97)], fill=255)
    # outer edge / arch (a band on the outer side, the arch on the inner side stays empty)
    d.polygon([(X(w * 0.14), Y(h * 0.80)), (X(w * 0.52), Y(h * 0.80)), (X(w * 0.62), Y(h * 0.50)),
               (X(w * 0.74), Y(h * 0.30)), (X(w * 0.30), Y(h * 0.30)), (X(w * 0.16), Y(h * 0.55))], fill=255)
    # ball of the foot
    d.ellipse([X(w * 0.50) - w * 0.36 * s, Y(h * 0.20), X(w * 0.50) + w * 0.36 * s, Y(h * 0.42)], fill=255)
    # toes: big toe on the inner side (left foot -> right side of the print)
    toes = [(0.76, 0.12, 0.13), (0.55, 0.075, 0.085), (0.38, 0.08, 0.075), (0.24, 0.10, 0.065), (0.12, 0.14, 0.055)]
    if child:
        toes = [(x, y + 0.01, r * 1.1) for x, y, r in toes]
    for x, y, r in toes:
        cx, cy = X(w * x), Y(h * y)
        d.ellipse([cx - r * w * s, cy - r * w * s * 1.15, cx + r * w * s, cy + r * w * s * 1.15], fill=255)


def gen_feet():
    # 4 cells of 32x64: adult left, adult right, child left, child right (child prints are drawn smaller)
    W, H = 128, 64
    def draw(d, s):
        foot(d, s, 3, 2, 26, 60, False)
        foot(d, s, 32 + 3, 2, 26, 60, True)
        foot(d, s, 64 + 7, 14, 18, 42, False, True)
        foot(d, s, 96 + 7, 14, 18, 42, True, True)
    m = mask_from(draw, W, H, 6, 0.35)
    n = noise(W, H, 0.2, 3)
    grain = rng.random((H, W)).astype(np.float32)
    # the print is darker at the edges (pressed in) and patchy inside, a few bright specks = wet shine
    edge = np.clip(m - blur_arr(m, 1.6), 0, 1) * 2.5
    alpha = np.clip(m * (0.62 + 0.38 * n) + edge * 0.3, 0, 1) * (grain > 0.06)
    shade = np.clip(0.70 + 0.30 * n - edge * 0.4, 0, 1)
    shine = (grain > 0.965) & (m > 0.5)
    shade[shine] = 1.0
    rgb = np.dstack([shade, shade, shade])
    save(to_img(rgb, alpha), PART, "ev_feet.png")


def gen_hands():
    # 2 bloody handprints 64x64 (fingers up), already red (tint 1,1,1)
    W, H = 128, 64
    def hand(d, s, ox, spread, seed):
        r = random.Random(seed)
        cx, cy = ox + 32, 40
        d.ellipse([(cx - 13) * s, (cy - 12) * s, (cx + 13) * s, (cy + 14) * s], fill=255)  # palm
        fingers = [(-11, -spread * 1.2, 20), (-4, -spread * 0.4, 25), (4, spread * 0.3, 26), (11, spread * 1.0, 22)]
        for fx, ang, ln in fingers:
            a = math.radians(ang)
            x0, y0 = cx + fx, cy - 8
            x1, y1 = x0 + math.sin(a) * ln, y0 - math.cos(a) * ln
            d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=255, width=int(6.4 * s))
            d.ellipse([(x1 - 3.2) * s, (y1 - 3.2) * s, (x1 + 3.2) * s, (y1 + 3.2) * s], fill=255)
        # thumb
        d.line([((cx + 12) * s, (cy + 4) * s), ((cx + 22) * s, (cy - 8) * s)], fill=255, width=int(7 * s))
        d.ellipse([(cx + 18.5) * s, (cy - 12) * s, (cx + 25.5) * s, (cy - 5) * s], fill=255)
        # drips running down from the palm
        for i in range(4):
            x = cx + r.uniform(-11, 11)
            y0 = cy + 10
            y1 = min(63, y0 + r.uniform(6, 22))
            d.line([(x * s, y0 * s), (x * s, y1 * s)], fill=255, width=int(r.uniform(1.6, 2.8) * s))
            d.ellipse([(x - 1.7) * s, (y1 - 1.5) * s, (x + 1.7) * s, (y1 + 2) * s], fill=255)
    def draw(d, s):
        hand(d, s, 0, 9, 1)
        hand(d, s, 64, 16, 2)
    m = mask_from(draw, W, H, 6, 0.3)
    n = noise(W, H, 0.25, 3)
    grain = rng.random((H, W)).astype(np.float32)
    # smeared: patchy alpha, darker clotted edges, a few gaps where the palm did not touch
    edge = np.clip(m - blur_arr(m, 1.2), 0, 1) * 2
    alpha = np.clip(m * (0.35 + 0.65 * n ** 0.7) + edge * 0.45, 0, 1) * (grain > 0.05)
    r = 0.45 + 0.25 * n - edge * 0.25
    g = 0.02 + 0.03 * n
    b = 0.03 + 0.03 * n
    save(to_img(np.dstack([r, g, b]), alpha), PART, "ev_hands.png")


def gen_drag():
    # 64x32 smear, horizontal (it is stretched along the drag direction): long streaks and finger lines
    W, H = 64, 32
    y = np.linspace(-1, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    streaks = noise(W, H, 0.05, 2, 11)
    streaks = np.array(Image.fromarray((streaks * 255).astype(np.uint8)).resize((W, H)), np.float32) / 255
    rows = np.array([rng.random() for _ in range(H)], np.float32)[:, None]
    rows = blur_arr(np.repeat(rows, W, 1), 0.6)
    body = np.clip(1 - (np.abs(y) / 0.78) ** 3, 0, 1)
    alpha = body * (0.35 + 0.65 * rows) * (0.7 + 0.3 * noise(W, H, 0.3, 3))
    # finger scrapes at the edges
    for yy in (0.18, 0.3, 0.7, 0.82):
        r0 = int(yy * H)
        alpha[r0, :] = np.maximum(alpha[r0, :], 0.75 * (0.6 + 0.4 * rng.random(W)))
    alpha *= np.clip(x * 6, 0, 1) * np.clip((1 - x) * 6, 0, 1) * 0.5 + 0.5
    r = 0.30 + 0.15 * rows
    save(to_img(np.dstack([r, r * 0.12, r * 0.1]), np.clip(alpha, 0, 1)), PART, "ev_drag.png")


def gen_puff():
    # soft round puff (white) for breath, smoke, dust, motes
    W = 32
    yy, xx = np.mgrid[0:W, 0:W]
    d = np.hypot(xx - 15.5, yy - 15.5) / 15.5
    n = noise(W, W, 0.3, 3, 21)
    a = np.clip(1 - d, 0, 1) ** 1.6 * (0.6 + 0.4 * n)
    save(to_img((1, 1, 1), a), PART, "ev_puff.png")
    # glowing orb for the will-o'-wisp / eye glow (additive)
    a = np.clip(1 - d, 0, 1) ** 2.2
    core = np.clip(1 - d * 2.2, 0, 1)
    rgb = np.dstack([0.6 + 0.4 * core, 0.9 + 0.1 * core, 1.0 * np.ones_like(core)])
    save(to_img(rgb, np.clip(a + core, 0, 1)), PART, "ev_orb.png")
    # tiny drop and spark
    S = 8
    yy, xx = np.mgrid[0:S, 0:S]
    drop = np.clip(1 - np.hypot((xx - 3.5) / 2.6, (yy - 4.6) / 3.0), 0, 1)
    drop[0:3, 3:5] = np.maximum(drop[0:3, 3:5], 0.7)
    save(to_img((1, 1, 1), np.clip(drop * 1.5, 0, 1)), PART, "ev_drop.png")
    spark = np.zeros((S, S), np.float32)
    spark[3:5, :] = 0.6
    spark[:, 3:5] = 0.6
    spark[2:6, 2:6] = np.maximum(spark[2:6, 2:6], 0.5)
    spark[3:5, 3:5] = 1
    save(to_img((1, 1, 1), spark), PART, "ev_spark.png")
    # ash flakes: 4 frames of 8x8
    fl = np.zeros((8, 32), np.float32)
    for i in range(4):
        pts = rng.integers(1, 7, (5, 2))
        for py, px in pts:
            fl[py, i * 8 + px] = 1
        fl[:, i * 8:i * 8 + 8] = np.maximum(fl[:, i * 8:i * 8 + 8], blur_arr(fl[:, i * 8:i * 8 + 8], 0.6) * 1.5)
    g = 0.35 + 0.2 * rng.random((8, 32))
    save(to_img(np.dstack([g, g, g * 0.95]), np.clip(fl, 0, 1)), PART, "ev_ash.png")


WORDS = ["ข้างหลัง", "หนีไป", "เห็นเธอแล้ว", "อย่าหันไป", "มานี่สิ", "ใครอยู่ตรงนั้น", "ไม่มีทางออก", "อยู่กับฉัน"]


def gen_words():
    # 8 rows of 256x32: charcoal / ash writing (white = ash, tinted grey in the particle)
    W, H = 256, 32 * len(WORDS)
    img = Image.new("L", (W * 3, H * 3), 0)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_TH, 64)
    for i, w in enumerate(WORDS):
        bb = d.textbbox((0, 0), w, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x = (W * 3 - tw) / 2 - bb[0]
        y = i * 96 + (96 - th) / 2 - bb[1]
        # shaky finger writing: draw a few offset copies
        for k in range(5):
            d.text((x + random.uniform(-2.5, 2.5), y + random.uniform(-2.5, 2.5)), w, font=font, fill=int(150 + 20 * k))
    m = np.array(img.resize((W, H), Image.LANCZOS), np.float32) / 255
    n = noise(W, H, 0.12, 3)
    grain = rng.random((H, W)).astype(np.float32)
    alpha = np.clip(m * 1.3, 0, 1) * (0.55 + 0.45 * n) * (grain > 0.12)
    # ash dust around the letters
    alpha = np.maximum(alpha, blur_arr(m, 2.5) * 0.35 * (grain > 0.55))
    v = 0.55 + 0.45 * n
    save(to_img(np.dstack([v, v, v]), alpha), PART, "ev_words.png")


def gen_scratch():
    # 2 variants 64x64: claw gouges, pale splintered wood inside, dark edges
    W, H = 128, 64
    layers = []
    for v in range(2):
        img = Image.new("L", (64 * 6, 64 * 6), 0)
        d = ImageDraw.Draw(img)
        for i in range(4 if v == 0 else 3):
            x0 = (12 + i * 12 + random.uniform(-2, 2)) * 6
            pts = []
            for t in np.linspace(0, 1, 12):
                pts.append((x0 + (t * 14 + math.sin(t * 5 + i) * 2) * 6 * (1 if v == 0 else -0.6), (6 + t * 52) * 6))
            for k in range(len(pts) - 1):
                wdt = int((1.2 + 3.2 * math.sin(math.pi * k / (len(pts) - 1))) * 6)
                d.line([pts[k], pts[k + 1]], fill=255, width=max(2, wdt))
        layers.append(np.array(img.resize((64, 64), Image.LANCZOS), np.float32) / 255)
    m = np.hstack(layers)
    edge = np.clip(blur_arr(m, 1.4) - m * 0.6, 0, 1)
    alpha = np.clip(m + edge * 0.8, 0, 1)
    wood = 0.85 + 0.15 * noise(W, H, 0.1, 2)
    r = np.where(m > 0.35, wood, 0.12)
    g = np.where(m > 0.35, wood * 0.82, 0.07)
    b = np.where(m > 0.35, wood * 0.62, 0.05)
    save(to_img(np.dstack([r, g, b]), alpha), PART, "ev_scratch.png")


def gen_hair():
    # 3 variants 64x64 of long black strands (the last one = a clump)
    W, H = 192, 64
    img = Image.new("L", (W * 4, H * 4), 0)
    d = ImageDraw.Draw(img)
    for v in range(3):
        count = 9 if v < 2 else 26
        for i in range(count):
            ph = random.uniform(0, 6.3)
            amp = random.uniform(2, 6 if v < 2 else 9)
            x0 = v * 64 + random.uniform(4, 60)
            y0 = random.uniform(2, 12) if v < 2 else random.uniform(10, 30)
            pts = []
            steps = 30
            for k in range(steps):
                t = k / (steps - 1)
                pts.append(((x0 + math.sin(ph + t * random.uniform(5, 9)) * amp + (t - 0.5) * random.uniform(-8, 8)) * 4,
                            (y0 + t * (52 if v < 2 else 30)) * 4))
            d.line(pts, fill=random.randint(170, 255), width=random.choice([2, 3, 4]))
    m = np.array(img.resize((W, H), Image.LANCZOS), np.float32) / 255
    v = 0.1 + 0.25 * noise(W, H, 0.2, 2)
    save(to_img(np.dstack([v, v * 0.9, v * 0.85]), np.clip(m * 1.6, 0, 1)), PART, "ev_hair.png")


def eye_pair(w, h, openness, seed=0):
    """glowing pair of eyes, openness 0..1, white-hot centre (tinted in the particle)"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.zeros((h, w), np.float32)
    for cx in (w * 0.28, w * 0.72):
        cy = h * 0.5
        ew, eh = w * 0.17, h * 0.34 * max(0.05, openness)
        # almond shape
        d = ((xx - cx) / ew) ** 2 + ((yy - cy) / eh) ** 2
        a = np.maximum(a, np.clip(1.2 - d, 0, 1))
        if openness > 0.3:
            pupil = np.clip(1 - np.hypot((xx - cx) / (ew * 0.28), (yy - cy) / (eh * 0.9)), 0, 1)
            a = np.maximum(a * (1 - pupil * 0.9), 0)
    glow = blur_arr(a, 1.2) * 0.6
    return np.clip(a + glow, 0, 1)


def gen_eyes():
    # flipbook 4 frames of 32x16: open, open, half, closed (the particle picks the frame from its age)
    frames = [eye_pair(32, 16, o) for o in (1.0, 0.75, 0.35, 0.05)]
    a = np.hstack(frames)
    core = np.clip(a * 1.3, 0, 1)
    rgb = np.dstack([np.ones_like(a), 0.6 + 0.4 * core, 0.5 + 0.5 * core])
    save(to_img(rgb, a), PART, "ev_eyes.png")


def gen_candle():
    # candle body 16x32 (wax with drips, burnt wick) + flame flipbook 4 x (16x32)
    W, H = 16, 32
    def body(d, s):
        d.rectangle([4 * s, 12 * s, 11.5 * s, 31.5 * s], fill=255)
        for x, ln in ((4.5, 6), (7, 3), (10.5, 8)):
            d.line([(x * s, 12 * s), (x * s, (12 + ln) * s)], fill=255, width=int(1.6 * s))
        d.polygon([(4 * s, 12.5 * s), (6 * s, 11 * s), (9 * s, 11.5 * s), (11.5 * s, 12.5 * s)], fill=255)
    m = mask_from(body, W, H, 8)
    shade = np.tile(np.linspace(0.70, 1.0, W)[None, :] ** 0.5, (H, 1)) * (0.9 + 0.1 * noise(W, H, 0.2, 2))
    wax = np.dstack([shade * 0.96, shade * 0.92, shade * 0.82])
    wick = np.zeros((H, W), np.float32)
    wick[8:12, 7:9] = 1
    rgb = np.where(wick[..., None] > 0, 0.08, wax)
    save(to_img(rgb, np.maximum(m, wick)), PART, "ev_candle.png")
    frames = []
    for f in range(4):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        sway = math.sin(f * 1.6) * 1.2
        cx = 7.5 + sway * (1 - yy / H)
        tip = 3 + f % 2
        wid = np.clip((yy - tip) / (H - tip), 0, 1) ** 0.6 * 4.2 * np.clip((H - 4 - yy) / 6, 0, 1)
        d = np.abs(xx - cx) / np.maximum(wid, 0.01)
        a = np.clip(1 - d, 0, 1) * (yy > tip)
        frames.append(a)
    a = np.hstack(frames)
    hot = np.clip(a * 1.6 - 0.5, 0, 1)
    rgb = np.dstack([np.ones_like(a), 0.55 + 0.45 * hot, 0.15 + 0.7 * hot])
    save(to_img(rgb, np.clip(a * 1.4, 0, 1)), PART, "ev_flame.png")


def gen_reach_hand():
    # pale hands reaching up out of the ground: 2 frames of 32x64 (open, clawing)
    W, H = 64, 64
    def hand(d, s, ox, claw):
        cx = ox + 16
        d.polygon([((cx - 5) * s, 64 * s), ((cx + 5) * s, 64 * s), ((cx + 6) * s, 34 * s), ((cx - 6) * s, 34 * s)], fill=255)
        d.ellipse([(cx - 8) * s, 22 * s, (cx + 8) * s, 38 * s], fill=255)
        for i, fx in enumerate((-6, -2, 2, 6)):
            top = 6 + abs(fx) * 0.8
            bend = (3 if claw else 0) * (1 if fx > 0 else -1)
            d.line([((cx + fx * 0.8) * s, 26 * s), ((cx + fx * 1.2 + bend) * s, (top + (6 if claw else 0)) * s)],
                   fill=255, width=int(3.1 * s))
        d.line([((cx - 7) * s, 32 * s), ((cx - 13) * s, 24 * s)], fill=255, width=int(3.4 * s))
    def draw(d, s):
        hand(d, s, 0, False)
        hand(d, s, 32, True)
    m = mask_from(draw, W, H, 6, 0.3)
    n = noise(W, H, 0.2, 3)
    yy = np.linspace(0, 1, H)[:, None]
    shade = (0.62 + 0.3 * n) * (1 - 0.5 * yy)
    edge = np.clip(m - blur_arr(m, 1.0), 0, 1)
    rgb = np.dstack([shade * 0.92 - edge * 0.3, shade * 0.95 - edge * 0.3, shade - edge * 0.2])
    save(to_img(rgb, m * np.clip((1 - yy) * 5, 0, 1)), PART, "ev_reach.png")


# ================================================================ screen overlays (HUD)
SW, SH = 256, 144


def vignette(w, h, power=2.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / math.sqrt(2)
    return np.clip(d, 0, 1) ** power


def gen_face(variant):
    # full screen scare face, 512x288
    W, H = 512, 288
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    n = noise(W, H, 0.4, 5, 100 + variant)
    tilt = 0.0 if variant == 1 else -0.35
    cx, cy = W / 2 + (0 if variant == 1 else 30), H / 2 + 12
    ca, sa = math.cos(tilt), math.sin(tilt)
    X = ((xx - cx) * ca + (yy - cy) * sa)
    Y = (-(xx - cx) * sa + (yy - cy) * ca)
    fw, fh = (118, 150) if variant == 1 else (128, 160)
    face = np.clip(1.15 - np.hypot(X / fw, Y / fh), 0, 1) ** 0.35
    # skin: grey-green, bony shading
    shade = 0.55 + 0.35 * (1 - np.hypot(X / fw, (Y + 40) / fh)) + 0.12 * (n - 0.5)
    skin = np.dstack([shade * 0.78, shade * 0.80, shade * 0.74])
    img = skin * face[..., None]
    # sockets: big black holes, faint pinprick pupils
    for ex in (-44, 44):
        ey = -28 if variant == 1 else -24
        s = np.hypot((X - ex) / 30, (Y - ey) / (26 if variant == 1 else 34))
        hole = np.clip(1.25 - s, 0, 1) ** 0.7
        img *= (1 - hole[..., None] * 0.97)
        pupil = np.clip(1 - np.hypot((X - ex - 2) / 3.2, (Y - ey) / 3.2), 0, 1)
        img += pupil[..., None] * np.array([0.9, 0.9, 0.85])
        # blood tears
        tear = (np.abs(X - ex - 6) < 2.2 + 1.5 * n) & (Y > ey + 18) & (Y < ey + 90 + 40 * n)
        img[tear] = img[tear] * 0.3 + np.array([0.35, 0.0, 0.0])
    # mouth: a long gaping oval with ragged teeth rows
    mh = 58 if variant == 1 else 30
    mw = 30 if variant == 1 else 80
    my = 70 if variant == 1 else 62
    ms = np.hypot(X / mw, (Y - my) / mh)
    mouth = np.clip(1.15 - ms, 0, 1) ** 0.6
    img *= (1 - mouth[..., None] * 0.98)
    teeth_top = (np.abs(Y - (my - mh * 0.78)) < 6) & (np.sin(X * 0.55) > -0.2) & (ms < 1.0)
    teeth_bot = (np.abs(Y - (my + mh * 0.78)) < 6) & (np.sin(X * 0.55 + 1.3) > -0.2) & (ms < 1.0)
    img[teeth_top | teeth_bot] = np.array([0.72, 0.68, 0.55])
    # cracks / veins
    cracks = (np.abs(noise(W, H, 0.08, 3, 55 + variant) - 0.5) < 0.012) & (face > 0.3)
    img[cracks] *= 0.35
    # hair: black curtains on both sides
    hair = np.clip((np.abs(X) - fw * 0.72) / 30, 0, 1) * np.clip((Y + fh * 1.3) / 60, 0, 1)
    strands = 0.6 + 0.4 * np.sin(X * 0.9 + n * 6)
    img *= (1 - hair[..., None] * 0.95 * strands[..., None])
    top_hair = np.clip((-Y - fh * 0.62) / 25, 0, 1)
    img *= (1 - top_hair[..., None] * 0.97)
    # grain, vignette, red cast
    img += (rng.random((H, W, 1)) - 0.5) * 0.10
    v = vignette(W, H, 1.3)
    img *= (1 - v[..., None] * 0.9)
    img[..., 0] *= 1.08
    save(to_img(np.clip(img, 0, 1), np.ones((H, W), np.float32)), UI, f"face_{variant}.png")


def gen_vhs():
    # 4 frames of 256x144 in a strip: tracking band, chroma fringes, PLAY / time OSD
    frames = []
    font = ImageFont.truetype(FONT_MONO, 11)
    for f in range(4):
        img = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        a = np.zeros((SH, SW), np.float32)
        rgb = np.zeros((SH, SW, 3), np.float32)
        # scanlines
        a[::2, :] = 0.10
        # tracking band (moves each frame)
        band_y = [118, 12, 64, 96][f]
        for y in range(band_y, min(SH, band_y + 14)):
            k = 1 - abs(y - band_y - 7) / 7
            row = rng.random(SW) > 0.35
            a[y, row] = np.maximum(a[y, row], 0.55 * k + 0.2)
            rgb[y, row] = 0.9
            shift = int(rng.integers(3, 14))
            rgb[y] = np.roll(rgb[y], shift, 0)
        # chroma fringes: thin magenta / cyan lines
        for _ in range(7):
            y = int(rng.integers(0, SH))
            x0 = int(rng.integers(0, SW - 60))
            ln = int(rng.integers(30, 160))
            c = np.array([1.0, 0.1, 0.9]) if rng.random() < 0.5 else np.array([0.1, 0.9, 1.0])
            a[y, x0:x0 + ln] = 0.35
            rgb[y, x0:x0 + ln] = c
        # snow
        snow = rng.random((SH, SW)) > 0.985
        a[snow] = 0.5
        rgb[snow] = 1
        base = to_img(rgb, a)
        img.alpha_composite(base)
        d = ImageDraw.Draw(img)
        if f % 2 == 0:
            d.polygon([(10, 10), (10, 20), (18, 15)], fill=(235, 235, 235, 230))
            d.text((22, 8), "PLAY", font=font, fill=(235, 235, 235, 230))
        d.text((188, 124), "AM 03:33", font=font, fill=(235, 235, 235, 220))
        d.text((10, 124), "SP", font=font, fill=(235, 235, 235, 200))
        frames.append(img)
    strip = Image.new("RGBA", (SW * 4, SH))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * SW, 0))
    save(strip, UI, "vhs.png")
    # colour wash for the VHS look (one image, faint)
    yy = np.linspace(0, 1, SH)[:, None] * np.ones((1, SW))
    wash = np.dstack([0.25 + 0.2 * yy, 0.05 * np.ones_like(yy), 0.35 - 0.1 * yy])
    save(to_img(wash, 0.18 + vignette(SW, SH, 1.5) * 0.5), UI, "vhs_wash.png")


def gen_edge_eyes():
    # 4 frames: dark vignette with ~12 eyes along the edges, frames = closed, half, open, open
    rs = np.random.default_rng(12)
    spots = []
    while len(spots) < 13:
        x, y = rs.uniform(14, SW - 14), rs.uniform(8, SH - 8)
        edge = min(x, SW - x, y * 1.6, (SH - y) * 1.6)
        if edge < 34 and all(math.hypot(x - a, y - b) > 30 for a, b in spots):
            spots.append((x, y))
    frames = []
    base = vignette(SW, SH, 1.6) * 1.35
    for openness in (0.05, 0.4, 1.0, 0.85):
        a = np.clip(base, 0, 0.97)
        rgb = np.zeros((SH, SW, 3), np.float32)
        for (x, y) in spots:
            e = eye_pair(22, 10, openness)
            x0, y0 = int(x - 11), int(y - 5)
            sub = (slice(y0, y0 + 10), slice(x0, x0 + 22))
            rgb[sub] = np.maximum(rgb[sub], np.dstack([e, e * 0.85, e * 0.6]))
            a[sub] = np.maximum(a[sub], e)
        frames.append(to_img(rgb, a))
    strip = Image.new("RGBA", (SW * 4, SH))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * SW, 0))
    save(strip, UI, "edge_eyes.png")


def gen_blood_edge():
    # 8 frames: blood pooled along the top edge, streams running down; the streams scroll so the loop is seamless
    F = 8
    period = SH
    streams = []
    rs = np.random.default_rng(65)
    x = 4
    while x < SW - 4:
        streams.append((x, rs.uniform(1.2, 3.2), rs.uniform(0.25, 0.9), rs.uniform(0, 1)))
        x += rs.uniform(10, 26)
    top = np.zeros((SH, SW), np.float32)
    yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
    edge_line = 8 + 6 * noise(SW, 1, 0.3, 3, 7)[0]
    top = np.clip((edge_line[None, :] - yy) / 3 + 1, 0, 1)
    frames = []
    for f in range(F):
        a = top.copy()
        for (sx, wdt, length, ph) in streams:
            ln = length * SH
            col = np.clip(1 - np.abs(xx - sx) / wdt, 0, 1)
            under = (yy < ln) & (yy > 0)
            a = np.maximum(a, col * under * np.clip((ln - yy) / 10 + 0.3, 0, 1))
            # a fat drop sliding down the stream (moves with the frame)
            dy = ((ph + f / F) % 1.0) * ln
            drop = np.clip(1 - np.hypot((xx - sx) / (wdt * 1.4), (yy - dy) / (wdt * 2.2)), 0, 1)
            a = np.maximum(a, drop * 1.2)
        a = np.clip(a, 0, 1)
        n = noise(SW, SH, 0.3, 2, 99)
        rgb = np.dstack([0.42 + 0.18 * n, 0.01 + 0.02 * n, 0.02 + 0.02 * n])
        spec = (a > 0.8) & (np.roll(a, 1, 1) < a)
        rgb[spec] = np.array([0.75, 0.2, 0.2])
        frames.append(to_img(rgb, a * 0.95))
    strip = Image.new("RGBA", (SW * F, SH))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * SW, 0))
    save(strip, UI, "blood_edge.png")


def gen_dark():
    save(to_img((0.0, 0.0, 0.02), np.ones((16, 16), np.float32)), UI, "black.png")
    v = vignette(SW, SH, 0.9)
    save(to_img((0, 0, 0.02), np.clip(0.45 + v * 0.75, 0, 0.985)), UI, "dark_vignette.png")


# ================================================================ photos (the cursed photo item)
PW = 192


def photo_base(seed, dark=0.25):
    n = noise(PW, PW, 0.5, 5, seed)
    img = np.dstack([n * dark * 1.05, n * dark, n * dark * 0.9])
    return img


def figure(img, cx, base_y, h, alpha=0.9, pale=False, width=0.18):
    yy, xx = np.mgrid[0:PW, 0:PW].astype(np.float32)
    head_r = h * 0.09
    hy = base_y - h + head_r
    head = np.hypot((xx - cx) / head_r, (yy - hy) / (head_r * 1.25)) < 1
    body_w = h * width
    t = np.clip((yy - (hy + head_r)) / (base_y - hy - head_r), 0, 1)
    body = (yy > hy + head_r * 0.8) & (yy < base_y) & (np.abs(xx - cx) < body_w * (0.55 + 0.45 * t))
    arms = (yy > hy + head_r * 1.5) & (yy < hy + h * 0.62) & (np.abs(np.abs(xx - cx) - body_w * 0.8) < h * 0.035)
    m = (head | body | arms).astype(np.float32)
    m = blur_arr(m, 0.8) * alpha
    col = np.array([0.78, 0.8, 0.76]) if pale else np.array([0.01, 0.01, 0.01])
    img[:] = img * (1 - m[..., None]) + col * m[..., None]
    if not pale:
        for ex in (-head_r * 0.35, head_r * 0.35):
            e = np.hypot(xx - cx - ex, yy - hy) < max(0.8, head_r * 0.13)
            img[e] = np.array([0.95, 0.95, 0.9])


def blocky_player_back(img, cx, base_y, h):
    # a Minecraft-ish player seen from behind: the viewer
    s = h / 32
    def rect(x0, y0, x1, y1, c):
        img[int(base_y - y1 * s):int(base_y - y0 * s), int(cx + x0 * s):int(cx + x1 * s)] = c
    rect(-4, 0, 0, 12, np.array([0.18, 0.2, 0.45]))
    rect(0, 0, 4, 12, np.array([0.16, 0.18, 0.42]))
    rect(-4, 12, 4, 24, np.array([0.1, 0.45, 0.5]))
    rect(-8, 12, -4, 24, np.array([0.55, 0.4, 0.3]))
    rect(4, 12, 8, 24, np.array([0.55, 0.4, 0.3]))
    rect(-4, 24, 4, 32, np.array([0.25, 0.16, 0.08]))


def trees(img, count, seed, dark=0.02):
    rs = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rs.uniform(0, PW))
        w = int(rs.uniform(5, 16))
        img[:, max(0, x - w // 2):x + w // 2] = img[:, max(0, x - w // 2):x + w // 2] * 0.2 + dark


def finish_photo(img, name, flash=True):
    yy, xx = np.mgrid[0:PW, 0:PW].astype(np.float32)
    if flash:
        # camera flash: bright centre, fast falloff
        f = np.clip(1 - np.hypot(xx - PW / 2, yy - PW * 0.55) / (PW * 0.6), 0, 1) ** 1.5
        img = img + f[..., None] * np.array([0.22, 0.2, 0.16])
    img = img + (rng.random((PW, PW, 1)) - 0.5) * 0.12
    # faded, slightly green old print
    img = img * np.array([0.95, 1.0, 0.88]) + np.array([0.03, 0.04, 0.02])
    img = img * (1 - vignette(PW, PW, 1.4)[..., None] * 0.7)
    save(to_img(np.clip(img, 0, 1), np.ones((PW, PW), np.float32)), UI, name)


def gen_photos():
    # 1: you, from behind, in the dark forest - and something tall right behind you
    img = photo_base(1, 0.18)
    trees(img, 9, 1)
    img[140:, :] = img[140:, :] * 0.6 + np.array([0.05, 0.06, 0.04])
    figure(img, 120, 176, 150, 0.95, width=0.13)
    blocky_player_back(img, 80, 184, 70)
    finish_photo(img, "photo_1.png")
    # 2: a bedroom: the bed, and someone standing beside it
    img = photo_base(2, 0.22)
    img[118:170, 20:120] = np.array([0.42, 0.1, 0.1])  # blanket
    img[108:120, 20:52] = np.array([0.8, 0.78, 0.72])  # pillow
    img[170:176, 20:120] = np.array([0.2, 0.12, 0.06])
    figure(img, 150, 178, 140, 0.92)
    finish_photo(img, "photo_2.png")
    # 3: a long dark corridor with a pale face at the end
    img = photo_base(3, 0.12)
    yy, xx = np.mgrid[0:PW, 0:PW].astype(np.float32)
    hall = (np.abs(xx - PW / 2) < 20 + (yy - 70) * 0.5) & (yy > 60)
    img[hall] = img[hall] + 0.08
    face = np.hypot((xx - PW / 2) / 7, (yy - 86) / 9) < 1
    img[face] = np.array([0.82, 0.82, 0.78])
    for ex in (-2.5, 2.5):
        img[np.hypot(xx - PW / 2 - ex, yy - 84) < 1.5] = 0
    finish_photo(img, "photo_3.png", flash=False)
    # 4: lake at night, a pale hand reaching out of the water
    img = photo_base(4, 0.15)
    img[100:, :] = img[100:, :] * 0.5 + np.array([0.02, 0.05, 0.08])
    img[98:101, :] += 0.12
    figure(img, 96, 106, 34, 0.9, pale=True, width=0.1)
    finish_photo(img, "photo_4.png", flash=False)
    # 5: many figures standing in the trees, all facing the camera
    img = photo_base(5, 0.2)
    trees(img, 6, 5)
    for x, hgt in ((30, 60), (70, 48), (108, 66), (150, 52), (176, 40)):
        figure(img, x, 150, hgt, 0.85)
    finish_photo(img, "photo_5.png")
    # 6: close-up of an eye filling the frame
    img = photo_base(6, 0.35) + np.array([0.25, 0.2, 0.18])
    yy, xx = np.mgrid[0:PW, 0:PW].astype(np.float32)
    white = np.hypot((xx - 96) / 80, (yy - 96) / 40) < 1
    img[white] = np.array([0.85, 0.8, 0.72]) + (noise(PW, PW, 0.05, 2, 66)[white][:, None] - 0.5) * 0.3
    veins = (np.abs(noise(PW, PW, 0.06, 3, 77) - 0.5) < 0.02) & white
    img[veins] = np.array([0.6, 0.05, 0.05])
    iris = np.hypot(xx - 96, yy - 96) < 30
    img[iris] = np.array([0.2, 0.15, 0.1])
    img[np.hypot(xx - 96, yy - 96) < 12] = 0.0
    img[np.hypot(xx - 88, yy - 88) < 4] = 0.95
    finish_photo(img, "photo_6.png")
    # polaroid frame (the photo sits in the top square)
    FW, FH = 240, 290
    fr = np.ones((FH, FW, 3), np.float32) * np.array([0.93, 0.91, 0.85])
    fr *= (0.94 + 0.06 * noise(FW, FH, 0.3, 3, 8)[..., None])
    stain = noise(FW, FH, 0.15, 3, 9)
    fr[stain > 0.7] *= np.array([0.9, 0.82, 0.7])
    a = np.ones((FH, FW), np.float32)
    a[:2, :] = a[-2:, :] = 0
    a[:, :2] = a[:, -2:] = 0
    fr[24:216, 24:216] = 0.05
    save(to_img(fr, a), UI, "photo_frame.png")


# ================================================================ bloody paper + item icons
def gen_blood_paper():
    src = os.path.join(RP, "textures/ui/succubi_paper/paper.png")
    p = Image.open(src).convert("RGBA")
    W, H = p.size
    arr = np.array(p, np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3]
    # age: darker, dirtier
    n = noise(W, H, 0.6, 4, 13)
    rgb *= (0.78 + 0.22 * n)[..., None]
    splat = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rs = np.random.default_rng(42)
    for _ in range(4):
        cx, cy, r = rs.uniform(40, W - 40), rs.uniform(30, H - 30), rs.uniform(14, 34)
        blob = np.clip(1.2 - np.hypot(xx - cx, yy - cy) / r - (noise(W, H, 0.15, 3)) * 0.6, 0, 1)
        splat = np.maximum(splat, blob)
        for _ in range(9):
            ang = rs.uniform(0, 6.28)
            dist = rs.uniform(r, r * 2.6)
            sx, sy = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
            splat = np.maximum(splat, np.clip(1 - np.hypot(xx - sx, yy - sy) / rs.uniform(2, 6), 0, 1))
    # a bloody thumbprint at the lower right and a finger smear across the top
    tp = np.hypot((xx - W * 0.82) / 22, (yy - H * 0.78) / 28)
    ridges = (np.sin(tp * 26) > 0.1) & (tp < 1)
    splat = np.maximum(splat, ridges * 0.8)
    smear = (np.abs(yy - 22 - np.sin(xx / 40) * 4) < 5) & (xx > W * 0.3) & (xx < W * 0.75)
    splat = np.maximum(splat, smear * noise(W, H, 0.1, 2, 5) * 1.2)
    splat = np.clip(splat, 0, 1) * a
    blood = np.array([0.38, 0.03, 0.03])
    rgb = rgb * (1 - splat[..., None] * 0.85) + blood * splat[..., None] * 0.85
    save(to_img(rgb, a), os.path.join(RP, "textures/ui/succubi_paper"), "paper_blood.png")


def gen_icons():
    S = 64
    # cursed photo: a small tilted polaroid with a dark picture and a pale figure
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    card = Image.new("RGBA", (40, 48), (236, 232, 220, 255))
    d = ImageDraw.Draw(card)
    d.rectangle([4, 4, 35, 35], fill=(24, 26, 22, 255))
    d.rectangle([4, 26, 35, 35], fill=(38, 44, 32, 255))
    d.ellipse([17, 11, 23, 17], fill=(210, 212, 200, 255))
    d.polygon([(16, 17), (24, 17), (26, 34), (14, 34)], fill=(200, 202, 190, 255))
    d.rectangle([0, 0, 39, 47], outline=(150, 145, 130, 255))
    d.line([(6, 41), (30, 41)], fill=(110, 20, 20, 255), width=2)
    card = card.rotate(-12, resample=Image.BICUBIC, expand=True)
    img.alpha_composite(card, ((S - card.width) // 2, (S - card.height) // 2))
    save(img, ITEMS, "cursed_photo.png")
    # mystery note: folded yellowed paper with a blood smear
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(10, 14), (50, 8), (56, 50), (14, 56)], fill=(224, 208, 170, 255), outline=(150, 128, 90, 255))
    d.line([(30, 11), (35, 53)], fill=(185, 165, 125, 255), width=2)
    for i in range(5):
        y = 20 + i * 6
        d.line([(16, y + 1), (46, y - 3)], fill=(90, 70, 50, 220), width=1)
    d.ellipse([34, 36, 50, 50], fill=(120, 16, 16, 230))
    d.line([(42, 48), (43, 58)], fill=(120, 16, 16, 230), width=3)
    save(img, ITEMS, "mystery_note.png")


if __name__ == "__main__":
    gen_feet()
    gen_hands()
    gen_drag()
    gen_puff()
    gen_words()
    gen_scratch()
    gen_hair()
    gen_eyes()
    gen_candle()
    gen_reach_hand()
    gen_face(1)
    gen_face(2)
    gen_vhs()
    gen_edge_eyes()
    gen_blood_edge()
    gen_dark()
    gen_photos()
    gen_blood_paper()
    gen_icons()
