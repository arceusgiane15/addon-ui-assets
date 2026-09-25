import { system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import {
  getHeightCm, setHeightCm, isHitboxAvailable, limitsFor, clampFor, lockFor, startCooldown, isFree, bodyStats,
  percentText, standardCm, cooldownMinutes
} from "./height.js";

// Invisible colour codes tell RP ui/server_form.json to draw the height window.
// "hNNN" in the title = silhouette height (NNN = cm / 10), "rP" / "rA" = which ruler (players 0-250 cm, admins 0-500 cm).
//  - menu (ActionForm): ปรับส่วนสูง / รีเซ็ตส่วนสูง / ยกเลิก
//  - slider (ModalForm): ยืนยัน saves, ยกเลิก / X / Esc leave without changing anything
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
    .button("รีเซ็ต", TEX + "wbtn_reset" + suffix)
    .button("ยกเลิก", TEX + "wbtn_cancel");
  const r = await show(form, player);
  if (!r || r.canceled || r.selection === 2) return;
  if (lockText(player)) {
    player.onScreenDisplay.setActionBar(lockText(player));
    return;
  }
  if (r.selection === 0) return openSlider(player);
  if (r.selection === 1) return openReset(player);
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
