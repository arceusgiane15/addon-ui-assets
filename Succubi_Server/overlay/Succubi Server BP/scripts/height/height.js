import { CONFIG } from "./config.js";
import { hpFor, speedFor, damageFor } from "./body.js";
import { enabled, isAdmin, num } from "../succubi/settings_store.js";

// Body size comes from player.json: each kotarus:set_h_XXX event adds a component group holding
// minecraft:scale (XXX / 180), the matching collision box and the walking speed for that height (10 cm steps).
// Entity scale covers the whole model, so gun animations that override bones can no longer undo it like the old
// playanimation scaling did. Speed lives in the same group, so no potion effect is used for it.
const appliedHitbox = new Map();
const appliedSpeed = new Map();
let hitboxAvailable = CONFIG.applyHitbox;

export function clampCm(value) {
  const cm = Math.round(Number(value));
  if (!isFinite(cm)) return CONFIG.baseCm;
  return Math.min(CONFIG.maxCm, Math.max(CONFIG.minCm, cm));
}

export function getHeightCm(player) {
  const stored = player.getDynamicProperty(CONFIG.propHeight);
  return typeof stored === "number" ? clampCm(stored) : CONFIG.baseCm;
}

export function cmToScale(cm) {
  return cm / CONFIG.baseCm;
}

// Base HP (setting, 100) at 180 cm, doubling every 40 cm taller and halving every 40 cm shorter (50-200 by default).
// With "height changes HP" off everyone has the base HP.
export function calculateMaxHp(cm) {
  const base = num("hp_base");
  return enabled("height_hp") ? hpFor(cm, base) : Math.min(200, base);
}

// the speed group that fits this height (player.json succubi:spd_140 ... spd_220, 180 = normal speed)
export function speedStepFor(cm) {
  if (!enabled("height_speed")) return 180;
  return Math.min(220, Math.max(140, hitboxStepFor(cm)));
}

// What the body does at this height (speed follows the 10 cm step the player.json group uses)
export function bodyStats(cm) {
  const step = hitboxStepFor(cm);
  return {
    hp: calculateMaxHp(cm),
    speed: enabled("height_speed") ? speedFor(speedStepFor(cm)) : 1,
    damage: enabled("height_damage") ? damageFor(step) : 1
  };
}

// "+15 %" / "-23 %" / "ปกติ"
export function percentText(factor) {
  const p = Math.round((factor - 1) * 100);
  return p === 0 ? "ปกติ" : `${p > 0 ? "+" : ""}${p}%`;
}

export function hitboxStepFor(cm) {
  const step = CONFIG.hitboxStepCm;
  return Math.min(CONFIG.maxCm, Math.max(step, Math.round(cm / step) * step));
}

function eventFor(cm) {
  return "kotarus:set_h_" + String(hitboxStepFor(cm)).padStart(3, "0");
}

function applyBody(player, cm, force) {
  if (!hitboxAvailable) return;
  const step = hitboxStepFor(cm);
  if (!force && appliedHitbox.get(player.id) === step) return;
  try {
    player.triggerEvent(eventFor(cm));
    appliedHitbox.set(player.id, step);
  } catch (e) {
    hitboxAvailable = false;
    appliedHitbox.clear();
  }
}

// walking speed lives in its own group family so it can be switched off without touching body size
function applySpeed(player, cm, force) {
  const step = speedStepFor(cm);
  if (!force && appliedSpeed.get(player.id) === step) return;
  try {
    player.triggerEvent("succubi:set_spd_" + String(step).padStart(3, "0"));
    appliedSpeed.set(player.id, step);
  } catch (e) {}
}

function syncHeightTag(player, cm) {
  const wanted = CONFIG.heightTagPrefix + String(hitboxStepFor(cm)).padStart(3, "0");
  try {
    for (const tag of player.getTags()) {
      if (tag.startsWith(CONFIG.heightTagPrefix) && tag !== wanted) player.removeTag(tag);
    }
    player.addTag(wanted);
  } catch (e) {}
}

export function applyHpScaling(player, cm) {
  const targetMaxHp = calculateMaxHp(cm);
  try {
    player.setDynamicProperty(CONFIG.propMaxHp, targetMaxHp);
    const healthComp = player.getComponent("minecraft:health");
    if (healthComp && healthComp.currentValue > targetMaxHp) healthComp.setCurrentValue(targetMaxHp);
  } catch (e) {}
  return targetMaxHp;
}

// periodic = the 2-second re-check: body size is re-sent as before, speed only when it changed
// (re-adding the speed group while running could make the stride hitch)
export function applyHeight(player, force, periodic = false) {
  const cm = getHeightCm(player);
  applyBody(player, cm, force === true);
  applySpeed(player, cm, force === true && !periodic);
  syncHeightTag(player, cm);
  applyHpScaling(player, cm);
  return cm;
}

export function setHeightCm(player, value) {
  const cm = clampCm(value);
  try {
    player.setDynamicProperty(CONFIG.propHeight, cm);
  } catch (e) {}
  applyHeight(player, true);
  return cm;
}

export function forget(playerId, keepFight = false) {
  appliedHitbox.delete(playerId);
  appliedSpeed.delete(playerId);
  if (!keepFight) lastFight.delete(playerId);
}

// ---------------------------------------------------------------- fair-play rules
// Admins (creative / tag succubi_admin) and the "ส่วนสูงอิสระ" world switch keep the old free 1-500 cm.
const lastFight = new Map(); // player id -> Date.now() of the last hit taken or dealt

export const isFree = (player) => enabled("height_free") || isAdmin(player);

export function limitsFor(player) {
  return isFree(player) ? [CONFIG.minCm, CONFIG.maxCm] : [CONFIG.playerMinCm, CONFIG.playerMaxCm];
}

export function clampFor(player, cm) {
  const [lo, hi] = limitsFor(player);
  return Math.min(hi, Math.max(lo, clampCm(cm)));
}

export function markFight(player) {
  if (player?.typeId === "minecraft:player") lastFight.set(player.id, Date.now());
}

// Seconds the player still has to wait before a change, and why (0 = may change now)
export function lockFor(player) {
  if (isFree(player)) return { seconds: 0, reason: "" };
  const fight = CONFIG.combatLockSeconds * 1000 - (Date.now() - (lastFight.get(player.id) ?? 0));
  if (fight > 0) return { seconds: Math.ceil(fight / 1000), reason: "fight" };
  const next = Number(player.getDynamicProperty(CONFIG.propNextChange)) || 0;
  const wait = next - Date.now();
  if (wait > 0) return { seconds: Math.ceil(wait / 1000), reason: "cooldown" };
  return { seconds: 0, reason: "" };
}

export function startCooldown(player) {
  if (isFree(player)) return;
  try {
    player.setDynamicProperty(CONFIG.propNextChange, Date.now() + CONFIG.cooldownSeconds * 1000);
  } catch (e) {}
}

// Heights saved before the rules existed are pulled back into the allowed range
export function enforceLimits(player) {
  const cm = getHeightCm(player);
  const ok = clampFor(player, cm);
  if (ok !== cm) {
    setHeightCm(player, ok);
    player.sendMessage(`§e[ส่วนสูง] ปรับเป็น ${ok} ซม. ให้อยู่ในช่วงที่เซิร์ฟอนุญาต (${CONFIG.playerMinCm}-${CONFIG.playerMaxCm} ซม.)`);
  }
}

export function isHitboxAvailable() {
  return hitboxAvailable;
}
