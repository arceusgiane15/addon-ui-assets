"""v1.0.16: 40 more strange events, book stall, amulets (wallet button), blood moon, Rule of Horror kit."""
import json, os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import boxkit, shop_art
from build_food import wjson
from build_scripts import edit
import build_v14
import data_v16  # registers books / amulets / stalls into data_extra + stands (must be imported before the build runs)
from data_v16 import BOOKS, PAGES, AMULETS, HORROR_PROPS, wand_icon, bell_icon
from v16_events import HOOKS_JS, NEW_EVENTS_JS, HELPERS_JS, NEW_NAMES
from v16_js import AMULETS_JS, BOOKS_JS, BLOODMOON_JS
from v16_horror import HORROR_JS

PAPER_FLAG, AMULET_FLAG = "§0§9§5§1", "§0§9§5§2"
AMULET_THEME = dict(base=(90, 20, 24), dark=(50, 10, 12), accent=(232, 186, 60), glass=(26, 10, 10), cell=(60, 22, 24))

NEWS = [
    "ด่วน! พบเงาดำยืนมองชาวบ้านกลางทุ่ง ตำรวจยังไม่พบเบาะแส",
    "ถังไก่ทอดยายน้อยขายหมดเกลี้ยงตั้งแต่เช้า ลูกค้าต่อคิวยาวถึงร้านยา",
    "{who} ถูกลือว่าเห็นรูปปั้นขยับเอง เจ้าตัวปฏิเสธ 'ผมไม่ได้มองมันเลย'",
    "หมอเตือน: สติต่ำอันตราย ควรอ่านหนังสือ กินของอร่อย และนอนให้พอ",
    "ร้านน้ำชาฮารุโตะยืนยัน 'เพลงในร้านไม่ได้เปิดเองตอนตีสาม'",
    "นักวิชาการชี้ คืนพระจันทร์เลือดมาเฉลี่ยสัปดาห์ละครั้ง แนะนำให้อยู่เป็นกลุ่ม",
    "{who} ซื้อเครื่องรางนางกวักไป ร้านค้าทั่วเซิร์ฟบ่นขายได้กำไรน้อยลง",
    "พบป้ายประกาศกฎประหลาดหน้าอาคารร้าง เขียนว่า 'ห้ามวิ่ง'",
    "ตลาดนัดสัปดาห์นี้ ราคาเกลือแร่ ORS ยังคงที่ 8 บาท",
    "ผลสำรวจ: ชาวเซิร์ฟ 9 ใน 10 คนเคยได้ยินเสียงเคาะประตูทั้งที่ไม่มีใคร",
    "{who} ได้รับรางวัลนักอ่านดีเด่นประจำเดือน (ข่าวลือ)",
    "ช่างตัดสินใจไม่ซ่อมประตูบ้านร้าง 'มันเปิดเองอยู่แล้ว'",
    "ราคาข้าวกะเพราไข่ดาวในร้านสะดวกซื้อยังคุ้มที่สุดในย่าน",
    "มีผู้พบเห็นค้างคาวบินออกมาจากความมืดเป็นฝูง ทั้งที่ไม่มีถ้ำ",
]


