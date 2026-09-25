"""HUD changes for v1.1.9 (RP ui/succubi_hud.json). Safe to run again.

 - the floating specks (sanity below ~97 %) are gone
 - TV static by sanity tier, token Rg1..Rg4 from scripts/succubi/hud.js:
     Rg1 50-70 %  now and then a faint flicker of static bands
     Rg2 30-50 %  more often, faint scanlines, torn lines
     Rg3 15-30 %  often and stronger, a dark band rolls up the screen, the odd veil of static
     Rg4  < 15 %  a constant veil of static (breathing, not flashing) plus the bursts above
   Every flicker is a chain of alpha animations of different lengths, so the layers never line up and it reads as
   random. Bursts stay under 3 per second (photosensitivity guideline); the player's "screen effects off" (Nx) hides
   all of it.
 - Don't Starve day clock, top right: Rk00..Rk47 hand, Rn1..Rn4 + R5/R6/R7/R8 digits = day number
 - rising / falling arrows over the gauges: J<gauge><1-6> (1-3 = up with that many arrows, 4-6 = down)
"""
import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon", "Succubi Server RP", "ui",
                    "succubi_hud.json")
NS = "succubi_hud"
TEX = "textures/ui/succubi_hud/"


def has(token):
    return {
        "binding_type": "view",
        "source_control_name": "succubi_hud_data",
        "source_property_name": f"((not ((#preserved_text - '{token}') = #preserved_text)))",
        "target_property_name": "#visible",
    }


def full(texture, layer, **extra):
    img = {"type": "image", "texture": TEX + texture, "size": ["100%", "100%"], "offset": [0, 0],
           "anchor_from": "center", "anchor_to": "center", "layer": layer}
    img.update(extra)
    return img


# ---------------------------------------------------------------- animations
def blips(ui, name, pattern):
    """pattern: (seconds dark, peak alpha, seconds held) ... ; returns the first anim reference"""
    steps = []
    for wait, peak, hold in pattern:
        steps += [(wait, 0.0, 0.0), (0.04, 0.0, peak), (hold, peak, peak), (0.07, peak, 0.0)]
    for i, (duration, a, b) in enumerate(steps):
        ui[f"{name}_{i}"] = {
            "anim_type": "alpha", "easing": "linear", "duration": duration, "from": a, "to": b,
            "next": f"@{NS}.{name}_{(i + 1) % len(steps)}",
        }
    return f"@{NS}.{name}_0"


def breathe(ui, name, low, high, seconds):
    ui[f"{name}_0"] = {"anim_type": "alpha", "easing": "in_out_sine", "duration": seconds, "from": low, "to": high,
                       "next": f"@{NS}.{name}_1"}
    ui[f"{name}_1"] = {"anim_type": "alpha", "easing": "in_out_sine", "duration": seconds, "from": high, "to": low,
                       "next": f"@{NS}.{name}_0"}
    return f"@{NS}.{name}_0"


def flipbook(ui, name, frames, step, fps):
    ui[name] = {"anim_type": "flip_book", "initial_uv": [0, 0], "frame_count": frames, "frame_step": step,
                "fps": fps, "easing": "linear"}
    return f"@{NS}.{name}"


def loop_offset(ui, name, start, end, seconds, easing="linear"):
    ui[name] = {"anim_type": "offset", "easing": easing, "duration": seconds, "from": start, "to": end,
                "next": f"@{NS}.{name}"}
    return f"@{NS}.{name}"


def bob(ui, name, dy, seconds):
    ui[f"{name}_0"] = {"anim_type": "offset", "easing": "in_out_sine", "duration": seconds, "from": [0, 0],
                       "to": [0, dy], "next": f"@{NS}.{name}_1"}
    ui[f"{name}_1"] = {"anim_type": "offset", "easing": "in_out_sine", "duration": seconds, "from": [0, dy],
                       "to": [0, 0], "next": f"@{NS}.{name}_0"}
    return f"@{NS}.{name}_0"


