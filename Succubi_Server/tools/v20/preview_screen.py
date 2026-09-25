"""Whole-screen preview of the Succubi HUD screen effects (grey-out at low sanity, red aura at low health)
over a colourful stand-in for the game world.

    python3 preview_screen.py <out dir> <vanilla textures/ui dir> <png> [gif]"""
import math, os, random, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preview_hud as P
from common import CORE_RP, rjson

W, H = 400, 225          # GUI units (16:9)
G = 2


def world():
    rng = random.Random(3)
    im = Image.new('RGBA', (W * G, H * G))
    d = ImageDraw.Draw(im)
    for y in range(H * G):
        t = y / (H * G * 0.6)
        d.line([(0, y), (W * G, y)], fill=(int(90 + 90 * t), int(160 + 60 * t), 250, 255))
    d.ellipse([620, 50, 700, 130], fill=(255, 230, 120, 255))
    for cx, cy in ((120, 70), (330, 50), (520, 110)):
        for k in range(4):
            d.rectangle([cx + k * 22, cy - (k % 2) * 10, cx + k * 22 + 40, cy + 18], fill=(250, 250, 255, 255))
    ground = int(H * G * 0.58)
    for x in range(0, W * G, 16):
        h = ground + int(math.sin(x / 90) * 18)
        d.rectangle([x, h, x + 15, h + 8], fill=(98, 176, 60, 255))
        d.rectangle([x, h + 8, x + 15, H * G], fill=(134, 96, 64, 255))
        for yy in range(h + 16, H * G, 16):
            if rng.random() < 0.15:
                d.rectangle([x + 3, yy + 3, x + 9, yy + 9], fill=(110, 110, 116, 255))
    for tx in (90, 260, 780):                                   # trees
        base = ground + int(math.sin(tx / 90) * 18)
        d.rectangle([tx, base - 70, tx + 16, base], fill=(110, 76, 44, 255))
        d.rectangle([tx - 36, base - 130, tx + 52, base - 62], fill=(52, 140, 50, 255))
        d.rectangle([tx - 20, base - 150, tx + 36, base - 126], fill=(64, 160, 58, 255))
    hx, hb = 440, ground + int(math.sin(440 / 90) * 18)          # house
    d.rectangle([hx, hb - 90, hx + 150, hb], fill=(214, 190, 150, 255))
    d.polygon([(hx - 16, hb - 90), (hx + 75, hb - 150), (hx + 166, hb - 90)], fill=(200, 50, 50, 255))
    d.rectangle([hx + 60, hb - 50, hx + 90, hb], fill=(120, 80, 50, 255))
    d.rectangle([hx + 18, hb - 70, hx + 46, hb - 44], fill=(140, 200, 240, 255))
    for fx in range(20, W * G, 37):                              # flowers
        fy = ground + int(math.sin(fx / 90) * 18) - 6
        d.rectangle([fx, fy, fx + 5, fy + 5], fill=rng.choice([(240, 60, 60), (250, 220, 40), (170, 90, 230), (255, 140, 200)]) + (255,))
    # hotbar + xp bar
    vui = sys.argv[2]
    slot = Image.open(os.path.join(vui, 'hotbar_0.png')).convert('RGBA').resize((20 * G, 22 * G), Image.NEAREST)
    for i in range(9):
        im.alpha_composite(slot, (int((W / 2 - 90 + i * 20) * G), int((H - 22) * G)))
    xe = Image.open(os.path.join(vui, 'experiencebarempty.png')).convert('RGBA').resize((182 * G, 5 * G), Image.NEAREST)
    im.alpha_composite(xe, (int((W / 2 - 91) * G), int((H - 28) * G)))
    return im


