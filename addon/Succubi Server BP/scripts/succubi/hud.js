import { world, system, EquipmentSlot } from "@minecraft/server";
import { getThirst, thirstMax } from "./thirst.js";
import { getSanity, SANITY_MAX } from "./sanity.js";
import { enabled } from "./settings_store.js";
import { ARMOR_POINTS } from "./armor_values.js";
import { shownHp } from "../height/height.js";
import { clockTokens } from "./daytime.js";

// The HUD is drawn by RP ui/succubi_hud.json (four round gauges). Its data travels in the title, which the RP
// never displays and keeps (preserves) after the title fades, so a value is only sent when it changes:
//   shud:H13F18T09S20Pn X0Y8Z6 Of0Mf9Kf0 Ot0Mt4Kt5 Os1Ms0Ks0 An Lt Dh If It Is G15 Er     (spaces only here for reading)
//   H/F/T/S = health / food / thirst / sanity ring, 00-20 (Txx / Sxx = that system is switched off)
//   P = health colour (n normal, p poison, w wither)   X Y Z = health number digits (HP)
//   O M K + f/t/s = food / thirst / sanity number digits in % (hundreds, tens, ones)
//   A = armor (n none, y shown with digits B C)
//   Lx = low (slow pulse)   Dx = just lost some (red flash, icon shakes)   Ux = just gained (glow, icon pops)
//   Ix = neither (icon at rest)
//   Tokens are letters and digits only, and the UI checks one token per condition (the game misread
//   longer 'and' chains: the health number stuck at 88, the heart stayed wither-grey)
//   G = the health ring before the hit (pale damage trail)       x = h f t s
//   Vxn = icon stage n (4 full .. 0 almost gone): cracked heart, eaten drumstick, drying drop, warping brain
//   Er regeneration sparkles, Ea absorption halo, Ef burning, Qh hunger effect
//   Wn = the admins turned the gauge numbers off (settings item -> สถานะและ HUD)
//   whole screen (RP): sanity below 65 % lays a grey filter over the screen step by step; health at 75 % and
//   below keeps the edges red, deeper at every step (from H); Nx = this player turned the screen effects off
//   Rg1..Rg4 = TV static tier from sanity (below 70 / 50 / 30 / 15 %)
//   Jxn = Don't Starve arrows over gauge x: n 1-3 = rising (that many arrows), 4-6 = falling (n - 3 arrows)
//   Rk.. Rn.. R5..R8.. = the day clock and the day number (see daytime.js)
//   "shud:off" hides the HUD (tag hide_hud, creative, spectator)
// Map makers who show their own /title can pause the HUD: /scriptevent succubi:hud_pause 10
const MARKER = "shud:";
const FOOD_OBJECTIVE = "succubi_food"; // written by the "Succubi Server Link BP" pack
const UPDATE_TICKS = 5;
const FLASH_TICKS = 30; // how long a gain / loss flash stays on screen
const SAFETY_RESEND_TICKS = 1200; // once a minute, in case the client rebuilt its HUD
const pad2 = (n) => String(n).padStart(2, "0");

const lastSent = new Map(); // player id -> { payload, tick }
const rateMemory = new Map(); // player id -> { last: {h, f, t, s}, samples: {h: [[tick, change]...], ...} }
const pausedUntil = new Map(); // player id (or "*") -> tick

export function toSteps(value, max) {
  if (!(max > 0) || !(value > 0)) return 0;
  return Math.max(1, Math.min(20, Math.round((value / max) * 20)));
}

function readFood(player) {
  try {
    const score = world.scoreboard.getObjective(FOOD_OBJECTIVE)?.getScore(player);
    if (typeof score === "number") return Math.max(0, Math.min(20, Math.round(score)));
  } catch (e) {}
  return 20; // link pack not running: show full instead of a false alarm
}

function getMaxHp(player) {
  const stored = Number(player.getDynamicProperty("kotarus:max_hp"));
  return stored > 0 ? stored : 100;
}

// The height system sets max HP (50-200); natural regen must not push health above it
function capHealth(player, maxHp) {
  const health = player.getComponent("minecraft:health");
  if (!health) return maxHp;
  if (health.currentValue > maxHp) health.setCurrentValue(maxHp);
  return Math.min(health.currentValue, maxHp);
}

