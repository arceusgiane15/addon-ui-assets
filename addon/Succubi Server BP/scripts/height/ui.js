import { world, system, EquipmentSlot } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { CONFIG } from "./config.js";
import {
  getHeightCm, setHeightCm, isHitboxAvailable, limitsFor, clampFor, lockFor, startCooldown, isFree, bodyStats,
  percentText, standardCm, cooldownMinutes
} from "./height.js";

// Invisible colour codes tell RP ui/server_form.json to draw the height window.
// "hNNN" in the title = silhouette height (NNN = cm / 10), "rP" / "rA" = which ruler (players 0-250 cm, admins 0-500 cm).
//  - menu (ActionForm): ปรับส่วนสูง / เงย-ก้มปรับ / รีเซ็ตส่วนสูง / ยกเลิก
//  - slider (ModalForm): ยืนยัน saves, ยกเลิก / X / Esc leave without changing anything
//  - tilt mode: look up = taller, look down = shorter, sneak = confirm, use the item again = cancel
export const HEIGHT_FLAG = "§0§9§8§5";
const TEX = "textures/ui/succubi_height/";

const wait = (ticks) => new Promise((resolve) => system.runTimeout(resolve, ticks));

async function show(form, player) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const response = await form.show(player);
    if (!response.canceled || response.cancelationReason !== "UserBusy") return response;
    await wait(10);
  }
  return undefined;
}

const silhouetteToken = (cm) => "h" + String(Math.max(1, Math.min(50, Math.round(cm / 10)))).padStart(3, "0");
const fmtWait = (s) => (s >= 60 ? `${Math.floor(s / 60)} นาที ${s % 60} วิ` : `${s} วิ`);
const title = (player, cm) => `§lปรับส่วนสูง${HEIGHT_FLAG}${silhouetteToken(cm)}${isFree(player) ? "rA" : "rP"}`;

function lockText(player) {
  const lock = lockFor(player);
  if (!lock.seconds) return "";
  return lock.reason === "fight" ? `§cเพิ่งต่อสู้ รออีก ${fmtWait(lock.seconds)}` : `§cเปลี่ยนได้อีกครั้งใน ${fmtWait(lock.seconds)}`;
}

export function statsLine(cm) {
  const st = bodyStats(cm);
  return `§c${st.hp} HP§7 · ความเร็ว §b${percentText(st.speed)}§7 · แรงตี §6${percentText(st.damage)}`;
}

// the smaller effects, only the ones that differ from normal
function extraLine(cm) {
  const st = bodyStats(cm);
  const parts = [
    ["ตก", st.fall],
    ["หิว", st.hunger],
    ["รับดาเมจ", st.hurt]
  ].filter(([, f]) => Math.round((f - 1) * 100) !== 0);
  return parts.length ? "§7" + parts.map(([n, f]) => `${n} ${percentText(f)}`).join(" · ") : "";
}

function rulesLine(player) {
  const [lo, hi] = limitsFor(player);
  const cd = cooldownMinutes();
  return `§7${lo}-${hi} ซม.${isFree(player) || !cd ? "" : ` · เปลี่ยนได้ ${cd} นาทีครั้ง`}`;
}

// Change the height for real (after the lock was checked once more)
function apply(player, next, how) {
  const late = lockText(player);
  if (late) {
    player.onScreenDisplay.setActionBar(late);
    return false;
  }
  setHeightCm(player, next);
  startCooldown(player);
  player.playSound("random.levelup", { pitch: 1.6, volume: 0.6 });
  player.onScreenDisplay.setActionBar(`§a${how} ${next} ซม. §7· ${statsLine(next)}`);
  if (!isHitboxAvailable()) player.sendMessage("§c[ส่วนสูง] ปรับขนาดตัวไม่ได้ (ไม่พบ event ใน player.json)");
  return true;
}

// ---------------------------------------------------------------- menu
export async function openHeightForm(player) {
  const current = getHeightCm(player);
  const lock = lockText(player);
  const extra = extraLine(current);
  const suffix = lock ? "_off" : "";
  const form = new ActionFormData()
    .title(title(player, current))
    .body(`§fตอนนี้ §d${current} ซม.\n${statsLine(current)}\n${extra ? extra + "\n" : ""}${rulesLine(player)}${lock ? "\n" + lock : ""}`)
    .button("ปรับส่วนสูง", TEX + "wbtn_adjust" + suffix)
    .button("เงย-ก้มปรับ", TEX + "wbtn_tilt" + suffix)
    .button("รีเซ็ต", TEX + "wbtn_reset" + suffix)
    .button("ยกเลิก", TEX + "wbtn_cancel");
  const r = await show(form, player);
  if (!r || r.canceled || r.selection === 3) return;
  if (lockText(player)) {
    player.onScreenDisplay.setActionBar(lockText(player));
    return;
  }
  if (r.selection === 0) return openSlider(player);
  if (r.selection === 1) return startTilt(player);
  if (r.selection === 2) return openReset(player);
}

