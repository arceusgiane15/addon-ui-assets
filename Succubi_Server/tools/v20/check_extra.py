"""Extra consistency checks on a built output: player.json events/groups, UI element references, HUD data control."""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import rjson, walk_strings, CORE_BP, CORE_RP, GUNS_BP, GUNS_RP

def player_ok(path):
    e = rjson(path)['minecraft:entity']
    groups = set(e.get('component_groups', {}))
    events = set(e.get('events', {}))
    bad = []
    def walk(node):
        if isinstance(node, dict):
            for k in ('add', 'remove'):
                if isinstance(node.get(k), dict):
                    for g in node[k].get('component_groups', []):
                        if g not in groups:
                            bad.append(f'group {g}')
            if 'trigger' in node and isinstance(node['trigger'], str) and node['trigger'] not in events:
                bad.append(f'trigger {node["trigger"]}')
            if 'event' in node and isinstance(node['event'], str) and ':' in node['event'] and node['event'] not in events:
                bad.append(f'event {node["event"]}')
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(e)
    return bad

def ui_refs(rp):
    ns = {}
    for p in glob.glob(os.path.join(rp, 'ui', '*.json')):
        d = rjson(p)
        if isinstance(d, dict) and 'namespace' in d:
            ns.setdefault(d['namespace'], set()).update(k.split('@')[0] for k in d if k != 'namespace')
    own = {n for n in ns if n.startswith('succubi')}
    bad = []
    for p in glob.glob(os.path.join(rp, 'ui', '*.json')):
        for s in walk_strings(rjson(p)):
            for m in re.findall(r'@(succubi\w*)\.(\w+)', s):
                if m[0] not in ns or m[1] not in ns[m[0]]:
                    bad.append(f'{os.path.basename(p)}: @{m[0]}.{m[1]}')
            m = re.match(r'^(succubi\w*)\.(\w+)$', s)
            if m and (m.group(1) not in ns or m.group(2) not in ns[m.group(1)]):
                bad.append(f'{os.path.basename(p)}: {s}')
    return bad

if __name__ == '__main__':
    out = sys.argv[1]
    for p in (CORE_BP, GUNS_BP):
        print(p, 'player.json:', player_ok(os.path.join(out, p, 'entities/player.json')) or 'ok')
    print('core UI refs:', ui_refs(os.path.join(out, CORE_RP)) or 'ok')
    defs = rjson(os.path.join(out, CORE_RP, 'ui/_ui_defs.json'))['ui_defs']
    print('core ui_defs:', defs)
    print('guns ui_defs:', rjson(os.path.join(out, GUNS_RP, 'ui/_ui_defs.json'))['ui_defs'])
