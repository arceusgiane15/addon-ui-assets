"""Succubi HUD v2: two rows of bars above the hotbar, in the place of the vanilla hearts / hunger.

  [♥ ████████▒▒ 86]        [▒▒████████ 🍗]      bottom row: health (+number, poison/wither colours) | food
  [💧 ██████▒▒▒▒   ]        [▒▒▒███████ 🧠]      top row:    thirst | sanity (hidden when switched off)
  [🛡 8] armor badge left of the health bar, only while wearing armor

Art is drawn at 2 art-pixels per GUI unit and saved 2x upscaled (4 texels per unit, nearest = crisp).
Data comes from the title "shud:..." (see BP scripts/succubi/hud.js); a hidden control keeps the last
value after the title fades, so the script only sends changes."""
import math, os
from PIL import Image, ImageDraw
from registry import step
from common import wjson, CORE_RP, GUNS_RP, rjson
import pixel as px

TEX = 'textures/ui/succubi_hud/'
D = 2                  # art pixels per GUI unit
CELL_W, CELL_H = 82, 9  # GUI units
ICON = 9
BAR_W = CELL_W - ICON - 1   # 72 units: 1 frame + 70 inner + 1 frame
STEPS = 20

STATS = {
    # key: (token letter, light, main, dark, side)
    'health': ('H', (255, 134, 164), (232, 51, 94), (150, 18, 56), 'left'),
    'health_poison': ('H', (170, 232, 110), (96, 178, 46), (52, 112, 24), 'left'),
    'health_wither': ('H', (130, 130, 138), (70, 68, 76), (34, 32, 38), 'left'),
    'food': ('F', (255, 214, 128), (240, 164, 49), (170, 104, 22), 'right'),
    'thirst': ('T', (150, 228, 255), (51, 181, 240), (22, 110, 176), 'left'),
    'sanity': ('S', (228, 176, 255), (176, 102, 240), (110, 52, 176), 'right'),
}
TRACK_TOP, TRACK, TRACK_BOTTOM = (26, 14, 23, 235), (44, 24, 38, 235), (58, 33, 51, 235)
FRAME = (10, 5, 9, 255)


# ------------------------------------------------------------------------------------------ art
def bar_frame(side):
    """frame + empty track, BAR_W x CELL_H units, pill shaped, subtle segment ticks every 2 steps"""
    w, h = BAR_W * D, CELL_H * D
    im = px.canvas(w, h)
    d = ImageDraw.Draw(im)
    r = h // 2
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=FRAME)
    d.rounded_rectangle([2, 2, w - 3, h - 3], radius=r - 2, fill=TRACK)
    d.line([(r, 2), (w - r, 2)], fill=TRACK_TOP, width=1)
    d.line([(r, h - 3), (w - r, h - 3)], fill=TRACK_BOTTOM, width=1)
    return im


def inner_box():
    return 2, 2, BAR_W * D - 3, CELL_H * D - 3     # x0, y0, x1, y1 inside the frame (art px)


