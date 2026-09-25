"""Render the Succubi HUD from the generated ui/succubi_hud.json, over a game-like scene with the vanilla
hotbar. Plays the JSON UI animations (alpha / offset / size chains, flip books), so the change and status
effects can be seen without the game.

    python3 preview_hud.py <out dir> <vanilla textures/ui dir> <png>      still frames of a few states
    python3 preview_hud.py <out dir> <vanilla textures/ui dir> <gif> gif  animated tour of every effect"""
import math, os, re, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CORE_RP, rjson

G = 4             # screen pixels per GUI unit
W, H = 240, 90    # GUI units shown
ANCH = {'top_left': (0, 0), 'top_middle': (0.5, 0), 'top_right': (1, 0), 'left_middle': (0, 0.5), 'center': (0.5, 0.5),
        'right_middle': (1, 0.5), 'bottom_left': (0, 1), 'bottom_middle': (0.5, 1), 'bottom_right': (1, 1)}
_cache = {}
STRICT = os.environ.get('HUD_STRICT') == '1'


def evaluate(expr, payload):
    e = re.sub(r"\(not \(\(#preserved_text - '([^']*)'\) = #preserved_text\)\)", lambda m: repr(m.group(1) in payload), expr)
    e = re.sub(r"\(\(#preserved_text - '([^']*)'\) = #preserved_text\)", lambda m: repr(m.group(1) not in payload), e)
    return bool(eval(e.replace('false', 'False').replace('true', 'True')))


def visible(ctl, payload):
    from validate import expression_risk
    for b in ctl.get('bindings', []):
        if b.get('target_property_name') == '#visible' and b.get('source_control_name'):
            if STRICT and expression_risk(b['source_property_name']):
                continue                      # like the game: a misread condition leaves the image showing
            if not evaluate(b['source_property_name'], payload):
                return False
    return True


EASE = {
    'linear': lambda t: t,
    'in_out_sine': lambda t: -(math.cos(math.pi * t) - 1) / 2,
    'out_quad': lambda t: 1 - (1 - t) ** 2,
    'out_back': lambda t: 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2,
}


def anim_value(ref, anims, t):
    """value of a looping anim chain at time t (alpha -> float, offset/size -> [x, y])"""
    name = ref.split('.')[-1]
    chain, seen = [], set()
    while name and name not in seen:
        seen.add(name)
        a = anims[name]
        chain.append(a)
        name = a.get('next', '').split('.')[-1] if a.get('next') else None
    total = sum(a['duration'] for a in chain)
    t = t % total if name else min(t, total)
    prev = next((a['to'] for a in reversed(chain) if 'to' in a), None)
    for a in chain:
        if t <= a['duration'] or a is chain[-1]:
            if a['anim_type'] == 'wait':
                return prev
            k = EASE.get(a.get('easing', 'linear'), EASE['linear'])(min(1, t / a['duration']))
            f, to = a['from'], a['to']
            if isinstance(f, list):
                return [f[i] + (to[i] - f[i]) * k for i in range(len(f))]
            return f + (to - f) * k
        t -= a['duration']
        if 'to' in a:
            prev = a['to']


def tex(rp, path):
    if path not in _cache:
        _cache[path] = Image.open(os.path.join(rp, path + '.png')).convert('RGBA')
    return _cache[path]


def draw(canvas, rp, anims, ctl, px_, py_, pw, ph, payload, t):
    if not visible(ctl, payload):
        return
    w, h = ctl.get('size', [pw, ph])
    w = pw if w == '100%' else w
    h = ph if h == '100%' else h
    off = list(ctl.get('offset', [0, 0]))
    anim_alpha = None
    for ref in ctl.get('anims', []):
        a = anims[ref.split('.')[-1]]
        if a['anim_type'] == 'offset':
            off = anim_value(ref, anims, t)
        if a['anim_type'] == 'size':
            w, h = anim_value(ref, anims, t)
        if a['anim_type'] == 'alpha':
            anim_alpha = anim_value(ref, anims, t)
    af, at = ANCH[ctl.get('anchor_from', 'center')], ANCH[ctl.get('anchor_to', 'center')]
    x = px_ + af[0] * pw - at[0] * w + off[0]
    y = py_ + af[1] * ph - at[1] * h + off[1]
    if ctl.get('type') == 'image':
        im = tex(rp, ctl['texture'])
        if 'uv_size' in ctl:
            uw, uh = ctl['uv_size']
            fb = anims[ctl['uv'].split('.')[-1]]
            frame = int(t * fb['fps']) % fb['frame_count']
            im = im.crop((frame * fb['frame_step'], 0, frame * fb['frame_step'] + uw, uh))
        dw, dh, dx, dy = w, h, 0, 0
        if ctl.get('keep_ratio', True):          # the game default: the texture keeps its shape, centred
            k = min(w / im.width, h / im.height)
            dw, dh = im.width * k, im.height * k
            dx, dy = (w - dw) / 2, (h - dh) / 2
        im = im.resize((max(1, round(dw * G)), max(1, round(dh * G))), Image.LANCZOS)
        if anim_alpha is not None or isinstance(ctl.get('alpha'), (str, int, float)):
            a = anim_alpha if anim_alpha is not None else ctl['alpha'] if not isinstance(ctl['alpha'], str) else anim_value(ctl['alpha'], anims, t)
            a = max(0.0, min(1.0, a))
            im = im.copy()
            im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
        canvas.append((ctl.get('layer', 0), im, (round((x + dx) * G), round((y + dy) * G))))
    for c in ctl.get('controls', []):
        (_, body), = c.items()
        draw(canvas, rp, anims, body, x, y, w, h, payload, t)


