import { world, system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { enabled, setEnabled, isAdmin, num, setNum, resetNums, NUMS } from "./settings_store.js";
import { applyNametagsToAll } from "./nametags.js";
import { gunsInstalled } from "./packs.js";
import { enforceLimits, calculateMaxHp } from "../height/height.js";
import { EVENT_IDS, EVENT_NAMES, runEvent, setSanity, getSanity } from "./sanity.js";
import { setThirst, getThirst, thirstMax } from "./thirst.js";
import { linkPackRunning } from "./regen.js";

// Server settings item (อุปกรณ์ตั้งค่าเซิร์ฟเวอร์), admins only (creative mode or the tag "succubi_admin"):
//   สถานะและ HUD   - sanity / thirst systems with their gauges, gauge numbers, pressure sounds, test tools
//   Rule of Horror - master switch (off = nothing strange happens at all), random events, rule zones and props
//   สเตตัสพื้นฐาน   - max HP, regeneration, food, water, sanity rates and what height changes
export const SETTINGS_ID = "succubi:server_settings";
const FLAG = "§0§9§4§1"; // gold settings window (RP ui/server_form.json)
const onOff = (v) => (v ? "§aเปิด" : "§cปิด");
const REGEN_CHOICES = [0, 0.5, 1, 1.5, 2, 3, 4, 5, 8, 10, 15, 20, 30];
const FOOD_CHOICES = [0, 10, 20, 30, 45, 60, 90, 120, 180, 300];

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

function announce(player, text) {
  world.sendMessage(`§e[ตั้งค่า] ${player.name}: ${text}`);
}

function toggle(player, key, label) {
  setEnabled(key, !enabled(key));
  if (key === "nametag_near") applyNametagsToAll();
  if (key === "height_free" && !enabled("height_free")) {
    for (const p of world.getAllPlayers()) {
      try {
        enforceLimits(p);
      } catch (e) {}
    }
  }
  announce(player, `${label} ${onOff(enabled(key))}`);
}

// ---------------------------------------------------------------- main
export async function openSettings(player) {
  if (!isAdmin(player)) {
    player.sendMessage("§c[ตั้งค่า] ใช้ได้เฉพาะแอดมิน (โหมดสร้างสรรค์ หรือมีแท็ก succubi_admin)");
    return;
  }
  const form = new ActionFormData()
    .title(`§lตั้งค่าเซิร์ฟเวอร์${FLAG}`)
    .body(
      `§7แพ็คปืน: ${gunsInstalled() ? "§aเปิดอยู่" : "§8ไม่ได้ติดตั้ง"}§7 · Link BP: ${linkPackRunning() ? "§aทำงาน" : "§cไม่พบ (อาหารบน HUD/ฟื้นเลือด/อาหารลด)"}\n` +
        "§7ทุกอย่างในนี้มีผลกับทุกคนในโลก"
    )
    .button("§lสถานะและ HUD\n§7สติ · น้ำ · ตัวเลข · เสียงกดดัน")
    .button(`§lRule of Horror: ${onOff(enabled("horror"))}\n§7เรื่องผิดปกติ · โซนกฎ · รูปปั้น`)
    .button("§lสเตตัสพื้นฐาน\n§7เลือด ฟื้นเลือด อาหาร น้ำ สติ ส่วนสูง")
    .button(`§lชื่อผู้เล่น: ${enabled("nametag_near") ? "§eเห็นเมื่อมองตรงๆ" : "§aแสดงตลอด"}`)
    .button("§7ปิด");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) return openStatus(player);
  if (r.selection === 1) return openHorror(player);
  if (r.selection === 2) return openBase(player);
  if (r.selection === 3) {
    toggle(player, "nametag_near", "ชื่อผู้เล่นแบบเห็นเมื่อมอง");
    return openSettings(player);
  }
}