def bar_fill(stat, steps, side):
    """only the coloured part for `steps` of 20, same size as the frame"""
    _, light, main, dark, _ = STATS[stat]
    w, h = BAR_W * D, CELL_H * D
    x0, y0, x1, y1 = inner_box()
    full = x1 - x0 + 1
    n = round(full * steps / STEPS)
    im = px.canvas(w, h)
    if n <= 0:
        return im
    fill = px.canvas(w, h)
    d = ImageDraw.Draw(fill)
    ih = y1 - y0 + 1
    for yy in range(ih):
        t = yy / max(1, ih - 1)
        c = px.mix(light, main, min(1, t * 2.2)) if t < 0.45 else px.mix(main, dark, (t - 0.45) / 0.55)
        d.line([(x0, y0 + yy), (x1, y0 + yy)], fill=px.rgba(c))
    d.line([(x0 + 2, y0), (x1 - 2, y0)], fill=px.rgba(px.mix(light, (255, 255, 255), 0.55)))   # gloss
    # segment ticks: 10 segments like the vanilla hearts
    for i in range(1, 10):
        tx = x0 + round(full * i / 10)
        d.line([(tx, y0 + 1), (tx, y1)], fill=px.rgba(dark, 150))
    # clip to the rounded inner shape and to n pixels from the fill side
    mask = px.canvas(w, h)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([x0, y0, x1, y1], radius=(ih) // 2, fill=(255, 255, 255, 255))
    if side == 'left':
        md.rectangle([x0 + n, 0, w, h], fill=(0, 0, 0, 0))
    else:
        md.rectangle([0, 0, x1 - n, h], fill=(0, 0, 0, 0))
    im.paste(fill, (0, 0), mask.getchannel('A'))
    # bright leading edge
    ed = ImageDraw.Draw(im)
    ex = x0 + n - 1 if side == 'left' else x1 - n + 1
    if 0 < n < full:
        ed.line([(ex, y0 + 1), (ex, y1 - 1)], fill=px.rgba(px.mix(light, (255, 255, 255), 0.4)))
    return im


def _shade_shape(mask, light, main, dark, glint=True):
    """colour a 1-bit shape with a top-left light / bottom-right dark gradient, then outline it"""
    w, h = mask.size
    im = px.canvas(w, h)
    p, m = im.load(), mask.load()
    for y in range(h):
        for x in range(w):
            if m[x, y][3] > 127:
                t = (x * 0.45 + y * 0.8) / (w * 0.45 + h * 0.8)
                c = px.mix(light, main, min(1, t * 2)) if t < 0.5 else px.mix(main, dark, (t - 0.5) * 2)
                p[x, y] = px.rgba(c)
    return px.outline(im, FRAME)


def icon_heart(light, main, dark):
    s = ICON * D                                        # 18
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.ellipse([1, 2, 9, 10], fill=(255, 255, 255, 255))
    d.ellipse([8, 2, 16, 10], fill=(255, 255, 255, 255))
    d.polygon([(1, 7), (16, 7), (8.5, 16)], fill=(255, 255, 255, 255))
    im = _shade_shape(m, light, main, dark)
    q = im.load()
    for (x, y) in ((4, 4), (5, 4), (4, 5)):
        q[x, y] = px.WHITE
    return im


def icon_drumstick():
    s = ICON * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.ellipse([6, 1, 16, 11], fill=(255, 255, 255, 255))           # meat
    d.polygon([(7, 8), (10, 11), (5, 13)], fill=(255, 255, 255, 255))
    meat = _shade_shape(m, (255, 196, 120), (205, 110, 45), (120, 56, 20))
    bone = px.canvas(s, s)
    b = ImageDraw.Draw(bone)
    b.line([(3, 14), (7, 10)], fill=(236, 226, 214, 255), width=2)
    b.ellipse([1, 13, 4, 16], fill=(236, 226, 214, 255))
    b.ellipse([2, 14, 5, 17], fill=(236, 226, 214, 255))
    bone = px.outline(bone, FRAME)
    bone.alpha_composite(meat)
    q = bone.load()
    for (x, y) in ((9, 3), (10, 3), (9, 4)):
        q[x, y] = (255, 236, 200, 255)
    return bone


def icon_drop():
    s = ICON * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.ellipse([3, 6, 14, 17], fill=(255, 255, 255, 255))
    d.polygon([(8.5, 0), (3.2, 10), (13.8, 10)], fill=(255, 255, 255, 255))
    im = _shade_shape(m, (190, 240, 255), (51, 181, 240), (18, 96, 160))
    q = im.load()
    for (x, y) in ((6, 9), (6, 10), (7, 8), (6, 11)):
        q[x, y] = px.WHITE
    return im


def icon_brain():
    s = ICON * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    for box in ([1, 3, 9, 11], [8, 3, 16, 11], [2, 7, 10, 15], [7, 7, 15, 15], [4, 1, 13, 8]):
        d.ellipse(box, fill=(255, 255, 255, 255))
    im = _shade_shape(m, (255, 200, 236), (214, 120, 220), (120, 52, 150))
    d2 = ImageDraw.Draw(im)
    fold = (120, 52, 150, 255)
    d2.line([(8, 3), (8, 14)], fill=fold)
    d2.line([(4, 7), (6, 6)], fill=fold)
    d2.line([(11, 6), (13, 8)], fill=fold)
    d2.line([(4, 11), (6, 12)], fill=fold)
    d2.line([(11, 12), (13, 11)], fill=fold)
    q = im.load()
    for (x, y) in ((5, 4), (6, 4)):
        q[x, y] = px.WHITE
    return im


def icon_shield():
    s = ICON * D
    m = px.canvas(s, s)
    d = ImageDraw.Draw(m)
    d.polygon([(2, 2), (15, 2), (15, 8), (8.5, 16), (2, 8)], fill=(255, 255, 255, 255))
    im = _shade_shape(m, (236, 240, 248), (160, 170, 188), (86, 94, 112))
    d2 = ImageDraw.Draw(im)
    d2.line([(8, 3), (8, 14)], fill=(236, 240, 248, 255))
    d2.line([(9, 3), (9, 14)], fill=(110, 118, 136, 255))
    return im


def glow(color, size):
    """soft round glow for the low-value pulse (not pixel art on purpose)"""
    s = size * D * 2
    im = Image.new('RGBA', (s, s))
    p = im.load()
    c = s / 2
    for y in range(s):
        for x in range(s):
            r = math.hypot(x + 0.5 - c, y + 0.5 - c) / c
            a = max(0.0, 1 - r) ** 1.6
            p[x, y] = tuple(color[:3]) + (int(a * 200),)
    return im


def draw_all(rp):
    d = os.path.join(rp, TEX)
    for side in ('left', 'right'):
        px.save(bar_frame(side), os.path.join(d, f'frame_{side}.png'), 2)
    for stat, (_, light, main, dark, side) in STATS.items():
        for n in range(1, STEPS + 1):
            px.save(bar_fill(stat, n, side), os.path.join(d, f'fill_{stat}_{n:02d}.png'), 2)
    px.save(icon_heart(*STATS['health'][1:4]), os.path.join(d, 'icon_health.png'), 2)
    px.save(icon_heart(*STATS['health_poison'][1:4]), os.path.join(d, 'icon_health_poison.png'), 2)
    px.save(icon_heart(*STATS['health_wither'][1:4]), os.path.join(d, 'icon_health_wither.png'), 2)
    px.save(icon_drumstick(), os.path.join(d, 'icon_food.png'), 2)
    px.save(icon_drop(), os.path.join(d, 'icon_thirst.png'), 2)
    px.save(icon_brain(), os.path.join(d, 'icon_sanity.png'), 2)
    px.save(icon_shield(), os.path.join(d, 'icon_armor.png'), 2)
    for k, c in (('health', (255, 40, 90)), ('food', (255, 160, 40)), ('thirst', (40, 170, 255)), ('sanity', (190, 90, 255))):
        glow(c, 12).save(os.path.join(d, f'glow_{k}.png'))
    for ch in '0123456789':
        px.save(digit_big(ch), os.path.join(d, f'num_{ch}.png'), 2)
    # armor badge plate
    plate = px.canvas(19 * D, CELL_H * D)
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, 19 * D - 1, CELL_H * D - 1], radius=CELL_H * D // 2, fill=(10, 5, 9, 200))
    px.save(plate, os.path.join(d, 'armor_plate.png'), 2)


