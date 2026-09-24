"""v1.0.18 UI renovation:
- every text at 100% size (no more 75-85% labels)
- colours checked for contrast (text vs the art under it)
- shops: 3 columns + scrolling list, change / insert all / close fixed on top
- amulet slots + amulet picker: own screens with big cards
- every other screen (settings item, rule wand, original addon menus, typing screens) gets a custom themed window
- rule wand zone editor + haunted speaker: every choice is a button screen, only text needs the typing screen"""
import json, math, os, re
from PIL import Image, ImageDraw
import shop_art, v18_art
from v18_art import THEMES
from build_food import wjson
from build_scripts import edit
import build_v14
from build_v14 import TEX, shop_entries
from data_v16 import AMULETS

UI = 'textures/ui/succubi_ui/'
SETTINGS_FLAG = "§0§9§4§1"
HORROR_FLAG = "§0§9§4§2"
PICKER_FLAG = "§0§9§5§3"
THEME_FLAGS = {'settings': SETTINGS_FLAG, 'horror': HORROR_FLAG}


def has(flag):
    return f"(not ((#title_text - '{flag}') = #title_text))"


def theme_visible(t):
    if t == 'default':
        return " and ".join(f"((#title_text - '{f}') = #title_text)" for f in THEME_FLAGS.values())
    return has(THEME_FLAGS[t])


def themed(name, tex_fn, **extra):
    """one image per theme, only the one matching the title flag is visible"""
    out = []
    for t in THEMES:
        c = {"type": "image", "texture": tex_fn(t), "size": ["100%", "100%"], "layer": 1,
             "bindings": [{"binding_name": "#title_text"},
                          {"binding_type": "view", "source_property_name": f"({theme_visible(t)})", "target_property_name": "#visible"}]}
        c.update(extra)
        out.append({f"{name}_{t}": c})
    return out


def coll(name, override=None):
    b = {"binding_name": name, "binding_type": "collection", "binding_collection_name": "form_buttons"}
    if override:
        b["binding_name_override"] = override
    return b


def label(text_binding, **kw):
    lab = {"type": "label", "text": text_binding, "color": [1, 1, 1], "shadow": True, "localize": False, "layer": 4,
           "anchor_from": "left_middle", "anchor_to": "left_middle"}
    lab.update(kw)
    return lab


# ---------------------------------------------------------------- themed plain screens
def ui_theme_json():
    def state(s):
        tex = lambda t: f"{UI}btn_{t}_{s}"
        icon = {"type": "image", "size": [24, 24], "offset": [8, 0], "anchor_from": "left_middle", "anchor_to": "left_middle", "layer": 3,
                "bindings": [coll("#form_button_texture", "#texture"), coll("#form_button_texture_file_system", "#texture_file_system"),
                             {"binding_type": "view", "source_property_name": "(not ((#texture = '') or (#texture = 'loading')))",
                              "target_property_name": "#visible"}]}
        with_icon = label("#form_button_text", offset=[36, 0], size=["100% - 40px", "default"],
                          bindings=[coll("#form_button_text"), coll("#form_button_texture"),
                                    {"binding_type": "view", "source_property_name": "(not (#form_button_texture = ''))", "target_property_name": "#visible"}])
        plain = label("#form_button_text", offset=[16, 0], size=["100% - 20px", "default"],
                      bindings=[coll("#form_button_text"), coll("#form_button_texture"),
                                {"binding_type": "view", "source_property_name": "(#form_button_texture = '')", "target_property_name": "#visible"}])
        return {"type": "panel", "size": ["100%", "100%"], "offset": [0, 1 if s == 'pressed' else 0],
                "controls": themed("art", tex) + [{"icon": icon}, {"label_icon": with_icon}, {"label_plain": plain}]}

    def xstate(s):
        return {"type": "panel", "size": ["100%", "100%"], "offset": [0, 1 if s == 'pressed' else 0],
                "controls": themed("x", lambda t: f"{UI}x_{t}_{s}")}

    title = {"type": "label", "text": "#title_text", "color": [1, 0.97, 0.99], "shadow": True, "localize": False, "layer": 5,
             "anchor_from": "top_left", "anchor_to": "top_left", "offset": [12, 8], "size": ["100% - 44px", 10],
             "bindings": [{"binding_name": "#title_text"}]}
    close = {"close@succubi_ui.close_button": {"anchor_from": "top_right", "anchor_to": "top_right", "offset": [-8, 4], "layer": 6}}

    def window(kind, W, H):
        return {"type": "panel", "size": [W, H], "layer": 2, "controls":
                themed("bg", lambda t: f"{UI}{kind}_{t}") + [{"title": title}, close,
                {"content": {"type": "panel", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [8, 28],
                             "size": [W - 16, H - 36], "layer": 5,
                             "controls": [{"form@server_form.long_form_panel" if kind == 'list' else "form@server_form.custom_form_panel": {}}]}}]}

    return {
        "namespace": "succubi_ui",
        "lb_default": state('default'), "lb_hover": state('hover'), "lb_pressed": state('pressed'),
        "x_default": xstate('default'), "x_hover": xstate('hover'), "x_pressed": xstate('pressed'),
        "close_button@common.button": {"size": [18, 18], "$pressed_button_name": "button.menu_exit",
                                       "controls": [{"default@succubi_ui.x_default": {}}, {"hover@succubi_ui.x_hover": {}},
                                                    {"pressed@succubi_ui.x_pressed": {}}]},
        "list_window": window('list', 300, 200),
        "modal_window": window('modal', 300, 214),
    }


