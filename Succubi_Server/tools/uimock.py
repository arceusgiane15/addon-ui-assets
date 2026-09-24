"""Rough preview of the v1.0.18 screens (2 px per UI unit, Noto Thai stands in for the game font)."""
import re, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, 'tools')
RP = 'out/Succubi Server RP/'
F = {False: ImageFont.truetype('fonts/NotoSansThai.ttf', 15), True: ImageFont.truetype('fonts/NotoSansThai.ttf', 16)}
COL = dict(zip('0123456789abcdefg', ['#000000', '#0000AA', '#00AA00', '#00AAAA', '#AA0000', '#AA00AA', '#FFAA00', '#AAAAAA', '#555555', '#5555FF',
                                      '#55FF55', '#55FFFF', '#FF5555', '#FF55FF', '#FFFF55', '#FFFFFF', '#DDD605']))


def text(img, xy, s, base='#FFFFFF', width=None, shadow=True):
    d = ImageDraw.Draw(img)
    x0, y = xy
    for line in s.split('\n'):
        x, col, bold = x0, base, False
        for tok in re.split(r'(§.)', line):
            if tok.startswith('§'):
                c = tok[1]
                if c in COL: col, bold = COL[c], False
                elif c == 'l': bold = True
                elif c == 'r': col, bold = base, False
                continue
            if not tok: continue
            f = F[bold]
            if shadow: d.text((x + 2, y + 2), tok, font=f, fill='#3a3a3a')
            d.text((x, y), tok, font=f, fill=col)
            x += d.textlength(tok, font=f)
        if width and x - x0 > width: d.rectangle([x0 + width, y, x0 + width + 3, y + 16], fill='#ff00ff')  # overflow marker
        y += 20
    return y


def img(p):
    return Image.open(RP + p + '.png').convert('RGBA')


def paste(canvas, p, xy, size=None):
    im = img(p) if isinstance(p, str) else p
    if size: im = im.resize(size, Image.LANCZOS)
    canvas.alpha_composite(im, xy)


def button_label(canvas, x, y, w, h, s, off_x, base='#FFFFFF'):
    lines = s.split('\n')
    top = y + h // 2 - len(lines) * 10
    text(canvas, (x + off_x, top), s, base=base, width=w - off_x - 4)
