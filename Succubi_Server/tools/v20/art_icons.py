"""New item icons for the things that looked flat or crude: the 14 amulets, the tool items and the medical kit.
Pixel art at 32 x 32 (saved 64 x 64, nearest), dark outline, three-tone shading - the same family as the bat
icon set. Shop cards that show these icons get the new picture swapped in."""
import os
from PIL import Image, ImageDraw
from registry import step
from common import CORE_RP
import pixel as px

N = 32
INK = (16, 8, 13, 255)
GOLD = [(255, 236, 150), (236, 188, 64), (168, 112, 28)]
BRONZE = [(236, 170, 110), (184, 110, 58), (110, 60, 30)]
SILVER = [(240, 244, 250), (170, 178, 196), (96, 104, 124)]
IVORY = [(255, 250, 232), (230, 216, 180), (170, 150, 110)]
RED = [(255, 120, 120), (214, 44, 56), (130, 16, 30)]


def new():
    return Image.new('RGBA', (N, N)), None


def shaded(draw_fn, tones, light=(-1, -1)):
    """draw a white mask with draw_fn(ImageDraw), colour it with three tones by a diagonal light, return RGBA"""
    m = Image.new('L', (N, N), 0)
    draw_fn(ImageDraw.Draw(m))
    im = Image.new('RGBA', (N, N))
    p, q = im.load(), m.load()
    xs = [x for y in range(N) for x in range(N) if q[x, y]]
    ys = [y for y in range(N) for x in range(N) if q[x, y]]
    if not xs:
        return im
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for y in range(N):
        for x in range(N):
            if q[x, y]:
                ax, ay = -light[0], -light[1]
                t = ((x - x0) / max(1, x1 - x0) * ax + (y - y0) / max(1, y1 - y0) * ay) / max(1e-6, abs(ax) + abs(ay))
                c = tones[0] if t < 0.28 else tones[1] if t < 0.7 else tones[2]
                p[x, y] = px.rgba(c)
    return im


def edge_highlight(im, color, dx=1, dy=1):
    """lighten pixels whose up-left neighbour is transparent (rim light)"""
    out = im.copy()
    p, q = im.load(), out.load()
    for y in range(N):
        for x in range(N):
            if p[x, y][3] and (x - dx < 0 or y - dy < 0 or p[x - dx, y - dy][3] == 0):
                q[x, y] = px.rgba(color)
    return out


def finish(*layers):
    im = Image.new('RGBA', (N, N))
    for l in layers:
        im.alpha_composite(l)
    return px.outline(im, INK)


def loop_top(cx=16, y=1):
    """gold ring for a pendant"""
    return shaded(lambda d: (d.ellipse([cx - 3, y, cx + 3, y + 6], outline=255, width=2)), GOLD)


def frame_pendant(inner_tones, draw_inner, shape='round', frame=GOLD):
    """gold frame + dark window + an inner figure"""
    def outer(d):
        if shape == 'round':
            d.rounded_rectangle([7, 6, 25, 30], radius=7, fill=255)
        else:
            d.ellipse([6, 6, 26, 30], fill=255)
    def window(d):
        if shape == 'round':
            d.rounded_rectangle([9, 8, 23, 28], radius=5, fill=255)
        else:
            d.ellipse([8, 8, 24, 28], fill=255)
    f = edge_highlight(shaded(outer, frame), frame[0])
    w = shaded(window, [(70, 36, 30), (46, 22, 20), (30, 14, 14)])
    fig = shaded(draw_inner, inner_tones)
    return finish(loop_top(), f, w, edge_highlight(fig, inner_tones[0]))


# ------------------------------------------------------------------------------------------ amulets
def luang_por():
    def monk(d):
        d.ellipse([14, 10, 18, 14], fill=255)                  # head
        d.polygon([(12, 15), (20, 15), (22, 24), (10, 24)], fill=255)   # robe
        d.ellipse([9, 22, 23, 27], fill=255)                   # crossed legs
        d.polygon([(15, 9), (17, 9), (16, 7)], fill=255)       # ushnisha
    return frame_pendant(BRONZE, monk)


