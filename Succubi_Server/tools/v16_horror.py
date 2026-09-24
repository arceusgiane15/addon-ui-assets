HORROR_JS = r'''import { world, system, ItemStack, EquipmentSlot } from "@minecraft/server";
import { ActionFormData, ModalFormData } from "@minecraft/server-ui";
import { addSanity, runEvent } from "./sanity.js";
import { enabled } from "./settings_store.js";
import { runAs } from "./cmd.js";
import { PAPER_FLAG } from "./books.js";

// Rule of Horror kit (อุปกรณ์กฎสยอง) - for admins building horror maps:
//  rule wand     : create rule zones (break the rule inside the zone -> punishment)
//  rule board    : a notice board players read (admin writes the rules)
//  watcher statue: moves toward players only while nobody is looking at it
//  haunted speaker: plays a creepy sound to players nearby every N seconds
//  ghost bell    : ring -> everyone within 48 blocks hears it and loses a little sanity
export const WAND = "succubi:rule_wand";
export const BELL = "succubi:ghost_bell";
const BOARD = "succubi:rule_board";
const STATUE = "succubi:watcher_statue";
const SPEAKER = "succubi:haunted_speaker";
const PROPS = [BOARD, STATUE, SPEAKER];
const ZONES = "succubi:rule_zones";
const DIMS = ["overworld", "nether", "the_end"];

export const RULES = [
  ["no_sprint", "ห้ามวิ่ง"], ["no_jump", "ห้ามกระโดด"], ["must_sneak", "ต้องย่อตัวตลอด"], ["no_sneak", "ห้ามย่อตัว"],
  ["freeze", "ห้ามขยับตัว (ยืนนิ่ง)"], ["no_light", "ห้ามถือแสงไฟ"], ["no_weapon", "ห้ามถืออาวุธ"], ["no_eat", "ห้ามกินหรือดื่ม"],
  ["no_build", "ห้ามวางหรือทุบบล็อก"], ["no_door", "ห้ามเปิดประตู"], ["time_limit", "ห้ามอยู่เกินเวลา (ตั้งวินาทีในช่องค่า)"],
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
  if (!enabled("rules") || zones.length === 0) return;
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
  if (!enabled("rules") || !player || !survival(player)) return;
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

// ---------------------------------------------------------------- wand screens
async function wandMenu(player) {
  if (!isAdmin(player)) return player.sendMessage("§c[กฎสยอง] ใช้ได้เฉพาะแอดมิน (โหมดสร้างสรรค์ หรือแท็ก succubi_admin)");
  const near = zones.filter((z) => z.dim === player.dimension.id && flat(player.location, z) <= 128).length;
  const form = new ActionFormData()
    .title("§l§4ไม้เท้ากฎสยอง")
    .body(`§7โซนกฎทั้งหมด ${zones.length} โซน (ใกล้ตัว ${near})\n§7ถือไม้เท้านี้ไว้จะเห็นขอบโซนเป็นเปลวไฟ\nอุปกรณ์กฎสยอง: ${enabled("rules") ? "§aเปิด" : "§cปิด"} §7(ปิดได้ที่อุปกรณ์ตั้งค่า)`)
    .button("§l§2สร้างโซนกฎตรงที่ยืน")
    .button("§lโซนใกล้ตัว / แก้ไข")
    .button("§lวิธีใช้อุปกรณ์กฎสยอง")
    .button("§7ปิด");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  if (r.selection === 0) return editZone(player, undefined);
  if (r.selection === 1) return zoneList(player);
  if (r.selection === 2) return help(player);
}

async function editZone(player, zone) {
  const z = zone ?? { id: `z${Date.now().toString(36)}`, name: "", dim: player.dimension.id, x: Math.floor(player.location.x) + 0.5,
    y: Math.floor(player.location.y), z: Math.floor(player.location.z) + 0.5, r: 6, rule: "no_sprint", value: "30",
    punish: "sanity10", time: "always", enter: "", violate: "", on: true };
  const form = new ModalFormData()
    .title(zone ? "§lแก้ไขโซนกฎ" : "§lสร้างโซนกฎ")
    .textField("ชื่อโซน", "เช่น ห้องใต้ดิน", z.name)
    .dropdown("กฎของโซน", RULES.map((x) => x[1]), idx(RULES, z.rule))
    .slider("รัศมี (บล็อก)", 2, 40, 1, z.r)
    .textField("ค่า (กฎจำกัดเวลา = จำนวนวินาที)", "30", String(z.value ?? "30"))
    .dropdown("บทลงโทษเมื่อทำผิด", PUNISH.map((x) => x[1]), idx(PUNISH, z.punish))
    .dropdown("ช่วงเวลาที่กฎทำงาน", TIMES.map((x) => x[1]), idx(TIMES, z.time))
    .textField("ข้อความตอนเดินเข้าโซน (เว้นว่าง = ชื่อกฎ)", "เช่น ห้ามส่งเสียงดัง", z.enter)
    .textField("ข้อความตอนทำผิด (เว้นว่าง = ค่าเริ่มต้น)", "เช่น มันได้ยินคุณแล้ว", z.violate)
    .toggle("เปิดใช้งานโซนนี้", z.on);
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const v = r.formValues;
  Object.assign(z, { name: String(v[0] || label(RULES, RULES[v[1]][0])), rule: RULES[v[1]][0], r: Number(v[2]), value: String(v[3] || "30"),
    punish: PUNISH[v[4]][0], time: TIMES[v[5]][0], enter: String(v[6] ?? ""), violate: String(v[7] ?? ""), on: !!v[8] });
  if (!zone) zones.push(z);
  saveZones();
  player.sendMessage(`§a[กฎสยอง] บันทึกโซน "${z.name}" (${label(RULES, z.rule)}, รัศมี ${z.r}, โทษ: ${label(PUNISH, z.punish)})`);
}

async function zoneList(player) {
  const list = zones.filter((z) => z.dim === player.dimension.id).map((z) => ({ z, d: flat(player.location, z) }))
    .sort((a, b) => a.d - b.d).slice(0, 30);
  if (list.length === 0) return player.sendMessage("§7[กฎสยอง] ยังไม่มีโซนในมิตินี้");
  const form = new ActionFormData().title("§lโซนกฎ").body("§7เรียงจากใกล้ไปไกล");
  for (const { z, d } of list) form.button(`${z.on ? "§4" : "§8"}${z.name}\n§7${label(RULES, z.rule)} · ${Math.round(d)} ม.`);
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const z = list[r.selection]?.z;
  if (!z) return;
  const m = new ActionFormData().title(`§l${z.name}`)
    .body(`§7กฎ: §f${label(RULES, z.rule)}\n§7โทษ: §f${label(PUNISH, z.punish)}\n§7รัศมี ${z.r} · ${label(TIMES, z.time)} · ${z.on ? "§aเปิด" : "§cปิด"}`)
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
  const form = new ActionFormData().title("§lวิธีใช้อุปกรณ์กฎสยอง").body([
    "§6ไม้เท้ากฎสยอง§f: คลิกขวาเพื่อสร้าง/แก้ไขโซนกฎ ใครอยู่ในโซนแล้วทำผิดกฎจะโดนลงโทษ (ผู้เล่นโหมดสร้างสรรค์ไม่โดน)",
    "§6ป้ายประกาศกฎ§f: วางไว้ให้คนอ่าน แอดมินถือไม้เท้าแล้วคลิกขวาที่ป้ายเพื่อเขียนกฎ",
    "§6รูปปั้นเฝ้ามอง§f: ขยับเข้าหาผู้เล่นเฉพาะตอนไม่มีใครมองมัน ถ้าถึงตัวจะโดนหลอก แอดมินถือไม้เท้าคลิกขวาเพื่อเปิด/ปิด",
    "§6ลำโพงหลอน§f: เล่นเสียงหลอนให้คนรอบๆ ทุกกี่วินาทีก็ได้ แอดมินคลิกขวาเพื่อตั้งค่า",
    "§6กระดิ่งเรียกผี§f: แอดมินสั่นแล้วทุกคนในระยะ 48 บล็อกได้ยินและสติลดเล็กน้อย",
    "§7เก็บของที่วางไว้: แอดมินย่อ + คลิกขวา"
  ].join("\n\n")).button("§7ปิด");
  await show(form, player);
}

// ---------------------------------------------------------------- props (board / statue / speaker)
function readJson(entity, key, fallback) {
  try {
    const v = entity.getDynamicProperty(key);
    return typeof v === "string" ? JSON.parse(v) : fallback;
  } catch (e) {
    return fallback;
  }
}

const DEFAULT_BOARD = { title: "กฎของสถานที่นี้", lines: ["ห้ามวิ่งในทางเดิน", "ถ้าได้ยินเสียงเคาะสามครั้ง อย่าเปิดประตู", "ถ้าไฟดับ ให้ยืนนิ่งนับถึงสิบ", "ห้ามมองรูปปั้นนานเกินไป... แต่ก็ห้ามละสายตา"] };

async function readBoard(player, board) {
  const b = readJson(board, "succubi:board", DEFAULT_BOARD);
  const body = b.lines.filter((l) => l).map((l, i) => `§4${i + 1}.§0 ${l}`).join("\n");
  const form = new ActionFormData().title(`§l${b.title}${PAPER_FLAG}`).body(body || "§7(ยังไม่มีกฎ)").button("§4ปิด", "textures/ui/succubi_paper/btn_close");
  await show(form, player);
}

async function editBoard(player, board) {
  const b = readJson(board, "succubi:board", DEFAULT_BOARD);
  const form = new ModalFormData().title("§lเขียนป้ายประกาศกฎ").textField("หัวข้อ", "กฎของสถานที่นี้", b.title);
  for (let i = 0; i < 8; i++) form.textField(`กฎข้อ ${i + 1}`, "เว้นว่างได้", b.lines[i] ?? "");
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const v = r.formValues;
  board.setDynamicProperty("succubi:board", JSON.stringify({ title: String(v[0] || "กฎ"), lines: v.slice(1).map((x) => String(x ?? "")) }));
  player.sendMessage("§a[กฎสยอง] บันทึกป้ายแล้ว");
}

const SOUNDS = [
  ["ambient.cave", "เสียงถ้ำ"], ["mob.warden.heartbeat", "หัวใจเต้น"], ["mob.ghast.moan", "ครวญคราง"], ["mob.ghast.scream", "กรีดร้อง"],
  ["mob.vex.ambient", "หัวเราะเล็กๆ"], ["mob.zombie.say", "ซอมบี้"], ["mob.endermen.stare", "เอนเดอร์แมนจ้อง"], ["block.bell.hit", "ระฆัง"],
  ["mob.zombie.woodbreak", "พังประตู"], ["random.door_open", "ประตูเปิด"], ["step.gravel", "ฝีเท้า"], ["mob.elderguardian.curse", "คำสาป"],
  ["note.harp", "กล่องดนตรี"], ["mob.warden.sniff", "ดมกลิ่น"]
];
const EVERY = [10, 20, 30, 60, 120, 300];
const RADIUS = [8, 16, 24, 32];
const LOSS = [0, 1, 2, 3, 5];
const DEFAULT_SPEAKER = { sound: "ambient.cave", every: 30, radius: 16, loss: 1 };

async function editSpeaker(player, sp) {
  const c = readJson(sp, "succubi:speaker", DEFAULT_SPEAKER);
  const form = new ModalFormData().title("§lตั้งค่าลำโพงหลอน")
    .dropdown("เสียง", SOUNDS.map((s) => s[1]), Math.max(0, SOUNDS.findIndex((s) => s[0] === c.sound)))
    .dropdown("เล่นทุกกี่วินาที", EVERY.map(String), Math.max(0, EVERY.indexOf(c.every)))
    .dropdown("ระยะได้ยิน (บล็อก)", RADIUS.map(String), Math.max(0, RADIUS.indexOf(c.radius)))
    .dropdown("สติลดต่อครั้ง", LOSS.map(String), Math.max(0, LOSS.indexOf(c.loss)));
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const v = r.formValues;
  sp.setDynamicProperty("succubi:speaker", JSON.stringify({ sound: SOUNDS[v[0]][0], every: EVERY[v[1]], radius: RADIUS[v[2]], loss: LOSS[v[3]] }));
  player.sendMessage("§a[กฎสยอง] ตั้งค่าลำโพงแล้ว");
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
      if (entity.typeId === BOARD) return (admin && wand ? editBoard(player, entity) : readBoard(player, entity)).catch(() => {});
      if (entity.typeId === SPEAKER) {
        if (admin) return editSpeaker(player, entity).catch(() => {});
        return player.onScreenDisplay.setActionBar("§7ซ่า... ซ่า... มีเสียงใครบางคนแทรกมา");
      }
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
let speakers = [];
function refreshProps() {
  statues = [];
  speakers = [];
  for (const d of DIMS) {
    try {
      const dim = world.getDimension(d);
      statues.push(...dim.getEntities({ type: STATUE }));
      speakers.push(...dim.getEntities({ type: SPEAKER }));
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
  if (!enabled("rules")) return;
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

// ---------------------------------------------------------------- speakers
const speakerClock = new Map();
function speakerTick() {
  if (!enabled("rules")) return;
  for (const sp of speakers) {
    try {
      if (!sp.isValid()) continue;
      const c = readJson(sp, "succubi:speaker", DEFAULT_SPEAKER);
      const t = (speakerClock.get(sp.id) ?? 0) + 1;
      if (t < c.every) {
        speakerClock.set(sp.id, t);
        continue;
      }
      speakerClock.set(sp.id, 0);
      const l = sp.location;
      for (const p of sp.dimension.getPlayers({ location: l, maxDistance: c.radius })) {
        runAs(p, `playsound ${c.sound} @s ${l.x.toFixed(1)} ${l.y.toFixed(1)} ${l.z.toFixed(1)} 1 ${c.sound === "note.harp" ? 0.7 : 0.85}`);
        if (c.loss > 0 && survival(p) && enabled("sanity")) addSanity(p, -c.loss);
      }
    } catch (e) {}
  }
}

// ---------------------------------------------------------------- bell
function ringBell(player) {
  const last = Number(player.getDynamicProperty("succubi:bell")) || 0;
  if (Date.now() - last < 10000) return player.onScreenDisplay.setActionBar("§7กระดิ่งยังสั่นอยู่...");
  player.setDynamicProperty("succubi:bell", Date.now());
  const l = player.location;
  const admin = isAdmin(player);
  for (const p of player.dimension.getPlayers({ location: l, maxDistance: admin ? 48 : 12 })) {
    runAs(p, `playsound block.bell.hit @s ${l.x.toFixed(1)} ${l.y.toFixed(1)} ${l.z.toFixed(1)} 1 0.5`);
    if (!admin || p.id === player.id || !survival(p)) continue;
    if (enabled("sanity")) addSanity(p, -3);
    p.onScreenDisplay.setActionBar("§7เสียงกระดิ่งดังมาจากที่ไหนสักแห่ง...");
    if (Math.random() < 0.25 && enabled("sanity") && enabled("events")) later(40, () => runEvent(p));
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
    else if (id === BELL) system.run(() => ringBell(player));
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
  system.runInterval(speakerTick, 20);
  system.runInterval(refreshProps, 100);
}
'''
