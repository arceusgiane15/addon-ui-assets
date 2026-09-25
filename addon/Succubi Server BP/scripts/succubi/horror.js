import { world, system, ItemStack, EquipmentSlot } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { addSanity, runEvent } from "./sanity.js";
import { enabled } from "./settings_store.js";

// rule zones, boards' effects and statues run only while Rule of Horror and its "zones and props" switch are on
const horrorOn = () => enabled("horror") && enabled("rules");
import { runAs } from "./cmd.js";
import { PAPER_FLAG } from "./books.js";

// Rule of Horror kit - for admins building horror maps (creative menu: Tools, next to the rule wand):
//  rule wand     : create rule zones (break the rule inside the zone -> punishment)
//  rule board    : a notice board players read; admins get an "แก้ไข" button on it and a full text editor
//  watcher statue: moves toward players only while nobody is looking at it
// Everything here stops when the settings item's Rule of Horror switch is off (horrorOn below).
export const WAND = "succubi:rule_wand";
const BOARD = "succubi:rule_board";
const STATUE = "succubi:watcher_statue";
const PROPS = [BOARD, STATUE];
const ZONES = "succubi:rule_zones";
const DIMS = ["overworld", "nether", "the_end"];

export const RULES = [
  ["no_sprint", "ห้ามวิ่ง"], ["no_jump", "ห้ามกระโดด"], ["must_sneak", "ต้องย่อตัวตลอด"], ["no_sneak", "ห้ามย่อตัว"],
  ["freeze", "ห้ามขยับตัว (ยืนนิ่ง)"], ["no_light", "ห้ามถือแสงไฟ"], ["no_weapon", "ห้ามถืออาวุธ"], ["no_eat", "ห้ามกินหรือดื่ม"],
  ["no_build", "ห้ามวางหรือทุบบล็อก"], ["no_door", "ห้ามเปิดประตู"], ["time_limit", "ห้ามอยู่ในโซนเกินเวลา"],
  ["no_look_up", "ห้ามมองขึ้นฟ้า"], ["no_look_down", "ห้ามก้มมองพื้น"], ["not_alone", "ห้ามอยู่คนเดียว (ต้องมี 2 คนขึ้นไป)"],
  ["no_entry", "ห้ามเข้า"], ["no_chat", "ห้ามพิมพ์แชต (ต้องเปิด Beta APIs)"]
];
export const PUNISH = [
  ["sanity10", "ลดสติ 10"], ["sanity25", "ลดสติ 25"], ["event", "เหตุการณ์ผิดปกติสุ่ม"], ["jumpscare", "ผีโผล่ตรงหน้า (jumpscare)"],
  ["damage", "ดาเมจ 4"], ["pushout", "ผลักออกนอกโซน"], ["red_fog", "หมอกแดง 30 วินาที"], ["spawn", "ส่งกลับจุดเกิดโลก"], ["kill", "ตายทันที"]
];
const TIMES = [["always", "ตลอดเวลา"], ["night", "เฉพาะกลางคืน"], ["day", "เฉพาะกลางวัน"]];
const label = (list, id) => (list.find((x) => x[0] === id) ?? list[0])[1];
const idx = (list, id) => Math.max(0, list.findIndex((x) => x[0] === id));

export function isAdmin(player) {
  try {
    return player.hasTag("succubi_admin") || String(player.getGameMode?.()).toLowerCase() === "creative";
  } catch (e) {
    return false;
  }
}
const survival = (p) => {
  try {
    const m = String(p.getGameMode?.()).toLowerCase();
    return m !== "creative" && m !== "spectator";
  } catch (e) {
    return true;
  }
};
const isNight = () => {
  const t = world.getTimeOfDay();
  return t >= 13000 && t < 23000;
};
const later = (t, fn) => system.runTimeout(() => {
  try {
    fn();
  } catch (e) {}
}, t);
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
const flat = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);
const held = (p) => p.getComponent("minecraft:equippable")?.getEquipment(EquipmentSlot.Mainhand);

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

// ---------------------------------------------------------------- jumpscare (shared)
export function jumpscare(player, loss = 15) {
  const d = player.getViewDirection();
  const len = Math.hypot(d.x, d.z) || 1;
  const at = { x: player.location.x + (d.x / len) * 2.2, y: player.location.y, z: player.location.z + (d.z / len) * 2.2 };
  try {
    const s = player.dimension.spawnEntity("succubi:shadow_figure", at);
    s.teleport(at, { facingLocation: player.location });
    later(16, () => s.remove());
  } catch (e) {}
  runAs(player, "playsound mob.endermen.scream @s ~ ~ ~ 1 0.7");
  runAs(player, "playsound mob.ghast.scream @s ~ ~ ~ 1 1.2");
  runAs(player, "camerashake add @s 0.9 1 rotational");
  runAs(player, "camera @s fade time 0 0.12 0.35 color 110 0 0");
  if (enabled("sanity")) addSanity(player, -loss);
}

