import { world, system } from "@minecraft/server";
import { enabled } from "./settings_store.js";
import { getThirst, thirstMax } from "./thirst.js";
import { getSanity, SANITY_MAX } from "./sanity.js";
import { readFood } from "./regen.js";

// Pressure sounds (RP sounds/succubi, made by tools/v20/sfx.py), heard only by the player they are about:
//  health <= 50 %  heartbeat, faster and a little louder the closer to death (same tempo as the red screen edges)
//  food   <= 30 %  stomach growls (more often at 15 %)
//  water  <= 30 %  short panting (more often at 15 %)
//  sanity <= 50 %  whispers; <= 30 % also cave noises; <= 15 % ringing in the ears
// Off for everyone: settings item -> สถานะและ HUD. Off for one player: wallet -> ตั้งค่า -> เสียงกดดัน (tag no_pressure_sfx).
const TICKS = 2;
const RED_START = 15; // health steps (of 20), as in the RP's red edges

export const heartBpm = (step) => 72 + (78 * (RED_START - Math.max(1, step))) / (RED_START - 1);
const rand = (a, b) => a + Math.random() * (b - a);
const next = new Map(); // `${player id}:${sound}` -> tick it may play again

function survival(p) {
  try {
    const m = String(p.getGameMode?.()).toLowerCase();
    return m !== "creative" && m !== "spectator";
  } catch (e) {
    return true;
  }
}

function due(player, key, now, waitTicks) {
  const k = `${player.id}:${key}`;
  if ((next.get(k) ?? 0) > now) return false;
  next.set(k, now + Math.max(1, Math.round(waitTicks)));
  return true;
}

function play(player, id, volume, pitch = 1) {
  try {
    player.playSound(id, { volume, pitch });
  } catch (e) {}
}

// what should play for this player right now (exported for the tests)
export function pressureFor(player, now) {
  const out = [];
  const health = player.getComponent("minecraft:health");
  const maxHp = Number(player.getDynamicProperty("kotarus:max_hp")) || 100;
  const hp = health?.currentValue ?? maxHp;
  if (!(hp > 0)) return out;
  const hpRatio = hp / maxHp;
  if (hpRatio <= 0.5) {
    const step = Math.max(1, Math.round(hpRatio * 20));
    const k = (10 - Math.min(10, step)) / 9; // 0 at 50 %, 1 near death
    if (due(player, "heart", now, (20 * 60) / heartBpm(step))) out.push(["succubi.heartbeat", 0.45 + 0.4 * k, 1 + 0.08 * k]);
  }
  const food = readFood(player);
  if (food <= 6 && due(player, "stomach", now, 20 * (food <= 3 ? rand(9, 16) : rand(18, 32)))) out.push(["succubi.stomach", food <= 3 ? 0.9 : 0.6, rand(0.9, 1.1)]);
  if (enabled("thirst")) {
    const t = getThirst(player) / thirstMax();
    if (t <= 0.3 && due(player, "pant", now, 20 * (t <= 0.15 ? rand(8, 14) : rand(16, 28)))) out.push(["succubi.pant", t <= 0.15 ? 1.0 : 0.75, rand(0.95, 1.08)]);
  }
  if (enabled("sanity")) {
    const s = getSanity(player) / SANITY_MAX;
    if (s <= 0.5) {
      const wait = s <= 0.15 ? rand(7, 14) : s <= 0.3 ? rand(14, 26) : rand(28, 50);
      if (due(player, "whisper", now, 20 * wait)) out.push(Math.random() < (s <= 0.3 ? 0.3 : 0) ? ["ambient.cave", 0.8, rand(0.7, 1)] : ["succubi.whisper", s <= 0.15 ? 0.95 : s <= 0.3 ? 0.75 : 0.55, rand(0.85, 1.05)]);
    }
    if (s <= 0.15 && due(player, "ring", now, 20 * rand(20, 40))) out.push(["succubi.tinnitus", 0.6, 1]);
  }
  return out;
}

export function initPressure() {
  world.afterEvents.playerLeave.subscribe((e) => {
    for (const k of [...next.keys()]) if (k.startsWith(`${e.playerId}:`)) next.delete(k);
  });
  system.runInterval(() => {
    if (!enabled("pressure")) return;
    const now = system.currentTick;
    for (const p of world.getAllPlayers()) {
      try {
        if (!survival(p) || p.hasTag("no_pressure_sfx")) continue;
        for (const [id, volume, pitch] of pressureFor(p, now)) play(p, id, volume, pitch);
      } catch (e) {}
    }
  }, TICKS);
}
