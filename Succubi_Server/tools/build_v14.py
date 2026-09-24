"""v1.0.14: dish names on every shop card (wider shop screen), 'insert all' lights up when you carry cash,
brain sanity icon, server settings item (switch sanity / thirst / strange events, test events on yourself)."""
import json, os, re
from PIL import Image, ImageDraw
import boxkit, shop_art
from build_food import wjson
from build_scripts import edit
from build_extra import card_icon
from data import SHOPS, SUCCUBI
from data_extra import SHOPS_EXTRA
from stands import STANDS

UI_W = 360          # shop screen width (UI units); the vending machines keep their own 280 wide screens
CELL_W = 71         # grid cell (4 columns)
TEX = 'textures/ui/succubi_shops/'

SHORT = {
    # kiosk dishes
    "food:somtum_plate": "ส้มตำไทย", "food:somtum_pla_ra": "ตำปูปลาร้า", "food:larb_plate": "ลาบหมู", "food:kratip_rice": "ข้าวเหนียว",
    "food:kaeng_som": "แกงส้มใต้", "food:omelette_rice": "ข้าวไข่เจียว", "food:fried_chicken_bucket": "ถังไก่ทอด",
    "food:spicy_chicken_bucket": "ไก่ซอสเกาหลี", "food:moo_ping": "หมูปิ้ง+ข้าว", "food:ramen_bowl": "ราเมงโชยุ",
    "food:tomyum_ramen": "ราเมงต้มยำ", "food:tonkotsu_ramen": "ราเมงทงคตสึ", "food:fried_insects_plate": "แมลงทอด",
    "food:spicy_insects_plate": "แมลงต้มยำ", "food:boba_tea": "ชานมไข่มุก", "food:thai_tea_boba": "ชาไทยไข่มุก",
    "food:matcha_boba": "มัทฉะไข่มุก", "food:cocoa_boba": "โกโก้ไข่มุก", "food:kratom_bottle": "ชาสูตรลับ",
    # pharmacy / store
    "succubi:med_paracetamol": "พาราเซตามอล", "succubi:med_cough_syrup": "ยาแก้ไอ", "succubi:med_inhaler": "ยาดม",
    "succubi:med_balm": "ยาหม่อง", "succubi:med_plaster": "พลาสเตอร์", "succubi:med_ors": "เกลือแร่ ORS",
    "succubi:med_vitamin_c": "วิตามินซี", "succubi:med_motion": "ยาแก้เมารถ", "succubi:med_antacid": "ยาธาตุ",
    "kotarus:bandage_blackpowder": "ผ้าพันแผล", "kotarus:syringe_blackpowder": "เข็มลดไข้", "kotarus:medkit_blackpowder": "ชุดชุบชีวิต",
    "succubi:snack_peanuts": "ถั่วอบเกลือ", "succubi:drink_milk": "นมจืด", "succubi:drink_m150": "M-150",
    "succubi:onigiri_tuna": "ข้าวปั้นทูน่า", "succubi:onigiri_salmon": "ปั้นแซลมอน", "succubi:sandwich_ham": "แซนด์วิช",
    "succubi:toastie_ham": "แซนด์วิชอบ", "succubi:dim_sum": "ขนมจีบ", "succubi:bao": "ซาลาเปา", "succubi:sausage": "ไส้กรอก",
    "succubi:rice_krapow": "ข้าวกะเพรา", "succubi:rice_garlic_pork": "หมูกระเทียม", "succubi:boiled_eggs": "ไข่ต้ม",
    "succubi:teddy_bear": "ตุ๊กตาหมี", "succubi:snack_chips_nori": "มันฯสาหร่าย", "succubi:snack_chips_bbq": "มันฯบาร์บีคิว",
    # vending items
    "succubi:drink_water_bottle": "น้ำดื่ม", "succubi:drink_pepsi": "เป๊ปซี่", "succubi:drink_fanta_orange": "แฟนต้า",
    "succubi:drink_sprite": "สไปรท์", "succubi:drink_coca_cola": "โค้ก", "succubi:drink_schweppes": "ชเวปส์",
    "succubi:drink_boss_coffee": "กาแฟกระป๋อง", "succubi:drink_pocari_sweat": "โพคารี่", "succubi:drink_redbull": "เรดบูล",
    "succubi:drink_green_tea": "ชาเขียว", "succubi:drink_monster_energy": "มอนสเตอร์", "succubi:snack_wafer": "เวเฟอร์",
    "succubi:snack_jelly": "เยลลี่", "succubi:snack_prawn_crackers": "ข้าวเกรียบ", "succubi:snack_cream_bun": "ขนมปังครีม",
    "succubi:snack_chips": "มันฝรั่ง", "succubi:snack_fish_strips": "ปลาเส้น", "succubi:snack_cookies": "คุกกี้",
    "succubi:snack_biscuit_sticks": "บิสกิตแท่ง", "succubi:snack_seaweed": "สาหร่าย", "succubi:snack_chocolate": "ช็อกโกแลต",
    "succubi:snack_chips_tube": "มันฯกระป๋อง",
}