def server_form_overrides(sf):
    """long_form fallback + list look + typing screens, in the vanilla server_form namespace"""
    ctl = sf['long_form']['controls']
    ctl[0] = {"succubi_list@succubi_ui.list_window": {"bindings": [
        {"binding_name": "#title_text"},
        {"binding_type": "view", "source_property_name": "(((#title_text - '§0§9') = #title_text) or " + has('§0§9§4') + ")",
         "target_property_name": "#visible"}]}}
    sf['long_form_scrolling_content'] = {
        "type": "stack_panel", "size": ["100% - 4px", "100%c"], "orientation": "vertical", "anchor_from": "top_left", "anchor_to": "top_left",
        "controls": [
            {"label_offset_panel": {"type": "panel", "size": ["100%", "100%c"], "controls": [
                {"main_label": {"type": "label", "offset": [3, 2], "color": [0.96, 0.94, 0.98], "shadow": True, "size": ["100% - 6px", "default"],
                                "anchor_from": "top_left", "anchor_to": "top_left", "text": "#form_text"}}]}},
            {"padding": {"type": "panel", "size": ["100%", 6]}},
            {"wrapping_panel": {"type": "panel", "size": ["100%", "100%c"], "controls": [
                {"long_form_dynamic_buttons_panel@server_form.long_form_dynamic_buttons_panel": {}}]}}]}
    sf['dynamic_button'] = {"type": "panel", "size": ["100%", 33], "controls": [{"button@common.button": {
        "size": ["100%", 31], "anchor_from": "top_left", "anchor_to": "top_left", "$pressed_button_name": "button.form_button_click",
        "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
        "controls": [{"default@succubi_ui.lb_default": {}}, {"hover@succubi_ui.lb_hover": {}}, {"pressed@succubi_ui.lb_pressed": {}}]}}]}
    sf['custom_form'] = {"type": "panel", "size": ["100%", "100%"], "controls": [{"window@succubi_ui.modal_window": {}}]}
    return sf


def theme_art(rp):
    d = f'{rp}/{UI}'
    os.makedirs(d, exist_ok=True)
    for t, th in THEMES.items():
        v18_art.window(th, 600, 400).save(f'{d}list_{t}.png')
        v18_art.window(th, 600, 428).save(f'{d}modal_{t}.png')
        for s in ('default', 'hover', 'pressed'):
            v18_art.list_button(th, s).save(f'{d}btn_{t}_{s}.png')
            v18_art.close_button(th, s).save(f'{d}x_{t}_{s}.png')


# ---------------------------------------------------------------- shops: 3 columns, scrolling
CELL_W, CELL_H, ACT_H = 88, 34, 30
LIST_H = 134


def shop_ui(rp, log):
    d = f'{rp}/{TEX}'
    VT, WT = f'{rp}/textures/ui/succubi_vending/', f'{rp}/textures/ui/succubi_wallet/'
    bw = (CELL_W - 2) * 2
    for name in ('btn_change', 'btn_change_off', 'btn_insert_all', 'btn_insert_all_off'):
        v18_art.ensure_dark(shop_art.widen(Image.open(VT + name + '.png'), bw), (48, 8, bw - 12, 48)).save(d + name + '.png')
    v18_art.ensure_dark(shop_art.widen(Image.open(WT + 'amt_close.png'), bw), (48, 8, bw - 12, 48)).save(d + 'amt_close.png')

    ui = json.load(open(f'{rp}/ui/succubi_shops.json'))
    for old in ('sh_label', 'sh_default', 'sh_hover', 'sh_pressed', 'cell'):   # the old 4-column cards are no longer used
        ui.pop(old, None)
    art_l = {"art@succubi_vending.vs_art": {}}
    visible_if_card = {"binding_type": "view", "source_property_name": "(not ((#form_button_texture - '/p_') = #form_button_texture))",
                       "target_property_name": "#visible"}

    def states(lab_name):
        st = lambda overlay, dy: {"type": "panel", "size": ["100%", "100%"], "offset": [0, dy], "controls":
                                  [art_l, {"label@succubi_shops." + lab_name: {}}] +
                                  ([{"overlay": {"type": "image", "texture": overlay, "size": ["100%", "100%"], "layer": 2}}] if overlay else [])}
        return st(None, 0), st("textures/ui/succubi_wallet/amt_hover", 0), st("textures/ui/succubi_wallet/amt_pressed", 1)

    def cell(size, btn, prefix, extra_bind=None):
        return {"type": "panel", "size": size, "bindings": ([coll("#form_button_texture"), extra_bind] if extra_bind else []),
                "controls": [{"button@common.button": {
                    "size": btn, "$pressed_button_name": "button.form_button_click",
                    "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
                    "controls": [{f"default@succubi_shops.{prefix}_default": {}}, {f"hover@succubi_shops.{prefix}_hover": {}},
                                 {f"pressed@succubi_shops.{prefix}_pressed": {}}]}}]}

    ui["s3_label"] = label("#form_button_text", offset=[27, 0], size=["100% - 29px", "default"], bindings=[coll("#form_button_text")])
    ui["s3a_label"] = label("#form_button_text", offset=[25, 0], size=["100% - 27px", "default"], bindings=[coll("#form_button_text")])
    ui["s3_default"], ui["s3_hover"], ui["s3_pressed"] = states("s3_label")
    ui["s3a_default"], ui["s3a_hover"], ui["s3a_pressed"] = states("s3a_label")
    ui["cell3"] = cell([CELL_W, CELL_H], [CELL_W - 2, CELL_H - 2], "s3", visible_if_card)
    ui["cell3a"] = cell([CELL_W, ACT_H], [CELL_W - 2, ACT_H - 2], "s3a")

    icon_of = {}
    for s, icon, items in shop_entries(rp):
        v18_art.shop_background(s['key'], s['theme'], icon).save(f'{d}bg_{s["key"]}.png', optimize=True)
        for key, img in items:
            v18_art.card(s['theme'], img).save(f'{d}p_{s["key"]}_{key}.png')
            v18_art.card(s['theme'], img, off=True).save(f'{d}p_{s["key"]}_{key}_off.png')
        rows = math.ceil(len(items) / 3)
        ui[f'{s["key"]}_content'] = {"type": "panel", "size": [CELL_W * 3, CELL_H * rows], "anchor_from": "top_left", "anchor_to": "top_left",
                                     "clips_children": True, "controls": [{"grid": {
                                         "type": "grid", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [0, -CELL_H],
                                         "size": [CELL_W * 3, CELL_H * (rows + 1)], "grid_dimensions": [3, rows + 1],
                                         "grid_item_template": "succubi_shops.cell3", "collection_name": "form_buttons"}}]}
        ui[f'{s["key"]}_panel'] = shop_panel(s)
        icon_of[s['key']] = len(items)
    wjson(f'{rp}/ui/succubi_shops.json', ui)
    log(f'shop screens: 3 columns + scrolling ({len(icon_of)} shops)')


