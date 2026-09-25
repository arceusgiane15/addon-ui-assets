"""Shadow creatures drawn with particles only the mad can see (v1.1.9). Safe to run again.

The chaser (succubi:shadow_creature, tools/gen_shadow_assets.py) is an invisible body: this render controller
hides its model and the script keeps it under the invisibility effect (that also removes the ground shadow). What the insane
player sees is sent with Player.spawnParticle, which shows only to that player:

 succubi:shadow_body    smoke puffs filling a box (variable.hx / hy / hz = half size, variable.n = how many)
 succubi:shadow_eye     a red eye with a soft glow
 succubi:shadow_wisp    dark smoke curling up from the feet
 succubi:shadow_ember   a few violet sparks drifting around it
 succubi:shadow_gather  smoke pulled together where it appears
 succubi:shadow_burst   smoke thrown apart when it is destroyed

Textures: textures/particle/succubi/shadow_smoke.png (8 frames, 16x16, dissolving puff), shadow_glow.png.
"""
import json
import math
import os
import random

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "addon")
BP = os.path.join(ROOT, "Succubi Server BP")
RP = os.path.join(ROOT, "Succubi Server RP")
rnd = random.Random(1115)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- textures
def smoke_strip():
    """8 frames top to bottom: a round puff that thins out and breaks up (white, tinted by the particle)"""
    img = Image.new("RGBA", (16, 128), (0, 0, 0, 0))
    holes = [(rnd.uniform(2, 13), rnd.uniform(2, 13), rnd.random()) for _ in range(40)]
    for f in range(8):
        age = f / 7
        radius = 7.2 - age * 1.8
        for y in range(16):
            for x in range(16):
                dx, dy = x - 7.5, y - 7.5
                dist = math.hypot(dx, dy) + math.sin(x * 1.7 + y * 1.3 + f) * 0.6
                if dist > radius:
                    continue
                edge = 1 - dist / radius
                a = min(1.0, edge * 2.6) * (1 - age * 0.3)
                for hx, hy, t in holes:  # holes open up as it ages
                    if t < age * 0.6 and math.hypot(x - hx, y - hy) < 1.0 + age:
                        a *= 0.5
                shade = int(200 + 55 * edge)
                img.putpixel((x, f * 16 + y), (shade, shade, shade, int(255 * max(0, min(1, a)))))
    return img


def glow():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5) / 7.5
            if d < 1:
                img.putpixel((x, y), (255, 255, 255, int(255 * (1 - d) ** 1.6)))
    return img


# ---------------------------------------------------------------- particles
SMOKE = "textures/particle/succubi/shadow_smoke"
GLOW = "textures/particle/succubi/shadow_glow"
FADE = "1 - math.pow(variable.particle_age / variable.particle_lifetime, 2)"


def smoke_uv():
    return {"texture_width": 16, "texture_height": 128,
            "flipbook": {"base_UV": [0, 0], "size_UV": [16, 16], "step_UV": [0, 16],
                         "max_frame": 8, "stretch_to_lifetime": True}}


def effect(identifier, material, texture, components):
    return {"format_version": "1.10.0", "particle_effect": {
        "description": {"identifier": identifier,
                        "basic_render_parameters": {"material": material, "texture": texture}},
        "components": components}}


# the shadow's colour: near black with a violet heart (no lighting, so it stays dark in torchlight)
DARK = ["0.05 + variable.particle_random_2 * 0.05", "0.02", "0.07 + variable.particle_random_2 * 0.06", FADE + " * 0.92"]