def scene(vanilla_ui):
    im = Image.new('RGBA', (W * G, H * G))
    d = ImageDraw.Draw(im)
    for yy in range(H * G):
        tt = yy / (H * G)
        c = (int(120 + 60 * tt), int(170 + 40 * tt), 235) if tt < 0.45 else (86, 140, 58)
        d.line([(0, yy), (W * G, yy)], fill=c + (255,))
    hb_x, hb_y = W / 2 - 91, H - 22
    slot = Image.open(os.path.join(vanilla_ui, 'hotbar_0.png')).convert('RGBA').resize((20 * G, 22 * G), Image.NEAREST)
    for i in range(9):
        im.alpha_composite(slot, (int((hb_x + 1 + i * 20) * G), int(hb_y * G)))
    xe = Image.open(os.path.join(vanilla_ui, 'experiencebarempty.png')).convert('RGBA').resize((182 * G, 5 * G), Image.NEAREST)
    xf = Image.open(os.path.join(vanilla_ui, 'experiencebarfull.png')).convert('RGBA').resize((182 * G, 5 * G), Image.NEAREST)
    im.alpha_composite(xe, (int(hb_x * G), int((hb_y - 6) * G)))
    im.alpha_composite(xf.crop((0, 0, int(182 * G * 0.4), 5 * G)), (int(hb_x * G), int((hb_y - 6) * G)))
    return im


def stage(r):
    return 4 if r >= 0.75 else 3 if r >= 0.5 else 2 if r >= 0.3 else 1 if r >= 0.15 else 0


def with_stages(payload):
    """add the tokens hud.js would send that a preview payload leaves out: icon stages, % numbers, at-rest flags"""
    if payload.endswith('off'):
        return payload
    for letter, flag in (('H', 'h'), ('F', 'f'), ('T', 't'), ('S', 's')):
        m = re.search(letter + r'(\d\d)', payload)
        if not m:
            continue
        v = int(m.group(1))
        if f'V{flag}' not in payload:
            payload += f'V{flag}{stage(v / 20)}'
        if flag != 'h' and f'O{flag}' not in payload:
            p = v * 5
            payload += f'O{flag}{p // 100}M{flag}{p // 10 % 10}K{flag}{p % 10}'
        if f'D{flag}' not in payload and f'U{flag}' not in payload and f'I{flag}' not in payload:
            payload += f'I{flag}'
    return payload


def render(out, vanilla_ui, payload, t=0.0, bg=None):
    payload = with_stages(payload)
    rp = os.path.join(out, CORE_RP)
    ui = rjson(os.path.join(rp, 'ui/succubi_hud.json'))
    im = (bg or scene(vanilla_ui)).copy()
    layer = ui['hud_layer']
    shown = next(c['succubi_hud_shown'] for c in layer['controls'] if 'succubi_hud_shown' in c)
    if not visible(shown, payload):
        return im
    items = []
    draw(items, rp, ui, shown['controls'][0]['hud_root'], 0, 0, W, H, payload, t)
    for _, tile, pos in sorted(items, key=lambda i: i[0]):
        im.alpha_composite(tile, pos) if pos[0] >= 0 and pos[1] >= 0 else paste_clip(im, tile, pos)
    return im


def paste_clip(im, tile, pos):
    x, y = pos
    cx, cy = max(0, -x), max(0, -y)
    im.alpha_composite(tile.crop((cx, cy, tile.width, tile.height)), (x + cx, y + cy))


