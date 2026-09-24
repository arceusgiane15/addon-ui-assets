"""Software renderer for Bedrock geometry (cubes with box / per-face UV, bone pivots + rotations, poly_mesh),
textured, z-buffered, with simple lighting. Used for model previews and for rendering item icons.

    render(geo_path, identifier, texture_path, view='icon', size=256) -> PIL image"""
import math
import numpy as np
from PIL import Image
from common import rjson

FACE_DIRS = {
    # face: (normal, corner order as (x,y,z) picks from (min,max) per axis, looking at the face from outside)
    'north': (np.array([0, 0, -1.0]), [(1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)]),
    'south': (np.array([0, 0, 1.0]), [(0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)]),
    'east': (np.array([1.0, 0, 0]), [(1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)]),
    'west': (np.array([-1.0, 0, 0]), [(0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)]),
    'up': (np.array([0, 1.0, 0]), [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)]),
    'down': (np.array([0, -1.0, 0]), [(0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)]),
}


def rot(rx, ry, rz):
    """Bedrock bone/cube rotation (degrees), applied Z then Y then X on the (flipped-X) model"""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return X @ Y @ Z


def load_geo(path, ident=None):
    d = rjson(path)
    geos = d.get('minecraft:geometry') or []
    if not geos:          # legacy format
        for k, v in d.items():
            if k.startswith('geometry.') and (ident is None or k.split(':')[0] == ident):
                v = dict(v)
                v['description'] = {'identifier': k.split(':')[0], 'texture_width': v.get('texturewidth', 64), 'texture_height': v.get('textureheight', 64)}
                return v
    for g in geos:
        if ident is None or g['description']['identifier'] == ident:
            return g
    raise KeyError(ident)


def box_uv(uv, size, mirror=False):
    """per-face uv rects [u, v, w, h] for Minecraft box UV"""
    u, v = uv
    w, h, d = size
    f = {
        'east': [u, v + d, d, h], 'north': [u + d, v + d, w, h], 'west': [u + d + w, v + d, d, h], 'south': [u + 2 * d + w, v + d, w, h],
        'up': [u + d, v, w, d], 'down': [u + d + w, v + d, w, -d],
    }
    if mirror:
        f['east'], f['west'] = f['west'], f['east']
    return f


def geo_quads(g):
    """[(4 world points, 4 uv points (texture px), normal)]"""
    tw = g['description'].get('texture_width', 64)
    th = g['description'].get('texture_height', 64)
    bones = {b['name']: b for b in g.get('bones', [])}

    def bone_matrix(b):
        """returns function mapping a point in bone space to model space (applying parents)"""
        chain = []
        cur = b
        while cur is not None:
            chain.append(cur)
            cur = bones.get(cur.get('parent'))
        def f(p):
            for c in chain:
                if c.get('rotation'):
                    piv = np.array(c.get('pivot', [0, 0, 0]), float)
                    r = c['rotation']
                    p = (rot(-r[0], -r[1], r[2]) @ ((p - piv) * np.array([-1, 1, 1]))) * np.array([-1, 1, 1]) + piv
            return p
        return f

    quads = []
    for b in g.get('bones', []):
        tf = bone_matrix(b)
        for cube in b.get('cubes', []):
            o = np.array(cube['origin'], float)
            s = np.array(cube['size'], float)
            inf = cube.get('inflate', 0)
            lo, hi = o - inf, o + s + inf
            uv = cube.get('uv', [0, 0])
            faces = uv if isinstance(uv, dict) else box_uv(uv, s, cube.get('mirror', b.get('mirror', False)))
            cr = cube.get('rotation')
            cpiv = np.array(cube.get('pivot', [0, 0, 0]), float)
            for face, (n, corners) in FACE_DIRS.items():
                fu = faces.get(face)
                if fu is None:
                    continue
                if isinstance(fu, dict):
                    u0, v0 = fu['uv']
                    uw, vh = fu.get('uv_size', [s[0], s[1]])
                else:
                    u0, v0, uw, vh = fu
                pts = []
                for c in corners:
                    p = np.array([hi[i] if c[i] else lo[i] for i in range(3)])
                    if cr:
                        p = (rot(-cr[0], -cr[1], cr[2]) @ ((p - cpiv) * np.array([-1, 1, 1]))) * np.array([-1, 1, 1]) + cpiv
                    pts.append(tf(p))
                uvs = [(u0, v0), (u0 + uw, v0), (u0 + uw, v0 + vh), (u0, v0 + vh)]
                quads.append((pts, [(a / tw, bb / th) for a, bb in uvs]))
        pm = b.get('poly_mesh')
        if pm:
            P, U = pm['positions'], pm['uvs']
            norm = pm.get('normalized_uvs', False)
            for poly in pm['polys']:
                pts = [tf(np.array(P[v[0]], float)) for v in poly]
                uvs = [U[v[2]] for v in poly]
                uvs = [(uu, 1 - vv) if norm else (uu / tw, vv / th) for uu, vv in uvs]
                if len(pts) == 3:
                    pts.append(pts[2]); uvs.append(uvs[2])
                quads.append((pts, uvs))
    return quads


