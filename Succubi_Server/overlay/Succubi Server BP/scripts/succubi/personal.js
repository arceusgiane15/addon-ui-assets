import { system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { openWallet } from "./money.js";
import { openHeightForm } from "../height/ui.js";
import { getHeightCm, lockFor } from "../height/height.js";
import { gunsInstalled } from "./packs.js";
import { refreshHud } from "./hud.js";

// Player's own settings, opened from the wallet (replaces the old compass menu - no free items here)
const UI = "textures/ui/succubi_ui/icons/";

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

export async function openPersonal(player, note = "") {
  const hidden = player.hasTag("hide_hud");
  const lock = lockFor(player);
  const guns = gunsInstalled();
  const form = new ActionFormData()
    .title("§lตั้งค่าของฉัน")
    .body(note || "§7ตั้งค่าเฉพาะตัวคุณ ไม่มีผลกับคนอื่น");
  form.button(`§lแถบสถานะ (HUD): ${hidden ? "§cซ่อน" : "§aแสดง"}\n§7เลือด อาหาร น้ำ สติ เหนือช่องของ`, `${UI}hud`);
  const noFx = player.hasTag("no_screen_fx");
  form.button(`§lเอฟเฟกต์จอ: ${noFx ? "§cปิด" : "§aเปิด"}\n§7ขอบจอแดงตอนเลือดน้อย · จอเทาตอนสติต่ำ`, `${UI}screen_fx`);
  form.button(
    `§lปรับส่วนสูง · ${getHeightCm(player)} ซม.\n§7${lock.seconds ? `เปลี่ยนได้อีกใน ${Math.ceil(lock.seconds / 60)} นาที` : "ส่วนสูงมีผลกับเลือดสูงสุด"}`,
    `${UI}height`
  );
  if (guns) form.button("§lวิธีใช้ปืน\n§7ยิง เล็ง รีโหลด", `${UI}gun`);
  form.button("§lกลับไปกระเป๋าตังค์", `${UI}back`);

  const r = await show(form, player);
  if (!r || r.canceled) return;
  const sel = r.selection;
  if (sel === 0) {
    if (hidden) player.removeTag("hide_hud");
    else player.addTag("hide_hud");
    refreshHud(player);
    return openPersonal(player, hidden ? "§aแสดงแถบสถานะแล้ว" : "§eซ่อนแถบสถานะแล้ว (กดอีกครั้งเพื่อแสดง)");
  }
  if (sel === 1) {
    if (noFx) player.removeTag("no_screen_fx");
    else player.addTag("no_screen_fx");
    refreshHud(player);
    return openPersonal(player, noFx ? "§aเปิดเอฟเฟกต์จอแล้ว" : "§eปิดเอฟเฟกต์จอแล้ว (แถบสถานะยังอยู่)");
  }
  if (sel === 2) return openHeightForm(player);
  if (guns && sel === 3) return openGunGuide(player);
  return openWallet(player);
}

async function openGunGuide(player) {
  const form = new ActionFormData()
    .title("§lวิธีใช้ปืน")
    .body(
      "§f§lเริ่มต้น§r\n" +
        "§7ปืนที่เพิ่งได้มายังไม่มีกระสุน ต้องรีโหลดก่อน\n\n" +
        "§f§lรีโหลด§r\n" +
        "§7• ถือปืนไว้ในมือหลัก\n" +
        "§7• พกแม็กกาซีนรุ่นเดียวกับปืนไว้ในช่องเก็บของ\n" +
        "§7• คลิกขวาค้าง หรือย่อแล้วคลิกซ้าย\n" +
        "§7• เล่นท่ารีโหลดจบ กระสุนเต็มทันที\n\n" +
        "§f§lยิงและเล็ง§r\n" +
        "§7• มีกระสุนแล้วคลิกขวาเพื่อยิง\n" +
        "§7• ย่อตัวเพื่อเล็งศูนย์\n\n" +
        "§7ไม่ต้องถือแม็กไว้มือซ้าย ระบบดึงจากช่องเก็บของให้เอง"
    )
    .button("§lเข้าใจแล้ว", `${UI}back`);
  await show(form, player);
  return openPersonal(player);
}
