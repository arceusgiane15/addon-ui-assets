"""Kiosk shops merged into Succubi Server: right-click menu with a HUD skin per shop."""
import json, os, shutil
from PIL import Image
import shop_art
from data import SHOPS, FOODS, FOOD_BY_KEY, SUCCUBI
from build_food import wjson, lore

KIOSK = 'kiosk'
KIOSKS = ['chicken_kiosk', 'fried_insects_kiosk', 'haruto_tea_kiosk', 'omelette_kiosk', 'ramen_kiosk', 'somtum_kiosk']


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def kiosk_entity(name):
    d = json.load(open(f'{KIOSK}/kiosk_shops_BP/entities/{name}.json'))
    comps = d['minecraft:entity']['components']
    # the kiosk was a chest (right-click opened a 27 slot inventory): it is a shop counter now
    for k in ('minecraft:inventory', 'minecraft:is_chested', 'minecraft:tameable', 'minecraft:is_tamed', 'minecraft:rideable'):
        comps.pop(k, None)
    comps['minecraft:type_family']['family'] = ['kiosk', 'succubi_shop', 'structure', 'inanimate']
    dismantle = comps['minecraft:interact']['interactions'][0]
    comps['minecraft:interact']['interactions'] = [
        dismantle,
        {"on_interact": {"filters": {"all_of": [
            {"test": "is_family", "subject": "other", "value": "player"},
            {"test": "is_sneaking", "subject": "other", "value": False}]}},
         "interact_text": "action.interact.succubi_shop"}]
    return d


def kiosk_item(name):
    return {"format_version": "1.21.0", "minecraft:item": {
        "description": {"identifier": f"kiosk:{name}", "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:display_name": {"value": f"item.kiosk:{name}.name"},
            "minecraft:icon": f"kiosk_{name}",
            "minecraft:max_stack_size": 1,
            "minecraft:entity_placer": {"entity": f"kiosk:{name}"}}}}


def merge_kiosks(bp, rp, item_tex, log):
    for n in KIOSKS:
        wjson(f'{bp}/entities/kiosk/{n}.json', kiosk_entity(n))
        wjson(f'{bp}/items/kiosk/{n}.json', kiosk_item(n))
        copy(f'{KIOSK}/kiosk_shops_BP/loot_tables/kiosks/{n}.json', f'{bp}/loot_tables/kiosks/{n}.json')
        copy(f'{KIOSK}/kiosk_shops_RP/entity/{n}.entity.json', f'{rp}/entity/kiosk/{n}.entity.json')
        copy(f'{KIOSK}/kiosk_shops_RP/models/entity/{n}.geo.json', f'{rp}/models/entity/kiosk/{n}.geo.json')
        copy(f'{KIOSK}/kiosk_shops_RP/textures/entity/kiosks/{n}_atlas.png', f'{rp}/textures/entity/kiosks/{n}_atlas.png')
        copy(f'{KIOSK}/kiosk_shops_RP/textures/items/{n}.png', f'{rp}/textures/items/kiosk/{n}.png')
        item_tex[f'kiosk_{n}'] = {"textures": f'textures/items/kiosk/{n}'}
    copy(f'{KIOSK}/kiosk_shops_RP/animations/haruto_tea_kiosk.animation.json', f'{rp}/animations/kiosk/haruto_tea_kiosk.animation.json')
    for s in ('tea_announcement.ogg', 'tea_bgm_01.ogg'):
        copy(f'{KIOSK}/kiosk_shops_RP/sounds/kiosk/{s}', f'{rp}/sounds/kiosk/{s}')
    sd_path = f'{rp}/sounds/sound_definitions.json'
    sd = json.load(open(sd_path))
    sd['sound_definitions'].update(json.load(open(f'{KIOSK}/kiosk_shops_RP/sounds/sound_definitions.json'))['sound_definitions'])
    wjson(sd_path, sd)
    log('kiosks merged')


def vending_placers(bp, rp, item_tex, log):
    """the vending machines become placeable items in the shop group (spawn eggs removed)"""
    for m in ('drink', 'snack'):
        ent = f'{bp}/entities/succubi_{m}_vending_machine.json'
        d = json.load(open(ent)); d['minecraft:entity']['description']['is_spawnable'] = False; wjson(ent, d)
        ident = f'succubi:{m}_vending_machine_placer'
        wjson(f'{bp}/items/succubi/{m}_vending_machine_placer.json', {"format_version": "1.21.0", "minecraft:item": {
            "description": {"identifier": ident, "menu_category": {"category": "equipment"}},
            "components": {"minecraft:display_name": {"value": f"item.{ident}.name"},
                           "minecraft:icon": f"succubi_{m}_vending_machine_placer",
                           "minecraft:max_stack_size": 1,
                           "minecraft:entity_placer": {"entity": f"succubi:{m}_vending_machine"}}}})
        item_tex[f'succubi_{m}_vending_machine_placer'] = {"textures": f'textures/items/succubi/{m}_vending_machine_placer'}
    log('vending machine placers added')