def nang_kwak():
    def lady(d):
        d.ellipse([14, 10, 18, 14], fill=255)
        d.polygon([(15, 8), (17, 8), (16, 5)], fill=255)       # crown spire
        d.polygon([(12, 15), (20, 15), (21, 26), (11, 26)], fill=255)
        d.rectangle([19, 13, 22, 15], fill=255)                # beckoning hand up
    return frame_pendant([(255, 170, 180), (220, 60, 90), (130, 20, 50)], lady)


def kuman_thong():
    def child(d):
        d.ellipse([13, 10, 19, 16], fill=255)                  # big child head
        d.ellipse([15, 7, 17, 10], fill=255)                   # topknot
        d.rounded_rectangle([12, 16, 20, 23], radius=2, fill=255)
        d.rectangle([12, 23, 15, 27], fill=255)
        d.rectangle([17, 23, 20, 27], fill=255)
    return frame_pendant(GOLD, child, frame=[(210, 170, 120), (120, 70, 40), (70, 36, 20)])


def hanuman():
    def mask(d):
        d.ellipse([10, 11, 22, 26], fill=255)
        d.polygon([(11, 12), (21, 12), (16, 4)], fill=255)     # crown
    face = shaded(mask, [(255, 255, 255), (220, 224, 236), (150, 156, 176)])
    eyes = Image.new('RGBA', (N, N))
    e = ImageDraw.Draw(eyes)
    e.rectangle([12, 16, 14, 17], fill=(20, 110, 60, 255))
    e.rectangle([18, 16, 20, 17], fill=(20, 110, 60, 255))
    e.rectangle([13, 21, 19, 22], fill=(200, 40, 50, 255))      # mouth
    e.line([(16, 12), (16, 15)], fill=(236, 188, 64, 255))
    crown_gold = shaded(lambda d: d.polygon([(11, 12), (21, 12), (16, 4)], fill=255), GOLD)
    return finish(loop_top(), face, crown_gold, eyes)


def takrut():
    tube = shaded(lambda d: d.rounded_rectangle([4, 12, 28, 20], radius=4, fill=255), SILVER, light=(0, -1))
    cords = Image.new('RGBA', (N, N))
    c = ImageDraw.Draw(cords)
    for x in (9, 16, 23):
        c.rectangle([x, 11, x + 1, 21], fill=(214, 44, 56, 255))
    c.line([(16, 11), (16, 4)], fill=(214, 44, 56, 255), width=2)
    etch = Image.new('RGBA', (N, N))
    ImageDraw.Draw(etch).line([(6, 16), (26, 16)], fill=(120, 128, 150, 255))
    return finish(edge_highlight(tube, (255, 255, 255)), etch, cords)


def bia_kae():
    shell = shaded(lambda d: d.ellipse([7, 8, 25, 28], fill=255), IVORY)
    slit = Image.new('RGBA', (N, N))
    s = ImageDraw.Draw(slit)
    s.line([(16, 11), (16, 25)], fill=(110, 80, 50, 255), width=2)
    for y in range(12, 25, 3):
        s.point((14, y), fill=(150, 120, 80, 255)); s.point((18, y), fill=(150, 120, 80, 255))
    thread = Image.new('RGBA', (N, N))
    t = ImageDraw.Draw(thread)
    for y in (14, 20):
        t.line([(7, y), (25, y + 2)], fill=(214, 44, 56, 255), width=1)
    t.line([(16, 8), (16, 2)], fill=(214, 44, 56, 255))
    return finish(edge_highlight(shell, (255, 255, 255)), slit, thread)


def pha_yant():
    cloth = shaded(lambda d: d.polygon([(5, 6), (27, 5), (26, 27), (6, 28)], fill=255),
                   [(255, 240, 230), (240, 218, 204), (200, 170, 160)])
    ink = Image.new('RGBA', (N, N))
    i = ImageDraw.Draw(ink)
    red = (190, 30, 40, 255)
    i.rectangle([8, 8, 24, 25], outline=red)
    for y in (12, 15, 18, 21):
        i.line([(10, y), (22, y)], fill=red)
    i.ellipse([13, 13, 19, 19], outline=red)
    i.line([(16, 9), (16, 24)], fill=red)
    return finish(cloth, ink)


