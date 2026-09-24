"""Shop HUD art in the same style as the vending machine screens (560x360 background, 92x56 menu cards)."""
import math
from PIL import Image, ImageDraw, ImageFilter

SS = 3  # supersampling


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def lighten(c, t):
    return mix(c, (255, 255, 255), t)


def darken(c, t):
    return mix(c, (0, 0, 0), t)


def rrect(d, box, r, fill, outline=None, width=1):
    x0, y0, x1, y1 = [v * SS for v in box]
    d.rounded_rectangle([x0, y0, x1, y1], radius=r * SS, fill=fill, outline=outline, width=width * SS)


def vgrad(size, top, bottom):
    w, h = size
    g = Image.new('RGBA', (w, h))
    px = g.load()
    for y in range(h):
        c = mix(top, bottom, y / max(1, h - 1))
        for x in range(w):
            px[x, y] = c + (255,)
    return g


def paste_masked(base, img, box, radius):
    """paste img into base clipped to a rounded rect (coords unscaled)"""
    x0, y0, x1, y1 = box
    mask = Image.new('L', base.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=radius * SS, fill=255)
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    layer.paste(img.resize(((x1 - x0) * SS, (y1 - y0) * SS)), (x0 * SS, y0 * SS))
    base.paste(layer, (0, 0), Image.composite(layer, Image.new('RGBA', base.size, (0, 0, 0, 0)), mask).split()[3])


# ---------------------------------------------------------------- decorations per shop
def deco_header(key, d, th, W):
    """drawn inside the header bar (x 14..424, y 10..38)"""
    base, dark, acc = th['base'], th['dark'], th['accent']
    if key == 'chicken':      # red / white awning stripes
        for i in range(0, 41):
            x = 264 + i * 10
            if x >= 424: break
            if i % 2 == 0:
                d.rectangle([x * SS, 10 * SS, min(x + 10, 424) * SS, 38 * SS], fill=(248, 242, 230, 255))
        for i in range(0, 42):  # scallops under the header
            cx = 264 + i * 10 + 5
            if cx > 424: break
            col = (248, 242, 230, 255) if i % 2 == 0 else base + (255,)
            d.ellipse([(cx - 5) * SS, 33 * SS, (cx + 5) * SS, 43 * SS], fill=col)
    elif key == 'ramen':      # noren curtain panels + red lanterns
        for i in range(3):
            x = 262 + i * 34
            d.rectangle([x * SS, 10 * SS, (x + 30) * SS, 40 * SS], fill=acc + (255,))
            d.line([(x + 15) * SS, 14 * SS, (x + 15) * SS, 36 * SS], fill=darken(acc, 0.35) + (255,), width=2 * SS)
        for cx in (384, 408):
            d.ellipse([(cx - 9) * SS, 13 * SS, (cx + 9) * SS, 37 * SS], fill=(214, 50, 40, 255), outline=(40, 20, 20, 255), width=SS)
            d.line([(cx - 8) * SS, 25 * SS, (cx + 8) * SS, 25 * SS], fill=(120, 20, 20, 255), width=SS)
    elif key == 'somtum':     # gold mortar & pestle + chilli dots
        d.ellipse([372 * SS, 16 * SS, 412 * SS, 40 * SS], fill=acc + (255,), outline=darken(acc, 0.4) + (255,), width=SS)
        d.rectangle([378 * SS, 16 * SS, 406 * SS, 24 * SS], fill=darken(acc, 0.1) + (255,))
        d.line([398 * SS, 8 * SS, 410 * SS, 24 * SS], fill=(120, 80, 40, 255), width=4 * SS)
        for i, cx in enumerate(range(300, 364, 14)):
            d.ellipse([(cx - 4) * SS, 20 * SS, (cx + 4) * SS, 28 * SS], fill=(214, 40, 30, 255) if i % 2 else (86, 170, 60, 255))
    elif key == 'omelette':   # military stars + chevrons
        for i, cx in enumerate((362, 384, 406)):
            star(d, cx, 24, 8, acc + (255,))
    elif key == 'fried_insects':  # wood planks + skewers
        for i in range(6):
            x = 304 + i * 20
            d.rectangle([x * SS, 12 * SS, (x + 18) * SS, 36 * SS], fill=lighten(base, 0.08 * (i % 2)) + (255,))
        for cx in (326, 356, 386):
            d.line([cx * SS, 12 * SS, (cx + 10) * SS, 36 * SS], fill=(230, 210, 170, 255), width=2 * SS)
            for k in range(3):
                y = 16 + k * 6; x = cx + (y - 12) * 10 / 24
                d.ellipse([(x - 4) * SS, (y - 2) * SS, (x + 4) * SS, (y + 3) * SS], fill=acc + (255,))
    elif key == 'haruto_tea':  # tea leaves + cup
        for cx, cy, ang in ((316, 24, 30), (340, 22, -20), (364, 25, 15)):
            leaf(d, cx, cy, 10, 5, ang, acc + (255,))
        d.rounded_rectangle([388 * SS, 14 * SS, 412 * SS, 38 * SS], radius=4 * SS, fill=(240, 230, 210, 255), outline=(90, 60, 30, 255), width=SS)
        d.line([404 * SS, 6 * SS, 400 * SS, 16 * SS], fill=(30, 30, 30, 255), width=2 * SS)


