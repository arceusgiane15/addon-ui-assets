"""A small JSON UI renderer for the Succubi form screens, so layouts can be checked without the game.

It understands what our ui/*.json use: panels, images, labels, grids, stack panels with factories, common.button
(drawn in its default state), @inheritance across namespaces, anchors, % sizes, and view-binding expressions
(- = + and or not on #title_text / #form_text / #form_button_text / #form_button_texture).
Text uses Noto Sans Thai standing in for the game's smooth font; § colour codes are honoured."""
import glob, os, re
from PIL import Image, ImageDraw, ImageFont
from common import rjson, FONT_THAI

G = 3   # screen pixels per GUI unit
MC = dict(zip('0123456789abcdef', [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (255, 170, 0), (170, 170, 170),
                                    (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]))


def _font(px, bold):
    f = ImageFont.truetype(FONT_THAI, px)
    try:
        f.set_variation_by_name('Bold' if bold else 'Regular')
    except Exception:
        pass
    return f


FONTS = {}


def font(scale=1.0, bold=False):
    k = (round(scale * 100), bold)
    if k not in FONTS:
        FONTS[k] = _font(int(8.2 * G * scale), bold)
    return FONTS[k]


# ------------------------------------------------------------------------------------------ expressions
TOK = re.compile(r"\s*(?:(\()|(\))|('(?:[^'])*')|(#[\w.]+|\$[\w.|]+)|(-?\d+(?:\.\d+)?)|(and|or|not)\b|(=|-|\+|\*|/|<|>))")


def evaluate(expr, env):
    toks, pos = [], 0
    expr = expr.strip()
    while pos < len(expr):
        m = TOK.match(expr, pos)
        if not m or m.end() == pos:
            raise ValueError(f'cannot parse {expr!r} at {pos}')
        pos = m.end()
        toks.append(next((i, g) for i, g in enumerate(m.groups()) if g is not None))
    i = [0]

    def peek():
        return toks[i[0]] if i[0] < len(toks) else (None, None)

    def take():
        t = toks[i[0]]
        i[0] += 1
        return t

    def primary():
        k, v = take()
        if k == 0:
            r = orx()
            take()
            return r
        if k == 2:
            return v[1:-1]
        if k == 3:
            val = env.get(v, '')
            return val
        if k == 4:
            return float(v)
        if k == 5 and v == 'not':
            return not cmp_()
        raise ValueError(f'unexpected {v} in {expr}')

    def addsub():
        a = primary()
        while peek()[1] in ('-', '+'):
            op = take()[1]
            b = primary()
            if op == '-':
                a = a.replace(b, '') if isinstance(a, str) else a - b
            else:
                a = (str(a) + str(b)) if isinstance(a, str) or isinstance(b, str) else a + b
        return a

    def cmp_():
        a = addsub()
        while peek()[1] in ('=', '<', '>'):
            op = take()[1]
            b = addsub()
            a = (a == b) if op == '=' else (a < b) if op == '<' else (a > b)
        return a

    def notx():
        if peek() == (5, 'not'):
            take()
            return not notx()
        return cmp_()

    def andx():
        a = notx()
        while peek() == (5, 'and'):
            take()
            b = notx()
            a = bool(a) and bool(b)
        return a

    def orx():
        a = andx()
        while peek() == (5, 'or'):
            take()
            b = andx()
            a = bool(a) or bool(b)
        return a

    return orx()


# ------------------------------------------------------------------------------------------ element library
class Lib:
    def __init__(self, rp):
        self.rp = rp
        self.ns = {}
        for p in glob.glob(os.path.join(rp, 'ui', '*.json')):
            d = rjson(p)
            if isinstance(d, dict) and 'namespace' in d:
                self.ns.setdefault(d['namespace'], {}).update({k.split('@')[0]: (k, v) for k, v in d.items() if k != 'namespace'})

    def resolve(self, ref, ns):
        """element body for 'namespace.name' (following its own @ base)"""
        if '.' in ref:
            ns, name = ref.split('.', 1)
        else:
            name = ref
        if ns not in self.ns or name not in self.ns[ns]:
            return {'type': 'panel', '__missing__': f'{ns}.{name}'}
        key, body = self.ns[ns][name]
        return self.merge(key, body, ns)

    def merge(self, key, body, ns):
        if '@' in key:
            base = self.resolve(key.split('@', 1)[1], ns)
            out = dict(base)
            out.update(body)
            return out
        return dict(body)


# ------------------------------------------------------------------------------------------ layout + draw
def parse_len(v, parent, default):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = re.match(r'^\s*(\d+(?:\.\d+)?)%\s*(?:([+-])\s*(\d+(?:\.\d+)?)px)?\s*$', v)
        if m:
            base = parent * float(m.group(1)) / 100
            if m.group(2):
                base += float(m.group(3)) * (1 if m.group(2) == '+' else -1)
            return base
        m = re.match(r'^\s*(\d+(?:\.\d+)?)%c', v)
        if m:
            return None
    return default


ANCH = {'top_left': (0, 0), 'top_middle': (0.5, 0), 'top_right': (1, 0), 'left_middle': (0, 0.5), 'center': (0.5, 0.5),
        'right_middle': (1, 0.5), 'bottom_left': (0, 1), 'bottom_middle': (0.5, 1), 'bottom_right': (1, 1)}


class Renderer:
    def __init__(self, rp, form):
        self.lib = Lib(rp)
        self.rp = rp
        self.form = form              # {'title':, 'body':, 'buttons': [(text, texture)]}
        self.missing = set()

    def env(self, item=None):
        e = {'#title_text': self.form['title'], '#form_text': self.form['body'], '#form_button_length': float(len(self.form['buttons']))}
        if item is not None:
            t, tex = self.form['buttons'][item]
            e.update({'#form_button_text': t, '#form_button_texture': tex or '', '#texture': tex or ''})
        return e

    def visible(self, c, item):
        if c.get('ignored') is True or c.get('visible') is False:
            return False
        for b in c.get('bindings', []) if isinstance(c.get('bindings'), list) else []:
            if b.get('target_property_name') == '#visible' and b.get('source_property_name', '').startswith('('):
                if b.get('source_control_name'):
                    continue
                try:
                    if not evaluate(b['source_property_name'], self.env(item)):
                        return False
                except Exception as ex:
                    self.missing.add(f'expr {b["source_property_name"][:60]}: {ex}')
        return True

    def texture(self, c, item):
        tex = c.get('texture')
        for b in c.get('bindings', []) if isinstance(c.get('bindings'), list) else []:
            if b.get('binding_name_override') == '#texture' and item is not None:
                tex = self.form['buttons'][item][1]
        if not tex or tex.startswith('#') or tex.startswith('$'):
            return None
        for ext in ('.png', '.tga', '.jpg'):
            p = os.path.join(self.rp, tex + ext)
            if os.path.exists(p):
                return Image.open(p).convert('RGBA')
        self.missing.add(f'texture {tex}')
        return None

    def text_of(self, c, item):
        t = c.get('text', '')
        if t in ('#title_text', '#form_text', '#form_button_text'):
            return self.env(item).get(t, '')
        return t if not str(t).startswith('#') else ''

    def draw_text(self, im, x, y, w, s, c):
        base = tuple(int(v * 255) for v in c.get('color', [1, 1, 1])[:3])
        scale = float(c.get('font_scale_factor', 1.0))
        d = ImageDraw.Draw(im)
        col, bold = base, False
        cy = y
        lh = 10 * G * scale
        for line in s.split('\n'):
            cx = x
            for tok in re.split(r'(§.)', line):
                if tok.startswith('§'):
                    k = tok[1]
                    if k in MC:
                        col, bold = MC[k], False
                    elif k == 'l':
                        bold = True
                    elif k == 'r':
                        col, bold = base, False
                    continue
                if not tok:
                    continue
                f = font(scale, bold)
                if c.get('shadow'):
                    d.text((cx + G * 0.7, cy + G * 0.7), tok, font=f, fill=tuple(int(v * 0.25) for v in col))
                d.text((cx, cy), tok, font=f, fill=col)
                cx += d.textlength(tok, font=f)
            cy += lh
        return cy - y

    def text_size(self, c, item):
        s = self.text_of(c, item)
        scale = float(c.get('font_scale_factor', 1.0))
        d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        w = max((d.textlength(re.sub(r'§.', '', ln), font=font(scale, True)) for ln in s.split('\n')), default=0) / G
        return w, 10 * scale * len(s.split('\n'))

    def node(self, key, body, ns):
        full = self.lib.merge(key, body, ns)
        if '__missing__' in full:
            self.missing.add(full['__missing__'])
        return full

    def layout(self, c, pw, ph, item):
        w = parse_len((c.get('size') or ['100%', '100%'])[0], pw, pw)
        h = parse_len((c.get('size') or ['100%', '100%'])[1], ph, ph)
        if c.get('type') == 'label':
            tw, th = self.text_size(c, item)
            if (c.get('size') or [None, None])[0] in (None, 'default'):
                w = tw
            if (c.get('size') or [None, None])[1] in (None, 'default') or not isinstance(h, (int, float)):
                h = th
        return w or 0, h or 0

    def draw(self, im, key, body, ns, px_, py_, pw, ph, item=None, depth=0):
        c = self.node(key, body, ns)
        if not self.visible(c, item) or depth > 40:
            return
        name = key.split('@')[0]
        w, h = self.layout(c, pw, ph, item)
        af = ANCH[c.get('anchor_from', 'center')]
        at = ANCH[c.get('anchor_to', 'center')]
        off = c.get('offset', [0, 0])
        ox = parse_len(off[0], pw, 0) if isinstance(off, list) else 0
        oy = parse_len(off[1], ph, 0) if isinstance(off, list) else 0
        x = px_ + af[0] * pw - at[0] * w + ox
        y = py_ + af[1] * ph - at[1] * h + oy
        t = c.get('type', 'panel')
        base_ref = key.split('@', 1)[1] if '@' in key else ''
        if t == 'image':
            tex = self.texture(c, item)
            if tex and w > 0 and h > 0:
                tex = tex.resize((max(1, round(w * G)), max(1, round(h * G))), Image.LANCZOS)
                if isinstance(c.get('alpha'), (int, float)):
                    tex.putalpha(tex.getchannel('A').point(lambda v: int(v * c['alpha'])))
                im.alpha_composite(tex, (round(x * G), round(y * G)))
        elif t == 'label':
            self.draw_text(im, x * G, y * G, w, self.text_of(c, item), c)
        kids = c.get('controls', []) if isinstance(c.get('controls'), list) else []
        cns = ns if '.' not in base_ref else base_ref.split('.')[0]
        # form scaffolding from vanilla we emulate
        if base_ref in ('server_form.long_form_panel',):
            self.long_form(im, x, y, w, h)
            return
        if base_ref == 'server_form.custom_form_panel':
            self.draw_text(im, (x + 3) * G, (y + 2) * G, w, self.form['body'] or '§7(ช่องกรอกข้อมูลของเกม)', {'color': [0.9, 0.9, 0.9]})
            return
        if t == 'grid':
            cols, rows = c.get('grid_dimensions', [1, 1])
            tmpl = c.get('grid_item_template')
            n = len(self.form['buttons'])
            cw, ch = w / cols, h / rows
            for idx in range(min(n, cols * rows)):
                gx, gy = idx % cols, idx // cols
                self.draw_template(im, tmpl, x + gx * cw, y + gy * ch, idx, depth)
        if t == 'stack_panel' and c.get('factory'):
            tmpl = c['factory']['control_name']
            tpl = self.lib.resolve(tmpl, ns)
            tw_, th_ = self.layout(tpl, pw, ph, 0)
            n = len(self.form['buttons'])
            horiz = c.get('orientation') == 'horizontal'
            total = tw_ * n if horiz else th_ * n
            sx = px_ + af[0] * pw - at[0] * (total if horiz else w) + ox
            sy = py_ + af[1] * ph - at[1] * (th_ if horiz else total) + oy
            for idx in range(n):
                self.draw_template(im, tmpl, sx + (idx * tw_ if horiz else 0), sy + (0 if horiz else idx * th_), idx, depth)
            return
        if t == 'stack_panel':
            horiz = c.get('orientation') == 'horizontal'
            cx, cy = x, y
            for k in kids:
                (kk, kb), = k.items()
                cc = self.node(kk, kb, cns)
                cw_, ch_ = self.layout(cc, w, h, item)
                self.draw(im, kk, kb, cns, cx, cy, cw_ if horiz else w, ch_ if not horiz else h, item, depth + 1)
                if horiz:
                    cx += cw_
                else:
                    cy += ch_
            return
        for k in kids:
            (kk, kb), = k.items()
            if base_ref == 'common.button' and kk.split('@')[0] in ('hover', 'pressed', 'locked'):
                continue
            self.draw(im, kk, kb, cns, x, y, w, h, item, depth + 1)

    def draw_template(self, im, tmpl, x, y, idx, depth):
        tpl = self.lib.resolve(tmpl, tmpl.split('.')[0])
        w, h = self.layout(tpl, 0, 0, idx)
        self.draw(im, 'cell@' + tmpl, {'anchor_from': 'top_left', 'anchor_to': 'top_left', 'offset': [0, 0]}, tmpl.split('.')[0], x, y, w, h, idx, depth + 1)

    def long_form(self, im, x, y, w, h):
        """vanilla scrolling list: body text, then one dynamic button (server_form.dynamic_button) per form button"""
        sf = self.lib.resolve('server_form.long_form_scrolling_content', 'server_form')
        cy = y
        label = {'color': [0.96, 0.94, 0.98], 'shadow': True}
        body = self.form['body']
        if body:
            cy += self.draw_text(im, (x + 3) * G, (cy + 2) * G, w, body, label) / G + 6
        for idx in range(len(self.form['buttons'])):
            self.draw(im, 'b@server_form.dynamic_button', {'anchor_from': 'top_left', 'anchor_to': 'top_left'}, 'server_form', x, cy, w, 33, idx)
            cy += 33
            if cy > y + h:
                break


def render(rp, root_ref, form, size=(420, 280), bg=(40, 60, 50)):
    r = Renderer(rp, form)
    im = Image.new('RGBA', (size[0] * G, size[1] * G), bg + (255,))
    # checker-ish world backdrop
    d = ImageDraw.Draw(im)
    for yy in range(0, size[1] * G, 12 * G):
        for xx in range(0, size[0] * G, 12 * G):
            if (xx // (12 * G) + yy // (12 * G)) % 2:
                d.rectangle([xx, yy, xx + 12 * G - 1, yy + 12 * G - 1], fill=tuple(int(v * 1.12) for v in bg) + (255,))
    ns = root_ref.split('.')[0]
    r.draw(im, 'root@' + root_ref, {'anchor_from': 'center', 'anchor_to': 'center'}, ns, 0, 0, size[0], size[1])
    return im, sorted(r.missing)