def khiao_suea():
    fang = shaded(lambda d: d.polygon([(12, 8), (21, 8), (19, 18), (14, 29), (13, 20)], fill=255), IVORY)
    cap = shaded(lambda d: d.rounded_rectangle([11, 5, 22, 10], radius=2, fill=255), GOLD)
    return finish(loop_top(y=0), edge_highlight(fang, (255, 255, 255)), edge_highlight(cap, GOLD[0]))


def ta_thip():
    disc = shaded(lambda d: d.ellipse([4, 7, 28, 29], fill=255), [(120, 80, 170), (70, 40, 120), (40, 20, 70)])
    eye = shaded(lambda d: d.ellipse([7, 13, 25, 23], fill=255), [(255, 255, 255), (230, 230, 240), (180, 180, 200)])
    iris = shaded(lambda d: d.ellipse([12, 13, 20, 23], fill=255), [(120, 240, 200), (30, 170, 130), (10, 90, 70)])
    pupil = Image.new('RGBA', (N, N))
    pd = ImageDraw.Draw(pupil)
    pd.ellipse([14, 15, 18, 21], fill=(10, 10, 20, 255))
    pd.point((15, 16), fill=(255, 255, 255, 255))
    rays = Image.new('RGBA', (N, N))
    r = ImageDraw.Draw(rays)
    for x in (10, 16, 22):
        r.line([(x, 9), (x, 11)], fill=(242, 193, 78, 255))
    return finish(loop_top(), edge_highlight(disc, (170, 130, 220)), eye, iris, pupil, rays)


def cursed_doll():
    body = shaded(lambda d: (d.ellipse([10, 3, 22, 14], fill=255), d.rounded_rectangle([12, 12, 20, 24], radius=2, fill=255),
                             d.rectangle([5, 14, 27, 18], fill=255), d.rectangle([12, 22, 15, 30], fill=255), d.rectangle([17, 22, 20, 30], fill=255)),
                  [(214, 170, 120), (160, 110, 64), (96, 60, 30)])
    marks = Image.new('RGBA', (N, N))
    m = ImageDraw.Draw(marks)
    for (x, y) in ((13, 7), (18, 7)):
        m.line([(x - 1, y - 1), (x + 1, y + 1)], fill=(20, 10, 10, 255))
        m.line([(x + 1, y - 1), (x - 1, y + 1)], fill=(20, 10, 10, 255))
    m.line([(13, 11), (19, 11)], fill=(20, 10, 10, 255))
    for x in range(12, 21, 2):
        m.point((x, 18), fill=(90, 50, 25, 255))                # stitches
    pins = Image.new('RGBA', (N, N))
    pdr = ImageDraw.Draw(pins)
    for (a, b, head) in (((25, 9), (18, 15), (214, 44, 56)), ((6, 25), (13, 20), (60, 120, 230)), ((26, 24), (20, 19), (242, 193, 78))):
        pdr.line([a, b], fill=(200, 200, 210, 255))
        pdr.rectangle([a[0] - 1, a[1] - 1, a[0] + 1, a[1] + 1], fill=head + (255,))
    return finish(body, marks, pins)


def yant_kan_phi():
    paper = shaded(lambda d: d.rectangle([9, 2, 23, 30], fill=255), [(255, 244, 150), (246, 214, 80), (200, 160, 40)], light=(0, -1))
    ink = Image.new('RGBA', (N, N))
    i = ImageDraw.Draw(ink)
    red = (200, 26, 36, 255)
    i.rectangle([10, 3, 22, 29], outline=red)
    i.ellipse([13, 5, 19, 11], outline=red)
    i.line([(16, 11), (16, 27)], fill=red)
    for y in (14, 18, 22):
        i.line([(12, y), (20, y + 2)], fill=red)
    i.line([(12, 26), (20, 26)], fill=red)
    return finish(paper, ink)


def lek_lai():
    ore = shaded(lambda d: d.polygon([(16, 5), (24, 13), (22, 25), (14, 28), (8, 20), (9, 11)], fill=255),
                 [(220, 230, 255), (110, 120, 150), (30, 34, 50)])
    gleam = Image.new('RGBA', (N, N))
    g = ImageDraw.Draw(gleam)
    g.line([(12, 11), (15, 8)], fill=(255, 255, 255, 255))
    g.point((20, 21), fill=(200, 220, 255, 255))
    g.point((11, 19), fill=(160, 180, 220, 255))
    return finish(ore, gleam)


