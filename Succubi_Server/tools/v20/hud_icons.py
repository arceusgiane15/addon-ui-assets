"""Gauge icons that change with the value, Don't Starve style. Five stages each (4 = full ... 0 = almost gone):

  heart   plump and shiny -> hairline crack -> split crack, chipped -> torn in two, dripping -> shattered halves
  food    juicy drumstick -> one bite -> two bites -> a scrap on the bone -> bare cracked bone
  water   full drop -> 3/4 -> half -> a puddle in a cracked empty drop -> dry cracked shell full of dust
  brain   calm pink -> worried, a vein -> grey-violet, dark veins, stitches -> cracked, an eye opens -> black,
          horns, one glowing red eye

Pixel art on a 22 x 22 grid (shown at 11 GUI units), dark outline, three-tone shading like the other icons."""
import math
from PIL import Image, ImageDraw
import pixel as px

N = 22
INK = (10, 5, 9, 255)
WHITE = (255, 250, 252, 255)


def blank():
    return Image.new('RGBA', (N, N))


def mask_of(fn):
    m = Image.new('L', (N, N), 0)
    fn(ImageDraw.Draw(m))
    return m


def shade(mask, light, main, dark, lx=0.45, ly=0.8):
    """colour a mask: light top-left, dark bottom-right (hard pixel bands)"""
    im = blank()
    p, q = im.load(), mask.load()
    pts = [(x, y) for y in range(N) for x in range(N) if q[x, y] > 127]
    if not pts:
        return im
    x0 = min(x for x, _ in pts); x1 = max(x for x, _ in pts)
    y0 = min(y for _, y in pts); y1 = max(y for _, y in pts)
    for x, y in pts:
        t = ((x - x0) / max(1, x1 - x0) * lx + (y - y0) / max(1, y1 - y0) * ly) / (lx + ly)
        c = light if t < 0.3 else main if t < 0.72 else dark
        p[x, y] = px.rgba(c)
    return im


def cut(mask, fn):
    """erase fn's shape from a mask"""
    d = ImageDraw.Draw(mask)
    fn(d)
    return mask


def crack(im, pts, dark=(40, 8, 20), light=None):
    d = ImageDraw.Draw(im)
    d.line(pts, fill=px.rgba(dark), width=1)
    if light:
        d.line([(x + 1, y) for x, y in pts], fill=px.rgba(light), width=1)
    return im


def keep_inside(im, mask):
    """clip decorations to a shape"""
    out = blank()
    out.paste(im, (0, 0), mask)
    return out


def done(*layers, outline=True):
    im = blank()
    for l in layers:
        im.alpha_composite(l)
    return px.outline(im, INK) if outline else im


def dots(im, pts, col):
    q = im.load()
    for x, y in pts:
        if 0 <= x < N and 0 <= y < N:
            q[x, y] = px.rgba(col)
    return im


# ------------------------------------------------------------------------------------------ heart
def heart_mask(scale=1.0, dx=0, dy=0):
    def f(d):
        s = scale
        cx, cy = 11 + dx, 11 + dy
        d.ellipse([cx - 9.5 * s, cy - 8 * s, cx - 0.5 * s, cy + 1 * s], fill=255)
        d.ellipse([cx - 0.5 * s, cy - 8 * s, cx + 8.5 * s, cy + 1 * s], fill=255)
        d.polygon([(cx - 9.3 * s, cy - 2.5 * s), (cx + 8.3 * s, cy - 2.5 * s), (cx - 0.5 * s, cy + 9.5 * s)], fill=255)
    return mask_of(f)