def js_obj(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- scripts
def scripts(bp, log):
    sd = f'{bp}/scripts/succubi'
    open(f'{sd}/hooks.js', 'w', encoding='utf-8').write(HOOKS_JS)

    s = f'{sd}/sanity.js'
    edit(s, 'import { enabled } from "./settings_store.js";\n', 'import { enabled } from "./settings_store.js";\nimport { HOOKS, product, anyTrue } from "./hooks.js";\n')
    edit(s, "const EVENTS = [\n", HELPERS_JS + "\nconst EVENTS = [\n")
    edit(s, '  { id: "zombie", loss: 5, run: (p) => sound(p, "mob.zombie.say", ahead(p, -2), 1, 0.7) }\n];',
         '  { id: "zombie", loss: 5, run: (p) => sound(p, "mob.zombie.say", ahead(p, -2), 1, 0.7) },' + NEW_EVENTS_JS.rstrip().rstrip(',') + "\n];")
    edit(s, 'const SHARED = ["thunder", "red_fog", "bells"];', 'const SHARED = ["thunder", "red_fog", "bells", "midnight_bells", "white_fog", "shadow_circle", "wither_spawn"];')
    edit(s, "export const EVENT_NAMES = {\n", "export const EVENT_NAMES = {\n" + "".join(f'  {k}: "{v}",\n' for k, v in NEW_NAMES.items()))
    edit(s, "  addSanity(player, -ev.loss);", "  addSanity(player, -ev.loss * product(HOOKS.eventLoss, player));")
    edit(s, '  const left = typeof next === "number" ? next - 1 : nextDelay();\n  if (left <= 0) {\n    runEvent(player);',
         '  const left = typeof next === "number" ? next - product(HOOKS.eventRate, player) : nextDelay();\n  if (left <= 0) {\n    if (!anyTrue(HOOKS.eventBlock, player)) runEvent(player);')

    amulets = {a['key'].replace('amulet_', ''): {"id": f"succubi:{a['key']}", "name": a['name'], "short": a['short'], "effect": a['effect']} for a in AMULETS}
    open(f'{sd}/amulets.js', 'w', encoding='utf-8').write(AMULETS_JS.replace("__DATA__", js_obj(amulets)))
    books = {f"succubi:{b['key']}": {"key": b['key'], "name": b['name'], "sanity": b['sanity'], "cooldown": b['cooldown'],
                                     "consumed": b['consumed'], "special": b.get('special', ''), "pages": PAGES.get(b['key'], [])} for b in BOOKS}
    open(f'{sd}/books.js', 'w', encoding='utf-8').write(BOOKS_JS.replace("__DATA__", js_obj(books)).replace("__NEWS__", js_obj(NEWS)))
    open(f'{sd}/bloodmoon.js', 'w', encoding='utf-8').write(BLOODMOON_JS.replace("addSanity(p, -0.08)", "addSanity(p, -0.05)"))
    open(f'{sd}/horror.js', 'w', encoding='utf-8').write(HORROR_JS)

    # settings: new switches + blood moon now
    st = f'{sd}/settings_store.js'
    edit(st, 'const KEYS = { sanity: "succubi:cfg_sanity", thirst: "succubi:cfg_thirst", events: "succubi:cfg_events" };',
         'const KEYS = { sanity: "succubi:cfg_sanity", thirst: "succubi:cfg_thirst", events: "succubi:cfg_events", rules: "succubi:cfg_rules", bloodmoon: "succubi:cfg_bloodmoon" };')
    se = f'{sd}/settings.js'
    edit(se, 'import { setThirst, getThirst, THIRST_MAX } from "./thirst.js";\n',
         'import { setThirst, getThirst, THIRST_MAX } from "./thirst.js";\nimport { isBloodMoon, startBloodMoon, endBloodMoon } from "./bloodmoon.js";\n')
    edit(se, '    ["events", `§lเหตุการณ์ผิดปกติ: ${onOff(enabled("events"))}`]\n  ];',
         '    ["events", `§lเหตุการณ์ผิดปกติ: ${onOff(enabled("events"))}`],\n'
         '    ["rules", `§lอุปกรณ์กฎสยอง: ${onOff(enabled("rules"))}`],\n'
         '    ["bloodmoon", `§lคืนพระจันทร์เลือด (สุ่ม): ${onOff(enabled("bloodmoon"))}`]\n  ];')
    edit(se, '  form.button("§lเติมน้ำของฉันให้เต็ม");\n  form.button("§7ปิด");',
         '  form.button("§lเติมน้ำของฉันให้เต็ม");\n  form.button(isBloodMoon() ? "§l§cหยุดคืนพระจันทร์เลือด" : "§l§4เริ่มคืนพระจันทร์เลือดตอนนี้\\n§7(เปลี่ยนเวลาเป็นกลางคืน)");\n  form.button("§7ปิด");')
    edit(se, '    player.sendMessage("§b[ตั้งค่า] เติมน้ำเต็มแล้ว");\n    return openSettings(player);\n  }\n}',
         '    player.sendMessage("§b[ตั้งค่า] เติมน้ำเต็มแล้ว");\n    return openSettings(player);\n  }\n'
         '  if (i === rows.length + 3) {\n    if (isBloodMoon()) endBloodMoon();\n    else startBloodMoon(true);\n  }\n}')

    # wallet: amulet button
    m = f'{sd}/money.js'
    edit(m, 'import { getBalance, setBalance, formatBaht } from "./economy.js";\n',
         'import { getBalance, setBalance, formatBaht } from "./economy.js";\nimport { openAmulets } from "./amulets.js";\n')
    edit(m, '    .button("§lฝากเงิน", "textures/ui/succubi_wallet/btn_deposit")\n    .button("§lถอนเงิน", "textures/ui/succubi_wallet/btn_withdraw")\n    .button("§lปิด", "textures/ui/succubi_wallet/btn_close");',
         '    .button("§lฝากเงิน", "textures/ui/succubi_wallet/btn_deposit_s")\n    .button("§lถอนเงิน", "textures/ui/succubi_wallet/btn_withdraw_s")\n'
         '    .button("§lเครื่องราง", "textures/ui/succubi_wallet/btn_amulet_s")\n    .button("§lปิด", "textures/ui/succubi_wallet/btn_close_s");')
    edit(m, "  if (response.selection === 1) return openWithdraw(player);\n}",
         "  if (response.selection === 1) return openWithdraw(player);\n  if (response.selection === 2) return openAmulets(player);\n}")

    # shops: Nang Kwak discount
    v = f'{sd}/vending.js'
    edit(v, 'import { SHOPS, FACE_ON_PLACE } from "./shops.js";\n', 'import { SHOPS, FACE_ON_PLACE } from "./shops.js";\nimport { priceFor } from "./amulets.js";\n')
    edit(v, "  const credit = getCredit(player);\n  if (credit < product.price) return { ok: false, need: product.price - credit };\n  setCredit(player, credit - product.price);",
         "  const credit = getCredit(player);\n  const price = priceFor(player, product);\n  if (credit < price) return { ok: false, need: price - credit };\n  setCredit(player, credit - price);")
    edit(v, "    const affordable = credit >= p.price;", "    const price = priceFor(player, p);\n    const affordable = credit >= price;")
    edit(v, '${affordable ? "§e§l" : "§8"}${p.price}.-`', '${affordable ? "§e§l" : "§8"}${price}.-`')
    edit(v, '      : `${affordable ? "§l" : "§7"}${p.price}.-`;', '      : `${affordable ? "§l" : "§7"}${price}.-`;')

    mj = f'{bp}/scripts/main.js'
    edit(mj, 'import { initSettings } from "./succubi/settings.js";\n',
         'import { initSettings } from "./succubi/settings.js";\nimport { initAmulets } from "./succubi/amulets.js";\nimport { initBooks } from "./succubi/books.js";\n'
         'import { initBloodMoon } from "./succubi/bloodmoon.js";\nimport { initHorror } from "./succubi/horror.js";\n')
    edit(mj, "initSettings();\n", "initSettings();\ninitAmulets();\ninitBooks();\ninitBloodMoon();\ninitHorror();\n")
    log('v1.0.16 scripts')


# ---------------------------------------------------------------- UI
def paper_texture(w, h):
    rng = np.random.default_rng(7)
    base = np.zeros((h, w, 4), np.uint8)
    y, x = np.mgrid[0:h, 0:w]
    tone = 232 - 18 * ((x - w / 2) ** 2 / (w / 2) ** 2 + (y - h / 2) ** 2 / (h / 2) ** 2) + rng.normal(0, 3, (h, w))
    base[..., 0] = np.clip(tone, 0, 255); base[..., 1] = np.clip(tone * 0.93, 0, 255); base[..., 2] = np.clip(tone * 0.78, 0, 255); base[..., 3] = 255
    im = Image.fromarray(base, 'RGBA')
    d = ImageDraw.Draw(im)
    for yy in range(70, h - 60, 30):   # faint ruled lines
        d.line([(30, yy), (w - 30, yy)], fill=(200, 180, 150, 255), width=1)
    for (cx, cy, r) in ((w * 0.9, h * 0.13, 30), (w * 0.08, h * 0.86, 24)):   # stains (kept off the text)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(180, 140, 100, 160), width=5)
    # torn edge mask
    mask = Image.new('L', (w, h), 0); md = ImageDraw.Draw(mask)
    pts = []
    for i in range(41):
        pts.append((w * i / 40, 6 + rng.uniform(0, 8)))
    for i in range(41):
        pts.append((w - 6 - rng.uniform(0, 8), h * i / 40))
    for i in range(40, -1, -1):
        pts.append((w * i / 40, h - 6 - rng.uniform(0, 8)))
    for i in range(40, -1, -1):
        pts.append((6 + rng.uniform(0, 8), h * i / 40))
    md.polygon(pts, fill=255)
    im.putalpha(mask.filter(ImageFilter.GaussianBlur(1.2)))
    shadow = Image.new('RGBA', (w, h), (0, 0, 0, 0)); shadow.putalpha(mask.point(lambda v: int(v * 0.5)).filter(ImageFilter.GaussianBlur(6)))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); out.alpha_composite(shadow, (4, 5)); out.alpha_composite(im)
    return out


