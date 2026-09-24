# Tiny orthographic renderer for Bedrock geo (poly_mesh only + cubes as boxes) to inspect orientation.
import json, sys, numpy as np
from PIL import Image, ImageDraw

def load(path, ident=None):
    d = json.load(open(path))
    for g in d['minecraft:geometry']:
        if ident is None or g['description']['identifier'] == ident:
            return g
    raise KeyError(ident)

def faces(g, tex):
    """yield (list of 3d points, rgb) in model space (bone rotations ignored unless apply_rot)"""
    tw, th = g['description'].get('texture_width', 16), g['description'].get('texture_height', 16)
    out = []
    for b in g['bones']:
        pm = b.get('poly_mesh')
        if not pm: continue
        P = pm['positions']; U = pm['uvs']; norm = pm.get('normalized_uvs', False)
        for poly in pm['polys']:
            pts = [P[v[0]] for v in poly]
            uvs = [U[v[2]] for v in poly]
            u = np.mean([x[0] for x in uvs]); v = np.mean([x[1] for x in uvs])
            if not norm: u /= tw; v /= th
            px = min(tex.width - 1, max(0, int(u * tex.width))); py = min(tex.height - 1, max(0, int((1 - v if norm else v) * tex.height)))
            # sample a few texels around
            c = tex.getpixel((px, py))
            if c[3] < 10: continue
            out.append((b['name'], np.array(pts, float), c[:3]))
    return out

def rot_matrix(rx, ry, rz):
    rx, ry, rz = np.radians([rx, ry, rz])
    X = np.array([[1,0,0],[0,np.cos(rx),-np.sin(rx)],[0,np.sin(rx),np.cos(rx)]])
    Y = np.array([[np.cos(ry),0,np.sin(ry)],[0,1,0],[-np.sin(ry),0,np.cos(ry)]])
    Z = np.array([[np.cos(rz),-np.sin(rz),0],[np.sin(rz),np.cos(rz),0],[0,0,1]])
    return X, Y, Z

def view(fs, direction, size=300):
    # direction: 'front' looks from -Z toward +Z (sees north faces), etc. Returns image.
    # axes: screen x, screen y(up), depth(toward viewer)
    V = {
        'north(-z)': (np.array([-1,0,0]), np.array([0,1,0]), np.array([0,0,-1])),  # viewer at -z looking +z
        'south(+z)': (np.array([1,0,0]), np.array([0,1,0]), np.array([0,0,1])),
        'east(+x)': (np.array([0,0,-1]), np.array([0,1,0]), np.array([1,0,0])),
        'west(-x)': (np.array([0,0,1]), np.array([0,1,0]), np.array([-1,0,0])),
        'top(+y)': (np.array([1,0,0]), np.array([0,0,-1]), np.array([0,1,0])),
    }[direction]
    sx, sy, sd = V
    allp = np.concatenate([f[1] for f in fs])
    X = allp @ sx; Y = allp @ sy
    cx, cy = (X.max()+X.min())/2, (Y.max()+Y.min())/2
    span = max(X.max()-X.min(), Y.max()-Y.min()) * 1.1 + 1e-6
    sc = size / span
    img = Image.new('RGB', (size, size + 16), (60, 60, 70)); dr = ImageDraw.Draw(img)
    order = sorted(fs, key=lambda f: np.mean(f[1] @ sd))
    for name, pts, c in order:
        xy = [((p @ sx - cx) * sc + size/2, size/2 - (p @ sy - cy) * sc) for p in pts]
        dr.polygon(xy, fill=tuple(c))
    dr.text((4, size + 2), direction, fill=(255,255,255))
    return img

if __name__ == '__main__':
    geo, ident, texp, outp = sys.argv[1], (sys.argv[2] if sys.argv[2] != '-' else None), sys.argv[3], sys.argv[4]
    g = load(geo, ident); tex = Image.open(texp).convert('RGBA')
    fs = faces(g, tex)
    ims = [view(fs, d, 220) for d in ['north(-z)', 'south(+z)', 'east(+x)', 'west(-x)', 'top(+y)']]
    W = Image.new('RGB', (220*5, 236))
    for i, im in enumerate(ims): W.paste(im, (i*220, 0))
    W.save(outp)
    print(len(fs), 'faces')
