import { world, system } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { enabled, setEnabled, isAdmin } from "./settings_store.js";
import { applyNametagsToAll } from "./nametags.js";
import { gunsInstalled } from "./packs.js";
import { enforceLimits } from "../height/height.js";
import { EVENT_IDS, EVENT_NAMES, runEvent, setSanity, getSanity } from "./sanity.js";
import { setThirst, getThirst, THIRST_MAX } from "./thirst.js";
import { isBloodMoon, startBloodMoon, endBloodMoon } from "./bloodmoon.js";

export const SETTINGS_ID = "succubi:server_settings";
const onOff = (v) => (v ? "§aเปิด" : "§cปิด");

// World switches are for admins: creative mode or the tag "succubi_admin" (isAdmin in settings_store.js)

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

export async function openSettings(player) {
  if (!isAdmin(player)) {
    player.sendMessage("§c[ตั้งค่า] ใช้ได้เฉพาะแอดมิน (โหมดสร้างสรรค์ หรือมีแท็ก succubi_admin)");
    return;
  }
  const rows = [
    ["sanity", `§lระบบค่าสติ: ${onOff(enabled("sanity"))}`],
    ["thirst", `§lระบบหิวน้ำ: ${onOff(enabled("thirst"))}`],
    ["events", `§lเหตุการณ์ผิดปกติ: ${onOff(enabled("events"))}`],
    ["rules", `§lอุปกรณ์กฎสยอง: ${onOff(enabled("rules"))}`],
    ["bloodmoon", `§lคืนพระจันทร์เลือด (สุ่ม): ${onOff(enabled("bloodmoon"))}`],
    ["nametag_near", `§lชื่อผู้เล่น: ${enabled("nametag_near") ? "§eเห็นเมื่อมองตรงๆ" : "§aแสดงตลอด"}`],
    ["height_free", `§lส่วนสูงอิสระ 1-500 ซม.: ${onOff(enabled("height_free"))}\n§7ปิด = ผู้เล่นปรับได้ 140-220 ซม. ทุก 5 นาที`]
  ];
  const form = new ActionFormData()
    .title("§lตั้งค่าเซิร์ฟเวอร์§0§9§4§1")
    .body(
      `§7สติของฉัน §d${getSanity(player).toFixed(0)}§7/100   น้ำ §b${getThirst(player).toFixed(0)}§7/${THIRST_MAX}\n` +
        `§7แพ็คปืน: ${gunsInstalled() ? "§aเปิดอยู่" : "§8ไม่ได้ติดตั้ง"}§7 · สวิตช์มีผลกับทุกคนในโลก`
    );
  rows.forEach(([, label]) => form.button(label));
  form.button("§lทดลองเหตุการณ์ผิดปกติ\n§7เกิดกับตัวเองเท่านั้น");
  form.button("§lตั้งค่าสติของฉัน\n§7ไว้ทดสอบหมอก");
  form.button("§lเติมน้ำของฉันให้เต็ม");
  form.button(isBloodMoon() ? "§l§cหยุดคืนพระจันทร์เลือด" : "§l§4เริ่มคืนพระจันทร์เลือดตอนนี้\n§7(เปลี่ยนเวลาเป็นกลางคืน)");
  form.button("§7ปิด");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const i = r.selection;
  if (i < rows.length) {
    const key = rows[i][0];
    setEnabled(key, !enabled(key));
    if (key === "nametag_near") applyNametagsToAll();
    if (key === "height_free" && !enabled("height_free")) {
      for (const p of world.getAllPlayers()) {
        try {
          enforceLimits(p);
        } catch (e) {}
      }
    }
    world.sendMessage(`§e[ตั้งค่า] ${player.name} ${enabled(key) ? "§aเปิด" : "§cปิด"}§e${rows[i][1].split(":")[0].replace("§l", "")}`);
    return openSettings(player);
  }
  if (i === rows.length) return openEvents(player);
  if (i === rows.length + 1) return openSetSanity(player);
  if (i === rows.length + 2) {
    setThirst(player, THIRST_MAX);
    player.sendMessage("§b[ตั้งค่า] เติมน้ำเต็มแล้ว");
    return openSettings(player);
  }
  if (i === rows.length + 3) {
    if (isBloodMoon()) endBloodMoon();
    else startBloodMoon(true);
  }
}

async function openEvents(player) {
  const form = new ActionFormData().title("§lทดลองเหตุการณ์ผิดปกติ§0§9§4§1").body("§7เลือกแล้วเกิดกับตัวเองทันที (ลดสติจริง)");
  form.button("§l§dสุ่ม 1 เหตุการณ์");
  for (const id of EVENT_IDS) form.button(EVENT_NAMES[id] ?? id);
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) runEvent(player);
  else if (r.selection <= EVENT_IDS.length) runEvent(player, EVENT_IDS[r.selection - 1]);
  else return openSettings(player);
}

async function openSetSanity(player) {
  const values = [100, 60, 45, 25, 10, 0];
  const form = new ActionFormData().title("§lตั้งค่าสติของฉัน§0§9§4§1").body("§7ต่ำกว่า 50 / 30 / 15 จะมีหมอกมืด 3 ระดับ");
  values.forEach((v) => form.button(`§l${v}`));
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection < values.length) {
    setSanity(player, values[r.selection]);
    player.sendMessage(`§d[ตั้งค่า] สติ = ${values[r.selection]}`);
  }
  return openSettings(player);
}

export function initSettings() {
  world.afterEvents.itemUse.subscribe((event) => {
    if (event.itemStack?.typeId !== SETTINGS_ID) return;
    system.run(() => {
      openSettings(event.source).catch(() => {});
    });
  });
}
