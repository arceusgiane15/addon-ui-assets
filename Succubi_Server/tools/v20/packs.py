"""Per-pack generated files: manifests, player.json variants, creative catalog split, armor table."""
import copy as _copy
import json, os
from common import (rjson, wjson, VERSION, VERSION_TEXT, MIN_ENGINE, UUID,
                    CORE_BP, CORE_RP, GUNS_BP, GUNS_RP, LINK_BP)

# ------------------------------------------------------------------------------------------ manifests
def manifests(out):
    v = VERSION
    core_bp = {
        "format_version": 2,
        "header": {"name": "Succubi Server BP",
                   "description": f"Succubi Server v{VERSION_TEXT} · กระเป๋าเงิน ร้านค้า ส่วนสูง การแพทย์ หิวน้ำ ค่าสติ เรื่องสยอง (ปืนอยู่ในแพ็ค Succubi Guns)",
                   "uuid": UUID[CORE_BP][0], "version": v, "min_engine_version": MIN_ENGINE},
        "modules": [
            {"description": "Succubi Server data", "type": "data", "uuid": UUID[CORE_BP][1], "version": v},
            {"description": "Succubi Server scripts", "type": "script", "language": "javascript", "entry": "scripts/main.js",
             "uuid": UUID[CORE_BP][2], "version": v}],
        "dependencies": [
            {"uuid": UUID[CORE_RP][0], "version": v},
            {"uuid": UUID[LINK_BP][0], "version": [1, 0, 1]},
            {"module_name": "@minecraft/server", "version": "1.19.0"},
            {"module_name": "@minecraft/server-ui", "version": "1.3.0"}],
        "metadata": {"authors": ["Succubi Server"]}}
    core_rp = {
        "format_version": 2,
        "header": {"name": "Succubi Server RP",
                   "description": f"Succubi Server v{VERSION_TEXT} · โมเดล เท็กซ์เจอร์ เสียง HUD และหน้าจอ",
                   "uuid": UUID[CORE_RP][0], "version": v, "min_engine_version": MIN_ENGINE},
        "modules": [{"description": "Succubi Server resources", "type": "resources", "uuid": UUID[CORE_RP][1], "version": v}],
        "dependencies": [{"uuid": UUID[CORE_BP][0], "version": v}],
        "metadata": {"authors": ["Succubi Server"]}}
    guns_bp = {
        "format_version": 2,
        "header": {"name": "Succubi Guns BP",
                   "description": f"ปืน เกราะ ระเบิด ของตกแต่งทหาร (Aplok Guns) สำหรับ Succubi Server v{VERSION_TEXT} · วางไว้เหนือ Succubi Server BP · ถอดออกได้ทุกเมื่อ",
                   "uuid": UUID[GUNS_BP][0], "version": v, "min_engine_version": MIN_ENGINE},
        "modules": [
            {"description": "Aplok Guns data", "type": "data", "uuid": UUID[GUNS_BP][1], "version": v},
            {"description": "Aplok Guns scripts", "type": "script", "language": "javascript", "entry": "scripts/aplok_guns.js",
             "uuid": UUID[GUNS_BP][2], "version": v}],
        "dependencies": [
            {"uuid": UUID[GUNS_RP][0], "version": v},
            {"uuid": UUID[CORE_BP][0], "version": v},
            {"module_name": "@minecraft/server", "version": "1.19.0"},
            {"module_name": "@minecraft/server-ui", "version": "1.3.0"}],
        # the obfuscated Aplok Guns scripts build functions at runtime
        "capabilities": ["script_eval"],
        "metadata": {"authors": ["Gabriel Aplok (Aplok Guns)", "Succubi Server"]}}
    guns_rp = {
        "format_version": 2,
        "header": {"name": "Succubi Guns RP",
                   "description": f"โมเดล เสียง และเอฟเฟกต์ของปืน (Aplok Guns) สำหรับ Succubi Server v{VERSION_TEXT}",
                   "uuid": UUID[GUNS_RP][0], "version": v, "min_engine_version": MIN_ENGINE},
        "modules": [{"description": "Aplok Guns resources", "type": "resources", "uuid": UUID[GUNS_RP][1], "version": v}],
        "dependencies": [{"uuid": UUID[GUNS_BP][0], "version": v}],
        "metadata": {"authors": ["Gabriel Aplok (Aplok Guns)", "Succubi Server"]}}
    link_bp = {
        "format_version": 2,
        "header": {"name": "Succubi Server Link BP",
                   "description": "ส่งค่าความหิวให้ HUD ของ Succubi Server (เปิดพร้อม BP หลักอัตโนมัติ)",
                   "uuid": UUID[LINK_BP][0], "version": [1, 0, 1], "min_engine_version": MIN_ENGINE},
        "modules": [
            {"type": "data", "uuid": UUID[LINK_BP][1], "version": [1, 0, 1]},
            {"type": "script", "language": "javascript", "entry": "scripts/main.js", "uuid": UUID[LINK_BP][2], "version": [1, 0, 1]}],
        "dependencies": [{"module_name": "@minecraft/server", "version": "2.0.0"}]}
    for name, m in ((CORE_BP, core_bp), (CORE_RP, core_rp), (GUNS_BP, guns_bp), (GUNS_RP, guns_rp), (LINK_BP, link_bp)):
        wjson(os.path.join(out, name, 'manifest.json'), m)


