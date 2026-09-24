import { CONFIG } from "./config.js";
import { enabled, isAdmin } from "../succubi/settings_store.js";

// Body size comes from player.json: each kotarus:set_h_XXX event adds a component group holding
// minecraft:scale (XXX / 180) and the matching collision box (10 cm steps). Entity scale covers the whole
// model, so gun animations that override bones can no longer undo it like the old playanimation scaling did.
const appliedHitbox = new Map();
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

// Base 100 HP at 180 cm, +1 HP per cm, clamped 50-200 HP
export function calculateMaxHp(cm) {
  const targetHp = CONFIG.baseHp + (cm - CONFIG.baseCm) * CONFIG.hpPerCm;
  return Math.min(CONFIG.maxHp, Math.max(CONFIG.minHp, Math.round(targetHp)));
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

export function applyHeight(player, force) {
  const cm = getHeightCm(player);
  applyBody(player, cm, force === true);
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