def paper_button(w, h, fill, edge, glyph):
    S = 3
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([2 * S, 2 * S, (w - 2) * S, (h - 3) * S], radius=10 * S, fill=fill + (255,), outline=edge + (255,), width=2 * S)
    d.rounded_rectangle([7 * S, 10 * S, 33 * S, (h - 11) * S], radius=6 * S, fill=edge + (255,))
    cx, cy = 20 * S, (h / 2 - 0.5) * S
    if glyph == 'next':
        d.polygon([(cx - 5 * S, cy - 7 * S), (cx + 7 * S, cy), (cx - 5 * S, cy + 7 * S)], fill=fill + (255,))
    elif glyph == 'done':
        d.line([(cx - 7 * S, cy), (cx - 2 * S, cy + 6 * S), (cx + 8 * S, cy - 7 * S)], fill=fill + (255,), width=3 * S)
    else:
        d.line([(cx - 6 * S, cy - 6 * S), (cx + 6 * S, cy + 6 * S)], fill=fill + (255,), width=3 * S)
        d.line([(cx - 6 * S, cy + 6 * S), (cx + 6 * S, cy - 6 * S)], fill=fill + (255,), width=3 * S)
    return im.resize((w, h), Image.LANCZOS)


def paper_ui(rp):
    tex = f'{rp}/textures/ui/succubi_paper'
    os.makedirs(tex, exist_ok=True)
    paper_texture(600, 400).save(f'{tex}/paper.png')
    paper_button(134, 56, (236, 222, 190), (120, 84, 50), 'next').save(f'{tex}/btn_next.png')
    paper_button(134, 56, (214, 236, 200), (60, 110, 60), 'done').save(f'{tex}/btn_done.png')
    paper_button(134, 56, (240, 206, 196), (150, 50, 40), 'close').save(f'{tex}/btn_close.png')
    lab = {"type": "label", "text": "#form_button_text", "color": [0.22, 0.13, 0.06], "shadow": False, "localize": False, "layer": 3,
           "anchor_from": "left_middle", "anchor_to": "left_middle", "offset": [21, 0], "size": ["100% - 23px", "default"], "font_scale_factor": 0.8,
           "bindings": [{"binding_name": "#form_button_text", "binding_type": "collection", "binding_collection_name": "form_buttons"}]}
    state = lambda overlay, dy: {"type": "panel", "size": ["100%", "100%"], "offset": [0, dy], "controls":
                                 [{"art@succubi_vending.vs_art": {}}, {"label@succubi_paper.pp_label": {}}] +
                                 ([{"overlay": {"type": "image", "texture": overlay, "size": ["100%", "100%"], "layer": 2}}] if overlay else [])}
    ui = {"namespace": "succubi_paper",
          "pp_label": lab, "pp_default": state(None, 0), "pp_hover": state("textures/ui/succubi_wallet/amt_hover", 0),
          "pp_pressed": state("textures/ui/succubi_wallet/amt_pressed", 1),
          "cell": {"type": "panel", "size": [71, 30], "controls": [{"button@common.button": {
              "size": [67, 28], "$pressed_button_name": "button.form_button_click",
              "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
              "controls": [{"default@succubi_paper.pp_default": {}}, {"hover@succubi_paper.pp_hover": {}}, {"pressed@succubi_paper.pp_pressed": {}}]}}]},
          "paper_panel": {"type": "panel", "size": [300, 200], "layer": 2, "controls": [
              {"bg": {"type": "image", "texture": "textures/ui/succubi_paper/paper", "size": ["100%", "100%"], "layer": 1}},
              {"title": {"type": "label", "text": "#title_text", "color": [0.5, 0.08, 0.06], "localize": False, "shadow": False,
                         "anchor_from": "top_middle", "anchor_to": "top_middle", "offset": [0, 12], "layer": 5, "bindings": [{"binding_name": "#title_text"}]}},
              {"body": {"type": "label", "text": "#form_text", "color": [0.2, 0.12, 0.06], "localize": False, "shadow": False,
                        "anchor_from": "top_left", "anchor_to": "top_left", "offset": [20, 30], "size": [260, "default"], "layer": 5,
                        "bindings": [{"binding_name": "#form_text"}]}},
              {"slots": {"type": "grid", "anchor_from": "bottom_right", "anchor_to": "bottom_right", "offset": [-14, -12], "size": [142, 30],
                         "grid_dimensions": [2, 1], "grid_item_template": "succubi_paper.cell", "collection_name": "form_buttons", "layer": 5}}]}}
    wjson(f'{rp}/ui/succubi_paper.json', ui)
    defs = json.load(open(f'{rp}/ui/_ui_defs.json'))
    if 'ui/succubi_paper.json' not in defs['ui_defs']:
        defs['ui_defs'].append('ui/succubi_paper.json')
    wjson(f'{rp}/ui/_ui_defs.json', defs)


