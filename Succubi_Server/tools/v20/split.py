"""Split the single v1.0.19 pack pair into Succubi Server (core) and Succubi Guns (Aplok Guns content).

The core packs must work on their own, so the gun packs can simply be switched off or deleted later.
BP files are sorted by the identifiers they define; RP files by following references outward from
each side's definitions (entities, attachables, UI), so a texture/model/animation lands in every pack
that uses it."""
import glob, os, re
from common import (rjson, wjson, copy, walk_strings, read_lang, write_lang,
                    CORE_BP, CORE_RP, GUNS_BP, GUNS_RP, LINK_BP)

GUN_NS = ('trenbankai', 'c7afd424')
GUN_BP_DIRS = ('animation_controllers/', 'animations/', 'functions/', 'structures/', 'scripts/main/')
GUN_BP_FILES = ('scripts/aplok_guns.js', 'scripts/tsconfig.tsbuildinfo',
                'CHANGELOG.md', 'CREDITS.md', 'LICENSE.md', 'NOTICE.md')
# handled elsewhere (rebuilt per pack) or dropped
BP_SPECIAL = ('manifest.json', 'contents.json', 'pack_icon.png', 'item_catalog/crafting_item_catalog.json',
              'entities/player.json', 'texts/en_US.lang', 'texts/th_TH.lang', 'texts/languages.json')
RP_SPECIAL = ('manifest.json', 'contents.json', 'pack_icon.png', 'textures/item_texture.json', 'textures/terrain_texture.json',
              'textures/texture_list.json', 'sounds/sound_definitions.json', 'blocks.json', 'texts/en_US.lang', 'texts/th_TH.lang',
              'texts/languages.json', 'ui/_ui_defs.json', 'ui/hud_screen.json',
              'textures/ui/title.tga',            # Aplok Guns logo on the title screen: removed
              'ui/content_log.json')              # forced the content log label on screen: removed
# Always core / always guns in the RP, whatever the references say
RP_CORE_DIRS = ('textures/ui/succubi_', 'ui/succubi_', 'ui/server_form.json', 'fogs/blood_moon', 'fogs/green_fog', 'fogs/red_fog',
                'fogs/sanity_fog', 'fogs/white_fog', 'sounds/kiosk/')
RP_GUN_DIRS = ('particles/', 'ui/hud/', 'ui/pause_screen.json', 'textures/ui/hud/', 'textures/ui/creators/', 'textures/ui/docs/',
               'textures/ui/slowness_effect', 'textures/ui/hud_mob_effect_background', 'materials/', 'fogs/fog_default',
               'textures/blocks/', 'models/blocks/', 'CHANGELOG.md', 'CREDITS.md', 'LICENSE.md', 'NOTICE.md')
# vanilla heart / hunger icons made transparent for the Succubi HUD
RP_CORE_UI_FILES = re.compile(r'^textures/ui/(absorption|freeze|poison|wither)?_?heart|^textures/ui/hunger_')


def ns(ident):
    return ident.split(':', 1)[0] if isinstance(ident, str) and ':' in ident else ''


def rel_files(root):
    out = []
    for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
        if os.path.isfile(p):
            out.append(os.path.relpath(p, root).replace(os.sep, '/'))
    return sorted(out)


# ------------------------------------------------------------------------------------------ BP
def bp_owner(path, full):
    if path in BP_SPECIAL or path.startswith('subpacks/'):
        return 'special'
    if path in GUN_BP_FILES or path.startswith(GUN_BP_DIRS):
        return 'guns'
    if path.endswith('.json'):
        d = rjson(full)
        idents = []
        for top, v in d.items():
            if isinstance(v, dict) and isinstance(v.get('description'), dict):
                idents.append(v['description'].get('identifier'))
                if top.startswith('minecraft:recipe'):
                    res = v.get('result', v.get('output'))
                    for r in (res if isinstance(res, list) else [res]):
                        idents.append(r.get('item') if isinstance(r, dict) else r)
        if isinstance(d.get('minecraft:recipe_furnace'), dict):
            idents.append(d['minecraft:recipe_furnace'].get('output'))
        if any(ns(i) in GUN_NS for i in idents):
            return 'guns'
        if path.startswith('loot_tables/blocks/'):
            return 'guns'
    return 'core'


