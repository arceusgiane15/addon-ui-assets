"""Remade models (the old ones were stacks of plain boxes):
  bao (steamed bun), boiled eggs, onigiri salmon / tuna, ham sandwich, shrimp shumai in a bamboo steamer,
  the watcher statue (now a weeping stone angel) and the shadow figure.
Same geometry identifiers, bones and texture paths as before, so attachables / entities / held poses keep working.
Item icons and shop cards are rendered from the new models."""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from registry import step
from common import rjson, wjson, CORE_RP
from meshkit import Mesh, rot, rounded_polygon
import render_geo
from art_icons import swap_everywhere

TEX = 256
RNG = random.Random(7)


def noise_fill(im, box, base, var=12, seed=1, speck=None, speck_n=0):
    rng = random.Random(seed)
    x0, y0, x1, y1 = [int(v) for v in box]
    p = im.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = rng.randint(-var, var)
            p[x, y] = tuple(max(0, min(255, c + k)) for c in base[:3]) + (255,)
    d = ImageDraw.Draw(im)
    if speck:
        for _ in range(speck_n):
            x, y = rng.randint(x0, x1 - 2), rng.randint(y0, y1 - 2)
            c = speck[rng.randrange(len(speck))]
            d.ellipse([x, y, x + rng.randint(1, 3), y + rng.randint(1, 2)], fill=c + (255,))


def vshade(im, box, top=1.08, bottom=0.8):
    x0, y0, x1, y1 = [int(v) for v in box]
    p = im.load()
    for y in range(y0, y1):
        k = top + (bottom - top) * (y - y0) / max(1, y1 - y0 - 1)
        for x in range(x0, x1):
            r, g, b, a = p[x, y]
            p[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), a)