def lcd_colour(s):
    return [round(c / 255, 3) for c in shop_art.lighten(s['theme']['accent'], 0.35)]


def shop_panel(s):
    W, H = v18_art.SHOP_W // 2, v18_art.SHOP_H // 2
    return {"type": "panel", "size": [W, H], "layer": 2, "controls": [
        {"bg": {"type": "image", "texture": f"{TEX}bg_{s['key']}", "size": ["100%", "100%"], "layer": 1}},
        {"title": {"type": "label", "text": f"§l{s['title']}", "color": [1, 1, 1], "localize": False, "shadow": True,
                   "anchor_from": "top_left", "anchor_to": "top_left", "offset": [12, 9], "layer": 5}},
        {"lcd": {"type": "label", "text": "#form_text", "color": lcd_colour(s), "localize": False, "shadow": True,
                 "anchor_from": "top_left", "anchor_to": "top_left", "offset": [293, 31], "size": [56, "default"], "layer": 5,
                 "bindings": [{"binding_name": "#form_text"}]}},
        {"actions": {"type": "grid", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [8, 26], "size": [CELL_W * 3, ACT_H],
                     "grid_dimensions": [3, 1], "grid_item_template": "succubi_shops.cell3a", "collection_name": "form_buttons", "layer": 5}},
        {"list": {"type": "panel", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [8, 61], "size": [276, LIST_H - 2], "layer": 5,
                  "controls": [{"scroll@common.scrolling_panel": {
                      "anchor_from": "top_left", "anchor_to": "top_left", "size": ["100%", "100%"], "$show_background": False,
                      "$scrolling_content": f"succubi_shops.{s['key']}_content", "$scroll_size": [5, "100% - 4px"],
                      "$scrolling_pane_size": ["100%", "100%"], "$scrolling_pane_offset": [0, 0],
                      "$scroll_bar_right_padding_size": [0, 0]}}]}}]}


SHOP3_JS = r'''// Shops with names (kiosks, pharmacy, store shelves, books, amulets): 3 columns + scrolling list.
// Buttons: 0 change, 1 insert all cash, 2 close, then the products.
async function openShop3(player, machine, note = "") {
  const credit = getCredit(player);
  const container = inventoryOf(player);
  const slots = machine.slots ?? COIN_SLOTS;
  const hasCash = (value) => !!container && countOf(container, CASH_ID[value]) > 0;
  const anyCash = slots.some(hasCash);
  const T = machine.btnTex;
  const form = new ActionFormData()
    .title(`§l${machine.title}${machine.flag}`)
    .body(`§fเงินที่ใส่\n§l§a${formatBaht(credit)} บาท§r${note ? `\n\n${note}` : ""}`);
  form.button(credit > 0 ? "§lทอนเงิน" : "§7ทอนเงิน", `${T}btn_change${credit > 0 ? "" : "_off"}`);
  form.button(anyCash ? "§lใส่เงินหมด" : "§7ใส่เงินหมด", `${T}btn_insert_all${anyCash ? "" : "_off"}`);
  form.button("§lปิด", `${T}amt_close`);
  for (const p of machine.products) {
    const price = priceFor(player, p);
    const ok = credit >= price;
    form.button(`§f${p.short ?? p.name}\n${ok ? "§e§l" : "§7"}${price}.-`, `${machine.tex ?? VT}p_${machine.prefix}_${p.key}${ok ? "" : "_off"}`);
  }
  const response = await show(form, player);
  if (!response || response.canceled) return closeMachine(player, machine);
  const index = response.selection;
  let message = "";
  if (index === 0) {
    const back = returnChange(player);
    if (back > 0) player.playSound("random.orb");
    message = back > 0 ? `§fทอนเงิน\n${formatBaht(back)} บาท` : "§fยังไม่ได้ใส่เงิน";
  } else if (index === 1) {
    const total = insertAll(player, slots);
    if (total > 0) player.playSound("random.click");
    message = total > 0 ? `§fใส่เงิน\n${formatBaht(total)} บาท` : "§cไม่มีเงินสด\nในตัว";
  } else {
    const product = machine.products[index - 3];
    if (!product) return closeMachine(player, machine);
    const result = buy(player, product);
    if (result.ok) player.playSound("random.pop");
    message = result.ok ? `§fได้รับ\n§e${product.short ?? product.name}` : `§cใส่เพิ่มอีก\n${result.need} บาท`;
  }
  return openShop3(player, machine, message);
}

'''