def heart(tier, pal):
    light, main, dark = pal
    if tier >= 3:
        m = heart_mask()
        im = shade(m, light, main, dark)
        dots(im, [(5, 5), (6, 5), (5, 6), (7, 4)], WHITE)
        if tier == 3:
            crack(im, [(11, 4), (10, 7), (12, 9)], dark=px.shade(dark, 0.55))
        return done(im)
    if tier == 2:
        m = heart_mask(0.96)
        cut(m, lambda d: d.polygon([(18, 3), (20, 3), (20, 6)], fill=0))          # chipped corner
        im = shade(m, px.mix(light, main, 0.4), px.shade(main, 0.85), px.shade(dark, 0.85))
        crack(im, [(11, 3), (9, 7), (12, 10), (10, 14), (11, 17)], dark=px.shade(dark, 0.4))
        crack(im, [(9, 7), (6, 9)], dark=px.shade(dark, 0.4))
        dots(im, [(5, 6), (6, 5)], px.mix(light, WHITE, 0.3))
        return done(im)
    # 1: torn in two, 0: halves fall apart
    gap = 1 if tier == 1 else 2
    left = mask_of(lambda d: None)
    right = mask_of(lambda d: None)
    full = heart_mask(0.94)
    L, R, F = left.load(), right.load(), full.load()
    jag = [11, 10, 12, 10, 11, 9, 12, 10, 11, 12, 10, 11, 12, 11, 10, 11, 12, 11, 10, 11, 11, 11]
    for y in range(N):
        for x in range(N):
            if F[x, y] > 127:
                if x < jag[y] - gap // 2:
                    L[x, y] = 255
                elif x > jag[y] + (gap - gap // 2) - 1:
                    R[x, y] = 255
    c = (px.shade(main, 0.75), px.shade(main, 0.6), px.shade(dark, 0.6)) if tier == 1 else \
        (px.shade(main, 0.55), px.shade(dark, 0.7), px.shade(dark, 0.45))
    lh = shade(left, *c)
    rh = shade(right, *c)
    if tier == 0:
        lh = lh.rotate(12, center=(8, 16), resample=Image.NEAREST).transform((N, N), Image.AFFINE, (1, 0, 1, 0, 1, -1))
        rh = rh.rotate(-12, center=(14, 16), resample=Image.NEAREST).transform((N, N), Image.AFFINE, (1, 0, -1, 0, 1, 0))
    im = done(lh, rh)
    drops = [(11, 19), (11, 20)] if tier == 1 else [(10, 19), (10, 20), (12, 21)]
    return dots(im, drops, px.shade(dark, 0.9))


# ------------------------------------------------------------------------------------------ food (drumstick)
def drumstick(tier, meat=((255, 200, 128), (214, 118, 48), (128, 60, 22))):
    bone_col = ((248, 240, 228), (220, 210, 196), (160, 148, 134))
    if tier == 0:
        bone_col = ((214, 206, 196), (170, 160, 150), (110, 100, 92))
    bone = mask_of(lambda d: (d.line([(4, 18), (11, 11)], fill=255, width=3), d.ellipse([1, 16, 6, 21], fill=255), d.ellipse([3, 18, 8, 22], fill=255)))
    if tier == 0:
        bone = mask_of(lambda d: (d.line([(4, 18), (15, 7)], fill=255, width=3), d.ellipse([1, 16, 6, 21], fill=255),
                                  d.ellipse([3, 18, 8, 22], fill=255), d.ellipse([13, 3, 18, 8], fill=255), d.ellipse([15, 5, 20, 10], fill=255)))
    b = shade(bone, *bone_col)
    layers = [b]
    if tier >= 1:
        size = {4: 1.0, 3: 1.0, 2: 0.86, 1: 0.55}[tier]
        cx, cy = 14, 8
        r = 7.2 * size
        m = mask_of(lambda d: (d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255),
                               d.polygon([(cx - r * 0.7, cy + r * 0.3), (cx - r * 0.1, cy + r * 0.9), (8, 14)], fill=255)))
        if tier <= 3:
            cut(m, lambda d: d.ellipse([16, -1, 23, 5], fill=0))             # first bite
        if tier <= 2:
            cut(m, lambda d: d.ellipse([19, 6, 25, 12], fill=0))             # second bite
        c = meat if tier >= 2 else tuple(px.shade(x, 0.85) for x in meat)
        mt = shade(m, *c)
        if tier >= 3:
            dots(mt, [(11, 3), (12, 3), (11, 4)], (255, 236, 200))
        if tier <= 3:
            d = ImageDraw.Draw(mt)
            for (x, y) in ((17, 5), (18, 4), (20, 6)):                        # tooth marks on the bite edge
                if mt.getpixel((x, y))[3]:
                    d.point((x, y), fill=px.rgba(px.shade(meat[2], 0.8)))
        layers.append(mt)
    im = done(*layers)
    if tier == 0:
        crack(im, [(9, 12), (10, 13), (9, 14)], dark=(90, 80, 72))
    return im