def render(out, payload, t, base):
    rp = os.path.join(out, CORE_RP)
    ui = rjson(os.path.join(rp, 'ui/succubi_hud.json'))
    payload = P.with_stages(payload)
    im = base.copy()
    layer = ui['hud_layer']
    items = []
    old_g, old_w, old_h = P.G, P.W, P.H
    P.G, P.W, P.H = G, W, H
    try:
        for c in layer['controls']:
            (name, body), = c.items()
            if name == 'succubi_screen_fx':
                P.draw(items, rp, ui, body, 0, 0, W, H, payload, t)
            if name == 'succubi_hud_shown' and P.visible(body, payload):
                P.draw(items, rp, ui, body['controls'][0]['hud_root'], 0, 0, W, H, payload, t)
    finally:
        P.G, P.W, P.H = old_g, old_w, old_h
    for _, tile, pos in sorted(items, key=lambda i: i[0]):
        P.paste_clip(im, tile, pos) if pos[0] < 0 or pos[1] < 0 else im.alpha_composite(tile, pos)
    return im


def label(im, text):
    from art_ui import font
    d = ImageDraw.Draw(im)
    f = font(20, True)
    d.rounded_rectangle([10, 10, 22 + d.textlength(text, font=f), 42], radius=8, fill=(10, 5, 9, 210))
    d.text((16, 11), text, font=f, fill=(255, 220, 240))
    return im


def pay(h, s, extra=''):
    hp = h * 5
    return f'shud:H{h:02d}F16T15S{s:02d}PnX{hp // 100}Y{hp // 10 % 10}Z{hp % 10}An' + extra + ('Lh' if h <= 5 else '') + ('Ls' if s <= 6 else '')


SHOTS = [
    ('ปกติ', pay(18, 18)),
    ('สติ 50%: ฟิลเตอร์เทาเริ่มคลุมทั้งจอ', pay(18, 10)),
    ('สติ 25%: เทาหนัก ขอบจอมืดนิดๆ', pay(18, 5)),
    ('สติ 5%: เกือบขาวดำ เม็ดซ่าบางๆ', pay(18, 1)),
    ('เลือด 70%: ขอบแดงจางๆ เส้นเลือดนิดเดียว', pay(14, 18)),
    ('เลือด 50%: แดงขึ้น เส้นเลือดยาวขึ้น', pay(10, 18)),
    ('เลือด 25%: แดงเข้ม เส้นเลือดเยอะ', pay(5, 18)),
    ('เลือด 5%: แดงหนาเกือบทั้งจอ', pay(1, 18)),
]

if __name__ == '__main__':
    out, vui, target = sys.argv[1:4]
    base = world()
    if len(sys.argv) > 4 and sys.argv[4] == 'gif':
        frames, fps = [], 12
        seq = [(label, p, 0.8 if i == 0 else 1.6) for i, (label, p) in enumerate(SHOTS)]
        # a slow slide of sanity from 100 % to 0 first
        for i in range(48):
            s = max(0, 20 - i * 20 // 44)
            frames.append(label(render(out, pay(18, s), i / fps, base), f'สติค่อยๆ ลด: {s * 5}%'))
        for i in range(60):
            h = max(1, 20 - i * 19 // 52)
            frames.append(label(render(out, pay(h, 18), i / fps, base), f'เลือดค่อยๆ ลด: {h * 5}%'))
        for i in range(24):
            h = min(20, 1 + i)
            frames.append(label(render(out, pay(h, 18), i / fps, base), f'ฟื้นเลือด: {h * 5}%'))
        frames = [f.convert('RGB').resize((W * G // 1, H * G // 1)).quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
        frames[0].save(target, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=True)
        print('saved', target, len(frames))
    else:
        shots = [label(render(out, p, 0.12, base), l) for l, p in SHOTS]
        sw, sh = shots[0].size
        sheet = Image.new('RGBA', (sw * 2, sh * ((len(shots) + 1) // 2)))
        for i, s in enumerate(shots):
            sheet.alpha_composite(s, ((i % 2) * sw, (i // 2) * sh))
        sheet.save(target)
        print('saved', target)