// ---------------------------------------------------------------- rule zones
let zones = [];
function loadZones() {
  try {
    const v = JSON.parse(world.getDynamicProperty(ZONES) ?? "[]");
    zones = Array.isArray(v) ? v : [];
  } catch (e) {
    zones = [];
  }
}
function saveZones() {
  world.setDynamicProperty(ZONES, JSON.stringify(zones));
}
const inside = (p, z) => z.dim === p.dimension.id && flat(p.location, z) <= z.r && Math.abs(p.location.y - z.y) <= Math.max(4, z.r);
const activeNow = (z) => z.on && (z.time === "always" || (z.time === "night") === isNight());

const state = new Map(); // player id -> { zones: Map(zoneId -> enteredTick), last: pos, outside: pos, cool: Map }
function st(p) {
  if (!state.has(p.id)) state.set(p.id, { zones: new Map(), last: { ...p.location }, outside: { ...p.location }, cool: new Map() });
  return state.get(p.id);
}

function punish(player, zone) {
  const s = st(player);
  const now = system.currentTick;
  if (now - (s.cool.get(zone.id) ?? -1000) < 60) return;
  s.cool.set(zone.id, now);
  player.sendMessage(zone.violate ? `§4${zone.violate}` : `§4คุณทำผิดกฎ: ${label(RULES, zone.rule)}`);
  switch (zone.punish) {
    case "sanity10": if (enabled("sanity")) addSanity(player, -10); runAs(player, "playsound mob.elderguardian.curse @s ~ ~ ~ 0.6 1"); break;
    case "sanity25": if (enabled("sanity")) addSanity(player, -25); runAs(player, "playsound mob.elderguardian.curse @s ~ ~ ~ 1 0.7"); break;
    case "event": runEvent(player); break;
    case "jumpscare": jumpscare(player); break;
    case "damage": player.applyDamage(4); break;
    case "pushout": player.teleport(s.outside); break;
    case "red_fog":
      runAs(player, "fog @s push succubi:red_fog succubi_rule");
      later(600, () => runAs(player, "fog @s remove succubi_rule"));
      break;
    case "spawn": {
      const sp = world.getDefaultSpawnLocation();
      player.teleport({ x: sp.x + 0.5, y: sp.y > 300 ? 100 : sp.y, z: sp.z + 0.5 }, { dimension: world.getDimension("overworld") });
      break;
    }
    case "kill": player.kill(); break;
  }
}

const LIGHTS = ["torch", "lantern", "candle", "glowstone", "sea_lantern", "shroomlight", "froglight", "jack_o_lantern", "flare"];
function holdsLight(p) {
  const eq = p.getComponent("minecraft:equippable");
  for (const slot of [EquipmentSlot.Mainhand, EquipmentSlot.Offhand]) {
    const id = eq?.getEquipment(slot)?.typeId ?? "";
    if (LIGHTS.some((l) => id.includes(l))) return true;
  }
  return false;
}
function holdsWeapon(p) {
  const it = held(p);
  if (!it) return false;
  const id = it.typeId;
  try {
    if (it.hasTag("is_weapon") || it.hasTag("minecraft:is_sword")) return true;
  } catch (e) {}
  return /sword|axe|bow|trident|mace/.test(id) && !id.includes("pickaxe");
}

function breaks(p, z, s) {
  switch (z.rule) {
    case "no_sprint": return p.isSprinting;
    case "no_jump": return p.isJumping || p.getVelocity().y > 0.35;
    case "must_sneak": return !p.isSneaking;
    case "no_sneak": return p.isSneaking;
    case "freeze": return flat(p.location, s.last) > 0.25;
    case "no_light": return holdsLight(p);
    case "no_weapon": return holdsWeapon(p);
    case "time_limit": return system.currentTick - (s.zones.get(z.id) ?? system.currentTick) > (Number(z.value) || 30) * 20;
    case "no_look_up": return p.getRotation().x < -55;
    case "no_look_down": return p.getRotation().x > 55;
    case "not_alone": return world.getAllPlayers().filter((o) => survival(o) && inside(o, z)).length < 2;
    case "no_entry": return true;
    default: return false;
  }
}