function armorPoints(player) {
  let total = 0;
  try {
    const eq = player.getComponent("minecraft:equippable");
    for (const slot of [EquipmentSlot.Head, EquipmentSlot.Chest, EquipmentSlot.Legs, EquipmentSlot.Feet]) {
      const id = eq?.getEquipment(slot)?.typeId;
      if (id) total += ARMOR_POINTS[id] ?? 0;
    }
  } catch (e) {}
  return Math.min(99, total);
}

function healthTint(player) {
  try {
    if (player.getEffect("wither")) return "w";
    if (player.getEffect("poison") || player.getEffect("fatal_poison")) return "p";
  } catch (e) {}
  return "n";
}

function effectTokens(player) {
  let s = "";
  try {
    if (player.getEffect("regeneration")) s += "Er";
    if (player.getEffect("absorption")) s += "Ea";
    if (player.getEffect("hunger")) s += "Qh";
  } catch (e) {}
  try {
    if (player.getComponent("minecraft:onfire")) s += "Ef";
  } catch (e) {}
  return s;
}

// ---------------------------------------------------------------- change flashes
// Only noticeable jumps flash (a hit, a meal, a drink, a scare) - not the slow drain of thirst or sanity.
const RULES = {
  h: { loss: 0.5, gain: 2 },
  f: { loss: 2, gain: 0.5 },
  t: { loss: 1.5, gain: 0.5 },
  s: { loss: 2.5, gain: 2.5 }
};
const memory = new Map(); // player id -> { last: {h, f, t, s}, until: {"Uh": tick, ...}, trail, trailUntil }

function flashes(player, values, hpStep, tick) {
  let m = memory.get(player.id);
  if (!m) {
    m = { last: { ...values }, until: {}, trail: 0, trailUntil: 0 };
    memory.set(player.id, m);
  }
  for (const k of Object.keys(RULES)) {
    const now = values[k];
    const before = m.last[k];
    if (typeof now !== "number" || typeof before !== "number") continue;
    if (before - now >= RULES[k].loss) {
      m.until["D" + k] = tick + FLASH_TICKS;
      delete m.until["U" + k];
      if (k === "h") {
        // the trail shows the ring as it was before this run of hits
        const beforeStep = toSteps(before, values.hmax);
        m.trail = m.trailUntil > tick ? Math.max(m.trail, beforeStep) : beforeStep;
        m.trailUntil = tick + FLASH_TICKS;
      }
    } else if (now - before >= RULES[k].gain) {
      m.until["U" + k] = tick + FLASH_TICKS;
      delete m.until["D" + k];
    }
    m.last[k] = now;
  }
  let s = "";
  for (const [flag, until] of Object.entries(m.until)) {
    if (until > tick) s += flag;
    else delete m.until[flag];
  }
  for (const k of Object.keys(RULES)) {
    if (!m.until["D" + k] && !m.until["U" + k]) s += "I" + k; // at rest: the icon's own idle motion
  }
  if (m.trailUntil > tick && m.trail > hpStep) s += `G${pad2(m.trail)}`;
  return s;
}

// ---------------------------------------------------------------- Don't Starve rate arrows
// Changes are measured as a share of the gauge's max. A single step bigger than "jump" is a meal, a drink or a
// hit (the flashes above show those), not a rate. The rest is summed over "window" seconds and turned into
// % of max per minute; steps = how fast for 1 / 2 / 3 arrows. Thirst always drains a little (7.5 %/min by
// default), so its first arrow starts above that.
export const RATE = {
  h: { window: 4, jump: 0.025, steps: [3, 12, 40] },
  f: { window: 60, jump: 0.11, steps: [6, 20, 50] },
  t: { window: 6, jump: 0.04, steps: [12, 25, 50] },
  s: { window: 5, jump: 0.02, steps: [1.5, 10, 30] }
};