// ---------------------------------------------------------------- slider
async function openSlider(player) {
  const current = getHeightCm(player);
  const [lo, hi] = limitsFor(player);
  const label = `§fตอนนี้ §d${current} ซม.\n${statsLine(current)}\n${rulesLine(player)}\n§fส่วนสูง (ซม.)`;
  const form = new ModalFormData()
    .title(title(player, current))
    .slider(label, lo, hi, 1, clampFor(player, current))
    .submitButton("ยืนยัน");
  const response = await show(form, player);
  if (!response || response.canceled) return; // ยกเลิก / X / Esc: nothing changes
  const next = clampFor(player, Number(response.formValues?.[0]));
  if (!isFinite(next)) return;
  if (next === current) {
    player.onScreenDisplay.setActionBar(`§7ส่วนสูงเท่าเดิม ${current} ซม.`);
    return;
  }
  apply(player, next, "ส่วนสูง");
}

// ---------------------------------------------------------------- reset
async function openReset(player) {
  const current = getHeightCm(player);
  const target = clampFor(player, standardCm());
  if (target === current) {
    player.onScreenDisplay.setActionBar(`§7ส่วนสูงมาตรฐาน ${current} ซม. อยู่แล้ว`);
    return;
  }
  const cd = cooldownMinutes();
  const form = new ActionFormData()
    .title(title(player, target))
    .body(
      `§fรีเซ็ตเป็นส่วนสูงมาตรฐาน\n§d${current} → ${target} ซม.\n${statsLine(target)}` +
        (isFree(player) || !cd ? "" : `\n§7นับเป็นการเปลี่ยน 1 ครั้ง (รอ ${cd} นาที)`)
    )
    .button("ยืนยัน", TEX + "wbtn_confirm")
    .button("ยกเลิก", TEX + "wbtn_cancel");
  const r = await show(form, player);
  if (!r || r.canceled || r.selection !== 0) return;
  apply(player, target, "รีเซ็ตส่วนสูงเป็น");
}

// ---------------------------------------------------------------- tilt mode (look up / down)
const PITCH_SPAN = 50; // looking 50 degrees up = tallest, 50 degrees down = shortest
const TILT_TICKS = 2;
const TILT_TIMEOUT = 20 * 30;
const tilting = new Map(); // player id -> { value, armed, started, shown }

function holdsAdjuster(player) {
  try {
    return player.getComponent("minecraft:equippable")?.getEquipment(EquipmentSlot.Mainhand)?.typeId === CONFIG.itemId;
  } catch (e) {
    return false;
  }
}

export function heightFromPitch(pitch, lo, hi) {
  const t = Math.min(1, Math.max(0, (PITCH_SPAN - pitch) / (2 * PITCH_SPAN)));
  return Math.round(lo + t * (hi - lo));
}

function startTilt(player) {
  tilting.set(player.id, { value: getHeightCm(player), armed: !player.isSneaking, started: system.currentTick, shown: 0 });
  player.playSound("random.orb", { pitch: 1.4, volume: 0.5 });
  player.sendMessage("§d[ส่วนสูง]§f เงยหน้า = สูงขึ้น · ก้มหน้า = เตี้ยลง · §eย่อตัว = ยืนยัน§f · ใช้ไอเทมอีกครั้ง = ยกเลิก");
}

function stopTilt(player, text) {
  tilting.delete(player.id);
  if (text) player.onScreenDisplay.setActionBar(text);
}

function tiltTick(player, t, tick) {
  if (!holdsAdjuster(player)) return stopTilt(player, "§7ยกเลิกการปรับส่วนสูง (เปลี่ยนของในมือ)");
  if (tick - t.started > TILT_TIMEOUT) return stopTilt(player, "§7ยกเลิกการปรับส่วนสูง (หมดเวลา)");
  const [lo, hi] = limitsFor(player);
  const value = heightFromPitch(player.getRotation().x, lo, hi);
  if (value !== t.value) {
    // a soft tick every 5 cm, higher pitch for taller
    if (Math.floor(value / 5) !== Math.floor(t.value / 5)) {
      player.playSound("random.click", { pitch: 0.7 + ((value - lo) / Math.max(1, hi - lo)) * 0.9, volume: 0.35 });
    }
    t.value = value;
    t.shown = 0;
  }
  if (!player.isSneaking) t.armed = true;
  else if (t.armed) {
    tilting.delete(player.id);
    if (value === getHeightCm(player)) return player.onScreenDisplay.setActionBar(`§7ส่วนสูงเท่าเดิม ${value} ซม.`);
    apply(player, value, "ส่วนสูง");
    return;
  }
  if (tick - t.shown >= 20) {
    t.shown = tick;
    const now = getHeightCm(player);
    const arrow = value > now ? "§a▲" : value < now ? "§c▼" : "§7•";
    player.onScreenDisplay.setActionBar(`${arrow} §d${value} ซม.§7 (ตอนนี้ ${now}) · ${statsLine(value)}\n§7เงย/ก้มหน้าเพื่อปรับ · §eย่อตัว = ยืนยัน§7 · ใช้ไอเทม = ยกเลิก`);
  }
}

// Using the adjuster while tilting cancels instead of opening the menu
export function onAdjusterUse(player) {
  if (tilting.has(player.id)) return stopTilt(player, "§7ยกเลิกการปรับส่วนสูง");
  openHeightForm(player).catch(() => {});
}

export function initTiltMode() {
  world.afterEvents.playerLeave.subscribe((e) => tilting.delete(e.playerId));
  system.runInterval(() => {
    if (tilting.size === 0) return;
    const tick = system.currentTick;
    for (const player of world.getAllPlayers()) {
      const t = tilting.get(player.id);
      if (!t) continue;
      try {
        tiltTick(player, t, tick);
      } catch (e) {
        tilting.delete(player.id);
      }
    }
  }, TILT_TICKS);
}