function zoneTick() {
  if (!horrorOn() || zones.length === 0) return;
  for (const p of world.getAllPlayers()) {
    if (!survival(p)) continue;
    const s = st(p);
    let any = false;
    for (const z of zones) {
      if (!activeNow(z) || !inside(p, z)) {
        s.zones.delete(z.id);
        continue;
      }
      any = true;
      if (!s.zones.has(z.id)) {
        s.zones.set(z.id, system.currentTick);
        p.onScreenDisplay.setActionBar(`§4[กฎ] §f${z.enter || label(RULES, z.rule)}`);
        runAs(p, "playsound note.bass @s ~ ~ ~ 1 0.5");
      }
      try {
        if (breaks(p, z, s)) punish(p, z);
      } catch (e) {}
    }
    if (!any) s.outside = { ...p.location };
    s.last = { ...p.location };
  }
}

function eventRule(player, rule) {
  if (!horrorOn() || !player || !survival(player)) return;
  for (const z of zones) if (z.rule === rule && activeNow(z) && inside(player, z)) punish(player, z);
}

// admins holding the wand see the zones
function drawZones() {
  for (const p of world.getAllPlayers()) {
    if (held(p)?.typeId !== WAND) continue;
    const near = zones.filter((z) => z.dim === p.dimension.id && flat(p.location, z) < 64).slice(0, 12);
    for (const z of near) {
      const n = Math.min(32, Math.max(12, Math.round(z.r * 3)));
      for (let i = 0; i < n; i++) {
        const a = (Math.PI * 2 * i) / n;
        try {
          p.dimension.spawnParticle(z.on ? "minecraft:basic_flame_particle" : "minecraft:basic_smoke_particle", { x: z.x + Math.cos(a) * z.r, y: z.y + 0.3, z: z.z + Math.sin(a) * z.r });
        } catch (e) {}
      }
      try {
        p.dimension.spawnParticle("minecraft:villager_angry", { x: z.x, y: z.y + 1.5, z: z.z });
      } catch (e) {}
    }
  }
}

// ---------------------------------------------------------------- wand screens (horror skin: HORROR_FLAG at the end of the title)
const HORROR_FLAG = "§0§9§4§2";
const onOffText = (v) => (v ? "§aเปิด" : "§cปิด");
const RADII = [2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40];
const SECONDS = [10, 15, 20, 30, 45, 60, 90, 120, 180, 300];

async function wandMenu(player) {
  if (!isAdmin(player)) return player.sendMessage("§c[กฎสยอง] ใช้ได้เฉพาะแอดมิน (โหมดสร้างสรรค์ หรือแท็ก succubi_admin)");
  const near = zones.filter((z) => z.dim === player.dimension.id && flat(player.location, z) <= 128).length;
  const form = new ActionFormData()
    .title(`§lไม้เท้ากฎสยอง${HORROR_FLAG}`)
    .body(`§fโซนกฎทั้งหมด §e${zones.length}§f โซน (ใกล้ตัว §e${near}§f)\n§7ถือไม้เท้านี้ไว้จะเห็นขอบโซนเป็นเปลวไฟ\n§fRule of Horror: ${onOffText(enabled("horror"))} §7· โซนและของประกอบ: ${onOffText(enabled("rules"))} §7(ตั้งได้ที่อุปกรณ์ตั้งค่า)`)
    .button("§l§aสร้างโซนกฎตรงที่ยืน\n§7ตั้งกฎ รัศมี และบทลงโทษ")
    .button("§lโซนใกล้ตัว / แก้ไข\n§7ย้าย วาร์ป หรือลบโซน")
    .button("§lวิธีใช้อุปกรณ์กฎสยอง")
    .button("§7ปิด");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) return editZone(player, undefined);
  if (r.selection === 1) return zoneList(player);
  if (r.selection === 2) return help(player);
}

// pick one from a list (custom screen); undefined = back
async function pick(player, title, names, current) {
  const form = new ActionFormData().title(`§l${title}${HORROR_FLAG}`).body("§fเลือก 1 อย่าง");
  names.forEach((n, i) => form.button(i === current ? `§l§e> ${n} <` : `§f${n}`));
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled || r.selection >= names.length) return undefined;
  return r.selection;
}

// typing screen (only for text); undefined = cancelled
async function typeText(player, title, hint, value) {
  const form = new ModalFormData().title(`§l${title}${HORROR_FLAG}`).textField(title, hint, String(value ?? ""));
  const r = await show(form, player);
  if (!r || r.canceled) return undefined;
  return String(r.formValues?.[0] ?? "").slice(0, LINE_CHARS);
}

const TEXTS = {
  name: ["ชื่อโซน", "เช่น ห้องใต้ดิน"],
  enter: ["ข้อความตอนเดินเข้าโซน", "เช่น ห้ามส่งเสียงดัง"],
  violate: ["ข้อความตอนทำผิด", "เช่น มันได้ยินคุณแล้ว"]
};