OPEN_MACHINE_JS = r'''export async function openMachine(player, machine, note = "") {
  const credit = getCredit(player);
  const container = inventoryOf(player);
  const slots = machine.slots ?? COIN_SLOTS; // notes/coins this machine takes
  const buttons = machine.coinButtons === false ? [] : slots; // coin buttons shown on the screen
  const art = (vendingPath, name) => (machine.btnTex ? `${machine.btnTex}${name}` : vendingPath);
  const hasCash = (value) => !!container && countOf(container, CASH_ID[value]) > 0;
  const anyCash = slots.some(hasCash);
  const form = new ActionFormData()
    .title(`§l${machine.title}${machine.flag}`)
    .body(`§2เงินที่ใส่\n§l§a${formatBaht(credit)} บาท§r${note ? `\n\n${note}` : ""}`);
  for (const p of machine.products) {
    const affordable = credit >= p.price;
    const text = machine.names
      ? `${affordable ? "§f" : "§7"}${p.short ?? p.name}\n${affordable ? "§e§l" : "§8"}${p.price}.-`
      : `${affordable ? "§l" : "§7"}${p.price}.-`;
    form.button(text, `${machine.tex ?? VT}p_${machine.prefix}_${p.key}${affordable ? "" : "_off"}`);
  }
  form.button(credit > 0 ? "§lทอน" : "§7ทอน", art(`${VT}btn_change`, "btn_change") + (credit > 0 ? "" : "_off"));
  for (const value of buttons) {
    const has = hasCash(value);
    form.button(`${has ? "§l" : "§7"}+${value}`, art(`${WT}amt_${value}`, `amt_${value}`) + (has ? "" : "_off"));
  }
  form.button(anyCash ? "§lใส่หมด" : "§7ใส่หมด", art(`${VT}btn_insert_all`, "btn_insert_all") + (anyCash ? "" : "_off"));
  form.button("", art(`${WT}amt_close`, "amt_close"));
'''

SETTINGS_STORE_JS = '''import { world } from "@minecraft/server";

// World-wide switches set from the settings item (default: on)
const KEYS = { sanity: "succubi:cfg_sanity", thirst: "succubi:cfg_thirst", events: "succubi:cfg_events" };

export function enabled(key) {
  try {
    return world.getDynamicProperty(KEYS[key]) !== false;
  } catch (e) {
    return true;
  }
}

export function setEnabled(key, value) {
  world.setDynamicProperty(KEYS[key], !!value);
}
'''