# ---------------------------------------------------------------- TV static
TIERS = {
    1: {"bands": [(8.3, 0.30, 0.10), (5.9, 0.22, 0.07), (10.7, 0.34, 0.12)]},
    2: {"bands": [(3.1, 0.42, 0.10), (4.7, 0.35, 0.08), (2.3, 0.48, 0.14), (5.3, 0.38, 0.09)],
        "tear": [(4.1, 0.55, 0.12), (6.2, 0.45, 0.08), (3.3, 0.60, 0.10)],
        "scan": 0.12},
    3: {"bands": [(1.7, 0.55, 0.12), (2.6, 0.48, 0.10), (1.1, 0.60, 0.16), (2.2, 0.50, 0.08)],
        "tear": [(2.3, 0.70, 0.12), (1.6, 0.60, 0.10), (3.1, 0.75, 0.14)],
        "veil": [(3.7, 0.16, 0.18), (5.1, 0.20, 0.12)],
        "scan": 0.20, "roll": 5.0},
    4: {"bands": [(0.8, 0.65, 0.14), (1.2, 0.60, 0.10), (0.6, 0.70, 0.16), (1.0, 0.62, 0.12)],
        "tear": [(1.1, 0.80, 0.12), (0.9, 0.70, 0.10), (1.5, 0.85, 0.16)],
        "static": (0.12, 0.24, 1.4),
        "scan": 0.28, "roll": 3.0},
}


def glitch_tier(ui, n, cfg):
    fb_static = flipbook(ui, "fb_tv_static", 4, 192, 12)
    fb_bands = flipbook(ui, "fb_tv_bands", 6, 256, 9)
    fb_tear = flipbook(ui, "fb_tv_tear", 4, 256, 8)
    controls = []
    if "static" in cfg:
        low, high, sec = cfg["static"]
        controls.append({"static": full("fx_static", 5, uv_size=[192, 108], uv=fb_static,
                                        alpha=breathe(ui, f"tv{n}_static", low, high, sec))})
    if "veil" in cfg:
        controls.append({"veil": full("fx_static", 5, uv_size=[192, 108], uv=fb_static,
                                      alpha=blips(ui, f"tv{n}_veil", cfg["veil"]))})
    if "scan" in cfg:
        controls.append({"scan": full("fx_scanlines", 6, alpha=cfg["scan"])})
    if "roll" in cfg:
        roll = full("fx_roll", 6, alpha=0.8)
        roll["size"] = ["100%", "28%"]
        roll["anims"] = [loop_offset(ui, f"tv{n}_roll", [0, 260], [0, -260], cfg["roll"])]
        controls.append({"roll": roll})
    controls.append({"bands": full("fx_static_bands", 7, uv_size=[256, 144], uv=fb_bands,
                                   alpha=blips(ui, f"tv{n}_bands", cfg["bands"]))})
    if "tear" in cfg:
        controls.append({"tear": full("fx_tear", 8, uv_size=[256, 144], uv=fb_tear,
                                      alpha=blips(ui, f"tv{n}_tear", cfg["tear"]))})
    return {f"tv_{n}": {"type": "panel", "size": ["100%", "100%"], "layer": 5, "controls": controls,
                        "bindings": [has(f"Rg{n}")]}}