// zone editor: every choice is a button, the draft is kept until "save"
async function editZone(player, zone, draft) {
  const z = draft ?? { ...(zone ?? { id: `z${Date.now().toString(36)}`, name: "", dim: player.dimension.id, x: Math.floor(player.location.x) + 0.5,
    y: Math.floor(player.location.y), z: Math.floor(player.location.z) + 0.5, r: 6, rule: "no_sprint", value: "30",
    punish: "sanity10", time: "always", enter: "", violate: "", on: true }) };
  const rows = [
    ["name", `§lชื่อโซน\n${z.name ? `§f${z.name}` : "§7(ว่าง = ใช้ชื่อกฎ)"}`],
    ["rule", `§lกฎของโซน\n§e${label(RULES, z.rule)}`],
    ["r", `§lรัศมี\n§e${z.r} บล็อก`]
  ];
  if (z.rule === "time_limit") rows.push(["value", `§lอยู่ในโซนได้นาน\n§e${z.value} วินาที`]);
  rows.push(
    ["punish", `§lบทลงโทษ\n§e${label(PUNISH, z.punish)}`],
    ["time", `§lช่วงเวลาที่กฎทำงาน\n§e${label(TIMES, z.time)}`],
    ["enter", `§lข้อความตอนเดินเข้าโซน\n${z.enter ? `§f${z.enter}` : "§7(ว่าง = บอกชื่อกฎ)"}`],
    ["violate", `§lข้อความตอนทำผิด\n${z.violate ? `§f${z.violate}` : "§7(ว่าง = ข้อความเริ่มต้น)"}`],
    ["on", `§lสถานะโซน: ${onOffText(z.on)}\n§7แตะเพื่อสลับ`]
  );
  const form = new ActionFormData().title(`§l${zone ? "แก้ไขโซนกฎ" : "สร้างโซนกฎ"}${HORROR_FLAG}`)
    .body("§fแตะแต่ละแถวเพื่อเปลี่ยนค่า แล้วกด §aบันทึกโซน");
  rows.forEach(([, t]) => form.button(t));
  form.button("§l§aบันทึกโซน");
  form.button("§7ยกเลิก");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const i = r.selection;
  if (i === rows.length) return saveZone(player, zone, z);
  if (i > rows.length) return;
  const key = rows[i][0];
  if (key === "rule") {
    const v = await pick(player, "กฎของโซน", RULES.map((x) => x[1]), idx(RULES, z.rule));
    if (v !== undefined) z.rule = RULES[v][0];
  } else if (key === "r") {
    const v = await pick(player, "รัศมีของโซน", RADII.map((n) => `${n} บล็อก`), RADII.indexOf(z.r));
    if (v !== undefined) z.r = RADII[v];
  } else if (key === "value") {
    const v = await pick(player, "อยู่ในโซนได้นาน", SECONDS.map((n) => `${n} วินาที`), SECONDS.indexOf(Number(z.value)));
    if (v !== undefined) z.value = String(SECONDS[v]);
  } else if (key === "punish") {
    const v = await pick(player, "บทลงโทษ", PUNISH.map((x) => x[1]), idx(PUNISH, z.punish));
    if (v !== undefined) z.punish = PUNISH[v][0];
  } else if (key === "time") {
    const v = await pick(player, "ช่วงเวลาที่กฎทำงาน", TIMES.map((x) => x[1]), idx(TIMES, z.time));
    if (v !== undefined) z.time = TIMES[v][0];
  } else if (key === "on") {
    z.on = !z.on;
  } else {
    const [title, hint] = TEXTS[key];
    const v = await typeText(player, title, hint, z[key]);
    if (v !== undefined) z[key] = v;
  }
  return editZone(player, zone, z);
}

function saveZone(player, zone, z) {
  if (!z.name) z.name = label(RULES, z.rule);
  if (zone) Object.assign(zone, z);
  else zones.push(z);
  saveZones();
  player.sendMessage(`§a[กฎสยอง] บันทึกโซน "${z.name}" (${label(RULES, z.rule)}, รัศมี ${z.r}, โทษ: ${label(PUNISH, z.punish)})`);
}

