"""Compute hold/eat poses for food attachables and emit animation JSON + previews."""
import sys, json, numpy as np
sys.path.insert(0, 'tools')
import pose
from xf import R

MOUTH = np.array([0.0, 25.5, -4.5])

def n(v):
    v = np.array(v, float); return v / np.linalg.norm(v)

# Target poses in world(body) space. kind: 'plate' (eat from a dish) or 'hand' (drink / hand-held snack)
def targets(kind):
    A3, h3 = pose.arm_3p(0.0)
    A3e, h3e = pose.arm_3p(1.0)
    A1, h1 = pose.arm_1p()
    E = pose.EYE_1P
    toward_cam_1p = n(E - h1)
    T = {}
    if kind == 'plate':
        T['tp_hold'] = dict(arm=(A3, h3), up=[0, 1, 0], front=[0, 0, -1], at=h3 + np.array([0.3, 0.6, -2.2]))
        T['tp_eat'] = dict(arm=(A3e, h3e), up=n([0.15, 1, 0.75]), front=[0, 0, -1], at=MOUTH + np.array([-0.6, -3.2, -4.0]))
        T['fp_hold'] = dict(arm=(A1, h1), up=n([0, 1, -0.5]), front=-toward_cam_1p, at=h1 + np.array([-4.0, 3.5, -1.0]))
        T['fp_eat'] = dict(arm=(A1, h1), up=n([0, 0.9, -0.8]), front=[0, -1, 0], at=E + np.array([1.2, -7.5, 13.0]))
    else:
        T['tp_hold'] = dict(arm=(A3, h3), up=[0, 1, 0], front=[0, 0, -1], at=h3 + np.array([0.3, 0.2, -1.2]))
        T['tp_eat'] = dict(arm=(A3e, h3e), up=n([0.2, 0.75, 0.9]), front=[0, 0, -1], at=MOUTH + np.array([-0.4, -2.2, -3.6]))
        T['fp_hold'] = dict(arm=(A1, h1), up=n([-0.15, 1, -0.3]), front=-toward_cam_1p, at=h1 + np.array([-3.0, 3.5, -1.0]))
        T['fp_eat'] = dict(arm=(A1, h1), up=n([-0.05, 0.6, -1.0]), front=[0, -1, 0], at=E + np.array([1.0, -6.0, 11.5]))
    return T

def solve_all(kind, U, F, C, pivot, scale):
    out = {}
    for key, t in targets(kind).items():
        A, hand = t['arm']
        rot, pos, Q = pose.solve(A, hand, U, F, C, np.array(pivot, float), t['up'], t['front'], t['at'], scale)
        out[key] = dict(rotation=rot, position=pos)
    return out