def deco_extra(key, d, th):
    if key == 'pharmacy':
        for i, cx in enumerate((330, 360)):
            d.rounded_rectangle([(cx - 11) * SS, 18 * SS, (cx + 11) * SS, 30 * SS], radius=6 * SS, fill=(250, 250, 250, 255))
            d.rectangle([cx * SS, 18 * SS, (cx + 11) * SS, 30 * SS], fill=((230, 70, 70) if i == 0 else (60, 130, 220)) + (255,))
        a = 9
        d.rectangle([(398 - a) * SS, 21 * SS, (398 + a) * SS, 27 * SS], fill=(255, 255, 255, 255))
        d.rectangle([395 * SS, (24 - a) * SS, 401 * SS, (24 + a) * SS], fill=(255, 255, 255, 255))
    elif key == 'books':
        for i, c in enumerate(((230, 80, 80), (60, 140, 230), (250, 200, 40), (80, 190, 90), (150, 80, 180), (240, 150, 40))):
            h = 18 + (i % 3) * 3
            d.rectangle([(350 + i * 12) * SS, (36 - h) * SS, (360 + i * 12) * SS, 36 * SS], fill=c + (255,))
            d.rectangle([(350 + i * 12) * SS, (36 - h + 4) * SS, (360 + i * 12) * SS, (36 - h + 6) * SS], fill=(250, 240, 210, 255))
    elif key in ('amulets', 'amuletui'):
        for i, cx in enumerate((360, 386, 412)):
            d.ellipse([(cx - 9) * SS, 15 * SS, (cx + 9) * SS, 33 * SS], fill=(232, 186, 60, 255), outline=(150, 110, 30, 255), width=SS)
            d.ellipse([(cx - 4) * SS, 20 * SS, (cx + 4) * SS, 28 * SS], fill=(120, 30, 30, 255))
    elif key.startswith('seven'):
        for i, c in enumerate(((241, 107, 34), (0, 160, 100), (228, 30, 42))):
            d.rectangle([(352 + i * 24) * SS, 12 * SS, (372 + i * 24) * SS, 36 * SS], fill=c + (255,))


