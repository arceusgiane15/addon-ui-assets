"""Rebuild Food Items geometry into a clean hand-bound attachable model (upright, grip at H0)."""
import json, copy, numpy as np
import pose

def merge_meshes(g, include=None, offsets=None):
    """flatten all poly_mesh bones (ignoring their rotations: raw positions are authored upright)"""
    P, N, UV, polys = [], [], [], []
    for b in g['bones']:
        pm = b.get('poly_mesh')
        if not pm or (include and b['name'] not in include): continue
        off = np.array((offsets or {}).get(b['name'], [0, 0, 0]), float)
        base_p, base_n, base_uv = len(P), len(N), len(UV)
        P += [list(np.array(p, float) + off) for p in pm['positions']]
        N += pm['normals']; UV += pm['uvs']
        for poly in pm['polys']:
            polys.append([[v[0] + base_p, v[1] + base_n, v[2] + base_uv] for v in poly])
        assert pm.get('normalized_uvs', False)
    return np.array(P), N, UV, polys

def build(g, ident, kind, target_size, include=None, offsets=None, grip_frac=0.3):
    P, N, UV, polys = merge_meshes(g, include, offsets)
    mn, mx = P.min(0), P.max(0)
    size = mx - mn
    if kind == 'plate':
        s = target_size / max(size[0], size[2])
        grip = np.array([(mn[0] + mx[0]) / 2, mn[1], (mn[2] + mx[2]) / 2])
    else:
        s = target_size / size[1]
        grip = np.array([(mn[0] + mx[0]) / 2, mn[1] + grip_frac * size[1], (mn[2] + mx[2]) / 2])
    Q = pose.H0 + (P - grip) * s
    geo = {
        "description": {
            "identifier": ident,
            "texture_width": g['description'].get('texture_width', 16),
            "texture_height": g['description'].get('texture_height', 16),
            "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1, 0]
        },
        "bones": [
            {"name": "succubi_food", "pivot": [round(float(x), 4) for x in pose.H0],
             "binding": "q.item_slot_to_bone_name(c.item_slot)"},
            {"name": "succubi_food_model", "parent": "succubi_food", "pivot": [round(float(x), 4) for x in pose.H0],
             "poly_mesh": {"normalized_uvs": True,
                           "positions": [[round(float(v), 4) for v in p] for p in Q],
                           "normals": N, "uvs": UV, "polys": polys}}
        ]
    }
    return geo