# ---------------------------------------------------------------- clock
def clock():
    controls = [{"face": {"type": "image", "texture": TEX + "clock_face", "size": [34, 34], "layer": 1,
                          "anchor_from": "center", "anchor_to": "center"}}]
    for n in range(48):
        controls.append({f"hand_{n:02d}": {
            "type": "image", "texture": TEX + "clock_hands", "size": [34, 34], "layer": 3,
            "uv": [(n % 8) * 144, (n // 8) * 144], "uv_size": [144, 144],
            "anchor_from": "center", "anchor_to": "center", "bindings": [has(f"Rk{n:02d}")]}})
    controls.append({"day_label": {
        "type": "label", "text": "วันที่", "color": [1, 0.93, 0.8], "shadow": True, "localize": False,
        "font_type": "smooth", "font_scale_factor": 0.6, "layer": 4, "anchor_from": "center", "anchor_to": "center",
        "offset": [0, -3.5]}})
    for k in range(1, 5):
        digits = []
        for i in range(k):
            x = (i - (k - 1) / 2) * 4
            for d in range(10):
                digits.append({f"d{i}{d}": {
                    "type": "image", "texture": TEX + f"num_{d}", "size": [3.5, 4.5], "offset": [x, 3.5],
                    "layer": 4, "anchor_from": "center", "anchor_to": "center",
                    "bindings": [has(f"R{5 + i}{d}")]}})
        controls.append({f"day_{k}": {"type": "panel", "size": ["100%", "100%"], "layer": 0, "controls": digits,
                                      "bindings": [has(f"Rn{k}")]}})
    return {"succubi_clock": {"type": "panel", "size": [34, 34], "anchor_from": "top_right",
                              "anchor_to": "top_right", "offset": [-5, 5], "layer": 30, "controls": controls,
                              "bindings": [has("Rk")]}}


# ---------------------------------------------------------------- arrows
def arrows(ui, gauge):
    up = bob(ui, "arrow_up_bob", -1.5, 0.55)
    down = bob(ui, "arrow_down_bob", 1.5, 0.55)
    panels = []
    for code in range(1, 7):
        count = code if code <= 3 else code - 3
        rising = code <= 3
        imgs = []
        for i in range(count):
            imgs.append({f"a{i}": {"type": "image", "texture": TEX + f"arrow_{'up' if rising else 'down'}_{gauge}",
                                   "size": [6, 5], "offset": [(i - (count - 1) / 2) * 5, -15], "layer": 12,
                                   "anchor_from": "center", "anchor_to": "center",
                                   "anims": [up if rising else down]}})
        panels.append({f"rate_{code}": {"type": "panel", "size": ["100%", "100%"], "layer": 0, "controls": imgs,
                                        "bindings": [has(f"J{gauge}{code}")]}})
    return {"arrows": {"type": "panel", "size": ["100%", "100%"], "layer": 0, "controls": panels}}


def main():
    with open(PATH, encoding="utf-8") as f:
        ui = json.load(f)

    # drop what an earlier run made, and the old floating specks / grain
    for key in list(ui):
        if key.startswith(("tv", "fb_tv_", "arrow_up_bob", "arrow_down_bob", "drift_")) or key == "fb_grain":
            del ui[key]

    layer = ui["hud_layer"]["controls"]
    fx = next(c for c in layer if "succubi_screen_fx" in c)["succubi_screen_fx"]
    fx_on = fx["controls"][0]["fx_on"]
    fx_on["controls"] = [c for c in fx_on["controls"]
                         if not next(iter(c)).startswith(("specks_", "grain", "tv_"))]
    for n, cfg in TIERS.items():
        fx_on["controls"].append(glitch_tier(ui, n, cfg))

    shown = next(c for c in layer if "succubi_hud_shown" in c)["succubi_hud_shown"]
    shown["controls"] = [c for c in shown["controls"] if "succubi_clock" not in c]
    shown["controls"].append(clock())

    root = shown["controls"][0]["hud_root"]
    names = {"health": "h", "food": "f", "thirst": "t", "sanity": "s"}
    for c in root["controls"]:
        key = next(iter(c))
        if key in names:
            c[key]["controls"] = [x for x in c[key]["controls"] if "arrows" not in x]
            c[key]["controls"].append(arrows(ui, names[key]))

    with open(PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(ui, indent=2, ensure_ascii=False) + "\n")
    print("patched", os.path.basename(PATH))


if __name__ == "__main__":
    main()
