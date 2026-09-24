"""Food: 3D models from the Food Items pack rebuilt as hand-bound attachables, eat/drink poses for every food."""
import json, os, shutil, numpy as np
from PIL import Image
import pose, canon, foodpose, recolor, preview
from data import FOODS, MODELS, EFFECT_TH, ROMAN

FOOD_SRC = 'food'


def wjson(path, obj, compact=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=2)


def lore(f):
    lines = [f"§7{f['desc']}"]
    if f['food']:
        lines.append(f"§6อิ่มท้อง §f+{f['food']}")
    if f['thirst'] > 0:
        lines.append(f"§bดับกระหาย §f+{f['thirst']}")
    elif f['thirst'] < 0:
        lines.append(f"§cกระหายน้ำ §f{f['thirst']} §7(เผ็ด/เค็ม)")
    if f['effects']:
        lines.append("§d" + ", ".join(f"{EFFECT_TH[e]}{ROMAN[a]} {s}วิ" for e, s, a in f['effects']))
    return lines


# ---------------------------------------------------------------- poses / animations
def fmt(x):
    return round(float(x), 2)


def pose_anims(prefix, kind, U, F, C, pivot, scale, bone):
    """hold/eat animations (first & third person) for one bone convention"""
    P = foodpose.solve_all(kind, U, F, C, pivot, scale)
    A1, _ = pose.arm_1p()
    bob_axis = A1.T @ np.array([0.0, 1.0, 0.0])   # screen-up in the bound frame (1st person)
    anims = {}
    sc = fmt(scale)

    def side(v, i):
        # off-hand mirrors the pose (leftItem frame)
        if i == 0:
            return f"c.item_slot == 'off_hand' ? {fmt(-v)} : {fmt(v)}"
        return fmt(v)

    def rot_mirror(r):
        return [fmt(r[0]), f"c.item_slot == 'off_hand' ? {fmt(-r[1])} : {fmt(r[1])}", f"c.item_slot == 'off_hand' ? {fmt(-r[2])} : {fmt(r[2])}"]

    anims[f'animation.{prefix}.hold_tp'] = {"loop": True, "bones": {bone: {
        "rotation": rot_mirror(P['tp_hold']['rotation']),
        "position": [side(P['tp_hold']['position'][0], 0), fmt(P['tp_hold']['position'][1]), fmt(P['tp_hold']['position'][2])],
        "scale": sc}}}
    anims[f'animation.{prefix}.hold_fp'] = {"loop": True, "bones": {bone: {
        "rotation": [fmt(v) for v in P['fp_hold']['rotation']],
        "position": [fmt(v) for v in P['fp_hold']['position']],
        "scale": f"c.item_slot == 'off_hand' ? 0 : {sc}"}}}
    anims[f'animation.{prefix}.eat_tp'] = {"loop": True, "bones": {bone: {
        "rotation": [fmt(v) for v in P['tp_eat']['rotation']],
        "position": [fmt(v) for v in P['tp_eat']['position']],
        "scale": sc}}}
    bob = "math.sin(q.life_time * 1100) * 0.45"
    anims[f'animation.{prefix}.eat_fp'] = {"loop": True, "bones": {bone: {
        "rotation": [fmt(v) for v in P['fp_eat']['rotation']],
        "position": [f"{fmt(P['fp_eat']['position'][i])} + {bob} * {fmt(bob_axis[i])}" for i in range(3)],
        "scale": sc}}}
    return anims, P


def controller(prefix):
    eating = "c.item_slot == 'main_hand' && q.main_hand_item_use_duration > 0"
    return {f'controller.animation.{prefix}': {
        "initial_state": "hold",
        "states": {
            "hold": {"animations": [{"hold_fp": "c.is_first_person"}, {"hold_tp": "!c.is_first_person"}],
                     "transitions": [{"eat": eating}], "blend_transition": 0.12},
            "eat": {"animations": [{"eat_fp": "c.is_first_person"}, {"eat_tp": "!c.is_first_person"}],
                    "transitions": [{"hold": f"!({eating})"}], "blend_transition": 0.12}}}}


def attachable(ident, texture, geometry, prefix):
    return {"format_version": "1.10.0", "minecraft:attachable": {"description": {
        "identifier": ident,
        "materials": {"default": "entity_alphatest"},
        "textures": {"default": texture},
        "geometry": {"default": geometry},
        "animations": {"hold_fp": f"animation.{prefix}.hold_fp", "hold_tp": f"animation.{prefix}.hold_tp",
                       "eat_fp": f"animation.{prefix}.eat_fp", "eat_tp": f"animation.{prefix}.eat_tp",
                       "wield": f"controller.animation.{prefix}"},
        "scripts": {"animate": ["wield"]},
        "render_controllers": ["controller.render.succubi_money"]}}}