# ---------------------------------------------------------------- amulet screens
AM_CELL = [112, 48]


def amulet_ui(rp):
    from build_v16 import AMULET_THEME
    th = AMULET_THEME
    d = f'{rp}/{TEX}'
    for a in AMULETS:
        k = a['key'].replace('amulet_', '')
        v18_art.card(th, a['icon'](), W=216, H=88, icon_px=60).save(f'{d}p_amuletui_{k}.png')
    empty = Image.new('RGBA', (64, 64), (0, 0, 0, 0)); ed = ImageDraw.Draw(empty)
    ed.rounded_rectangle([8, 8, 56, 56], radius=8, outline=(232, 186, 60, 230), width=3)
    ed.line([(32, 20), (32, 44)], fill=(232, 186, 60, 240), width=4); ed.line([(20, 32), (44, 32)], fill=(232, 186, 60, 240), width=4)
    v18_art.card(th, empty, W=216, H=88, icon_px=60).save(f'{d}p_amuletui_empty.png')
    WT = f'{rp}/textures/ui/succubi_wallet/'
    for n in ('amt_close', 'amt_back'):
        b = v18_art.ensure_dark(shop_art.widen(Image.open(WT + n + '.png'), 216), (48, 8, 204, 48))
        v18_art.pad_to(b, 88).save(f'{d}{n}_am.png')
    v18_art.amulet_background(th, AMULETS[0]['icon']()).save(f'{d}bg_amuletui.png', optimize=True)

    ui = json.load(open(f'{rp}/ui/succubi_shops.json'))
    ui["am_label"] = label("#form_button_text", offset=[37, 0], size=["100% - 39px", "default"], bindings=[coll("#form_button_text")])
    st = lambda overlay, dy: {"type": "panel", "size": ["100%", "100%"], "offset": [0, dy], "controls":
                              [{"art@succubi_vending.vs_art": {}}, {"label@succubi_shops.am_label": {}}] +
                              ([{"overlay": {"type": "image", "texture": overlay, "size": ["100%", "100% - 2px"], "layer": 2}}] if overlay else [])}
    ui["am_default"], ui["am_hover"], ui["am_pressed"] = st(None, 0), st("textures/ui/succubi_wallet/amt_hover", 0), st("textures/ui/succubi_wallet/amt_pressed", 1)
    ui["am_cell"] = {"type": "panel", "size": AM_CELL, "controls": [{"button@common.button": {
        "size": [AM_CELL[0] - 4, AM_CELL[1] - 4], "$pressed_button_name": "button.form_button_click",
        "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
        "controls": [{"default@succubi_shops.am_default": {}}, {"hover@succubi_shops.am_hover": {}}, {"pressed@succubi_shops.am_pressed": {}}]}}]}
    rows = math.ceil((len(AMULETS) + 1) / 2)
    ui["am_pick_content"] = {"type": "panel", "size": [AM_CELL[0] * 2, AM_CELL[1] * rows], "anchor_from": "top_left", "anchor_to": "top_left",
                             "controls": [{"grid": {"type": "grid", "anchor_from": "top_left", "anchor_to": "top_left",
                                                    "size": [AM_CELL[0] * 2, AM_CELL[1] * rows], "grid_dimensions": [2, rows],
                                                    "grid_item_template": "succubi_shops.am_cell", "collection_name": "form_buttons"}}]}

    def panel(title, body_ctl):
        return {"type": "panel", "size": [v18_art.AM_W // 2, v18_art.AM_H // 2], "layer": 2, "controls": [
            {"bg": {"type": "image", "texture": f"{TEX}bg_amuletui", "size": ["100%", "100%"], "layer": 1}},
            {"title": {"type": "label", "text": title, "color": [1, 0.93, 0.75], "localize": False, "shadow": True,
                       "anchor_from": "top_left", "anchor_to": "top_left", "offset": [12, 9], "layer": 5}},
            {"lcd": {"type": "label", "text": "#form_text", "color": [1, 0.9, 0.6], "localize": False, "shadow": True,
                     "anchor_from": "top_left", "anchor_to": "top_left", "offset": [245, 33], "size": [66, "default"], "layer": 5,
                     "bindings": [{"binding_name": "#form_text"}]}},
            body_ctl]}
    ui["amuletui_panel"] = panel("§lเครื่องราง", {"slots": {
        "type": "grid", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [8, 27], "size": [AM_CELL[0] * 2, AM_CELL[1] * 3],
        "grid_dimensions": [2, 3], "grid_item_template": "succubi_shops.am_cell", "collection_name": "form_buttons", "layer": 5}})
    ui["amulet_picker_panel"] = panel("§lเลือกเครื่องราง", {"list": {
        "type": "panel", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [8, 27], "size": [228, 166], "layer": 5,
        "controls": [{"scroll@common.scrolling_panel": {
            "anchor_from": "top_left", "anchor_to": "top_left", "size": ["100%", "100%"], "$show_background": False,
            "$scrolling_content": "succubi_shops.am_pick_content", "$scroll_size": [5, "100% - 4px"],
            "$scrolling_pane_size": ["100%", "100%"], "$scrolling_pane_offset": [0, 0], "$scroll_bar_right_padding_size": [0, 0]}}]}})
    wjson(f'{rp}/ui/succubi_shops.json', ui)