// samples: [[tick, change]] -> 0 (steady), 1-3 rising, 4-6 falling
export function rateCode(samples, now, cfg) {
  let sum = 0;
  for (const [t, d] of samples) if (now - t <= cfg.window * 20) sum += d;
  const perMinute = (sum * 100 * 60) / cfg.window;
  const size = Math.abs(perMinute);
  const level = size >= cfg.steps[2] ? 3 : size >= cfg.steps[1] ? 2 : size >= cfg.steps[0] ? 1 : 0;
  if (!level) return 0;
  return perMinute > 0 ? level : level + 3;
}

function rateTokens(player, shares, tick) {
  let m = rateMemory.get(player.id);
  if (!m) {
    m = { last: { ...shares }, samples: { h: [], f: [], t: [], s: [] } };
    rateMemory.set(player.id, m);
  }
  let out = "";
  for (const k of Object.keys(RATE)) {
    const now = shares[k];
    const list = m.samples[k];
    if (typeof now !== "number" || !isFinite(now)) {
      list.length = 0;
      continue;
    }
    const before = m.last[k];
    m.last[k] = now;
    if (typeof before === "number" && isFinite(before)) {
      const d = now - before;
      if (d !== 0 && Math.abs(d) < RATE[k].jump) list.push([tick, d]);
    }
    while (list.length && tick - list[0][0] > RATE[k].window * 20) list.shift();
    const code = rateCode(list, tick, RATE[k]);
    if (code) out += `J${k}${code}`;
  }
  return out;
}

// TV static tier from sanity in % (0 = clean screen)
export function staticTier(sanityPercent) {
  if (sanityPercent < 15) return 4;
  if (sanityPercent < 30) return 3;
  if (sanityPercent < 50) return 2;
  if (sanityPercent < 70) return 1;
  return 0;
}

// the faint number under a gauge: O M K = hundreds, tens, ones of the value in %
export function percentDigits(letter, value, max) {
  const p = max > 0 && value > 0 ? Math.max(0, Math.min(100, Math.round((value / max) * 100))) : 0;
  return `O${letter}${Math.floor(p / 100)}M${letter}${Math.floor(p / 10) % 10}K${letter}${p % 10}`;
}

// 4 full, 3 >= 50 %, 2 >= 30 %, 1 >= 15 %, 0 below (sanity fog starts at 50 / 30 / 15 too)
export function stage(ratio) {
  if (!(ratio > 0)) return 0;
  return ratio >= 0.75 ? 4 : ratio >= 0.5 ? 3 : ratio >= 0.3 ? 2 : ratio >= 0.15 ? 1 : 0;
}

export function buildPayload(player, tick = system.currentTick) {
  const maxHp = getMaxHp(player);
  const hp = shownHp(player, capHealth(player, maxHp));
  const hpNum = Math.max(0, Math.min(999, Math.ceil(hp)));
  const food = readFood(player);
  const thirstOn = enabled("thirst");
  const sanityOn = enabled("sanity");
  const thirstRaw = thirstOn ? getThirst(player) : undefined;
  const sanityRaw = sanityOn ? getSanity(player) : undefined;
  const thirst = thirstOn ? toSteps(thirstRaw, thirstMax()) : 0;
  const sanity = sanityOn ? toSteps(sanityRaw, SANITY_MAX) : 0;
  const hpStep = toSteps(hp, maxHp);
  const armor = armorPoints(player);
  let s = MARKER;
  s += `H${pad2(hpStep)}F${pad2(food)}`;
  s += thirstOn ? `T${pad2(thirst)}` : "Txx";
  s += sanityOn ? `S${pad2(sanity)}` : "Sxx";
  s += `P${healthTint(player)}`;
  s += `X${Math.floor(hpNum / 100)}Y${Math.floor(hpNum / 10) % 10}Z${hpNum % 10}`;
  s += percentDigits("f", food, 20);
  if (thirstOn) s += percentDigits("t", thirstRaw, thirstMax());
  if (sanityOn) s += percentDigits("s", sanityRaw, SANITY_MAX);
  s += armor > 0 ? `AyB${Math.floor(armor / 10)}C${armor % 10}` : "An";
  // icon stage (Don't Starve style: the heart cracks, the drumstick gets eaten, the drop dries, the brain warps)
  s += `Vh${stage(hp / maxHp)}Vf${stage(food / 20)}`;
  if (thirstOn) s += `Vt${stage(thirstRaw / thirstMax())}`;
  if (sanityOn) s += `Vs${stage(sanityRaw / SANITY_MAX)}`;
  if (hp <= maxHp * 0.25) s += "Lh";
  if (food <= 6) s += "Lf";
  if (thirstOn && thirst <= 6) s += "Lt";
  if (sanityOn && sanity <= 6) s += "Ls";
  s += flashes(player, { h: hp, hmax: maxHp, f: food, t: thirstRaw, s: sanityRaw }, hpStep, tick);
  if (player.hasTag("no_screen_fx")) s += "Nx";
  if (!enabled("hud_numbers")) s += "Wn"; // player turned the red aura / grey screen off
  if (sanityOn) {
    const tier = staticTier((sanityRaw / SANITY_MAX) * 100);
    if (tier) s += `Rg${tier}`;
  }
  if (enabled("hud_arrows")) {
    s += rateTokens(player, {
      h: maxHp > 0 ? hp / maxHp : undefined,
      f: food / 20,
      t: thirstOn ? thirstRaw / thirstMax() : undefined,
      s: sanityOn ? sanityRaw / SANITY_MAX : undefined
    }, tick);
  }
  s += clockTokens();
  s += effectTokens(player);
  return s;
}