// ---------------------------------------------------------------- สถานะและ HUD
async function openStatus(player) {
  const rows = [
    ["sanity", "ระบบสติ + วงสมองบน HUD", "ปิด = ไม่มีสติ หมอกสติ จอเทา และวงสมอง"],
    ["thirst", "ระบบกระหายน้ำ + วงน้ำบน HUD", "ปิด = ไม่ต้องดื่มน้ำ และไม่มีวงน้ำ"],
    ["hud_numbers", "ตัวเลขใต้วงบน HUD", "เลือด (HP) อาหาร น้ำ สติ (%)"],
    ["pressure", "เสียงกดดัน", "หัวใจเต้น ท้องร้อง หอบ กระซิบ ตอนค่าต่ำ"]
  ];
  const form = new ActionFormData().title(`§lสถานะและ HUD${FLAG}`)
    .body(`§7แตะเพื่อเปิด/ปิด · สติของฉัน §d${getSanity(player).toFixed(0)}§7 · น้ำ §b${getThirst(player).toFixed(0)}§7/${thirstMax()}`);
  rows.forEach(([key, label, hint]) => form.button(`§l${label}: ${onOff(enabled(key))}\n§7${hint}`));
  form.button("§lเติมน้ำของฉันให้เต็ม");
  form.button("§lตั้งค่าสติของฉัน\n§7ไว้ทดสอบหมอกและจอเทา");
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const i = r.selection;
  if (i < rows.length) {
    toggle(player, rows[i][0], rows[i][1]);
    return openStatus(player);
  }
  if (i === rows.length) {
    setThirst(player, thirstMax());
    player.sendMessage("§b[ตั้งค่า] เติมน้ำเต็มแล้ว");
    return openStatus(player);
  }
  if (i === rows.length + 1) return openSetSanity(player);
  return openSettings(player);
}

async function openSetSanity(player) {
  const values = [100, 60, 45, 25, 10, 0];
  const form = new ActionFormData().title(`§lตั้งค่าสติของฉัน${FLAG}`).body("§7ต่ำกว่า 70 จอเริ่มเทา · 50 / 30 / 15 หมอกมืด 3 ระดับ");
  values.forEach((v) => form.button(`§l${v}`));
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection < values.length) {
    setSanity(player, values[r.selection]);
    player.sendMessage(`§d[ตั้งค่า] สติ = ${values[r.selection]}`);
  }
  return openStatus(player);
}

// ---------------------------------------------------------------- Rule of Horror
async function openHorror(player) {
  const master = enabled("horror");
  const form = new ActionFormData().title(`§lRule of Horror${FLAG}`)
    .body(
      `§fโหมดสยอง: ${onOff(master)}\n` +
        "§7ปิด = ไม่มีเรื่องผิดปกติใดๆ เกิดขึ้นเลย ทั้งเหตุการณ์สุ่ม เหตุการณ์จากหนังสือ โซนกฎ และรูปปั้น\n" +
        "§7(ป้ายกฎยังอ่านได้ สติยังลดตามปกติจากมอนสเตอร์และการโดนตี)"
    )
    .button(`§lโหมด Rule of Horror: ${onOff(master)}\n§7สวิตช์หลักของทุกอย่างด้านล่าง`)
    .button(`§lเหตุการณ์ผิดปกติแบบสุ่ม: ${onOff(enabled("events"))}\n§7ราวทุก ${num("event_minutes")} นาทีต่อคน`)
    .button(`§lโซนกฎ ป้ายกฎ รูปปั้น: ${onOff(enabled("rules"))}\n§7ของจากไม้เท้ากฎสยอง`)
    .button("§lความถี่เหตุการณ์\n§7ตั้งเป็นนาที")
    .button("§lทดลองเหตุการณ์\n§7เกิดกับตัวเองเท่านั้น")
    .button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) toggle(player, "horror", "โหมด Rule of Horror");
  else if (r.selection === 1) toggle(player, "events", "เหตุการณ์ผิดปกติแบบสุ่ม");
  else if (r.selection === 2) toggle(player, "rules", "โซนกฎ ป้ายกฎ รูปปั้น");
  else if (r.selection === 3) {
    const m = new ModalFormData().title(`§lความถี่เหตุการณ์${FLAG}`)
      .slider("เหตุการณ์ผิดปกติเกิดกับแต่ละคนราวทุกกี่นาที (เล่นจริง)", NUMS.event_minutes.min, NUMS.event_minutes.max, 5, num("event_minutes"));
    const a = await show(m, player);
    if (a && !a.canceled) setNum("event_minutes", a.formValues[0]);
  } else if (r.selection === 4) return openEvents(player);
  else return openSettings(player);
  return openHorror(player);
}

async function openEvents(player) {
  const form = new ActionFormData().title(`§lทดลองเหตุการณ์ผิดปกติ${FLAG}`)
    .body(enabled("horror") ? "§7เลือกแล้วเกิดกับตัวเองทันที (ลดสติจริง)" : "§cโหมด Rule of Horror ปิดอยู่ เหตุการณ์จะไม่เกิด");
  form.button("§l§dสุ่ม 1 เหตุการณ์");
  for (const id of EVENT_IDS) form.button(EVENT_NAMES[id] ?? id);
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) runEvent(player);
  else if (r.selection <= EVENT_IDS.length) runEvent(player, EVENT_IDS[r.selection - 1]);
  else return openHorror(player);
}