def camera(view):
    if view == 'icon':          # classic 3/4 item icon view
        return rot(30, -45, 0)
    if view == 'front':
        return rot(0, 180, 0)
    if view == 'side':
        return rot(0, 90, 0)
    if view == 'three':
        return rot(20, 150, 0)
    if isinstance(view, tuple):
        return rot(*view)
    return np.eye(3)


def render(geo_path, ident, tex_path, view='icon', size=256, pad=0.08, light=(0.35, 0.9, 0.55), bg=None, quads=None, fit=None):
    g = load_geo(geo_path, ident) if quads is None else None
    quads = quads if quads is not None else geo_quads(g)
    tex = np.asarray(Image.open(tex_path).convert('RGBA')).astype(float) if isinstance(tex_path, str) else np.asarray(tex_path.convert('RGBA')).astype(float)
    TH, TW = tex.shape[:2]
    M = camera(view)
    L = np.array(light) / np.linalg.norm(light)
    tri = []
    allp = []
    for pts, uvs in quads:
        P = [M @ p for p in pts]
        allp += P
        tri.append((P, uvs))
    if not allp:
        return Image.new('RGBA', (size, size))
    A = np.array(allp)
    mn, mx = A.min(0), A.max(0)
    if fit is None:
        span = max(mx[0] - mn[0], mx[1] - mn[1]) * (1 + 2 * pad) + 1e-6
        cx, cy = (mx[0] + mn[0]) / 2, (mx[1] + mn[1]) / 2
    else:
        span, cx, cy = fit
    sc = size / span
    S = size * 2                       # supersample
    img = np.zeros((S, S, 4))
    zb = np.full((S, S), -1e9)
    for P, uvs in tri:
        n = np.cross(P[1] - P[0], P[2] - P[0])
        if np.linalg.norm(n) < 1e-9:
            n = np.cross(P[2] - P[0], P[3] - P[0])
        nn = n / (np.linalg.norm(n) + 1e-9)
        shade = 0.55 + 0.45 * max(0.0, float(np.dot(nn, L))) + 0.1 * max(0.0, nn[1])
        for a, b, c in ((0, 1, 2), (0, 2, 3)):
            raster(img, zb, [P[a], P[b], P[c]], [uvs[a], uvs[b], uvs[c]], tex, TW, TH, sc * 2, cx, cy, S, shade)
    out = Image.fromarray(np.clip(img, 0, 255).astype('uint8'), 'RGBA').resize((size, size), Image.LANCZOS)
    if bg:
        base = Image.new('RGBA', out.size, bg)
        base.alpha_composite(out)
        return base
    return out


def raster(img, zb, P, UV, tex, TW, TH, sc, cx, cy, S, shade):
    xs = [(p[0] - cx) * sc + S / 2 for p in P]
    ys = [S / 2 - (p[1] - cy) * sc for p in P]
    zs = [p[2] for p in P]
    x0, x1 = max(0, int(min(xs))), min(S - 1, int(max(xs)) + 1)
    y0, y1 = max(0, int(min(ys))), min(S - 1, int(max(ys)) + 1)
    if x1 < x0 or y1 < y0:
        return
    area = (xs[1] - xs[0]) * (ys[2] - ys[0]) - (xs[2] - xs[0]) * (ys[1] - ys[0])
    if abs(area) < 1e-9:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    w0 = ((xs[1] - gx) * (ys[2] - gy) - (xs[2] - gx) * (ys[1] - gy)) / area
    w1 = ((xs[2] - gx) * (ys[0] - gy) - (xs[0] - gx) * (ys[2] - gy)) / area
    w2 = 1 - w0 - w1
    m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
    if not m.any():
        return
    z = w0 * zs[0] + w1 * zs[1] + w2 * zs[2]
    u = w0 * UV[0][0] + w1 * UV[1][0] + w2 * UV[2][0]
    v = w0 * UV[0][1] + w1 * UV[1][1] + w2 * UV[2][1]
    tx = np.clip((u * TW).astype(int), 0, TW - 1)
    ty = np.clip((v * TH).astype(int), 0, TH - 1)
    col = tex[ty, tx]
    m &= col[..., 3] > 16
    sub = zb[y0:y1 + 1, x0:x1 + 1]
    m &= z > sub
    if not m.any():
        return
    sub[m] = z[m]
    region = img[y0:y1 + 1, x0:x1 + 1]
    c = col.copy()
    c[..., :3] *= shade
    region[m] = c[m]
    region[m, 3] = 255
