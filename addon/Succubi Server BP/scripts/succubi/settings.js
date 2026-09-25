import { world, system } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { enabled, setEnabled, isAdmin, num, setNum, resetNums, setMany, NUMS, HEIGHT_SWITCHES } from "./settings_store.js";
import { applyNametagsToAll } from "./nametags.js";
import { gunsInstalled } from "./packs.js";
import { enforceLimits, calculateMaxHp, bodyStats, percentText } from "../height/height.js";
import { heightPoints } from "../height/body.js";
import { HALFDAY_CHOICES, timeText, clockText } from "./daytime.js";
import { EVENT_IDS, EVENT_NAMES, runEvent, setSanity, getSanity } from "./sanity.js";
import { setThirst, getThirst, thirstMax } from "./thirst.js";
import { linkPackRunning } from "./regen.js";

// Server settings item (อุปกรณ์ตั้งค่าเซิร์ฟเวอร์), admins only (creative mode or the tag "succubi_admin"):
//   สถานะและ HUD   - sanity / thirst systems with their gauges, gauge numbers, pressure sounds, test tools
//   Rule of Horror - master switch (off = nothing strange happens at all), random events, rule zones and props
//   สเตตัสพื้นฐาน   - max HP, regeneration, food, water, sanity rates and what height changes
//   เวลาและนาฬิกา  - how fast the day runs (default: 1 real hour from morning to evening), the HUD clock
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
    .button(`§lเวลาและนาฬิกา\n§7${timeText()}`)
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
  if (r.selection === 4) return openTime(player);
}

