"""Pharmacy stall + convenience-store shelves: models, items, shop screens, scripts."""
import json, os
import numpy as np
from PIL import Image
import boxkit, pose, shop_art, recolor, build_shop
from build_food import wjson
from data import EFFECT_TH, ROMAN
from data_extra import EXTRA, CHIP_FLAVOURS, SHOPS_EXTRA
from stands import STANDS
from build_scripts import edit

ITEM_SCALE = 1.2
CURE_TH = {"poison": "พิษ", "nausea": "คลื่นไส้", "weakness": "อ่อนแรง", "slowness": "เชื่องช้า", "blindness": "ตาพร่า",
           "darkness": "มืดมัว", "mining_fatigue": "เหนื่อยล้า", "hunger": "หิวโซ"}


def lore(f):
    L = [f"§7{f['desc']}"]
    if f.get('heal'):
        L.append(f"§aฟื้นเลือดทันที §f+{f['heal']}")
    if f.get('food'):
        L.append(f"§6อิ่มท้อง §f+{f['food']}")
    if f.get('thirst', 0) > 0:
        L.append(f"§bดับกระหาย §f+{f['thirst']}")
    elif f.get('thirst', 0) < 0:
        L.append(f"§cกระหายน้ำ §f{f['thirst']} §7(เค็ม/เผ็ด)")
    if f.get('effects'):
        L.append("§d" + ", ".join(f"{EFFECT_TH[e]}{ROMAN[a]} {s}วิ" for e, s, a in f['effects']))
    if f.get('cure'):
        L.append("§eหายจาก: " + ", ".join(CURE_TH.get(c, c) for c in f['cure']))
    return L


def product(f, ident):
    return {"key": f['key'], "id": ident, "name": f['name'], "price": f['price'], "food": f.get('food', 0),
            "saturation": f.get('sat', 0), "thirst": f.get('thirst', 0),
            "effects": [{"effect": e, "seconds": s, "amplifier": a} for e, s, a in f.get('effects', [])],
            "cure": f.get('cure', []), "heal": f.get('heal', 0), "lore": lore(f)}


def item_json(ident, icon, f, use, dur):
    return {"format_version": "1.21.0", "minecraft:item": {
        "description": {"identifier": ident, "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:display_name": {"value": f"item.{ident}.name"},
            "minecraft:icon": icon,
            "minecraft:max_stack_size": 16,
            "minecraft:food": {"nutrition": f.get('food', 0), "saturation_modifier": f.get('sat', 0), "can_always_eat": True},
            "minecraft:use_animation": use,
            "minecraft:use_modifiers": {"use_duration": dur, "movement_modifier": 0.35},
            "minecraft:tags": {"tags": ["succubi:food"] + (["succubi:medicine"] if f.get('group') == 'medical' else [])}}}}


def attachable(ident, tex, geo, prefix):
    return {"format_version": "1.10.0", "minecraft:attachable": {"description": {
        "identifier": ident, "materials": {"default": "entity_alphatest"}, "textures": {"default": tex}, "geometry": {"default": geo},
        "animations": {"hold_fp": f"animation.{prefix}.hold_fp", "hold_tp": f"animation.{prefix}.hold_tp",
                       "eat_fp": f"animation.{prefix}.eat_fp", "eat_tp": f"animation.{prefix}.eat_tp", "wield": f"controller.animation.{prefix}"},
        "scripts": {"animate": ["wield"]}, "render_controllers": ["controller.render.succubi_money"]}}}


