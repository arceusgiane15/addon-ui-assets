"""Checks that a set of packs is self-contained: every model, texture, animation, render controller, sound,
item icon and UI texture a pack uses exists in that pack, in a pack it may rely on, or in vanilla.

validate(out, groups) where groups = {'core': [bp, rp, link], 'guns': [bp, rp] + core...}"""
import glob, json, os, re
from common import rjson, walk_strings, HERE

VAN = json.load(open(os.path.join(HERE, 'vanilla_index.json')))
VAN = {k: set(v) for k, v in VAN.items()}
VANILLA_MATERIALS = {'entity', 'entity_alphatest', 'entity_alphablend', 'entity_emissive', 'entity_emissive_alpha', 'entity_nocull',
                     'entity_change_color', 'entity_glint', 'entity_beam', 'entity_beam_additive', 'entity_alphatest_glint',
                     'entity_emissive_alpha_one_sided', 'entity_alphatest_change_color', 'player_animated', 'player_spectator',
                     'charged_creeper', 'spider', 'item_in_hand', 'entity_custom', 'entity_multitexture', 'entity_lead_base',
                     'entity_dissolve_layer0', 'entity_dissolve_layer1', 'wither_boss', 'entity_alphatest_one_sided', 'beacon_beam',
                     'armor', 'armor_enchanted', 'armor_leather', 'armor_leather_enchanted'}
# engine-side definitions the vanilla player uses but bedrock-samples does not ship, and one broken
# texture path that Aplok Guns has always had (debug geometry that never renders)
ENGINE_OK = {'animation.humanoid.fishing_rod', 'controller.animation.player.base', 'controller.animation.player.hudplayer',
             'textures/blocks/container_blue_side'}


def files_of(root):
    return [os.path.relpath(p, root).replace(os.sep, '/') for p in glob.glob(os.path.join(root, '**', '*'), recursive=True) if os.path.isfile(p)]


class Pack:
    def __init__(self, root):
        self.root = root
        self.files = files_of(root)
        self.json = {}
        for f in self.files:
            if f.endswith(('.json', '.material')):
                try:
                    self.json[f] = rjson(os.path.join(root, f))
                except Exception as e:
                    self.json[f] = e
        self.tex = {os.path.splitext(f)[0] for f in self.files if f.startswith('textures/') and f.endswith(('.png', '.tga', '.jpg'))}
        self.defs = {k: set() for k in ('geometry', 'animation', 'controller', 'render', 'particle', 'material', 'sound_event', 'entity', 'attachable', 'item', 'block', 'fog')}
        for f, d in self.json.items():
            if not isinstance(d, dict):
                continue
            for g in d.get('minecraft:geometry', []) if isinstance(d.get('minecraft:geometry'), list) else []:
                self.defs['geometry'].add(g['description']['identifier'])
            for k in d:
                if k.startswith('geometry.'):
                    self.defs['geometry'].add(k.split(':')[0])
            for key, field in (('animation', 'animations'), ('controller', 'animation_controllers'), ('render', 'render_controllers')):
                if isinstance(d.get(field), dict):
                    self.defs[key] |= set(d[field])
            if 'particle_effect' in d:
                self.defs['particle'].add(d['particle_effect']['description']['identifier'])
            if f.endswith('.material'):
                self.defs['material'] |= {k.split(':')[0] for k in d.get('materials', {})}
            if f == 'sounds/sound_definitions.json':
                self.defs['sound_event'] |= set(d.get('sound_definitions', d))
            for key, kind in (('minecraft:client_entity', 'entity'), ('minecraft:attachable', 'attachable'), ('minecraft:item', 'item'),
                              ('minecraft:block', 'block'), ('minecraft:entity', 'entity'), ('minecraft:fog_settings', 'fog')):
                if key in d:
                    self.defs[kind].add(d[key]['description']['identifier'])
        it = self.json.get('textures/item_texture.json')
        self.item_tex = it.get('texture_data', {}) if isinstance(it, dict) else {}