SETTINGS_JS = r'''import { world, system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { enabled, setEnabled } from "./settings_store.js";
import { EVENT_IDS, EVENT_NAMES, runEvent, setSanity, getSanity } from "./sanity.js";
import { setThirst, getThirst, THIRST_MAX } from "./thirst.js";

export const SETTINGS_ID = "succubi:server_settings";
const onOff = (v) => (v ? "§aเปิด" : "§cปิด");

// World switches are for admins: creative mode or the tag "succubi_admin"
function isAdmin(player) {
  try {
    if (player.hasTag("succubi_admin")) return true;
    return String(player.getGameMode?.()).toLowerCase() === "creative";
  } catch (e) {
    return false;
  }
}

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

export async function openSettings(player) {
  if (!isAdmin(player)) {
    player.sendMessage("§c[ตั้งค่า] ใช้ได้เฉพาะแอดมิน (โหมดสร้างสรรค์ หรือมีแท็ก succubi_admin)");
    return;
  }
  const rows = [
    ["sanity", `§lระบบค่าสติ: ${onOff(enabled("sanity"))}`],
    ["thirst", `§lระบบหิวน้ำ: ${onOff(enabled("thirst"))}`],
    ["events", `§lเหตุการณ์ผิดปกติ: ${onOff(enabled("events"))}`]
  ];
  const form = new ActionFormData()
    .title("§lตั้งค่าเซิร์ฟเวอร์")
    .body(`§7สติของฉัน §d${getSanity(player).toFixed(0)}§7/100   น้ำ §b${getThirst(player).toFixed(0)}§7/${THIRST_MAX}\n§7สวิตช์มีผลกับทุกคนในโลก`);
  rows.forEach(([, label]) => form.button(label));
  form.button("§lทดลองเหตุการณ์ผิดปกติ\n§7เกิดกับตัวเองเท่านั้น");
  form.button("§lตั้งค่าสติของฉัน\n§7ไว้ทดสอบหมอก");
  form.button("§lเติมน้ำของฉันให้เต็ม");
  form.button("§7ปิด");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const i = r.selection;
  if (i < rows.length) {
    const key = rows[i][0];
    setEnabled(key, !enabled(key));
    world.sendMessage(`§e[ตั้งค่า] ${player.name} ${enabled(key) ? "§aเปิด" : "§cปิด"}§e${rows[i][1].split(":")[0].replace("§l", "")}`);
    return openSettings(player);
  }
  if (i === rows.length) return openEvents(player);
  if (i === rows.length + 1) return openSetSanity(player);
  if (i === rows.length + 2) {
    setThirst(player, THIRST_MAX);
    player.sendMessage("§b[ตั้งค่า] เติมน้ำเต็มแล้ว");
    return openSettings(player);
  }
}

async function openEvents(player) {
  const form = new ActionFormData().title("§lทดลองเหตุการณ์ผิดปกติ").body("§7เลือกแล้วเกิดกับตัวเองทันที (ลดสติจริง)");
  form.button("§l§dสุ่ม 1 เหตุการณ์");
  for (const id of EVENT_IDS) form.button(EVENT_NAMES[id] ?? id);
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) runEvent(player);
  else if (r.selection <= EVENT_IDS.length) runEvent(player, EVENT_IDS[r.selection - 1]);
  else return openSettings(player);
}

async function openSetSanity(player) {
  const values = [100, 60, 45, 25, 10, 0];
  const form = new ActionFormData().title("§lตั้งค่าสติของฉัน").body("§7ต่ำกว่า 50 / 30 / 15 จะมีหมอกมืด 3 ระดับ");
  values.forEach((v) => form.button(`§l${v}`));
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection < values.length) {
    setSanity(player, values[r.selection]);
    player.sendMessage(`§d[ตั้งค่า] สติ = ${values[r.selection]}`);
  }
  return openSettings(player);
}

export function initSettings() {
  world.afterEvents.itemUse.subscribe((event) => {
    if (event.itemStack?.typeId !== SETTINGS_ID) return;
    system.run(() => {
      openSettings(event.source).catch(() => {});
    });
  });
}
'''


