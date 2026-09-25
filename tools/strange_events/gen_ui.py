# Adds the strange-event screens to the RP UI (idempotent: re-running replaces what it added).
#  ui/succubi_hud.json : screen overlays switched by HUD tokens (sent in the title by hud.js / screenfx.js)
#     Yqf1 / Yqf2 scare face     Yqv VHS         Yqe eyes at the screen edge     Yqb blood from the top edge
#     Yqk lights out (black)     Yqd darkness closing in (vignette)
#     (Y is otherwise always followed by a digit, so "Yq" never shows up by accident)
#  ui/succubi_paper.json: bloody paper variant (title flag §8§8§5) + the photo window (photo_panel)
#  ui/server_form.json  : routes the photo flag §0§9§5§8 to photo_panel (photo n = §7§7§n)
import json
import os
import sys

RP = sys.argv[1] if len(sys.argv) > 1 else "Succubi Server RP"
UI = os.path.join(RP, "ui")
TEX = "textures/ui/succubi_events/"


def load(name):
    with open(os.path.join(UI, name)) as f:
        return json.load(f)


def dump(name, data):
    with open(os.path.join(UI, name), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("updated", name)


def has(token, source="#preserved_text"):
    return f"(not (({source} - '{token}') = {source}))"


def hud_vis(token):
    return [{"binding_type": "view", "source_control_name": "succubi_hud_data",
             "source_property_name": has(token), "target_property_name": "#visible"}]


def full_image(texture, layer, token=None, alpha=None, uv=None, uv_size=None):
    c = {"type": "image", "texture": TEX + texture, "size": ["100%", "100%"], "offset": [0, 0],
         "anchor_from": "center", "anchor_to": "center", "layer": layer, "keep_ratio": False}
    if alpha is not None:
        c["alpha"] = alpha
    if uv:
        c["uv"] = uv
        c["uv_size"] = uv_size
    if token:
        c["bindings"] = hud_vis(token)
    return c


def find(node, name):
    for c in node.get("controls", []):
        for k, v in c.items():
            if k == name:
                return v
            if isinstance(v, dict):
                r = find(v, name)
                if r is not None:
                    return r
    return None


def strip(controls, prefix):
    return [c for c in controls if not any(k.startswith(prefix) for k in c)]


def hud():
    d = load("succubi_hud.json")
    d["ev_vhs_fb"] = {"anim_type": "flip_book", "initial_uv": [0, 0], "frame_count": 4, "frame_step": 256, "fps": 7, "easing": "linear"}
    d["ev_eyes_fb"] = {"anim_type": "flip_book", "initial_uv": [0, 0], "frame_count": 4, "frame_step": 256, "fps": 2, "easing": "linear"}
    d["ev_blood_fb"] = {"anim_type": "flip_book", "initial_uv": [0, 0], "frame_count": 8, "frame_step": 256, "fps": 4, "easing": "linear"}
    d["ev_flicker_a"] = {"anim_type": "alpha", "easing": "linear", "duration": 0.18, "from": 1.0, "to": 0.82, "next": "@succubi_hud.ev_flicker_b"}
    d["ev_flicker_b"] = {"anim_type": "alpha", "easing": "linear", "duration": 0.27, "from": 0.82, "to": 1.0, "next": "@succubi_hud.ev_flicker_a"}

    layer = d["hud_layer"]
    fx = find(layer, "succubi_screen_fx")
    fx_on = find(layer, "fx_on")
    # effects the player can switch off (screen effects off = Nx): face, VHS, eyes, blood
    fx_on["controls"] = strip(fx_on["controls"], "ev_")
    fx_on["controls"] += [
        {"ev_blood": full_image("blood_edge", 36, "Yqb", 1.0, "@succubi_hud.ev_blood_fb", [256, 144])},
        {"ev_eyes": full_image("edge_eyes", 37, "Yqe", 1.0, "@succubi_hud.ev_eyes_fb", [256, 144])},
        {"ev_vhs": {"type": "panel", "size": ["100%", "100%"], "layer": 38, "controls": [
            {"wash": full_image("vhs_wash", 38)},
            {"strip": full_image("vhs", 39, None, "@succubi_hud.ev_flicker_a", "@succubi_hud.ev_vhs_fb", [256, 144])},
        ], "bindings": hud_vis("Yqv")}},
        {"ev_face_1": full_image("face_1", 45, "Yqf1")},
        {"ev_face_2": full_image("face_2", 45, "Yqf2")},
    ]
    # darkness is part of play (count to ten, hold a light): always drawn
    fx["controls"] = strip(fx["controls"], "ev_")
    fx["controls"] += [
        {"ev_dark": full_image("dark_vignette", 30, "Yqd", 1.0)},
        {"ev_black": full_image("black", 31, "Yqk", 0.965)},
    ]
    # 24 h digital clock under the clock face: R1 R2 = hour digits, R3 R4 = minute digits (daytime.js)
    shown = find(layer, "succubi_hud_shown")
    shown["controls"] = strip(shown["controls"], "succubi_clock_time")
    digits = []
    for slot, (token, x) in enumerate((("R1", -9.2), ("R2", -4.4), ("R3", 4.4), ("R4", 9.2))):
        for n in range(10):
            digits.append({f"t{slot}{n}": {
                "type": "image", "texture": f"textures/ui/succubi_hud/num_{n}", "size": [4.4, 5.6], "offset": [x, 0],
                "layer": 3, "anchor_from": "center", "anchor_to": "center", "bindings": hud_vis(f"{token}{n}")}})
    at = next(i for i, c in enumerate(shown["controls"]) if "succubi_clock" in c) + 1
    shown["controls"].insert(at, {"succubi_clock_time": {
        "type": "panel", "size": [30, 9], "anchor_from": "top_right", "anchor_to": "top_right", "offset": [-7, 41], "layer": 30,
        "controls": [
            {"bg": {"type": "image", "texture": TEX + "black", "size": ["100%", "100%"], "layer": 1, "alpha": 0.45}},
            {"colon": {"type": "label", "text": ":", "color": [1, 0.93, 0.8], "shadow": True, "localize": False,
                       "font_type": "smooth", "font_scale_factor": 0.7, "layer": 4, "anchor_from": "center",
                       "anchor_to": "center", "offset": [0, -0.6]}},
        ] + digits,
        "bindings": hud_vis("Rk")}})
    dump("succubi_hud.json", d)


def paper():
    d = load("succubi_paper.json")
    pp = d["paper_panel"]
    pp["controls"] = strip(pp["controls"], "bg_blood")
    pp["controls"].insert(1, {"bg_blood": {
        "type": "image", "texture": "textures/ui/succubi_paper/paper_blood", "size": ["100%", "100%"], "layer": 2,
        "bindings": [{"binding_name": "#title_text"},
                     {"binding_type": "view", "source_property_name": has("§8§8§5", "#title_text"), "target_property_name": "#visible"}]}})
    controls = [{"frame": {"type": "image", "texture": TEX + "photo_frame", "size": ["100%", "100%"], "layer": 1}}]
    for n in range(1, 7):
        controls.append({f"photo_{n}": {
            "type": "image", "texture": TEX + f"photo_{n}", "size": [158, 158], "layer": 2,
            "anchor_from": "top_middle", "anchor_to": "top_middle", "offset": [0, 20],
            "bindings": [{"binding_name": "#title_text"},
                         {"binding_type": "view", "source_property_name": has(f"§7§7§{n}", "#title_text"),
                          "target_property_name": "#visible"}]}})
    controls += [
        {"caption": {"type": "label", "text": "#form_text", "color": [0.35, 0.05, 0.04], "localize": False,
                     "shadow": False, "anchor_from": "top_middle", "anchor_to": "top_middle", "offset": [0, 184],
                     "size": [190, "default"], "text_alignment": "center", "layer": 5, "font_type": "smooth",
                     "bindings": [{"binding_name": "#form_text"}]}},
        {"slots": {"type": "grid", "anchor_from": "bottom_middle", "anchor_to": "bottom_middle", "offset": [36, -8],
                   "size": [142, 30], "grid_dimensions": [2, 1], "grid_item_template": "succubi_paper.cell",
                   "collection_name": "form_buttons", "layer": 5}},
    ]
    d["photo_panel"] = {"type": "panel", "size": [200, 242], "layer": 2, "controls": controls}
    dump("succubi_paper.json", d)


def server_form():
    d = load("server_form.json")
    lf = d["long_form"]
    lf["controls"] = strip(lf["controls"], "succubi_photo@")
    entry = {"succubi_photo@succubi_paper.photo_panel": {"bindings": [
        {"binding_name": "#title_text"},
        {"binding_type": "view", "source_property_name": has("§0§9§5§8", "#title_text"), "target_property_name": "#visible"}]}}
    # right after the paper window
    at = next(i for i, c in enumerate(lf["controls"]) if "succubi_paper@succubi_paper.paper_panel" in c)
    lf["controls"].insert(at + 1, entry)
    dump("server_form.json", d)


if __name__ == "__main__":
    hud()
    paper()
    server_form()
