"""Content taken out of the core pack and content added to it (v1.1.6).

Removed for good: the haunted speaker (ลำโพงหลอน), the ghost bell (กระดิ่งเรียกผี) and the blood moon
(คืนพระจันทร์เลือด). Items or entities of these types left in old worlds simply disappear when the world loads.
Added: the admin's writable book (succubi:book_custom). Creative menu: the rule board and the watcher statue
move into the Tools group next to the rule wand, and the Rule of Horror group is gone."""
import os
import numpy as np
from PIL import Image, ImageDraw
from registry import step
from common import rjson, wjson, CORE_BP, CORE_RP

REMOVED_FILES = {
    CORE_BP: ['items/succubi/haunted_speaker_placer.json', 'entities/succubi_shops/haunted_speaker.json',
              'items/extra/ghost_bell.json', 'scripts/succubi/bloodmoon.js'],
    CORE_RP: ['entity/succubi_shops/haunted_speaker.entity.json', 'models/entity/succubi_shops/haunted_speaker.geo.json',
              'textures/entity/succubi_shops/haunted_speaker.png', 'textures/items/succubi/haunted_speaker_placer.png',
              'textures/items/extra/ghost_bell.png', 'fogs/blood_moon.json'],
}
REMOVED_TEXTURE_KEYS = ['succubi_haunted_speaker_placer', 'succubi_ghost_bell']
REMOVED_LANG = ['item.succubi:haunted_speaker_placer.name', 'entity.succubi:haunted_speaker.name',
                'item.succubi:ghost_bell.name', 'itemGroup.name.succubi:horror']
REMOVED_ITEMS = ['succubi:haunted_speaker_placer', 'succubi:ghost_bell']

BOOK = 'succubi:book_custom'
BOOK_ITEM = {
    "format_version": "1.21.0",
    "minecraft:item": {
        "description": {"identifier": BOOK, "menu_category": {"category": "equipment"}},
        "components": {
            "minecraft:display_name": {"value": "item.succubi:book_custom.name"},
            "minecraft:icon": "succubi_book_custom",
            "minecraft:max_stack_size": 1,
        },
    },
}
ADDED_LANG = {
    'th_TH': {'item.succubi:book_custom.name': 'สมุดเขียนเอง'},
    'en_US': {'item.succubi:book_custom.name': 'Writable Book'},
}


def edit_lang(path, drop, add):
    with open(path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    keep = [l for l in lines if l.split('=', 1)[0].strip() not in drop and l.split('=', 1)[0].strip() not in add]
    keep += [f'{k}={v}' for k, v in add.items()]
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(keep) + '\n')


def groups(catalog):
    """every creative group in the catalog, as (group dict, items list)"""
    out = []
    for cat in catalog['minecraft:crafting_items_catalog']['categories']:
        for g in cat.get('groups', []):
            out.append(g)
    return out


def item_name(x):
    return x if isinstance(x, str) else x.get('name')


def regroup(catalog):
    gs = groups(catalog)
    by_name = {g['group_identifier']['name']: g for g in gs if isinstance(g.get('group_identifier'), dict)}
    tools = by_name['itemGroup.name.succubi:tools']
    horror = by_name.pop('itemGroup.name.succubi:horror', None)
    moved = [i for i in (horror or {}).get('items', []) if item_name(i) not in REMOVED_ITEMS]
    items = [i for i in tools['items'] if item_name(i) not in REMOVED_ITEMS]
    at = next((n + 1 for n, i in enumerate(items) if item_name(i) == 'succubi:rule_wand'), len(items))
    tools['items'] = items[:at] + moved + items[at:]
    for cat in catalog['minecraft:crafting_items_catalog']['categories']:
        cat['groups'] = [g for g in cat.get('groups', []) if g is not horror]
    books = by_name['itemGroup.name.succubi:books']
    if BOOK not in [item_name(i) for i in books['items']]:
        books['items'].insert(0, BOOK)
    return [item_name(i) for i in tools['items']]


