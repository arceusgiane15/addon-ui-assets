# The curse staff window skin (title flag §0§9§4§3) and its icons: violet-black window with a glowing rune border,
# buttons with a violet bar that glow on hover, 64x64 icons for targets / radius / self / event kinds, and the staff item.
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RP = sys.argv[1] if len(sys.argv) > 1 else "Succubi Server RP"
UI = os.path.join(RP, "textures/ui/succubi_ui")
ICONS = os.path.join(UI, "icons")
os.makedirs(ICONS, exist_ok=True)
rng = np.random.default_rng(777)

VIOLET = (170, 70, 255)
MAGENTA = (255, 60, 190)


def noise(w, h, cells=12, seed=0):
    g = np.random.default_rng(seed).random((cells, int(cells * w / h) + 1)).astype(np.float32)
    return np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255


def glow_layer(size, draw_fn, radius, color, strength=1.0):
    m = Image.new("L", size, 0)
    draw_fn(ImageDraw.Draw(m))
    g = m.filter(ImageFilter.GaussianBlur(radius))
    a = np.clip(np.array(g, np.float32) / 255 * strength * 2.2, 0, 1)
    out = np.zeros((size[1], size[0], 4), np.float32)
    out[..., :3] = np.array(color, np.float32) / 255
    out[..., 3] = a
    return Image.fromarray((out * 255).astype(np.uint8), "RGBA")


def sigil(d, cx, cy, r, color, width=2):
    # a ring with a five-point star and small runes on the ring
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)
    pts = [(cx + r * 0.82 * math.sin(math.radians(a)), cy - r * 0.82 * math.cos(math.radians(a))) for a in range(0, 720, 144)]
    d.line(pts, fill=color, width=width)
    for k in range(10):
        a = math.radians(k * 36 + 18)
        x, y = cx + r * 1.22 * math.sin(a), cy - r * 1.22 * math.cos(a)
        d.line([(x - 2, y - 3), (x + 2, y + 3)], fill=color, width=1)
        d.line([(x + 2, y - 3), (x, y)], fill=color, width=1)


def window():
    W, H = 640, 440
    yy = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    n = noise(W, H, 10, 1) * 0.6 + noise(W, H, 40, 2) * 0.4
    r = 0.06 + 0.05 * n - 0.03 * yy
    g = 0.02 + 0.02 * n
    b = 0.10 + 0.08 * n - 0.04 * yy
    base = np.dstack([r, g, b, np.ones_like(r)])
    img = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), "RGBA")
    # faint watermark eye in the middle
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wm)
    d.ellipse([W / 2 - 120, H / 2 - 36, W / 2 + 120, H / 2 + 64], outline=(120, 50, 200, 40), width=3)
    d.ellipse([W / 2 - 30, H / 2 - 16, W / 2 + 30, H / 2 + 44], outline=(120, 50, 200, 40), width=3)
    img.alpha_composite(wm)
    # header band
    head = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(head)
    for y in range(0, 50):
        k = 1 - y / 50
        d.line([(4, y + 3), (W - 5, y + 3)], fill=(int(60 + 50 * k), int(10 + 8 * k), int(90 + 70 * k), 255))
    img.alpha_composite(head)
    # glowing border + header line + sigil
    def border(dr):
        dr.rounded_rectangle([3, 3, W - 4, H - 4], radius=10, outline=255, width=3)
        dr.line([(6, 53), (W - 7, 53)], fill=255, width=2)
    img.alpha_composite(glow_layer((W, H), border, 6, VIOLET, 0.9))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 3, W - 4, H - 4], radius=10, outline=(210, 140, 255, 255), width=2)
    d.line([(6, 53), (W - 7, 53)], fill=(220, 120, 255, 255), width=2)
    img.alpha_composite(glow_layer((W, H), lambda dr: sigil(dr, 30, 28, 14, 255, 3), 4, MAGENTA, 1.0))
    sigil(ImageDraw.Draw(img), 30, 28, 14, (255, 170, 230, 255), 2)
    # corner runes
    for (x, y) in ((16, H - 18), (W - 18, H - 18)):
        d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(200, 120, 255, 200), width=2)
        d.line([(x, y - 8), (x, y + 8)], fill=(200, 120, 255, 200), width=1)
    img.save(os.path.join(UI, "list_curse.png"))
    # the small modal (text input) window uses the same look
    img.resize((640, 440)).save(os.path.join(UI, "modal_curse.png"))