def cell_ui():
    lab = {"type": "label", "text": "#form_button_text", "color": [1, 1, 1], "shadow": True, "localize": False, "layer": 3,
           "anchor_from": "left_middle", "anchor_to": "left_middle", "offset": [21, 0], "size": ["100% - 23px", "default"],
           "font_scale_factor": 0.75,
           "bindings": [{"binding_name": "#form_button_text", "binding_type": "collection", "binding_collection_name": "form_buttons"}]}
    state = lambda overlay, dy: {"type": "panel", "size": ["100%", "100%"], "offset": [0, dy], "controls":
                                 [{"art@succubi_vending.vs_art": {}}, {"label@succubi_shops.sh_label": {}}] +
                                 ([{"overlay": {"type": "image", "texture": overlay, "size": ["100%", "100%"], "layer": 2}}] if overlay else [])}
    return {
        "sh_label": lab,
        "sh_default": state(None, 0),
        "sh_hover": state("textures/ui/succubi_wallet/amt_hover", 0),
        "sh_pressed": state("textures/ui/succubi_wallet/amt_pressed", 1),
        "cell": {"type": "panel", "size": [CELL_W, 30], "controls": [{"button@common.button": {
            "size": [CELL_W - 4, 28], "$pressed_button_name": "button.form_button_click",
            "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
            "controls": [{"default@succubi_shops.sh_default": {}}, {"hover@succubi_shops.sh_hover": {}}, {"pressed@succubi_shops.sh_pressed": {}}]}}]}}


def panel(s):
    grid_w = CELL_W * 4
    lcd = [c / 255 for c in shop_art.lighten(s['theme']['accent'], 0.35)]
    return {"type": "panel", "size": [UI_W, 180], "layer": 2, "controls": [
        {"bg": {"type": "image", "texture": f"{TEX}bg_{s['key']}", "size": ["100%", "100%"], "layer": 1}},
        {"title": {"type": "label", "text": f"§l{s['title']}", "color": [1, 1, 1], "localize": False, "shadow": True,
                   "anchor_from": "top_left", "anchor_to": "top_left", "offset": [12, 7], "layer": 5}},
        {"lcd": {"type": "label", "text": "#form_text", "color": [round(x, 3) for x in lcd], "localize": False, "shadow": False,
                 "anchor_from": "top_left", "anchor_to": "top_left", "offset": [UI_W - 59, 26], "layer": 5,
                 "bindings": [{"binding_name": "#form_text"}], "size": [47, "default"]}},
        {"slots": {"type": "grid", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [9, 21], "size": [grid_w, 150],
                   "grid_dimensions": [4, 5], "grid_item_template": "succubi_shops.cell", "collection_name": "form_buttons", "layer": 5}}]}


def shop_entries(rp):
    """(shop dict, bg icon, [(card key, icon image)])"""
    out = []
    for s in SHOPS:
        icon = Image.open(f'kiosk/kiosk_shops_RP/textures/items/{s["entity"].split(":")[1]}.png')
        items = []
        for k in s['menu']:
            if k.startswith('s:'):
                ident, _ = SUCCUBI[k[2:]]
                items.append((k[2:], Image.open(f'{rp}/textures/items/succubi_food/{ident.split(":")[1]}.png')))
            else:
                items.append((k, Image.open(f'{rp}/textures/items/food/{k}.png')))
        out.append((s, icon, items))
    for s in SHOPS_EXTRA:
        icon = boxkit.render(STANDS[s['entity']]['model'](), 256, ppu=8)
        items = []
        for e in s['menu']:
            img, key = card_icon(rp, e)
            items.append((key, img))
        out.append((s, icon, items))
    return out


