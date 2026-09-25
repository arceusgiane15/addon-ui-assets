import { system } from "@minecraft/server";
import { CONFIG } from "./config.js";
import { hpFor, speedPercent, hungerPercent, damageFor, fallFor, hurtFor, heightPoints } from "./body.js";
import { enabled, isAdmin, num } from "../succubi/settings_store.js";

// Body size comes from player.json: each kotarus:set_h_XXX event adds a component group holding
// minecraft:scale (XXX / 180) and the matching collision box (10 cm steps). Entity scale covers the whole model,
// so gun animations that override bones can no longer undo it like the old playanimation scaling did.
// Walking speed (succubi:spdp_XXX, % of normal), food exhaustion (succubi:hun_XXX, %) and max HP
// (succubi:hp_XXX) are group families of their own, so no potion effects are used.
const appliedHitbox = new Map();
const appliedSpeed = new Map();
const appliedHunger = new Map();
const appliedHp = new Map();
const pendingHp = new Map(); // player id -> HP being put back after an HP group change
let hitboxAvailable = CONFIG.applyHitbox;
let hpGroupsAvailable = true;

const pad3 = (n) => String(n).padStart(3, "0");

export function clampCm(value) {
  const cm = Math.round(Number(value));
  if (!isFinite(cm)) return CONFIG.baseCm;
  return Math.min(CONFIG.maxCm, Math.max(CONFIG.minCm, cm));
}

// the standard height (settings), where HP / speed / strength are normal - new players start here
export const standardCm = () => heightPoints().std;

export function getHeightCm(player) {
  const stored = player.getDynamicProperty(CONFIG.propHeight);
  return typeof stored === "number" ? clampCm(stored) : standardCm();
}

export function cmToScale(cm) {
  return cm / CONFIG.baseCm;
}

// Max HP for a height (settings: HP at the shortest / standard / tallest height; all the same with the switch off)
export function calculateMaxHp(cm) {
  return hpFor(cm);
}