def amulet_ui(rp):
    d = f'{rp}/textures/ui/succubi_shops/'
    card_w = (build_v14.CELL_W - 4) * 2
    for a in AMULETS:
        k = a['key'].replace('amulet_', '')
        shop_art.card(AMULET_THEME, a['icon'](), W=card_w).save(f'{d}p_amuletui_{k}.png')
    empty = Image.new('RGBA', (64, 64), (0, 0, 0, 0)); ed = ImageDraw.Draw(empty)
    ed.rounded_rectangle([8, 8, 56, 56], radius=8, outline=(232, 186, 60, 200), width=3)
    ed.line([(32, 20), (32, 44)], fill=(232, 186, 60, 220), width=4); ed.line([(20, 32), (44, 32)], fill=(232, 186, 60, 220), width=4)
    shop_art.card(AMULET_THEME, empty, W=card_w).save(f'{d}p_amuletui_empty.png')
    shop_art.widen(Image.open(f'{rp}/textures/ui/succubi_wallet/amt_back.png'), card_w).save(f'{d}amt_back.png')
    s = dict(key='amuletui', title='เครื่องราง', theme=AMULET_THEME, flag=AMULET_FLAG)
    shop_art.background('amuletui', AMULET_THEME, AMULETS[0]['icon'](), rows=5, W=build_v14.UI_W * 2).save(f'{d}bg_amuletui.png', optimize=True)
    ui = json.load(open(f'{rp}/ui/succubi_shops.json'))
    ui['amuletui_panel'] = build_v14.panel(s)
    wjson(f'{rp}/ui/succubi_shops.json', ui)