def rebuild_shop_ui(rp, log):
    card_w = (CELL_W - 4) * 2
    d = f'{rp}/{TEX}'
    # wide versions of the change / coin / insert-all / close buttons
    VT, WT = f'{rp}/textures/ui/succubi_vending/', f'{rp}/textures/ui/succubi_wallet/'
    for name in ('btn_change', 'btn_change_off', 'btn_insert_all', 'btn_insert_all_off'):
        shop_art.widen(Image.open(VT + name + '.png'), card_w).save(d + name + '.png')
    for v in (1, 5, 10, 20, 50, 100, 500, 1000):
        for suf in ('', '_off'):
            shop_art.widen(Image.open(f'{WT}amt_{v}{suf}.png'), card_w).save(f'{d}amt_{v}{suf}.png')
    shop_art.widen(Image.open(WT + 'amt_close.png'), card_w).save(d + 'amt_close.png')

    ui = json.load(open(f'{rp}/ui/succubi_shops.json'))
    ui.update(cell_ui())
    for s, icon, items in shop_entries(rp):
        shop_art.background(s['key'], s['theme'], icon, rows=5, W=UI_W * 2).save(f'{d}bg_{s["key"]}.png', optimize=True)
        for key, img in items:
            shop_art.card(s['theme'], img, W=card_w).save(f'{d}p_{s["key"]}_{key}.png')
            shop_art.card(s['theme'], img, off=True, W=card_w).save(f'{d}p_{s["key"]}_{key}_off.png')
        ui[f'{s["key"]}_panel'] = panel(s)
    wjson(f'{rp}/ui/succubi_shops.json', ui)
    log(f'shop screens rebuilt {UI_W} wide with names')


def brain_icon(path):
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pink, dark = (255, 190, 214, 255), (190, 90, 140, 255)
    for (x0, y0, x1, y1) in [(28, 60, 132, 150), (52, 34, 132, 110), (28, 110, 118, 200), (124, 60, 228, 150), (124, 34, 204, 110), (138, 110, 228, 200)]:
        d.ellipse([x0, y0, x1, y1], fill=pink)
    d.line([(128, 40), (128, 204)], fill=dark, width=10)
    for pts in ([(62, 88), (92, 104), (80, 136)], [(58, 160), (96, 150)], [(194, 88), (164, 104), (176, 136)], [(198, 160), (160, 150)]):
        d.line(pts, fill=dark, width=9, joint='curve')
    im.resize((64, 64), Image.LANCZOS).save(path)


def gear_icon(path):
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    import math
    c, R, r = S / 2, 110, 76
    for i in range(8):
        a = i * math.pi / 4
        pts = [(c + math.cos(a + da) * rr, c + math.sin(a + da) * rr) for da, rr in ((-0.22, r), (-0.15, R), (0.15, R), (0.22, r))]
        d.polygon(pts, fill=(170, 176, 190, 255))
    d.ellipse([c - 86, c - 86, c + 86, c + 86], fill=(170, 176, 190, 255))
    d.ellipse([c - 38, c - 38, c + 38, c + 38], fill=(60, 64, 76, 255))
    d.ellipse([c - 86, c - 86, c + 86, c + 86], outline=(110, 116, 130, 255), width=8)
    im.resize((64, 64), Image.LANCZOS).save(path)


