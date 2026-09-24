"""v1.0.18 art: themed windows / list buttons for every plain screen, 3-column shop screens, amulet screens.
Everything is drawn at 2 px per UI unit."""
import numpy as np
from PIL import Image, ImageDraw
import shop_art
from shop_art import SS, rrect, vgrad, lighten, darken, mix

# themes for the plain screens (settings item, rule wand, everything else incl. the original addon's menus)
THEMES = {
    'default': dict(base=(34, 24, 46), head=(74, 42, 104), accent=(236, 120, 180), well=(22, 16, 31), btn=(66, 46, 92)),
    'settings': dict(base=(26, 34, 44), head=(38, 72, 104), accent=(96, 192, 236), well=(15, 21, 29), btn=(44, 64, 86)),
    'horror': dict(base=(22, 10, 10), head=(96, 14, 14), accent=(214, 50, 44), well=(11, 5, 5), btn=(64, 22, 22)),
}


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def region_colour(img, box):
    a = np.asarray(img.convert('RGBA').crop(box)).reshape(-1, 4).astype(float)
    a = a[a[:, 3] > 128]
    return tuple(a[:, :3].mean(0)) if len(a) else (0, 0, 0)


def ensure_dark(img, box, text=(255, 255, 255), need=4.5):
    """darken the whole image (hue kept) until text on the region under it reaches the contrast ratio"""
    img = img.convert('RGBA')
    for _ in range(40):
        if contrast(text, region_colour(img, box)) >= need:
            return img
        a = np.asarray(img).astype(float)
        a[..., :3] *= 0.93
        img = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    return img


def _canvas(W, H):
    img = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def window(th, W, H):
    """W x H px (2 px per unit): header bar 8..48 px, content well from 52 px"""
    img, d = _canvas(W, H)
    base, head, acc, well = th['base'], th['head'], th['accent'], th['well']
    rrect(d, (4, 6, W - 2, H - 1), 16, (0, 0, 0, 110))
    rrect(d, (2, 2, W - 5, H - 5), 16, base + (255,), outline=darken(base, 0.5) + (255,), width=2)
    rrect(d, (6, 6, W - 9, H - 9), 13, None, outline=lighten(base, 0.18) + (255,), width=1)
    rrect(d, (8, 8, W - 11, 46), 10, head + (255,))
    d.rectangle([14 * SS, 43 * SS, (W - 17) * SS, 45 * SS], fill=acc + (255,))
    rrect(d, (12, 52, W - 15, H - 14), 10, well + (255,), outline=lighten(well, 0.16) + (255,), width=1)
    return img.resize((W, H), Image.LANCZOS)


def list_button(th, state, W=544, H=62):
    img, d = _canvas(W, H)
    c = th['btn']
    if state == 'hover':
        c = lighten(c, 0.16)
    elif state == 'pressed':
        c = darken(c, 0.25)
    rrect(d, (1, 3, W - 1, H - 1), 9, darken(c, 0.55) + (255,))
    body = vgrad(((W - 2) * SS, (H - 6) * SS), lighten(c, 0.10), darken(c, 0.12))
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([1 * SS, 1 * SS, (W - 1) * SS, (H - 5) * SS], radius=9 * SS, fill=255)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); layer.paste(body, (1 * SS, 1 * SS))
    img.paste(layer, (0, 0), mask)
    acc = th['accent'] if state != 'pressed' else darken(th['accent'], 0.3)
    rrect(d, (6, 10, 11, H - 15), 2, acc + (255,))
    if state == 'hover':
        rrect(d, (1, 1, W - 1, H - 5), 9, None, outline=acc + (255,), width=2)
    out = img.resize((W, H), Image.LANCZOS)
    return ensure_dark(out, (60, 8, W - 20, H - 12))