// Creative / spectator players don't need survival stats on screen
function hiddenMode(player) {
  try {
    const mode = String(player.getGameMode?.()).toLowerCase();
    return mode === "creative" || mode === "spectator";
  } catch (e) {
    return false;
  }
}

function paused(player, tick) {
  return (pausedUntil.get(player.id) ?? 0) > tick || (pausedUntil.get("*") ?? 0) > tick;
}

export function updateHud(player, tick, force = false) {
  if (paused(player, tick)) return;
  const previous = lastSent.get(player.id);
  let payload;
  if (player.hasTag("hide_hud") || hiddenMode(player)) {
    capHealth(player, getMaxHp(player));
    payload = MARKER + "off";
  } else {
    payload = buildPayload(player, tick);
  }
  if (!force && previous && previous.payload === payload && tick - previous.tick < SAFETY_RESEND_TICKS) return;
  player.onScreenDisplay.setTitle(payload, { fadeInDuration: 0, stayDuration: 10, fadeOutDuration: 0 });
  lastSent.set(player.id, { payload, tick });
}

// Send the current values right away (after a HUD toggle, respawn, dimension change ...)
export function refreshHud(player) {
  system.runTimeout(() => {
    try {
      updateHud(player, system.currentTick, true);
    } catch (e) {}
  }, 2);
}

export function initHud() {
  world.afterEvents.playerLeave.subscribe((event) => {
    lastSent.delete(event.playerId);
    pausedUntil.delete(event.playerId);
    memory.delete(event.playerId);
    rateMemory.delete(event.playerId);
  });
  world.afterEvents.playerSpawn.subscribe((event) => {
    if (event.player) rateMemory.delete(event.player.id); // a respawn is not a rate
    if (event.player) system.runTimeout(() => refreshHud(event.player), 20);
  });
  try {
    world.afterEvents.playerDimensionChange.subscribe((event) => {
      if (event.player) system.runTimeout(() => refreshHud(event.player), 20);
    });
  } catch (e) {}
  // /scriptevent succubi:hud_pause <seconds>  (from a player: that player only, from a command block: everyone)
  system.afterEvents.scriptEventReceive.subscribe((event) => {
    if (event.id !== "succubi:hud_pause") return;
    const seconds = Math.max(1, Math.min(600, Number(event.message) || 10));
    const until = system.currentTick + seconds * 20;
    const src = event.sourceEntity;
    pausedUntil.set(src?.typeId === "minecraft:player" ? src.id : "*", until);
  });
  system.runInterval(() => {
    const tick = system.currentTick;
    for (const player of world.getAllPlayers()) {
      try {
        const wasPaused = lastSent.get(player.id)?.paused;
        if (paused(player, tick)) {
          lastSent.set(player.id, { payload: "", tick, paused: true });
          continue;
        }
        updateHud(player, tick, !!wasPaused);
      } catch (e) {}
    }
  }, UPDATE_TICKS);
}
