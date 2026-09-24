"""Pose solver + preview for held food attachables (Bedrock space: front=-z, up=+y, player's right=-x).
Validated against vanilla trident/spyglass: bound item frame = rightItem bone frame, model point H0 ~ hand."""
import numpy as np, json
from xf import R, Rx, Ry, Rz

H0 = np.array([0.0, 22.5, -0.5])        # model point that sits in the fist when bound to the item bone
ARM_PIVOT = np.array([-5.0, 22.0, 0.0])
ITEM_PIVOT = np.array([-6.0, 15.0, 1.0])

def euler_from_matrix(M):
    """Inverse of R(rot) = Rz(-rz) Ry(ry) Rx(-rx). Returns [rx, ry, rz] degrees."""
    # M = Rz(c) Ry(b) Rx(a) with a=-rx, b=ry, c=-rz  (standard ZYX)
    b = np.arcsin(-np.clip(M[2, 0], -1, 1))
    if abs(np.cos(b)) > 1e-6:
        a = np.arctan2(M[2, 1], M[2, 2]); c = np.arctan2(M[1, 0], M[0, 0])
    else:
        a = np.arctan2(-M[1, 2], M[1, 1]); c = 0.0
    a, b, c = np.degrees([a, b, c])
    return [round(float(-a), 2), round(float(b), 2), round(float(-c), 2)]

def frame(up, front):
    """rotation whose columns send local (+x,+y,-z(front)) to world; up, front are world dirs"""
    u = np.array(up, float); u /= np.linalg.norm(u)
    f = np.array(front, float); f = f - u * (f @ u); f /= np.linalg.norm(f)
    back = -f; x = np.cross(u, back)  # right-handed basis (x, y, z=back)
    return np.stack([x, u, back], axis=1)

def local_frame(U, F):
    return frame(U, F)

# ---- arm frames ----
def arm_3p(use=0.0, bob=0.0):
    rot = np.array([-18.0, 0, 0]) + use * np.array([-60, -22.5, -5.625]) + bob * 11.25
    A = R(rot); hand = ARM_PIVOT + A @ (ITEM_PIVOT - ARM_PIVOT)
    return A, hand

ARM_1P_ROT = [95.0, -45.0, 115.0]
EYE_1P = np.array([0.0, 25.5, 0.0])
def arm_1p():
    A = R(ARM_1P_ROT); pivot = ARM_PIVOT + np.array([13.5, -10.0, 12.0])
    hand = pivot + A @ (ITEM_PIVOT - ARM_PIVOT + np.array([0, 0, -1.0]))
    return A, hand

def solve(A, hand, U, F, C, pivot, up_w, front_w, target_w, scale):
    """U,F: item up/front in root-local coords; C: item grip point in root-local model coords.
    Returns rotation (bedrock euler) + position offset for the root bone."""
    Lw = frame(up_w, front_w)            # desired world basis
    Lm = local_frame(U, F)               # item's own basis
    Q = A.T @ Lw @ Lm.T                  # rotation in bound frame
    T = H0 + A.T @ (np.array(target_w, float) - hand)   # target in bound model coords
    d = T - pivot - Q @ (scale * (np.array(C, float) - pivot))
    return euler_from_matrix(Q), [round(float(x), 2) for x in d], Q

def posed_points(P, A, hand, rot, pos, pivot, scale, child=None):
    """P model points (root-local already child-transformed) -> world."""
    Q = R(rot); pivot = np.asarray(pivot, float)
    X = pivot + np.asarray(pos, float) + (Q @ (scale * (P - pivot).T)).T
    return hand + (A @ (X - H0).T).T