def food_geo(ident, mesh, tw=TEX, th=TEX):
    return {"description": {"identifier": ident, "texture_width": tw, "texture_height": th,
                            "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
            "bones": [{"name": "succubi_food", "pivot": [0.0, 22.5, -0.5]},
                      {"name": "succubi_food_model", "parent": "succubi_food", "pivot": [0.0, 22.5, -0.5], "poly_mesh": mesh.json()}]}


# ------------------------------------------------------------------------------------------ foods (y 20.5 .. ~26)
def bao():
    m, tex = Mesh(TEX, TEX), Image.new('RGBA', (TEX, TEX))
    # paper square
    noise_fill(tex, (0, 0, 64, 64), (238, 226, 196), 6, 2)
    m.obox((0, 20.6, -0.5), (6.0, 0.2, 6.0), rects={'up': (0, 0, 64, 64), 'down': (0, 0, 64, 64), 'north': (0, 0, 64, 4),
                                                   'south': (0, 0, 64, 4), 'east': (0, 0, 64, 4), 'west': (0, 0, 64, 4)})
    # bun: soft dome, pleats towards a pinched top with a red dot
    side = (0, 64, 256, 192)
    noise_fill(tex, side, (250, 246, 236), 5, 3)
    vshade(tex, side, 1.02, 0.86)
    d = ImageDraw.Draw(tex)
    for i in range(16):
        x = i * 16 + 8
        d.line([(x, 64), (x - 5, 120)], fill=(222, 214, 198, 255), width=2)
    d.rectangle([0, 64, 256, 70], fill=(214, 60, 70, 255))            # red dot band at the very top
    prof = [(2.55, 20.72), (2.95, 21.2), (3.05, 21.9), (2.9, 22.7), (2.5, 23.5), (1.85, 24.2), (1.05, 24.65), (0.35, 24.85), (0.0, 24.9)]
    m.lathe(prof, (0, 0, -0.5), side, segs=18, cap_bottom=(0, 0, 64, 64))
    return m, tex


def boiled_eggs():
    m, tex = Mesh(TEX, TEX), Image.new('RGBA', (TEX, TEX))
    # clear-ish tray
    noise_fill(tex, (0, 0, 128, 40), (214, 228, 236), 4, 4)
    d = ImageDraw.Draw(tex)
    d.ellipse([10, 6, 58, 34], fill=(178, 196, 208, 255))
    d.ellipse([70, 6, 118, 34], fill=(178, 196, 208, 255))
    noise_fill(tex, (0, 40, 128, 52), (190, 206, 216), 4, 5)
    m.obox((0, 20.85, -0.5), (6.2, 0.7, 3.4), rects={'up': (0, 0, 128, 40), 'down': (0, 0, 128, 40), 'north': (0, 40, 128, 52),
                                                    'south': (0, 40, 128, 52), 'east': (0, 40, 40, 52), 'west': (0, 40, 40, 52)})
    # whole egg
    shell = (0, 64, 128, 160)
    noise_fill(tex, shell, (250, 246, 240), 4, 6)
    vshade(tex, shell, 1.03, 0.84)
    egg = [(0.0, 21.0), (0.9, 21.15), (1.3, 21.8), (1.35, 22.6), (1.2, 23.4), (0.8, 24.1), (0.3, 24.45), (0.0, 24.5)]
    m.lathe(egg, (-1.4, 0, -0.5), shell, segs=14)
    # half egg, cut face up: white ring + soft yolk
    white = (128, 64, 256, 160)
    noise_fill(tex, white, (252, 250, 244), 3, 7)
    vshade(tex, white, 1.0, 0.86)
    cap = (128, 160, 224, 256)
    d.ellipse([128, 160, 224, 256], fill=(252, 250, 244, 255))
    d.ellipse([146, 178, 206, 238], fill=(244, 170, 40, 255))
    d.ellipse([156, 186, 190, 220], fill=(252, 196, 70, 255))
    half = [(0.0, 21.0), (0.9, 21.12), (1.3, 21.6), (1.4, 22.2)]
    m.lathe(half, (1.4, 0, -0.5), white, segs=14, cap_top=cap, sx=1.0, sz=1.25)
    return m, tex


def onigiri(filling):
    m, tex = Mesh(TEX, TEX), Image.new('RGBA', (TEX, TEX))
    rice = [(250, 250, 246), (236, 236, 228), (255, 255, 255)]
    # caps (front / back)
    for box, seed in (((0, 0, 128, 128), 11), ((128, 0, 256, 128), 12)):
        noise_fill(tex, box, (246, 246, 240), 6, seed, speck=rice, speck_n=260)
        d = ImageDraw.Draw(tex)
        x0 = box[0]
        d.rectangle([x0 + 34, 72, x0 + 94, 128], fill=(30, 44, 30, 255))           # nori
        for i in range(8):
            d.line([(x0 + 34, 76 + i * 7), (x0 + 94, 76 + i * 7)], fill=(44, 62, 42, 255))
        if True:                                                                # filling shows on both faces
            col = (244, 120, 80) if filling == 'salmon' else (226, 206, 160)
            d.ellipse([x0 + 50, 30, x0 + 78, 50], fill=col + (255,))
            d.ellipse([x0 + 56, 34, x0 + 66, 40], fill=tuple(min(255, c + 30) for c in col) + (255,))
    # sides
    noise_fill(tex, (0, 128, 256, 192), (240, 240, 234), 6, 13, speck=rice, speck_n=300)
    d = ImageDraw.Draw(tex)
    d.rectangle([0, 128, 70, 192], fill=(30, 44, 30, 255))     # nori under the base
    outline = rounded_polygon([(-3.0, 20.6), (3.0, 20.6), (0.0, 26.0)], 1.0, 5)
    m.extrude(outline, -1.7, 0.7, (0, 128, 256, 192), (0, 0, 128, 128), (128, 0, 256, 128))
    return m, tex


def sandwich_ham():
    m, tex = Mesh(TEX, TEX), Image.new('RGBA', (TEX, TEX))
    # cut face: white bread with lettuce / ham / cheese through the middle (the triangle shape comes from the mesh)
    noise_fill(tex, (0, 0, 256, 128), (250, 240, 214), 5, 20, speck=[(236, 222, 190)], speck_n=200)
    d = ImageDraw.Draw(tex)
    for (y, h, c) in ((58, 9, (110, 186, 64)), (67, 12, (236, 136, 146)), (79, 8, (250, 204, 74))):
        d.rectangle([0, y, 256, y + h], fill=c + (255,))
        for x in range(0, 256, 9):
            d.line([(x, y), (x + 4, y + h)], fill=tuple(int(v * 0.9) for v in c) + (255,))
    noise_fill(tex, (0, 128, 256, 192), (204, 144, 70), 10, 21)          # crust
    # two halves leaning on each other, both outlines counter-clockwise
    halves = (([(-3.2, 20.6), (1.4, 20.6), (-3.2, 25.8)], -1.9, -0.3),
              ([(3.2, 20.6), (3.2, 25.8), (-1.4, 20.6)], -0.5, 1.1))
    for outline, z0, z1 in halves:
        m.extrude(outline, z0, z1, (0, 128, 256, 192), (0, 0, 128, 128), (128, 0, 256, 128))
    return m, tex


def dim_sum():
    m, tex = Mesh(TEX, TEX), Image.new('RGBA', (TEX, TEX))
    # bamboo steamer: slats + rim
    side = (0, 0, 256, 48)
    noise_fill(tex, side, (206, 166, 96), 8, 31)
    d = ImageDraw.Draw(tex)
    for x in range(0, 256, 8):
        d.line([(x, 0), (x, 48)], fill=(170, 128, 66, 255))
    d.rectangle([0, 0, 256, 6], fill=(150, 108, 52, 255))
    floor = (0, 48, 96, 144)
    noise_fill(tex, floor, (196, 160, 92), 8, 32)
    for y in range(52, 144, 10):
        d.line([(0, y), (96, y)], fill=(160, 122, 60, 255), width=2)
    prof = [(3.2, 20.6), (3.25, 21.8), (3.0, 21.8), (3.0, 21.0)]
    m.lathe(prof, (0, 0, -0.5), side, segs=20, cap_bottom=floor)
    m.disc((0, 21.0, -0.5), 3.0, floor, True, 20)
    # shumai: yellow wrapper cup, pork top with an orange dot
    wrap = (0, 160, 128, 208)
    noise_fill(tex, wrap, (248, 214, 90), 10, 33)
    for x in range(0, 128, 11):
        d.line([(x, 160), (x + 4, 208)], fill=(226, 180, 60, 255), width=2)
    top = (128, 160, 224, 256)
    noise_fill(tex, top, (226, 170, 150), 14, 34, speck=[(200, 140, 120), (240, 200, 180)], speck_n=80)
    d.ellipse([160, 190, 192, 222], fill=(250, 110, 40, 255))
    for (x, z) in ((-1.25, -1.75), (1.25, -1.75), (-1.25, 0.75), (1.25, 0.75)):
        cup = [(0.75, 21.0), (1.0, 21.6), (1.05, 22.4), (0.95, 22.7)]
        m.lathe(cup, (x, 0, z), wrap, segs=10, cap_top=top)
    return m, tex


FOODS = {
    'bao': bao, 'boiled_eggs': boiled_eggs, 'onigiri_salmon': lambda: onigiri('salmon'), 'onigiri_tuna': lambda: onigiri('tuna'),
    'sandwich_ham': sandwich_ham, 'dim_sum': dim_sum,
}


# ------------------------------------------------------------------------------------------ weeping stone angel
def stone(im, box, seed, base=(146, 146, 140), cracks=4, moss=40):
    noise_fill(im, box, base, 10, seed, speck=[(118, 118, 112), (170, 170, 162)], speck_n=(box[2] - box[0]) * (box[3] - box[1]) // 40)
    rng = random.Random(seed)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    for _ in range(cracks):
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        for _ in range(6):
            nx, ny = x + rng.randint(-8, 8), y + rng.randint(2, 10)
            d.line([(x, y), (nx, ny)], fill=(70, 70, 66, 255))
            x, y = nx, ny
    for _ in range(moss):
        x, y = rng.randint(x0, x1 - 4), rng.randint(int(y0 + (y1 - y0) * 0.6), y1 - 3)
        d.ellipse([x, y, x + rng.randint(2, 6), y + rng.randint(1, 4)], fill=(78, 108, 56, 255))


def watcher_statue():
    T = 512
    m, tex = Mesh(T, T), Image.new('RGBA', (T, T))
    stone(tex, (0, 0, 512, 64), 41, (120, 120, 116), cracks=3, moss=60)       # pedestal sides
    stone(tex, (0, 64, 128, 192), 42, (132, 132, 126), cracks=2, moss=10)     # pedestal top
    stone(tex, (128, 64, 512, 256), 43, (156, 156, 150), cracks=6, moss=50)   # robe
    d = ImageDraw.Draw(tex)
    for x in range(128, 512, 24):                                             # robe folds
        d.line([(x, 64), (x + 6, 256)], fill=(120, 120, 114, 255), width=3)
    stone(tex, (0, 256, 256, 384), 44, (160, 160, 154), cracks=3, moss=4)     # head / hands / arms
    stone(tex, (256, 256, 512, 512), 45, (150, 150, 146), cracks=5, moss=10)  # wings
    for i in range(10):                                                       # feathers
        y = 262 + i * 24
        d.arc([270, y, 500, y + 60], 190, 350, fill=(118, 118, 112, 255), width=3)
    d.rectangle([0, 384, 256, 512], fill=(10, 8, 10, 255))                    # shadowed face under the hands
    # pedestal
    m.obox((0, 1.5, 0), (12, 3, 12), rects={f: (0, 0, 512, 64) for f in ('north', 'south', 'east', 'west')} | {'up': (0, 64, 128, 192), 'down': (0, 64, 128, 192)})
    m.obox((0, 3.5, 0), (10, 1, 10), rects={f: (0, 0, 512, 16) for f in ('north', 'south', 'east', 'west')} | {'up': (0, 64, 128, 192), 'down': (0, 64, 128, 192)})
    # robe: flares at the hem, narrow waist, shoulders
    robe = [(4.6, 4.0), (4.4, 7.0), (3.7, 12.0), (3.2, 17.0), (3.4, 21.0), (4.0, 24.0), (3.6, 25.2), (1.6, 26.0)]
    m.lathe(robe, (0, 0, 0), (128, 64, 512, 256), segs=18, sz=0.85, cap_bottom=(0, 64, 128, 192))
    # bowed head
    head = [(0.0, 25.4), (1.6, 25.8), (2.2, 27.0), (2.2, 28.4), (1.8, 29.6), (1.0, 30.3), (0.0, 30.5)]
    m.lathe(head, (0, 0, -0.9), (0, 256, 256, 320), segs=12)
    # arms raised, hands over the face
    for sgn in (-1, 1):
        R = rot(-62, 0, sgn * 18)
        m.obox((sgn * 3.0, 22.6, -1.4), (1.7, 6.0, 1.7), R, default_rect=(0, 320, 128, 384))
        m.obox((sgn * 1.0, 27.8, -2.9), (1.9, 2.8, 1.0), rot(8, 0, -sgn * 12), default_rect=(128, 320, 256, 384))
    # wings folded behind, tips above the head
    wing = [(0.0, 0.0), (2.6, 2.5), (4.6, 7.0), (5.4, 12.5), (4.8, 17.5), (3.2, 20.0), (2.0, 16.0), (0.8, 11.0), (-0.4, 5.0)]
    for sgn in (-1, 1):
        R = rot(0, sgn * 34, 0)
        pts = [(sgn * (1.3 + x), 12.0 + y) for x, y in wing]
        if sgn < 0:
            pts = pts[::-1]
        before = len(m.polys)
        m.extrude(pts, 2.4, 3.2, (256, 256, 512, 288), (256, 288, 512, 512), (256, 288, 512, 512))
        # rotate the wing just added around its root
        root = np.array([sgn * 1.3, 12.0, 2.8])
        idx = sorted({v[0] for poly in m.polys[before:] for v in poly})
        for i in idx:
            p = np.array(m.P[i]) - root
            m.P[i] = [round(float(c), 5) for c in (R @ p + root)]
        nidx = sorted({v[1] for poly in m.polys[before:] for v in poly})
        for i in nidx:
            m.N[i] = [round(float(c), 5) for c in (R @ np.array(m.N[i]))]
    geo = {"description": {"identifier": "geometry.watcher_statue", "texture_width": T, "texture_height": T,
                           "visible_bounds_width": 3, "visible_bounds_height": 4, "visible_bounds_offset": [0, 1.5, 0]},
           "bones": [{"name": "root", "pivot": [0, 0, 0], "poly_mesh": m.json()}]}
    return geo, tex


def shadow_figure():
    T = 256
    m, tex = Mesh(T, T), Image.new('RGBA', (T, T))
    d = ImageDraw.Draw(tex)
    for y in range(T):
        c = int(8 + 14 * (1 - y / T))
        d.line([(0, y), (T, y)], fill=(c, 4, c + 8, 255))
    # eyes
    d.rectangle([0, 200, 64, 256], fill=(12, 4, 16, 255))
    d.ellipse([10, 214, 24, 222], fill=(255, 60, 70, 255))
    d.ellipse([40, 214, 54, 222], fill=(255, 60, 70, 255))
    d.ellipse([13, 216, 19, 219], fill=(255, 220, 220, 255))
    d.ellipse([43, 216, 49, 219], fill=(255, 220, 220, 255))
    # tattered cloak edge: alpha-cut teeth
    rng = random.Random(5)
    cloak = (64, 128, 256, 256)
    for x in range(64, 256, 6):
        h = rng.randint(6, 26)
        d.rectangle([x, 256 - h, x + 3, 256], fill=(0, 0, 0, 0))
    body = (0, 0, 64, 128)
    # legs
    for sgn in (-1, 1):
        m.obox((sgn * 1.3, 8.0, 0), (1.6, 16.0, 1.6), rot(0, 0, sgn * 2), default_rect=body)
    # cloak / torso (lathe, ragged hem via texture alpha)
    torso = [(3.8, 6.0), (3.4, 12.0), (2.8, 20.0), (3.2, 27.0), (3.6, 30.0), (1.2, 31.2)]
    m.lathe(torso, (0, 0, 0), cloak, segs=12, sz=0.6)
    # long arms hanging to the knees
    for sgn in (-1, 1):
        m.obox((sgn * 4.0, 19.5, 0.2), (1.2, 18.0, 1.2), rot(0, 0, sgn * 6), default_rect=body)
        m.obox((sgn * 4.9, 9.8, 0.2), (1.0, 2.6, 1.4), rot(0, 0, sgn * 10), default_rect=body)   # long fingers
    # head, slightly tilted
    m.obox((0, 34.0, -0.3), (4.2, 5.6, 4.2), rot(0, 0, 8), rects={'north': (0, 200, 64, 256)}, default_rect=body)
    geo = {"description": {"identifier": "geometry.succubi_shadow_figure", "texture_width": T, "texture_height": T,
                           "visible_bounds_width": 2, "visible_bounds_height": 3.5, "visible_bounds_offset": [0, 1.5, 0]},
           "bones": [{"name": "root", "pivot": [0, 0, 0], "poly_mesh": m.json()}]}
    return geo, tex


# ------------------------------------------------------------------------------------------ install
def replace_geo(path, geo):
    d = rjson(path)
    gs = d['minecraft:geometry']
    for i, g in enumerate(gs):
        if g['description']['identifier'] == geo['description']['identifier']:
            gs[i] = geo
            break
    else:
        gs.append(geo)
    d['format_version'] = '1.16.0'
    wjson(path, d)


def icon(geo, tex, size=64, view=(28, -38, 0)):
    return render_geo.render(None, None, tex, view, size, pad=0.04, quads=render_geo.geo_quads(geo))


def mesh_check(geo):
    """every face wound outward (cross(b - a, c - a) along the stored normal)"""
    bad = 0
    for b in geo['bones']:
        pm = b.get('poly_mesh')
        if not pm:
            continue
        P, N = np.array(pm['positions']), np.array(pm['normals'])
        for poly in pm['polys']:
            a, bb, c = (P[v[0]] for v in poly[:3])
            cr = np.cross(bb - a, c - a)
            if np.linalg.norm(cr) > 1e-9 and np.dot(cr, N[poly[0][1]]) < 0:
                bad += 1
    return bad


@step
def build_models(out, ctx, log):
    rp = os.path.join(out, CORE_RP)
    geo_file = os.path.join(rp, 'models/entity/succubi_extra_items.geo.json')
    cards = 0
    for name, fn in FOODS.items():
        mesh, tex = fn()
        geo = food_geo(f'geometry.succubi_extra_{name}', mesh)
        assert mesh_check(geo) == 0, name
        replace_geo(geo_file, geo)
        tex.save(os.path.join(rp, f'textures/entity/extra/{name}.png'))
        ic = icon(geo, tex)
        ic.save(os.path.join(rp, f'textures/items/extra/{name}.png'))
        cards += swap_everywhere(rp, name, ic)
    geo, tex = watcher_statue()
    assert mesh_check(geo) == 0
    replace_geo(os.path.join(rp, 'models/entity/succubi_shops/watcher_statue.geo.json'), geo)
    tex.save(os.path.join(rp, 'textures/entity/succubi_shops/watcher_statue.png'))
    icon(geo, tex).save(os.path.join(rp, 'textures/items/succubi/watcher_statue_placer.png'))
    geo, tex = shadow_figure()
    assert mesh_check(geo) == 0
    replace_geo(os.path.join(rp, 'models/entity/succubi_shadow_figure.geo.json'), geo)
    tex.save(os.path.join(rp, 'textures/entity/succubi_shops/shadow_figure.png'))
    log(f'models: {len(FOODS)} foods + watcher statue + shadow figure remade, {cards} shop cards updated')