def moon():
    stand = shaded(lambda d: d.polygon([(9, 29), (23, 29), (20, 24), (12, 24)], fill=255), GOLD)
    orb = shaded(lambda d: d.ellipse([6, 3, 26, 25], fill=255), [(210, 230, 255), (120, 150, 230), (60, 70, 160)])
    crescent = Image.new('RGBA', (N, N))
    c = ImageDraw.Draw(crescent)
    c.ellipse([10, 7, 22, 19], fill=(255, 248, 210, 255))
    c.ellipse([13, 5, 25, 17], fill=(0, 0, 0, 0))
    shine = Image.new('RGBA', (N, N))
    ImageDraw.Draw(shine).line([(9, 9), (11, 7)], fill=(255, 255, 255, 255))
    base = Image.new('RGBA', (N, N))
    base.alpha_composite(orb)
    cm = crescent.getchannel('A')
    base.paste(crescent, (0, 0), cm)
    return finish(stand, base, shine)


def mae_pho():
    stalks = Image.new('RGBA', (N, N))
    s = ImageDraw.Draw(stalks)
    for (x0, x1) in ((10, 14), (16, 16), (22, 18)):
        s.line([(x0, 6), (x1, 24)], fill=(120, 150, 40, 255))
    grains = Image.new('RGBA', (N, N))
    gd = ImageDraw.Draw(grains)
    for (cx, cy) in ((9, 5), (11, 9), (8, 10), (16, 4), (15, 8), (17, 7), (16, 11), (23, 5), (21, 9), (24, 10)):
        gd.ellipse([cx - 1, cy - 1, cx + 1, cy + 2], fill=(242, 200, 80, 255))
        gd.point((cx - 1, cy - 1), fill=(255, 240, 170, 255))
    tie = shaded(lambda d: d.rounded_rectangle([11, 20, 21, 24], radius=1, fill=255), RED)
    base = shaded(lambda d: d.polygon([(13, 24), (19, 24), (21, 30), (11, 30)], fill=255), [(170, 200, 90), (110, 150, 50), (60, 90, 30)])
    return finish(stalks, base, grains, tie)


AMULET_ART = {
    'luang_por': luang_por, 'takrut': takrut, 'bia_kae': bia_kae, 'pha_yant': pha_yant, 'khiao_suea': khiao_suea,
    'nang_kwak': nang_kwak, 'kuman_thong': kuman_thong, 'ta_thip': ta_thip, 'cursed_doll': cursed_doll,
    'yant_kan_phi': yant_kan_phi, 'lek_lai': lek_lai, 'moon': moon, 'hanuman': hanuman, 'mae_pho': mae_pho,
}


# ------------------------------------------------------------------------------------------ tools
def ghost_bell():
    bell = shaded(lambda d: (d.chord([7, 5, 25, 30], 180, 360, fill=255), d.rectangle([7, 17, 25, 24], fill=255),
                             d.polygon([(4, 24), (28, 24), (26, 27), (6, 27)], fill=255)),
                  [(200, 230, 210), (90, 150, 130), (40, 80, 70)])
    handle = shaded(lambda d: d.rounded_rectangle([13, 1, 19, 7], radius=2, fill=255), [(120, 80, 60), (80, 50, 36), (50, 30, 20)])
    clapper = shaded(lambda d: d.ellipse([14, 26, 18, 30], fill=255), GOLD)
    runes = Image.new('RGBA', (N, N))
    r = ImageDraw.Draw(runes)
    for x in (11, 16, 21):
        r.line([(x, 14), (x, 20)], fill=(230, 255, 240, 200))
    return finish(handle, edge_highlight(bell, (220, 255, 235)), runes, clapper)


