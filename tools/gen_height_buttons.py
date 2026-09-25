"""Wide buttons for the height window (RP textures/ui/succubi_height/wbtn_*.png, 148x44 = 74x22 on screen).

The plates are the pack's own 72x44 buttons stretched in the middle; the icons are the repo's 128 px bat icons
(green plus, red back, black-red minus, gear) scaled down, with a check mark / arrows painted in their style.
"""
import os
from PIL import Image, ImageDraw, ImageEnhance

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TEX = os.path.join(REPO, "addon", "Succubi Server RP", "textures", "ui", "succubi_height")
W, H = 148, 44
EDGE = 10  # plate corner width kept as is when stretching
ICON = 32


def stretch(name):
    src = Image.open(os.path.join(TEX, name + ".png")).convert("RGBA")
    sw, sh = src.size
    out = Image.new("RGBA", (W, H))
    right = src.crop((sw - EDGE, 0, sw, sh))
    out.paste(right.transpose(Image.FLIP_LEFT_RIGHT), (0, 0))  # plates are symmetric; the left side may hold an icon
    out.paste(right, (W - EDGE, 0))
    mid = src.crop((sw - EDGE - 2, 0, sw - EDGE - 1, sh)).resize((W - 2 * EDGE, sh), Image.NEAREST)  # a clean column
    out.paste(mid, (EDGE, 0))
    return out


def icon(name):
    im = Image.open(os.path.join(REPO, name + ".png")).convert("RGBA")
    corner = im.getpixel((0, 0))
    if corner[3] == 255:  # the gear sits on a flat grey square: clear it from the corners inwards
        for xy in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
            ImageDraw.floodfill(im, xy, (0, 0, 0, 0), thresh=0)
    im = im.resize((ICON, ICON), Image.BOX)
    px = im.load()
    for y in range(ICON):
        for x in range(ICON):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= 110 else 0)
    return im


def face(base, paint):
    """Paint over the middle of a repo button face (covers the old symbol) and draw a new one."""
    im = icon(base)
    d = ImageDraw.Draw(im)
    fill = im.getpixel((9, 22))  # the face colour below the old symbol
    d.rectangle((10, 14, 22, 25), fill=fill)
    paint(d)
    return im


WHITE = (255, 255, 255, 255)
DARK = (30, 12, 20, 255)
RED = (235, 60, 70, 255)


def check(d):
    d.line((10, 20, 14, 24), fill=WHITE, width=3)
    d.line((14, 24, 22, 15), fill=WHITE, width=3)


def tilt(d):
    # up arrow (white) and down arrow (red) side by side
    d.polygon([(11, 18), (14, 14), (17, 18)], fill=WHITE)
    d.rectangle((13, 18, 15, 25), fill=WHITE)
    d.polygon([(17, 21), (20, 25), (23, 21)], fill=RED)
    d.rectangle((19, 14, 21, 21), fill=RED)


def reset(d):
    d.arc((10, 14, 22, 26), start=40, end=330, fill=WHITE, width=2)
    d.polygon([(19, 12), (24, 16), (18, 18)], fill=WHITE)


BUTTONS = {
    # name: (plate, icon image or None)
    "wbtn_adjust": ("btn_confirm", lambda: icon("pixel_art_native")),
    "wbtn_tilt": ("btn_reset", lambda: face("black_red_minus_button_bat_128x128", tilt)),
    "wbtn_reset": ("btn_type", lambda: face("black_red_minus_button_bat_128x128", reset)),
    "wbtn_cancel": ("btn_close", lambda: icon("red_back_button_white_arrow")),
    "wbtn_confirm": ("btn_plus", lambda: face("green_plus_button_white_plus", check)),
}


def main():
    for out_name, (plate, make_icon) in BUTTONS.items():
        base = stretch(plate)
        # keep the plate colour of the "on" variant for the icon buttons
        img = base.copy()
        ic = make_icon()
        img.alpha_composite(ic, (5, (H - ICON) // 2 - 1))
        img.save(os.path.join(TEX, out_name + ".png"))
        # greyed variant: the height is locked
        off = ImageEnhance.Brightness(ImageEnhance.Color(img).enhance(0.15)).enhance(0.55)
        off.save(os.path.join(TEX, out_name + "_off.png"))
    for overlay in ("btn_hover", "btn_pressed"):
        stretch(overlay).save(os.path.join(TEX, "w" + overlay + ".png"))
    print("buttons written to", os.path.relpath(TEX, REPO))


if __name__ == "__main__":
    main()