# 5x7 digits (art px) with a 1px outline -> 7x9 art px = 3.5 x 4.5 units
BIG = {
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['.###.', '#...#', '....#', '..##.', '....#', '#...#', '.###.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['..##.', '.#...', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'],
}


def digit_big(ch):
    im = px.canvas(7, 9)
    q = im.load()
    for y, r in enumerate(BIG[ch]):
        for x, c in enumerate(r):
            if c == '#':
                q[x + 1, y + 1] = px.WHITE
    return px.outline(im, FRAME)


# ------------------------------------------------------------------------------------------ JSON UI
DATA = 'succubi_hud_data'
P = '#preserved_text'


def has(tok):
    return f"(not (({P} - '{tok}') = {P}))"


def hasnt(tok):
    return f"(({P} - '{tok}') = {P})"


def vis(expr):
    return [{"binding_type": "view", "source_control_name": DATA, "source_property_name": f"({expr})",
             "target_property_name": "#visible"}]


def img(tex, size, offset=(0, 0), layer=1, expr=None, anchor='top_left', **kw):
    c = {"type": "image", "texture": TEX + tex, "size": list(size), "offset": list(offset), "layer": layer,
         "anchor_from": anchor, "anchor_to": anchor}
    if expr:
        c["bindings"] = vis(expr)
    c.update(kw)
    return c


def cell(stat_key, letter, side, x, y, icon_variants, low_flag, glow_key, number=False):
    """one stat: frame, 20 fills (visible by token), icon (+ variants), low pulse, optional number"""
    ctl = []
    bar_x = ICON + 1 if side == 'left' else 0
    icon_x = 0 if side == 'left' else BAR_W + 1
    ctl.append({"frame": img(f'frame_{side}', (BAR_W, CELL_H), (bar_x, 0), 2)})
    fills = [(stat_key, None)] if stat_key != 'health' else [('health', 'Pn'), ('health_poison', 'Pp'), ('health_wither', 'Pw')]
    for key, tint in fills:
        for n in range(1, STEPS + 1):
            expr = has(f'{letter}{n:02d}') + (f" and {has(tint)}" if tint else '')
            ctl.append({f"fill_{key}_{n:02d}": img(f'fill_{key}_{n:02d}', (BAR_W, CELL_H), (bar_x, 0), 3, expr)})
    ctl.append({"glow": img(f'glow_{glow_key}', (ICON * 2, ICON * 2), (icon_x - ICON / 2, -ICON / 2), 1, has(low_flag),
                            alpha="@succubi_hud.pulse_out")})
    for tex, expr in icon_variants:
        ctl.append({f"icon_{tex}": img(tex, (ICON, ICON), (icon_x, 0), 4, expr)})
    if number:
        # health number, right end of the bar: ones / tens / hundreds (leading zeros hidden)
        R = bar_x + BAR_W - 3
        for pos, (letter_d, cond) in enumerate((('Z', None), ('Y', 'tens'), ('X', 'hundreds'))):
            for dgt in range(10):
                if cond == 'hundreds' and dgt == 0:
                    continue
                expr = has(f'{letter_d}{dgt}')
                if cond == 'tens' and dgt == 0:
                    expr += f" and {hasnt('X0')}"
                ctl.append({f"n{letter_d}{dgt}": img(f'num_{dgt}', (3.5, 4.5), (R - 3.5 * (pos + 1), 2.25), 6, expr)})
    return {"type": "panel", "size": [CELL_W, CELL_H], "offset": [x, y], "anchor_from": "top_left", "anchor_to": "top_left",
            "controls": ctl}


def hud_json():
    root_ctl = []
    gap = 182 - 2 * CELL_W                                # 18: room for the XP level number
    row_top, row_bottom = 0, CELL_H + 2
    root_ctl.append({"health": cell('health', 'H', 'left', 0, row_bottom,
                                    [('icon_health', has('Pn')), ('icon_health_poison', has('Pp')), ('icon_health_wither', has('Pw'))],
                                    '!h', 'health', number=True)})
    root_ctl.append({"food": cell('food', 'F', 'right', CELL_W + gap, row_bottom, [('icon_food', None)], '!f', 'food')})
    thirst = cell('thirst', 'T', 'left', 0, row_top, [('icon_thirst', None)], '!t', 'thirst')
    thirst["bindings"] = vis(hasnt('Txx'))
    sanity = cell('sanity', 'S', 'right', CELL_W + gap, row_top, [('icon_sanity', None)], '!s', 'sanity')
    sanity["bindings"] = vis(hasnt('Sxx'))
    root_ctl += [{"thirst": thirst}, {"sanity": sanity}]
    # armor badge, left of the health bar
    armor = {"type": "panel", "size": [19, CELL_H], "offset": [-21, row_bottom], "anchor_from": "top_left", "anchor_to": "top_left",
             "bindings": vis(has('Ay')),
             "controls": [{"plate": img('armor_plate', (19, CELL_H), (0, 0), 1)},
                          {"icon": img('icon_armor', (ICON, ICON), (0, 0), 3)}]}
    for dgt in range(10):
        if dgt:
            armor["controls"].append({f"t{dgt}": img(f'num_{dgt}', (3.5, 4.5), (10, 2.25), 4, has(f'B{dgt}'))})
        armor["controls"].append({f"o{dgt}": img(f'num_{dgt}', (3.5, 4.5), (13.5, 2.25), 4, has(f'C{dgt}'))})
    root_ctl.append({"armor": armor})

    root = {"type": "panel", "anchor_from": "bottom_middle", "anchor_to": "bottom_middle", "offset": [0, -29],
            "size": [182, 2 * CELL_H + 2], "layer": 30, "controls": root_ctl,
            "bindings": [{"binding_name": "#show_survival_ui", "binding_name_override": "#visible"}]}
    # the HUD's own visibility ("off" = hidden by the player / creative) lives on an inner panel so the
    # data keeper below never sits inside a hidden parent
    shown = {"type": "panel", "size": ["100%", "100%"], "controls": [{"hud_root": root}], "bindings": vis(hasnt('shud:off'))}
    data = {"type": "panel", "size": [0, 0], "bindings": [
        {"binding_name": "#hud_title_text_string"},
        {"binding_name": "#hud_title_text_string", "binding_name_override": P, "binding_condition": "visibility_changed"},
        {"binding_type": "view",
         "source_property_name": f"((not (#hud_title_text_string = {P})) and (not ((#hud_title_text_string - 'shud:') = #hud_title_text_string)))",
         "target_property_name": "#visible"}]}
    return {
        "namespace": "succubi_hud",
        "pulse_out": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.55, "from": 1.0, "to": 0.15, "next": "@succubi_hud.pulse_in"},
        "pulse_in": {"anim_type": "alpha", "easing": "in_out_sine", "duration": 0.55, "from": 0.15, "to": 1.0, "next": "@succubi_hud.pulse_out"},
        "hud_layer": {"type": "panel", "size": ["100%", "100%"], "controls": [{DATA: data}, {"succubi_hud_shown": shown}]},
    }


