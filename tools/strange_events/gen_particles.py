# Particle effects for the strange events (RP particles/succubi/ev_*.json).
# Spawned per player with Player.spawnParticle, so only the haunted player sees them.
# Variables come from the script (MolangVariableMap): life, yaw, side, kind, tint, word, v, red, trap, dx/dy/dz ...
# Billboard "size" is half the width / height in blocks.
import json
import os
import sys

RP = sys.argv[1] if len(sys.argv) > 1 else "Succubi Server RP"
OUT = os.path.join(RP, "particles/succubi")
os.makedirs(OUT, exist_ok=True)
TEX = "textures/particle/succubi/"
LIFE = "(variable.life > 0 ? variable.life : 1)"
AGE = "(variable.particle_age / variable.particle_lifetime)"
FADE = f"math.clamp(variable.particle_age / 0.15, 0, 1) * math.clamp((1 - {AGE}) / 0.3, 0, 1)"


def effect(ident, texture, components, material="particles_blend"):
    data = {
        "format_version": "1.10.0",
        "particle_effect": {
            "description": {
                "identifier": f"succubi:{ident}",
                "basic_render_parameters": {"material": material, "texture": TEX + texture},
            },
            "components": components,
        },
    }
    with open(os.path.join(OUT, f"{ident}.json"), "w") as f:
        json.dump(data, f, indent=2)
    print("wrote", ident)


def once(n=1, shape=None):
    c = {
        "minecraft:emitter_rate_instant": {"num_particles": n},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
    }
    c.update(shape or {"minecraft:emitter_shape_point": {"offset": [0, 0, 0]}})
    return c


def billboard(size, facing, uv, tw, th, uv_size):
    return {
        "minecraft:particle_appearance_billboard": {
            "size": size,
            "facing_camera_mode": facing,
            "uv": {"texture_width": tw, "texture_height": th, "uv": uv, "uv_size": uv_size},
        }
    }


def decal(ident, texture, size, facing, uv, tw, th, uv_size, color, material="particles_blend", spin="variable.yaw"):
    c = once()
    c["minecraft:particle_lifetime_expression"] = {"max_lifetime": LIFE}
    c["minecraft:particle_initial_spin"] = {"rotation": spin}
    c.update(billboard(size, facing, uv, tw, th, uv_size))
    c["minecraft:particle_appearance_tinting"] = {"color": color}
    effect(ident, texture, c, material)