# ------------------------------------------------------------------------------------------ RP
class RPIndex:
    def __init__(self, root):
        self.root = root
        self.files = rel_files(root)
        self.defines = {}          # token -> {file}
        self.json = {}
        self.tex = {}              # 'textures/..' (no ext) -> [file]
        for f in self.files:
            base, ext = os.path.splitext(f)
            if f.startswith('textures/') and ext in ('.png', '.tga', '.jpg'):
                self.tex.setdefault(base, []).append(f)
                continue
            if ext != '.json' and ext != '.material':
                continue
            try:
                d = rjson(os.path.join(root, f))
            except Exception:
                continue
            self.json[f] = d
            for tok in self.defined_tokens(f, d):
                self.defines.setdefault(tok, set()).add(f)
        sd = self.json.get('sounds/sound_definitions.json', {})
        self.sounds = sd.get('sound_definitions', sd)
        self.item_tex = self.json.get('textures/item_texture.json', {}).get('texture_data', {})

    @staticmethod
    def defined_tokens(f, d):
        toks = []
        if not isinstance(d, dict):
            return toks
        for key in ('minecraft:client_entity', 'minecraft:attachable', 'particle_effect', 'minecraft:fog_settings'):
            if key in d:
                toks.append(d[key]['description']['identifier'])
        for g in d.get('minecraft:geometry', []) if isinstance(d.get('minecraft:geometry'), list) else []:
            toks.append(g['description']['identifier'])
        for k, v in d.items():                   # legacy geometry format
            if k.startswith('geometry.'):
                toks.append(k.split(':')[0])
        for key in ('animations', 'animation_controllers', 'render_controllers'):
            if isinstance(d.get(key), dict):
                toks.extend(d[key].keys())
        if f.endswith('.material'):
            for k in d.get('materials', {}):
                toks.append(k.split(':')[0])
        return toks

    def refs(self, f):
        """files referenced by file f (+ sound events and item texture keys)"""
        out, events = set(), set()
        d = self.json.get(f)
        if d is None:
            return out, events
        for s in walk_strings(d):
            if s in self.defines:
                out |= self.defines[s]
            base = s.split(':')[0]
            if base != s and base in self.defines:
                out |= self.defines[base]
            if s.startswith('textures/'):
                out |= set(self.tex.get(s, [])) | set(self.tex.get(os.path.splitext(s)[0], []))
            if s in self.sounds:
                events.add(s)
        return out, events

    def closure(self, roots, events=()):
        todo, seen, ev = list(roots), set(), set(events)
        while todo:
            f = todo.pop()
            if f in seen:
                continue
            seen.add(f)
            more, e = self.refs(f)
            ev |= e
            todo.extend(more - seen)
        return seen, ev


def is_core_ident(i):
    return ns(i) not in GUN_NS and i != 'minecraft:player'