def close_button(th, state, S=36):
    img, d = _canvas(S, S)
    c = darken(th['head'], 0.2) if state == 'default' else (lighten(th['accent'], 0.1) if state == 'hover' else darken(th['accent'], 0.3))
    rrect(d, (1, 1, S - 1, S - 1), 8, c + (255,), outline=th['accent'] + (255,), width=2)
    m = 11
    for a, b in (((m, m), (S - m, S - m)), ((S - m, m), (m, S - m))):
        d.line([a[0] * SS, a[1] * SS, b[0] * SS, b[1] * SS], fill=(255, 255, 255, 255), width=4 * SS)
    return img.resize((S, S), Image.LANCZOS)


# ---------------------------------------------------------------- shops (360 x 200 units)
SHOP_W, SHOP_H = 720, 400


def shop_background(key, th, icon):
    W, H = SHOP_W, SHOP_H
    img, d = _canvas(W, H)
    base, dark, acc, glass = th['base'], th['dark'], th['accent'], th['glass']
    rrect(d, (6, 8, W - 2, H - 1), 20, (0, 0, 0, 100))
    rrect(d, (2, 2, W - 6, H - 6), 20, base + (255,), outline=darken(base, 0.45) + (255,), width=2)
    rrect(d, (6, 6, W - 10, H - 10), 17, None, outline=lighten(base, 0.25) + (255,), width=1)
    rrect(d, (10, 8, W - 14, 44), 9, dark + (255,))
    deco = Image.new('RGBA', (560 * SS, H * SS), (0, 0, 0, 0)); dd = ImageDraw.Draw(deco)
    shop_art.deco_header(key, dd, th, 560)
    shop_art.deco_extra(key, dd, th)
    deco = deco.crop((0, 0, 560 * SS, 46 * SS))
    img.alpha_composite(deco, ((W - 14 - 430) * SS, 0))
    board = darken(dark, 0.25)
    rrect(d, (10, 48, 566, 116), 9, darken(dark, 0.1) + (255,), outline=lighten(dark, 0.2) + (255,), width=2)      # action row
    rrect(d, (10, 118, 566, H - 12), 9, board + (255,), outline=lighten(dark, 0.2) + (255,), width=2)          # products
    rrect(d, (572, 48, W - 14, H - 12), 9, darken(base, 0.18) + (255,), outline=darken(base, 0.45) + (255,), width=2)
    rrect(d, (578, 54, W - 20, 206), 7, glass + (255,), outline=lighten(glass, 0.3) + (255,), width=2)
    rrect(d, (582, 58, W - 24, 202), 5, darken(glass, 0.2) + (255,))
    rrect(d, (596, 216, W - 38, 230), 4, (30, 30, 34, 255))
    d.rectangle([612 * SS, 221 * SS, (W - 54) * SS, 224 * SS], fill=(0, 0, 0, 255))
    rrect(d, (590, 238, W - 32, 252), 4, (30, 30, 34, 255))
    d.rectangle([596 * SS, 243 * SS, (W - 38) * SS, 246 * SS], fill=(0, 0, 0, 255))
    rrect(d, (590, 270, W - 32, H - 22), 8, lighten(base, 0.12) + (255,), outline=darken(base, 0.4) + (255,), width=2)
    ic = icon.convert('RGBA').resize((92 * SS, 92 * SS), Image.LANCZOS)
    img.alpha_composite(ic, ((592 + ((W - 32 - 590) - 92) // 2) * SS, 276 * SS))
    return img.resize((W, H), Image.LANCZOS)


def _dark_enough(c, maxL=0.12):
    for _ in range(40):
        if lum(c) <= maxL:
            break
        c = darken(c, 0.08)
    return c


def card(th, icon, off=False, W=172, H=64, icon_px=40):
    """menu card: icon box on the left, name + price label from x = 27 units"""
    img, d = _canvas(W, H)
    c = (46, 46, 50) if off else _dark_enough(th['cell'])
    rrect(d, (1, 3, W - 1, H - 1), 9, darken(c, 0.5) + (255,))
    body = vgrad(((W - 4) * SS, (H - 7) * SS), lighten(c, 0.10), darken(c, 0.10))
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([2 * SS, 1 * SS, (W - 2) * SS, (H - 5) * SS], radius=9 * SS, fill=255)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); layer.paste(body, (2 * SS, 1 * SS))
    img.paste(layer, (0, 0), mask)
    acc = (120, 120, 124) if off else th['accent']
    d.rounded_rectangle([8 * SS, 4 * SS, (W - 8) * SS, 6 * SS], radius=SS, fill=acc + (190,))
    top = (H - 4 - icon_px - 6) // 2 + 2
    rrect(d, (5, top, 5 + icon_px + 6, top + icon_px + 6), 6, lighten(c, 0.22) + (255,), outline=darken(c, 0.35) + (255,), width=1)
    icon = icon.convert('RGBA')
    bb = icon.getbbox()
    if bb:
        side = max(bb[2] - bb[0], bb[3] - bb[1])
        cx, cy = (bb[0] + bb[2]) // 2, (bb[1] + bb[3]) // 2
        icon = icon.crop((cx - side // 2 - 1, cy - side // 2 - 1, cx - side // 2 - 1 + side + 2, cy - side // 2 - 1 + side + 2))
    ic = icon.resize((icon_px * SS, icon_px * SS), Image.LANCZOS)
    if off:
        g = ic.convert('LA').convert('RGBA')
        g.putalpha(ic.split()[3].point(lambda a: int(a * 0.7)))
        ic = g
    img.alpha_composite(ic, ((8) * SS, (top + 3) * SS))
    return img.resize((W, H), Image.LANCZOS)


def pad_to(img, H):
    """centre a button vertically on a taller transparent canvas (no stretching)"""
    out = Image.new('RGBA', (img.width, H), (0, 0, 0, 0))
    out.alpha_composite(img.convert('RGBA'), (0, (H - img.height) // 2))
    return out


# ---------------------------------------------------------------- amulet screens (320 x 200 units)
AM_W, AM_H = 640, 400


def amulet_background(th, icon):
    W, H = AM_W, AM_H
    img, d = _canvas(W, H)
    base, dark, acc, glass = th['base'], th['dark'], th['accent'], th['glass']
    rrect(d, (6, 8, W - 2, H - 1), 20, (0, 0, 0, 100))
    rrect(d, (2, 2, W - 6, H - 6), 20, base + (255,), outline=darken(base, 0.45) + (255,), width=2)
    rrect(d, (6, 6, W - 10, H - 10), 17, None, outline=lighten(base, 0.25) + (255,), width=1)
    rrect(d, (10, 8, W - 14, 44), 9, dark + (255,))
    for cx in (W - 96, W - 70, W - 44):
        d.ellipse([(cx - 9) * SS, 17 * SS, (cx + 9) * SS, 35 * SS], fill=(232, 186, 60, 255), outline=(150, 110, 30, 255), width=SS)
        d.ellipse([(cx - 4) * SS, 22 * SS, (cx + 4) * SS, 30 * SS], fill=(120, 30, 30, 255))
    rrect(d, (10, 48, 468, H - 12), 9, darken(dark, 0.25) + (255,), outline=lighten(dark, 0.2) + (255,), width=2)
    rrect(d, (474, 48, W - 14, H - 12), 9, darken(base, 0.18) + (255,), outline=darken(base, 0.45) + (255,), width=2)
    rrect(d, (480, 54, W - 20, 230), 7, glass + (255,), outline=lighten(glass, 0.3) + (255,), width=2)
    rrect(d, (484, 58, W - 24, 226), 5, darken(glass, 0.2) + (255,))
    rrect(d, (496, 250, W - 36, H - 24), 8, lighten(base, 0.12) + (255,), outline=darken(base, 0.4) + (255,), width=2)
    ic = icon.convert('RGBA').resize((96 * SS, 96 * SS), Image.LANCZOS)
    img.alpha_composite(ic, ((496 + ((W - 36 - 496) - 96) // 2) * SS, 270 * SS))
    return img.resize((W, H), Image.LANCZOS)
