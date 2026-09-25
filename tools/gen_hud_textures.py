"""Textures for the v1.1.9 HUD (RP textures/ui/succubi_hud). HUD art is drawn at 4x (a 22 px gauge = 88 px).

 clock_face.png     144x144  Don't Starve style day clock: 16 segments, day / dusk / night / dawn, dark centre
 clock_hands.png    8x6 frames of 144x144 = 48 hand positions (frame n = 6:00 + n * 30 min, clockwise from the top)
 arrow_up_X.png     24x20    rising arrow in the gauge colour (X = h f t s)
 arrow_down_X.png   24x20    falling arrow
 fx_static.png      4 frames of 192x108  full-screen TV static (grey noise)
 fx_static_bands.png 6 frames of 256x144 static in a few horizontal bands (the "แวบ" glitch)
 fx_tear.png        4 frames of 256x144  torn lines with red / cyan fringes
 fx_scanlines.png   256x144 every other row darkened
 fx_roll.png        64x64    soft dark band that rolls up the screen
"""
import math
import os
import random

from PIL import Image, ImageDraw

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon", "Succubi Server RP", "textures", "ui",
                   "succubi_hud")
rnd = random.Random(1109)

INK = (18, 8, 16, 255)
DISC = (39, 23, 36, 245)
COLORS = {  # segment colours
    "day": (247, 196, 84, 255),
    "dusk": (214, 88, 72, 255),
    "night": (58, 66, 138, 255),
    "dawn": (232, 146, 118, 255),
}
GAUGE = {"h": (242, 74, 112), "f": (246, 160, 58), "t": (70, 170, 245), "s": (178, 108, 232)}
S = 144  # clock size (36 px on screen)
C = S / 2


def phase(tod):
    if tod < 12000:
        return "day"
    if tod < 13500:
        return "dusk"
    if tod < 22500:
        return "night"
    return "dawn"


def supersample(draw_fn, size, factor=4):
    big = Image.new("RGBA", (size[0] * factor, size[1] * factor), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), factor)
    return big.resize(size, Image.LANCZOS)


def clock_face():
    def paint(d, k):
        c = C * k
        r_out, r_ring, r_in = 70 * k, 64 * k, 40 * k
        d.ellipse((c - r_out, c - r_out, c + r_out, c + r_out), fill=INK)
        # 16 segments, 0 = top = 6:00, clockwise; angle 0 in PIL is 3 o'clock
        for i in range(16):
            tod = i * 1500 + 750
            start = -90 + i * 22.5
            d.pieslice((c - r_ring, c - r_ring, c + r_ring, c + r_ring), start + 1.2, start + 22.5 - 1.2,
                       fill=COLORS[phase(tod)])
        d.ellipse((c - r_in - 3 * k, c - r_in - 3 * k, c + r_in + 3 * k, c + r_in + 3 * k), fill=INK)
        d.ellipse((c - r_in, c - r_in, c + r_in, c + r_in), fill=DISC)

    return supersample(paint, (S, S))


def clock_hand(frame):
    def paint(d, k):
        c = C * k
        a = math.radians(-90 + frame * 7.5)
        r0, r1 = 41 * k, 69 * k
        x0, y0 = c + math.cos(a) * r0, c + math.sin(a) * r0
        x1, y1 = c + math.cos(a) * r1, c + math.sin(a) * r1
        d.line((x0, y0, x1, y1), fill=INK, width=9 * k)
        d.line((x0, y0, x1, y1), fill=(255, 244, 226, 255), width=4 * k)
        # round tip on the rim
        tip = 6 * k
        d.ellipse((x1 - tip, y1 - tip, x1 + tip, y1 + tip), fill=INK)
        d.ellipse((x1 - tip + 3 * k, y1 - tip + 3 * k, x1 + tip - 3 * k, y1 + tip - 3 * k), fill=(255, 244, 226, 255))

    return supersample(paint, (S, S))


def clock_hands():
    atlas = Image.new("RGBA", (S * 8, S * 6), (0, 0, 0, 0))
    for n in range(48):
        atlas.alpha_composite(clock_hand(n), ((n % 8) * S, (n // 8) * S))
    return atlas


def arrow(color, up):
    w, h = 24, 20
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(2, 16), (12, 4), (22, 16), (16, 16), (12, 11), (8, 16)]  # chevron pointing up
    if not up:
        pts = [(x, h - y) for x, y in pts]
    d.polygon(pts, fill=INK)
    inner = [(5, 14), (12, 6), (19, 14), (16, 14), (12, 9), (8, 14)]
    if not up:
        inner = [(x, h - y) for x, y in inner]
    d.polygon(inner, fill=color + (255,))
    return img


def noise_frame(w, h, bands=None):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    rows = range(h) if bands is None else [y for y0, y1 in bands for y in range(y0, min(h, y1))]
    for y in rows:
        row_shift = rnd.randint(-40, 40)  # rows a little brighter / darker, like a real signal
        for x in range(w):
            v = max(0, min(255, rnd.choice((20, 70, 128, 180, 235)) + row_shift))
            px[x, y] = (v, v, v, 235)
    return img


def strip(frames):
    w, h = frames[0].size
    out = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f, (i * w, 0))
    return out


def band_list(count, h):
    bands = []
    for _ in range(count):
        y0 = rnd.randint(0, h - 4)
        bands.append((y0, y0 + rnd.choice((2, 3, 5, 8, 13))))
    return bands


def tear_frame(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(rnd.randint(3, 6)):
        y = rnd.randint(0, h - 3)
        th = rnd.choice((1, 1, 2, 3))
        x0 = rnd.randint(-40, w // 2)
        x1 = x0 + rnd.randint(w // 3, w)
        shift = rnd.choice((-3, -2, 2, 3))
        d.rectangle((x0 + shift, y, x1 + shift, y + th), fill=(255, 40, 60, 150))
        d.rectangle((x0 - shift, y, x1 - shift, y + th), fill=(40, 230, 255, 150))
        d.rectangle((x0, y, x1, y + th), fill=(230, 230, 230, 120))
    for _ in range(rnd.randint(1, 3)):  # a displaced grey block
        y = rnd.randint(0, h - 10)
        x = rnd.randint(0, w - 30)
        d.rectangle((x, y, x + rnd.randint(20, 90), y + rnd.randint(3, 9)), fill=(120, 120, 128, 110))
    return img


def scanlines(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(0, h, 2):
        d.line((0, y, w, y), fill=(0, 0, 0, 150))
    return img


def roll():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = img.load()
    for y in range(64):
        a = int(150 * math.sin(math.pi * y / 63) ** 2)
        for x in range(64):
            px[x, y] = (10, 10, 14, a)
    return img


def main():
    save = lambda img, name: img.save(os.path.join(TEX, name + ".png"), optimize=True)
    save(clock_face(), "clock_face")
    save(clock_hands(), "clock_hands")
    for g, color in GAUGE.items():
        save(arrow(color, True), f"arrow_up_{g}")
        save(arrow(color, False), f"arrow_down_{g}")
    w, h = 256, 144
    save(strip([noise_frame(192, 108) for _ in range(4)]), "fx_static")  # coarser: it is a faint veil
    save(strip([noise_frame(w, h, band_list(rnd.randint(2, 4), h)) for _ in range(6)]), "fx_static_bands")
    save(strip([tear_frame(w, h) for _ in range(4)]), "fx_tear")
    save(scanlines(w, h), "fx_scanlines")
    save(roll(), "fx_roll")
    print("HUD textures written to", os.path.relpath(TEX))


if __name__ == "__main__":
    main()
