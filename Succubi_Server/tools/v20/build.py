"""Succubi Server v1.1 build.

    python3 tools/v20/build.py <v1.0.19 .mcaddon or unpacked folder> <work dir> [output .mcaddon]

1. split the old single pack pair into Succubi Server (core) + Succubi Guns (Aplok Guns)
2. copy overlay/ (hand-edited scripts and files) on top
3. generate manifests, player.json variants, creative catalogs, HUD armor table
4. art + UI generators (HUD, themed windows, icons, models)
5. validate every pack and zip the .mcaddon"""
import os, shutil, sys, zipfile, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (OVERLAY, rjson, wjson, copy, CORE_BP, CORE_RP, GUNS_BP, GUNS_RP, LINK_BP, VERSION_TEXT)
import split as splitter
import packs
from validate import validate

from registry import STEPS


def unpack(src, work):
    if os.path.isdir(src):
        return src
    dst = os.path.join(work, 'src')
    shutil.rmtree(dst, ignore_errors=True)
    with zipfile.ZipFile(src) as z:
        z.extractall(dst)
    return dst


def overlay(out, log):
    n = 0
    for root, _, files in os.walk(OVERLAY):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, OVERLAY)
            copy(full, os.path.join(out, rel))
            n += 1
    log(f'overlay: {n} files')


def build(src, work, target=None, log=print):
    src = unpack(src, work)
    out = os.path.join(work, 'out')
    shutil.rmtree(out, ignore_errors=True)
    ctx = splitter.split(src, out, log)
    # link pack comes over unchanged (apart from its manifest)
    for f in glob.glob(os.path.join(src, LINK_BP, '**', '*'), recursive=True):
        if os.path.isfile(f):
            copy(f, os.path.join(out, LINK_BP, os.path.relpath(f, os.path.join(src, LINK_BP))))
    overlay(out, log)

    # generated per-pack files
    packs.manifests(out)
    core_p, guns_p = packs.player_variants(os.path.join(src, CORE_BP, 'entities/player.json'))
    wjson(os.path.join(out, CORE_BP, 'entities/player.json'), core_p)
    wjson(os.path.join(out, GUNS_BP, 'entities/player.json'), guns_p)
    core_c, guns_c = packs.split_catalog(os.path.join(src, CORE_BP, 'item_catalog/crafting_item_catalog.json'), ctx['gun_items'])
    wjson(os.path.join(out, CORE_BP, 'item_catalog/crafting_item_catalog.json'), core_c)
    wjson(os.path.join(out, GUNS_BP, 'item_catalog/crafting_item_catalog.json'), guns_c)
    with open(os.path.join(out, CORE_BP, 'scripts/height/body.js'), 'w', encoding='utf-8') as f:
        f.write(packs.body_js())
    with open(os.path.join(out, CORE_BP, 'scripts/succubi/armor_values.js'), 'w', encoding='utf-8') as f:
        f.write(packs.armor_table([os.path.join(out, CORE_BP, 'items'), os.path.join(out, GUNS_BP, 'items')]))
    for p in (CORE_BP, CORE_RP, GUNS_BP, GUNS_RP):
        for junk in ('contents.json', 'textures/ui/title.tga', 'ui/content_log.json'):
            fp = os.path.join(out, p, junk)
            if os.path.exists(fp):
                os.remove(fp)
    ctx['src'] = src
    for fn in STEPS:
        fn(out, ctx, log)

    problems = validate(out, {
        'core': [CORE_BP, CORE_RP, LINK_BP],
        'guns': [GUNS_BP, GUNS_RP, CORE_BP, CORE_RP],
    }, log)
    if problems:
        raise SystemExit(f'{len(problems)} validation problem(s)')
    if target:
        pack_zip(out, target, log)
    return out


def pack_zip(out, target, log):
    if os.path.exists(target):
        os.remove(target)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in (CORE_BP, CORE_RP, GUNS_BP, GUNS_RP, LINK_BP):
            root = os.path.join(out, name)
            for f in sorted(glob.glob(os.path.join(root, '**', '*'), recursive=True)):
                if os.path.isfile(f) and '__pycache__' not in f:
                    z.write(f, os.path.join(name, os.path.relpath(f, root)))
    log(f'wrote {target} ({os.path.getsize(target) / 1e6:.1f} MB)')


# art / UI generators register themselves with @step
for mod in ('art_hud', 'art_ui', 'art_icons', 'art_models', 'sfx', 'content'):
    try:
        __import__(mod)
    except ModuleNotFoundError as e:
        if e.name != mod:
            raise

if __name__ == '__main__':
    src, work = sys.argv[1], sys.argv[2]
    target = sys.argv[3] if len(sys.argv) > 3 else None
    build(src, work, target)
