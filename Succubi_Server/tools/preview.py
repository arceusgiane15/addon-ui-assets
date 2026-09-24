import numpy as np, json
from PIL import Image, ImageDraw
from xf import R, bone_mats
import pose

def geo_faces(g, tex, bone_filter=None):
    """faces in root-local coords: all bones except the root are transformed by their own default rotations
    (root default rotation is assumed none). returns list of (pts Nx3, rgb)."""
    tw, th = g['description'].get('texture_width', 16), g['description'].get('texture_height', 16)
    mats = bone_mats(g['bones'])
    root = g['bones'][0]['name']
    out = []
    for b in g['bones']:
        A, t = mats[b['name']]
        pm = b.get('poly_mesh')
        if pm:
            P = np.array(pm['positions'], float); U = pm['uvs']; norm = pm.get('normalized_uvs', False)
            for poly in pm['polys']:
                pts = P[[v[0] for v in poly]]
                uv = np.mean([U[v[2]] for v in poly], axis=0)
                if norm: px, py = uv[0] * tex.width, (1 - uv[1]) * tex.height
                else: px, py = uv[0] / tw * tex.width, uv[1] / th * tex.height
                c = tex.getpixel((int(min(tex.width - 1, max(0, px))), int(min(tex.height - 1, max(0, py)))))
                if c[3] < 8: continue
                out.append(((A @ pts.T).T + t, c[:3]))
        for c in b.get('cubes', []):
            o = np.array(c['origin'], float); s = np.array(c['size'], float)
            corners = lambda idx: np.array([[o[0] + s[0] * i, o[1] + s[1] * j, o[2] + s[2] * k] for i, j, k in idx])
            faces = {'north': [(0,0,0),(1,0,0),(1,1,0),(0,1,0)], 'south': [(0,0,1),(1,0,1),(1,1,1),(0,1,1)],
                     'east': [(1,0,0),(1,0,1),(1,1,1),(1,1,0)], 'west': [(0,0,0),(0,0,1),(0,1,1),(0,1,0)],
                     'up': [(0,1,0),(1,1,0),(1,1,1),(0,1,1)], 'down': [(0,0,0),(1,0,0),(1,0,1),(0,0,1)]}
            uvd = c.get('uv', {})
            for fname, idx in faces.items():
                col = (200, 200, 200)
                if isinstance(uvd, dict) and fname in uvd:
                    u0 = np.array(uvd[fname]['uv'], float) + np.array(uvd[fname]['uv_size'], float) / 2
                    cc = tex.getpixel((int(min(tex.width - 1, max(0, u0[0] / tw * tex.width))), int(min(tex.height - 1, max(0, u0[1] / th * tex.height)))))
                    if cc[3] < 8: continue
                    col = cc[:3]
                pts = corners(idx)
                if c.get('rotation'):
                    piv = np.array(c.get('pivot', [0, 0, 0]), float)
                    pts = piv + (R(c['rotation']) @ (pts - piv).T).T
                out.append(((A @ pts.T).T + t, col))
    return out

def box_faces(o, s, M=None, piv=None, color=(230, 190, 150)):
    o = np.array(o, float); s = np.array(s, float)
    C = lambda i, j, k: o + s * np.array([i, j, k])
    quads = [[C(0,0,0),C(1,0,0),C(1,1,0),C(0,1,0)], [C(0,0,1),C(1,0,1),C(1,1,1),C(0,1,1)], [C(1,0,0),C(1,0,1),C(1,1,1),C(1,1,0)],
             [C(0,0,0),C(0,0,1),C(0,1,1),C(0,1,0)], [C(0,1,0),C(1,1,0),C(1,1,1),C(0,1,1)], [C(0,0,0),C(1,0,0),C(1,0,1),C(0,0,1)]]
    out = []
    for q in quads:
        q = np.array(q)
        if M is not None: q = M(q)
        out.append((q, color))
    return out

def shade(c, n, light=np.array([0.3, 0.8, -0.5])):
    l = light / np.linalg.norm(light)
    k = 0.55 + 0.45 * abs(float(n @ l))
    return tuple(int(min(255, x * k)) for x in c)

def render(faces, project, size=(360, 300), bg=(70, 75, 90), label=''):
    img = Image.new('RGB', size, bg); dr = ImageDraw.Draw(img)
    items = []
    for pts, col in faces:
        pr = [project(p) for p in pts]
        if any(p is None for p in pr): continue
        depth = np.mean([p[2] for p in pr])
        n = np.cross(pts[1] - pts[0], pts[2] - pts[0]); nn = np.linalg.norm(n)
        n = n / nn if nn > 1e-9 else np.array([0, 1, 0])
        items.append((depth, [(p[0], p[1]) for p in pr], shade(col, n)))
    for d, xy, c in sorted(items, key=lambda x: -x[0]):
        dr.polygon(xy, fill=c)
    dr.text((4, size[1] - 14), label, fill=(255, 255, 255))
    return img

def proj_1p(size=(360, 300), fov=70):
    f = (size[1] / 2) / np.tan(np.radians(fov / 2))
    def p(x):
        v = x - pose.EYE_1P
        if v[2] < 0.5: return None
        return (size[0] / 2 + f * v[0] / v[2], size[1] / 2 - f * v[1] / v[2], v[2])
    return p

def proj_ortho(right, up, fwd, center, scale, size=(360, 300)):
    right, up, fwd = map(lambda a: np.array(a, float), (right, up, fwd))
    def p(x):
        v = x - center
        return (size[0] / 2 + scale * (v @ right), size[1] / 2 - scale * (v @ up), v @ fwd)
    return p

def player_faces(A_arm, hand):
    fs = []
    fs += box_faces([-4, 24, -4], [8, 8, 8], color=(120, 90, 70))        # head
    fs += box_faces([-4, 12, -2], [8, 12, 4], color=(60, 110, 170))      # body
    fs += box_faces([4, 12, -2], [4, 12, 4], color=(230, 190, 150))       # left arm
    fs += box_faces([-4, 0, -2], [8, 12, 4], color=(50, 50, 90))          # legs
    # right arm posed about its pivot
    fs += box_faces([-8, 12, -2], [4, 12, 4], M=lambda q: pose.ARM_PIVOT + (A_arm @ (q - pose.ARM_PIVOT).T).T, color=(240, 200, 160))
    # mouth marker
    fs += box_faces([-1.5, 25, -4.3], [3, 1, 0.3], color=(200, 40, 40))
    return fs