def split(src, out, log=print):
    sbp, srp = os.path.join(src, CORE_BP), os.path.join(src, CORE_RP)
    # ---------------- BP
    owner = {f: bp_owner(f, os.path.join(sbp, f)) for f in rel_files(sbp)}
    for f, o in owner.items():
        if o in ('core', 'guns'):
            copy(os.path.join(sbp, f), os.path.join(out, CORE_BP if o == 'core' else GUNS_BP, f))
    core_items, gun_items = set(), set()
    for f, o in owner.items():
        if f.startswith('items/') and o in ('core', 'guns'):
            ident = rjson(os.path.join(sbp, f))['minecraft:item']['description']['identifier']
            (core_items if o == 'core' else gun_items).add(ident)
    log(f"BP: core {sum(o == 'core' for o in owner.values())} files, guns {sum(o == 'guns' for o in owner.values())} files")

    # script-side references (sound events, textures) of the core BP
    core_js = ''
    for f, o in owner.items():
        if o == 'core' and f.endswith(('.js', '.json')):
            core_js += open(os.path.join(sbp, f), encoding='utf-8', errors='ignore').read()

    # ---------------- RP
    idx = RPIndex(srp)
    core_roots, gun_roots = set(), set()
    for f, d in idx.json.items():
        for key in ('minecraft:client_entity', 'minecraft:attachable'):
            if key in d:
                ident = d[key]['description']['identifier']
                (core_roots if is_core_ident(ident) else gun_roots).add(f)
        if 'particle_effect' in d:
            gun_roots.add(f)
    for f in idx.files:
        if f in RP_SPECIAL:
            continue
        if f.startswith(RP_CORE_DIRS) or RP_CORE_UI_FILES.match(f):
            core_roots.add(f)
        elif f.startswith(RP_GUN_DIRS):
            gun_roots.add(f)
    # item icons
    def icon_files(items):
        res = set()
        for i in items:
            item = next((rjson(os.path.join(sbp, p)) for p, o in owner.items() if p.startswith('items/') and o in ('core', 'guns')
                         and rjson(os.path.join(sbp, p))['minecraft:item']['description']['identifier'] == i), None)
            icon = item['minecraft:item']['components'].get('minecraft:icon') if item else None
            key = icon if isinstance(icon, str) else (icon or {}).get('texture') or ((icon or {}).get('textures') or {}).get('default')
            ent = idx.item_tex.get(key)
            if ent:
                t = ent['textures']
                for p in (t if isinstance(t, list) else [t]):
                    res |= set(idx.tex.get(p if isinstance(p, str) else p.get('path'), []))
        return res
    core_roots |= icon_files(core_items)
    gun_roots |= icon_files(gun_items)
    # textures named in core scripts (form button icons etc.)
    for m in set(re.findall(r'textures/[A-Za-z0-9_/.\-]+', core_js)):
        core_roots |= set(idx.tex.get(m, []))
    core_events = {e for e in idx.sounds if e in core_js}

    core_files, core_ev = idx.closure(core_roots, core_events)
    gun_files, gun_ev = idx.closure(gun_roots)
    rest = [f for f in idx.files if f not in core_files and f not in gun_files and f not in RP_SPECIAL]
    # everything nobody claimed is Aplok content (sounds, extra textures ...)
    gun_files |= set(rest)
    for f in sorted(core_files):
        copy(os.path.join(srp, f), os.path.join(out, CORE_RP, f))
    for f in sorted(gun_files):
        copy(os.path.join(srp, f), os.path.join(out, GUNS_RP, f))
    both = core_files & gun_files
    log(f"RP: core {len(core_files)} files, guns {len(gun_files)} files ({len(both)} in both), unclaimed->guns {len(rest)}")

    # ---------------- shared tables
    core_ev |= core_events
    sd = idx.sounds
    snd_core = {k: v for k, v in sd.items() if k in core_ev}
    snd_guns = {k: v for k, v in sd.items() if k not in core_ev}
    # sound files follow their events
    for evs, pack in ((snd_core, CORE_RP), (snd_guns, GUNS_RP)):
        for v in evs.values():
            for s in v.get('sounds', []):
                p = s if isinstance(s, str) else s.get('name')
                for ext in ('.ogg', '.fsb', '.wav'):
                    fp = os.path.join(srp, p + ext)
                    if os.path.isfile(fp):
                        copy(fp, os.path.join(out, pack, p + ext))
    head = {k: v for k, v in idx.json['sounds/sound_definitions.json'].items() if k != 'sound_definitions'}
    wjson(os.path.join(out, CORE_RP, 'sounds/sound_definitions.json'), dict(head, sound_definitions=snd_core))
    wjson(os.path.join(out, GUNS_RP, 'sounds/sound_definitions.json'), dict(head, sound_definitions=snd_guns))

    it = idx.json['textures/item_texture.json']
    def item_keys(items):
        keys = set()
        for p, o in owner.items():
            if p.startswith('items/') and o in ('core', 'guns'):
                d = rjson(os.path.join(sbp, p))['minecraft:item']
                if d['description']['identifier'] in items:
                    icon = d['components'].get('minecraft:icon')
                    keys.add(icon if isinstance(icon, str) else (icon or {}).get('texture') or ((icon or {}).get('textures') or {}).get('default'))
        return keys
    ck, gk = item_keys(core_items), item_keys(gun_items)
    td = it['texture_data']
    def tex_in(pack, v):
        t = v['textures']
        return all(any(os.path.isfile(os.path.join(out, pack, (x if isinstance(x, str) else x.get('path')) + e)) for e in ('.png', '.tga'))
                   for x in (t if isinstance(t, list) else [t]))
    core_td = {k: v for k, v in td.items() if k in ck or (k not in gk and tex_in(CORE_RP, v))}
    gun_td = {k: v for k, v in td.items() if k not in core_td and tex_in(GUNS_RP, v)}
    dropped = [k for k in td if k not in core_td and k not in gun_td]
    if dropped:
        log(f'item textures dropped (no image anywhere): {dropped}')
    wjson(os.path.join(out, CORE_RP, 'textures/item_texture.json'), dict(it, texture_data=core_td))
    wjson(os.path.join(out, GUNS_RP, 'textures/item_texture.json'), dict(it, texture_data=gun_td))
    for k in ('textures/terrain_texture.json', 'blocks.json'):
        copy(os.path.join(srp, k), os.path.join(out, GUNS_RP, k))
    tl = idx.json.get('textures/texture_list.json', [])
    wjson(os.path.join(out, GUNS_RP, 'textures/texture_list.json'),
          [t for t in tl if any(os.path.isfile(os.path.join(out, GUNS_RP, t + e)) for e in ('.png', '.tga'))])
    log(f"item textures: core {len(core_td)} keys, guns {len(gun_td)} keys; sounds: core {len(snd_core)}, guns {len(snd_guns)}")

    # ---------------- languages: gun keys are the ones naming gun content
    gun_words = re.compile(r'trenbankai|aplok|c7afd424|weapon|ammo|attachment|sight|grenade|juggernaut|workbench|gunmetal|'
                           r'aluminum|steel|landmine|sandbag|hesco|container|barbed|corrugated|spotlight|ceiling_light|'
                           r'hedgehog|military|cooked_flesh|death\.attack|deaths|kills|nvg|scope|laser|silencer|foregrip|mag\b|'
                           r'^tile\.|^ui\.settings|^game\.', re.I)
    joined = {'en_US': 'game.message.joined=§d[Succubi]§r Welcome to the server!',
              'th_TH': 'game.message.joined=§d[Succubi]§r ยินดีต้อนรับสู่เซิร์ฟเวอร์!'}   # used to say "right-click a compass"

    for pack_src, core_dst, gun_dst in ((sbp, CORE_BP, GUNS_BP), (srp, CORE_RP, GUNS_RP)):
        for lang in ('en_US', 'th_TH'):
            rows = read_lang(os.path.join(pack_src, 'texts', lang + '.lang'))
            core_rows, gun_rows = [], []
            for key, line in rows:
                if key is None:
                    continue
                if key.startswith('pack.'):
                    continue
                if key == 'game.message.joined':
                    line = joined[lang]
                (gun_rows if gun_words.search(key) else core_rows).append((key, line))
            write_lang(os.path.join(out, core_dst, 'texts', lang + '.lang'), core_rows)
            write_lang(os.path.join(out, gun_dst, 'texts', lang + '.lang'), gun_rows)
        for p in (core_dst, gun_dst):
            wjson(os.path.join(out, p, 'texts/languages.json'), ['en_US', 'th_TH'])
    return dict(owner=owner, core_items=core_items, gun_items=gun_items, idx=idx)


if __name__ == '__main__':
    import sys, shutil
    src, out = sys.argv[1], sys.argv[2]
    shutil.rmtree(out, ignore_errors=True)
    r = split(src, out)
    print('core items', len(r['core_items']), 'gun items', len(r['gun_items']))
