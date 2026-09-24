"""v1.0.17: one creative group for the player tools (settings, wallet, rule wand, ghost bell, height adjuster)."""
import json
from build_food import wjson

GROUP = "itemGroup.name.succubi:tools"
TOOLS = ["succubi:server_settings", "succubi:wallet", "succubi:rule_wand", "succubi:ghost_bell", "kotarus:height_adjuster"]


def _name(i):
    return i if isinstance(i, str) else i.get('name')


def catalog(bp):
    path = f'{bp}/item_catalog/crafting_item_catalog.json'
    d = json.load(open(path))
    cats = d['minecraft:crafting_items_catalog']['categories']
    for c in cats:
        for g in c['groups']:
            g['items'] = [i for i in g['items'] if _name(i) not in TOOLS]
        c['groups'] = [g for g in c['groups'] if g['items'] or g['group_identifier']['name'] == GROUP]
    eq = next(c for c in cats if c['category_name'] == 'equipment')
    grp = {"group_identifier": {"icon": "succubi:server_settings", "name": GROUP}, "items": list(TOOLS)}
    at = next((n for n, g in enumerate(eq['groups']) if g['group_identifier']['name'] == 'itemGroup.name.succubi:money'), len(eq['groups']))
    eq['groups'].insert(at, grp)
    wjson(path, d)


def lang_lines(th):
    return ["", "## v1.0.17", f"{GROUP}={'เครื่องมือ' if th else 'Tools'}"]
