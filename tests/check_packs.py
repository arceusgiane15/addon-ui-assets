"""Static checks on the packs: JSON parses, every texture / sound / model the v1.1.9 changes point at exists.
Run: python3 tests/check_packs.py   (exit code 1 on any problem)"""
import glob
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon")
RP = os.path.join(ROOT, "Succubi Server RP")
BP = os.path.join(ROOT, "Succubi Server BP")
problems = []


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def texture_exists(ref):
    for pack in ("Succubi Server RP", "Succubi Guns RP"):
        base = os.path.join(ROOT, pack, ref)
        if any(os.path.exists(base + ext) for ext in (".png", ".tga", ".jpg")):
            return True
    return False


# 1. every JSON file parses
for path in glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True):
    try:
        load(path)
    except Exception as e:  # noqa: BLE001
        problems.append(f"JSON: {os.path.relpath(path, ROOT)}: {e}")

# 2. UI textures (the pack's own) exist
for ui in ("succubi_hud.json", "succubi_height.json"):
    raw = open(os.path.join(RP, "ui", ui), encoding="utf-8").read()
    for ref in sorted(set(re.findall(r'"(textures/ui/succubi_[^"]+)"', raw))):
        if not texture_exists(ref):
            problems.append(f"{ui}: missing texture {ref}")

# 3. button textures the height script passes to forms
js = open(os.path.join(BP, "scripts", "height", "ui.js"), encoding="utf-8").read()
for name in set(re.findall(r'"(wbtn_[a-z]+)"', js)):
    for suffix in ("", "_off"):
        if not texture_exists(f"textures/ui/succubi_height/{name}{suffix}"):
            problems.append(f"ui.js: missing button texture {name}{suffix}")

# 4. item textures
tex = load(os.path.join(RP, "textures", "item_texture.json"))["texture_data"]
for key in ("succubi_nightmare_fuel",):
    if key not in tex or not texture_exists(tex[key]["textures"]):
        problems.append(f"item_texture.json: {key} missing or its file is gone")

# 5. sounds
sounds = load(os.path.join(RP, "sounds", "sound_definitions.json"))["sound_definitions"]
for key in ("succubi.music.danger", "succubi.music.madness", "succubi.music.silence"):
    if key not in sounds:
        problems.append(f"sound_definitions: {key} missing")
        continue
    for s in sounds[key]["sounds"]:
        if not os.path.exists(os.path.join(RP, s["name"] + ".ogg")):
            problems.append(f"sound_definitions: {key} -> {s['name']}.ogg missing")

# 6. shadow creature: client entity, geometry, animation, render controller, loot, item, names
client = load(os.path.join(RP, "entity", "succubi_shadow_creature.entity.json"))["minecraft:client_entity"]["description"]
geos = set()
for path in glob.glob(os.path.join(RP, "models", "**", "*.json"), recursive=True):
    for g in load(path).get("minecraft:geometry", []):
        geos.add(g["description"]["identifier"])
if client["geometry"]["default"] not in geos:
    problems.append("shadow creature: geometry missing")
anims = {}
for path in glob.glob(os.path.join(RP, "animations", "**", "*.json"), recursive=True):
    anims.update(load(path).get("animations", {}))
for a in client["animations"].values():
    if a not in anims:
        problems.append(f"shadow creature: animation {a} missing")
rcs = {}
for path in glob.glob(os.path.join(RP, "render_controllers", "**", "*.json"), recursive=True):
    rcs.update(load(path).get("render_controllers", {}))
for rc in client["render_controllers"]:
    if rc not in rcs:
        problems.append(f"shadow creature: render controller {rc} missing")
if not texture_exists(client["textures"]["default"]):
    problems.append("shadow creature: texture missing")
entity = load(os.path.join(BP, "entities", "succubi_shadow_creature.json"))
loot = entity["minecraft:entity"]["components"]["minecraft:loot"]["table"]
if not os.path.exists(os.path.join(BP, loot)):
    problems.append(f"shadow creature: loot table {loot} missing")
items = {load(p)["minecraft:item"]["description"]["identifier"]
         for p in glob.glob(os.path.join(BP, "items", "**", "*.json"), recursive=True)
         if "minecraft:item" in load(p)}
for pool in load(os.path.join(BP, loot))["pools"]:
    for entry in pool["entries"]:
        if entry["name"] not in items:
            problems.append(f"loot: {entry['name']} is not an item of this pack")
for lang in ("th_TH.lang", "en_US.lang"):
    text = open(os.path.join(RP, "texts", lang), encoding="utf-8").read()
    for key in ("item.succubi:nightmare_fuel.name", "entity.succubi:shadow_creature.name"):
        if key + "=" not in text:
            problems.append(f"{lang}: {key} missing")

# 7. manifests agree on versions of the packs they depend on
manifests = {}
for path in glob.glob(os.path.join(ROOT, "*", "manifest.json")):
    m = load(path)
    manifests[m["header"]["uuid"]] = (os.path.basename(os.path.dirname(path)), m)
for uuid, (name, m) in manifests.items():
    for dep in m.get("dependencies", []):
        if "uuid" in dep and dep["uuid"] in manifests:
            other = manifests[dep["uuid"]][1]["header"]["version"]
            if dep["version"] != other:
                problems.append(f"{name}: depends on {manifests[dep['uuid']][0]} {dep['version']} but it is {other}")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("packs OK")