def vanilla_bottom_panels():
    """vanilla centered_gui_elements_at_bottom_middle(_touch) without hearts / armor / hunger,
    air bubbles and horse hearts moved up one row so they sit above the Succubi bars"""
    def panel(width, binding):
        right = width
        return {
            "type": "panel", "anchor_from": "bottom_middle", "anchor_to": "bottom_middle", "size": [width, 50],
            "controls": [
                {"horse_heart_rend_0@hud.horse_heart_renderer": {"offset": [right, -66], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                                 "bindings": [{"binding_name": "#creative_horse_hearts", "binding_name_override": "#visible"}]}},
                {"horse_heart_rend_1@hud.horse_heart_renderer": {"offset": [right, -60], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                                 "bindings": [{"binding_name": "#survival_horse_hearts", "binding_name_override": "#visible"}]}},
                {"bubbles_rend_0@hud.bubbles_renderer": {"offset": [right, -60], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                          "bindings": [{"binding_name": "#is_not_riding_bubbles", "binding_name_override": "#visible"}]}},
                {"bubbles_rend_1@hud.bubbles_renderer": {"offset": [right, -60], "anchor_from": "bottom_left", "anchor_to": "bottom_left",
                                                          "bindings": [{"binding_name": "#is_riding_bubbles", "binding_name_override": "#visible"}]}},
                {"exp_rend@hud.exp_progress_bar_and_hotbar": {}}],
            "bindings": [{"binding_name": binding, "binding_name_override": "#visible", "binding_type": "global"}]}
    return {"centered_gui_elements_at_bottom_middle": panel(180, "#hud_visible_centered"),
            "centered_gui_elements_at_bottom_middle_touch": panel(200, "#hud_visible_centered_touch")}


