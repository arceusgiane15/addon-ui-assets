import sys, json, numpy as np
sys.path.insert(0, 'tools')
from PIL import Image
import preview
from xf import R

def model_icon(geo_path, tex_path, out, yaw=-35, pitch=22, size=64):
    g = json.load(open(geo_path))['minecraft:geometry'][0]
    tex = Image.open(tex_path).convert('RGBA')
    fs = preview.geo_faces(g, tex)
    M = R([pitch, 0, 0]) @ R([0, yaw, 0])
    fs = [((M @ p.T).T, c) for p, c in fs]
    allp = np.concatenate([p for p, c in fs]); mn, mx = allp.min(0), allp.max(0)
    ctr = (mn + mx) / 2; span = max(mx[0] - mn[0], mx[1] - mn[1])
    S = 4
    im = preview.render(fs, preview.proj_ortho([-1, 0, 0], [0, 1, 0], [0, 0, 1], ctr, size * S * 0.92 / span, (size * S, size * S)), size=(size * S, size * S), bg=(255, 0, 255))
    a = np.asarray(im).copy()
    alpha = ~((a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255))
    rgba = np.dstack([a, (alpha * 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').resize((size, size), Image.LANCZOS).save(out)

if __name__ == '__main__':
    base = 'work/Succubi Server RP/'
    for m in ('drink', 'snack'):
        model_icon(base + f'models/entity/succubi_{m}_vending_machine.geo.json', base + f'textures/entity/succubi/{m}_vending_machine.png', f'view/{m}_placer.png')
