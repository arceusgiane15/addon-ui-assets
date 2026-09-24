"""Render every built food attachable from out/ using the generated animations (1P/3P hold & eat)."""
import sys, json, re, numpy as np
sys.path.insert(0, 'tools')
from PIL import Image
import pose, preview, foodpose
from xf import R, bone_mats
RP = 'out/Succubi Server RP/'
anims = json.load(open(RP + 'animations/succubi_food.animation.json'))['animations']

def ev(expr, fp=True):
    if isinstance(expr, (int, float)): return float(expr)
    e = expr.replace("c.item_slot == 'off_hand'", '0').replace('math.sin', 'np.sin').replace('q.life_time', '0')
    e = re.sub(r'(\S+) \? (\S+) : (\S+)', lambda m: m.group(3) if m.group(1) == '0' else m.group(2), e)
    return float(eval(e))

def geo_by_id():
    out = {}
    import glob
    for f in glob.glob(RP + 'models/entity/succubi_food*.geo.json'):
        for g in json.load(open(f))['minecraft:geometry']:
            out[g['description']['identifier']] = g
    return out
GEOS = geo_by_id()

def render_attachable(path):
    a = json.load(open(path))['minecraft:attachable']['description']
    g = GEOS[a['geometry']['default']]
    tex = Image.open(RP + a['textures']['default'] + '.png').convert('RGBA')
    fs0 = preview.geo_faces(g, tex)  # root-local
    root = g['bones'][0]; pivot = np.array(root['pivot'], float)
    kind = 'plate' if '.plate.' in a['animations']['hold_fp'] else 'hand'
    T = foodpose.targets(kind)
    ims = []
    for st in ('hold_fp', 'eat_fp', 'hold_tp', 'eat_tp'):
        an = anims[a['animations'][st]]['bones'][root['name']]
        rot = [ev(x) for x in an['rotation']]; pos = [ev(x) for x in an['position']]; sc = ev(an['scale'])
        A, hand = T[('fp_' if st.endswith('fp') else 'tp_') + st.split('_')[0]]['arm']
        Q = R(rot)
        item = [(hand + (A @ ((pivot + np.array(pos) + (Q @ (sc * (p - pivot)).T).T) - pose.H0).T).T, c) for p, c in fs0]
        if st.endswith('fp'):
            ims.append(preview.render(item, preview.proj_1p((220, 180)), size=(220, 180), label=st))
        else:
            body = preview.player_faces(A, hand) + item
            ims.append(preview.render(body, preview.proj_ortho([0.64, 0, -0.77], [0, 1, 0], [0.77, 0, 0.64], np.array([-2, 20, 0]), 6.5, (220, 180)), size=(220, 180), label=st))
    W = Image.new('RGB', (880, 180))
    for i, im in enumerate(ims): W.paste(im, (i * 220, 0))
    return a['identifier'], W

if __name__ == '__main__':
    import glob
    files = sorted(glob.glob(RP + 'attachables/food/*.json'))[:: int(sys.argv[1]) if len(sys.argv) > 1 else 1]
    files += [RP + 'attachables/succubi_food/drink_water_bottle.json', RP + 'attachables/succubi_food/snack_cookies.json']
    rows = [render_attachable(f) for f in files]
    for chunk in range(0, len(rows), 7):
        part = rows[chunk:chunk + 7]
        W = Image.new('RGB', (880 + 180, 180 * len(part)), (20, 20, 20))
        from PIL import ImageDraw
        for i, (ident, im) in enumerate(part):
            W.paste(im, (180, i * 180)); ImageDraw.Draw(W).text((4, i * 180 + 80), ident, fill=(255, 255, 255))
        W.save(f'view/verify_{chunk // 7}.png')
    print(len(rows))