def edit_button(paper_dir):
    """btn_edit for the paper screens: the green "done" button turned blue, with a pencil instead of the tick"""
    im = Image.open(os.path.join(paper_dir, 'btn_done.png')).convert('RGBA')
    src = np.array(im)
    inner = src[5:-5, 5:44]                                    # skip the button's own outline
    dark = (inner[..., :3].astype(int).sum(axis=2) < 300) & (inner[..., 3] > 200)
    ys, xs = np.nonzero(dark)
    x0, x1, y0, y1 = int(xs.min()) + 5, int(xs.max()) + 5, int(ys.min()) + 5, int(ys.max()) + 5
    a = src.astype(float)
    r, g, b = a[..., 0].copy(), a[..., 1].copy(), a[..., 2].copy()
    a[..., 0], a[..., 1], a[..., 2] = r * 0.75, g * 0.85 + 10, np.minimum(255, g * 0.55 + b * 0.5 + 60)
    im = Image.fromarray(a.clip(0, 255).astype('uint8'), 'RGBA')
    box = tuple(int(v) for v in np.median(np.array(im)[y0 + 3:y1 - 3, x0 + 3:x0 + 6, :3].reshape(-1, 3), axis=0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], radius=4, fill=box + (255,))
    cx, cy, k = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 26
    body = [(cx - 7 * k, cy + 5 * k), (cx + 4 * k, cy - 6 * k), (cx + 7 * k, cy - 3 * k), (cx - 4 * k, cy + 8 * k)]
    d.polygon(body, fill=(255, 255, 255, 255))
    d.polygon([(cx - 7 * k, cy + 5 * k), (cx - 4 * k, cy + 8 * k), (cx - 8.5 * k, cy + 9.5 * k)], fill=(255, 226, 150, 255))
    d.line([(cx + 2.5 * k, cy - 4.5 * k), (cx + 5.5 * k, cy - 1.5 * k)], fill=box + (255,), width=max(1, int(k)))
    im.save(os.path.join(paper_dir, 'btn_edit.png'))


@step
def build_content(out, ctx, log):
    n = 0
    for pack, files in REMOVED_FILES.items():
        for f in files:
            p = os.path.join(out, pack, f)
            if os.path.exists(p):
                os.remove(p)
                n += 1
    tex_path = os.path.join(out, CORE_RP, 'textures/item_texture.json')
    tex = rjson(tex_path)
    for k in REMOVED_TEXTURE_KEYS:
        tex['texture_data'].pop(k, None)
    tex['texture_data']['succubi_book_custom'] = {"textures": "textures/items/extra/book_custom"}
    wjson(tex_path, tex)
    wjson(os.path.join(out, CORE_BP, 'items/extra/book_custom.json'), BOOK_ITEM)
    edit_button(os.path.join(out, CORE_RP, 'textures/ui/succubi_paper'))
    for lang, add in ADDED_LANG.items():
        p = os.path.join(out, CORE_RP, f'texts/{lang}.lang')
        if os.path.exists(p):
            edit_lang(p, set(REMOVED_LANG), add)
    cat_path = os.path.join(out, CORE_BP, 'item_catalog/crafting_item_catalog.json')
    cat = rjson(cat_path)
    tools = regroup(cat)
    wjson(cat_path, cat)
    leftovers = []
    for pack in (CORE_BP, CORE_RP):
        for root, _, files in os.walk(os.path.join(out, pack)):
            for f in files:
                if f.endswith(('.json', '.lang', '.js')):
                    txt = open(os.path.join(root, f), encoding='utf-8', errors='ignore').read()
                    if 'haunted_speaker' in txt or 'ghost_bell' in txt or 'blood_moon' in txt:
                        leftovers.append(os.path.relpath(os.path.join(root, f), out))
    assert not leftovers, leftovers
    log(f'content: removed speaker / ghost bell / blood moon ({n} files), added the writable book; tools group = {tools}')