def button(state):
    W, H = 544, 62
    x = np.linspace(0, 1, W)[None, :] * np.ones((H, 1))
    y = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    lift = {"default": 0.0, "hover": 0.08, "pressed": -0.02}[state]
    r = 0.10 + 0.06 * (1 - x) + lift * 1.3 - 0.03 * y
    g = 0.03 + 0.02 * (1 - x) + lift * 0.3
    b = 0.16 + 0.08 * (1 - x) + lift * 1.6 - 0.04 * y
    img = Image.fromarray((np.clip(np.dstack([r, g, b, np.ones_like(r)]), 0, 1) * 255).astype(np.uint8), "RGBA")
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([1, 1, W - 2, H - 2], radius=8, fill=255)
    img.putalpha(mask)
    color = MAGENTA if state == "hover" else VIOLET
    def edge(dr):
        dr.rounded_rectangle([2, 2, W - 3, H - 3], radius=8, outline=255, width=2)
        dr.rectangle([4, 6, 10, H - 7], fill=255)
    if state != "pressed":
        img.alpha_composite(glow_layer((W, H), edge, 3 if state == "default" else 5, color, 0.7 if state == "default" else 1.1))
    d = ImageDraw.Draw(img)
    rim = (255, 150, 230, 255) if state == "hover" else (150, 90, 220, 255) if state == "default" else (100, 60, 150, 255)
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=8, outline=rim, width=2)
    d.rectangle([5, 7, 9, H - 8], fill=(255, 90, 210, 255) if state != "pressed" else (170, 60, 150, 255))
    img.save(os.path.join(UI, f"btn_curse_{state}.png"))


def close_x(state):
    S = 36
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fill = {"default": (40, 12, 60, 255), "hover": (90, 20, 110, 255), "pressed": (25, 8, 40, 255)}[state]
    d.rounded_rectangle([2, 2, S - 3, S - 3], radius=7, fill=fill, outline=(200, 120, 255, 255), width=2)
    c = (255, 170, 235, 255) if state == "hover" else (230, 180, 255, 255)
    d.line([(11, 11), (S - 12, S - 12)], fill=c, width=3)
    d.line([(S - 12, 11), (11, S - 12)], fill=c, width=3)
    img.save(os.path.join(UI, f"x_curse_{state}.png"))


