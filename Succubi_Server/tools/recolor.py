"""Texture variants (Thai tea, matcha, tom yum broth, ...) made by recolouring the Food Items atlases."""
import numpy as np
from PIL import Image


def rgb_to_hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    h = h * 60.0
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def hsv_to_rgb(h, s, v):
    h = (h % 360) / 60.0
    i = np.floor(h).astype(int) % 6; f = h - np.floor(h)
    p = v * (1 - s); q = v * (1 - s * f); t = v * (1 - s * (1 - f))
    out = np.zeros(h.shape + (3,))
    for k, (r, g, b) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        sel = i == k
        out[sel, 0] = r[sel]; out[sel, 1] = g[sel]; out[sel, 2] = b[sel]
    return out


def region_mask(shape, regions, scale):
    if regions is None:
        return np.ones(shape[:2], bool)
    m = np.zeros(shape[:2], bool)
    for x0, y0, x1, y1 in regions:
        m[int(y0 * scale):int(y1 * scale), int(x0 * scale):int(x1 * scale)] = True
    return m


def apply(img, recipe, atlas=True):
    """recipe(h, s, v, sel) -> (h, s, v); regions given in 1024-atlas coordinates, ignored for icons"""
    im = img.convert('RGBA'); a = np.asarray(im).astype(float) / 255.0
    h, s, v = rgb_to_hsv(a[..., :3])
    spec = RECIPES[recipe]
    reg = region_mask(a.shape, spec.get('regions') if atlas else None, a.shape[0] / 1024.0)
    hl, hh = spec['hue']
    hue_ok = (h >= hl) & (h <= hh) if hl <= hh else ((h >= hl) | (h <= hh))
    sel = reg & hue_ok & (s >= spec.get('smin', 0.0)) & (s <= spec.get('smax', 1.0)) & (v >= spec.get('vmin', 0.0)) & (a[..., 3] > 0.05)
    nh, ns, nv = spec['fn'](h.copy(), s.copy(), v.copy())
    h2 = np.where(sel, nh, h); s2 = np.where(sel, np.clip(ns, 0, 1), s); v2 = np.where(sel, np.clip(nv, 0, 1), v)
    rgb = hsv_to_rgb(h2, s2, v2)
    out = np.concatenate([rgb, a[..., 3:]], -1)
    return Image.fromarray((out * 255).round().astype(np.uint8), 'RGBA')


RECIPES = {
    # milk tea tan -> Thai tea orange
    'thai_tea': dict(hue=(18, 48), smin=0.18, vmin=0.3, fn=lambda h, s, v: (h * 0 + 24, np.maximum(s * 1.9, 0.72), v * 0.98)),
    # milk tea tan -> matcha latte green
    'matcha': dict(hue=(18, 48), smin=0.18, vmin=0.3, fn=lambda h, s, v: (h * 0 + 92, np.minimum(s * 1.25, 0.6), v * 0.9)),
    # milk tea tan -> dark cocoa
    'cocoa': dict(hue=(18, 48), smin=0.18, vmin=0.3, fn=lambda h, s, v: (h * 0 + 20, np.minimum(s * 1.4, 0.75), v * 0.55)),
    # golden shoyu broth -> red-orange tom yum
    'tomyum': dict(hue=(15, 55), smin=0.2, regions=[(256, 384, 512, 640), (0, 128, 256, 384), (512, 384, 768, 640)],
                   fn=lambda h, s, v: (h * 0 + 14, np.maximum(s * 1.3, 0.78), v * 0.95)),
    # golden broth -> milky tonkotsu
    'tonkotsu': dict(hue=(15, 55), smin=0.15, regions=[(256, 384, 512, 640)],
                     fn=lambda h, s, v: (h * 0 + 38, s * 0.22, np.minimum(v * 1.12 + 0.08, 0.97))),
    # orange fried chicken -> glossy red gochujang glaze
    'spicy_glaze': dict(hue=(10, 50), smin=0.35, regions=[(512, 512, 1024, 1024)],
                        fn=lambda h, s, v: (h * 0 + 358, np.minimum(s * 1.15, 0.95), v * 0.82)),
    # papaya salad -> darker pla ra dressing
    'pla_ra': dict(hue=(0, 360), smin=0.12, regions=[(0, 0, 512, 512), (512, 768, 1024, 1024)],
                   fn=lambda h, s, v: (h, s * 0.85, v * 0.68)),
    # golden fried insects -> tom yum powder coating
    'tomyum_powder': dict(hue=(12, 55), smin=0.3,
                          fn=lambda h, s, v: (h * 0 + 10, np.minimum(s * 1.2 + 0.05, 0.95), v * 0.9)),
}