# ---------------------------------------------------------------- wallet + paper
def wallet_ui(rp):
    w = f'{rp}/textures/ui/succubi_wallet/'
    for n in ('btn_deposit_s', 'btn_withdraw_s', 'btn_amulet_s', 'btn_close_s'):
        im = Image.open(w + n + '.png')
        v18_art.ensure_dark(im, (52, 8, im.width - 12, im.height - 12)).save(w + n + '.png')
    for v in (1, 5, 10, 20, 50, 100, 500, 1000):
        for suf in ('', '_off'):
            im = Image.open(f'{w}amt_{v}{suf}.png')
            v18_art.ensure_dark(im, (44, 8, im.width - 12, im.height - 12)).save(f'{w}amt_{v}{suf}.png')
    for n in ('amt_back', 'amt_close'):
        im = Image.open(w + n + '.png')
        v18_art.ensure_dark(im, (44, 8, im.width - 12, im.height - 12)).save(w + n + '.png')
    p = f'{rp}/ui/succubi_wallet.json'
    ui = json.load(open(p))
    ui['face_label'].pop('font_scale_factor', None)
    ui['face_label']['size'] = ["100% - 25px", "default"]
    ui['amt_label']['size'] = ["100% - 21px", "default"]
    wjson(p, ui)


def paper_ui(rp):
    p = f'{rp}/ui/succubi_paper.json'
    ui = json.load(open(p))
    ui['pp_label'].pop('font_scale_factor', None)
    ui['pp_label']['offset'] = [22, 0]
    ui['pp_label']['size'] = ["100% - 24px", "default"]
    wjson(p, ui)


