"""Tiny pixel-art toolkit: draw at 1 texel = 1 GUI unit, save upscaled (nearest) so the game keeps it crisp."""
from PIL import Image, ImageDraw

SCALE = 4

# Succubi palette
INK = (13, 7, 11, 255)          # outlines
PLUM_0 = (24, 12, 21, 255)      # darkest plum
PLUM_1 = (38, 20, 33, 255)
PLUM_2 = (58, 31, 50, 255)
PLUM_3 = (84, 46, 72, 255)
PINK = (255, 79, 163, 255)
PINK_L = (255, 155, 203, 255)
PINK_D = (176, 34, 104, 255)
CRIMSON = (139, 30, 63, 255)
GOLD = (242, 193, 78, 255)
GOLD_D = (168, 118, 30, 255)
WHITE = (255, 246, 250, 255)


def rgba(c, a=None):
    c = tuple(c)
    if len(c) == 3:
        c = c + (255,)
    return c if a is None else c[:3] + (a,)


def canvas(w, h, fill=(0, 0, 0, 0)):
    return Image.new('RGBA', (w, h), fill)


def up(im, scale=SCALE):
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def save(im, path, scale=SCALE):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    up(im, scale).save(path, optimize=True)


def from_rows(rows, palette):
    """rows: list of strings, one char per pixel; palette: char -> rgba ('.' / ' ' = transparent)"""
    h, w = len(rows), max(len(r) for r in rows)
    im = canvas(w, h)
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in palette:
                px[x, y] = rgba(palette[ch])
    return im


def outline(im, color=INK):
    """1px outline around every opaque pixel (4-neighbour), drawn behind"""
    w, h = im.size
    out = canvas(w, h)
    src = im.load()
    o = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] > 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] > 128:
                    o[x, y] = rgba(color)
                    break
    out.alpha_composite(im)
    return out


def pill(w, h, fill, edge=INK, round_=1):
    """rectangle with the corner pixels cut (pixel-art rounded)"""
    im = canvas(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=rgba(edge))
    d.rectangle([1, 1, w - 2, h - 2], fill=rgba(fill))
    px = im.load()
    for r in range(round_):
        for (x, y) in ((r, 0), (0, r), (w - 1 - r, 0), (w - 1, r), (r, h - 1), (0, h - 1 - r), (w - 1 - r, h - 1), (w - 1, h - 1 - r)):
            px[x, y] = (0, 0, 0, 0)
    if round_:
        for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
            px[x, y] = rgba(edge)
    return im


def shade(c, k):
    c = rgba(c)
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (c[3],)


def mix(a, b, t):
    a, b = rgba(a), rgba(b)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))


# 3x5 digits for HUD numbers
DIGITS = {
    '0': ['###', '#.#', '#.#', '#.#', '###'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['###', '..#', '###', '#..', '###'], '3': ['###', '..#', '.##', '..#', '###'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '###', '..#', '###'],
    '6': ['###', '#..', '###', '#.#', '###'], '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['###', '#.#', '###', '#.#', '###'], '9': ['###', '#.#', '###', '..#', '###'],
}


def digit(ch, color=WHITE, shadow=INK):
    """4x6: glyph + 1px drop shadow to the bottom-right"""
    im = canvas(4, 6)
    px = im.load()
    rows = DIGITS[ch]
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '#':
                px[x + 1, y + 1] = rgba(shadow)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '#':
                px[x, y] = rgba(color)
    return im