# ------------------------------------------------------------------------------------------ water drop
def drop_mask():
    return mask_of(lambda d: (d.ellipse([4, 8, 18, 22], fill=255), d.polygon([(11, 0), (4.3, 14), (17.7, 14)], fill=255)))


def drop(tier):
    m = drop_mask()
    water = ((190, 240, 255), (51, 181, 240), (18, 96, 160))
    glass = ((120, 150, 170), (70, 90, 110), (46, 58, 74))
    if tier == 4:
        im = shade(m, *water)
        dots(im, [(7, 12), (7, 13), (8, 11), (7, 14)], WHITE)
        return done(im)
    level = {3: 8, 2: 13, 1: 18, 0: 99}[tier]         # water line (y)
    empty = shade(m, *glass)
    if tier == 0:
        empty = shade(m, (176, 150, 112), (140, 112, 76), (96, 72, 46))       # dust
    full = shade(m, *water)
    under = mask_of(lambda d: d.rectangle([0, min(level, N), N, N], fill=255 if level < N else 0))
    im = blank()
    im.alpha_composite(empty)
    water_part = blank()
    water_part.paste(full, (0, 0), under)
    im.alpha_composite(water_part)
    d = ImageDraw.Draw(im)
    if level < N:
        for x in range(N):
            if m.getpixel((x, level)) > 127:
                d.point((x, level), fill=px.rgba((200, 244, 255)))          # surface shine
    dots(im, [(7, 11), (7, 12)], (200, 220, 235))
    if tier <= 1:
        crack(im, [(11, 3), (10, 6), (12, 8)], dark=(30, 26, 22))
        crack(im, [(15, 13), (13, 15), (14, 18)], dark=(30, 26, 22))
    if tier == 0:
        crack(im, [(6, 16), (8, 18), (7, 20)], dark=(60, 44, 30))
        cm = mask_of(lambda d: d.polygon([(10, 0), (12, 0), (11, 3)], fill=255))
        im.paste(blank(), (0, 0), cm)                                       # tip snapped off
    return done(im)


# ------------------------------------------------------------------------------------------ brain
BRAIN_ROWS = [
    "......................",
    "......................",
    ".....oooo.oooo........",
    "...ooLLLLoLLLLoo......",
    "..oLLLMMLoLMMLLLo.....",
    ".oLLMFFMMoMMFFMMLo....",
    ".oLMMMMFMoMFMMMMDo....",
    "oLMFFMMMMoMMMMFFMDo...",
    "oMMMMFFMMoMMFFMMMDo...",
    "oMFMMMMMMoMMMMMMFDo...",
    "oMMFFMMMMoMMMFFMDDo...",
    ".oMMMMFMMoMMFMMMDo....",
    ".oDMMMMMMoMMMMMDDo....",
    "..oDDMMMMoMMMMDDo.....",
    "...ooDDDDoDDDDoo......",
    ".....ooo.ooooo........",
    "............oo........",
    "............o.........",
]