def wallet_ui(rp):
    w = f'{rp}/textures/ui/succubi_wallet/'

    def narrow(img, W=114):
        img = img.convert('RGBA'); iw, h = img.size
        left, right = img.crop((0, 0, 52, h)), img.crop((iw - 14, 0, iw, h))
        mid = img.crop((52, 0, iw - 14, h)).resize((W - 66, h), Image.LANCZOS)
        out = Image.new('RGBA', (W, h), (0, 0, 0, 0)); out.paste(left, (0, 0)); out.paste(mid, (52, 0)); out.paste(right, (W - 14, 0))
        return out
    for n in ('btn_deposit', 'btn_withdraw', 'btn_close'):
        narrow(Image.open(w + n + '.png')).save(w + n + '_s.png')
    # amulet button: the deposit button recoloured to temple red + an amulet in the icon box
    base = Image.open(w + 'btn_deposit.png').convert('RGBA')
    a = np.asarray(base).astype(float)
    g = a[..., 1] > a[..., 0] + 20
    a[g, 0], a[g, 1], a[g, 2] = a[g, 1] * 0.95, a[g, 1] * 0.35, a[g, 1] * 0.3
    red = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    ic = AMULETS[0]['icon']().resize((30, 30), Image.LANCZOS)
    ImageDraw.Draw(red).rounded_rectangle([13, 9, 45, 41], radius=6, fill=(30, 22, 22, 255))   # cover the cash icon
    red.alpha_composite(ic, (14, 10))
    narrow(red).save(w + 'btn_amulet_s.png')
    p = f'{rp}/ui/succubi_wallet.json'
    ui = json.load(open(p))
    btn = ui['wallet_button']
    btn['size'] = [60, 30]
    btn['controls'][0]['button@common.button']['size'] = [57, 26]
    ui['face_label']['offset'] = [24, -1]
    ui['face_label']['font_scale_factor'] = 0.85
    wjson(p, ui)


