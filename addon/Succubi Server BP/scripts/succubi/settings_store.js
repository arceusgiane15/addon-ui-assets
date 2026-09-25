import { world } from "@minecraft/server";

// World-wide switches and numbers set from the settings item (อุปกรณ์ตั้งค่าเซิร์ฟเวอร์)
const KEYS = {
  sanity: "succubi:cfg_sanity", // sanity system + the brain gauge
  thirst: "succubi:cfg_thirst", // thirst system + the water gauge
  hud_numbers: "succubi:cfg_hud_numbers", // faint numbers under the gauges
  pressure: "succubi:cfg_pressure", // heartbeat / stomach / panting / whisper sounds when a value is low
  horror: "succubi:cfg_horror", // Rule of Horror master switch: off = nothing strange happens at all
  events: "succubi:cfg_events", // random strange events (inside Rule of Horror)
  rules: "succubi:cfg_rules", // rule zones, rule boards, watcher statues (inside Rule of Horror)
  height_hp: "succubi:cfg_height_hp", // height changes max HP
  height_speed: "succubi:cfg_height_speed", // height changes walking speed
  height_damage: "succubi:cfg_height_damage", // height changes melee hit strength
  nametag_near: "succubi:cfg_nametag_near", // player names only while looking at them (old "No Nametag" subpack)
  height_free: "succubi:cfg_height_free" // players may pick any height, no cooldown (old behaviour)
};
const DEFAULT_OFF = new Set(["nametag_near", "height_free"]);

// Numbers (base stats). 0 in regen_seconds / food_drain_seconds = leave it to the game.
export const NUMS = {
  hp_base: { def: 100, min: 20, max: 200 }, // max HP at 180 cm (height: half at 140 cm, double at 220 cm, never over 200)
  regen_seconds: { def: 0, min: 0, max: 60 }, // 1 HP every N seconds (0 = the game's own natural regeneration)
  regen_food: { def: 18, min: 0, max: 20 }, // food needed for that regeneration
  food_drain_seconds: { def: 0, min: 0, max: 600 }, // extra: 1 food every N seconds (0 = only the game's own hunger)
  thirst_max: { def: 20, min: 10, max: 100 },
  thirst_seconds: { def: 40, min: 5, max: 600 }, // 1 water every N seconds standing still (running x2.2, Nether x1.6)
  sanity_loss: { def: 100, min: 0, max: 300 }, // % of every sanity loss
  sanity_gain: { def: 100, min: 0, max: 300 }, // % of every sanity gain
  event_minutes: { def: 65, min: 10, max: 240 } // about how often a strange event finds each player
};

const listeners = [];
// fn(name) runs after any switch or number changes (regen, link pack config, heights re-apply)
export function onSettingChange(fn) {
  listeners.push(fn);
}
function changed(name) {
  for (const fn of listeners) {
    try {
      fn(name);
    } catch (e) {}
  }
}

export function enabled(key) {
  try {
    const v = world.getDynamicProperty(KEYS[key]);
    return v === undefined ? !DEFAULT_OFF.has(key) : v === true;
  } catch (e) {
    return !DEFAULT_OFF.has(key);
  }
}

export function setEnabled(key, value) {
  world.setDynamicProperty(KEYS[key], !!value);
  changed(key);
}

export function num(name) {
  const n = NUMS[name];
  try {
    const v = world.getDynamicProperty(`succubi:num_${name}`);
    return typeof v === "number" && isFinite(v) ? Math.min(n.max, Math.max(n.min, v)) : n.def;
  } catch (e) {
    return n.def;
  }
}

export function setNum(name, value) {
  const n = NUMS[name];
  const v = Math.min(n.max, Math.max(n.min, Number(value)));
  if (!isFinite(v)) return;
  world.setDynamicProperty(`succubi:num_${name}`, v);
  changed(name);
}

export function resetNums() {
  for (const name of Object.keys(NUMS)) world.setDynamicProperty(`succubi:num_${name}`, undefined);
  for (const key of ["height_hp", "height_speed", "height_damage"]) world.setDynamicProperty(KEYS[key], undefined);
  changed("*");
}

// Admins: creative mode or the tag "succubi_admin" (/tag <name> add succubi_admin)
export function isAdmin(player) {
  try {
    if (player.hasTag("succubi_admin")) return true;
    return String(player.getGameMode?.()).toLowerCase() === "creative";
  } catch (e) {
    return false;
  }
}
