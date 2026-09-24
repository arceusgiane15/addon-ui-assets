"""Build Bedrock poly_mesh geometry from code: lathes (bowls, buns, eggs, robes), extruded outlines (onigiri,
sandwiches, wings) and oriented boxes, all UV-mapped into regions of one texture painted by code.

Conventions (checked against the existing models): normalized UVs with v = 0 at the bottom of the texture,
counter-clockwise winding seen from outside (cross(b - a, c - a) points along the normal), quads only
(a triangle repeats its last vertex)."""
import math
import numpy as np


def _n(v):
    v = np.asarray(v, float)
    l = np.linalg.norm(v)
    return v / l if l > 1e-12 else v


class Mesh:
    def __init__(self, tex_w, tex_h):
        self.tw, self.th = tex_w, tex_h
        self.P, self.N, self.U, self.polys = [], [], [], []

    # uv given in texture pixels (x right, y down) -> normalized, v up
    def _uv(self, u, v):
        self.U.append([round(u / self.tw, 6), round(1 - v / self.th, 6)])
        return len(self.U) - 1

    def _p(self, p):
        self.P.append([round(float(c), 5) for c in p])
        return len(self.P) - 1

    def _nn(self, n):
        self.N.append([round(float(c), 5) for c in _n(n)])
        return len(self.N) - 1

    def face(self, pts, uvs, normals=None, flip=False):
        """3 or 4 points, uv pixel coords, optional per-vertex normals"""
        pts = [np.asarray(p, float) for p in pts]
        if flip:
            pts, uvs = pts[::-1], uvs[::-1]
            normals = normals[::-1] if normals else None
        fn = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        if np.linalg.norm(fn) < 1e-12 and len(pts) == 4:
            fn = np.cross(pts[2] - pts[0], pts[3] - pts[0])
        if normals is None:
            normals = [fn] * len(pts)
        verts = [[self._p(p), self._nn(n), self._uv(*uv)] for p, n, uv in zip(pts, normals, uvs)]
        if len(verts) == 3:
            verts.append(verts[2])
        self.polys.append(verts)

    # ------------------------------------------------------------------ primitives
    def lathe(self, profile, center, rect, segs=16, sx=1.0, sz=1.0, cap_bottom=None, cap_top=None, smooth=True, angle0=0.0):
        """profile [(r, y)] bottom->top; rect (x0, y0, x1, y1) texture px for the side (u around, v along profile);
        cap_* = rect for a flat disc when the profile ends with r > 0"""
        cx, cy, cz = center
        lens = [0.0]
        for (r0, y0), (r1, y1) in zip(profile, profile[1:]):
            lens.append(lens[-1] + math.hypot(r1 - r0, y1 - y0))
        total = lens[-1] or 1
        x0, y0t, x1, y1t = rect

        def pt(r, y, k):
            a = angle0 + 2 * math.pi * k / segs
            return np.array([cx + r * math.cos(a) * sx, y, cz + r * math.sin(a) * sz])

        def nrm(i, k):
            # profile tangent -> outward normal in the r/y plane
            ia, ib = max(0, i - 1), min(len(profile) - 1, i + 1)
            dr = profile[ib][0] - profile[ia][0]
            dy = profile[ib][1] - profile[ia][1]
            nr, ny = dy, -dr
            a = angle0 + 2 * math.pi * k / segs
            return np.array([nr * math.cos(a) / max(sx, 1e-6), ny, nr * math.sin(a) / max(sz, 1e-6)])

        for i in range(len(profile) - 1):
            (ra, ya), (rb, yb) = profile[i], profile[i + 1]
            va = y1t - (y1t - y0t) * lens[i] / total
            vb = y1t - (y1t - y0t) * lens[i + 1] / total
            for k in range(segs):
                ua = x0 + (x1 - x0) * k / segs
                ub = x0 + (x1 - x0) * (k + 1) / segs
                p = [pt(ra, ya, k), pt(ra, ya, k + 1), pt(rb, yb, k + 1), pt(rb, yb, k)]
                uv = [(ua, va), (ub, va), (ub, vb), (ua, vb)]
                ns = [nrm(i, k), nrm(i, k + 1), nrm(i + 1, k + 1), nrm(i + 1, k)] if smooth else None
                if ra < 1e-6:                                   # apex at the bottom
                    p, uv = [p[0], p[2], p[3]], [uv[0], uv[2], uv[3]]
                    ns = [ns[0], ns[2], ns[3]] if ns else None
                elif rb < 1e-6:                                 # apex at the top
                    p, uv = p[:3], uv[:3]
                    ns = ns[:3] if ns else None
                # outward for a profile going up with r > 0: order (k, k+1) runs +angle; flip to face out
                self.face(p, uv, ns, flip=True)
        for cap, (r, y), up in ((cap_bottom, profile[0], False), (cap_top, profile[-1], True)):
            if cap and r > 1e-6:
                self.disc((cx, y, cz), r, cap, up, segs, sx, sz, angle0)

    def disc(self, center, r, rect, up, segs=16, sx=1.0, sz=1.0, angle0=0.0):
        cx, cy, cz = center
        x0, y0, x1, y1 = rect
        mu, mv = (x0 + x1) / 2, (y0 + y1) / 2
        hu, hv = (x1 - x0) / 2, (y1 - y0) / 2
        c = np.array([cx, cy, cz])
        for k in range(segs):
            a = angle0 + 2 * math.pi * k / segs
            b = angle0 + 2 * math.pi * (k + 1) / segs
            pa = np.array([cx + r * math.cos(a) * sx, cy, cz + r * math.sin(a) * sz])
            pb = np.array([cx + r * math.cos(b) * sx, cy, cz + r * math.sin(b) * sz])
            uv = [(mu, mv), (mu + hu * math.cos(a), mv + hv * math.sin(a)), (mu + hu * math.cos(b), mv + hv * math.sin(b))]
            n = [0, 1, 0] if up else [0, -1, 0]
            pts = [c, pa, pb]
            # make winding match the wanted normal
            if np.dot(np.cross(pts[1] - pts[0], pts[2] - pts[0]), n) < 0:
                pts, uv = pts[::-1], uv[::-1]
            self.face(pts, uv, [n] * 3)

    def extrude(self, outline, z0, z1, side_rect, front_rect, back_rect=None, depth_axis='z'):
        """outline: [(x, y)] counter-clockwise seen from the front (-z); prism between z0 (front) and z1 (back).
        caps are mapped by the outline bounding box into front_rect / back_rect (back mirrored)"""
        pts = [np.array(p, float) for p in outline]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)

        def cap_uv(p, rect, mirror):
            x0, y0, x1, y1 = rect
            t = (p[0] - bx0) / max(1e-6, bx1 - bx0)
            if mirror:
                t = 1 - t
            s = (p[1] - by0) / max(1e-6, by1 - by0)
            return (x0 + (x1 - x0) * t, y1 - (y1 - y0) * s)

        def P3(p, z):
            return np.array([p[0], p[1], z])

        c = np.mean(pts, axis=0)
        for rect, z, n, mirror in ((front_rect, z0, [0, 0, -1], True), (back_rect or front_rect, z1, [0, 0, 1], False)):
            for a, b in zip(pts, pts[1:] + pts[:1]):
                tri = [P3(c, z), P3(a, z), P3(b, z)]
                uv = [cap_uv(c, rect, mirror), cap_uv(a, rect, mirror), cap_uv(b, rect, mirror)]
                if np.dot(np.cross(tri[1] - tri[0], tri[2] - tri[0]), n) < 0:
                    tri, uv = tri[::-1], uv[::-1]
                self.face(tri, uv, [n] * 3)
        # sides: u along the perimeter
        per = [0.0]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            per.append(per[-1] + np.linalg.norm(b - a))
        x0, y0, x1, y1 = side_rect
        for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
            ua = x0 + (x1 - x0) * per[i] / per[-1]
            ub = x0 + (x1 - x0) * per[i + 1] / per[-1]
            q = [P3(a, z0), P3(b, z0), P3(b, z1), P3(a, z1)]
            uv = [(ua, y0), (ub, y0), (ub, y1), (ua, y1)]
            edge = b - a
            n = np.array([edge[1], -edge[0], 0.0])        # outward for a CCW outline
            if np.dot(np.cross(q[1] - q[0], q[2] - q[0]), n) < 0:
                q, uv = q[::-1], uv[::-1]
            self.face(q, uv, [n] * 4)

    def obox(self, center, size, R=None, rects=None, default_rect=(0, 0, 1, 1)):
        """oriented box: size (w, h, d) around center, rotated by matrix R; rects per face name (texture px)"""
        R = np.eye(3) if R is None else R
        c = np.asarray(center, float)
        w, h, d = (s / 2 for s in size)
        rects = rects or {}
        faces = {
            'north': ([(-w, -h, -d), (w, -h, -d), (w, h, -d), (-w, h, -d)], (0, 0, -1)),
            'south': ([(w, -h, d), (-w, -h, d), (-w, h, d), (w, h, d)], (0, 0, 1)),
            'east': ([(w, -h, -d), (w, -h, d), (w, h, d), (w, h, -d)], (1, 0, 0)),
            'west': ([(-w, -h, d), (-w, -h, -d), (-w, h, -d), (-w, h, d)], (-1, 0, 0)),
            'up': ([(-w, h, -d), (w, h, -d), (w, h, d), (-w, h, d)], (0, 1, 0)),
            'down': ([(-w, -h, d), (w, -h, d), (w, -h, -d), (-w, -h, -d)], (0, -1, 0)),
        }
        for name, (corners, n) in faces.items():
            x0, y0, x1, y1 = rects.get(name, default_rect)
            pts = [c + R @ np.array(p) for p in corners]
            nn = R @ np.array(n, float)
            uv = [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]
            q, u = pts, uv
            if np.dot(np.cross(q[1] - q[0], q[2] - q[0]), nn) < 0:
                q, u = q[::-1], u[::-1]
            self.face(q, u, [nn] * 4)

    def json(self):
        return {"normalized_uvs": True, "positions": self.P, "normals": self.N, "uvs": self.U, "polys": self.polys}


def rot(rx=0, ry=0, rz=0):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


def rounded_polygon(corners, radius, steps=4):
    """CCW polygon with each corner rounded by an arc"""
    pts = [np.array(c, float) for c in corners]
    out = []
    n = len(pts)
    for i in range(n):
        p, a, b = pts[i], pts[i - 1], pts[(i + 1) % n]
        va, vb = _n(a - p), _n(b - p)
        ang = math.acos(max(-1, min(1, float(np.dot(va, vb)))))
        t = radius / math.tan(ang / 2)
        pa, pb = p + va * t, p + vb * t
        bis = _n(va + vb)
        centre = p + bis * (radius / math.sin(ang / 2))
        a0 = math.atan2(pa[1] - centre[1], pa[0] - centre[0])
        a1 = math.atan2(pb[1] - centre[1], pb[0] - centre[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for s in range(steps + 1):
            aa = a0 + da * s / steps
            out.append((centre[0] + radius * math.cos(aa), centre[1] + radius * math.sin(aa)))
    return out