def item_geometry(ident, parts, kind, tex_size, cubes):
    P = np.array([[c['origin'][i] + k * c['size'][i] for i in range(3)] for c in cubes for k in (0, 1)])
    mn, mx = P.min(0), P.max(0)
    grip = np.array([(mn[0] + mx[0]) / 2, mn[1] if kind == 'plate' else mn[1] + 0.3 * (mx[1] - mn[1]), (mn[2] + mx[2]) / 2])
    out = []
    for c in cubes:
        c = dict(c)
        c['origin'] = [round(float((c['origin'][i] - grip[i]) * ITEM_SCALE + pose.H0[i]), 4) for i in range(3)]
        c['size'] = [round(v * ITEM_SCALE, 4) for v in c['size']]
        if 'pivot' in c:
            c['pivot'] = [round(float((c['pivot'][i] - grip[i]) * ITEM_SCALE + pose.H0[i]), 4) for i in range(3)]
        out.append(c)
    H0 = [round(float(v), 4) for v in pose.H0]
    return {"description": {"identifier": ident, "texture_width": tex_size[0], "texture_height": tex_size[1],
                            "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]},
            "bones": [{"name": "succubi_food", "pivot": H0, "binding": "q.item_slot_to_bone_name(c.item_slot)"},
                      {"name": "succubi_food_model", "parent": "succubi_food", "pivot": H0, "cubes": out}]}


def icon_from(img, size=64):
    return img.resize((size, size), Image.LANCZOS)


def build_items(bp, rp, item_tex, log):
    geos, products = [], []
    for f in EXTRA:
        key, ident = f['key'], f"succubi:{f['key']}"
        parts = f['model']()
        cubes, atlas, size = boxkit.build(parts, ppu=16)
        os.makedirs(f'{rp}/textures/entity/extra', exist_ok=True); os.makedirs(f'{rp}/textures/items/extra', exist_ok=True)
        atlas.save(f'{rp}/textures/entity/extra/{key}.png')
        icon_from(boxkit.render(parts, 256, ppu=16)).save(f'{rp}/textures/items/extra/{key}.png')
        item_tex[f'succubi_{key}'] = {"textures": f'textures/items/extra/{key}'}
        geos.append(item_geometry(f'geometry.succubi_extra_{key}', parts, f['kind'], size, cubes))
        wjson(f'{rp}/attachables/extra/{key}.json', attachable(ident, f'textures/entity/extra/{key}', f'geometry.succubi_extra_{key}', f'succubi_food.{f["kind"]}'))
        dur = 1.0 if f['group'] == 'medical' else 1.6
        wjson(f'{bp}/items/extra/{key}.json', item_json(ident, f'succubi_{key}', f, f['use'], dur))
        products.append(product(f, ident))
    wjson(f'{rp}/models/entity/succubi_extra_items.geo.json', {"format_version": "1.16.0", "minecraft:geometry": geos})

    # chip flavours: recoloured Succubi chips bag
    base_item = json.load(open(f'{bp}/items/succubi_food/snack_chips.json'))
    for f in CHIP_FLAVOURS:
        key, ident = f['key'], f"succubi:{f['key']}"
        recolor.RECIPES['_chips'] = dict(hue=(30, 70), smin=0.35, fn=lambda h, s, v, hue=f['hue']: (h * 0 + hue, s, v * 0.95))
        tex = recolor.apply(Image.open(f'{rp}/textures/models/succubi_food/snack_chips.png'), '_chips', atlas=False)
        tex.save(f'{rp}/textures/models/succubi_food/{key}.png')
        icon = recolor.apply(Image.open(f'{rp}/textures/items/succubi_food/snack_chips.png'), '_chips', atlas=False)
        os.makedirs(f'{rp}/textures/items/extra', exist_ok=True)
        icon.save(f'{rp}/textures/items/extra/{key}.png')
        item_tex[f'succubi_{key}'] = {"textures": f'textures/items/extra/{key}'}
        wjson(f'{rp}/attachables/extra/{key}.json', attachable(ident, f'textures/models/succubi_food/{key}', 'geometry.succubi_snack_chips', 'succubi_food.vending_snack'))
        it = json.loads(json.dumps(base_item))
        it['minecraft:item']['description']['identifier'] = ident
        c = it['minecraft:item']['components']
        c['minecraft:display_name'] = {"value": f"item.{ident}.name"}; c['minecraft:icon'] = f'succubi_{key}'
        c['minecraft:food'] = {"nutrition": f['food'], "saturation_modifier": f['sat']}
        wjson(f'{bp}/items/extra/{key}.json', it)
        products.append(product(dict(f, effects=[], cure=[], heal=0), ident))
    log(f'extra items: {len(EXTRA)} + {len(CHIP_FLAVOURS)} chip flavours')
    return products


def stand_entity(ident):
    short = ident.split(':')[1]
    return {"format_version": "1.20.50", "minecraft:entity": {
        "description": {"identifier": ident, "is_spawnable": False, "is_summonable": True, "is_experimental": False},
        "components": {
            "minecraft:type_family": {"family": ["succubi_shop", "structure", "inanimate"]},
            "minecraft:collision_box": {"width": STANDS[ident]['collision'][0], "height": STANDS[ident]['collision'][1]},
            "minecraft:physics": {"has_gravity": True, "has_collision": True},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:knockback_resistance": {"value": 1.0},
            "minecraft:health": {"value": 100, "max": 100},
            "minecraft:damage_sensor": {"triggers": {"cause": "all", "deals_damage": False}},
            "minecraft:fire_immune": True, "minecraft:persistent": {},
            "minecraft:loot": {"table": f"loot_tables/succubi_shops/{short}.json"},
            "minecraft:interact": build_shop.shop_interact("action.interact.dismantle_stand")},
        "events": build_shop.SHOP_EVENTS}}


def build_stands(bp, rp, item_tex, log):
    icons = {}
    for ident, st in STANDS.items():
        short = ident.split(':')[1]
        parts = st['model']()
        cubes, atlas, size = boxkit.build(parts, ppu=8)
        os.makedirs(f'{rp}/textures/entity/succubi_shops', exist_ok=True)
        atlas.save(f'{rp}/textures/entity/succubi_shops/{short}.png')
        geo = {"description": {"identifier": f"geometry.{short}", "texture_width": size[0], "texture_height": size[1],
                               "visible_bounds_width": 4, "visible_bounds_height": 4, "visible_bounds_offset": [0, 1.5, 0]},
               "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": cubes}]}
        wjson(f'{rp}/models/entity/succubi_shops/{short}.geo.json', {"format_version": "1.16.0", "minecraft:geometry": [geo]})
        wjson(f'{rp}/entity/succubi_shops/{short}.entity.json', {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
            "identifier": ident, "materials": {"default": "entity_alphatest"}, "textures": {"default": f"textures/entity/succubi_shops/{short}"},
            "geometry": {"default": f"geometry.{short}"}, "render_controllers": ["controller.render.succubi_money"], "enable_attachables": False}}})
        wjson(f'{bp}/entities/succubi_shops/{short}.json', stand_entity(ident))
        wjson(f'{bp}/loot_tables/succubi_shops/{short}.json', {"pools": [{"rolls": 1, "entries": [{"type": "item", "name": f"{ident}_placer", "weight": 1}]}]})
        wjson(f'{bp}/items/succubi/{short}_placer.json', {"format_version": "1.21.0", "minecraft:item": {
            "description": {"identifier": f"{ident}_placer", "menu_category": {"category": "equipment"}},
            "components": {"minecraft:display_name": {"value": f"item.{ident}_placer.name"}, "minecraft:icon": f"succubi_{short}_placer",
                           "minecraft:max_stack_size": 1, "minecraft:entity_placer": {"entity": ident}}}})
        big = boxkit.render(parts, 256, ppu=8)
        icons[ident] = big
        big.resize((64, 64), Image.LANCZOS).save(f'{rp}/textures/items/succubi/{short}_placer.png')
        item_tex[f'succubi_{short}_placer'] = {"textures": f'textures/items/succubi/{short}_placer'}
    log(f'stands: {len(STANDS)}')
    return icons


