"""Vending machines in the same layout as the other shops (v1.1.9). Safe to run again.

 - textures/ui/succubi_shops/bg_vend_drink.png / bg_vend_snack.png (720x400): the store window layout
   (action row, scrolling product list, LCD on the right) painted as the red drink machine / blue snack machine
 - ui/succubi_shops.json: vend_drink_panel / vend_snack_panel, copies of the store panel with those skins
 - ui/server_form.json: the machines' title flags (§0§9§8§4 drink, §0§9§8§3 snack) now open those panels
The script side (scripts/succubi/vending.js) gives the machines names, the shop product buttons and all notes.
"""
import copy
import json
import os

from PIL import Image, ImageDraw

RP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon", "Succubi Server RP")
UI = os.path.join(RP, "ui")
TEX = os.path.join(RP, "textures", "ui", "succubi_shops")
INK = (22, 8, 12, 255)

SKINS = {
    "drink": {"rim": (222, 52, 52), "body": (110, 17, 21), "shade": (84, 12, 16), "side": (128, 20, 24),
              "bar": (63, 7, 11), "title": "§lตู้กดน้ำ"},
    "snack": {"rim": (44, 128, 218), "body": (20, 60, 116), "shade": (14, 44, 88), "side": (24, 72, 136),
              "bar": (10, 28, 62), "title": "§lตู้ขนม"},
}


def rgba(c, a=255):
    return tuple(c) + (a,)


def background(skin):
    k = 2  # drawn at 2x, then halved: smooth corners
    W, H = 720 * k, 400 * k
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = lambda *box: tuple(v * k for v in box)
    d.rounded_rectangle(s(2, 2, 718, 398), radius=18 * k, fill=INK)
    d.rounded_rectangle(s(5, 5, 715, 395), radius=16 * k, fill=rgba(skin["rim"]))
    d.rounded_rectangle(s(10, 8, 710, 392), radius=13 * k, fill=rgba(skin["body"]))
    # title bar with the three lamps of the machine
    d.rounded_rectangle(s(16, 10, 562, 44), radius=8 * k, fill=rgba(skin["bar"]))
    for i, lamp in enumerate(((255, 120, 170), (120, 220, 255), (255, 214, 90))):
        cx = 510 + i * 16
        d.ellipse(s(cx - 6, 21, cx + 6, 33), fill=rgba(lamp))
    # action row (change / insert all / close)
    d.rounded_rectangle(s(16, 50, 562, 114), radius=8 * k, fill=INK)
    d.rounded_rectangle(s(18, 52, 560, 112), radius=7 * k, fill=rgba(skin["shade"]))
    # product window: dark glass, light frame and a reflection stripe
    d.rounded_rectangle(s(16, 120, 562, 390), radius=8 * k, fill=(160, 170, 184, 255))
    d.rounded_rectangle(s(19, 123, 559, 387), radius=7 * k, fill=(16, 22, 32, 255))
    glass = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glass)
    g.polygon(s(40, 125, 110, 125, 60, 385, 22, 385), fill=(255, 255, 255, 22))
    img.alpha_composite(glass)
    # side panel: LCD, coin slot, note slot, pick-up tray
    d.rounded_rectangle(s(570, 50, 706, 390), radius=10 * k, fill=INK)
    d.rounded_rectangle(s(573, 53, 703, 387), radius=9 * k, fill=rgba(skin["side"]))
    d.rounded_rectangle(s(582, 58, 694, 204), radius=6 * k, fill=(4, 12, 6, 255))
    d.rounded_rectangle(s(585, 61, 691, 201), radius=5 * k, fill=(10, 30, 16, 255))
    for y, w in ((222, 36), (248, 46)):
        d.rounded_rectangle(s(638 - w, y - 8, 638 + w, y + 8), radius=4 * k, fill=(30, 30, 34, 255))
        d.line(s(638 - w + 8, y, 638 + w - 8, y), fill=(0, 0, 0, 255), width=3 * k)
    d.rounded_rectangle(s(590, 300, 686, 374), radius=8 * k, fill=(150, 156, 166, 255))
    d.rounded_rectangle(s(594, 304, 682, 370), radius=6 * k, fill=(40, 42, 48, 255))
    return img.resize((720, 400), Image.LANCZOS)


def main():
    for kind, skin in SKINS.items():
        background(skin).save(os.path.join(TEX, f"bg_vend_{kind}.png"))

    path = os.path.join(UI, "succubi_shops.json")
    with open(path, encoding="utf-8") as f:
        shops = json.load(f)
    for kind, skin in SKINS.items():
        panel = copy.deepcopy(shops["seven_drink_panel"])
        for c in panel["controls"]:
            key = next(iter(c))
            if key == "bg":
                c[key]["texture"] = f"textures/ui/succubi_shops/bg_vend_{kind}"
            elif key == "title":
                c[key]["text"] = skin["title"]
            elif key == "lcd":
                c[key]["color"] = [0.6, 1, 0.65]  # the machine's green LCD
                c[key]["shadow"] = False
        shops[f"vend_{kind}_panel"] = panel
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(shops, indent=2, ensure_ascii=False) + "\n")

    path = os.path.join(UI, "server_form.json")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    raw = raw.replace('"succubi_drink@succubi_vending.drink_panel"', '"succubi_drink@succubi_shops.vend_drink_panel"')
    raw = raw.replace('"succubi_snack@succubi_vending.snack_panel"', '"succubi_snack@succubi_shops.vend_snack_panel"')
    json.loads(raw)
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)
    print("vending skins written")


if __name__ == "__main__":
    main()