def server_form(rp):
    p = f'{rp}/ui/server_form.json'
    sf = json.load(open(p))
    controls = sf['long_form']['controls']
    default = controls[0]['long_form@common_dialogs.main_panel_no_buttons']['bindings'][1]
    names = {list(c)[0] for c in controls}
    for flag, name in ((PAPER_FLAG, 'succubi_paper@succubi_paper.paper_panel'), (AMULET_FLAG, 'succubi_amulets@succubi_shops.amuletui_panel')):
        if flag not in default['source_property_name']:
            default['source_property_name'] = default['source_property_name'][:-1] + f" and ((#title_text - '{flag}') = #title_text))"
        if name not in names:
            controls.append({name: {"bindings": [{"binding_name": "#title_text"},
                                                 {"binding_type": "view", "source_property_name": f"(not ((#title_text - '{flag}') = #title_text))",
                                                  "target_property_name": "#visible"}]}})
    # every Succubi skin flag starts with the invisible codes §0§9: the plain form shows only when the title has none
    default['source_property_name'] = "((#title_text - '§0§9') = #title_text)"
    wjson(p, sf)


# ---------------------------------------------------------------- horror props + items
def prop_entity(ident, st):
    player = {"test": "is_family", "subject": "other", "value": "player"}
    return {"format_version": "1.20.50", "minecraft:entity": {
        "description": {"identifier": ident, "is_spawnable": False, "is_summonable": True, "is_experimental": False},
        "components": {
            "minecraft:type_family": {"family": ["succubi_horror", "inanimate"]},
            "minecraft:collision_box": {"width": st['collision'][0], "height": st['collision'][1]},
            "minecraft:physics": {"has_gravity": True, "has_collision": True},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:knockback_resistance": {"value": 1.0},
            "minecraft:health": {"value": 100, "max": 100},
            "minecraft:damage_sensor": {"triggers": {"cause": "all", "deals_damage": False}},
            "minecraft:fire_immune": True, "minecraft:persistent": {},
            "minecraft:interact": {"interactions": [
                {"on_interact": {"filters": {"all_of": [player, {"test": "is_sneaking", "subject": "other", "value": True}]}, "event": "succubi:prop_pickup", "target": "self"},
                 "interact_text": "action.interact.succubi_pickup", "swing": True},
                {"on_interact": {"filters": {"all_of": [player, {"test": "is_sneaking", "subject": "other", "value": False}]}, "event": "succubi:prop_use", "target": "self"},
                 "interact_text": "action.interact.succubi_use", "swing": True}]}},
        "events": {"succubi:prop_use": {}, "succubi:prop_pickup": {}}}}


def horror_props(bp, rp, item_tex):
    for ident, st in HORROR_PROPS.items():
        short = ident.split(':')[1]
        parts = st['model']()
        cubes, atlas, size = boxkit.build(parts, ppu=8)
        atlas.save(f'{rp}/textures/entity/succubi_shops/{short}.png')
        wjson(f'{rp}/models/entity/succubi_shops/{short}.geo.json', {"format_version": "1.16.0", "minecraft:geometry": [{
            "description": {"identifier": f"geometry.{short}", "texture_width": size[0], "texture_height": size[1],
                            "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
            "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": cubes}]}]})
        wjson(f'{rp}/entity/succubi_shops/{short}.entity.json', {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
            "identifier": ident, "materials": {"default": "entity_alphatest"}, "textures": {"default": f"textures/entity/succubi_shops/{short}"},
            "geometry": {"default": f"geometry.{short}"}, "render_controllers": ["controller.render.succubi_money"], "enable_attachables": False}}})
        wjson(f'{bp}/entities/succubi_shops/{short}.json', prop_entity(ident, st))
        wjson(f'{bp}/items/succubi/{short}_placer.json', {"format_version": "1.21.0", "minecraft:item": {
            "description": {"identifier": f"{ident}_placer", "menu_category": {"category": "equipment"}},
            "components": {"minecraft:display_name": {"value": f"item.{ident}_placer.name"}, "minecraft:icon": f"succubi_{short}_placer",
                           "minecraft:max_stack_size": 1, "minecraft:entity_placer": {"entity": ident}}}})
        boxkit.render(parts, 256, ppu=8).resize((64, 64), Image.LANCZOS).save(f'{rp}/textures/items/succubi/{short}_placer.png')
        item_tex[f'succubi_{short}_placer'] = {"textures": f'textures/items/succubi/{short}_placer'}
    for key, fn in (("rule_wand", wand_icon), ("ghost_bell", bell_icon)):
        fn().save(f'{rp}/textures/items/extra/{key}.png')
        item_tex[f'succubi_{key}'] = {"textures": f'textures/items/extra/{key}'}
        wjson(f'{bp}/items/extra/{key}.json', {"format_version": "1.21.0", "minecraft:item": {
            "description": {"identifier": f"succubi:{key}", "menu_category": {"category": "equipment"}},
            "components": {"minecraft:display_name": {"value": f"item.succubi:{key}.name"}, "minecraft:icon": f"succubi_{key}",
                           "minecraft:max_stack_size": 1}}})