def card_icon(rp, entry):
    kind, rest = entry.split(':', 1)
    if kind == 'x' or kind == 'c':
        return Image.open(f'{rp}/textures/items/extra/{rest}.png'), rest
    if kind == 'v':   # vending products are keyed without their drink_/snack_ prefix
        return Image.open(f'{rp}/textures/items/succubi_food/{rest}.png'), rest.split('_', 1)[1]
    ns, name, price = rest.split(':')
    return Image.open(f'{rp}/textures/items/{name}.png'), name


def build_shop_ui(rp, stand_icons, log):
    tex_dir = f'{rp}/textures/ui/succubi_shops'
    panels = json.load(open(f'{rp}/ui/succubi_shops.json'))
    sf_path = f'{rp}/ui/server_form.json'; sf = json.load(open(sf_path))
    controls = sf['long_form']['controls']
    default = controls[0]['long_form@common_dialogs.main_panel_no_buttons']['bindings'][1]
    for s in SHOPS_EXTRA:
        shop_art.background(s['key'], s['theme'], stand_icons[s['entity']], rows=s['rows']).save(f'{tex_dir}/bg_{s["key"]}.png', optimize=True)
        for entry in s['menu']:
            icon, key = card_icon(rp, entry)
            shop_art.card(s['theme'], icon).save(f'{tex_dir}/p_{s["key"]}_{key}.png')
            shop_art.card(s['theme'], icon, off=True).save(f'{tex_dir}/p_{s["key"]}_{key}_off.png')
        h = 180 + 30 * (s['rows'] - 5)
        lcd = [c / 255 for c in shop_art.lighten(s['theme']['accent'], 0.35)]
        panels[f'{s["key"]}_panel'] = {"type": "panel", "size": [280, h], "layer": 2, "controls": [
            {"bg": {"type": "image", "texture": f"textures/ui/succubi_shops/bg_{s['key']}", "size": ["100%", "100%"], "layer": 1}},
            {"title": {"type": "label", "text": f"§l{s['title']}", "color": [1, 1, 1], "localize": False, "shadow": True,
                       "anchor_from": "top_left", "anchor_to": "top_left", "offset": [12, 7], "layer": 5}},
            {"lcd": {"type": "label", "text": "#form_text", "color": [round(x, 3) for x in lcd], "localize": False, "shadow": False,
                     "anchor_from": "top_left", "anchor_to": "top_left", "offset": [221, 26], "layer": 5,
                     "bindings": [{"binding_name": "#form_text"}], "size": [47, "default"]}},
            {"slots": {"type": "grid", "anchor_from": "top_left", "anchor_to": "top_left", "offset": [9, 21], "size": [200, 30 * s['rows']],
                       "grid_dimensions": [4, s['rows']], "grid_item_template": "succubi_vending.cell", "collection_name": "form_buttons", "layer": 5}}]}
        default['source_property_name'] = default['source_property_name'][:-1] + f" and ((#title_text - '{s['flag']}') = #title_text))"
        controls.append({f'succubi_shop_{s["key"]}@succubi_shops.{s["key"]}_panel': {"bindings": [
            {"binding_name": "#title_text"},
            {"binding_type": "view", "source_property_name": f"(not ((#title_text - '{s['flag']}') = #title_text))", "target_property_name": "#visible"}]}})
    wjson(f'{rp}/ui/succubi_shops.json', panels)
    wjson(sf_path, sf)
    log(f'extra shop screens: {len(SHOPS_EXTRA)}')