// What the body does at this height (1 = normal)
export function bodyStats(cm) {
  return {
    hp: hpFor(cm),
    speed: speedPercent(cm) / 100,
    damage: damageFor(cm),
    fall: fallFor(cm),
    hunger: hungerPercent(cm) / 100,
    hurt: hurtFor(cm)
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
  return "kotarus:set_h_" + pad3(hitboxStepFor(cm));
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

// speed and hunger groups are only re-sent when they change
// (re-adding the speed group while running could make the stride hitch)
function applyGroup(map, player, value, eventPrefix, force) {
  if (!force && map.get(player.id) === value) return;
  try {
    player.triggerEvent(eventPrefix + pad3(value));
    map.set(player.id, value);
  } catch (e) {}
}

// Max HP lives in the succubi:hp_XXX groups: the game's own healing (natural regeneration, the regeneration
// effect, golden apples) then stops at the right max. Adding a health group fills health up to the new max,
// so the HP the player had is put back straight after (never above the new max).
function applyHpGroup(player, hp, force) {
  if (!hpGroupsAvailable) return;
  if (!force && appliedHp.get(player.id) === hp) return;
  let before;
  try {
    before = player.getComponent("minecraft:health")?.currentValue;
  } catch (e) {}
  if (!(before > 0)) return; // dead: the respawn applies it
  try {
    player.triggerEvent("succubi:set_hp_" + pad3(hp));
  } catch (e) {
    hpGroupsAvailable = false; // player.json without HP groups: the script cap below still works
    return;
  }
  appliedHp.set(player.id, hp);
  const keep = Math.min(before, hp);
  if (keep >= hp) return;
  pendingHp.set(player.id, keep);
  // the group may be added now or at the end of the tick: put the HP back once it has been filled up
  const putBack = () => {
    try {
      if (!player.isValid()) return;
      const health = player.getComponent("minecraft:health");
      if (health && health.currentValue > 0 && health.currentValue >= hp - 0.01) health.setCurrentValue(keep);
    } catch (e) {}
  };
  putBack();
  system.runTimeout(putBack, 1);
  system.runTimeout(() => {
    putBack();
    pendingHp.delete(player.id);
  }, 3);
}

// HP to show while an HP group change is being settled (the HUD must not flash a full bar for a tick)
export function shownHp(player, current) {
  const keep = pendingHp.get(player.id);
  return keep === undefined ? current : Math.min(current, keep);
}

function syncHeightTag(player, cm) {
  const wanted = CONFIG.heightTagPrefix + pad3(hitboxStepFor(cm));
  try {
    for (const tag of player.getTags()) {
      if (tag.startsWith(CONFIG.heightTagPrefix) && tag !== wanted) player.removeTag(tag);
    }
    player.addTag(wanted);
  } catch (e) {}
}

export function applyHpScaling(player, cm, force = false) {
  const targetMaxHp = calculateMaxHp(cm);
  try {
    player.setDynamicProperty(CONFIG.propMaxHp, targetMaxHp);
    applyHpGroup(player, targetMaxHp, force);
    const healthComp = player.getComponent("minecraft:health");
    if (healthComp && healthComp.currentValue > targetMaxHp) healthComp.setCurrentValue(targetMaxHp);
  } catch (e) {}
  return targetMaxHp;
}

// periodic = the 2-second re-check: body size is re-sent as before, speed / hunger only when they changed.
// hpForce = re-add the HP group even if it looks applied (join / respawn)
export function applyHeight(player, force, periodic = false, hpForce = false) {
  const cm = getHeightCm(player);
  const again = force === true && !periodic;
  applyBody(player, cm, force === true);
  applyGroup(appliedSpeed, player, speedPercent(cm), "succubi:set_spdp_", again);
  applyGroup(appliedHunger, player, hungerPercent(cm), "succubi:set_hun_", again);
  syncHeightTag(player, cm);
  applyHpScaling(player, cm, hpForce);
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

// keepFight: a dimension change is not a reason to forget the last fight; keepHp: nor the applied HP group
export function forget(playerId, keepFight = false, keepHp = false) {
  appliedHitbox.delete(playerId);
  appliedSpeed.delete(playerId);
  appliedHunger.delete(playerId);
  if (!keepHp) {
    appliedHp.delete(playerId);
    pendingHp.delete(playerId);
  }
  if (!keepFight) lastFight.delete(playerId);
}

// ---------------------------------------------------------------- fair-play rules
// Admins (creative / tag succubi_admin) and the "ส่วนสูงอิสระ" world switch keep the old free 1-500 cm.
const lastFight = new Map(); // player id -> Date.now() of the last hit taken or dealt

export const isFree = (player) => enabled("height_free") || isAdmin(player);

export function limitsFor(player) {
  if (isFree(player)) return [CONFIG.minCm, CONFIG.maxCm];
  const { lo, hi } = heightPoints();
  return [lo, hi];
}

export function clampFor(player, cm) {
  const [lo, hi] = limitsFor(player);
  return Math.min(hi, Math.max(lo, clampCm(cm)));
}

export function markFight(player) {
  if (player?.typeId === "minecraft:player") lastFight.set(player.id, Date.now());
}

export const cooldownMinutes = () => num("h_cooldown");

// Seconds the player still has to wait before a change, and why (0 = may change now)
export function lockFor(player) {
  if (isFree(player)) return { seconds: 0, reason: "" };
  const fight = num("h_fight_lock") * 1000 - (Date.now() - (lastFight.get(player.id) ?? 0));
  if (fight > 0) return { seconds: Math.ceil(fight / 1000), reason: "fight" };
  const next = Number(player.getDynamicProperty(CONFIG.propNextChange)) || 0;
  const wait = Math.min(next - Date.now(), cooldownMinutes() * 60000); // a shorter setting also shortens a running wait
  if (wait > 0) return { seconds: Math.ceil(wait / 1000), reason: "cooldown" };
  return { seconds: 0, reason: "" };
}

export function startCooldown(player) {
  if (isFree(player)) return;
  try {
    player.setDynamicProperty(CONFIG.propNextChange, Date.now() + cooldownMinutes() * 60000);
  } catch (e) {}
}

// Heights saved before the rules (or under wider settings) are pulled back into the allowed range
export function enforceLimits(player) {
  const cm = getHeightCm(player);
  const ok = clampFor(player, cm);
  if (ok !== cm) {
    const [lo, hi] = limitsFor(player);
    setHeightCm(player, ok);
    player.sendMessage(`§e[ส่วนสูง] ปรับเป็น ${ok} ซม. ให้อยู่ในช่วงที่เซิร์ฟอนุญาต (${lo}-${hi} ซม.)`);
  }
}

export function isHitboxAvailable() {
  return hitboxAvailable;
}