// ---------------------------------------------------------------- สเตตัสพื้นฐาน
const secs = (v) => `${String(v).replace(/\.0$/, "")} วิ`;
export function regenText() {
  const s = num("regen_seconds");
  return s > 0 ? `1 HP ทุก ${secs(s)} เมื่ออาหารตั้งแต่ ${num("regen_food")}/20` : "แบบเกมปกติ (อาหาร 18 ขึ้นไป ฟื้น 1 HP ทุก 4 วิ, เพิ่งกินจะเร็วกว่า)";
}
export function foodText() {
  const s = num("food_drain_seconds");
  return s > 0 ? `หิวตามการเคลื่อนไหว + ลดเพิ่ม 1 หน่วยทุก ${secs(s)}` : "หิวตามการเคลื่อนไหวแบบเกม (วิ่ง กระโดด ต่อสู้)";
}

export function baseSummary() {
  const hpOn = enabled("height_hp");
  return [
    `§c§lเลือด§r §fMax HP §c${num("hp_base")}§f ที่ส่วนสูง 180 ซม.` +
      (hpOn ? `§7 (140 ซม. = ${calculateMaxHp(140)}, 220 ซม. = ${calculateMaxHp(220)})` : "§7 (ทุกคนเท่ากัน)"),
    `§7ฟื้นเลือด: §f${regenText()}`,
    `§6§lอาหาร§r §fสูงสุด 20 §7(ตายตัวตามเกม) · §f${foodText()}`,
    `§b§lน้ำ§r §fสูงสุด ${thirstMax()} · ลด 1 หน่วยทุก ${secs(num("thirst_seconds"))} §7(วิ่ง ×2.2, เนเธอร์ ×1.6)\n` +
      "§7ต่ำกว่า 30% เดินช้า · 10% อ่อนแรง · หมด = เลือดลด 2 ทุก 4 วิ",
    `§d§lสติ§r §fสูงสุด 100 · ลด ${num("sanity_loss")}% · ฟื้น ${num("sanity_gain")}%\n` +
      "§7ลดเมื่อ: โดนตี มอนสเตอร์ใกล้ตัว (บอสลดมาก) อยู่เนเธอร์/จี เจอเรื่องผิดปกติ\n" +
      "§7ฟื้นเมื่อ: กินดื่มของอร่อย นอน อยู่ใกล้เพื่อน ฟังเพลงร้านชา กอดตุ๊กตา อ่านหนังสือ",
    `§a§lส่วนสูง§r §fเลือด ${onOff(hpOn)} §f· ความเร็ว ${onOff(enabled("height_speed"))} §f· แรงตี ${onOff(enabled("height_damage"))}\n` +
      "§7ตัวเล็ก: เลือดน้อย วิ่งไว ตีเบา · ตัวสูง: เลือดมาก เดินช้า ตีแรง (ไม่ใช้เอฟเฟกต์ยา)"
  ].join("\n");
}

async function openBase(player, note = "") {
  const form = new ActionFormData().title(`§lสเตตัสพื้นฐาน${FLAG}`).body(baseSummary() + (note ? `\n\n${note}` : ""))
    .button("§lเลือดและการฟื้นเลือด")
    .button("§lอาหาร")
    .button("§lน้ำ")
    .button("§lสติ")
    .button("§lส่วนสูง")
    .button("§lคืนค่าเริ่มต้นทั้งหมด")
    .button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const pages = [editBlood, editFood, editWater, editSanity, editHeight];
  if (r.selection < pages.length) {
    const msg = await pages[r.selection](player);
    return openBase(player, msg ?? "");
  }
  if (r.selection === 5) {
    const c = await show(new ActionFormData().title(`§lคืนค่าเริ่มต้น${FLAG}`).body("§fคืนค่าสเตตัสพื้นฐานทั้งหมดเป็นค่าเริ่มต้น?")
      .button("§l§cคืนค่า").button("§7ยกเลิก"), player);
    if (c && !c.canceled && c.selection === 0) {
      resetNums();
      announce(player, "คืนค่าสเตตัสพื้นฐานเป็นค่าเริ่มต้น");
    }
    return openBase(player);
  }
  return openSettings(player);
}

const saved = "§aบันทึกแล้ว";

