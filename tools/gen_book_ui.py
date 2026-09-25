"""Book reading window (v1.1.13). Safe to run again.

 textures/ui/succubi_paper/book_normal.png  leather-bound page with a ribbon (drawn at 720x480, saved at 360x240 = its size on screen)
 textures/ui/succubi_paper/book_cursed.png  black cover, scorched and stained page (หนังสือเล่มดำ)
 textures/ui/succubi_paper/book_news.png    newsprint with a masthead (หนังสือพิมพ์)
 textures/ui/succubi_paper/btn_prev(_off).png
 ui/succubi_paper.json  book_panel: themed page, the book's own icon, title, text, 3 buttons (« ก่อนหน้า / ถัดไป » or
                        อ่านจบ / ปิด). Invisible colour codes in the title pick them (scripts/succubi/books.js):
                        §8§8§1 cursed, §8§8§2 newspaper (else normal), §6§6§<0-a> = which book icon
 ui/server_form.json    books use their own flag §0§9§5§9 -> book_panel (rule boards keep the paper, §0§9§5§1)
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

RP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon", "Succubi Server RP")
TEX = os.path.join(RP, "textures", "ui", "succubi_paper")
W, H = 720, 480
# icon codes -> item textures (keep in step with ICON in books.js)
ICONS = ["book_newspaper", "book_comic", "book_travel", "book_romance", "book_mystery", "book_dharma",
         "book_prayer", "book_coloring", "book_survival", "book_ghost", "book_custom"]
HEX = "0123456789a"


def grain(img, amount, seed):
    rnd = random.Random(seed)
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            n = rnd.randint(-amount, amount)
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a)


def vignette(img, strength, color=(60, 30, 10)):
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    px = over.load()
    cx, cy = img.width / 2, img.height / 2
    for y in range(img.height):
        for x in range(img.width):
            d = math.hypot((x - cx) / cx, (y - cy) / cy)
            a = max(0.0, d - 0.55) / 0.6
            px[x, y] = color + (int(255 * min(1, a) * strength),)
    img.alpha_composite(over)


def page_mask(box, rough, seed):
    """a page with a slightly uneven edge"""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    pts = []
    for x in range(x0, x1, 12):
        pts.append((x, y0 + rnd.uniform(-rough, rough)))
    for y in range(y0, y1, 12):
        pts.append((x1 + rnd.uniform(-rough, rough), y))
    for x in range(x1, x0, -12):
        pts.append((x, y1 + rnd.uniform(-rough, rough)))
    for y in range(y1, y0, -12):
        pts.append((x0 + rnd.uniform(-rough, rough), y))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def cover(img, fill, edge, stitch):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=26, fill=(20, 10, 6, 255))
    d.rounded_rectangle((6, 6, W - 7, H - 7), radius=22, fill=fill + (255,))
    d.rounded_rectangle((14, 14, W - 15, H - 15), radius=16, outline=edge + (255,), width=2)
    for x in range(28, W - 28, 14):  # stitching
        d.line((x, 10, x + 7, 10), fill=stitch + (255,), width=2)
        d.line((x, H - 11, x + 7, H - 11), fill=stitch + (255,), width=2)
    grain(img, 7, 3)


def ribbon(img, color):
    d = ImageDraw.Draw(img)
    x = W - 56  # at the right edge, clear of the text
    d.polygon([(x, 0), (x + 24, 0), (x + 24, 70), (x + 12, 60), (x, 70)], fill=(25, 8, 8, 255))
    d.polygon([(x + 3, 0), (x + 21, 0), (x + 21, 64), (x + 12, 56), (x + 3, 64)], fill=color + (255,))


def ornament(d, cx, y, color):
    d.line((cx - 95, y, cx - 18, y), fill=color, width=2)
    d.line((cx + 18, y, cx + 95, y), fill=color, width=2)
    d.polygon([(cx, y - 7), (cx + 9, y), (cx, y + 7), (cx - 9, y)], fill=color)


def normal():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cover(img, (98, 44, 26), (150, 96, 52), (196, 150, 96))
    page = Image.new("RGBA", (W, H), (243, 230, 200, 255))
    grain(page, 6, 5)
    vignette(page, 0.45)
    img.paste(page, (0, 0), page_mask((24, 22, W - 24, H - 22), 1.5, 7))
    d = ImageDraw.Draw(img)
    d.line((40, 74, W - 70, 74), fill=(160, 110, 70, 255), width=2)  # under the title
    ornament(d, 140, H - 50, (170, 120, 76, 255))
    ribbon(img, (150, 30, 40))
    return img


def cursed():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cover(img, (26, 14, 18), (90, 20, 26), (110, 30, 34))
    page = Image.new("RGBA", (W, H), (222, 204, 164, 255))
    grain(page, 12, 9)
    vignette(page, 0.7, (40, 10, 5))
    rnd = random.Random(13)
    stains = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stains)
    for _ in range(9):  # old blood stains
        x, y, r = rnd.randint(60, W - 60), rnd.randint(60, H - 60), rnd.randint(6, 26)
        sd.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=(110, 10, 12, rnd.randint(25, 60)))
    for _ in range(5):  # scratches
        x, y = rnd.randint(40, W - 160), rnd.randint(90, H - 60)
        sd.line((x, y, x + rnd.randint(40, 120), y + rnd.randint(-20, 20)), fill=(70, 30, 20, 70), width=2)
    hx, hy = W - 150, H - 150  # a faint hand print, lower right
    sd.ellipse((hx, hy, hx + 54, hy + 62), fill=(120, 12, 14, 45))
    for i, (dx, dy, l) in enumerate(((-6, -30, 34), (10, -44, 40), (26, -46, 42), (42, -38, 36), (58, -6, 30))):
        sd.line((hx + 12 + i * 8, hy + 8, hx + 12 + i * 8 + dx * 0.3, hy + dy), fill=(120, 12, 14, 45), width=12)
    stains = stains.filter(ImageFilter.GaussianBlur(1.2))
    page.alpha_composite(stains)
    img.paste(page, (0, 0), page_mask((24, 22, W - 24, H - 22), 6, 11))
    d = ImageDraw.Draw(img)
    d.line((40, 74, W - 70, 74), fill=(110, 30, 30, 255), width=2)
    ornament(d, 140, H - 50, (120, 30, 30, 255))
    ribbon(img, (30, 30, 30))
    return img


def news():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((4, 6, W - 5, H - 5), fill=(60, 60, 60, 120))  # soft shadow
    page = Image.new("RGBA", (W, H), (236, 233, 222, 255))
    grain(page, 9, 17)
    vignette(page, 0.3, (80, 70, 50))
    img.paste(page, (0, 0), page_mask((2, 2, W - 8, H - 8), 1, 19))
    d = ImageDraw.Draw(img)
    d.line((30, 30, W - 36, 30), fill=(30, 30, 30, 255), width=4)  # masthead rules
    d.line((30, 78, W - 36, 78), fill=(30, 30, 30, 255), width=4)
    d.line((30, 84, W - 36, 84), fill=(30, 30, 30, 255), width=1)
    d.line((30, H - 80, W - 36, H - 80), fill=(80, 80, 80, 255), width=1)
    return img


def prev_buttons():
    nxt = Image.open(os.path.join(TEX, "btn_next.png")).convert("RGBA")
    icon = nxt.crop((4, 4, 36, 52)).transpose(Image.FLIP_LEFT_RIGHT)  # the arrow tile, pointing back
    prev = nxt.copy()
    prev.paste(icon, (4, 4))
    off = ImageEnhance.Brightness(ImageEnhance.Color(prev).enhance(0.1)).enhance(0.8)
    off.putalpha(prev.getchannel("A").point(lambda a: int(a * 0.55)))
    return prev, off


def has(flag):
    return {"binding_type": "view", "source_property_name": f"(not ((#title_text - '{flag}') = #title_text))",
            "target_property_name": "#visible"}


def bg(name, binding):
    return {name: {"type": "image", "texture": f"textures/ui/succubi_paper/{name}", "size": ["100%", "100%"],
                   "layer": 1, "bindings": [{"binding_name": "#title_text"}, binding]}}


def panel():
    normal_vis = {"binding_type": "view",
                  "source_property_name": "(((#title_text - '§8§8§1') = #title_text) and ((#title_text - '§8§8§2') = #title_text))",
                  "target_property_name": "#visible"}
    controls = [bg("book_normal", normal_vis), bg("book_cursed", has("§8§8§1")), bg("book_news", has("§8§8§2"))]
    for i, key in enumerate(ICONS):
        controls.append({f"icon_{i}": {
            "type": "image", "texture": f"textures/items/extra/{key}", "size": [18, 18], "offset": [24, 12],
            "anchor_from": "top_left", "anchor_to": "top_left", "layer": 4,
            "bindings": [{"binding_name": "#title_text"}, has(f"§6§6§{HEX[i]}")]}})
    controls += [
        {"title": {"type": "label", "text": "#title_text", "color": [0.42, 0.12, 0.08], "localize": False,
                   "shadow": False, "anchor_from": "top_left", "anchor_to": "top_left", "offset": [46, 17],
                   "size": [260, 12], "layer": 5, "font_type": "smooth", "font_scale_factor": 1.1,
                   "bindings": [{"binding_name": "#title_text"}]}},
        {"body": {"type": "label", "text": "#form_text", "color": [0.18, 0.1, 0.05], "localize": False,
                  "shadow": False, "anchor_from": "top_left", "anchor_to": "top_left", "offset": [24, 44],
                  "size": [300, "default"], "layer": 5, "font_type": "smooth",
                  "bindings": [{"binding_name": "#form_text"}]}},
        {"slots": {"type": "grid", "anchor_from": "bottom_right", "anchor_to": "bottom_right", "offset": [-14, -10],
                   "size": [213, 30], "grid_dimensions": [3, 1], "grid_item_template": "succubi_paper.cell",
                   "collection_name": "form_buttons", "layer": 5}},
    ]
    return {"type": "panel", "size": [360, 240], "layer": 2, "controls": controls}


def paletted(img, colors=63):
    """dithered palette (no banding on the vignette); the last index = see-through for the rounded corners"""
    rgb = Image.new("RGB", img.size, (0, 0, 0))
    rgb.paste(img, mask=img.getchannel("A"))
    p = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
    pal = p.getpalette()[: colors * 3] + [0, 0, 0]
    p.putpalette(pal)
    clear = img.getchannel("A").point(lambda a: 255 if a < 128 else 0)
    p.paste(colors, mask=clear)
    p.info["transparency"] = colors
    return p


def main():
    # drawn at 2x, saved at 1x (360x240) with a dithered 96-colour palette: the paper grain would not compress
    # otherwise, and the single .mcaddon has to stay under 30 MB
    for name, make in (("book_normal", normal), ("book_cursed", cursed), ("book_news", news)):
        paletted(make().resize((W // 2, H // 2), Image.LANCZOS)).save(os.path.join(TEX, name + ".png"),
                                                                      optimize=True)
    prev, off = prev_buttons()
    prev.save(os.path.join(TEX, "btn_prev.png"))
    off.save(os.path.join(TEX, "btn_prev_off.png"))

    path = os.path.join(RP, "ui", "succubi_paper.json")
    with open(path, encoding="utf-8") as f:
        ui = json.load(f)
    ui["book_panel"] = panel()
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(ui, indent=2, ensure_ascii=False) + "\n")

    # books get their own flag (§0§9§5§9); rule boards keep the plain paper (§0§9§5§1)
    path = os.path.join(RP, "ui", "server_form.json")
    with open(path, encoding="utf-8") as f:
        form = json.load(f)
    controls = form["long_form"]["controls"]
    for c in controls:
        if "succubi_paper@succubi_paper.book_panel" in c:  # an earlier run had replaced the paper
            c["succubi_paper@succubi_paper.paper_panel"] = c.pop("succubi_paper@succubi_paper.book_panel")
    controls[:] = [c for c in controls if "succubi_book@succubi_paper.book_panel" not in c]
    at = next(i for i, c in enumerate(controls) if "succubi_paper@succubi_paper.paper_panel" in c)
    controls.insert(at + 1, {"succubi_book@succubi_paper.book_panel": {"bindings": [
        {"binding_name": "#title_text"},
        {"binding_type": "view", "source_property_name": "(not ((#title_text - '§0§9§5§9') = #title_text))",
         "target_property_name": "#visible"}]}})
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(form, indent=2, ensure_ascii=False) + "\n")
    print("book window written")


if __name__ == "__main__":
    main()