def build_scripts(bp, products, log):
    sd = f'{bp}/scripts/succubi'
    p = f'{sd}/products.js'
    js = open(p, encoding='utf-8').read()
    old = "export const PRODUCT_BY_ID = new Map([...DRINKS, ...SNACKS, ...KIOSK_FOODS].map((p) => [p.id, p]));"
    assert old in js
    menus = []
    for s in SHOPS_EXTRA:
        es = []
        for entry in s['menu']:
            kind, rest = entry.split(':', 1)
            if kind == 'k':
                ns, name, price = rest.split(':')
                es.append(f'["{ns}:{name}", {price}]')
            else:
                es.append(f'["succubi:{rest}"]')
        menus.append(f'  {s["key"]}: menu([{", ".join(es)}])')
    js = js.replace(old,
        "// GENERATED - pharmacy + convenience store goods (cure = effects removed, heal = instant health)\n"
        f"export const STORE_GOODS = {json.dumps(products, ensure_ascii=False, indent=2)};\n\n"
        "export const PRODUCT_BY_ID = new Map([...DRINKS, ...SNACKS, ...KIOSK_FOODS, ...STORE_GOODS].map((p) => [p.id, p]));\n\n"
        "// Server medical items the pharmacy also sells (their own scripts handle them)\n"
        "const MEDICAL = {\n"
        '  "kotarus:bandage_blackpowder": { key: "bandage_blackpowder", name: "ผ้าพันแผลธรรมดา" },\n'
        '  "kotarus:syringe_blackpowder": { key: "syringe_blackpowder", name: "ยาลดไข้ (เข็มฉีด)" },\n'
        '  "kotarus:medkit_blackpowder": { key: "medkit_blackpowder", name: "อุปกรณ์ชุบชีวิต" }\n'
        "};\n")
    js = js.replace("const menu = (entries) => entries.map(([id, price]) => ({ ...PRODUCT_BY_ID.get(id), price }));",
                    "const menu = (entries) =>\n  entries.map(([id, price]) => {\n    const p = PRODUCT_BY_ID.get(id) ?? { ...MEDICAL[id], id, lore: [] };\n    return { ...p, price: price ?? p.price };\n  });")
    js = js.rstrip().rstrip('};').rstrip() + ",\n" + ",\n".join(menus) + "\n};\n"
    open(p, 'w', encoding='utf-8').write(js)

    s_path = f'{sd}/shops.js'
    sj = open(s_path, encoding='utf-8').read().rstrip()
    assert sj.endswith('};')
    extra = [f'  "{s["entity"]}": {{ flag: "{s["flag"]}", title: "{s["title"]}", products: SHOP_MENUS.{s["key"]}, prefix: "{s["key"]}", tex: "textures/ui/succubi_shops/", who: "ร้าน", slots: {json.dumps(s["slots"])} }}'
             for s in SHOPS_EXTRA]
    sj = sj[:-2].rstrip() + ",\n" + ",\n".join(extra) + "\n};\n\n"
    sj += "// Stands built for this server turn to face whoever places them (the kiosks keep their own facing)\n"
    sj += "export const FACE_ON_PLACE = " + json.dumps(list(STANDS)) + ";\n"
    open(s_path, 'w', encoding='utf-8').write(sj)

    v = f'{sd}/vending.js'
    edit(v, 'import { SHOPS } from "./shops.js";', 'import { SHOPS, FACE_ON_PLACE } from "./shops.js";')
    edit(v, "    if (!MACHINES[entity?.typeId]) return;\n    system.runTimeout(",
         "    if (!MACHINES[entity?.typeId] && !FACE_ON_PLACE.includes(entity?.typeId)) return;\n    system.runTimeout(")

    # ---- opening / picking up shops: player interact event + entity event fallback
    js = open(v, encoding='utf-8').read()
    start = js.index("export function initVending() {")
    end = js.index("  // A freshly placed machine turns to face whoever placed it")
    js = js[:start] + SHOP_USE_JS + "export function initVending() {\n" + INTERACT_JS + "\n" + js[end:]
    old_hit = """    if (!MACHINES[machine?.typeId] || player?.typeId !== "minecraft:player" || !player.isSneaking) return;
    try {
      if (String(player.getGameMode?.()).toLowerCase() !== "creative") return;
      machine.remove();
      player.sendMessage("§e[ตู้] เก็บตู้ออกแล้ว");
    } catch (e) {}"""
    assert old_hit in js
    js = js.replace(old_hit, """    if (!(MACHINES[machine?.typeId] || SHOPS[machine?.typeId]) || player?.typeId !== "minecraft:player" || !player.isSneaking) return;
    try {
      if (String(player.getGameMode?.()).toLowerCase() !== "creative") return;
      pickUp(player, machine);
    } catch (e) {}""")
    open(v, 'w', encoding='utf-8').write(js)

    c = f'{sd}/consumables.js'
    edit(c, "  for (const e of product.effects) player.addEffect(e.effect, e.seconds * 20, { amplifier: e.amplifier, showParticles: true });\n",
         "  for (const e of product.effects) player.addEffect(e.effect, e.seconds * 20, { amplifier: e.amplifier, showParticles: true });\n"
         "  for (const id of product.cure ?? []) {\n    try {\n      player.removeEffect(id);\n    } catch (e) {}\n  }\n"
         "  if (product.heal > 0) {\n    const health = player.getComponent(\"minecraft:health\");\n"
         "    const max = Number(player.getDynamicProperty(\"kotarus:max_hp\")) || health?.effectiveMax || 100;\n"
         "    if (health) health.setCurrentValue(Math.min(max, health.currentValue + product.heal));\n  }\n")
    log('extra scripts updated')