# ---------------------------------------------------------------- scripts
HORROR_SCREENS_JS = r'''// ---------------------------------------------------------------- wand screens (horror skin: HORROR_FLAG at the end of the title)
const HORROR_FLAG = "§0§9§4§2";
const onOffText = (v) => (v ? "§aเปิด" : "§cปิด");
const RADII = [2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40];
const SECONDS = [10, 15, 20, 30, 45, 60, 90, 120, 180, 300];

async function wandMenu(player) {
  if (!isAdmin(player)) return player.sendMessage("§c[กฎสยอง] ใช้ได้เฉพาะแอดมิน (โหมดสร้างสรรค์ หรือแท็ก succubi_admin)");
  const near = zones.filter((z) => z.dim === player.dimension.id && flat(player.location, z) <= 128).length;
  const form = new ActionFormData()
    .title(`§lไม้เท้ากฎสยอง${HORROR_FLAG}`)
    .body(`§fโซนกฎทั้งหมด §e${zones.length}§f โซน (ใกล้ตัว §e${near}§f)\n§7ถือไม้เท้านี้ไว้จะเห็นขอบโซนเป็นเปลวไฟ\n§fอุปกรณ์กฎสยอง: ${onOffText(enabled("rules"))} §7(ปิดได้ที่อุปกรณ์ตั้งค่า)`)
    .button("§l§aสร้างโซนกฎตรงที่ยืน\n§7ตั้งกฎ รัศมี และบทลงโทษ")
    .button("§lโซนใกล้ตัว / แก้ไข\n§7ย้าย วาร์ป หรือลบโซน")
    .button("§lวิธีใช้อุปกรณ์กฎสยอง")
    .button("§7ปิด");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) return editZone(player, undefined);
  if (r.selection === 1) return zoneList(player);
  if (r.selection === 2) return help(player);
}

// pick one from a list (custom screen); undefined = back
async function pick(player, title, names, current) {
  const form = new ActionFormData().title(`§l${title}${HORROR_FLAG}`).body("§fเลือก 1 อย่าง");
  names.forEach((n, i) => form.button(i === current ? `§l§e> ${n} <` : `§f${n}`));
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled || r.selection >= names.length) return undefined;
  return r.selection;
}

// typing screen (only for text); undefined = cancelled
async function typeText(player, title, hint, value) {
  const form = new ModalFormData().title(`§l${title}${HORROR_FLAG}`).textField(title, hint, String(value ?? ""));
  const r = await show(form, player);
  if (!r || r.canceled) return undefined;
  return String(r.formValues?.[0] ?? "").slice(0, 80);
}

const TEXTS = {
  name: ["ชื่อโซน", "เช่น ห้องใต้ดิน"],
  enter: ["ข้อความตอนเดินเข้าโซน", "เช่น ห้ามส่งเสียงดัง"],
  violate: ["ข้อความตอนทำผิด", "เช่น มันได้ยินคุณแล้ว"]
};

// zone editor: every choice is a button, the draft is kept until "save"
async function editZone(player, zone, draft) {
  const z = draft ?? { ...(zone ?? { id: `z${Date.now().toString(36)}`, name: "", dim: player.dimension.id, x: Math.floor(player.location.x) + 0.5,
    y: Math.floor(player.location.y), z: Math.floor(player.location.z) + 0.5, r: 6, rule: "no_sprint", value: "30",
    punish: "sanity10", time: "always", enter: "", violate: "", on: true }) };
  const rows = [
    ["name", `§lชื่อโซน\n${z.name ? `§f${z.name}` : "§7(ว่าง = ใช้ชื่อกฎ)"}`],
    ["rule", `§lกฎของโซน\n§e${label(RULES, z.rule)}`],
    ["r", `§lรัศมี\n§e${z.r} บล็อก`]
  ];
  if (z.rule === "time_limit") rows.push(["value", `§lอยู่ในโซนได้นาน\n§e${z.value} วินาที`]);
  rows.push(
    ["punish", `§lบทลงโทษ\n§e${label(PUNISH, z.punish)}`],
    ["time", `§lช่วงเวลาที่กฎทำงาน\n§e${label(TIMES, z.time)}`],
    ["enter", `§lข้อความตอนเดินเข้าโซน\n${z.enter ? `§f${z.enter}` : "§7(ว่าง = บอกชื่อกฎ)"}`],
    ["violate", `§lข้อความตอนทำผิด\n${z.violate ? `§f${z.violate}` : "§7(ว่าง = ข้อความเริ่มต้น)"}`],
    ["on", `§lสถานะโซน: ${onOffText(z.on)}\n§7แตะเพื่อสลับ`]
  );
  const form = new ActionFormData().title(`§l${zone ? "แก้ไขโซนกฎ" : "สร้างโซนกฎ"}${HORROR_FLAG}`)
    .body("§fแตะแต่ละแถวเพื่อเปลี่ยนค่า แล้วกด §aบันทึกโซน");
  rows.forEach(([, t]) => form.button(t));
  form.button("§l§aบันทึกโซน");
  form.button("§7ยกเลิก");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const i = r.selection;
  if (i === rows.length) return saveZone(player, zone, z);
  if (i > rows.length) return;
  const key = rows[i][0];
  if (key === "rule") {
    const v = await pick(player, "กฎของโซน", RULES.map((x) => x[1]), idx(RULES, z.rule));
    if (v !== undefined) z.rule = RULES[v][0];
  } else if (key === "r") {
    const v = await pick(player, "รัศมีของโซน", RADII.map((n) => `${n} บล็อก`), RADII.indexOf(z.r));
    if (v !== undefined) z.r = RADII[v];
  } else if (key === "value") {
    const v = await pick(player, "อยู่ในโซนได้นาน", SECONDS.map((n) => `${n} วินาที`), SECONDS.indexOf(Number(z.value)));
    if (v !== undefined) z.value = String(SECONDS[v]);
  } else if (key === "punish") {
    const v = await pick(player, "บทลงโทษ", PUNISH.map((x) => x[1]), idx(PUNISH, z.punish));
    if (v !== undefined) z.punish = PUNISH[v][0];
  } else if (key === "time") {
    const v = await pick(player, "ช่วงเวลาที่กฎทำงาน", TIMES.map((x) => x[1]), idx(TIMES, z.time));
    if (v !== undefined) z.time = TIMES[v][0];
  } else if (key === "on") {
    z.on = !z.on;
  } else {
    const [title, hint] = TEXTS[key];
    const v = await typeText(player, title, hint, z[key]);
    if (v !== undefined) z[key] = v;
  }
  return editZone(player, zone, z);
}

function saveZone(player, zone, z) {
  if (!z.name) z.name = label(RULES, z.rule);
  if (zone) Object.assign(zone, z);
  else zones.push(z);
  saveZones();
  player.sendMessage(`§a[กฎสยอง] บันทึกโซน "${z.name}" (${label(RULES, z.rule)}, รัศมี ${z.r}, โทษ: ${label(PUNISH, z.punish)})`);
}

async function zoneList(player) {
  const list = zones.filter((z) => z.dim === player.dimension.id).map((z) => ({ z, d: flat(player.location, z) }))
    .sort((a, b) => a.d - b.d).slice(0, 30);
  if (list.length === 0) return player.sendMessage("§7[กฎสยอง] ยังไม่มีโซนในมิตินี้");
  const form = new ActionFormData().title(`§lโซนกฎ${HORROR_FLAG}`).body("§fเรียงจากใกล้ไปไกล");
  for (const { z, d } of list) form.button(`${z.on ? "§l§c" : "§7"}${z.name}\n§f${label(RULES, z.rule)} §7· ${Math.round(d)} ม.`);
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection >= list.length) return wandMenu(player);
  const z = list[r.selection].z;
  const m = new ActionFormData().title(`§l${z.name}${HORROR_FLAG}`)
    .body(`§7กฎ: §f${label(RULES, z.rule)}\n§7โทษ: §f${label(PUNISH, z.punish)}\n§7รัศมี §f${z.r}§7 · §f${label(TIMES, z.time)}§7 · ${onOffText(z.on)}`)
    .button("§lแก้ไข").button("§lย้ายโซนมาที่ฉันยืน").button("§lวาร์ปไปที่โซน").button("§l§cลบโซน").button("§7« กลับ");
  const a = await show(m, player);
  if (!a || a.canceled) return;
  if (a.selection === 0) return editZone(player, z);
  if (a.selection === 1) {
    Object.assign(z, { dim: player.dimension.id, x: Math.floor(player.location.x) + 0.5, y: Math.floor(player.location.y), z: Math.floor(player.location.z) + 0.5 });
    saveZones();
    return player.sendMessage("§a[กฎสยอง] ย้ายโซนแล้ว");
  }
  if (a.selection === 2) return player.teleport({ x: z.x, y: z.y, z: z.z }, { dimension: world.getDimension(z.dim.replace("minecraft:", "")) });
  if (a.selection === 3) {
    zones = zones.filter((x) => x.id !== z.id);
    saveZones();
    return player.sendMessage("§c[กฎสยอง] ลบโซนแล้ว");
  }
  return zoneList(player);
}

async function help(player) {
  const form = new ActionFormData().title(`§lวิธีใช้อุปกรณ์กฎสยอง${HORROR_FLAG}`).body([
    "§6ไม้เท้ากฎสยอง§f: คลิกขวาเพื่อสร้าง/แก้ไขโซนกฎ ใครอยู่ในโซนแล้วทำผิดกฎจะโดนลงโทษ (ผู้เล่นโหมดสร้างสรรค์ไม่โดน)",
    "§6ป้ายประกาศกฎ§f: วางไว้ให้คนอ่าน แอดมินถือไม้เท้าแล้วคลิกขวาที่ป้ายเพื่อเขียนกฎ",
    "§6รูปปั้นเฝ้ามอง§f: ขยับเข้าหาผู้เล่นเฉพาะตอนไม่มีใครมองมัน ถ้าถึงตัวจะโดนหลอก แอดมินถือไม้เท้าคลิกขวาเพื่อเปิด/ปิด",
    "§6ลำโพงหลอน§f: เล่นเสียงหลอนให้คนรอบๆ ทุกกี่วินาทีก็ได้ แอดมินคลิกขวาเพื่อตั้งค่า",
    "§6กระดิ่งเรียกผี§f: แอดมินสั่นแล้วทุกคนในระยะ 48 บล็อกได้ยินและสติลดเล็กน้อย",
    "§fเก็บของที่วางไว้: แอดมินย่อ + คลิกขวา"
  ].join("\n\n")).button("§7« กลับ");
  const r = await show(form, player);
  if (r && !r.canceled) return wandMenu(player);
}

'''

