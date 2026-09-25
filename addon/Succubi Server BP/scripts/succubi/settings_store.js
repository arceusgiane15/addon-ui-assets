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
  height_fall: "succubi:cfg_height_fall", // height changes fall damage taken
  height_hunger: "succubi:cfg_height_hunger", // height changes how fast food and water run out
  height_hurt: "succubi:cfg_height_hurt", // height changes damage taken from hits
  nametag_near: "succubi:cfg_nametag_near", // player names only while looking at them (old "No Nametag" subpack)
  height_free: "succubi:cfg_height_free", // players may pick any height, no cooldown (old behaviour)
  hud_clock: "succubi:cfg_hud_clock", // Don't Starve day clock + day number on the HUD
  hud_arrows: "succubi:cfg_hud_arrows", // Don't Starve rising / falling arrows over the gauges
  time_custom: "succubi:cfg_time_custom", // this pack runs the day at its own speed (num halfday_minutes)
  sanity_world: "succubi:cfg_sanity_world", // night, darkness, flowers, campfires, raw / cooked food move sanity
  shadows_real: "succubi:cfg_shadows_real", // below 15 % sanity shadow creatures come for the player
  tension_music: "succubi:cfg_tension_music" // low health / sanity: the pack's tense music instead of the game's calm music
};
const DEFAULT_OFF = new Set(["nametag_near", "height_free"]);
export const HEIGHT_SWITCHES = ["height_hp", "height_speed", "height_damage", "height_fall", "height_hunger", "height_hurt"];

// Numbers (base stats). 0 in regen_seconds / food_drain_seconds = leave it to the game.
// Height stats are set at three points - the shortest a player may be (h_min), the standard height (h_std) and the
// tallest (h_max) - and run in a straight line between them. Percent values: 100 = no change.
export const NUMS = {
  hp_base: { def: 100, min: 10, max: 400 }, // max HP at the standard height
  hp_short: { def: 50, min: 10, max: 400 }, // max HP at the shortest height
  hp_tall: { def: 200, min: 10, max: 400 }, // max HP at the tallest height
  h_min: { def: 140, min: 10, max: 500 }, // shortest height a player may pick (cm)
  h_std: { def: 180, min: 10, max: 500 }, // standard height: normal HP / speed / strength (cm)
  h_max: { def: 220, min: 10, max: 500 }, // tallest height a player may pick (cm)
  h_cooldown: { def: 5, min: 0, max: 60 }, // minutes between two height changes (reset included)
  h_fight_lock: { def: 15, min: 0, max: 120 }, // seconds after a fight before the height can change
  spd_short: { def: 115, min: 50, max: 150 }, // walking speed % at the shortest height
  spd_tall: { def: 87, min: 50, max: 150 }, // walking speed % at the tallest height
  dmg_short: { def: 77, min: 25, max: 300 }, // melee hit strength %
  dmg_tall: { def: 130, min: 25, max: 300 },
  fall_short: { def: 75, min: 0, max: 300 }, // fall damage taken %
  fall_tall: { def: 125, min: 0, max: 300 },
  hunger_short: { def: 85, min: 50, max: 200 }, // how fast food and water drain %
  hunger_tall: { def: 120, min: 50, max: 200 },
  hurt_short: { def: 110, min: 25, max: 300 }, // damage taken from hits %
  hurt_tall: { def: 90, min: 25, max: 300 },
  halfday_minutes: { def: 60, min: 5, max: 240 }, // real minutes from morning to evening (12 in-game hours; the game's own is 10)
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

// Several numbers / switches at once (presets), one change notice at the end
export function setMany(nums = {}, switches = {}, notice = "*") {
  for (const [name, value] of Object.entries(nums)) {
    const n = NUMS[name];
    const v = Math.min(n.max, Math.max(n.min, Number(value)));
    if (isFinite(v)) world.setDynamicProperty(`succubi:num_${name}`, v);
  }
  for (const [key, value] of Object.entries(switches)) world.setDynamicProperty(KEYS[key], !!value);
  changed(notice);
}

// names = which numbers go back to their defaults (all when left out); switches the same for on/off keys
export function resetNums(names = Object.keys(NUMS), switches = HEIGHT_SWITCHES) {
  for (const name of names) world.setDynamicProperty(`succubi:num_${name}`, undefined);
  for (const key of switches) world.setDynamicProperty(KEYS[key], undefined);
  changed("*");
}

// Height-related settings changed (the height system re-applies HP / speed / hunger groups for everyone)
export const isHeightSetting = (name) =>
  name === "*" || /^(h_|hp_|spd_|dmg_|fall_|hunger_|hurt_|height_)/.test(name);

// Admins: creative mode or the tag "succubi_admin" (/tag <name> add succubi_admin)
export function isAdmin(player) {
  try {
    if (player.hasTag("succubi_admin")) return true;
    return String(player.getGameMode?.()).toLowerCase() === "creative";
  } catch (e) {
    return false;
  }
}