def validate(out, groups, log=print):
    """groups: {name: [pack folder names]} - the first packs of a group are checked, all packs of the group are visible"""
    problems = []
    packs = {}
    for g, names in groups.items():
        for n in names:
            if n not in packs:
                packs[n] = Pack(os.path.join(out, n))

    def P(msg):
        problems.append(msg)

    for g, names in groups.items():
        vis = [packs[n] for n in names]
        has = lambda kind, v: v in ENGINE_OK or v in VAN.get(kind, set()) or any(v in p.defs[kind] for p in vis)
        tex_ok = lambda t: (t in ENGINE_OK or os.path.splitext(t)[0] in VAN['texture'] or any(os.path.splitext(t)[0] in p.tex for p in vis))
        item_tex = {}
        for p in vis:
            item_tex.update(p.item_tex)
        for n in names[:1] + [x for x in names[1:] if x.startswith(g_prefix(g))]:
            pk = packs[n]
            for f, d in pk.json.items():
                where = f'{n}/{f}'
                if isinstance(d, Exception):
                    P(f'{where}: JSON error {d}')
                    continue
                if not isinstance(d, dict):
                    continue
                for key in ('minecraft:client_entity', 'minecraft:attachable'):
                    if key not in d:
                        continue
                    desc = d[key]['description']
                    for gid in (desc.get('geometry') or {}).values():
                        if not has('geometry', gid):
                            P(f'{where}: geometry {gid} missing')
                    for t in (desc.get('textures') or {}).values():
                        if not tex_ok(t):
                            P(f'{where}: texture {t} missing')
                    for a in (desc.get('animations') or {}).values():
                        if not (has('animation', a) or has('controller', a)):
                            P(f'{where}: animation {a} missing')
                    for rc in desc.get('render_controllers') or []:
                        rid = rc if isinstance(rc, str) else next(iter(rc))
                        if not has('render', rid):
                            P(f'{where}: render controller {rid} missing')
                    for m in (desc.get('materials') or {}).values():
                        if not (has('material', m.split(':')[0]) or m in VANILLA_MATERIALS):
                            P(f'{where}: material {m} missing')
                    for pe in (desc.get('particle_effects') or {}).values():
                        if not has('particle', pe):
                            P(f'{where}: particle {pe} missing')
                    for se in (desc.get('sound_effects') or {}).values():
                        sid = se.get('effect') if isinstance(se, dict) else se
                        if sid and not has('sound_event', sid):
                            P(f'{where}: sound {sid} missing')
                if 'particle_effect' in d:
                    t = d['particle_effect']['description'].get('basic_render_parameters', {}).get('texture')
                    if t and not tex_ok(t):
                        P(f'{where}: particle texture {t} missing')
                if f == 'sounds/sound_definitions.json':
                    for ev, v in d.get('sound_definitions', d).items():
                        if not isinstance(v, dict):
                            continue
                        for s in v.get('sounds', []):
                            sp = s if isinstance(s, str) else s.get('name')
                            if sp in VAN['sound_file']:
                                continue
                            if not any(os.path.isfile(os.path.join(p.root, sp + e)) for p in vis for e in ('.ogg', '.fsb', '.wav', '')):
                                P(f'{where}: sound file {sp} missing ({ev})')
                if f == 'textures/item_texture.json':
                    for k, v in d.get('texture_data', {}).items():
                        t = v['textures']
                        for tt in (t if isinstance(t, list) else [t]):
                            tp = tt if isinstance(tt, str) else tt.get('path')
                            if not tex_ok(tp):
                                P(f'{where}: item texture {k} -> {tp} missing')
                if 'minecraft:item' in d:
                    icon = d['minecraft:item'].get('components', {}).get('minecraft:icon')
                    key = icon if isinstance(icon, str) else (icon or {}).get('texture') or ((icon or {}).get('textures') or {}).get('default')
                    if key and key not in item_tex:
                        P(f'{where}: icon {key} not in item_texture.json')
                if f.startswith('ui/'):
                    for s in walk_strings(d):
                        if isinstance(s, str) and s.startswith('textures/') and '$' not in s and not s.endswith('/'):
                            if not tex_ok(s):
                                P(f'{where}: UI texture {s} missing')
                if 'minecraft:entity' in d:
                    desc = d['minecraft:entity']['description']
                    for a in (desc.get('animations') or {}).values():
                        if not (has('animation', a) or has('controller', a)):
                            P(f'{where}: BP animation {a} missing')
            # scripts: relative imports resolve
            for f in pk.files:
                if not f.endswith('.js'):
                    continue
                src = open(os.path.join(pk.root, f), encoding='utf-8', errors='ignore').read()
                for m in re.findall(r'''\bimport\s*(?:[\w$\s{},*]+?\s*from\s*)?['"]([^'"@][^'"]*)['"]''', src):
                    if not m.startswith('.'):          # Aplok imports from the scripts root ('main/modules/core')
                        tgt = 'scripts/' + m
                        if tgt not in pk.files and tgt + '.js' not in pk.files:
                            P(f'{n}/{f}: import {m} not found')
                        continue
                    tgt = os.path.normpath(os.path.join(os.path.dirname(f), m)).replace(os.sep, '/')
                    if tgt not in pk.files and tgt + '.js' not in pk.files:
                        P(f'{n}/{f}: import {m} not found')
    for p in problems:
        log('  ! ' + p)
    log(f'validate: {len(problems)} problem(s) in {", ".join(groups)}')
    return problems


def g_prefix(g):
    return {'core': 'Succubi Server', 'guns': 'Succubi Guns'}.get(g, g)
