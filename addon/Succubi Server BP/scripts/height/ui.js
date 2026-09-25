import { system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { CONFIG } from "./config.js";
import {
  getHeightCm, setHeightCm, isHitboxAvailable, limitsFor, clampFor, lockFor, startCooldown, isFree, bodyStats, percentText
} from "./height.js";

// Invisible colour codes tell RP ui/server_form.json to draw the height window.
// "hNNN" in the title = silhouette height (NNN = cm / 10), "rP" / "rA" = which ruler (players 0-250 cm, admins 0-500 cm).
// It is a modal form with one slider: drag to the height you want and close the window - closing keeps the new
// height (the close button submits the form). Only Esc / the phone's back key leave without changing.
export const HEIGHT_FLAG = "§0§9§8§5";

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

function lockText(player) {
  const lock = lockFor(player);
  if (!lock.seconds) return "";
  return lock.reason === "fight" ? `§cเพิ่งต่อสู้ รออีก ${fmtWait(lock.seconds)}` : `§cเปลี่ยนได้อีกครั้งใน ${fmtWait(lock.seconds)}`;
}

function statsLine(cm) {
  const st = bodyStats(cm);
  return `§c${st.hp} HP§7 · ความเร็ว §b${percentText(st.speed)}§7 · แรงตี §6${percentText(st.damage)}`;
}

export async function openHeightForm(player) {
  const current = getHeightCm(player);
  const [lo, hi] = limitsFor(player);
  const free = isFree(player);
  const lock = lockText(player);
  if (lock) {
    // locked: show where things stand instead of a slider that would do nothing
    const form = new ActionFormData().title("§lปรับส่วนสูง")
      .body(`§fตอนนี้ §d${current} ซม.§f · ${statsLine(current)}\n\n${lock}`)
      .button("§lตกลง", "textures/ui/succubi_ui/icons/back");
    await show(form, player);
    return;
  }
  const label =
    `§fตอนนี้ §d${current} ซม.\n${statsLine(current)}\n` +
    `§7ตัวเล็ก วิ่งไว ตีเบา · ตัวสูง เดินช้า ตีแรง\n` +
    `§7${lo}-${hi} ซม.${free ? "" : ` · เปลี่ยนได้ ${CONFIG.cooldownSeconds / 60} นาทีครั้ง`}\n` +
    `§eเลื่อนแล้วกดปิด (X) = ใช้ความสูงนี้\n§fส่วนสูง (ซม.)`;
  const form = new ModalFormData()
    .title(`§lปรับส่วนสูง${HEIGHT_FLAG}${silhouetteToken(current)}${free ? "rA" : "rP"}`)
    .slider(label, lo, hi, 1, clampFor(player, current));
  const response = await show(form, player);
  if (!response || response.canceled) return;
  const next = clampFor(player, Number(response.formValues?.[0]));
  if (!isFinite(next) || next === current) return;
  const late = lockText(player);
  if (late) return player.onScreenDisplay.setActionBar(late);
  setHeightCm(player, next);
  startCooldown(player);
  player.playSound("random.levelup", { pitch: 1.6, volume: 0.6 });
  player.onScreenDisplay.setActionBar(`§aส่วนสูง ${next} ซม. §7· ${statsLine(next)}`);
  if (!isHitboxAvailable()) player.sendMessage("§c[ส่วนสูง] ปรับขนาดตัวไม่ได้ (ไม่พบ event ใน player.json)");
}