def lang_lines(th):
    L = ["", "## Pharmacy & convenience store (v1.0.12)"]
    for f in EXTRA + CHIP_FLAVOURS:
        L.append(f"item.succubi:{f['key']}.name={f['name'] if th else f['en']}")
    for ident, st in STANDS.items():
        L.append(f"item.{ident}_placer.name={st['name'] if th else st['en']}")
        L.append(f"entity.{ident}.name={st['name'] if th else st['en']}")
    L.append(f"action.interact.dismantle_stand={'เก็บร้าน' if th else 'Pick up'}")
    return L


def catalog(bp):
    path = f'{bp}/item_catalog/crafting_item_catalog.json'
    d = json.load(open(path))
    for cat in d['minecraft:crafting_items_catalog']['categories']:
        for g in cat['groups']:
            name = g['group_identifier']['name']
            add = []
            if name == 'itemGroup.name.succubi:medical':
                add = [f"succubi:{f['key']}" for f in EXTRA if f['group'] == 'medical']
            elif name == 'itemGroup.name.succubi:food':
                add = [f"succubi:{f['key']}" for f in EXTRA if f['group'] == 'food'] + [f"succubi:{f['key']}" for f in CHIP_FLAVOURS]
            elif name == 'itemGroup.name.succubi:shops':
                add = [f"{i}_placer" for i in STANDS]
            g['items'] += [a for a in add if a not in g['items']]
    wjson(path, d)


