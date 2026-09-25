import { num, enabled } from "../succubi/settings_store.js";

// Height -> body stats. Every stat is set at three heights in the settings item (สเตตัสพื้นฐาน -> ส่วนสูง):
// the shortest a player may pick (h_min), the standard height (h_std) and the tallest (h_max), and runs in a
// straight line between them. Heights outside the player range (admins, "ส่วนสูงอิสระ") keep the end values.
//
// The game applies HP, walking speed and hunger through player.json component groups, so those are rounded to
// the steps the groups exist in (tools/gen_player_groups.py makes them):
export const GROUPS = {
  hp: { min: 10, max: 400, step: 5 }, // succubi:hp_010 ... hp_400      (minecraft:health)
  speed: { min: 50, max: 150, step: 1 }, // succubi:spdp_050 ... spdp_150 (minecraft:movement, % of 0.1)
  hunger: { min: 50, max: 200, step: 5 } // succubi:hun_050 ... hun_200  (minecraft:exhaustion_values, %)
};

const snap = (value, g) => Math.min(g.max, Math.max(g.min, Math.round(value / g.step) * g.step));

// The three heights, always in order and at least 1 cm apart
export function heightPoints() {
  const lo = Math.round(num("h_min"));
  const hi = Math.max(lo + 2, Math.round(num("h_max")));
  const std = Math.min(hi - 1, Math.max(lo + 1, Math.round(num("h_std"))));
  return { lo, std, hi };
}

// Straight lines lo -> std -> hi through (short, normal, tall)
export function along(cm, short, normal, tall, points = heightPoints()) {
  const { lo, std, hi } = points;
  const c = Math.min(hi, Math.max(lo, Number(cm) || std));
  if (c <= std) return normal + (short - normal) * ((std - c) / (std - lo));
  return normal + (tall - normal) * ((c - std) / (hi - std));
}

const pct = (cm, key, on) => (enabled(on) ? along(cm, num(`${key}_short`), 100, num(`${key}_tall`)) / 100 : 1);

// Max HP (a multiple of 5, 10-400)
export function hpFor(cm) {
  const base = num("hp_base");
  const hp = enabled("height_hp") ? along(cm, num("hp_short"), base, num("hp_tall")) : base;
  return snap(hp, GROUPS.hp);
}

// Walking speed in whole percent (50-150)
export const speedPercent = (cm) => snap(pct(cm, "spd", "height_speed") * 100, GROUPS.speed);
// Food exhaustion in steps of 5 % (50-200); water drain uses the same number
export const hungerPercent = (cm) => snap(pct(cm, "hunger", "height_hunger") * 100, GROUPS.hunger);

// Multipliers (1 = normal)
export const damageFor = (cm) => pct(cm, "dmg", "height_damage");
export const fallFor = (cm) => pct(cm, "fall", "height_fall");
export const hurtFor = (cm) => pct(cm, "hurt", "height_hurt");