SPEAKER_JS = r'''async function editSpeaker(player, sp, draft) {
  const c = draft ?? { ...DEFAULT_SPEAKER, ...readJson(sp, "succubi:speaker", DEFAULT_SPEAKER) };
  const soundName = (SOUNDS.find((s) => s[0] === c.sound) ?? SOUNDS[0])[1];
  const form = new ActionFormData().title(`§lตั้งค่าลำโพงหลอน${HORROR_FLAG}`).body("§fแตะแต่ละแถวเพื่อเปลี่ยนค่า แล้วกด §aบันทึก")
    .button(`§lเสียง\n§e${soundName}`)
    .button(`§lเล่นทุก\n§e${c.every} วินาที`)
    .button(`§lระยะได้ยิน\n§e${c.radius} บล็อก`)
    .button(`§lสติลดต่อครั้ง\n§e${c.loss}`)
    .button("§lลองฟังเสียง")
    .button("§l§aบันทึก")
    .button("§7ยกเลิก");
  const r = await show(form, player);
  if (!r || r.canceled || r.selection === 6) return;
  const i = r.selection;
  if (i === 5) {
    sp.setDynamicProperty("succubi:speaker", JSON.stringify({ sound: c.sound, every: c.every, radius: c.radius, loss: c.loss }));
    return player.sendMessage("§a[กฎสยอง] ตั้งค่าลำโพงแล้ว");
  }
  if (i === 4) {
    try {
      player.playSound(c.sound);
    } catch (e) {}
  } else if (i === 0) {
    const v = await pick(player, "เสียงของลำโพง", SOUNDS.map((s) => s[1]), SOUNDS.findIndex((s) => s[0] === c.sound));
    if (v !== undefined) c.sound = SOUNDS[v][0];
  } else if (i === 1) {
    const v = await pick(player, "เล่นทุกกี่วินาที", EVERY.map((n) => `${n} วินาที`), EVERY.indexOf(c.every));
    if (v !== undefined) c.every = EVERY[v];
  } else if (i === 2) {
    const v = await pick(player, "ระยะได้ยิน", RADIUS.map((n) => `${n} บล็อก`), RADIUS.indexOf(c.radius));
    if (v !== undefined) c.radius = RADIUS[v];
  } else if (i === 3) {
    const v = await pick(player, "สติลดต่อครั้ง", LOSS.map(String), LOSS.indexOf(c.loss));
    if (v !== undefined) c.loss = LOSS[v];
  }
  return editSpeaker(player, sp, c);
}
'''


def cut(s, start, end):
    a = s.index(start)
    b = s.index(end, a)
    return a, b