def menu_products():
    """menu per shop in the same shape as products.js entries"""
    menus = {}
    for s in SHOPS:
        items = []
        for k in s['menu']:
            if k.startswith('s:'):
                ident, price = SUCCUBI[k[2:]]
                items.append({"ref": ident, "key": k[2:], "price": price})
            else:
                items.append({"ref": f"food:{k}", "key": k, "price": FOOD_BY_KEY[k]['price']})
        menus[s['key']] = items
    return menus


def shop_ui(rp, log):
    tex_dir = f'{rp}/textures/ui/succubi_shops'
    os.makedirs(tex_dir, exist_ok=True)
    panels = {"namespace": "succubi_shops"}
    menus = menu_products()
    for s in SHOPS:
        kiosk_icon = Image.open(f'{KIOSK}/kiosk_shops_RP/textures/items/{s["entity"].split(":")[1]}.png')
        shop_art.background(s['key'], s['theme'], kiosk_icon).save(f'{tex_dir}/bg_{s["key"]}.png', optimize=True)
        for it in menus[s['key']]:
            if it['ref'].startswith('food:'):
                icon = Image.open(f'{rp}/textures/items/food/{it["key"]}.png')
            else:
                icon = Image.open(f'{rp}/textures/items/succubi_food/{it["ref"].split(":")[1]}.png')
            shop_art.card(s['theme'], icon).save(f'{tex_dir}/p_{s["key"]}_{it["key"]}.png')
            shop_art.card(s['theme'], icon, off=True).save(f'{tex_dir}/p_{s["key"]}_{it["key"]}_off.png')
        lcd = [c / 255 for c in shop_art.lighten(s['theme']['accent'], 0.35)]
        panels[f'{s["key"]}_panel'] = {
            "type": "panel", "size": [280, 180], "layer": 2,
            "controls": [
                {"bg": {"type": "image", "texture": f"textures/ui/succubi_shops/bg_{s['key']}", "size": ["100%", "100%"], "layer": 1}},
                {"title": {"type": "label", "text": f"§l{s['title']}", "color": [1, 1, 1], "localize": False, "shadow": True,
                           "anchor_from": "top_left", "anchor_to": "top_left", "offset": [12, 7], "layer": 5}},
                {"lcd": {"type": "label", "text": "#form_text", "color": [round(x, 3) for x in lcd], "localize": False, "shadow": False,
                         "anchor_from": "top_left", "anchor_to": "top_left", "offset": [221, 26], "layer": 5,
                         "bindings": [{"binding_name": "#form_text"}], "size": [47, "default"]}},
                {"slots": {"type": "grid", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [9, 21], "size": [200, 150],
                           "grid_dimensions": [4, 5], "grid_item_template": "succubi_vending.cell", "collection_name": "form_buttons", "layer": 5}}]}
    wjson(f'{rp}/ui/succubi_shops.json', panels)

    defs = json.load(open(f'{rp}/ui/_ui_defs.json'))
    if 'ui/succubi_shops.json' not in defs['ui_defs']:
        defs['ui_defs'].append('ui/succubi_shops.json')
    wjson(f'{rp}/ui/_ui_defs.json', defs)

    sf_path = f'{rp}/ui/server_form.json'
    sf = json.load(open(sf_path))
    controls = sf['long_form']['controls']
    default = controls[0]['long_form@common_dialogs.main_panel_no_buttons']['bindings'][1]
    flags = ['§0§9§8§7', '§0§9§8§6', '§0§9§8§5', '§0§9§8§4', '§0§9§8§3'] + [s['flag'] for s in SHOPS]
    default['source_property_name'] = '(' + ' and '.join(f"((#title_text - '{f}') = #title_text)" for f in flags) + ')'
    names = {list(c)[0] for c in controls}
    for s in SHOPS:
        cname = f'succubi_shop_{s["key"]}@succubi_shops.{s["key"]}_panel'
        if cname in names:
            continue
        controls.append({cname: {"bindings": [{"binding_name": "#title_text"},
                                              {"binding_type": "view", "source_property_name": f"(not ((#title_text - '{s['flag']}') = #title_text))",
                                               "target_property_name": "#visible"}]}})
    wjson(sf_path, sf)
    log('shop UI: %d panels' % len(SHOPS))
    return menus
