import { system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { CONFIG } from "./config.js";
import {
  getHeightCm, setHeightCm, calculateMaxHp, isHitboxAvailable, hitboxStepFor,
  limitsFor, clampFor, lockFor, startCooldown, isFree
} from "./height.js";

// Invisible colour codes tell RP ui/server_form.json to draw the height board.
// "hNNN" in the title = silhouette height (NNN = cm / 10), "rP" / "rA" = which ruler (players 0-250 cm, admins 0-500 cm).
export const HEIGHT_FLAG = "§0§9§8§5";
// Buttons, in this order (the board lays them out by index):
// 0 -10 | 1 -1 | 2 +1 | 3 +10 | 4 type | 5 reset | 6 confirm | 7 close
const STEPS = [-10, -1, 1, 10];

const wait = (ticks) => new Promise((resolve) => system.runTimeout(resolve, ticks));
const drafts = new Map(); // player id -> cm being tried on the board (not applied until confirmed)

async function show(form, player) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const response = await form.show(player);
    if (!response.canceled || response.cancelationReason !== "UserBusy") return response;
    await wait(10);
  }
  return undefined;
}

const silhouetteToken = (cm) => "h" + String(Math.max(1, Math.min(50, Math.round(cm / 10)))).padStart(3, "0");
const bodyScale = (cm) => hitboxStepFor(cm) / CONFIG.baseCm;
const fmtWait = (s) => (s >= 60 ? `${Math.floor(s / 60)} นาที ${s % 60} วิ` : `${s} วิ`);

function scaleWarning(player, cm) {
  if (!isHitboxAvailable()) return "\n§cปรับขนาดตัวไม่ได้ (ไม่พบ event ใน player.json)";
  try {
    const actual = player.getComponent("minecraft:scale")?.value;
    if (typeof actual === "number" && Math.abs(actual - bodyScale(cm)) > 0.02) return `\n§cตัวในเกมยังเป็น x${actual.toFixed(2)}`;
  } catch (e) {}
  return "";
}

function lockText(player) {
  const lock = lockFor(player);
  if (!lock.seconds) return "";
  return lock.reason === "fight" ? `§cเพิ่งต่อสู้ รออีก ${fmtWait(lock.seconds)}` : `§cเปลี่ยนได้อีกครั้งใน ${fmtWait(lock.seconds)}`;
}

// Height board. The +/- buttons only move a preview; "ยืนยัน" applies it.
export async function openHeightForm(player, note = "") {
  const current = getHeightCm(player);
  if (!drafts.has(player.id)) drafts.set(player.id, clampFor(player, current));
  const draft = drafts.get(player.id);
  const [lo, hi] = limitsFor(player);
  const free = isFree(player);
  const lock = lockText(player);
  const changed = draft !== current;

  const form = new ActionFormData()
    .title(`§lปรับส่วนสูง${HEIGHT_FLAG}${silhouetteToken(draft)}${free ? "rA" : "rP"}`)
    .body(
      `§7ที่เลือก §d§l${draft} ซม.§r${changed ? ` §7(ตอนนี้ ${current})` : ""}\n` +
        `§7เลือดสูงสุด §c§l${calculateMaxHp(draft)} HP§r\n` +
        `§7ปรับได้ ${lo}-${hi} ซม.${free ? "" : ` · ${CONFIG.cooldownSeconds / 60} นาที/ครั้ง`}` +
        (lock ? `\n${lock}` : "") + scaleWarning(player, current) + (note ? `\n${note}` : "")
    );
  for (const step of STEPS) {
    const blocked = (step < 0 && draft <= lo) || (step > 0 && draft >= hi);
    form.button(`§l${step > 0 ? "+" : ""}${step}`, `textures/ui/succubi_height/btn_${step < 0 ? "minus" : "plus"}${blocked ? "_off" : ""}`);
  }
  form.button("§lพิมพ์", "textures/ui/succubi_height/btn_type");
  form.button("§lรีเซ็ต", "textures/ui/succubi_height/btn_reset");
  form.button("§lยืนยัน", `textures/ui/succubi_height/btn_confirm${changed && !lock ? "" : "_off"}`);
  form.button("§lปิด", "textures/ui/succubi_height/btn_close");

  const response = await show(form, player);
  if (!response || response.canceled || response.selection === 7) {
    drafts.delete(player.id);
    return;
  }
  let message = "";
  const sel = response.selection;
  if (sel < STEPS.length) {
    const next = clampFor(player, draft + STEPS[sel]);
    if (next === draft) message = "§eสุดช่วงที่ปรับได้แล้ว";
    drafts.set(player.id, next);
  } else if (sel === 4) {
    await openHeightTyped(player);
  } else if (sel === 5) {
    drafts.set(player.id, clampFor(player, CONFIG.baseCm));
  } else if (sel === 6) {
    if (!changed) {
      message = "§7ยังไม่ได้เปลี่ยนความสูง";
    } else if (lockText(player)) {
      message = lockText(player);
    } else {
      setHeightCm(player, draft);
      startCooldown(player);
      player.playSound("random.levelup", { pitch: 1.6, volume: 0.6 });
      message = `§aเปลี่ยนเป็น ${draft} ซม. แล้ว`;
      await wait(3); // let the new body size apply before the board reads it back
    }
  }
  return openHeightForm(player, message);
}

// Exact height typed as a number (still only a preview until confirmed)
export async function openHeightTyped(player) {
  const [lo, hi] = limitsFor(player);
  const form = new ModalFormData()
    .title("พิมพ์ส่วนสูง")
    .textField(`ส่วนสูงเป็นเซนติเมตร (${lo}-${hi})\n§7ปกติ ${CONFIG.baseCm} ซม. = ${CONFIG.baseHp} HP`, String(CONFIG.baseCm), String(drafts.get(player.id) ?? getHeightCm(player)));
  const response = await show(form, player);
  if (!response || response.canceled) return;
  const typed = String(response.formValues?.[0] ?? "").trim();
  if (typed !== "" && isFinite(Number(typed))) drafts.set(player.id, clampFor(player, Number(typed)));
}