BASE = 'shud:H17F18T15S16PnX0Y8Z6AnVh4Vf4Vt3Vs4'
STAGES = [('shud:H{h:02d}F{h:02d}T{h:02d}S{h:02d}PnX{x}Y{y}Z{z}AnVh{v}Vf{v}Vt{v}Vs{v}' + ('LhLfLtLs' if v <= 1 else '')).format(
    h=h, v=v, x=(h * 5) // 100, y=(h * 5) // 10 % 10, z=(h * 5) % 10) for h, v in ((20, 4), (13, 3), (8, 2), (4, 1), (2, 0))]
STATES = [
    ('ค่าลดลงเรื่อยๆ: ไอคอนเปลี่ยนรูปตามระดับ', STAGES),
    ('ไอคอนเปลี่ยนตามค่า: เต็ม', STAGES[0]),
    ('เหลือครึ่ง: หัวใจร้าว น่องไก่ถูกกัด น้ำพร่อง สมองเริ่มเครียด', STAGES[1]),
    ('ต่ำ: หัวใจแตกร้าว เหลือเนื้อน้อย น้ำครึ่งหยด สมองมีรอยเย็บ', STAGES[2]),
    ('วิกฤต: หัวใจฉีก เลือดหยด / ท้องร้อง / หยดน้ำแตก มีไอร้อน / สมองมีตา มือเงาคืบมา', STAGES[3]),
    ('ใกล้หมด: หัวใจแหลก / เหลือกระดูก แมลงวันตอม / แห้งเป็นฝุ่น / สติหลุด', STAGES[4]),
    ('ปกติ', BASE),
    ('โดนตี: แดงกะพริบ หัวใจสั่น แถบจางๆ บอกเลือดที่เสียไป', 'shud:H11F18T15S16PnX0Y5Z4AyB0C8DhG17'),
    ('ฟื้นเลือด (Regeneration): ประกายวิ่งรอบหัวใจ', 'shud:H14F18T15S16PnX0Y7Z0AnUhEr'),
    ('กินอาหาร: เรืองแสง ไอคอนเด้ง', 'shud:H17F20T15S16PnX0Y8Z6AnUf'),
    ('ดื่มน้ำ', 'shud:H17F18T20S16PnX0Y8Z6AnUt'),
    ('ติดพิษ: วงเขียว มีฟองลอย', 'shud:H12F18T15S16PpX0Y6Z0An'),
    ('Wither: วงดำ มีควัน', 'shud:H09F18T15S16PwX0Y4Z5An'),
    ('ไฟไหม้ตัว', 'shud:H13F18T15S16PnX0Y6Z5AnEfDh'),
    ('Absorption: วงทองรอบหัวใจ', 'shud:H20F18T15S16PnX1Y0Z0AnEa'),
    ('ติดหิว (Hunger): วงอาหารเขียวคล้ำ', 'shud:H17F09T15S16PnX0Y8Z6AnQhDf'),
    ('เจอเรื่องแปลก: สติลดวูบ', 'shud:H17F18T15S07PnX0Y8Z6AnDs'),
    ('ใกล้ตาย / หิว / คอแห้ง / สติหลุด', 'shud:H03F04T03S02PnX0Y1Z5AnLhLfLtLs'),
]


def caption(im, text):
    from art_ui import font
    d = ImageDraw.Draw(im)
    f = font(22, True)
    d.rounded_rectangle([12, 10, 24 + d.textlength(text, font=f), 46], radius=8, fill=(10, 5, 9, 200))
    d.text((18, 12), text, font=f, fill=(255, 220, 240))
    return im


def crop(im):
    return im.crop((int((W / 2 - 100) * G), int((H - 80) * G), int((W / 2 + 100) * G), H * G))


if __name__ == '__main__':
    out, vui, target = sys.argv[1:4]
    bg = scene(vui)
    if len(sys.argv) > 4 and sys.argv[4] == 'gif':
        frames = []
        fps, per = 12, 1.6
        for label, payload in STATES:
            seq = payload if isinstance(payload, list) else [payload]
            for i in range(int(per * fps * (2.5 if len(seq) > 1 else 1))):
                t = i / fps
                cur = seq[min(len(seq) - 1, int(i / (per * fps * 2.5) * len(seq)))]
                frames.append(caption(crop(render(out, vui, cur, t, bg)), label).convert('RGB').quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        frames[0].save(target, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=True)
        print('saved', target, len(frames), 'frames')
    else:
        shots = [caption(crop(render(out, vui, p, 0.1, bg)), label) for label, p in STATES if not isinstance(p, list)]
        cols = 3
        w, h = shots[0].size
        sheet = Image.new('RGBA', (w * cols, h * math.ceil(len(shots) / cols)))
        for i, s in enumerate(shots):
            sheet.alpha_composite(s, ((i % cols) * w, (i // cols) * h))
        sheet.save(target)
        print('saved', target)