def fogs(rp):
    for ident, (a, b, col) in {"succubi:green_fog": (3, 38, "#1E4A1A"), "succubi:white_fog": (1, 14, "#D8DCDC"),
                               "succubi:blood_moon": (20, 110, "#4A0A0A")}.items():
        wjson(f'{rp}/fogs/{ident.split(":")[1]}.json', {"format_version": "1.16.100", "minecraft:fog_settings": {
            "description": {"identifier": ident},
            "distance": {"air": {"fog_start": a, "fog_end": b, "fog_color": col, "render_distance_type": "fixed"}}}})


def build(bp, rp, item_tex, log):
    scripts(bp, log)
    paper_ui(rp)
    amulet_ui(rp)
    wallet_ui(rp)
    server_form(rp)
    horror_props(bp, rp, item_tex)
    fogs(rp)
    log('v1.0.16: UI + horror props + fogs')


def catalog(bp):
    path = f'{bp}/item_catalog/crafting_item_catalog.json'
    d = json.load(open(path))
    cats = d['minecraft:crafting_items_catalog']['categories']
    groups = {
        "itemGroup.name.succubi:books": ("succubi:book_comic", [f"succubi:{b['key']}" for b in BOOKS]),
        "itemGroup.name.succubi:amulets": ("succubi:amulet_luang_por", [f"succubi:{a['key']}" for a in AMULETS]),
        "itemGroup.name.succubi:horror": ("succubi:rule_wand", ["succubi:rule_wand", "succubi:ghost_bell"] + [f"{i}_placer" for i in HORROR_PROPS]),
    }
    have = {g['group_identifier']['name'] for c in cats for g in c['groups']}
    for name, (icon, items) in groups.items():
        if name not in have:
            cats.append({"category_name": "equipment", "groups": [{"group_identifier": {"icon": icon, "name": name}, "items": items}]})
    for c in cats:
        for g in c['groups']:
            if g['group_identifier']['name'] == 'itemGroup.name.succubi:shops':
                for i in ("succubi:book_stall_placer", "succubi:amulet_stall_placer"):
                    if i not in g['items']:
                        g['items'].append(i)
    wjson(path, d)


def lang_lines(th):
    L = ["", "## v1.0.16"]
    L.append(f"itemGroup.name.succubi:books={'หนังสือ' if th else 'Books'}")
    L.append(f"itemGroup.name.succubi:amulets={'เครื่องราง' if th else 'Amulets'}")
    L.append(f"itemGroup.name.succubi:horror={'อุปกรณ์กฎสยอง' if th else 'Rule of Horror Kit'}")
    L.append(f"item.succubi:rule_wand.name={'ไม้เท้ากฎสยอง' if th else 'Rule Wand'}")
    L.append(f"item.succubi:ghost_bell.name={'กระดิ่งเรียกผี' if th else 'Ghost Bell'}")
    for ident, st in HORROR_PROPS.items():
        L.append(f"item.{ident}_placer.name={st['name'] if th else st['en']}")
        L.append(f"entity.{ident}.name={st['name'] if th else st['en']}")
    L.append(f"action.interact.succubi_use={'ใช้' if th else 'Use'}")
    L.append(f"action.interact.succubi_pickup={'เก็บ (แอดมิน)' if th else 'Pick up (admin)'}")
    return L
