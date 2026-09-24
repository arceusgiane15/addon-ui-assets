"""Render the Succubi HUD from the generated ui/succubi_hud.json for given payloads, over a game-like scene
with the vanilla hotbar, so the layout can be checked without the game.

    python3 preview_hud.py <out dir> <vanilla textures/ui dir> <png>"""
import json, os, re, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CORE_RP, rjson

G = 4          # screen pixels per GUI unit
W, H = 300, 120  # GUI units shown


def evaluate(expr, payload):
    e = expr
    e = re.sub(r"\(not \(\(#preserved_text - '([^']*)'\) = #preserved_text\)\)", lambda m: repr(m.group(1) in payload), e)
    e = re.sub(r"\(\(#preserved_text - '([^']*)'\) = #preserved_text\)", lambda m: repr(m.group(1) not in payload), e)
    e = e.replace('false', 'False').replace('true', 'True')
    return bool(eval(e))


def visible(ctl, payload):
    for b in ctl.get('bindings', []):
        if b.get('target_property_name') == '#visible' and b.get('source_control_name'):
            if not evaluate(b['source_property_name'], payload):
                return False
    return True


def draw(canvas, rp, ctl, x, y, payload):
    if not visible(ctl, payload):
        return
    w, h = ctl.get('size', [0, 0])
    if ctl.get('type') == 'image':
        tex = Image.open(os.path.join(rp, ctl['texture'] + '.png')).convert('RGBA')
        tex = tex.resize((max(1, round(w * G)), max(1, round(h * G))), Image.NEAREST)
        if 'alpha' in ctl:
            a = tex.getchannel('A').point(lambda v: int(v * 0.75))
            tex.putalpha(a)
        canvas.alpha_composite(tex, (round(x * G), round(y * G)))
    for c in ctl.get('controls', []):
        (name, body), = c.items()
        ox, oy = body.get('offset', [0, 0])
        draw(canvas, rp, body, x + ox, y + oy, payload)


def scene(vanilla_ui):
    im = Image.new('RGBA', (W * G, H * G))
    d = ImageDraw.Draw(im)
    for yy in range(H * G):             # sky -> grass
        t = yy / (H * G)
        c = (int(120 + 60 * t), int(170 + 40 * t), 235) if t < 0.55 else (86, 140, 58)
        d.line([(0, yy), (W * G, yy)], fill=c + (255,))
    for i in range(0, W * G, 24):
        d.rectangle([i, int(H * G * 0.55), i + 11, int(H * G * 0.55) + 6], fill=(104, 160, 70, 255))
    # vanilla hotbar + xp bar
    hb_x = W / 2 - 91
    hb_y = H - 22
    slot = Image.open(os.path.join(vanilla_ui, 'hotbar_0.png')).convert('RGBA')
    for i in range(9):
        s = slot.resize((20 * G, 22 * G), Image.NEAREST)
        im.alpha_composite(s, (int((hb_x + 1 + i * 20) * G), int(hb_y * G)))
    xe = Image.open(os.path.join(vanilla_ui, 'experiencebarempty.png')).convert('RGBA').resize((182 * G, 5 * G), Image.NEAREST)
    xf = Image.open(os.path.join(vanilla_ui, 'experiencebarfull.png')).convert('RGBA').resize((182 * G, 5 * G), Image.NEAREST)
    im.alpha_composite(xe, (int(hb_x * G), int((hb_y - 6) * G)))
    im.alpha_composite(xf.crop((0, 0, int(182 * G * 0.4), 5 * G)), (int(hb_x * G), int((hb_y - 6) * G)))
    return im


def render(out, vanilla_ui, payload):
    rp = os.path.join(out, CORE_RP)
    ui = rjson(os.path.join(rp, 'ui/succubi_hud.json'))
    im = scene(vanilla_ui)
    layer = ui['hud_layer']
    shown = next(c['succubi_hud_shown'] for c in layer['controls'] if 'succubi_hud_shown' in c)
    if not visible(shown, payload):
        return im
    root = shown['controls'][0]['hud_root']
    rw, rh = root['size']
    ox, oy = root['offset']
    x = W / 2 - rw / 2 + ox
    y = H - rh + oy
    draw(im, rp, root, x, y, payload)
    return im


if __name__ == '__main__':
    out, vui, target = sys.argv[1:4]
    payloads = [
        'shud:H17F18T15S16PnX0Y8Z6An',
        'shud:H04F05T03S04PpX0Y2Z0AyB0C8!h!f!t!s',
        'shud:H20F20TxxSxxPwX1Y4Z0AyB2C0',
    ]
    frames = [render(out, vui, p) for p in payloads]
    sheet = Image.new('RGBA', (W * G, H * G * len(frames)))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (0, i * H * G))
    sheet = sheet.crop((int((W / 2 - 120) * G), 0, int((W / 2 + 120) * G), H * G * len(frames)))
    sheet.save(target)
    print('saved', target)