async function zoneList(player) {
  const list = zones.filter((z) => z.dim === player.dimension.id).map((z) => ({ z, d: flat(player.location, z) }))
    .sort((a, b) => a.d - b.d).slice(0, 30);
  if (list.length === 0) return player.sendMessage("§7[กฎสยอง] ยังไม่มีโซนในมิตินี้");
  const form = new ActionFormData().title(`§lโซนกฎ${HORROR_FLAG}`).body("§fเรียงจากใกล้ไปไกล");
  for (const { z, d } of list) form.button(`${z.on ? "§l§c" : "§7"}${z.name}\n§f${label(RULES, z.rule)} §7· ${Math.round(d)} ม.`);
  form.button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection >= list.length) return wandMenu(player);
  const z = list[r.selection].z;
  const m = new ActionFormData().title(`§l${z.name}${HORROR_FLAG}`)
    .body(`§7กฎ: §f${label(RULES, z.rule)}\n§7โทษ: §f${label(PUNISH, z.punish)}\n§7รัศมี §f${z.r}§7 · §f${label(TIMES, z.time)}§7 · ${onOffText(z.on)}`)
    .button("§lแก้ไข").button("§lย้ายโซนมาที่ฉันยืน").button("§lวาร์ปไปที่โซน").button("§l§cลบโซน").button("§7« กลับ");
  const a = await show(m, player);
  if (!a || a.canceled) return;
  if (a.selection === 0) return editZone(player, z);
  if (a.selection === 1) {
    Object.assign(z, { dim: player.dimension.id, x: Math.floor(player.location.x) + 0.5, y: Math.floor(player.location.y), z: Math.floor(player.location.z) + 0.5 });
    saveZones();
    return player.sendMessage("§a[กฎสยอง] ย้ายโซนแล้ว");
  }
  if (a.selection === 2) return player.teleport({ x: z.x, y: z.y, z: z.z }, { dimension: world.getDimension(z.dim.replace("minecraft:", "")) });
  if (a.selection === 3) {
    zones = zones.filter((x) => x.id !== z.id);
    saveZones();
    return player.sendMessage("§c[กฎสยอง] ลบโซนแล้ว");
  }
  return zoneList(player);
}

async function help(player) {
  const form = new ActionFormData().title(`§lวิธีใช้อุปกรณ์กฎสยอง${HORROR_FLAG}`).body([
    "§6ไม้เท้ากฎสยอง§f: คลิกขวาเพื่อสร้าง/แก้ไขโซนกฎ ใครอยู่ในโซนแล้วทำผิดกฎจะโดนลงโทษ (ผู้เล่นโหมดสร้างสรรค์ไม่โดน)",
    "§6ป้ายประกาศกฎ§f: วางไว้ให้คนอ่าน แอดมินคลิกขวาที่ป้ายแล้วกด §eแก้ไข§f เพื่อเขียนหัวข้อ กฎทีละข้อ (สูงสุด 20 ข้อ) และข้อความท้ายป้าย",
    "§6รูปปั้นเฝ้ามอง§f: ขยับเข้าหาผู้เล่นเฉพาะตอนไม่มีใครมองมัน ถ้าถึงตัวจะโดนหลอก แอดมินถือไม้เท้าคลิกขวาเพื่อเปิด/ปิด",
    "§fเก็บของที่วางไว้: แอดมินย่อ + คลิกขวา",
    "§fปิดทั้งโหมด: อุปกรณ์ตั้งค่า → Rule of Horror (ปิดแล้วไม่มีเรื่องผิดปกติใดๆ เกิดขึ้น)"
  ].join("\n\n")).button("§7« กลับ");
  const r = await show(form, player);
  if (r && !r.canceled) return wandMenu(player);
}

// ---------------------------------------------------------------- props (board / statue)
function readJson(entity, key, fallback) {
  try {
    const v = entity.getDynamicProperty(key);
    return typeof v === "string" ? JSON.parse(v) : fallback;
  } catch (e) {
    return fallback;
  }
}

const DEFAULT_BOARD = { title: "กฎของสถานที่นี้", lines: ["ห้ามวิ่งในทางเดิน", "ถ้าได้ยินเสียงเคาะสามครั้ง อย่าเปิดประตู", "ถ้าไฟดับ ให้ยืนนิ่งนับถึงสิบ", "ห้ามมองรูปปั้นนานเกินไป... แต่ก็ห้ามละสายตา"], footer: "", numbered: true };
const BOARD_LINES = 20;
const LINE_CHARS = 120;
const PAPER_BTN = "textures/ui/succubi_paper/";

function boardOf(board) {
  const b = { ...DEFAULT_BOARD, ...readJson(board, "succubi:board", DEFAULT_BOARD) };
  b.lines = (Array.isArray(b.lines) ? b.lines : []).map((l) => String(l ?? "")).filter((l) => l.trim() !== "");
  return b;
}

// the paper holds about 11 rows of text: long boards turn into pages
export function paginate(rows, budget = 11, perRow = 44) {
  const pages = [[]];
  let used = 0;
  for (const r of rows) {
    const cost = Math.max(1, Math.ceil(r.replace(/§./g, "").length / perRow));
    if (used + cost > budget && pages[pages.length - 1].length) {
      pages.push([]);
      used = 0;
    }
    pages[pages.length - 1].push(r);
    used += cost;
  }
  return pages;
}

