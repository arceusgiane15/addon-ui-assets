"""v1.1 UI renovation:
- one Succubi look for every plain window (list + typing screens): dark plum glass, bat emblem, accent per theme
  (Succubi pink for players, gold for the admin settings item, blood red for the horror kit)
- smooth font (the game's vector font, draws Thai properly) on every Succubi label
- wallet: close X in the corner, the 4th button is now "ตั้งค่า" (player settings, replaces the compass menu)
- height board rebuilt for the preview/confirm flow, with the bat plus/minus buttons from the art pack
- menu icons (HUD, height, guns, back) from / in the style of the bat icon set"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from registry import step
from common import rjson, wjson, CORE_RP, PROJECT, FONT_THAI
import pixel as px

UI = 'textures/ui/succubi_ui/'
ART = os.path.join(PROJECT, 'art')           # the bat icon set (repo root art copied here)
SETTINGS_FLAG, HORROR_FLAG = '§0§9§4§1', '§0§9§4§2'

THEMES = {
    #            panel_top       panel_bottom    card           accent            accent_dark      text
    'default': ((40, 20, 36), (22, 11, 20), (48, 25, 43), (255, 92, 170), (150, 30, 98), (255, 240, 248)),
    'settings': ((30, 26, 44), (15, 13, 24), (40, 35, 58), (242, 193, 78), (150, 110, 30), (255, 248, 230)),
    'horror': ((30, 10, 12), (10, 3, 4), (40, 14, 17), (222, 44, 64), (112, 12, 26), (255, 232, 232)),
}
INK = (8, 4, 7, 255)


def font(size, bold=True):
    f = ImageFont.truetype(FONT_THAI, size)
    try:
        f.set_variation_by_name('Bold' if bold else 'Regular')
    except Exception:
        pass
    return f


def vgrad(w, h, top, bottom):
    im = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=px.rgba(px.mix(top, bottom, y / max(1, h - 1))))
    return im


BAT = [
    "......#...#......",
    "#.....#####.....#",
    "##...#######...##",
    "###.#########.###",
    "#################",
    "#######.#.#######",
    "##..###...###..##",
    "#....#.....#....#",
]


def bat(color, scale=1):
    im = px.from_rows(BAT, {'#': color})
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def window(theme, w, h, title_h=24):
    """w x h GUI units, drawn at 2 texels per unit"""
    top, bottom, card, acc, acc_d, _ = THEMES[theme]
    W, H, T = w * 2, h * 2, title_h * 2
    im = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(im)
    r = 10
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=r, fill=INK)
    d.rounded_rectangle([2, 2, W - 3, H - 3], radius=r - 2, fill=px.rgba(acc_d))
    body = vgrad(W - 8, H - 8, top, bottom)
    m = Image.new('L', body.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, body.width - 1, body.height - 1], radius=r - 4, fill=255)
    im.paste(body, (4, 4), m)
    # title bar
    bar = vgrad(W - 8, T - 4, px.mix(acc_d, top, 0.35), px.mix(acc_d, bottom, 0.75))
    mb = Image.new('L', bar.size, 0)
    ImageDraw.Draw(mb).rounded_rectangle([0, 0, bar.width - 1, bar.height + 10], radius=r - 4, fill=255)
    im.paste(bar, (4, 4), mb)
    d.line([(4, T), (W - 5, T)], fill=px.rgba(acc), width=2)
    d.line([(4, T + 2), (W - 5, T + 2)], fill=INK, width=1)
    d.line([(8, 5), (W - 9, 5)], fill=px.rgba(px.mix(acc, (255, 255, 255), 0.35), 110), width=1)   # glassy top edge
    # bat emblem left of the title
    b = bat(px.rgba(acc), 2)
    im.alpha_composite(px.outline(b, INK), (14, (T - b.height) // 2 + 2))
    # corner filigree
    for (x, y, fx) in ((10, H - 12, 1), (W - 11, H - 12, -1)):
        for i in range(6):
            d.point((x + fx * i, y), fill=px.rgba(acc, 170))
            d.point((x, y - i), fill=px.rgba(acc, 170))
        d.point((x + fx * 2, y - 2), fill=px.rgba(acc, 170))
    return im


def list_button(theme, state):
    """272 x 31 units -> 544 x 62"""
    top, bottom, card, acc, acc_d, _ = THEMES[theme]
    W, H = 544, 62
    im = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(im)
    c = card if state == 'default' else px.mix(card, acc, 0.22) if state == 'hover' else px.mix(card, (0, 0, 0), 0.25)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=8, fill=INK)
    edge = acc if state == 'hover' else px.mix(card, acc, 0.35)
    d.rounded_rectangle([2, 2, W - 3, H - 3], radius=7, fill=px.rgba(edge))
    body = vgrad(W - 8, H - 8, px.mix(c, (255, 255, 255), 0.06), px.mix(c, (0, 0, 0), 0.18))
    m = Image.new('L', body.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, body.width - 1, body.height - 1], radius=5, fill=255)
    im.paste(body, (4, 4), m)
    d.rectangle([4, 10, 9, H - 11], fill=px.rgba(acc if state != 'pressed' else acc_d))      # accent tab
    d.line([(14, 6), (W - 14, 6)], fill=(255, 255, 255, 40))
    return im


def close_button(theme, state):
    top, bottom, card, acc, acc_d, text = THEMES[theme]
    S = 36
    im = Image.new('RGBA', (S, S))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=7, fill=INK)
    fill = acc_d if state == 'default' else acc if state == 'hover' else px.mix(acc_d, (0, 0, 0), 0.3)
    d.rounded_rectangle([2, 2, S - 3, S - 3], radius=6, fill=px.rgba(fill))
    d.line([(4, 4), (S - 5, 4)], fill=(255, 255, 255, 60))
    for off, col in ((1, INK), (0, px.rgba(text))):
        d.line([(11 + off, 11 + off), (24 + off, 24 + off)], fill=col, width=4)
        d.line([(24 + off, 11 + off), (11 + off, 24 + off)], fill=col, width=4)
    return im


# ------------------------------------------------------------------------------------------ icons
def key_background(im, tol=24):
    """art drawn on a solid backdrop: flood the backdrop colour from the corners to transparent"""
    im = im.copy()
    w, h = im.size
    p = im.load()
    bg = p[0, 0]
    if bg[3] < 255:
        return im
    seen, stack = set(), [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        c = p[x, y]
        if max(abs(c[i] - bg[i]) for i in range(3)) > tol:
            continue
        p[x, y] = (0, 0, 0, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return im


def load_art(name, size):
    im = key_background(Image.open(os.path.join(ART, name)).convert('RGBA'))
    bbox = im.getbbox()
    im = im.crop(bbox)
    side = max(im.size)
    sq = Image.new('RGBA', (side, side))
    sq.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    return sq.resize((size, size), Image.NEAREST if size >= side else Image.LANCZOS)


def icon_tile(inner, bg=(34, 17, 30), edge=(255, 92, 170)):
    """48x48 rounded tile with an icon, for list buttons"""
    im = Image.new('RGBA', (48, 48))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 47, 47], radius=9, fill=INK)
    d.rounded_rectangle([2, 2, 45, 45], radius=8, fill=px.rgba(edge))
    d.rounded_rectangle([4, 4, 43, 43], radius=7, fill=px.rgba(bg))
    inner = inner.copy()
    inner.thumbnail((34, 34), Image.NEAREST)
    im.alpha_composite(inner, ((48 - inner.width) // 2, (48 - inner.height) // 2))
    return im


def pix_icon(rows, pal, scale):
    return px.outline(px.from_rows(rows, pal), INK).resize(((len(rows[0]) + 0) * scale, len(rows) * scale), Image.NEAREST)


HUD_ICON = ["................",
            "..############..",
            ".#pppppppppppp#.",
            ".#p##pp##pp##p#.",
            ".#p#rp#yp#bp#p#.",
            ".#p#rp#yp#bp#p#.",
            ".#pppppppppppp#.",
            "..############..",
            "................"]
RULER_ICON = ["..##..",
              ".#yy#.",
              ".#yk#.",
              ".#yy#.",
              ".#yk#.",
              ".#yy#.",
              ".#yk#.",
              ".#yy#.",
              ".#yk#.",
              ".#yy#.",
              "..##.."]
GUN_ICON = ["................",
            ".##############.",
            ".#gggggggggggggg#",
            ".##gg#########...",
            "..#gg#.#k#......",
            "..#gg###k#......",
            "..#gg#.##.......",
            "..####.........."]


def menu_icons(rp):
    d = os.path.join(rp, UI, 'icons')
    os.makedirs(d, exist_ok=True)
    back = load_art('red_back_button_white_arrow.png', 40)
    icon_tile(back).save(os.path.join(d, 'back.png'))
    hud = px.from_rows(["..............",
                        ".############.",
                        ".#rrrrrrrr..#.",
                        ".############.",
                        ".#yyyyyy....#.",
                        ".############.",
                        ".#bbbbbbbbb.#.",
                        ".############.",
                        ".#vvvvv.....#.",
                        ".############."],
                       {'#': (10, 5, 9), 'r': (232, 51, 94), 'y': (240, 164, 49), 'b': (51, 181, 240), 'v': (176, 102, 240)})
    icon_tile(hud.resize((hud.width * 3, hud.height * 3), Image.NEAREST)).save(os.path.join(d, 'hud.png'))
    ruler = px.from_rows(["...#....#.",
                          "..###..#w#",
                          "..###..#w#",
                          "...#...#w#",
                          "..###..#w#",
                          ".#####.#w#",
                          ".#####.#w#",
                          "..###..#w#",
                          "..#.#..#w#",
                          "..#.#..###"],
                         {'#': (255, 92, 170), 'w': (255, 240, 248)})
    icon_tile(px.outline(ruler, INK).resize((36, 36), Image.NEAREST)).save(os.path.join(d, 'height.png'))
    gun = px.from_rows(["..............",
                        ".############.",
                        ".#ggggggggggg#",
                        ".##gg########.",
                        "..#gg#.#k#....",
                        "..#gg###k#....",
                        "..#gg#.##.....",
                        "..####........"],
                       {'#': (20, 16, 22), 'g': (120, 122, 136), 'k': (60, 58, 70)})
    icon_tile(gun.resize((gun.width * 3, gun.height * 3), Image.NEAREST)).save(os.path.join(d, 'gun.png'))
    gear = load_art('pixel_art_native.png', 40)
    icon_tile(gear, edge=(242, 193, 78)).save(os.path.join(d, 'settings.png'))
    scr = px.from_rows(["############",
                        "#rr......rr#",
                        "#r..gggg..r#",
                        "#..gggggg..#",
                        "#..gggggg..#",
                        "#r..gggg..r#",
                        "#rr......rr#",
                        "############",
                        "     ##     ",
                        "   ######   "],
                       {'#': (30, 22, 32), 'r': (214, 30, 50), 'g': (150, 146, 156), '.': (70, 60, 80)})
    icon_tile(px.outline(scr, INK).resize((42, 35), Image.NEAREST)).save(os.path.join(d, 'screen_fx.png'))


# ------------------------------------------------------------------------------------------ JSON
def has(flag):
    return f"(not ((#title_text - '{flag}') = #title_text))"


def theme_visible(t):
    if t == 'default':
        return f"((#title_text - '{SETTINGS_FLAG}') = #title_text) and ((#title_text - '{HORROR_FLAG}') = #title_text)"
    return has(SETTINGS_FLAG if t == 'settings' else HORROR_FLAG)


def themed(name, tex_fn):
    out = []
    for t in THEMES:
        out.append({f"{name}_{t}": {"type": "image", "texture": tex_fn(t), "size": ["100%", "100%"], "layer": 1,
                                   "bindings": [{"binding_name": "#title_text"},
                                                {"binding_type": "view", "source_property_name": f"({theme_visible(t)})",
                                                 "target_property_name": "#visible"}]}})
    return out


def restyle_windows(ui):
    """new art + title next to the bat emblem; sizes a little larger for readability"""
    for kind, (w, h) in (('list_window', (320, 220)), ('modal_window', (320, 234))):
        win = ui[kind]
        win['size'] = [w, h]
        for c in win['controls']:
            (k, v), = c.items()
            if k == 'title':
                v.update({"offset": [38, 7], "size": ["100% - 70px", 12], "font_scale_factor": 1.1})
            if k.startswith('close'):
                v.update({"offset": [-6, 3]})
            if k == 'content':
                v.update({"offset": [10, 30], "size": [w - 20, h - 40]})
    return ui


FORM_FLAGS = None


def smooth(node):
    """every Succubi label uses the smooth (vector) font: Thai vowels and tone marks sit where they belong"""
    n = 0
    if isinstance(node, dict):
        if node.get('type') == 'label' and 'font_type' not in node:
            node['font_type'] = 'smooth'
            n += 1
        for v in node.values():
            n += smooth(v)
    elif isinstance(node, list):
        for v in node:
            n += smooth(v)
    return n


def wallet_ui(ui):
    """close X in the corner (the 4th row button is now settings)"""
    wp = ui['wallet_panel']
    wp['controls'] = [c for c in wp['controls'] if 'close' not in next(iter(c))]
    wp['controls'].append({"close@succubi_ui.close_button": {"anchor_from": "top_right", "anchor_to": "top_right", "offset": [-10, 10], "layer": 8}})
    return ui


def wallet_art(rp):
    d = os.path.join(rp, 'textures/ui/succubi_wallet')
    base = Image.open(os.path.join(d, 'btn_amulet_s.png')).convert('RGBA')        # purple-red candy button, icon well left
    W, H = base.size
    im = Image.new('RGBA', (W, H))
    # recolour the amulet button to royal purple and swap the icon
    src = base.load()
    q = im.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = src[x, y]
            if a and x > 40:
                lum = (r * 0.3 + g * 0.59 + b * 0.11) / 255
                r, g, b = int(92 + 90 * lum), int(44 + 50 * lum), int(150 + 90 * lum)
            q[x, y] = (r, g, b, a)
    gear = load_art('pixel_art_native.png', 30)
    ImageDraw.Draw(im).rounded_rectangle([7, 7, 43, 43], radius=5, fill=(24, 12, 22, 255))
    im.alpha_composite(gear, (10, 10))
    im.save(os.path.join(d, 'btn_settings_s.png'))


# ------------------------------------------------------------------------------------------ height board
H_W, H_H = 284, 184


def height_art(rp):
    d = os.path.join(rp, 'textures/ui/succubi_height')
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    top, bottom, card, acc, acc_d, text = THEMES['default']
    bg = window('default', H_W, H_H)
    dr = ImageDraw.Draw(bg)
    # ruler well (left) and info well (right)
    dr.rounded_rectangle([20, 60, 2 * 118, 2 * H_H - 20], radius=10, fill=(12, 6, 11, 230))
    dr.rounded_rectangle([2 * 126, 60, 2 * H_W - 20, 2 * 96], radius=10, fill=(12, 6, 11, 230))
    bg.save(os.path.join(d, 'height_bg.png'))
    # ruler scales: players 0-250 cm, admins 0-500 cm (drawn into the well: 108 x 146 units at (10,30))
    for mode, top_cm, step_cm in (('P', 250, 10), ('A', 500, 20)):
        im = Image.new('RGBA', (216, 292))
        rd = ImageDraw.Draw(im)
        f = font(15)
        for cm in range(0, top_cm + 1, step_cm):
            y = 292 - 12 - (cm / top_cm) * 264
            major = cm % (step_cm * 5) == 0
            rd.line([(8, y), (8 + (16 if major else 8), y)], fill=(255, 190, 226, 220 if major else 120), width=2 if major else 1)
            if major:
                rd.text((28, y - 9), str(cm), font=f, fill=(255, 190, 226, 230))
        y180 = 292 - 12 - (180 / top_cm) * 264
        for xx in range(8, 208, 8):
            rd.line([(xx, y180), (xx + 4, y180)], fill=(255, 92, 170, 200), width=2)
        im.save(os.path.join(d, f'ruler_{mode}.png'))
    person(d)
    # buttons 36 x 22 units
    art = {
        'minus': load_art('black_red_minus_button_bat_128x128.png', 34),
        'plus': load_art('green_plus_button_white_plus.png', 34),
        'close': load_art('red_back_button_white_arrow.png', 34),
    }
    for name, col in (('minus', (150, 30, 60)), ('plus', (40, 140, 80)), ('type', (70, 60, 120)), ('reset', (150, 110, 30)),
                      ('confirm', (230, 70, 150)), ('close', (90, 30, 40))):
        for off in (False, True):
            im = Image.new('RGBA', (72, 44))
            bd = ImageDraw.Draw(im)
            c = col if not off else (60, 52, 58)
            bd.rounded_rectangle([0, 0, 71, 43], radius=8, fill=INK)
            bd.rounded_rectangle([2, 2, 69, 41], radius=7, fill=px.rgba(px.mix(c, (255, 255, 255), 0.18)))
            bd.rounded_rectangle([2, 6, 69, 41], radius=7, fill=px.rgba(c))
            bd.line([(8, 5), (63, 5)], fill=(255, 255, 255, 90))
            if name in art:
                a = art[name].copy()
                a.thumbnail((30, 30), Image.LANCZOS)
                if off:
                    a = a.convert('LA').convert('RGBA')
                    a.putalpha(a.getchannel('A').point(lambda v: v // 2))
                im.alpha_composite(a, (4, 7))
            im.save(os.path.join(d, f'btn_{name}{"_off" if off else ""}.png'))
    for name in ('hover', 'pressed'):
        im = Image.new('RGBA', (72, 44))
        ImageDraw.Draw(im).rounded_rectangle([2, 2, 69, 41], radius=7, fill=(255, 255, 255, 50) if name == 'hover' else (0, 0, 0, 70))
        im.save(os.path.join(d, f'btn_{name}.png'))


def person(d):
    """pixel silhouettes: you (pink) and the 180 cm reference (grey), 17 x 34 art px"""
    rows = [
        ".......###.......",
        "......#####......",
        "......#####......",
        "......#####......",
        ".......###.......",
        "....#########....",
        "...###########...",
        "..#############..",
        "..###.#####.###..",
        "..###.#####.###..",
        "..###.#####.###..",
        "..###.#####.###..",
        "..##..#####..##..",
        "..##..#####..##..",
        "......#####......",
        "......##.##......",
        "......##.##......",
        "......##.##......",
        "......##.##......",
        "......##.##......",
        "......##.##......",
        ".....###.###.....",
    ]
    for name, col in (('person', (255, 92, 170)), ('person_ref', (140, 120, 136))):
        im = px.outline(px.from_rows(rows, {'#': col}), INK)
        im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.path.join(d, f'{name}.png'))


def height_json():
    T = 'textures/ui/succubi_height/'
    RULER = (12, 32, 104, 144)                      # x, y, w, h (units) of the ruler well contents
    ctl = [{"bg": {"type": "image", "texture": T + "height_bg", "size": ["100%", "100%"], "layer": 1}},
           {"title": {"type": "label", "text": "§lปรับส่วนสูง", "color": [1, 0.94, 0.97], "shadow": True, "localize": False,
                      "anchor_from": "top_left", "anchor_to": "top_left", "offset": [38, 7], "layer": 5, "font_scale_factor": 1.1}},
           {"close@succubi_ui.close_button": {"anchor_from": "top_right", "anchor_to": "top_right", "offset": [-6, 3], "layer": 8}}]
    tt = "#title_text"
    for mode, top_cm in (('P', 250), ('A', 500)):
        ctl.append({f"ruler_{mode}": {"type": "image", "texture": T + f"ruler_{mode}", "size": [RULER[2], RULER[3] + 2],
                                      "offset": [RULER[0], RULER[1]], "anchor_from": "top_left", "anchor_to": "top_left", "layer": 2,
                                      "bindings": [{"binding_name": tt}, {"binding_type": "view", "target_property_name": "#visible",
                                                                           "source_property_name": f"(not (({tt} - 'r{mode}') = {tt}))"}]}})
        base_y = RULER[1] + RULER[3] + 2 - 6        # floor line inside the ruler art
        px_per_cm = (RULER[3] + 2) * (264 / 292) / top_cm
        ref_h = 180 * px_per_cm
        ctl.append({f"ref_{mode}": {"type": "image", "texture": T + "person_ref", "size": [ref_h / 2, ref_h],
                                    "offset": [RULER[0] + 58, base_y], "anchor_from": "top_left", "anchor_to": "bottom_middle", "layer": 3,
                                    "bindings": [{"binding_name": tt}, {"binding_type": "view", "target_property_name": "#visible",
                                                                         "source_property_name": f"(not (({tt} - 'r{mode}') = {tt}))"}]}})
        for n in range(1, 51):
            cm = n * 10
            if cm > top_cm:
                continue
            h = cm * px_per_cm
            ctl.append({f"you_{mode}_{n:03d}": {
                "type": "image", "texture": T + "person", "size": [h / 2, h], "offset": [RULER[0] + 86, base_y],
                "anchor_from": "top_left", "anchor_to": "bottom_middle", "layer": 3,
                "bindings": [{"binding_name": tt}, {"binding_type": "view", "target_property_name": "#visible",
                                                    "source_property_name": f"((not (({tt} - 'r{mode}') = {tt})) and (not (({tt} - 'h{n:03d}') = {tt})))"}]}})
    ctl.append({"info": {"type": "label", "text": "#form_text", "color": [1, 0.93, 0.97], "localize": False, "shadow": True,
                         "anchor_from": "top_left", "anchor_to": "top_left", "offset": [132, 36], "size": [140, "default"], "layer": 5,
                         "bindings": [{"binding_name": "#form_text"}]}})
    ctl.append({"buttons": {"type": "grid", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [126, 104],
                            "size": [152, 48], "grid_dimensions": [4, 2], "grid_item_template": "succubi_height.cell",
                            "collection_name": "form_buttons", "layer": 5}})
    return ctl


def height_ui(ui):
    ui['height_panel'] = {"type": "panel", "size": [H_W, H_H], "layer": 2, "controls": height_json()}
    ui['cell'] = {"type": "panel", "size": [38, 24], "controls": [{"button@common.button": {
        "size": [36, 22], "$pressed_button_name": "button.form_button_click",
        "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
        "controls": [{"default@succubi_height.hb_default": {}}, {"hover@succubi_height.hb_hover": {}}, {"pressed@succubi_height.hb_pressed": {}}]}}]}
    # label sits right of the icon
    ui['hb_label'].update({"anchor_from": "center", "anchor_to": "center", "offset": [5, -1]})
    return ui


@step
def build_ui(out, ctx, log):
    rp = os.path.join(out, CORE_RP)
    d = os.path.join(rp, UI)
    for t in THEMES:
        window(t, 320, 220).save(os.path.join(d, f'list_{t}.png'))
        window(t, 320, 234).save(os.path.join(d, f'modal_{t}.png'))
        for s in ('default', 'hover', 'pressed'):
            list_button(t, s).save(os.path.join(d, f'btn_{t}_{s}.png'))
            close_button(t, s).save(os.path.join(d, f'x_{t}_{s}.png'))
    menu_icons(rp)
    wallet_art(rp)
    height_art(rp)

    uid = os.path.join(rp, 'ui')
    ui = restyle_windows(rjson(os.path.join(uid, 'succubi_ui.json')))
    wjson(os.path.join(uid, 'succubi_ui.json'), ui)
    wjson(os.path.join(uid, 'succubi_wallet.json'), wallet_ui(rjson(os.path.join(uid, 'succubi_wallet.json'))))
    wjson(os.path.join(uid, 'succubi_height.json'), height_ui(rjson(os.path.join(uid, 'succubi_height.json'))))
    n = 0
    for f in sorted(os.listdir(uid)):
        if f.endswith('.json') and (f.startswith('succubi_') or f == 'server_form.json'):
            data = rjson(os.path.join(uid, f))
            k = smooth(data)
            n += k
            wjson(os.path.join(uid, f), data)
    log(f'UI: Succubi theme windows, wallet settings button, height board, smooth font on {n} labels')


# ------------------------------------------------------------------------------------------ pack icon for the gun packs
def guns_pack_icon():
    S = 256
    im = Image.new('RGBA', (S, S), (10, 5, 9, 255))
    d = ImageDraw.Draw(im)
    glow = Image.new('RGBA', (S, S))
    gp = glow.load()
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - S / 2, y - 104) / 118
            if r < 1:
                gp[x, y] = (255, 60, 150, int(110 * (1 - r) ** 2))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    pink = (255, 79, 163, 255)
    d.ellipse([48, 24, 208, 184], outline=pink, width=10)
    for (x0, y0, x1, y1) in ((128, 6, 128, 58), (128, 150, 128, 202), (30, 104, 82, 104), (174, 104, 226, 104)):
        d.line([(x0, y0), (x1, y1)], fill=pink, width=10)
    b = bat((255, 214, 234, 255), 5)
    im.alpha_composite(px.outline(b, INK), ((S - b.width) // 2, 104 - b.height // 2))
    f = font(58)
    t = 'GUNS'
    w = d.textlength(t, font=f)
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        d.text(((S - w) / 2 + dx, 190 + dy), t, font=f, fill=(10, 5, 9, 255))
    d.text(((S - w) / 2, 190), t, font=f, fill=pink)
    return im


@step
def build_pack_icons(out, ctx, log):
    from common import GUNS_BP, GUNS_RP
    icon = guns_pack_icon()
    for p in (GUNS_BP, GUNS_RP):
        icon.save(os.path.join(out, p, 'pack_icon.png'))
    src = os.path.join(ctx['src'], CORE_RP.replace('RP', 'BP'), 'pack_icon.png')
    for p in ('Succubi Server BP', 'Succubi Server RP'):
        Image.open(src).save(os.path.join(out, p, 'pack_icon.png'))
    log('pack icons: Succubi Guns icon drawn')