# ---------------------------------------------------------------- icons (64x64, drawn at 4x then glowed)
def icon(name, draw_fn, color=(235, 190, 255)):
    S, K = 64, 4
    m = Image.new("L", (S * K, S * K), 0)
    draw_fn(ImageDraw.Draw(m), K)
    m = m.resize((S, S), Image.LANCZOS)
    arr = np.array(m, np.float32) / 255
    glow = np.array(m.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    out = np.zeros((S, S, 4), np.float32)
    gc = np.array(MAGENTA, np.float32) / 255
    fc = np.array(color, np.float32) / 255
    a = np.clip(arr + glow * 0.9, 0, 1)
    rgb = (fc * arr[..., None] + gc * (glow * (1 - arr))[..., None]) / np.maximum(a[..., None], 1e-3)
    out[..., :3] = np.clip(rgb, 0, 1)
    out[..., 3] = a
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(os.path.join(ICONS, f"curse_{name}.png"))


def person(d, K, cx, cy, s=1.0, w=255):
    d.ellipse([(cx - 6 * s) * K, (cy - 18 * s) * K, (cx + 6 * s) * K, (cy - 6 * s) * K], fill=w)
    d.rounded_rectangle([(cx - 9 * s) * K, (cy - 4 * s) * K, (cx + 9 * s) * K, (cy + 16 * s) * K], radius=int(5 * s * K), fill=w)


def icons():
    icon("all", lambda d, K: ([d.ellipse([(32 - r) * K, (32 - r) * K, (32 + r) * K, (32 + r) * K], outline=255, width=3 * K) for r in (26, 17)],
                              [d.ellipse([(x - 4) * K, (y - 4) * K, (x + 4) * K, (y + 4) * K], fill=255) for x, y in ((32, 10), (52, 38), (14, 42), (32, 32))]))
    icon("one", lambda d, K: person(d, K, 32, 36, 1.2))
    icon("two", lambda d, K: (person(d, K, 22, 38, 1.0), person(d, K, 43, 38, 1.0)))
    icon("pick", lambda d, K: (d.ellipse([12 * K, 12 * K, 52 * K, 52 * K], outline=255, width=3 * K),
                               d.line([(32 * K, 4 * K), (32 * K, 22 * K)], fill=255, width=3 * K), d.line([(32 * K, 42 * K), (32 * K, 60 * K)], fill=255, width=3 * K),
                               d.line([(4 * K, 32 * K), (22 * K, 32 * K)], fill=255, width=3 * K), d.line([(42 * K, 32 * K), (60 * K, 32 * K)], fill=255, width=3 * K),
                               d.ellipse([28 * K, 28 * K, 36 * K, 36 * K], fill=255)))
    icon("radius", lambda d, K: ([d.arc([(32 - r) * K, (32 - r) * K, (32 + r) * K, (32 + r) * K], 200, 340, fill=255, width=3 * K) for r in (10, 18, 26)],
                                 d.ellipse([28 * K, 40 * K, 36 * K, 48 * K], fill=255)))
    icon("self_on", lambda d, K: (person(d, K, 26, 38, 1.1), d.line([(40 * K, 34 * K), (47 * K, 42 * K), (60 * K, 24 * K)], fill=255, width=4 * K)), (190, 255, 210))
    icon("self_off", lambda d, K: (person(d, K, 26, 38, 1.1), d.line([(42 * K, 24 * K), (60 * K, 42 * K)], fill=255, width=4 * K),
                                   d.line([(60 * K, 24 * K), (42 * K, 42 * K)], fill=255, width=4 * K)), (255, 170, 170))
    icon("random", lambda d, K: (d.rounded_rectangle([12 * K, 12 * K, 52 * K, 52 * K], radius=8 * K, outline=255, width=3 * K),
                                 [d.ellipse([(x - 4) * K, (y - 4) * K, (x + 4) * K, (y + 4) * K], fill=255) for x, y in ((22, 22), (32, 32), (42, 42), (42, 22), (22, 42))]))
    icon("trace", lambda d, K: (d.ellipse([14 * K, 26 * K, 28 * K, 52 * K], fill=255), [d.ellipse([(x - 3) * K, (y - 3) * K, (x + 3) * K, (y + 3) * K], fill=255) for x, y in ((14, 20), (20, 17), (26, 19))],
                                d.ellipse([36 * K, 14 * K, 50 * K, 40 * K], fill=255), [d.ellipse([(x - 3) * K, (y - 3) * K, (x + 3) * K, (y + 3) * K], fill=255) for x, y in ((38, 8), (44, 6), (50, 9))]))
    icon("sight", lambda d, K: (d.chord([6 * K, 16 * K, 58 * K, 48 * K], 180, 360, outline=255, width=3 * K), d.chord([6 * K, 16 * K, 58 * K, 48 * K], 0, 180, outline=255, width=3 * K),
                                d.ellipse([24 * K, 24 * K, 40 * K, 40 * K], fill=255)))
    icon("sound", lambda d, K: (d.polygon([(10 * K, 26 * K), (20 * K, 26 * K), (32 * K, 14 * K), (32 * K, 50 * K), (20 * K, 38 * K), (10 * K, 38 * K)], fill=255),
                                [d.arc([(32 - r) * K, (32 - r) * K, (32 + r) * K, (32 + r) * K], 300, 60, fill=255, width=3 * K) for r in (12, 20, 28)]))
    icon("screen", lambda d, K: (d.rounded_rectangle([6 * K, 10 * K, 58 * K, 46 * K], radius=4 * K, outline=255, width=3 * K),
                                 d.line([(32 * K, 46 * K), (32 * K, 54 * K)], fill=255, width=3 * K), d.line([(20 * K, 56 * K), (44 * K, 56 * K)], fill=255, width=3 * K),
                                 d.ellipse([24 * K, 18 * K, 30 * K, 26 * K], fill=255), d.ellipse([34 * K, 18 * K, 40 * K, 26 * K], fill=255), d.arc([22 * K, 26 * K, 42 * K, 40 * K], 200, 340, fill=255, width=3 * K)))
    icon("fight", lambda d, K: (d.polygon([(32 * K, 6 * K), (54 * K, 32 * K), (32 * K, 58 * K), (10 * K, 32 * K)], outline=255, width=3 * K),
                                d.polygon([(32 * K, 18 * K), (42 * K, 32 * K), (32 * K, 46 * K), (22 * K, 32 * K)], fill=255)), (255, 220, 140))


def staff_item():
    S = 64
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(14, 56), (40, 22)], fill=(70, 40, 30, 255), width=6)
    d.line([(14, 56), (40, 22)], fill=(110, 70, 50, 255), width=3)
    for t in (0.3, 0.55):
        x, y = 14 + (40 - 14) * t, 56 + (22 - 56) * t
        d.line([(x - 4, y - 3), (x + 4, y + 3)], fill=(180, 140, 60, 255), width=2)
    img.alpha_composite(glow_layer((S, S), lambda dr: dr.ellipse([34, 6, 56, 28], fill=255), 5, MAGENTA, 1.0))
    d.polygon([(45, 4), (54, 16), (45, 30), (36, 16)], fill=(170, 80, 255, 255), outline=(240, 200, 255, 255))
    d.polygon([(45, 8), (50, 16), (45, 24), (40, 16)], fill=(230, 170, 255, 255))
    d.arc([30, 8, 60, 34], 200, 340, fill=(190, 150, 70, 255), width=2)
    img.save(os.path.join(RP, "textures/items/extra/curse_staff.png"))


if __name__ == "__main__":
    window()
    for s in ("default", "hover", "pressed"):
        button(s)
        close_x(s)
    icons()
    staff_item()
    print("curse skin written")
