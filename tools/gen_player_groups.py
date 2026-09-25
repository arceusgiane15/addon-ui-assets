"""Adds the height-system component groups to both player.json files (Succubi Server BP and Succubi Guns BP).

Both packs define minecraft:player; whichever sits higher in the world's behavior pack list wins, so the two
files must carry the same groups. Safe to run again: it rebuilds the groups and events it owns.

  succubi:hp_XXX    minecraft:health (value = max = XXX)          XXX = 010 ... 400, step 5
  succubi:spdp_XXX  minecraft:movement (0.1 * XXX / 100)          XXX = 050 ... 150, step 1
  succubi:hun_XXX   minecraft:exhaustion_values (x XXX / 100)     XXX = 050 ... 200, step 5

Each has a succubi:set_<family>_XXX event that removes the rest of its family and adds that one group.
The old 10 cm speed groups (succubi:spd_140 ... spd_220) stay defined so the new speed events can take them off
players who still carry one; their set events are gone (the script no longer uses them).
Keep the ranges in step with GROUPS in scripts/height/body.js.
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon")
FILES = [
    os.path.join(ROOT, "Succubi Server BP", "entities", "player.json"),
    os.path.join(ROOT, "Succubi Guns BP", "entities", "player.json"),
]

HP = range(10, 401, 5)
SPEED = range(50, 151, 1)
HUNGER = range(50, 201, 5)
BASE_SPEED = 0.1
OLD_SPEED_GROUPS = [f"succubi:spd_{cm:03d}" for cm in range(140, 221, 10)]


def family(prefix, values, make):
    return {f"succubi:{prefix}_{v:03d}": make(v) for v in values}


def build(entity):
    comps = entity["components"]
    exhaustion = comps["minecraft:exhaustion_values"]
    groups = entity["component_groups"]
    events = entity["events"]

    # forget what an earlier run made
    for name in list(groups):
        if name.startswith(("succubi:hp_", "succubi:spdp_", "succubi:hun_")):
            del groups[name]
    for name in list(events):
        if name.startswith(("succubi:set_hp_", "succubi:set_spdp_", "succubi:set_hun_", "succubi:set_spd_")):
            del events[name]

    families = {
        "hp": family("hp", HP, lambda v: {"minecraft:health": {"value": v, "max": v}}),
        "spdp": family("spdp", SPEED, lambda v: {"minecraft:movement": {"value": round(BASE_SPEED * v / 100, 5)}}),
        "hun": family(
            "hun", HUNGER,
            lambda v: {"minecraft:exhaustion_values": {k: round(x * v / 100, 6) for k, x in exhaustion.items()}},
        ),
    }
    for prefix, fam in families.items():
        groups.update(fam)
        names = list(fam)
        extra = OLD_SPEED_GROUPS if prefix == "spdp" else []
        for name in names:
            value = name.rsplit("_", 1)[1]
            events[f"succubi:set_{prefix}_{value}"] = {
                "remove": {"component_groups": [n for n in names if n != name] + extra},
                "add": {"component_groups": [name]},
            }


def main():
    for path in FILES:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        build(data["minecraft:entity"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print("updated", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