function boardRows(b) {
  const rows = b.lines.map((l, i) => (b.numbered ? `§4${i + 1}.§0 ${l}` : `§0${l}`));
  if (b.footer) rows.push("", `§8${b.footer}`);
  return rows.length ? rows : ["§7(ยังไม่มีกฎ)"];
}

// players: read page by page. Admins: the same paper with an "แก้ไข" button (preview = reading a draft)
async function readBoard(player, board, page = 0, draft = undefined) {
  const b = draft ?? boardOf(board);
  const pages = paginate(boardRows(b));
  const last = page >= pages.length - 1;
  const admin = isAdmin(player) && !draft;
  const form = new ActionFormData()
    .title(`§l${b.title}${PAPER_FLAG}`)
    .body(pages[page].join("\n") + (pages.length > 1 ? `\n\n§r§8— หน้า ${page + 1}/${pages.length} —` : ""));
  const buttons = [];
  if (!last) buttons.push(["next", "§0หน้าถัดไป »", "btn_next"]);
  if (admin) buttons.push(["edit", "§1แก้ไข", "btn_edit"]);
  if (buttons.length < 2) buttons.push(["close", draft ? "§4กลับ" : "§4ปิด", "btn_close"]);
  buttons.forEach(([, text, icon]) => form.button(text, PAPER_BTN + icon));
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const what = buttons[r.selection]?.[0];
  if (what === "next") return readBoard(player, board, page + 1, draft);
  if (what === "edit") return editBoard(player, board);
}

const cut = (v) => String(v ?? "").slice(0, LINE_CHARS);

// editor: every part is a button; nothing is written to the board until "บันทึกป้าย"
async function editBoard(player, board, draft = undefined, note = "") {
  if (!isAdmin(player)) return;
  const b = draft ?? boardOf(board);
  const form = new ActionFormData()
    .title(`§lเขียนป้ายประกาศกฎ${HORROR_FLAG}`)
    .body(`§fแตะแถวเพื่อแก้ แล้วกด §aบันทึกป้าย§f\n§7กฎ ${b.lines.length}/${BOARD_LINES} ข้อ · ข้อละไม่เกิน ${LINE_CHARS} ตัวอักษร${note ? `\n${note}` : ""}`);
  const rows = [["title", `§lหัวข้อ\n§f${b.title}`]];
  b.lines.forEach((l, i) => rows.push([i, `§l${i + 1}. §r§f${l.length > 34 ? l.slice(0, 34) + "..." : l}`]));
  if (b.lines.length < BOARD_LINES) rows.push(["add", "§l§a+ เพิ่มกฎข้อใหม่"]);
  rows.push(
    ["bulk", "§lเขียนทุกข้อในหน้าเดียว\n§7แก้หลายข้อพร้อมกัน"],
    ["footer", `§lข้อความท้ายป้าย\n${b.footer ? `§f${b.footer}` : "§7(ว่าง)"}`],
    ["numbered", `§lเลขหน้าข้อ: ${onOffText(b.numbered)}`],
    ["preview", "§lดูตัวอย่างแบบที่ผู้เล่นเห็น"],
    ["save", "§l§aบันทึกป้าย"],
    ["cancel", "§7ยกเลิก"]
  );
  rows.forEach(([, t]) => form.button(t));
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const key = rows[r.selection][0];
  if (key === "cancel") return;
  if (key === "save") {
    board.setDynamicProperty("succubi:board", JSON.stringify({ title: b.title || "กฎ", lines: b.lines, footer: b.footer, numbered: b.numbered }));
    player.sendMessage("§a[กฎสยอง] บันทึกป้ายแล้ว");
    return readBoard(player, board);
  }
  if (key === "preview") {
    await readBoard(player, board, 0, b);
  } else if (key === "numbered") {
    b.numbered = !b.numbered;
  } else if (key === "title" || key === "footer") {
    const v = await typeText(player, key === "title" ? "หัวข้อป้าย" : "ข้อความท้ายป้าย", key === "title" ? "กฎของสถานที่นี้" : "เช่น ฝ่าฝืนรับผิดชอบเอง", b[key]);
    if (v !== undefined) b[key] = v.trim() || (key === "title" ? "กฎ" : "");
  } else if (key === "add") {
    const v = await typeText(player, `กฎข้อ ${b.lines.length + 1}`, "พิมพ์กฎ", "");
    if (v) b.lines.push(v.trim());
  } else if (key === "bulk") {
    const m = new ModalFormData().title(`§lเขียนกฎทุกข้อ${HORROR_FLAG}`);
    const n = Math.min(BOARD_LINES, b.lines.length + 4);
    for (let i = 0; i < n; i++) m.textField(`กฎข้อ ${i + 1}`, "เว้นว่าง = ไม่มีข้อนี้", b.lines[i] ?? "");
    const a = await show(m, player);
    if (a && !a.canceled) b.lines = a.formValues.map(cut).map((x) => x.trim()).filter((x) => x);
  } else if (typeof key === "number") {
    await editLine(player, b, key);
  }
  return editBoard(player, board, b);
}

