import { world, system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { openWallet } from "./money.js";
import { openHeightForm } from "../height/ui.js";
import { getHeightCm, lockFor } from "../height/height.js";

// Player's own settings, opened from the wallet (replaces the old compass menu - no free items here).
// Since v1.1.11 only the height lives here: the HUD, screen effects, pressure sounds and tension music are
// switched for everyone by admins only (settings item -> สถานะและ HUD).
const UI = "textures/ui/succubi_ui/icons/";
// what players could switch off for themselves before v1.1.11 - cleared on join so nobody stays stuck
const OLD_PERSONAL_TAGS = ["hide_hud", "no_screen_fx", "no_pressure_sfx", "no_tension_music"];

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

export async function openPersonal(player, note = "") {
  const lock = lockFor(player);
  const form = new ActionFormData()
    .title("§lตั้งค่าของฉัน")
    .body(note || "§7ตั้งค่าเฉพาะตัวคุณ ไม่มีผลกับคนอื่น");
  form.button(
    `§lปรับส่วนสูง · ${getHeightCm(player)} ซม.\n§7${lock.seconds ? `เปลี่ยนได้อีกใน ${Math.ceil(lock.seconds / 60)} นาที` : "ส่วนสูงมีผลกับเลือด ความเร็ว แรงตี"}`,
    `${UI}height`
  );
  form.button("§lกลับไปกระเป๋าตังค์", `${UI}back`);
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) return openHeightForm(player);
  return openWallet(player);
}

export function initPersonal() {
  world.afterEvents.playerSpawn.subscribe((event) => {
    if (!event.initialSpawn || !event.player) return;
    for (const tag of OLD_PERSONAL_TAGS) {
      try {
        if (event.player.hasTag(tag)) event.player.removeTag(tag);
      } catch (e) {}
    }
  });
}