def build(bp, rp, item_tex, log):
    sd = f'{bp}/scripts/succubi'
    # short names on shop cards
    pj = f'{sd}/products.js'
    js = open(pj, encoding='utf-8').read()
    old = "    return { ...p, price: price ?? p.price };"
    assert old in js
    js = js.replace(old, "    return { ...p, short: SHORT_NAMES[id] ?? p.name, price: price ?? p.price };")
    js = js.replace("const menu = (entries) =>", f"const SHORT_NAMES = {json.dumps(SHORT, ensure_ascii=False, indent=2)};\n\nconst menu = (entries) =>", 1)
    open(pj, 'w', encoding='utf-8').write(js)

    # vending.js: new button builder (names, wide art, insert-all lights up with any cash)
    v = f'{sd}/vending.js'
    vs = open(v, encoding='utf-8').read()
    a = vs.index("export async function openMachine(player, machine, note = \"\") {")
    b = vs.index("  const response = await show(form, player);", a)
    vs = vs[:a] + OPEN_MACHINE_JS + "\n" + vs[b:]
    open(v, 'w', encoding='utf-8').write(vs)
    sh = f'{sd}/shops.js'
    s = open(sh, encoding='utf-8').read()
    n = s.count('tex: "textures/ui/succubi_shops/",')
    s = s.replace('tex: "textures/ui/succubi_shops/",', 'tex: "textures/ui/succubi_shops/", btnTex: "textures/ui/succubi_shops/", names: true,')
    open(sh, 'w', encoding='utf-8').write(s)
    assert n == len(SHOPS) + len(SHOPS_EXTRA), n
    rebuild_shop_ui(rp, log)

    # brain icon for sanity
    brain_icon(f'{rp}/textures/ui/succubi_hud/icon_sanity.png')

    # settings: switches + event tester
    open(f'{sd}/settings_store.js', 'w', encoding='utf-8').write(SETTINGS_STORE_JS)
    open(f'{sd}/settings.js', 'w', encoding='utf-8').write(SETTINGS_JS)
    t = f'{sd}/thirst.js'
    edit(t, 'import { PRODUCT_BY_ID } from "./products.js";\n', 'import { PRODUCT_BY_ID } from "./products.js";\nimport { enabled } from "./settings_store.js";\n')
    edit(t, "export function tickThirst(player, second) {\n  if (isExempt(player)) return;", "export function tickThirst(player, second) {\n  if (isExempt(player) || !enabled(\"thirst\")) return;")
    edit(t, "    const gain = thirstGain(item);\n", "    if (!enabled(\"thirst\")) return;\n    const gain = thirstGain(item);\n")
    h = f'{sd}/hud.js'
    edit(h, 'import { getSanity, SANITY_MAX } from "./sanity.js";\n', 'import { getSanity, SANITY_MAX } from "./sanity.js";\nimport { enabled } from "./settings_store.js";\n')
    edit(h, "T${pad2(toSteps(getThirst(player), THIRST_MAX))}", 'T${pad2(enabled("thirst") ? toSteps(getThirst(player), THIRST_MAX) : 20)}')
    edit(h, "S${pad2(toSteps(getSanity(player), SANITY_MAX))}", 'S${pad2(enabled("sanity") ? toSteps(getSanity(player), SANITY_MAX) : 20)}')
    m = f'{bp}/scripts/main.js'
    edit(m, 'import { initSanity } from "./succubi/sanity.js";\n', 'import { initSanity } from "./succubi/sanity.js";\nimport { initSettings } from "./succubi/settings.js";\n')
    edit(m, "initSanity();\n", "initSanity();\ninitSettings();\n")

    os.makedirs(f'{rp}/textures/items/extra', exist_ok=True)
    gear_icon(f'{rp}/textures/items/extra/server_settings.png')
    item_tex['succubi_server_settings'] = {"textures": 'textures/items/extra/server_settings'}
    wjson(f'{bp}/items/extra/server_settings.json', {"format_version": "1.21.0", "minecraft:item": {
        "description": {"identifier": "succubi:server_settings", "menu_category": {"category": "equipment"}},
        "components": {"minecraft:display_name": {"value": "item.succubi:server_settings.name"}, "minecraft:icon": "succubi_server_settings",
                       "minecraft:max_stack_size": 1}}})
    cat = f'{bp}/item_catalog/crafting_item_catalog.json'
    log('v1.0.14: names, insert-all, brain icon, settings')


def catalog(bp):
    path = f'{bp}/item_catalog/crafting_item_catalog.json'
    d = json.load(open(path))
    for cat in d['minecraft:crafting_items_catalog']['categories']:
        for g in cat['groups']:
            if g['group_identifier']['name'] == 'itemGroup.name.succubi:shops' and 'succubi:server_settings' not in g['items']:
                g['items'].append('succubi:server_settings')
    wjson(path, d)


def lang_lines(th):
    return ["", "## Settings (v1.0.14)", f"item.succubi:server_settings.name={'อุปกรณ์ตั้งค่าเซิร์ฟเวอร์' if th else 'Server Settings'}"]