PARTICLES = {
    "succubi_shadow_body": effect("succubi:shadow_body", "particles_blend", SMOKE, {
        "minecraft:emitter_rate_instant": {"num_particles": "variable.n"},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_box": {"offset": [0, 0, 0],
                                        "half_dimensions": ["variable.hx", "variable.hy", "variable.hz"],
                                        "surface_only": False, "direction": [0, 1, 0]},
        "minecraft:particle_lifetime_expression": {"max_lifetime": "0.45 + variable.particle_random_1 * 0.3"},
        "minecraft:particle_initial_speed": "0.05 + variable.particle_random_3 * 0.1",
        "minecraft:particle_initial_spin": {"rotation": "variable.particle_random_4 * 360",
                                            "rotation_rate": "(variable.particle_random_1 - 0.5) * 60"},
        "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.35, 0], "linear_drag_coefficient": 2},
        "minecraft:particle_appearance_billboard": {
            "size": ["0.3 - variable.particle_age * 0.25 + variable.particle_random_3 * 0.08",
                     "0.3 - variable.particle_age * 0.25 + variable.particle_random_3 * 0.08"],
            "facing_camera_mode": "rotate_xyz", "uv": smoke_uv()},
        "minecraft:particle_appearance_tinting": {"color": DARK},
    }),
    "succubi_shadow_wisp": effect("succubi:shadow_wisp", "particles_blend", SMOKE, {
        "minecraft:emitter_rate_instant": {"num_particles": 3},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_disc": {"offset": [0, 0.05, 0], "radius": 0.35, "plane_normal": "y",
                                         "surface_only": False, "direction": "outwards"},
        "minecraft:particle_lifetime_expression": {"max_lifetime": "0.9 + variable.particle_random_1 * 0.5"},
        "minecraft:particle_initial_speed": 0.15,
        "minecraft:particle_initial_spin": {"rotation": "variable.particle_random_4 * 360", "rotation_rate": 40},
        "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.9, 0], "linear_drag_coefficient": 1.5},
        "minecraft:particle_appearance_billboard": {
            "size": ["0.12 + variable.particle_age * 0.25", "0.12 + variable.particle_age * 0.25"],
            "facing_camera_mode": "rotate_xyz", "uv": smoke_uv()},
        "minecraft:particle_appearance_tinting": {"color": ["0.06", "0.02", "0.09", FADE + " * 0.7"]},
    }),
    "succubi_shadow_eye": effect("succubi:shadow_eye", "particles_add", GLOW, {
        "minecraft:emitter_rate_instant": {"num_particles": 2},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_point": {"offset": [0, 0, 0]},
        "minecraft:particle_lifetime_expression": {"max_lifetime": 0.2},
        "minecraft:particle_appearance_billboard": {
            # one small hot core, one wider dim halo
            "size": ["variable.particle_random_1 < 0.5 ? 0.06 : 0.2", "variable.particle_random_1 < 0.5 ? 0.06 : 0.2"],
            "facing_camera_mode": "rotate_xyz",
            "uv": {"texture_width": 16, "texture_height": 16, "uv": [0, 0], "uv_size": [16, 16]}},
        "minecraft:particle_appearance_tinting": {
            "color": ["1", "variable.particle_random_1 < 0.5 ? 0.45 : 0.08", "variable.particle_random_1 < 0.5 ? 0.45 : 0.1",
                      "variable.particle_random_1 < 0.5 ? 1 : 0.55"]},
    }),
    "succubi_shadow_ember": effect("succubi:shadow_ember", "particles_add", GLOW, {
        "minecraft:emitter_rate_instant": {"num_particles": 2},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_box": {"offset": [0, 0, 0], "half_dimensions": [0.35, 0.8, 0.35],
                                        "surface_only": False, "direction": "outwards"},
        "minecraft:particle_lifetime_expression": {"max_lifetime": "1.2 + variable.particle_random_1"},
        "minecraft:particle_initial_speed": 0.1,
        "minecraft:particle_motion_dynamic": {
            "linear_acceleration": ["math.sin(variable.particle_age * 300) * 0.6", 0.35,
                                    "math.cos(variable.particle_age * 300) * 0.6"],
            "linear_drag_coefficient": 1},
        "minecraft:particle_appearance_billboard": {
            "size": [0.035, 0.035], "facing_camera_mode": "rotate_xyz",
            "uv": {"texture_width": 16, "texture_height": 16, "uv": [0, 0], "uv_size": [16, 16]}},
        "minecraft:particle_appearance_tinting": {"color": ["0.55", "0.2", "0.85", FADE]},
    }),
    "succubi_shadow_gather": effect("succubi:shadow_gather", "particles_blend", SMOKE, {
        "minecraft:emitter_rate_instant": {"num_particles": 40},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_sphere": {"offset": [0, 1, 0], "radius": 1.6, "surface_only": True,
                                           "direction": "inwards"},
        "minecraft:particle_lifetime_expression": {"max_lifetime": 0.7},
        "minecraft:particle_initial_speed": 2.4,
        "minecraft:particle_motion_dynamic": {"linear_drag_coefficient": 1.5},
        "minecraft:particle_appearance_billboard": {
            "size": ["0.25 - variable.particle_age * 0.2", "0.25 - variable.particle_age * 0.2"],
            "facing_camera_mode": "rotate_xyz", "uv": smoke_uv()},
        "minecraft:particle_appearance_tinting": {"color": DARK},
    }),
    "succubi_shadow_burst": effect("succubi:shadow_burst", "particles_blend", SMOKE, {
        "minecraft:emitter_rate_instant": {"num_particles": 70},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_sphere": {"offset": [0, 1, 0], "radius": 0.5, "surface_only": False,
                                           "direction": "outwards"},
        "minecraft:particle_lifetime_expression": {"max_lifetime": "0.8 + variable.particle_random_1 * 0.7"},
        "minecraft:particle_initial_speed": "2 + variable.particle_random_2 * 2",
        "minecraft:particle_initial_spin": {"rotation": "variable.particle_random_4 * 360", "rotation_rate": 90},
        "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.6, 0], "linear_drag_coefficient": 3},
        "minecraft:particle_appearance_billboard": {
            "size": ["0.3 - variable.particle_age * 0.15", "0.3 - variable.particle_age * 0.15"],
            "facing_camera_mode": "rotate_xyz", "uv": smoke_uv()},
        "minecraft:particle_appearance_tinting": {"color": DARK},
    }),
}

HIDDEN_RC = {"format_version": "1.8.0", "render_controllers": {"controller.render.succubi_hidden": {
    "geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"],
    "part_visibility": [{"*": False}]}}}


def main():
    tex = os.path.join(RP, "textures", "particle", "succubi")
    os.makedirs(tex, exist_ok=True)
    smoke_strip().save(os.path.join(tex, "shadow_smoke.png"))
    glow().save(os.path.join(tex, "shadow_glow.png"))
    for name, data in PARTICLES.items():
        write_json(os.path.join(RP, "particles", "succubi", name + ".json"), data)
    write_json(os.path.join(RP, "render_controllers", "succubi_hidden.render_controllers.json"), HIDDEN_RC)

    print("particle shadow written")


if __name__ == "__main__":
    main()