async function editBlood(player) {
  const regen = num("regen_seconds");
  const m = new ModalFormData().title(`§lเลือด${FLAG}`)
    .slider("Max HP ที่ส่วนสูง 180 ซม.", NUMS.hp_base.min, NUMS.hp_base.max, 10, num("hp_base"))
    .dropdown("ฟื้นเลือด", REGEN_CHOICES.map((s) => (s ? `1 HP ทุก ${secs(s)}` : "แบบเกมปกติ")), Math.max(0, REGEN_CHOICES.indexOf(regen)))
    .slider("ฟื้นเลือดเมื่ออาหารอย่างน้อย (ใช้กับแบบกำหนดเอง)", 0, 20, 1, num("regen_food"));
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  const [hp, regenIdx, food] = r.formValues;
  setNum("hp_base", hp);
  setNum("regen_seconds", REGEN_CHOICES[regenIdx] ?? 0);
  setNum("regen_food", food);
  announce(player, `Max HP ${num("hp_base")} · ฟื้นเลือด ${regenText()}`);
  return saved;
}

async function editFood(player) {
  const m = new ModalFormData().title(`§lอาหาร${FLAG}`)
    .dropdown(
      "อาหารสูงสุด 20 (ตายตัวตามเกม)\nอาหารลดเพิ่มจากการเคลื่อนไหว",
      FOOD_CHOICES.map((s) => (s ? `ลด 1 หน่วยทุก ${secs(s)}` : "ไม่ลดเพิ่ม (แบบเกม)")),
      Math.max(0, FOOD_CHOICES.indexOf(num("food_drain_seconds")))
    );
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  setNum("food_drain_seconds", FOOD_CHOICES[r.formValues[0]] ?? 0);
  announce(player, `อาหาร: ${foodText()}`);
  return linkPackRunning() ? saved : "§cต้องเปิด Succubi Server Link BP ด้วย อาหารถึงจะลดเพิ่มได้";
}

async function editWater(player) {
  const m = new ModalFormData().title(`§lน้ำ${FLAG}`)
    .slider("น้ำสูงสุด", NUMS.thirst_max.min, NUMS.thirst_max.max, 5, num("thirst_max"))
    .slider("น้ำลด 1 หน่วยทุกกี่วินาที (ยืนเฉยๆ)", NUMS.thirst_seconds.min, 300, 5, Math.min(300, num("thirst_seconds")));
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  setNum("thirst_max", r.formValues[0]);
  setNum("thirst_seconds", r.formValues[1]);
  for (const p of world.getAllPlayers()) setThirst(p, getThirst(p)); // clamp to a lower max
  announce(player, `น้ำสูงสุด ${num("thirst_max")} · ลด 1 ทุก ${secs(num("thirst_seconds"))}`);
  return saved;
}

async function editSanity(player) {
  const m = new ModalFormData().title(`§lสติ${FLAG}`)
    .slider("สติลด (% ของปกติ)", 0, 300, 25, num("sanity_loss"))
    .slider("สติฟื้น (% ของปกติ)", 0, 300, 25, num("sanity_gain"));
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  setNum("sanity_loss", r.formValues[0]);
  setNum("sanity_gain", r.formValues[1]);
  announce(player, `สติลด ${num("sanity_loss")}% · ฟื้น ${num("sanity_gain")}%`);
  return saved;
}

async function editHeight(player) {
  const keys = [
    ["height_hp", "ส่วนสูงมีผลกับเลือด (140 ซม. = ครึ่งหนึ่ง, 220 ซม. = สองเท่า)"],
    ["height_speed", "ส่วนสูงมีผลกับความเร็ว (140 ซม. +15%, 220 ซม. -13%)"],
    ["height_damage", "ส่วนสูงมีผลกับแรงตี (140 ซม. -23%, 220 ซม. +30%)"],
    ["height_free", "ส่วนสูงอิสระ 1-500 ซม. (ปิด = ผู้เล่นปรับได้ 140-220 ซม. ทุก 5 นาที)"]
  ];
  const m = new ModalFormData().title(`§lส่วนสูง${FLAG}`);
  keys.forEach(([key, label]) => m.toggle(label, enabled(key)));
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  keys.forEach(([key, label], i) => {
    if (!!r.formValues[i] !== enabled(key)) toggle(player, key, label.split(" (")[0]);
  });
  return saved;
}

export function initSettings() {
  world.afterEvents.itemUse.subscribe((event) => {
    if (event.itemStack?.typeId !== SETTINGS_ID) return;
    system.run(() => {
      openSettings(event.source).catch(() => {});
    });
  });
}