def scripts(bp):
    sd = f'{bp}/scripts/succubi'
    # shops: 3-column screen for every shop with names
    v = f'{sd}/vending.js'
    vs = open(v, encoding='utf-8').read()
    head = 'export async function openMachine(player, machine, note = "") {\n'
    assert vs.count(head) == 1
    vs = vs.replace(head, SHOP3_JS + head + '  if (machine.names) return openShop3(player, machine, note);\n')
    open(v, 'w', encoding='utf-8').write(vs)

    # wallet: dark text colours on the cream pocket, labels not bold (fit at 100% size)
    m = f'{sd}/money.js'
    ms = open(m, encoding='utf-8').read()
    for old, new in (("§l§2${formatBaht(balance)}", "§l§1${formatBaht(balance)}"), ("§l§2${formatBaht(getBalance(player))}", "§l§1${formatBaht(getBalance(player))}"),
                     ("§l§6${formatBaht(countCash(player))}", "§l§4${formatBaht(countCash(player))}"), ("`§2ถอนแล้ว", "`§1ถอนแล้ว"),
                     ("`§c${FAIL_TEXT", "`§4${FAIL_TEXT"), ("`§2ฝากแล้ว", "`§1ฝากแล้ว"), ('"§cไม่มีเงินสดในตัว"', '"§4ไม่มีเงินสดในตัว"'),
                     ('"§lฝากเงิน"', '"ฝากเงิน"'), ('"§lถอนเงิน", "textures/ui/succubi_wallet/btn_withdraw_s"', '"ถอนเงิน", "textures/ui/succubi_wallet/btn_withdraw_s"'),
                     ('"§lเครื่องราง"', '"เครื่องราง"'), ('"§lปิด", "textures/ui/succubi_wallet/btn_close_s"', '"ปิด", "textures/ui/succubi_wallet/btn_close_s"')):
        assert ms.count(old) == 1, old
        ms = ms.replace(old, new)
    open(m, 'w', encoding='utf-8').write(ms)

    # amulets: readable hints, own picker screen
    a = f'{sd}/amulets.js'
    edit(a, 'export const AMULET_FLAG = "§0§9§5§2"; // skin in RP ui/server_form.json',
         'export const AMULET_FLAG = "§0§9§5§2"; // skin in RP ui/server_form.json\nexport const PICKER_FLAG = "§0§9§5§3";')
    edit(a, 'form.button(`§f${AMULETS[key].short}\\n§7แตะเพื่อถอด`', 'form.button(`§f${AMULETS[key].short}\\n§eแตะเพื่อถอด`')
    edit(a, 'form.button("§7ช่องว่าง\\n§8แตะเพื่อใส่"', 'form.button("§fช่องว่าง\\n§eแตะเพื่อใส่"')
    edit(a, 'form.button("", `${TEX}amt_close`)', 'form.button("§lปิด", `${TEX}amt_close_am`)')
    edit(a, '.title(`§lเลือกเครื่องราง${AMULET_FLAG}`).body("§eเลือกชิ้นที่\\nจะใส่")', '.title(`§lเลือกเครื่องราง${PICKER_FLAG}`).body("§eเลือกชิ้นที่\\nจะใส่")')
    edit(a, 'form.button(`§f${AMULETS[key].short}\\n§7แตะเพื่อใส่`', 'form.button(`§f${AMULETS[key].short}\\n§eแตะเพื่อใส่`')
    edit(a, 'form.button("", `${TEX}amt_back`)', 'form.button("§lกลับ", `${TEX}amt_back_am`)')

    # books: page number in the paper's ink colour
    edit(f'{sd}/books.js', '\\n\\n§8— หน้า ${page + 1}/${pages.length} —', '\\n\\n§r§l— หน้า ${page + 1}/${pages.length} —')

    # settings item: settings skin
    st = f'{sd}/settings.js'
    ss = open(st, encoding='utf-8').read()
    n0 = len(re.findall(r'\.title\("(§l[^"]*)"\)', ss))
    ss = re.sub(r'\.title\("(§l[^"]*)"\)', lambda mm: f'.title("{mm.group(1)}{SETTINGS_FLAG}")', ss)
    assert n0 >= 3, n0
    ss = ss.replace('"§7ปิด"', '"§7ปิด"')
    open(st, 'w', encoding='utf-8').write(ss)

    # rule wand / speaker / board: horror skin, button editors
    h = f'{sd}/horror.js'
    hs = open(h, encoding='utf-8').read()
    a0, b0 = cut(hs, "// ---------------------------------------------------------------- wand screens", "// ---------------------------------------------------------------- props")
    hs = hs[:a0] + HORROR_SCREENS_JS + hs[b0:]
    a1, b1 = cut(hs, "async function editSpeaker(player, sp) {", "\nfunction pickUp(player, entity) {")
    hs = hs[:a1] + SPEAKER_JS + hs[b1:]
    old = '"ห้ามอยู่เกินเวลา (ตั้งวินาทีในช่องค่า)"'
    assert hs.count(old) == 1
    hs = hs.replace(old, '"ห้ามอยู่ในโซนเกินเวลา"')
    old = 'new ModalFormData().title("§lเขียนป้ายประกาศกฎ")'
    assert hs.count(old) == 1
    hs = hs.replace(old, 'new ModalFormData().title(`§lเขียนป้ายประกาศกฎ${HORROR_FLAG}`)')
    open(h, 'w', encoding='utf-8').write(hs)


def build(bp, rp, log):
    theme_art(rp)
    wjson(f'{rp}/ui/succubi_ui.json', ui_theme_json())
    defs = json.load(open(f'{rp}/ui/_ui_defs.json'))
    if 'ui/succubi_ui.json' not in defs['ui_defs']:
        defs['ui_defs'].append('ui/succubi_ui.json')
    wjson(f'{rp}/ui/_ui_defs.json', defs)
    shop_ui(rp, log)
    amulet_ui(rp)
    wallet_ui(rp)
    paper_ui(rp)
    sfp = f'{rp}/ui/server_form.json'
    sf = server_form_overrides(json.load(open(sfp)))
    sf['long_form']['controls'].append({"succubi_amulet_picker@succubi_shops.amulet_picker_panel": {"bindings": [
        {"binding_name": "#title_text"},
        {"binding_type": "view", "source_property_name": has(PICKER_FLAG), "target_property_name": "#visible"}]}})
    wjson(sfp, sf)
    scripts(bp)
    log('v1.0.18: UI renovation (fonts, contrast, 3-column shops, themed screens)')