def build(bp, rp, item_tex, log):
    products = build_items(bp, rp, item_tex, log)
    icons = build_stands(bp, rp, item_tex, log)
    build_shop_ui(rp, icons, log)
    build_scripts(bp, products, log)


SHOP_USE_JS = """const lastOpen = new Map(); // player id -> tick of the last shop screen, so both events don't open it twice
const alive = (e) => { try { return typeof e.isValid === "function" ? e.isValid() : e.isValid; } catch (err) { return false; } };

function openFor(player, entity) {
  const machine = MACHINES[entity?.typeId] ?? SHOPS[entity?.typeId];
  if (!machine || !player) return;
  const now = system.currentTick;
  if (now - (lastOpen.get(player.id) ?? -100) < 10) return;
  lastOpen.set(player.id, now);
  system.run(() => {
    openMachine(player, machine).catch(() => {});
  });
}

// Entity events don't say who clicked: the player looking at the shop, else the closest one
function whoUsed(entity) {
  try {
    const near = entity.dimension.getPlayers({ location: entity.location, maxDistance: 10 });
    for (const p of near) {
      try {
        if (p.getEntitiesFromViewDirection({ maxDistance: 10 }).some((hit) => hit.entity?.id === entity.id)) return p;
      } catch (e) {}
    }
    return entity.dimension.getPlayers({ location: entity.location, closest: 1, maxDistance: 10 })[0];
  } catch (e) {
    return undefined;
  }
}

// Picked-up shop goes back into the inventory as the item that places it
export function pickUp(player, entity) {
  if (!alive(entity)) return;
  const id = entity.typeId;
  const item = id.startsWith("kiosk:") ? id : `${id}_placer`;
  const where = entity.location;
  const dim = entity.dimension;
  entity.remove();
  try {
    const leftover = player?.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(item, 1));
    if (leftover || !player) dim.spawnItem(leftover ?? new ItemStack(item, 1), where);
  } catch (e) {
    try {
      dim.spawnItem(new ItemStack(item, 1), where);
    } catch (err) {}
  }
  player?.sendMessage("§e[ร้าน] เก็บร้านเข้ากระเป๋าแล้ว");
  player?.playSound("random.pop");
}

"""

INTERACT_JS = """  world.afterEvents.playerInteractWithEntity.subscribe((event) => {
    const id = event.target?.typeId;
    if (!MACHINES[id] && !SHOPS[id]) return;
    if (SHOPS[id] && event.player.isSneaking) {
      system.run(() => pickUp(event.player, event.target));
      return;
    }
    openFor(event.player, event.target);
  });

  // Same click seen through the entity's own event (works even when the interact event above is not sent)
  try {
  world.afterEvents.dataDrivenEntityTrigger.subscribe(
    (event) => {
      const entity = event.entity;
      if (!alive(entity)) return;
      const player = whoUsed(entity);
      if (event.eventId === "succubi:shop_pickup") {
        if (SHOPS[entity.typeId]) system.run(() => pickUp(player, entity));
      } else {
        openFor(player, entity);
      }
    },
    { eventTypes: ["succubi:shop_use", "succubi:shop_pickup"] }
  );
  } catch (e) {
    console.warn("[Succubi] dataDrivenEntityTrigger unavailable: " + e);
  }
"""