def rule_wand():
    staff = Image.new('RGBA', (N, N))
    s = ImageDraw.Draw(staff)
    s.line([(5, 29), (21, 11)], fill=(60, 30, 40, 255), width=3)
    s.line([(6, 28), (21, 12)], fill=(110, 60, 70, 255), width=1)
    gem = shaded(lambda d: d.polygon([(23, 2), (29, 8), (24, 14), (18, 8)], fill=255), [(255, 150, 150), (214, 30, 50), (110, 10, 30)])
    claws = Image.new('RGBA', (N, N))
    c = ImageDraw.Draw(claws)
    for a, b in (((18, 13), (16, 7)), ((20, 15), (26, 15)), ((19, 14), (17, 16))):
        c.line([a, b], fill=(236, 188, 64, 255), width=1)
    b = px.from_rows(["#.....#", "##.#.##", "#######", ".#...#."], {'#': (30, 12, 20)})
    batl = Image.new('RGBA', (N, N))
    batl.alpha_composite(b, (2, 2))
    return finish(staff, claws, edge_highlight(gem, (255, 220, 220)), batl)


def height_adjuster():
    ruler = shaded(lambda d: d.rectangle([12, 2, 20, 30], fill=255), [(255, 230, 150), (236, 188, 64), (170, 120, 30)], light=(-1, 0))
    ticks = Image.new('RGBA', (N, N))
    t = ImageDraw.Draw(ticks)
    for y in range(4, 30, 3):
        t.line([(12, y), (15 if y % 6 else 17, y)], fill=(90, 60, 20, 255))
    arrows = Image.new('RGBA', (N, N))
    a = ImageDraw.Draw(arrows)
    pink = (255, 92, 170, 255)
    a.polygon([(6, 3), (10, 8), (2, 8)], fill=pink)
    a.rectangle([5, 8, 7, 23], fill=pink)
    a.polygon([(6, 29), (10, 24), (2, 24)], fill=pink)
    a.polygon([(26, 3), (30, 8), (22, 8)], fill=pink)
    a.rectangle([25, 8, 27, 23], fill=pink)
    a.polygon([(26, 29), (30, 24), (22, 24)], fill=pink)
    return finish(ruler, ticks, arrows)


