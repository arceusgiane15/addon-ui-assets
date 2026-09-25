import { world, system } from "@minecraft/server";
import { enabled, num, onSettingChange } from "./settings_store.js";

// Day length and the Don't Starve style day clock.
//  - "เวลาแบบกำหนดเอง" (time_custom, on by default): the game's daylight cycle is switched off and this pack moves
//    the time itself, halfday_minutes real minutes from morning to evening (default 60 = 1 real hour; the game's
//    own is 10). The night takes as long. Beds still skip the night (playersSleepingPercentage is respected).
//    Switching it off hands the cycle back to the game (only if this pack was the one that took it).
//  - HUD clock: "Rk00".."Rk47" = hand position (0 = 6:00, clockwise), "Rn1".."Rn4" = how many digits the day
//    number has, "R5/R6/R7/R8" + digit = those digits from the left (RP ui/succubi_hud.json draws them).
//    (digits, not letters: "Rb2" would also read as the armor token "B2" if the UI ever compared case-blind)
export const HALFDAY_CHOICES = [10, 15, 20, 30, 45, 60, 90, 120, 180, 240];
const OWNED = "succubi:daylight_owned";
const STEP_TICKS = 10;
const SLEEP_TICKS = 100; // everyone needed in bed for 5 seconds -> morning
const DAY = 24000;
let carry = 0;
let sleepTicks = 0;

// game time ticks per real tick
export const timeRate = () => 12000 / (num("halfday_minutes") * 60 * 20);

const fmtMinutes = (m) =>
  m % 60 === 0 ? `${m / 60} ชม.` : m > 60 ? `${Math.floor(m / 60)} ชม. ${m % 60} นาที` : `${m} นาที`;

export function timeText() {
  if (!enabled("time_custom")) return "แบบเกมปกติ (เช้าถึงเย็น 10 นาที)";
  const m = num("halfday_minutes");
  return `เช้าถึงเย็น ${fmtMinutes(m)} (1 วันเต็ม ${fmtMinutes(m * 2)})`;
}

// 0 = 6:00, 6000 = noon, 12000 = 18:00, 18000 = midnight
export function phaseOf(tod) {
  const t = ((tod % DAY) + DAY) % DAY;
  if (t < 12000) return "day";
  if (t < 13500) return "dusk";
  if (t < 22500) return "night";
  return "dawn";
}
const PHASE_TH = { day: "กลางวัน", dusk: "พลบค่ำ", night: "กลางคืน", dawn: "ใกล้รุ่ง" };

export function clockTime(tod) {
  const t = ((tod % DAY) + DAY) % DAY;
  const minutes = Math.floor((t / 1000) * 60) + 6 * 60;
  const h = Math.floor(minutes / 60) % 24;
  return `${String(h).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
}

export function dayNumber() {
  try {
    return world.getDay() + 1;
  } catch (e) {
    return 1;
  }
}

function timeOfDay() {
  try {
    return world.getTimeOfDay();
  } catch (e) {
    return 0;
  }
}

export function clockText() {
  const tod = timeOfDay();
  return `วันที่ ${dayNumber()} · ${clockTime(tod)} น. (${PHASE_TH[phaseOf(tod)]})`;
}

// HUD tokens for the clock ("" when the clock is switched off)
export function clockTokens(tod = timeOfDay(), day = dayNumber()) {
  if (!enabled("hud_clock")) return "";
  const t = ((tod % DAY) + DAY) % DAY;
  const frame = Math.floor(t / 500) % 48;
  const digits = String(Math.max(1, Math.min(9999, Math.floor(day))));
  let s = `Rk${String(frame).padStart(2, "0")}Rn${digits.length}`;
  for (let i = 0; i < digits.length; i++) s += "R" + (5 + i) + digits[i];
  return s;
}

// ---------------------------------------------------------------- running the time
function syncRule() {
  try {
    const rules = world.gameRules;
    if (enabled("time_custom")) {
      if (rules.doDayLightCycle) {
        rules.doDayLightCycle = false;
        world.setDynamicProperty(OWNED, true);
      }
    } else if (world.getDynamicProperty(OWNED) === true) {
      rules.doDayLightCycle = true;
      world.setDynamicProperty(OWNED, false);
    }
  } catch (e) {}
}

function running() {
  try {
    // an admin who turns the game's cycle back on (/gamerule) wins; a cycle frozen before this pack stays frozen
    return enabled("time_custom") && world.getDynamicProperty(OWNED) === true && !world.gameRules.doDayLightCycle;
  } catch (e) {
    return false;
  }
}

function survivalLike(p) {
  try {
    return String(p.getGameMode()).toLowerCase() !== "spectator";
  } catch (e) {
    return true;
  }
}

// With the cycle off the game may not skip the night for sleepers, so do it here
function sleepCheck() {
  const players = world.getAllPlayers().filter((p) => p.dimension.id === "minecraft:overworld" && survivalLike(p));
  const asleep = players.filter((p) => p.isSleeping).length;
  let pct = 100;
  try {
    pct = world.gameRules.playersSleepingPercentage;
  } catch (e) {}
  const need = Math.max(1, Math.ceil((players.length * Math.max(0, Math.min(100, pct))) / 100));
  if (asleep === 0 || asleep < need) {
    sleepTicks = 0;
    return;
  }
  sleepTicks += STEP_TICKS;
  if (sleepTicks < SLEEP_TICKS) return;
  sleepTicks = 0;
  const tod = timeOfDay();
  if (tod < 12000) return; // already morning (the game did it)
  world.setAbsoluteTime(world.getAbsoluteTime() + (DAY - tod));
  try {
    world.getDimension("overworld").setWeather("Clear");
  } catch (e) {}
}

export function initDaytime() {
  system.run(syncRule);
  onSettingChange((name) => {
    if (name === "time_custom" || name === "halfday_minutes" || name === "*") syncRule();
  });
  system.runInterval(() => {
    if (!running()) {
      carry = 0;
      return;
    }
    try {
      carry += timeRate() * STEP_TICKS;
      const whole = Math.floor(carry);
      if (whole > 0) {
        carry -= whole;
        world.setAbsoluteTime(world.getAbsoluteTime() + whole);
      }
      sleepCheck();
    } catch (e) {}
  }, STEP_TICKS);
}