// ---------------------------------------------------------------- สถานะและ HUD
async function openStatus(player) {
  const rows = [
    ["sanity", "ระบบสติ + วงสมองบน HUD", "ปิด = ไม่มีสติ หมอกสติ จอเทา และวงสมอง"],
    ["thirst", "ระบบกระหายน้ำ + วงน้ำบน HUD", "ปิด = ไม่ต้องดื่มน้ำ และไม่มีวงน้ำ"],
    ["hud_numbers", "ตัวเลขใต้วงบน HUD", "เลือด (HP) อาหาร น้ำ สติ (%)"],
    ["pressure", "เสียงกดดัน", "หัวใจเต้น ท้องร้อง หอบ กระซิบ ตอนค่าต่ำ"],
    ["hud_arrows", "ลูกศรขึ้น/ลงบนวง", "บอกว่าค่ากำลังเพิ่มหรือลด และเร็วแค่ไหน"],
    ["hud_clock", "นาฬิกาและวันที่ (มุมขวาบน)", "กลางวัน · เย็น · กลางคืน + วันที่"],
    ["tension_music", "เพลงตึงเครียดแทนเพลงเกม", "เลือดต่ำ / สติต่ำ จะไม่มีเพลงชิลของเกมมาขัด"]
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
  const form = new ActionFormData().title(`§lตั้งค่าสติของฉัน${FLAG}`).body("§7ต่ำกว่า 70 จอเริ่มซ่าแบบทีวี · 65 จอเริ่มเทา · 50 / 30 / 15 หมอกมืดและจอซ่าหนักขึ้น · ต่ำกว่า 15 เงามาหา");
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
  const { lo, std, hi } = heightPoints();
  return [
    `§c§lเลือด§r §fMax HP §c${num("hp_base")}§f ที่ส่วนสูงมาตรฐาน ${std} ซม.` +
      (hpOn ? `§7 (${lo} ซม. = ${calculateMaxHp(lo)}, ${hi} ซม. = ${calculateMaxHp(hi)})` : "§7 (ทุกคนเท่ากัน)"),
    `§7ฟื้นเลือด: §f${regenText()}`,
    `§6§lอาหาร§r §fสูงสุด 20 §7(ตายตัวตามเกม) · §f${foodText()}`,
    `§b§lน้ำ§r §fสูงสุด ${thirstMax()} · ลด 1 หน่วยทุก ${secs(num("thirst_seconds"))} §7(วิ่ง ×2.2, เนเธอร์ ×1.6)\n` +
      "§7ต่ำกว่า 30% เดินช้า · 10% อ่อนแรง · หมด = เลือดลด 2 ทุก 4 วิ",
    `§d§lสติ§r §fสูงสุด 100 · ลด ${num("sanity_loss")}% · ฟื้น ${num("sanity_gain")}%\n` +
      "§7ลดเมื่อ: โดนตี มอนสเตอร์ใกล้ตัว (บอสลดมาก) อยู่เนเธอร์/จี เจอเรื่องผิดปกติ" +
      (enabled("sanity_world") ? " กลางคืน ที่มืด กินของดิบ\n" : "\n") +
      "§7ฟื้นเมื่อ: กินดื่มของอร่อย นอน อยู่ใกล้เพื่อน ฟังเพลงร้านชา กอดตุ๊กตา อ่านหนังสือ" +
      (enabled("sanity_world") ? " เก็บดอกไม้ นั่งข้างกองไฟ" : "") +
      (enabled("shadows_real") ? "\n§7ต่ำกว่า 15%: เงากลายเป็นของจริงและเข้ามาทำร้าย" : ""),
    `§a§lส่วนสูง§r §f${lo}-${hi} ซม. (มาตรฐาน ${std}) · ` +
      HEIGHT_PAGES.map(([key, label]) => `${label} ${onOff(enabled(key))}`).join(" §f· ") +
      "\n§7ตัวเล็ก: เลือดน้อย วิ่งไว ตีเบา · ตัวสูง: เลือดมาก เดินช้า ตีแรง (ไม่ใช้เอฟเฟกต์ยา)"
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
      resetNums(Object.keys(NUMS).filter((n) => n !== "halfday_minutes"), [...HEIGHT_SWITCHES, "sanity_world", "shadows_real"]);
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
    .slider(`Max HP ที่ส่วนสูงมาตรฐาน ${heightPoints().std} ซม. (ค่าที่ตัวเตี้ย/ตัวสูงตั้งในหน้าส่วนสูง)`, NUMS.hp_base.min, NUMS.hp_base.max, 5, num("hp_base"))
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
    .slider("สติฟื้น (% ของปกติ)", 0, 300, 25, num("sanity_gain"))
    .toggle("สติแบบ Don't Starve: กลางคืน/ที่มืด/ของดิบลด · ดอกไม้/กองไฟ/ของสุกเพิ่ม", enabled("sanity_world"))
    .toggle("ต่ำกว่า 15% เงากลายเป็นของจริง (โจมตีได้ ตีตายได้ ดรอปเชื้อเพลิงฝันร้าย)", enabled("shadows_real"));
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  setNum("sanity_loss", r.formValues[0]);
  setNum("sanity_gain", r.formValues[1]);
  if (!!r.formValues[2] !== enabled("sanity_world")) toggle(player, "sanity_world", "สติแบบ Don't Starve");
  if (!!r.formValues[3] !== enabled("shadows_real")) toggle(player, "shadows_real", "เงาตอนสติต่ำ");
  announce(player, `สติลด ${num("sanity_loss")}% · ฟื้น ${num("sanity_gain")}%`);
  return saved;
}

// ---------------------------------------------------------------- ส่วนสูง
// Every stat is set at the shortest height, the standard height and the tallest height; in between it runs in a
// straight line. [switch, label, number key, unit, slider step, what it does]
const HEIGHT_PAGES = [
  ["height_hp", "เลือด", "hp", "HP", 5, "Max HP"],
  ["height_speed", "ความเร็ว", "spd", "%", 1, "ความเร็วเดิน/วิ่ง"],
  ["height_damage", "แรงตี", "dmg", "%", 5, "แรงตีมือเปล่า/อาวุธระยะประชิด (ปืน ธนู ไม่เปลี่ยน)"],
  ["height_fall", "ดาเมจตก", "fall", "%", 5, "ดาเมจที่ได้รับตอนตกจากที่สูง"],
  ["height_hunger", "หิวและน้ำ", "hunger", "%", 5, "ความเร็วที่อาหารและน้ำลด"],
  ["height_hurt", "ดาเมจที่รับ", "hurt", "%", 5, "ดาเมจที่ได้รับเวลาโดนตีหรือโดนยิง"]
];

// Presets keep the admin's standard HP and height range; they only move how much height matters
const HEIGHT_PRESETS = [
  ["สมดุล (ค่าเริ่มต้น)", { hp: [0.5, 2], spd: [115, 87], dmg: [77, 130], fall: [75, 125], hunger: [85, 120], hurt: [110, 90] }],
  ["ต่างกันมาก (เล่นสนุก)", { hp: [0.4, 2.5], spd: [125, 80], dmg: [65, 145], fall: [60, 150], hunger: [80, 135], hurt: [115, 85] }],
  ["ต่างกันน้อย (PvP จริงจัง)", { hp: [0.8, 1.3], spd: [107, 94], dmg: [90, 112], fall: [90, 110], hunger: [95, 108], hurt: [105, 95] }],
  ["ปิดผลทั้งหมด (ส่วนสูงเปลี่ยนแค่ขนาดตัว)", null]
];

const signed = (p) => (p === 100 ? "ปกติ" : `${p > 100 ? "+" : ""}${p - 100}%`);

// one row of the table: "140 ซม. · 50 HP · เร็ว +15% · ตี -23% · ตก -25% · หิว -15% · รับ +10%"
function heightRow(cm) {
  const st = bodyStats(cm);
  const bits = [`§c${st.hp} HP`];
  const add = (key, label, f) => {
    if (enabled(key)) bits.push(`§7${label} §f${percentText(f)}`);
  };
  add("height_speed", "เร็ว", st.speed);
  add("height_damage", "ตี", st.damage);
  add("height_fall", "ตก", st.fall);
  add("height_hunger", "หิว", st.hunger);
  add("height_hurt", "รับ", st.hurt);
  return `§d${cm} ซม.§7 · ` + bits.join(" §7· ");
}

export function heightTable() {
  const { lo, std, hi } = heightPoints();
  const rows = [lo, Math.round((lo + std) / 2), std, Math.round((std + hi) / 2), hi];
  return [...new Set(rows)].map((cm) => (cm === std ? heightRow(cm) + " §e(มาตรฐาน)" : heightRow(cm))).join("\n");
}

function pageSummary([key, , short, unit]) {
  if (!enabled(key)) return "§cปิด";
  if (short === "hp") return `§f${num("hp_short")} / ${num("hp_base")} / ${num("hp_tall")} HP`;
  return `§f${signed(num(short + "_short"))} / ปกติ / ${signed(num(short + "_tall"))}`;
}

async function editHeight(player, note = "") {
  const { lo, std, hi } = heightPoints();
  const form = new ActionFormData().title(`§lส่วนสูง${FLAG}`)
    .body(
      `§7ค่าที่ ตัวเตี้ยสุด / มาตรฐาน / ตัวสูงสุด ระหว่างนั้นไล่เป็นเส้นตรง\n${heightTable()}` + (note ? `\n\n${note}` : "")
    )
    .button(`§lช่วงส่วนสูงและกติกา\n§7${lo}-${hi} ซม. · มาตรฐาน ${std} · ${num("h_cooldown")} นาทีครั้ง`);
  HEIGHT_PAGES.forEach((page) => form.button(`§l${page[1]}\n${pageSummary(page)}`));
  form.button("§lพรีเซ็ต\n§7สมดุล · ต่างกันมาก · ต่างกันน้อย · ปิด");
  form.button("§lคืนค่าส่วนสูงเป็นค่าเริ่มต้น");
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return undefined;
  const i = r.selection;
  let msg;
  if (i === 0) msg = await editHeightRules(player);
  else if (i <= HEIGHT_PAGES.length) msg = await editHeightStat(player, HEIGHT_PAGES[i - 1]);
  else if (i === HEIGHT_PAGES.length + 1) msg = await pickHeightPreset(player);
  else if (i === HEIGHT_PAGES.length + 2) msg = await resetHeightSettings(player);
  else return undefined;
  return editHeight(player, msg ?? "");
}

async function editHeightRules(player) {
  const { lo, std, hi } = heightPoints();
  const m = new ModalFormData().title(`§lช่วงส่วนสูงและกติกา${FLAG}`)
    .slider("ส่วนสูงต่ำสุดที่ผู้เล่นปรับได้ (ซม.)", 10, 490, 5, lo)
    .slider("ส่วนสูงมาตรฐาน (ซม.) = เลือด ความเร็ว แรงตีปกติ / ผู้เล่นใหม่และปุ่มรีเซ็ต", 10, 495, 5, std)
    .slider("ส่วนสูงสูงสุดที่ผู้เล่นปรับได้ (ซม.)", 20, 500, 5, hi)
    .slider("เปลี่ยนได้ทุกกี่นาที (0 = ไม่จำกัด, รีเซ็ตก็นับ)", NUMS.h_cooldown.min, NUMS.h_cooldown.max, 1, num("h_cooldown"))
    .slider("ห้ามเปลี่ยนหลังต่อสู้กี่วินาที", NUMS.h_fight_lock.min, NUMS.h_fight_lock.max, 5, num("h_fight_lock"))
    .toggle("ส่วนสูงอิสระ 1-500 ซม. ไม่มีรอ (แอดมินได้เสมอ)", enabled("height_free"));
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  // keep them in order: shortest < standard < tallest
  const [a, b, c] = [r.formValues[0], r.formValues[1], r.formValues[2]].map(Number).sort((x, y) => x - y);
  const nLo = a;
  const nStd = Math.max(nLo + 5, b);
  const nHi = Math.max(nStd + 5, c);
  setMany({ h_min: nLo, h_std: nStd, h_max: nHi, h_cooldown: r.formValues[3], h_fight_lock: r.formValues[4] }, {}, "h_range");
  if (!!r.formValues[5] !== enabled("height_free")) toggle(player, "height_free", "ส่วนสูงอิสระ");
  announce(player, `ส่วนสูง ${nLo}-${nHi} ซม. (มาตรฐาน ${nStd}) · เปลี่ยนได้ทุก ${num("h_cooldown")} นาที · ล็อกหลังต่อสู้ ${num("h_fight_lock")} วิ`);
  return saved;
}

async function editHeightStat(player, [key, label, short, unit, step, what]) {
  const { lo, std, hi } = heightPoints();
  const nShort = `${short}_short`;
  const nTall = `${short}_tall`;
  const m = new ModalFormData().title(`§l${label}${FLAG}`).toggle(`ส่วนสูงมีผลกับ${what}`, enabled(key));
  const unitText = unit === "%" ? "% (100 = ปกติ)" : unit;
  m.slider(`${what} ที่ส่วนสูง ${lo} ซม. (เตี้ยสุด) ${unitText}`, NUMS[nShort].min, NUMS[nShort].max, step, num(nShort));
  if (short === "hp") m.slider(`Max HP ที่ส่วนสูงมาตรฐาน ${std} ซม.`, NUMS.hp_base.min, NUMS.hp_base.max, step, num("hp_base"));
  m.slider(`${what} ที่ส่วนสูง ${hi} ซม. (สูงสุด) ${unitText}`, NUMS[nTall].min, NUMS[nTall].max, step, num(nTall));
  const r = await show(m, player);
  if (!r || r.canceled) return undefined;
  const v = r.formValues;
  const values = short === "hp" ? { hp_short: v[1], hp_base: v[2], hp_tall: v[3] } : { [nShort]: v[1], [nTall]: v[2] };
  setMany(values, { [key]: !!v[0] }, key);
  const shown = short === "hp" ? `${num("hp_short")} / ${num("hp_base")} / ${num("hp_tall")} HP` : `${signed(num(nShort))} / ${signed(num(nTall))}`;
  announce(player, `ส่วนสูง → ${label} ${onOff(enabled(key))}§r ${enabled(key) ? `(เตี้ย/สูง: ${shown})` : ""}`);
  return saved;
}

async function pickHeightPreset(player) {
  const form = new ActionFormData().title(`§lพรีเซ็ตส่วนสูง${FLAG}`)
    .body(`§7เปลี่ยนแค่ว่าส่วนสูงมีผลมากแค่ไหน · ช่วงส่วนสูงและ Max HP มาตรฐาน (${num("hp_base")}) คงเดิม`);
  HEIGHT_PRESETS.forEach(([name]) => form.button(`§l${name}`));
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled || r.selection >= HEIGHT_PRESETS.length) return undefined;
  const [name, p] = HEIGHT_PRESETS[r.selection];
  const switches = Object.fromEntries(HEIGHT_SWITCHES.map((k) => [k, !!p]));
  if (!p) {
    setMany({}, switches, "height_preset");
  } else {
    const base = num("hp_base");
    const values = { hp_short: base * p.hp[0], hp_tall: base * p.hp[1] };
    for (const key of ["spd", "dmg", "fall", "hunger", "hurt"]) {
      values[`${key}_short`] = p[key][0];
      values[`${key}_tall`] = p[key][1];
    }
    values.hp_short = Math.round(values.hp_short / 5) * 5;
    values.hp_tall = Math.round(values.hp_tall / 5) * 5;
    setMany(values, switches, "height_preset");
  }
  announce(player, `พรีเซ็ตส่วนสูง: ${name}`);
  return saved;
}

async function resetHeightSettings(player) {
  const c = await show(new ActionFormData().title(`§lคืนค่าส่วนสูง${FLAG}`)
    .body("§fคืนค่าทุกอย่างในหน้าส่วนสูงเป็นค่าเริ่มต้น?\n§7140-220 ซม. มาตรฐาน 180 · 5 นาทีครั้ง · เลือด 50/100/200 · ผลทุกอย่างเปิด")
    .button("§l§cคืนค่า").button("§7ยกเลิก"), player);
  if (!c || c.canceled || c.selection !== 0) return undefined;
  const names = Object.keys(NUMS).filter((n) => /^(h_|hp_|spd_|dmg_|fall_|hunger_|hurt_)/.test(n));
  resetNums(names, [...HEIGHT_SWITCHES, "height_free"]);
  announce(player, "คืนค่าส่วนสูงเป็นค่าเริ่มต้น");
  return saved;
}

// ---------------------------------------------------------------- เวลาและนาฬิกา
async function openTime(player) {
  const form = new ActionFormData().title(`§lเวลาและนาฬิกา${FLAG}`)
    .body(`§f${clockText()}\n§7ความเร็วเวลา: §f${timeText()}\n§7นาฬิกาบน HUD: ${onOff(enabled("hud_clock"))}`)
    .button(`§lความเร็วเวลา\n§7${timeText()}`)
    .button(`§lเวลาแบบกำหนดเอง: ${onOff(enabled("time_custom"))}\n§7ปิด = เวลาเดินแบบเกมปกติ (เช้าถึงเย็น 10 นาที)`)
    .button(`§lนาฬิกาและวันที่บน HUD: ${onOff(enabled("hud_clock"))}`)
    .button("§lคืนค่าเวลา\n§71 ชม.จริง = เช้าถึงเย็นพอดี")
    .button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) {
    const current = Math.max(0, HALFDAY_CHOICES.indexOf(num("halfday_minutes")));
    const m = new ModalFormData().title(`§lความเร็วเวลา${FLAG}`).dropdown(
      "ใช้เวลาจริงกี่นาที จากเช้าถึงเย็นในเกม (12 ชม.ในเกม)\nกลางคืนยาวเท่ากัน",
      HALFDAY_CHOICES.map((m) => (m === 10 ? "10 นาที (เท่าเกมปกติ)" : m >= 60 ? `${m / 60} ชม.${m % 60 ? ` ${m % 60} นาที` : ""}` : `${m} นาที`)),
      current === -1 ? 0 : current
    );
    const a = await show(m, player);
    if (a && !a.canceled) {
      setMany({ halfday_minutes: HALFDAY_CHOICES[a.formValues[0]] ?? 60 }, { time_custom: true }, "halfday_minutes");
      announce(player, `ความเร็วเวลา: ${timeText()}`);
    }
  } else if (r.selection === 1) toggle(player, "time_custom", "เวลาแบบกำหนดเอง");
  else if (r.selection === 2) toggle(player, "hud_clock", "นาฬิกาและวันที่บน HUD");
  else if (r.selection === 3) {
    resetNums(["halfday_minutes"], ["time_custom"]);
    announce(player, `คืนค่าเวลา: ${timeText()}`);
  } else return openSettings(player);
  return openTime(player);
}

export function initSettings() {
  world.afterEvents.itemUse.subscribe((event) => {
    if (event.itemStack?.typeId !== SETTINGS_ID) return;
    system.run(() => {
      openSettings(event.source).catch(() => {});
    });
  });
}