def main():
    # ---- floor decals (flat on the ground, turned by variable.yaw)
    # footprints: kind 0 adult / 1 child, side 0 left / 1 right; tint 0 wet, 1 soot, 2 mud
    wet_alpha = f"(0.85 * {FADE}) * (1 - {AGE} * 0.35)"
    decal("ev_foot", "ev_feet", ["variable.kind > 0.5 ? 0.075 : 0.085", "variable.kind > 0.5 ? 0.15 : 0.17"],
          "emitter_transform_xz", ["(variable.kind * 2 + variable.side) * 32", 0], 128, 64, [32, 64],
          ["variable.tint < 0.5 ? 0.10 + {a} * 0.12 : (variable.tint < 1.5 ? 0.05 : 0.28)".format(a=AGE),
           "variable.tint < 0.5 ? 0.12 + {a} * 0.10 : (variable.tint < 1.5 ? 0.04 : 0.20)".format(a=AGE),
           "variable.tint < 0.5 ? 0.16 + {a} * 0.06 : (variable.tint < 1.5 ? 0.04 : 0.13)".format(a=AGE),
           f"variable.tint < 0.5 ? {wet_alpha} : 0.9 * {FADE}"])
    # ash words (redrawn every half second by the script, alpha-tested so overlapping copies do not flicker)
    decal("ev_word", "ev_words", [0.8, 0.1], "emitter_transform_xz", [0, "variable.word * 32"], 256, 256, [256, 32],
          [0.32, 0.31, 0.30, 1.0], "particles_alpha")
    # drag smear, stretched along the drag direction
    decal("ev_drag", "ev_drag", [0.55, 0.28], "emitter_transform_xz", [0, 0], 64, 32, [64, 32],
          [1, 1, 1, f"0.9 * {FADE}"])
    # hair strands / clump (v 0..2)
    decal("ev_hair", "ev_hair", ["variable.v > 1.5 ? 0.3 : 0.24", "variable.v > 1.5 ? 0.3 : 0.24"],
          "emitter_transform_xz", ["variable.v * 64", 0], 192, 64, [64, 64], [1, 1, 1, f"{FADE}"], "particles_alpha")

    # handprints crawling over the floor (no wall nearby)
    decal("ev_hand_y", "ev_hands", [0.2, 0.2], "emitter_transform_xz", ["variable.v * 64", 0], 128, 64, [64, 64],
          [1, 1, 1, f"0.95 * {FADE}"])

    # ---- wall decals: _x for walls facing east / west (plane YZ), _z for north / south (plane XY)
    for axis, facing in (("x", "emitter_transform_yz"), ("z", "emitter_transform_xy")):
        decal(f"ev_hand_{axis}", "ev_hands", [0.2, 0.2], facing, ["variable.v * 64", 0], 128, 64, [64, 64],
              [1, 1, 1, f"0.95 * {FADE}"], spin="variable.yaw")
        decal(f"ev_scratch_{axis}", "ev_scratch", [0.3, 0.3], facing, ["variable.v * 64", 0], 128, 64, [64, 64],
              [1, 1, 1, f"{FADE}"], spin="variable.yaw")

    # ---- camera-facing billboards
    # eyes: frame 0 open .. 3 closed; open fast, blink now and then, close at the end
    frame = ("variable.particle_age < 0.12 ? 3 : (variable.particle_age < 0.25 ? 2 : "
             f"((variable.particle_lifetime - variable.particle_age) < 0.25 ? 2 : "
             "(math.mod(variable.particle_age + variable.particle_random_1 * 3, 2.6) < 0.12 ? 3 : 0)))")
    c = once()
    c["minecraft:particle_lifetime_expression"] = {"max_lifetime": LIFE}
    c.update(billboard(["0.16 * (variable.scale > 0 ? variable.scale : 1)", "0.08 * (variable.scale > 0 ? variable.scale : 1)"],
                       "rotate_xyz", [f"({frame}) * 32", 0], 128, 16, [32, 16]))
    c["minecraft:particle_appearance_tinting"] = {"color": [
        1, "variable.red > 0.5 ? 0.18 : 0.85", "variable.red > 0.5 ? 0.12 : 0.55",
        f"math.clamp(variable.particle_age / 0.1, 0, 1)"]}
    effect("ev_eyes", "ev_eyes", c, "particles_add")

    # candle body and flame (redrawn by the script while lit)
    c = once()
    c["minecraft:particle_lifetime_expression"] = {"max_lifetime": LIFE}
    c.update(billboard([0.06, 0.12], "rotate_y", [0, 0], 16, 32, [16, 32]))
    effect("ev_candle", "ev_candle", c, "particles_alpha")
    c = once()
    c["minecraft:particle_lifetime_expression"] = {"max_lifetime": LIFE}
    c["minecraft:particle_appearance_billboard"] = {
        "size": ["0.045 + math.sin(variable.particle_age * 900) * 0.006", "0.09 + math.sin(variable.particle_age * 700) * 0.01"],
        "facing_camera_mode": "rotate_y",
        "uv": {"texture_width": 64, "texture_height": 32,
               "flipbook": {"base_UV": [0, 0], "size_UV": [16, 32], "step_UV": [16, 0], "frames_per_second": 10,
                            "max_frame": 4, "loop": True}}}
    effect("ev_flame", "ev_flame", c, "particles_add")

    # soft puffs: smoke (grey, rising), breath (white, drifting along dx/dy/dz), dust (falling), motes (glow)
    def puffs(ident, n, box, speed, direction, accel, drag, life, size, color, material="particles_blend"):
        c = once(n, {"minecraft:emitter_shape_box": {"offset": [0, 0, 0], "half_dimensions": box, "direction": direction}})
        c["minecraft:particle_lifetime_expression"] = {"max_lifetime": life}
        c["minecraft:particle_initial_speed"] = speed
        c["minecraft:particle_initial_spin"] = {"rotation": "variable.particle_random_4 * 360",
                                                "rotation_rate": "(variable.particle_random_1 - 0.5) * 40"}
        c["minecraft:particle_motion_dynamic"] = {"linear_acceleration": accel, "linear_drag_coefficient": drag}
        c.update(billboard(size, "rotate_xyz", [0, 0], 32, 32, [32, 32]))
        c["minecraft:particle_appearance_tinting"] = {"color": color}
        effect(ident, "ev_puff", c, material)

    puffs("ev_smoke", 7, [0.03, 0.02, 0.03], "0.15 + variable.particle_random_3 * 0.2", [0, 1, 0], [0, 0.4, 0], 1.5,
          "2.2 + variable.particle_random_1", ["0.09 + variable.particle_age * 0.12", "0.09 + variable.particle_age * 0.12"],
          [0.35, 0.34, 0.33, f"0.55 * (1 - {AGE})"])
    puffs("ev_breath", 6, [0.05, 0.05, 0.05], "0.6 + variable.particle_random_3 * 0.4",
          ["variable.dx", "variable.dy", "variable.dz"], [0, 0.05, 0], 2.2, "1.2 + variable.particle_random_1 * 0.6",
          ["0.06 + variable.particle_age * 0.18", "0.06 + variable.particle_age * 0.18"],
          [0.9, 0.95, 1.0, f"0.4 * (1 - {AGE})"])
    puffs("ev_dust", 14, [0.35, 0.02, 0.35], "0.05", [0, -1, 0], [0, -4, 0], 0.5, "0.9 + variable.particle_random_1 * 0.5",
          ["0.015 + variable.particle_random_2 * 0.02", "0.015 + variable.particle_random_2 * 0.02"],
          [0.55, 0.5, 0.45, f"0.8 * (1 - {AGE})"])
    puffs("ev_mote", 3, [0.25, 0.25, 0.25], "0.05", [0, 1, 0], [0, 0.1, 0], 1.0, 1.6,
          ["0.025", "0.025"], [0.8, 0.85, 1.0, f"0.6 * math.sin({AGE} * 180)"], "particles_add")

    # little drops: splash (water, when a wet print lands) and blood running down a wall
    def drops(ident, n, speed, direction, accel, life, color, size=0.018):
        c = once(n, {"minecraft:emitter_shape_point": {"offset": [0, 0, 0], "direction": direction}})
        c["minecraft:particle_lifetime_expression"] = {"max_lifetime": life}
        c["minecraft:particle_initial_speed"] = speed
        c["minecraft:particle_motion_dynamic"] = {"linear_acceleration": accel, "linear_drag_coefficient": 1}
        c.update(billboard([size, size * 1.4], "rotate_y", [0, 0], 8, 8, [8, 8]))
        c["minecraft:particle_appearance_tinting"] = {"color": color}
        effect(ident, "ev_drop", c)

    drops("ev_splash", 5, "0.8 + variable.particle_random_1", ["math.random(-1, 1)", 1.5, "math.random(-1, 1)"],
          [0, -9, 0], 0.35, [0.45, 0.55, 0.7, 0.8])
    drops("ev_blood_drip", 1, 0.05, [0, -1, 0], [0, -0.12, 0], "2.5 + variable.particle_random_1 * 2",
          [0.42, 0.02, 0.02, f"1 - {AGE} * 0.5"], 0.02)

    # ash burst when a word crumbles
    c = once(26, {"minecraft:emitter_shape_box": {"offset": [0, 0.02, 0], "half_dimensions": [0.7, 0.02, 0.12],
                                                  "direction": ["math.random(-0.4, 0.4)", 1, "math.random(-0.4, 0.4)"]}})
    c["minecraft:particle_lifetime_expression"] = {"max_lifetime": "1.2 + variable.particle_random_1 * 1.2"}
    c["minecraft:particle_initial_speed"] = "0.3 + variable.particle_random_2 * 0.6"
    c["minecraft:particle_initial_spin"] = {"rotation": "variable.particle_random_3 * 360", "rotation_rate": 120}
    c["minecraft:particle_motion_dynamic"] = {"linear_acceleration": [0.3, 0.15, 0], "linear_drag_coefficient": 1.5}
    c.update(billboard([0.03, 0.03], "rotate_xyz", ["math.floor(variable.particle_random_4 * 4) * 8", 0], 32, 8, [8, 8]))
    c["minecraft:particle_appearance_tinting"] = {"color": [1, 1, 1, f"1 - {AGE}"]}
    effect("ev_ash_burst", "ev_ash", c)

    # will-o'-wisp orb (redrawn while it moves) + its falling sparks; variable.trap tints it red for ตาทิพย์ wearers
    c = once()
    c["minecraft:particle_lifetime_expression"] = {"max_lifetime": 0.3}
    c["minecraft:particle_appearance_billboard"] = {
        "size": ["0.16 + math.sin(query.time_stamp * 0.3) * 0.02", "0.16 + math.sin(query.time_stamp * 0.3) * 0.02"],
        "facing_camera_mode": "rotate_xyz",
        "uv": {"texture_width": 32, "texture_height": 32, "uv": [0, 0], "uv_size": [32, 32]}}
    c["minecraft:particle_appearance_tinting"] = {"color": [
        "variable.trap > 0.5 ? 1.0 : 0.45", "variable.trap > 0.5 ? 0.3 : 0.95", "variable.trap > 0.5 ? 0.25 : 0.85", 1]}
    effect("ev_wisp", "ev_orb", c, "particles_add")

    def sparks(ident, n, speed, direction, accel, life, color, size=0.03):
        c = once(n, {"minecraft:emitter_shape_sphere": {"offset": [0, 0, 0], "radius": 0.1, "direction": direction}})
        c["minecraft:particle_lifetime_expression"] = {"max_lifetime": life}
        c["minecraft:particle_initial_speed"] = speed
        c["minecraft:particle_motion_dynamic"] = {"linear_acceleration": accel, "linear_drag_coefficient": 2}
        c.update(billboard([size, size], "rotate_xyz", [0, 0], 8, 8, [8, 8]))
        c["minecraft:particle_appearance_tinting"] = {"color": color}
        effect(ident, "ev_spark", c, "particles_add")

    sparks("ev_wisp_trail", 3, 0.2, "outwards", [0, -0.6, 0], "0.6 + variable.particle_random_1 * 0.5",
           ["variable.trap > 0.5 ? 1.0 : 0.5", "variable.trap > 0.5 ? 0.35 : 1.0", "variable.trap > 0.5 ? 0.3 : 0.9",
            f"1 - {AGE}"], 0.02)
    sparks("ev_holy_burst", 44, "2.5 + variable.particle_random_1 * 2", "outwards", [0, 0.5, 0],
           "0.9 + variable.particle_random_2 * 0.6", [1.0, 0.85, 0.35, f"1 - {AGE}"], 0.04)
    sparks("ev_gift", 18, 1.2, "outwards", [0, 1.2, 0], 1.2, [0.55, 1.0, 0.8, f"1 - {AGE}"], 0.035)

    # pale hands reaching out of the ground (redrawn while they rise), frame 0 open / 1 clawing
    c = once()
    c["minecraft:particle_lifetime_expression"] = {"max_lifetime": LIFE}
    c.update(billboard([0.14, 0.28], "rotate_y", ["variable.claw * 32", 0], 64, 64, [32, 64]))
    c["minecraft:particle_appearance_tinting"] = {"color": [1, 1, 1, 1]}
    effect("ev_reach", "ev_reach", c, "particles_alpha")


if __name__ == "__main__":
    main()