def server_settings():
    here = os.path.dirname(os.path.abspath(__file__))
    from art_ui import key_background
    gear = key_background(Image.open(os.path.join(here, '..', '..', 'art', 'pixel_art_native.png')).convert('RGBA'))
    gear = gear.crop(gear.getbbox())
    gear.thumbnail((N, N), Image.LANCZOS)
    im = Image.new('RGBA', (N, N))
    im.alpha_composite(gear, ((N - gear.width) // 2, (N - gear.height) // 2))
    # tidy the downscale into clean pixels
    q = im.load()
    for y in range(N):
        for x in range(N):
            r, g, b, a = q[x, y]
            q[x, y] = (r, g, b, 255 if a > 110 else 0)
    return im


def bandage():
    roll = shaded(lambda d: d.ellipse([4, 8, 22, 26], fill=255), [(255, 255, 255), (230, 226, 216), (170, 164, 150)])
    hole = shaded(lambda d: d.ellipse([10, 14, 16, 20], fill=255), [(150, 140, 130), (110, 100, 90), (80, 70, 60)])
    tail = shaded(lambda d: d.polygon([(18, 22), (29, 17), (30, 24), (20, 27)], fill=255), [(255, 255, 255), (236, 232, 222), (190, 184, 170)])
    cross = Image.new('RGBA', (N, N))
    c = ImageDraw.Draw(cross)
    c.rectangle([23, 19, 26, 23], fill=(214, 44, 56, 255))
    return finish(roll, hole, tail, cross)


def medkit():
    box = shaded(lambda d: d.rounded_rectangle([3, 9, 29, 29], radius=3, fill=255), RED, light=(0, -1))
    handle = shaded(lambda d: d.rounded_rectangle([11, 4, 21, 10], radius=2, outline=255, width=2), [(90, 90, 100), (60, 60, 70), (40, 40, 50)])
    cross = Image.new('RGBA', (N, N))
    c = ImageDraw.Draw(cross)
    c.rectangle([14, 13, 18, 25], fill=(255, 255, 255, 255))
    c.rectangle([10, 17, 22, 21], fill=(255, 255, 255, 255))
    bolt = Image.new('RGBA', (N, N))
    ImageDraw.Draw(bolt).polygon([(24, 12), (21, 18), (24, 18), (22, 24), (27, 16), (24, 16)], fill=(255, 220, 80, 255))
    return finish(handle, edge_highlight(box, RED[0]), cross, bolt)


def syringe():
    im = Image.new('RGBA', (N, N))
    d = ImageDraw.Draw(im)
    d.line([(4, 28), (8, 24)], fill=(210, 216, 230, 255), width=1)                  # needle
    barrel = Image.new('RGBA', (N, N))
    b = ImageDraw.Draw(barrel)
    b.polygon([(8, 21), (20, 9), (24, 13), (12, 25)], fill=(230, 240, 255, 255))
    b.polygon([(9, 22), (16, 15), (19, 18), (12, 25)], fill=(70, 220, 150, 255))   # medicine
    b.line([(10, 21), (19, 12)], fill=(255, 255, 255, 255))
    plunger = Image.new('RGBA', (N, N))
    p = ImageDraw.Draw(plunger)
    p.line([(22, 11), (27, 6)], fill=(150, 156, 176, 255), width=2)
    p.line([(24, 3), (30, 9)], fill=(214, 44, 56, 255), width=2)
    p.line([(19, 8), (25, 14)], fill=(150, 156, 176, 255), width=1)
    return finish(im, barrel, plunger)


TOOLS = {
    'extra/ghost_bell': ghost_bell, 'extra/rule_wand': rule_wand, 'extra/server_settings': server_settings,
    'height_adjuster': height_adjuster, 'bandage_blackpowder': bandage, 'medkit_blackpowder': medkit, 'syringe_blackpowder': syringe,
}


# ------------------------------------------------------------------------------------------ shop cards
def swap_card_icon(card_path, icon, W, H, icon_px, off=False):
    """replace the icon inside a card made by the v1.0.18 card() (icon box at x 5, icon at (8, top + 3))"""
    card = Image.open(card_path).convert('RGBA')
    top = (H - 4 - icon_px - 6) // 2 + 2
    fill = card.getpixel((9, top + 2))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([6, top + 1, 5 + icon_px + 5, top + icon_px + 5], radius=5, fill=fill)
    ic = icon.convert('RGBA')
    bb = ic.getbbox()
    if bb:
        ic = ic.crop(bb)
    side = max(ic.size)
    sq = Image.new('RGBA', (side + 2, side + 2))
    sq.alpha_composite(ic, ((side + 2 - ic.width) // 2, (side + 2 - ic.height) // 2))
    ic = sq.resize((icon_px, icon_px), Image.NEAREST if side <= icon_px else Image.LANCZOS)
    if off:
        g = ic.convert('LA').convert('RGBA')
        g.putalpha(ic.getchannel('A').point(lambda a: int(a * 0.7)))
        ic = g
    card.alpha_composite(ic, (8, top + 3))
    card.save(card_path)


def swap_everywhere(rp, name, icon):
    """every shop card whose file name ends with the item name"""
    d = os.path.join(rp, 'textures/ui/succubi_shops')
    n = 0
    for f in os.listdir(d):
        base = f[:-4]
        off = base.endswith('_off')
        core = base[:-4] if off else base
        if not core.startswith('p_') or not (core.endswith('_' + name) or core.endswith('_amulet_' + name)):
            continue
        im = Image.open(os.path.join(d, f))
        if im.size == (172, 64):
            swap_card_icon(os.path.join(d, f), icon, 172, 64, 40, off)
        elif im.size == (216, 88):
            swap_card_icon(os.path.join(d, f), icon, 216, 88, 60, off)
        else:
            continue
        n += 1
    return n


@step
def build_icons(out, ctx, log):
    rp = os.path.join(out, CORE_RP)
    items = os.path.join(rp, 'textures/items')
    cards = 0
    for k, fn in AMULET_ART.items():
        im = fn()
        px.save(im, os.path.join(items, f'extra/amulet_{k}.png'), 2)
        cards += swap_everywhere(rp, k, im)
    for path, fn in TOOLS.items():
        im = fn()
        px.save(im, os.path.join(items, path + '.png'), 2)
        cards += swap_everywhere(rp, os.path.basename(path), im)
    log(f'icons: {len(AMULET_ART)} amulets + {len(TOOLS)} tools redrawn, {cards} shop cards updated')