def brain(tier):
    pals = {
        4: {'L': (255, 206, 240), 'M': (230, 140, 226), 'D': (160, 76, 184), 'F': (140, 58, 166)},
        3: {'L': (236, 186, 236), 'M': (204, 124, 216), 'D': (134, 64, 170), 'F': (110, 40, 150)},
        2: {'L': (196, 170, 214), 'M': (156, 118, 186), 'D': (98, 66, 136), 'F': (70, 30, 100)},
        1: {'L': (140, 100, 170), 'M': (104, 64, 140), 'D': (64, 34, 96), 'F': (40, 12, 60)},
        0: {'L': (70, 40, 84), 'M': (46, 22, 60), 'D': (28, 10, 38), 'F': (170, 20, 40)},
    }[tier]
    pal = dict(pals)
    pal['o'] = INK
    rows = BRAIN_ROWS
    im = px.from_rows(rows, pal)
    im = im.crop((0, 0, N, N)) if im.size != (N, N) else im
    canvas = blank()
    canvas.alpha_composite(im, (2, 1))
    d = ImageDraw.Draw(canvas)
    if tier == 3:
        d.line([(6, 9), (8, 11), (7, 13)], fill=(170, 40, 90, 255))                   # worry vein
    if tier == 2:
        d.line([(5, 8), (8, 10), (6, 13)], fill=(120, 20, 60, 255))
        d.line([(15, 7), (17, 10)], fill=(120, 20, 60, 255))
        for y in (10, 12, 14):                                                        # stitches
            d.point((11, y), fill=(230, 220, 200, 255)); d.point((13, y), fill=(230, 220, 200, 255))
    if tier <= 1:
        d.line([(11, 4), (10, 8), (12, 11), (10, 15)], fill=(20, 4, 20, 255))         # crack down the middle
        d.line([(5, 9), (8, 10)], fill=(20, 4, 20, 255))
        eye_c = (255, 220, 60) if tier == 1 else (255, 40, 60)
        r = 2 if tier == 1 else 3
        d.ellipse([11 - r, 10 - r + 1, 11 + r, 10 + r - 1], fill=(250, 244, 230, 255))
        d.ellipse([10, 9, 12, 11], fill=px.rgba(eye_c))
        d.point((11, 10), fill=(10, 0, 0, 255))
    if tier == 0:
        for hx, sgn in ((5, -1), (17, 1)):                                            # little horns
            d.polygon([(hx, 5), (hx + sgn * 3, 1), (hx + sgn * 1, 5)], fill=(30, 8, 30, 255))
        d.line([(3, 16), (1, 20)], fill=(40, 10, 50, 255))                            # tendrils
        d.line([(18, 16), (21, 19)], fill=(40, 10, 50, 255))
        d.line([(9, 17), (8, 21)], fill=(40, 10, 50, 255))
    return px.outline(canvas, INK)


def tint(im, pal):
    """recolour an icon by luminance into a palette (poison / wither heart, sick food)"""
    light, main, dark = pal
    out = im.copy()
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = p[x, y]
            if a and (r, g, b) != INK[:3]:
                lum = (r * 0.3 + g * 0.59 + b * 0.11) / 255
                c = light if lum > 0.62 else main if lum > 0.36 else dark
                p[x, y] = px.rgba(c, a)
    return out


def all_icons(stats):
    """{'health': {tier: img}, 'health_poison': ..., 'food': ..., 'food_sick': ..., 'thirst': ..., 'sanity': ...}"""
    out = {}
    for key, pal in (('health', stats['health']), ('health_poison', stats['health_poison']), ('health_wither', stats['health_wither'])):
        out[key] = {t: heart(t, pal) for t in range(5)}
    out['food'] = {t: drumstick(t) for t in range(5)}
    out['food_sick'] = {t: drumstick(t, meat=((200, 214, 110), (140, 150, 50), (80, 90, 24))) for t in range(5)}
    out['thirst'] = {t: drop(t) for t in range(5)}
    out['sanity'] = {t: brain(t) for t in range(5)}
    return out
