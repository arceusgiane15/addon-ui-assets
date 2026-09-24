"""Build Bedrock cube models + painted texture atlases from code.
A part is dict(o=[x,y,z], s=[w,h,d], paint=<painter or {face: painter}>, rot=[rx,ry,rz], pivot=[...]).
Coordinates: y up, front = -z (north). Painters draw a face as seen from outside."""
import os
from PIL import Image, ImageDraw, ImageFont

FONT = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'NotoSansThai.ttf')
FACES = ('north', 'south', 'east', 'west', 'up', 'down')


def _font(px):
    f = ImageFont.truetype(FONT, max(6, int(px)))
    try:
        f.set_variation_by_name('Bold')
    except Exception:
        pass
    return f


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + ((c[3],) if len(c) > 3 else ())


# ---------------------------------------------------------------- painters: f(w, h, face) -> Image
def solid(c):
    return lambda w, h, face: Image.new('RGBA', (w, h), tuple(c) + ((255,) if len(c) == 3 else ()))


def vgrad(top, bottom):
    def p(w, h, face):
        im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
        for y in range(h):
            t = y / max(1, h - 1)
            d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
        return im
    return p


def label(bg, lines=(), fg=(255, 255, 255), bands=(), icon=None, border=None, size=0.22, top=0.5):
    """bands: [(y0, y1, color)] as fractions of height; lines: [text] or [(text, color, scale)]"""
    def p(w, h, face):
        im = Image.new('RGBA', (w, h), tuple(bg) + (255,)); d = ImageDraw.Draw(im)
        for y0, y1, c in bands:
            d.rectangle([0, int(y0 * h), w, int(y1 * h) - 1], fill=tuple(c) + (255,))
        if icon:
            icon(d, w, h)
        if border:
            d.rectangle([0, 0, w - 1, h - 1], outline=tuple(border) + (255,), width=max(1, w // 32))
        n = len(lines)
        for i, ln in enumerate(lines):
            text, col, sc = (ln, fg, 1.0) if isinstance(ln, str) else ln
            f = _font(h * size * sc)
            while f.size > 6 and d.textlength(text, font=f) > w * 0.92:
                f = _font(f.size - 1)
            tw = d.textlength(text, font=f)
            y = h * top - (n * f.size * 1.15) / 2 + i * f.size * 1.15
            d.text(((w - tw) / 2, y - f.size * 0.15), text, font=f, fill=tuple(col) + (255,))
        return im
    return p


def cross(color, cx=0.5, cy=0.5, r=0.3):
    def icon(d, w, h):
        a = int(min(w, h) * r); t = max(1, a // 3); x = int(w * cx); y = int(h * cy)
        d.rectangle([x - a, y - t, x + a, y + t], fill=tuple(color) + (255,))
        d.rectangle([x - t, y - a, x + t, y + a], fill=tuple(color) + (255,))
    return icon


def dots(colors, n=6, cy=0.75, r=0.06):
    def icon(d, w, h):
        rr = int(min(w, h) * r)
        for i in range(n):
            x = int(w * (i + 0.5) / n); y = int(h * cy)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=tuple(colors[i % len(colors)]) + (255,))
    return icon


def stripes(colors, vertical=False, count=6):
    def p(w, h, face):
        im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
        for i in range(count):
            c = tuple(colors[i % len(colors)]) + (255,)
            if vertical:
                d.rectangle([int(w * i / count), 0, int(w * (i + 1) / count), h], fill=c)
            else:
                d.rectangle([0, int(h * i / count), w, int(h * (i + 1) / count)], fill=c)
        return im
    return p


def grid_goods(colors, rows=1, cols=4, bg=(40, 40, 40), gap=0.12):
    """front of a shelf row: little product fronts"""
    def p(w, h, face):
        im = Image.new('RGBA', (w, h), tuple(bg) + (255,)); d = ImageDraw.Draw(im)
        cw, ch = w / cols, h / rows
        k = 0
        for r in range(rows):
            for c in range(cols):
                col = colors[k % len(colors)]; k += 1
                x0 = c * cw + cw * gap / 2; x1 = (c + 1) * cw - cw * gap / 2
                y0 = r * ch + ch * gap; y1 = (r + 1) * ch
                d.rectangle([x0, y0, x1, y1], fill=tuple(col) + (255,))
                d.rectangle([x0, y0 + (y1 - y0) * 0.35, x1, y0 + (y1 - y0) * 0.55], fill=shade(col, 1.35) + (255,))
        return im
    return p


def per_face(default, **faces):
    return {f: faces.get(f, default) for f in FACES}


# ---------------------------------------------------------------- build
def _face_px(part, face, ppu):
    w, h, d = part['s']
    dims = {'north': (w, h), 'south': (w, h), 'east': (d, h), 'west': (d, h), 'up': (w, d), 'down': (w, d)}[face]
    return max(1, round(dims[0] * ppu)), max(1, round(dims[1] * ppu))


def build(parts, ppu=8, max_w=1024):
    """returns (cubes, atlas image). cube uv in atlas pixels."""
    tiles = []
    for pi, p in enumerate(parts):
        paint = p['paint'] if isinstance(p['paint'], dict) else {f: p['paint'] for f in FACES}
        for face in FACES:
            if paint.get(face) is None:
                continue
            w, h = _face_px(p, face, p.get('ppu', ppu))
            tiles.append((pi, face, w, h, paint[face]))
    # shelf packing (tallest first)
    order = sorted(range(len(tiles)), key=lambda i: -tiles[i][3])
    x = y = row_h = 0; W = 0; pos = {}
    for i in order:
        _, _, w, h, _ = tiles[i]
        if x + w > max_w:
            x = 0; y += row_h; row_h = 0
        pos[i] = (x, y); x += w; row_h = max(row_h, h); W = max(W, x)
    H = y + row_h
    tw = 1
    while tw < W: tw *= 2
    th = 1
    while th < H: th *= 2
    atlas = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    uv = {}
    for i, (pi, face, w, h, painter) in enumerate(tiles):
        img = painter(w, h, face)
        if face in ('east', 'west', 'up', 'down') and isinstance(painter, type(lambda: 0)) is False:
            pass
        atlas.paste(img, pos[i])
        uv[(pi, face)] = (pos[i], (w, h))
    cubes = []
    for pi, p in enumerate(parts):
        faces = {}
        for face in FACES:
            if (pi, face) in uv:
                (u, v), (w, h) = uv[(pi, face)]
                if face in ('up', 'down'):   # bedrock flips up/down faces
                    faces[face] = {"uv": [u + w, v + h], "uv_size": [-w, -h]}
                else:
                    faces[face] = {"uv": [u, v], "uv_size": [w, h]}
        c = {"origin": [round(v, 4) for v in p['o']], "size": [round(v, 4) for v in p['s']], "uv": faces}
        if p.get('rot'):
            c["rotation"] = p['rot']; c["pivot"] = p.get('pivot', [p['o'][i] + p['s'][i] / 2 for i in range(3)])
        if p.get('inflate'):
            c["inflate"] = p['inflate']
        cubes.append(c)
    return cubes, atlas, (tw, th)


def transform(parts, scale, offset):
    out = []
    for p in parts:
        q = dict(p)
        q['o'] = [p['o'][i] * scale + offset[i] for i in range(3)]
        q['s'] = [v * scale for v in p['s']]
        if p.get('pivot'):
            q['pivot'] = [p['pivot'][i] * scale + offset[i] for i in range(3)]
        q['ppu'] = p.get('ppu', 16) / scale if 'ppu' in p else None
        if q['ppu'] is None:
            q.pop('ppu')
        out.append(q)
    return out


# ---------------------------------------------------------------- textured preview / icons
def _rot(yaw, pitch):
    import numpy as np
    a, b = np.radians(yaw), np.radians(pitch)
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    return Rx @ Ry


def render(parts, size=256, yaw=-28, pitch=-24, ppu=12, pad=0.08, bg=(0, 0, 0, 0)):
    """orthographic textured render, viewer looks toward +z (sees the north/front faces)"""
    import numpy as np
    M = _rot(yaw, pitch)
    quads = []
    for p in parts:
        paint = p['paint'] if isinstance(p['paint'], dict) else {f: p['paint'] for f in FACES}
        (x0, y0, z0), (w, h, d) = p['o'], p['s']
        x1, y1, z1 = x0 + w, y0 + h, z0 + d
        # face: (TL, TR, BL) corners as seen from outside, normal
        F = {'north': ((x0, y1, z0), (x1, y1, z0), (x0, y0, z0), (0, 0, -1)),
             'south': ((x1, y1, z1), (x0, y1, z1), (x1, y0, z1), (0, 0, 1)),
             'west': ((x1, y1, z0), (x1, y1, z1), (x1, y0, z0), (1, 0, 0)),
             'east': ((x0, y1, z1), (x0, y1, z0), (x0, y0, z1), (-1, 0, 0)),
             'up': ((x0, y1, z1), (x1, y1, z1), (x0, y1, z0), (0, 1, 0)),
             'down': ((x0, y0, z0), (x1, y0, z0), (x0, y0, z1), (0, -1, 0))}
        for face, (tl, tr, bl, n) in F.items():
            if paint.get(face) is None:
                continue
            n2 = M @ np.array(n, float)
            if n2[2] >= -1e-6:
                continue
            pts = [M @ np.array(c, float) for c in (tl, tr, bl)]
            quads.append((face, p, paint[face], pts, n2))
    allp = np.array([q for f in quads for q in f[3]] + [f[3][1] + f[3][2] - f[3][0] for f in quads])
    mn, mx = allp.min(0), allp.max(0)
    span = max(mx[0] - mn[0], mx[1] - mn[1]) * (1 + 2 * pad)
    sc = size / span; cx, cy = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2
    S = lambda v: np.array([size / 2 + (v[0] - cx) * sc, size / 2 - (v[1] - cy) * sc])
    out = Image.new('RGBA', (size, size), bg)
    def depth(q):
        tl, tr, bl = q[3]
        return (tl + tr + bl + (tr + bl - tl))[2] / 4
    for face, p, painter, (tl, tr, bl), n2 in sorted(quads, key=lambda q: -depth(q)):
        w, h = _face_px(p, face, ppu)
        img = painter(w, h, face).convert('RGBA')
        light = 0.62 + 0.38 * max(0.0, float(n2 @ np.array([0.35, 0.75, -0.55]) / 1.0))
        r, g, b, a = img.split()
        img = Image.merge('RGBA', [c.point(lambda v: int(min(255, v * light))) for c in (r, g, b)] + [a])
        s0, s1, s3 = S(tl), S(tr), S(bl)
        # affine: screen -> image
        A = np.array([[(s1 - s0)[0] / w, (s3 - s0)[0] / h], [(s1 - s0)[1] / w, (s3 - s0)[1] / h]])
        if abs(np.linalg.det(A)) < 1e-9:
            continue
        Ai = np.linalg.inv(A)
        coeffs = (Ai[0, 0], Ai[0, 1], -(Ai[0] @ s0), Ai[1, 0], Ai[1, 1], -(Ai[1] @ s0))
        warped = img.transform((size, size), Image.AFFINE, coeffs, resample=Image.BILINEAR)
        out.alpha_composite(warped)
    return out