def hud_screen_core():
    d = {
        "namespace": "hud",
        "succubi_bg": {"type": "panel", "size": ["100%", "100%"], "controls": [
            {"succubi_gate": {"type": "panel", "size": ["100%", "100%"], "controls": [{"layer@succubi_hud.hud_layer": {}}],
                              "bindings": [{"binding_name": "#hud_visible", "binding_name_override": "#visible", "binding_type": "global"}]}}]},
        "hud_screen@common.base_screen": {"$screen_bg_content": "hud.succubi_bg"},
        # our data titles never show; any other /title still does
        "hud_title_text": {"bindings": [
            {"binding_name": "#hud_title_text_string", "binding_type": "global"},
            {"binding_type": "view", "source_property_name": "((#hud_title_text_string - 'shud:') = #hud_title_text_string)",
             "target_property_name": "#visible"}]},
        # hearts, hunger and armor are drawn by the Succubi HUD (textures are also blanked as a fallback)
        "heart_renderer": {"ignored": True},
        "hunger_renderer": {"ignored": True},
        "armor_renderer": {"ignored": True},
    }
    d.update(vanilla_bottom_panels())
    return d


def hud_screen_guns():
    """Aplok Guns' own HUD bits (off-screen player renderer for first-person gun animations, item cooldowns)"""
    return {
        "namespace": "hud",
        "cooldown_renderer": {"ignored": False},
        "succubi_guns_extra": {"type": "panel", "size": ["100%", "100%"], "controls": [{"hud_elements@hud_elements.hud_elements": {}}]},
        "hud_screen@common.base_screen": {"$additional_screen_content": "hud.succubi_guns_extra"},
    }


