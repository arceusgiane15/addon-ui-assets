"""Sanity (สติ): HUD ring, fog, strange events, shadow figure, teddy bear."""
import json, os
from PIL import Image, ImageDraw
import boxkit, recolor
from build_food import wjson
from build_scripts import edit
from build_extra import item_geometry, attachable
from sanity_js import SANITY_JS
from data_extra import solid, per_face, label, centred

# how much sanity each thing gives when finished (eaten / drunk)
SANITY = {
    # kiosk dishes
    "food:somtum_plate": 8, "food:somtum_pla_ra": 8, "food:larb_plate": 8, "food:kratip_rice": 2, "food:kaeng_som": 10,
    "food:omelette_rice": 10, "food:fried_chicken_bucket": 20, "food:spicy_chicken_bucket": 20, "food:moo_ping": 8,
    "food:ramen_bowl": 15, "food:tomyum_ramen": 16, "food:tonkotsu_ramen": 18, "food:fried_insects_plate": 6,
    "food:spicy_insects_plate": 7, "food:boba_tea": 12, "food:thai_tea_boba": 12, "food:matcha_boba": 12,
    "food:cocoa_boba": 12, "food:kratom_bottle": 15,
    # pharmacy / store
    "succubi:med_paracetamol": 3, "succubi:med_cough_syrup": 2, "succubi:med_inhaler": 8, "succubi:med_balm": 6,
    "succubi:med_plaster": 2, "succubi:med_ors": 1, "succubi:med_vitamin_c": 3, "succubi:med_motion": 3, "succubi:med_antacid": 2,
    "succubi:snack_peanuts": 3, "succubi:drink_milk": 3, "succubi:drink_m150": 4, "succubi:onigiri_tuna": 5,
    "succubi:onigiri_salmon": 6, "succubi:sandwich_ham": 5, "succubi:toastie_ham": 7, "succubi:dim_sum": 6, "succubi:bao": 5,
    "succubi:sausage": 5, "succubi:rice_krapow": 9, "succubi:rice_garlic_pork": 9, "succubi:boiled_eggs": 3,
    "succubi:snack_chips_nori": 4, "succubi:snack_chips_bbq": 5,
    # vending machines
    "succubi:drink_water_bottle": 1, "succubi:drink_pepsi": 3, "succubi:drink_fanta_orange": 3, "succubi:drink_sprite": 3,
    "succubi:drink_coca_cola": 3, "succubi:drink_schweppes": 3, "succubi:drink_boss_coffee": 4, "succubi:drink_pocari_sweat": 2,
    "succubi:drink_redbull": 4, "succubi:drink_green_tea": 5, "succubi:drink_monster_energy": 5,
    "succubi:snack_wafer": 3, "succubi:snack_jelly": 3, "succubi:snack_prawn_crackers": 3, "succubi:snack_cream_bun": 4,
    "succubi:snack_chips": 4, "succubi:snack_fish_strips": 3, "succubi:snack_cookies": 5, "succubi:snack_biscuit_sticks": 5,
    "succubi:snack_seaweed": 4, "succubi:snack_chocolate": 6, "succubi:snack_chips_tube": 5,
    # vanilla
    "minecraft:cake": 10, "minecraft:cookie": 3, "minecraft:pumpkin_pie": 6, "minecraft:golden_apple": 8,
    "minecraft:enchanted_golden_apple": 20, "minecraft:honey_bottle": 4, "minecraft:milk_bucket": 3, "minecraft:baked_potato": 2,
    "minecraft:cooked_beef": 2, "minecraft:cooked_porkchop": 2, "minecraft:cooked_chicken": 2, "minecraft:bread": 1,
    "minecraft:rotten_flesh": -5, "minecraft:spider_eye": -6, "minecraft:poisonous_potato": -4, "minecraft:pufferfish": -8,
}

FOGS = {
    "succubi:sanity_fog_1": (18, 70, "#1B1226"),
    "succubi:sanity_fog_2": (7, 40, "#120B1A"),
    "succubi:sanity_fog_3": (2, 20, "#07040B"),
    "succubi:red_fog": (4, 45, "#5A0D0D"),
}


def shadow_model():
    black = (8, 6, 10)
    eyes = label(black, icon=lambda d, w, h: (d.rectangle([w * 0.18, h * 0.42, w * 0.38, h * 0.56], fill=(230, 230, 240, 255)),
                                              d.rectangle([w * 0.62, h * 0.42, w * 0.82, h * 0.56], fill=(230, 230, 240, 255))))
    return [centred(4, 12, 2, y=0, x=-2.2, paint=solid(black)), centred(4, 12, 2, y=0, x=2.2, paint=solid(black)),
            centred(8.5, 13, 4, y=12, paint=solid(black)),
            centred(3.5, 14, 3.5, y=11, x=-6.2, paint=solid(black)), centred(3.5, 14, 3.5, y=11, x=6.2, paint=solid(black)),
            centred(8, 8, 8, y=25, paint=per_face(solid(black), north=eyes))]