def star(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(((cx + rr * math.cos(a)) * SS, (cy + rr * math.sin(a)) * SS))
    d.polygon(pts, fill=fill)


def leaf(d, cx, cy, a, b, ang, fill):
    pts = []
    t = math.radians(ang)
    for i in range(24):
        u = 2 * math.pi * i / 24
        x, y = a * math.cos(u), b * math.sin(u) * abs(math.cos(u / 2))
        pts.append(((cx + x * math.cos(t) - y * math.sin(t)) * SS, (cy + x * math.sin(t) + y * math.cos(t)) * SS))
    d.polygon(pts, fill=fill)


def background(key, th, kiosk_icon, rows=5, W=560):
    H = 360 + 60 * (rows - 5)
    ex = H - 360
    dx = W - 560
    img = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base, dark, acc, glass = th['base'], th['dark'], th['accent'], th['glass']
    # drop shadow + body
    rrect(d, (6, 8, W - 4, H - 2), 22, (0, 0, 0, 90))
    rrect(d, (4, 4, W - 8, H - 8), 22, base + (255,), outline=darken(base, 0.45) + (255,), width=2)
    rrect(d, (8, 8, W - 12, H - 12), 19, None, outline=lighten(base, 0.25) + (255,), width=1)
    # header bar (decorations drawn for 560 wide, moved right with the header end)
    rrect(d, (14, 10, 424 + dx, 38), 8, dark + (255,))
    deco = Image.new('RGBA', (560 * SS, H * SS), (0, 0, 0, 0)); dd = ImageDraw.Draw(deco)
    deco_header(key, dd, th, 560)
    deco_extra(key, dd, th)
    img.alpha_composite(deco, (dx * SS, 0))
    # menu board (behind the product grid: grid at 18,42)
    rrect(d, (14, 40, 422 + dx, H - 14), 10, darken(dark, 0.25) + (255,), outline=lighten(dark, 0.2) + (255,), width=2)
    for r in range(rows):   # shelves between card rows
        y = 42 + 60 * (r + 1) - 3
        if y < H - 16:
            d.rectangle([18 * SS, y * SS, (418 + dx) * SS, (y + 2) * SS], fill=lighten(dark, 0.12) + (255,))
    # right column: register
    rrect(d, (430 + dx, 40, 546 + dx, H - 14), 10, darken(base, 0.18) + (255,), outline=darken(base, 0.45) + (255,), width=2)
    rrect(d, (438 + dx, 48, 540 + dx, 176), 7, glass + (255,), outline=lighten(glass, 0.3) + (255,), width=2)
    rrect(d, (442 + dx, 52, 536 + dx, 172), 5, darken(glass, 0.2) + (255,))
    rrect(d, (452 + dx, 188, 526 + dx, 204), 4, (30, 30, 34, 255))
    d.rectangle([(468 + dx) * SS, 194 * SS, (510 + dx) * SS, 197 * SS], fill=(0, 0, 0, 255))
    rrect(d, (446 + dx, 210, 532 + dx, 226), 4, (30, 30, 34, 255))
    d.rectangle([(452 + dx) * SS, 216 * SS, (526 + dx) * SS, 219 * SS], fill=(0, 0, 0, 255))
    rrect(d, (442 + dx, 238 + ex, 534 + dx, 338 + ex), 8, lighten(base, 0.12) + (255,), outline=darken(base, 0.4) + (255,), width=2)
    icon = kiosk_icon.convert('RGBA').resize((84 * SS, 84 * SS), Image.LANCZOS)
    img.alpha_composite(icon, ((446 + dx) * SS, (246 + ex) * SS))
    return img.resize((W, H), Image.LANCZOS)


def widen(img, W):
    """3-slice stretch of a 92x56 button (keeps the icon box on the left and the right edge)"""
    img = img.convert('RGBA'); w, h = img.size
    left, right = img.crop((0, 0, 44, h)), img.crop((w - 12, 0, w, h))
    mid = img.crop((44, 0, w - 12, h)).resize((W - 56, h), Image.LANCZOS)
    out = Image.new('RGBA', (W, h), (0, 0, 0, 0))
    out.paste(left, (0, 0)); out.paste(mid, (44, 0)); out.paste(right, (W - 12, 0))
    return out


def card(th, icon, off=False, W=92):
    H = 56
    img = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = th['cell']
    if off:
        c = (96, 96, 100)
    rrect(d, (1, 3, W - 1, 55), 8, darken(c, 0.45) + (255,))            # bottom shadow
    body = vgrad(((W - 4) * SS, (H - 8) * SS), lighten(c, 0.12), darken(c, 0.12))
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([2 * SS, 1 * SS, (W - 2) * SS, 51 * SS], radius=8 * SS, fill=255)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); layer.paste(body, (2 * SS, 1 * SS))
    img.paste(layer, (0, 0), mask)
    acc = th['accent'] if not off else (150, 150, 150)
    d.rounded_rectangle([7 * SS, 4 * SS, (W - 7) * SS, 6 * SS], radius=SS, fill=acc + (170,))  # top accent line
    # icon box
    rrect(d, (6, 11, 38, 45), 6, lighten(c, 0.28) + (255,), outline=darken(c, 0.3) + (255,), width=1)
    icon = icon.convert('RGBA')
    bb = icon.getbbox()
    if bb:
        w, h = bb[2] - bb[0], bb[3] - bb[1]; side = max(w, h)
        cx, cy = (bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2
        icon = icon.crop((cx - side // 2 - 1, cy - side // 2 - 1, cx - side // 2 - 1 + side + 2, cy - side // 2 - 1 + side + 2))
    ic = icon.resize((28 * SS, 28 * SS), Image.LANCZOS)
    if off:
        g = ic.convert('LA').convert('RGBA')
        g.putalpha(ic.split()[3].point(lambda a: int(a * 0.6)))
        ic = g
    img.alpha_composite(ic, (8 * SS, 14 * SS))
    return img.resize((W, H), Image.LANCZOS)