@step
def build_hud(out, ctx, log):
    rp = os.path.join(out, CORE_RP)
    d = os.path.join(rp, TEX)
    for f in os.listdir(d) if os.path.isdir(d) else []:
        os.remove(os.path.join(d, f))                  # old rings / pills
    draw_all(rp)
    wjson(os.path.join(rp, 'ui/succubi_hud.json'), hud_json())
    wjson(os.path.join(rp, 'ui/hud_screen.json'), hud_screen_core())
    defs = sorted(f'ui/{f}' for f in os.listdir(os.path.join(rp, 'ui')) if f.startswith('succubi_') and f.endswith('.json'))
    wjson(os.path.join(rp, 'ui/_ui_defs.json'), {"ui_defs": defs})
    # blank armor icons too (fallback if a client ignores "ignored")
    blank = Image.new('RGBA', (9, 9))
    for n in ('armor_empty', 'armor_half', 'armor_full'):
        blank.save(os.path.join(rp, f'textures/ui/{n}.png'))
    grp = os.path.join(out, GUNS_RP)
    wjson(os.path.join(grp, 'ui/hud_screen.json'), hud_screen_guns())
    wjson(os.path.join(grp, 'ui/_ui_defs.json'), {"ui_defs": ["ui/hud/hud_elements.json"]})
    log(f'HUD: {len(os.listdir(d))} textures, bars + armor badge + health number')