# ------------------------------------------------------------------------------------------ player.json
NAMETAG_GROUP = {"succubi:nametag_near": {"minecraft:nameable": {"always_show": False, "allow_name_tag_renaming": False}}}
NAMETAG_EVENTS = {"succubi:nametag_near": {"add": {"component_groups": ["succubi:nametag_near"]}},
                  "succubi:nametag_always": {"remove": {"component_groups": ["succubi:nametag_near"]}}}


def gun_part(name):
    return name.startswith('trenbankai:') or name in ('default', 'juggernaut') or name.endswith('_fire')


def player_variants(src_player):
    """(core player.json, gun player.json). The gun one is the Aplok Guns player + height + name tags;
    the core one is the same player with every gun part taken out."""
    guns = rjson(src_player)
    e = guns['minecraft:entity']
    e['component_groups'].update(NAMETAG_GROUP)
    e['events'].update(NAMETAG_EVENTS)
    core = _copy.deepcopy(guns)
    c = core['minecraft:entity']
    d = c['description']
    for k in ('animations', 'scripts', 'properties'):
        d.pop(k, None)
    comps = c['components']
    comps.pop('minecraft:on_death', None)          # only counted gun deaths
    comps.pop('minecraft:damage_sensor', None)     # only the juggernaut armor rules
    env = comps.get('minecraft:environment_sensor', {}).get('triggers', [])
    env = [t for t in env if not str(t.get('event', '')).startswith('trenbankai:')]
    if env:
        comps['minecraft:environment_sensor'] = {"triggers": env}
    else:
        comps.pop('minecraft:environment_sensor', None)
    c['component_groups'] = {k: v for k, v in c['component_groups'].items() if not gun_part(k)}
    events = {}
    for k, v in c['events'].items():
        if gun_part(k):
            continue
        if k == 'minecraft:entity_spawned':
            continue                                  # only reset gun states
        events[k] = v
    c['events'] = events
    leftovers = [s for s in json.dumps(core).split('"') if 'trenbankai' in s]
    assert not leftovers, leftovers
    return core, guns


# ------------------------------------------------------------------------------------------ creative catalog
def split_catalog(src_catalog, gun_items):
    cat = rjson(src_catalog)
    core, guns = _copy.deepcopy(cat), _copy.deepcopy(cat)
    for which, keep in ((core, lambda g: not is_gun_group(g, gun_items)), (guns, lambda g: is_gun_group(g, gun_items))):
        cats = which['minecraft:crafting_items_catalog']['categories']
        for c in cats:
            c['groups'] = [g for g in c.get('groups', []) if keep(g)]
        which['minecraft:crafting_items_catalog']['categories'] = [c for c in cats if c.get('groups')]
    return core, guns


def is_gun_group(g, gun_items):
    items = [(i if isinstance(i, str) else i.get('name')) for i in g.get('items', [])]
    return bool(items) and all(i in gun_items or i.startswith('trenbankai:') for i in items)


# ------------------------------------------------------------------------------------------ armor points for the HUD
VANILLA_ARMOR = {
    'leather': (1, 3, 2, 1), 'chainmail': (2, 5, 4, 1), 'iron': (2, 6, 5, 2), 'golden': (2, 5, 3, 1),
    'diamond': (3, 8, 6, 3), 'netherite': (3, 8, 6, 3)}


def armor_table(item_dirs):
    table = {}
    for mat, pts in VANILLA_ARMOR.items():
        for part, p in zip(('helmet', 'chestplate', 'leggings', 'boots'), pts):
            table[f'minecraft:{mat}_{part}'] = p
    table['minecraft:turtle_helmet'] = 2
    for d in item_dirs:
        for root, _, files in os.walk(d):
            for f in files:
                if not f.endswith('.json'):
                    continue
                try:
                    it = rjson(os.path.join(root, f))['minecraft:item']
                except Exception:
                    continue
                w = it.get('components', {}).get('minecraft:wearable')
                if isinstance(w, dict) and w.get('protection'):
                    table[it['description']['identifier']] = int(w['protection'])
    body = ',\n'.join(f'  "{k}": {v}' for k, v in sorted(table.items()))
    return ('// GENERATED by tools/v20/packs.py - armor points shown on the HUD (vanilla armor + wearables of every pack)\n'
            f'export const ARMOR_POINTS = {{\n{body}\n}};\n')
