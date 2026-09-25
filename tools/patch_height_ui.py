"""Height window (RP ui/succubi_height.json) for the v1.1.9 flow. Safe to run again.

 - Menu (ActionForm, height_panel): wide buttons in a 2 x 2 grid - ปรับส่วนสูง / รีเซ็ต / ยกเลิก.
   The reset question uses the same window with two buttons (ยืนยัน / ยกเลิก).
 - Slider (ModalForm, height_modal): the X now cancels (it used to save), and two buttons under the slider:
   ยืนยัน = submit the form, ยกเลิก = close without changing anything.
"""
import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon", "Succubi Server RP", "ui",
                    "succubi_height.json")
TEX = "textures/ui/succubi_height/"


def overlay(texture):
    return {"overlay": {"type": "image", "texture": TEX + texture, "size": ["100%", "100%"], "layer": 2}}


def state(offset_y, extra=None):
    controls = [{"art@succubi_height.hb_art": {}}, {"label@succubi_height.wb_label": {}}]
    if extra:
        controls.append(overlay(extra))
    return {"type": "panel", "size": ["100%", "100%"], "offset": [0, offset_y], "controls": controls}


def modal_button(name, pressed, texture, text, x):
    def face(offset_y, extra=None):
        controls = [
            {"art": {"type": "image", "texture": TEX + texture, "size": ["100%", "100%"], "layer": 1}},
            {"label": {"type": "label", "text": text, "color": [1, 1, 1], "shadow": True, "localize": False,
                       "layer": 3, "anchor_from": "center", "anchor_to": "center", "offset": [7, -1],
                       "font_type": "smooth"}},
        ]
        if extra:
            controls.append(overlay(extra))
        return {"type": "panel", "size": ["100%", "100%"], "offset": [0, offset_y], "controls": controls}

    return {
        f"{name}@common.button": {
            "size": [70, 21],
            "anchor_from": "top_left",
            "anchor_to": "top_left",
            "offset": [x, 150],
            "layer": 8,
            "$pressed_button_name": pressed,
            "controls": [
                {"default": face(0)},
                {"hover": face(0, "wbtn_hover")},
                {"pressed": face(1, "wbtn_pressed")},
            ],
        }
    }


def main():
    with open(PATH, encoding="utf-8") as f:
        ui = json.load(f)

    # wide menu buttons: 2 x 2 cells of 76 x 24 in the same 152 x 48 area
    ui["wcell"] = {
        "type": "panel",
        "size": [76, 24],
        "controls": [
            {
                "button@common.button": {
                    "size": [74, 22],
                    "$pressed_button_name": "button.form_button_click",
                    "bindings": [{"binding_type": "collection_details", "binding_collection_name": "form_buttons"}],
                    "controls": [
                        {"default@succubi_height.wb_default": {}},
                        {"hover@succubi_height.wb_hover": {}},
                        {"pressed@succubi_height.wb_pressed": {}},
                    ],
                }
            }
        ],
    }
    label = dict(ui["hb_label"])
    label["offset"] = [8, -1]
    ui["wb_label"] = label
    ui["wb_default"] = state(0)
    ui["wb_hover"] = state(0, "wbtn_hover")
    ui["wb_pressed"] = state(1, "wbtn_pressed")

    for c in ui["height_panel"]["controls"]:
        if "buttons" in c:
            c["buttons"]["grid_dimensions"] = [2, 2]
            c["buttons"]["grid_item_template"] = "succubi_height.wcell"

    modal = ui["height_modal"]["controls"]
    kept = []
    for c in modal:
        key = next(iter(c))
        if key.startswith(("confirm@", "cancel@")):
            continue  # made again below
        if key.startswith("close@"):
            c[key].pop("$pressed_button_name", None)  # back to the default: button.menu_exit = cancel
        if key == "form":
            c[key]["size"] = [140, 112]
        kept.append(c)
    kept.append(modal_button("confirm", "button.submit_custom_form", "wbtn_confirm", "ยืนยัน", 128))
    kept.append(modal_button("cancel", "button.menu_exit", "wbtn_cancel", "ยกเลิก", 202))
    ui["height_modal"]["controls"] = kept

    with open(PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(ui, indent=2, ensure_ascii=False) + "\n")
    print("patched", os.path.basename(PATH))


if __name__ == "__main__":
    main()