def hud(rp, log):
    tex = f'{rp}/textures/ui/succubi_hud'
    recolor.RECIPES['_violet'] = dict(hue=(0, 360), smin=0.2, fn=lambda h, s, v: (h * 0 + 272, s * 0.85, v))
    for i in range(1, 21):
        recolor.apply(Image.open(f'{tex}/ring_health_{i:02d}.png'), '_violet', atlas=False).save(f'{tex}/ring_sanity_{i:02d}.png')
    icon = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(icon)   # an eye
    d.ellipse([20, 70, 236, 186], fill=(255, 255, 255, 255))
    d.ellipse([88, 88, 168, 168], fill=(120, 70, 190, 255)); d.ellipse([112, 112, 144, 144], fill=(20, 12, 30, 255))
    icon.resize((64, 64), Image.LANCZOS).save(f'{tex}/icon_sanity.png')

    p = f'{rp}/ui/succubi_hud.json'
    h = json.load(open(p))
    root = h['hud_root']
    thirst = next(c for c in root['controls'] if 'gauge_thirst' in c)['gauge_thirst']
    s = json.dumps(thirst).replace('ring_thirst_', 'ring_sanity_').replace('icon_thirst', 'icon_sanity')
    import re
    s = re.sub(r"'T(\d\d)'", r"'S\1'", s)
    sanity = json.loads(s); sanity['offset'] = [72, 0]
    idx = next(i for i, c in enumerate(root['controls']) if 'gauge_thirst' in c)
    root['controls'].insert(idx + 1, {"gauge_sanity": sanity})
    for c in root['controls']:
        if 'money' in c:
            c['money']['offset'] = [c['money']['offset'][0] + 24, c['money']['offset'][1]]
    root['size'] = [root['size'][0] + 24, root['size'][1]]
    wjson(p, h)
    log('HUD: sanity ring added')


def build(bp, rp, item_tex, log):
    sd = f'{bp}/scripts/succubi'
    # values + lore lines
    open(f'{sd}/sanity_values.js', 'w', encoding='utf-8').write(
        "// GENERATED - sanity gained when an item is finished (negative = loses sanity)\n"
        f"export const SANITY_BY_ID = {json.dumps(SANITY, indent=2)};\n"
        'export const TEDDY_ID = "succubi:teddy_bear";\n')
    open(f'{sd}/sanity.js', 'w', encoding='utf-8').write(SANITY_JS)
    pj = f'{sd}/products.js'
    js = open(pj, encoding='utf-8').read()
    js = 'import { SANITY_BY_ID } from "./sanity_values.js";\n' + js
    anchor = "export const PRODUCT_BY_ID = new Map("
    i = js.index(anchor); j = js.index('\n', i)
    js = js[:j + 1] + ('\n// sanity line in every product description\n'
                       'for (const p of PRODUCT_BY_ID.values()) {\n'
                       '  const s = SANITY_BY_ID[p.id];\n'
                       '  if (s && !p.lore.some((l) => l.includes("สติ"))) p.lore = [...p.lore, s > 0 ? `§5สติ §f+${s}` : `§4สติ §f${s}`];\n'
                       '}\n') + js[j + 1:]
    open(pj, 'w', encoding='utf-8').write(js)

    # HUD payload gets S<steps>
    hj = f'{sd}/hud.js'
    edit(hj, 'import { getThirst, THIRST_MAX } from "./thirst.js";\n', 'import { getThirst, THIRST_MAX } from "./thirst.js";\nimport { getSanity, SANITY_MAX } from "./sanity.js";\n')
    edit(hj, "H${pad2(toSteps(hp, maxHp))}`;", "H${pad2(toSteps(hp, maxHp))}S${pad2(toSteps(getSanity(player), SANITY_MAX))}`;")
    edit(hj, '//   title    = "shud:F<food>T<thirst>H<health>"  (each 00-20, 5% per step)',
         '//   title    = "shud:F<food>T<thirst>H<health>S<sanity>"  (each 00-20, 5% per step)')
    m = f'{bp}/scripts/main.js'
    edit(m, 'import { initKioskAudio } from "./succubi/kiosk_audio.js";\n', 'import { initKioskAudio } from "./succubi/kiosk_audio.js";\nimport { initSanity } from "./succubi/sanity.js";\n')
    edit(m, "initKioskAudio();\n", "initKioskAudio();\ninitSanity();\n")
    hud(rp, log)

    # fogs
    for ident, (a, b, col) in FOGS.items():
        wjson(f'{rp}/fogs/{ident.split(":")[1]}.json', {"format_version": "1.16.100", "minecraft:fog_settings": {
            "description": {"identifier": ident},
            "distance": {"air": {"fog_start": a, "fog_end": b, "fog_color": col, "render_distance_type": "fixed"}}}})

    # shadow figure
    parts = shadow_model()
    cubes, atlas, size = boxkit.build(parts, ppu=4)
    atlas.save(f'{rp}/textures/entity/succubi_shops/shadow_figure.png')
    wjson(f'{rp}/models/entity/succubi_shadow_figure.geo.json', {"format_version": "1.16.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.succubi_shadow_figure", "texture_width": size[0], "texture_height": size[1],
                        "visible_bounds_width": 2, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
        "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": cubes}]}]})
    wjson(f'{rp}/entity/succubi_shadow_figure.entity.json', {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": "succubi:shadow_figure", "materials": {"default": "entity_alphatest"},
        "textures": {"default": "textures/entity/succubi_shops/shadow_figure"}, "geometry": {"default": "geometry.succubi_shadow_figure"},
        "render_controllers": ["controller.render.succubi_money"]}}})
    wjson(f'{bp}/entities/succubi_shadow_figure.json', {"format_version": "1.20.50", "minecraft:entity": {
        "description": {"identifier": "succubi:shadow_figure", "is_spawnable": False, "is_summonable": True, "is_experimental": False},
        "components": {"minecraft:type_family": {"family": ["succubi_shadow", "inanimate"]},
                       "minecraft:collision_box": {"width": 0.6, "height": 2.0},
                       "minecraft:physics": {"has_gravity": False, "has_collision": False},
                       "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
                       "minecraft:damage_sensor": {"triggers": {"cause": "all", "deals_damage": False}},
                       "minecraft:health": {"value": 20, "max": 20}, "minecraft:fire_immune": True}}})

    log('sanity system built')


def lang_lines(th):
    return ["", "## Sanity (v1.0.13)",
            f"entity.succubi:shadow_figure.name={'???' if th else '???'}"]
