"""Shadow creature (below 15 % sanity) and nightmare fuel. Safe to run again.

BP  entities/succubi_shadow_creature.json    the invisible body: hunts only players tagged succubi_insane
                                             (scripts/succubi/shadows.js draws it with particles for them only)
BP  items/extra/nightmare_fuel.json          burns in a furnace like a small coal (the killer gets it in hand)
RP  entity/succubi_shadow_creature.entity.json  renders nothing (controller.render.succubi_hidden)
RP  textures/items/extra/nightmare_fuel.png + item_texture.json entry + th_TH / en_US names
Particles and the hidden render controller: tools/gen_shadow_particles.py
"""
import json
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon")
BP = os.path.join(ROOT, "Succubi Server BP")
RP = os.path.join(ROOT, "Succubi Server RP")


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


ENTITY = {
    "format_version": "1.20.50",
    "minecraft:entity": {
        "description": {
            "identifier": "succubi:shadow_creature",
            "is_spawnable": False,
            "is_summonable": True,
            "is_experimental": False,
        },
        "components": {
            # not "monster": sane players nearby must not lose sanity to it, golems must not fight thin air
            "minecraft:type_family": {"family": ["succubi_shadow", "mob"]},
            "minecraft:collision_box": {"width": 0.6, "height": 1.9},
            # lots of real health: the script counts the hits, so the game's death smoke never shows
            "minecraft:health": {"value": 1000, "max": 1000},
            "minecraft:attack": {"damage": 5},
            "minecraft:movement": {"value": 0.27},
            "minecraft:movement.basic": {},
            "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_damage_blocks": True,
                                          "can_open_doors": False},
            "minecraft:jump.static": {},
            "minecraft:can_climb": {},
            "minecraft:physics": {},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:follow_range": {"value": 40, "max": 40},
            "minecraft:fire_immune": True,
            "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0, "breathes_water": True},
            "minecraft:damage_sensor": {"triggers": [
                {"cause": "fall", "deals_damage": False},
                {"cause": "suffocation", "deals_damage": False},
                {"cause": "drowning", "deals_damage": False},
            ]},
            "minecraft:nameable": {},
            "minecraft:conditional_bandwidth_optimization": {},
            # only players who lost their mind are prey; hits from anyone else are ignored (no hurt_by_target)
            "minecraft:behavior.nearest_attackable_target": {
                "priority": 1,
                "must_see": False,
                "reselect_targets": True,
                "within_radius": 40,
                "entity_types": [{
                    "filters": {"all_of": [
                        {"test": "is_family", "subject": "other", "value": "player"},
                        {"test": "has_tag", "subject": "other", "value": "succubi_insane"},
                    ]},
                    "max_dist": 40,
                }],
            },
            "minecraft:behavior.melee_attack": {"priority": 2, "speed_multiplier": 1.15, "track_target": True},
            "minecraft:behavior.random_stroll": {"priority": 6, "speed_multiplier": 0.7},
            "minecraft:behavior.look_at_player": {"priority": 7, "look_distance": 12, "probability": 0.05},
        },
    },
}

ITEM = {
    "format_version": "1.21.0",
    "minecraft:item": {
        "description": {"identifier": "succubi:nightmare_fuel", "menu_category": {"category": "items"}},
        "components": {
            "minecraft:display_name": {"value": "item.succubi:nightmare_fuel.name"},
            "minecraft:icon": "succubi_nightmare_fuel",
            "minecraft:max_stack_size": 64,
            "minecraft:fuel": {"duration": 40},
        },
    },
}

CLIENT = {
    "format_version": "1.10.0",
    "minecraft:client_entity": {
        "description": {
            "identifier": "succubi:shadow_creature",
            "materials": {"default": "entity_alphatest"},
            "textures": {"default": "textures/entity/succubi_shops/shadow_figure"},
            "geometry": {"default": "geometry.succubi_shadow_figure"},
            "render_controllers": ["controller.render.succubi_hidden"],
        }
    },
}

LANG = {
    "th_TH.lang": {
        "item.succubi:nightmare_fuel.name": "เชื้อเพลิงฝันร้าย",
        "entity.succubi:shadow_creature.name": "เงาจากความคลั่ง",
    },
    "en_US.lang": {
        "item.succubi:nightmare_fuel.name": "Nightmare Fuel",
        "entity.succubi:shadow_creature.name": "Shadow of Madness",
    },
}


def fuel_texture():
    """32 px dark goo blob with red glints (the shadow's eyes), shown at 64 px like the pack's other items"""
    rnd = random.Random(15)
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (14, 6, 16, 255)
    d.ellipse((6, 11, 26, 28), fill=ink)
    d.ellipse((10, 6, 21, 18), fill=ink)
    d.ellipse((4, 18, 12, 27), fill=ink)
    d.ellipse((20, 17, 29, 26), fill=ink)
    body = (48, 20, 56, 255)
    d.ellipse((8, 13, 24, 26), fill=body)
    d.ellipse((12, 8, 19, 16), fill=body)
    d.ellipse((6, 19, 11, 25), fill=body)
    d.ellipse((21, 19, 27, 24), fill=body)
    for _ in range(18):  # swirls of darker purple
        x, y = rnd.randint(9, 23), rnd.randint(10, 24)
        if img.getpixel((x, y)) == body:
            img.putpixel((x, y), (30, 12, 36, 255))
    d.point([(12, 13), (13, 12), (18, 21)], fill=(120, 70, 150, 255))  # highlights
    d.rectangle((13, 18, 14, 18), fill=(235, 60, 70, 255))  # the eyes
    d.rectangle((18, 18, 19, 18), fill=(235, 60, 70, 255))
    d.point([(16, 29), (16, 30), (9, 28)], fill=ink)  # drips
    return img.resize((64, 64), Image.NEAREST)


def patch_lang(path, entries):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    lines = [ln for ln in lines if ln.split("=", 1)[0] not in entries]
    lines += [f"{k}={v}" for k, v in entries.items()]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    write_json(os.path.join(BP, "entities", "succubi_shadow_creature.json"), ENTITY)
    write_json(os.path.join(BP, "items", "extra", "nightmare_fuel.json"), ITEM)
    write_json(os.path.join(RP, "entity", "succubi_shadow_creature.entity.json"), CLIENT)
    fuel_texture().save(os.path.join(RP, "textures", "items", "extra", "nightmare_fuel.png"))

    tex_path = os.path.join(RP, "textures", "item_texture.json")
    with open(tex_path, encoding="utf-8") as f:
        tex = json.load(f)
    tex["texture_data"]["succubi_nightmare_fuel"] = {"textures": "textures/items/extra/nightmare_fuel"}
    write_json(tex_path, tex)

    for name, entries in LANG.items():
        patch_lang(os.path.join(RP, "texts", name), entries)
    print("shadow creature + nightmare fuel written")


if __name__ == "__main__":
    main()
