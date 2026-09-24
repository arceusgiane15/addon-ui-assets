import { world, system, EquipmentSlot } from "@minecraft/server";
import { getThirst, THIRST_MAX } from "./thirst.js";
import { getSanity, SANITY_MAX } from "./sanity.js";
import { enabled } from "./settings_store.js";
import { ARMOR_POINTS } from "./armor_values.js";

// The HUD is drawn by RP ui/succubi_hud.json. Its data travels in the title, which the RP never displays
// and keeps (preserves) after the title fades, so a value is only sent when it changes:
//   shud:H13F18T09S20Pn X0Y8Z6 An !t     (spaces only here for reading)
//   H/F/T/S = health / food / thirst / sanity bar, 00-20 (Txx / Sxx = that system is switched off)
//   P = health colour (n normal, p poison, w wither)   X Y Z = health number digits
//   A = armor (n none, y shown with digits B C)         !h !f !t !s = low, pulses on screen
//   "shud:off" hides the HUD (tag hide_hud, creative, spectator)
// Map makers who show their own /title can pause the HUD: /scriptevent succubi:hud_pause 10
const MARKER = "shud:";
const FOOD_OBJECTIVE = "succubi_food"; // written by the "Succubi Server Link BP" pack
const UPDATE_TICKS = 10;
const SAFETY_RESEND_TICKS = 1200; // once a minute, in case the client rebuilt its HUD
const pad2 = (n) => String(n).padStart(2, "0");

const lastSent = new Map(); // player id -> { payload, tick }
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

export function buildPayload(player) {
  const maxHp = getMaxHp(player);
  const hp = capHealth(player, maxHp);
  const hpNum = Math.max(0, Math.min(999, Math.ceil(hp)));
  const food = readFood(player);
  const thirstOn = enabled("thirst");
  const sanityOn = enabled("sanity");
  const thirst = thirstOn ? toSteps(getThirst(player), THIRST_MAX) : 0;
  const sanity = sanityOn ? toSteps(getSanity(player), SANITY_MAX) : 0;
  const armor = armorPoints(player);
  let s = MARKER;
  s += `H${pad2(toSteps(hp, maxHp))}F${pad2(food)}`;
  s += thirstOn ? `T${pad2(thirst)}` : "Txx";
  s += sanityOn ? `S${pad2(sanity)}` : "Sxx";
  s += `P${healthTint(player)}`;
  s += `X${Math.floor(hpNum / 100)}Y${Math.floor(hpNum / 10) % 10}Z${hpNum % 10}`;
  s += armor > 0 ? `AyB${Math.floor(armor / 10)}C${armor % 10}` : "An";
  if (hp <= maxHp * 0.25) s += "!h";
  if (food <= 6) s += "!f";
  if (thirstOn && thirst <= 6) s += "!t";
  if (sanityOn && sanity <= 6) s += "!s";
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
    payload = buildPayload(player);
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
  });
  world.afterEvents.playerSpawn.subscribe((event) => {
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