async function editLine(player, b, i) {
  const form = new ActionFormData().title(`§lกฎข้อ ${i + 1}${HORROR_FLAG}`).body(`§f${b.lines[i]}`)
    .button("§lแก้ข้อความ").button("§lเลื่อนขึ้น").button("§lเลื่อนลง").button("§l§cลบข้อนี้").button("§7« กลับ");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) {
    const v = await typeText(player, `กฎข้อ ${i + 1}`, "พิมพ์กฎ", b.lines[i]);
    if (v !== undefined && v.trim()) b.lines[i] = v.trim();
  } else if (r.selection === 1 && i > 0) {
    [b.lines[i - 1], b.lines[i]] = [b.lines[i], b.lines[i - 1]];
  } else if (r.selection === 2 && i < b.lines.length - 1) {
    [b.lines[i + 1], b.lines[i]] = [b.lines[i], b.lines[i + 1]];
  } else if (r.selection === 3) {
    b.lines.splice(i, 1);
  }
}

function pickUp(player, entity) {
  const id = entity.typeId;
  entity.remove();
  const stack = new ItemStack(`${id}_placer`, 1);
  const left = player.getComponent("minecraft:inventory")?.container?.addItem(stack);
  if (left) player.dimension.spawnItem(left, player.location);
  player.sendMessage("§e[กฎสยอง] เก็บเข้ากระเป๋าแล้ว");
}

function whoUsed(entity) {
  try {
    const near = entity.dimension.getPlayers({ location: entity.location, maxDistance: 10 });
    for (const p of near) {
      try {
        if (p.getEntitiesFromViewDirection({ maxDistance: 10 }).some((hit) => hit.entity?.id === entity.id)) return p;
      } catch (e) {}
    }
    return entity.dimension.getPlayers({ location: entity.location, closest: 1, maxDistance: 10 })[0];
  } catch (e) {
    return undefined;
  }
}

const lastUse = new Map();
function useProp(player, entity, pickup) {
  if (!player || !entity) return;
  const now = system.currentTick;
  if (now - (lastUse.get(player.id) ?? -100) < 10) return;
  lastUse.set(player.id, now);
  const admin = isAdmin(player);
  const wand = held(player)?.typeId === WAND;
  system.run(() => {
    try {
      if (pickup && admin) return pickUp(player, entity);
      if (entity.typeId === BOARD) return readBoard(player, entity).catch(() => {});
      if (entity.typeId === STATUE) {
        if (admin && wand) {
          const on = entity.getDynamicProperty("succubi:active") !== false;
          entity.setDynamicProperty("succubi:active", !on);
          return player.sendMessage(`§e[กฎสยอง] รูปปั้น: ${!on ? "§aทำงาน" : "§cหยุด"}`);
        }
        return player.onScreenDisplay.setActionBar("§7หินเย็นเฉียบ... แต่คุณรู้สึกว่ามันเพิ่งขยับ");
      }
    } catch (e) {}
  });
}

// ---------------------------------------------------------------- watcher statues
let statues = [];
function refreshProps() {
  statues = [];
  for (const d of DIMS) {
    try {
      statues.push(...world.getDimension(d).getEntities({ type: STATUE }));
    } catch (e) {}
  }
}

function watched(statue, players) {
  const at = { x: statue.location.x, y: statue.location.y + 1.2, z: statue.location.z };
  for (const p of players) {
    const eye = p.getHeadLocation();
    const v = { x: at.x - eye.x, y: at.y - eye.y, z: at.z - eye.z };
    const len = Math.hypot(v.x, v.y, v.z) || 1;
    if (len > 40) continue;
    const d = p.getViewDirection();
    if ((v.x * d.x + v.y * d.y + v.z * d.z) / len > 0.77) return true; // within ~40 degrees of where they look
  }
  return false;
}

function passable(dim, pos) {
  try {
    const b = dim.getBlock(pos);
    return !b || b.isAir || b.isLiquid || /grass|flower|snow_layer|fern|vine|carpet|torch|button|rail|sapling|wheat|carrots|potatoes/.test(b.typeId);
  } catch (e) {
    return false;
  }
}

