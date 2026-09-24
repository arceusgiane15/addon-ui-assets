"""Build Succubi Server v1.0.12 = v1.0.10 + kiosk shops + Food Items dishes + pharmacy + convenience store.
usage: python3 tools/build.py <extracted v1.0.10 dir> <out dir>"""
import json, os, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import build_food, build_shop, build_scripts, build_extra, build_sanity, build_v14, icons, optimize
from build_food import wjson
from data import FOODS, SHOPS

VERSION = [1, 0, 14]


def log(msg):
    print('[build]', msg)


def lang_lines(th):
    L = ["", "## Kiosk shops & dishes (v1.0.11)"]
    for f in FOODS:
        L.append(f"item.food:{f['key']}.name={f['name'] if th else f['en']}")
    names = {s['entity']: (s['title'], s['en']) for s in SHOPS}
    for ent, (t, e) in names.items():
        n = ent.split(':')[1]
        L.append(f"item.{ent}.name={'ซุ้ม' + t if th else e + ' Kiosk'}")
        L.append(f"entity.{ent}.name={t if th else e}")
    L += [
        f"item.succubi:drink_vending_machine_placer.name={'ตู้กดน้ำ' if th else 'Drink Vending Machine'}",
        f"item.succubi:snack_vending_machine_placer.name={'ตู้ขนม' if th else 'Snack Vending Machine'}",
        f"itemGroup.name.succubi:shops={'ร้านค้า' if th else 'Shops'}",
        f"action.interact.succubi_shop={'ซื้ออาหาร' if th else 'Order'}",
        f"action.interact.dismantle={'รื้อซุ้ม' if th else 'Dismantle'}",
    ]
    return L


def catalog(bp):
    path = f'{bp}/item_catalog/crafting_item_catalog.json'
    d = json.load(open(path))
    cats = d['minecraft:crafting_items_catalog']['categories']
    for c in cats:
        for g in c['groups']:
            if g['group_identifier']['name'] == 'itemGroup.name.succubi:food':
                for f in FOODS:
                    if f"food:{f['key']}" not in g['items']:
                        g['items'].append(f"food:{f['key']}")
    shops = [s['entity'].replace('kiosk:', 'kiosk:') for s in SHOPS] + ['succubi:drink_vending_machine_placer', 'succubi:snack_vending_machine_placer']
    if not any(g['group_identifier']['name'] == 'itemGroup.name.succubi:shops' for c in cats for g in c['groups']):
        cats.append({"category_name": "equipment", "groups": [{
            "group_identifier": {"icon": "kiosk:ramen_kiosk", "name": "itemGroup.name.succubi:shops"}, "items": shops}]})
    wjson(path, d)


def bump(path, deps_to_bump):
    d = json.load(open(path))
    d['header']['version'] = VERSION
    d['header']['description'] = d['header']['description'].replace('v1.0.10', 'v1.0.14')
    for m in d['modules']:
        m['version'] = VERSION
    for dep in d.get('dependencies', []):
        if dep.get('uuid') in deps_to_bump:
            dep['version'] = VERSION
    wjson(path, d)


def contents(pack):
    files = []
    for root, _, fs in os.walk(pack):
        for f in fs:
            rel = os.path.relpath(os.path.join(root, f), pack).replace(os.sep, '/')
            if rel == 'contents.json':
                continue
            files.append(rel)
    wjson(f'{pack}/contents.json', {"content": [{"path": p} for p in sorted(files)]})


def main(src, out):
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(src, out)
    bp, rp = f'{out}/Succubi Server BP', f'{out}/Succubi Server RP'
    # stray editor temp file that shipped inside v1.0.10
    tmp = f'{bp}/structures/military_wall.mcstructure~RF5e7876a.TMP'
    if os.path.exists(tmp):
        os.remove(tmp)

    item_tex = build_food.build(bp, rp, log)
    build_shop.merge_kiosks(bp, rp, item_tex, log)
    build_shop.vending_placers(bp, rp, item_tex, log)
    for m in ('drink', 'snack'):
        os.makedirs(f'{rp}/textures/items/succubi', exist_ok=True)
        icons.model_icon(f'{rp}/models/entity/succubi_{m}_vending_machine.geo.json', f'{rp}/textures/entity/succubi/{m}_vending_machine.png',
                         f'{rp}/textures/items/succubi/{m}_vending_machine_placer.png')
    menus = build_shop.shop_ui(rp, log)
    build_scripts.build(bp, menus, log)
    build_extra.build(bp, rp, item_tex, log)
    build_sanity.build(bp, rp, item_tex, log)
    build_v14.build(bp, rp, item_tex, log)

    it_path = f'{rp}/textures/item_texture.json'
    it = json.load(open(it_path)); it['texture_data'].update(item_tex); wjson(it_path, it)
    tl_path = f'{rp}/textures/texture_list.json'
    tl = json.load(open(tl_path))
    for v in item_tex.values():
        if v['textures'] not in tl:
            tl.append(v['textures'])
    wjson(tl_path, tl)

    for lang, th in (('th_TH', True), ('en_US', False)):
        for pack in (rp,):
            p = f'{pack}/texts/{lang}.lang'
            s = open(p, encoding='utf-8').read().rstrip('\n')
            open(p, 'w', encoding='utf-8').write(s + '\n' + '\n'.join(lang_lines(th) + build_extra.lang_lines(th) + build_sanity.lang_lines(th) + build_v14.lang_lines(th)) + '\n')
    catalog(bp)
    build_extra.catalog(bp)
    build_v14.catalog(bp)

    bp_uuid, rp_uuid = '344a2ed9-b5c1-4651-af5b-b888f88e66f0', '5485ae30-e95c-4ba6-8cf9-c50b4fb71226'
    bump(f'{bp}/manifest.json', {rp_uuid})
    bump(f'{rp}/manifest.json', {bp_uuid})
    optimize.run(out, log)
    contents(bp)
    log('done')


def package(out, dest):
    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, fs in os.walk(out):
            for f in sorted(fs):
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, out))
    log(f'packaged {dest} ({os.path.getsize(dest) / 1e6:.1f} MB)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 3:
        package(sys.argv[2], sys.argv[3])