# ---------------------------------------------------------------- build
def build(out_bp, out_rp, log):
    rp_models = os.path.join(out_rp, 'models/entity/succubi_food_kiosk.geo.json')
    geos, anims, ctrls = [], {}, {}
    item_tex = {}

    # 1) one canonical geometry per base model (poses differ only by kind)
    for key, (stem, kind, size) in MODELS.items():
        g = json.load(open(f'{FOOD_SRC}/food_items_RP/models/entity/{stem}.geo.json'))['minecraft:geometry'][0]
        kw = {}
        if stem == 'moo_ping':   # sticky rice bag sits beside the skewers in the same hand
            kw = dict(offsets={'sticky_rice': [-9.5, 0.0, 2.0]})
        geos.append(canon.build(g, f'geometry.succubi_food_{key}', kind, size, **kw))
    for kind in ('plate', 'hand'):
        a, _ = pose_anims(f'succubi_food.{kind}', kind, [0, 1, 0], [0, 0, -1], pose.H0, pose.H0, 1.0, 'succubi_food')
        anims.update(a); ctrls.update(controller(f'succubi_food.{kind}'))
    wjson(rp_models, {"format_version": "1.16.0", "minecraft:geometry": geos}, compact=True)

    # 2) textures, attachables, items
    for f in FOODS:
        key, model = f['key'], f['model']
        stem, kind, _ = MODELS[model]
        atlas = Image.open(f'{FOOD_SRC}/food_items_RP/textures/entity/food/{stem}_atlas.png')
        icon = Image.open(f'{FOOD_SRC}/food_items_RP/textures/items/{stem}.png')
        if f.get('recolor'):
            atlas = recolor.apply(atlas, f['recolor'])
            icon = recolor.apply(icon, f['recolor'], atlas=False)
        tex_rel = f'textures/entity/food/{key}_atlas'
        os.makedirs(os.path.join(out_rp, 'textures/entity/food'), exist_ok=True)
        os.makedirs(os.path.join(out_rp, 'textures/items/food'), exist_ok=True)
        atlas.save(os.path.join(out_rp, tex_rel + '.png'), optimize=True)
        icon.save(os.path.join(out_rp, f'textures/items/food/{key}.png'))
        item_tex[f'food_{key}'] = {"textures": f'textures/items/food/{key}'}

        ident = f'food:{key}'
        wjson(os.path.join(out_rp, f'attachables/food/{key}.json'),
              attachable(ident, tex_rel, f'geometry.succubi_food_{model}', f'succubi_food.{kind}'))

        comps = {
            "minecraft:display_name": {"value": f"item.{ident}.name"},
            "minecraft:icon": f"food_{key}",
            "minecraft:max_stack_size": 16,
            "minecraft:food": {"nutrition": f['food'], "saturation_modifier": f['sat'], "can_always_eat": f['use'] == 'drink' or f['food'] <= 3},
            "minecraft:use_animation": f['use'],
            "minecraft:use_modifiers": {"use_duration": 1.6 if f['use'] == 'eat' else 1.4, "movement_modifier": 0.35},
            "minecraft:tags": {"tags": ["succubi:food", "succubi:kiosk_food", "succubi:drink" if f['use'] == 'drink' else "succubi:meal"]}
        }
        wjson(os.path.join(out_bp, f'items/food/kiosk/{key}.json'), {"format_version": "1.21.0", "minecraft:item": {
            "description": {"identifier": ident, "menu_category": {"category": "equipment"}}, "components": comps}})
    log(f'foods: {len(FOODS)} items, {len(MODELS)} models')

    # 3) Succubi vending food: same eat/drink handling (their geometry: root "succubi_money", child rotated -90 on X)
    base = os.path.join(out_rp, 'models/entity')
    for fname in ('succubi_food_drinks.geo.json', 'succubi_food_snacks.geo.json'):
        d = json.load(open(os.path.join(base, fname)))
        g = d['minecraft:geometry'][1 if 'drinks' in fname else 4]
        tex_name = g['description']['identifier'].replace('geometry.succubi_', '')
        tex = Image.open(os.path.join(out_rp, f'textures/models/succubi_food/{tex_name}.png')).convert('RGBA')
        fs = preview.geo_faces(g, tex)
        allp = np.concatenate([p for p, c in fs]); C = (allp.min(0) + allp.max(0)) / 2
        pivot = np.array(g['bones'][0]['pivot'], float)
        prefix = 'succubi_food.vending_' + ('drink' if 'drinks' in fname else 'snack')
        a, _ = pose_anims(prefix, 'hand', [0, -1, 0], [0, 0, 1], C, pivot, 0.4, 'succubi_money')
        anims.update(a); ctrls.update(controller(prefix))
    for fn in sorted(os.listdir(os.path.join(out_rp, 'attachables/succubi_food'))):
        path = os.path.join(out_rp, 'attachables/succubi_food', fn)
        d = json.load(open(path)); desc = d['minecraft:attachable']['description']
        prefix = 'succubi_food.vending_' + ('drink' if fn.startswith('drink_') else 'snack')
        new = attachable(desc['identifier'], desc['textures']['default'], desc['geometry']['default'], prefix)
        wjson(path, new)
    log('vending food attachables re-posed')

    wjson(os.path.join(out_rp, 'animations/succubi_food.animation.json'), {"format_version": "1.8.0", "animations": anims})
    wjson(os.path.join(out_rp, 'animation_controllers/succubi_food.controller.json'),
          {"format_version": "1.10.0", "animation_controllers": ctrls})
    return item_tex