const statueCool = new Map();
function statueTick() {
  if (!horrorOn()) return;
  for (const s of statues) {
    try {
      if (!s.isValid()) continue;
      if (s.getDynamicProperty("succubi:active") === false) continue;
      if (!s.getDynamicProperty("succubi:home")) s.setDynamicProperty("succubi:home", JSON.stringify(s.location));
      if ((statueCool.get(s.id) ?? 0) > system.currentTick) continue;
      const players = s.dimension.getPlayers({ location: s.location, maxDistance: 24 }).filter(survival);
      if (players.length === 0 || watched(s, players)) continue;
      let target = players[0];
      for (const p of players) if (dist(p.location, s.location) < dist(target.location, s.location)) target = p;
      const gap = flat(target.location, s.location);
      if (gap < 1.7) {
        jumpscare(target, 20);
        target.applyDamage(6);
        const home = readJson(s, "succubi:home", s.location);
        s.teleport(home);
        statueCool.set(s.id, system.currentTick + 200);
        continue;
      }
      const step = 0.55;
      const nx = s.location.x + ((target.location.x - s.location.x) / gap) * step;
      const nz = s.location.z + ((target.location.z - s.location.z) / gap) * step;
      let ny = s.location.y;
      const fy = Math.floor(ny);
      const feet = { x: Math.floor(nx), y: fy, z: Math.floor(nz) };
      if (!passable(s.dimension, feet)) {
        if (passable(s.dimension, { ...feet, y: fy + 1 }) && passable(s.dimension, { ...feet, y: fy + 2 })) ny = fy + 1;
        else continue;
      } else if (!passable(s.dimension, { ...feet, y: fy + 1 })) continue;
      else if (passable(s.dimension, { ...feet, y: fy - 1 })) ny = passable(s.dimension, { ...feet, y: fy - 2 }) ? ny : fy - 1;
      s.teleport({ x: nx, y: ny, z: nz }, { facingLocation: { x: target.location.x, y: ny, z: target.location.z } });
    } catch (e) {}
  }
}

// ---------------------------------------------------------------- init
export function initHorror() {
  loadZones();
  refreshProps();
  world.afterEvents.itemUse.subscribe((event) => {
    const id = event.itemStack?.typeId;
    const player = event.source;
    if (id === WAND) system.run(() => wandMenu(player).catch(() => {}));
  });
  world.afterEvents.playerInteractWithEntity.subscribe((event) => {
    if (PROPS.includes(event.target?.typeId)) useProp(event.player, event.target, event.player.isSneaking);
  });
  try {
    world.afterEvents.dataDrivenEntityTrigger.subscribe(
      (event) => {
        if (!PROPS.includes(event.entity?.typeId)) return;
        const player = whoUsed(event.entity);
        if (player) useProp(player, event.entity, event.eventId === "succubi:prop_pickup");
      },
      { eventTypes: ["succubi:prop_use", "succubi:prop_pickup"] }
    );
  } catch (e) {}
  world.afterEvents.entityHitEntity.subscribe((event) => {
    const e = event.hitEntity;
    const p = event.damagingEntity;
    if (!PROPS.includes(e?.typeId) || p?.typeId !== "minecraft:player") return;
    useProp(p, e, p.isSneaking && isAdmin(p));
  });
  world.afterEvents.entitySpawn.subscribe((event) => {
    const e = event.entity;
    if (!PROPS.includes(e?.typeId)) return;
    system.runTimeout(() => {
      try {
        const p = e.dimension.getPlayers({ location: e.location, closest: 1, maxDistance: 12 })[0];
        if (p) e.teleport(e.location, { facingLocation: { x: p.location.x, y: e.location.y, z: p.location.z } });
        if (e.typeId === STATUE) e.setDynamicProperty("succubi:home", JSON.stringify(e.location));
        refreshProps();
      } catch (err) {}
    }, 2);
  });
  // rules broken by actions
  world.afterEvents.itemCompleteUse.subscribe((e) => eventRule(e.source, "no_eat"));
  world.afterEvents.playerPlaceBlock.subscribe((e) => eventRule(e.player, "no_build"));
  world.afterEvents.playerBreakBlock.subscribe((e) => eventRule(e.player, "no_build"));
  world.afterEvents.playerInteractWithBlock.subscribe((e) => {
    if (e.block?.typeId?.includes("door") || e.block?.typeId?.includes("gate")) eventRule(e.player, "no_door");
  });
  const chat = world.beforeEvents.chatSend;
  if (chat) chat.subscribe((e) => system.run(() => eventRule(e.sender, "no_chat")));
  world.afterEvents.playerLeave.subscribe((e) => state.delete(e.playerId));

  system.runInterval(() => {
    try {
      zoneTick();
    } catch (e) {}
    try {
      drawZones();
    } catch (e) {}
  }, 10);
  system.runInterval(statueTick, 4);
  system.runInterval(refreshProps, 100);
}
