import { world, system } from "@minecraft/server";
import { runAs } from "./cmd.js";
import { SANITY_BY_ID, TEDDY_ID } from "./sanity_values.js";
import { enabled, num } from "./settings_store.js";
import { HOOKS, product, anyTrue } from "./hooks.js";

// Sanity (สติ) 0-100.
//  up:   tasty food / drinks / some medicine, sleeping (and waking up rested), friends nearby, the tea kiosk's music, hugging a teddy
//  down: getting hit, monsters nearby (bosses a lot), the Nether / End, strange events (~1 per real hour per player,
//        plus a rare one that hits everyone online at once)
//  low sanity only darkens the fog for that player (no blindness).
export const SANITY_MAX = 100;
const PROP = "succubi:sanity";
const NEXT = "succubi:sanity_next"; // seconds of play time until this player's next strange event
const WORLD_NEXT = "succubi:sanity_world_next"; // seconds until the next event for everyone
const FOG_ID = "succubi_sanity";
const EVENT_FOG_ID = "succubi_event";
const FOG_LEVELS = [
  { below: 15, fog: "succubi:sanity_fog_3", text: "§5สติใกล้หลุด... ทุกอย่างมืดไปหมด" },
  { below: 30, fog: "succubi:sanity_fog_2", text: "§5สติเริ่มไม่อยู่กับตัว" },
  { below: 50, fog: "succubi:sanity_fog_1", text: "§dรู้สึกหวาดระแวง..." }
];
const BOSSES = ["minecraft:warden", "minecraft:wither", "minecraft:ender_dragon", "minecraft:elder_guardian"];
const ANIMALS = ["minecraft:cow", "minecraft:pig", "minecraft:sheep", "minecraft:chicken", "minecraft:rabbit", "minecraft:horse", "minecraft:goat", "minecraft:llama"];
const TEA_KIOSK = "kiosk:haruto_tea_kiosk";

const rand = (a, b) => a + Math.random() * (b - a);
const pick = (list) => list[Math.floor(Math.random() * list.length)];
const fogLevel = new Map(); // player id -> index into FOG_LEVELS (-1 = none)
const sleeping = new Map();
const lastEvent = new Map();

export function getSanity(player) {
  const v = player.getDynamicProperty(PROP);
  return typeof v === "number" ? Math.max(0, Math.min(SANITY_MAX, v)) : SANITY_MAX;
}

export function setSanity(player, value) {
  const v = Math.max(0, Math.min(SANITY_MAX, value));
  try {
    player.setDynamicProperty(PROP, v);
  } catch (e) {}
  updateFog(player, v);
  return v;
}

// Every loss / gain is scaled by the base-stat settings (สติลด % / สติฟื้น %)
export const addSanity = (player, delta) =>
  setSanity(player, getSanity(player) + delta * (delta < 0 ? num("sanity_loss") : num("sanity_gain")) / 100);

// Rule of Horror master switch + the random-event switch inside it
export const eventsOn = () => enabled("horror") && enabled("events");

function exempt(player) {
  try {
    const mode = String(player.getGameMode?.()).toLowerCase();
    return mode === "creative" || mode === "spectator";
  } catch (e) {
    return false;
  }
}

function levelOf(v, current) {
  // 2 points of hysteresis so the fog does not flicker at a threshold
  for (let i = 0; i < FOG_LEVELS.length; i++) {
    const limit = FOG_LEVELS[i].below + (current === i ? 2 : 0);
    if (v < limit) return i;
  }
  return -1;
}

function updateFog(player, v, force = false) {
  const before = fogLevel.has(player.id) ? fogLevel.get(player.id) : -2;
  const now = levelOf(v, before);
  if (!force && now === before) return;
  fogLevel.set(player.id, now);
  runAs(player, `fog @s remove ${FOG_ID}`);
  if (now >= 0) {
    runAs(player, `fog @s push ${FOG_LEVELS[now].fog} ${FOG_ID}`);
    if (before === -2 || now < before || before < 0) player.onScreenDisplay.setActionBar(FOG_LEVELS[now].text);
  } else if (before >= 0) {
    player.onScreenDisplay.setActionBar("§aสติกลับมาเป็นปกติ");
  }
}

// ---------------------------------------------------------------- strange events
function ahead(player, dist) {
  const d = player.getViewDirection();
  const len = Math.hypot(d.x, d.z) || 1;
  const l = player.location;
  return { x: l.x + (d.x / len) * dist, y: l.y, z: l.z + (d.z / len) * dist };
}
const fmt = (p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)} ${p.z.toFixed(1)}`;
const sound = (player, id, at, volume = 1, pitch = 1) => runAs(player, `playsound ${id} @s ${fmt(at ?? player.location)} ${volume} ${pitch}`);
const later = (ticks, fn) => system.runTimeout(() => {
  try {
    fn();
  } catch (e) {}
}, ticks);


function particle(player, id, at) {
  try {
    player.dimension.spawnParticle(id, at);
  } catch (e) {}
}

function shadowAt(player, at, ticks) {
  let shadow;
  try {
    const top = player.dimension.getTopmostBlock({ x: at.x, z: at.z });
    if (top && Math.abs(top.location.y + 1 - player.location.y) < 12) at.y = top.location.y + 1;
  } catch (e) {}
  try {
    shadow = player.dimension.spawnEntity("succubi:shadow_figure", at);
    shadow.teleport(at, { facingLocation: player.location });
  } catch (e) {
    return undefined;
  }
  later(ticks, () => shadow.remove());
  return shadow;
}

function toggleDoors(player) {
  const l = player.location;
  let n = 0;
  for (let x = -6; x <= 6 && n < 4; x++) {
    for (let z = -6; z <= 6 && n < 4; z++) {
      for (let y = -1; y <= 2 && n < 4; y++) {
        try {
          const b = player.dimension.getBlock({ x: Math.floor(l.x) + x, y: Math.floor(l.y) + y, z: Math.floor(l.z) + z });
          if (!b || !b.typeId.includes("door")) continue;
          const perm = b.permutation;
          if (perm.getState("upper_block_bit") === true) continue;
          const open = perm.getState("open_bit");
          if (typeof open !== "boolean") continue;
          b.setPermutation(perm.withState("open_bit", !open));
          sound(player, open ? "random.door_close" : "random.door_open", b.location, 1, 0.8);
          n++;
        } catch (e) {}
      }
    }
  }
  if (n === 0) sound(player, "random.door_open", ahead(player, -4), 1, 0.8);
}

function swapHotbar(player) {
  const inv = player.getComponent("minecraft:inventory")?.container;
  if (!inv) return;
  const slots = [0, 1, 2, 3, 4, 5, 6, 7].filter((i) => {
    const it = inv.getItem(i);
    return !it || String(it.lockMode ?? "none") === "none";
  });
  if (slots.length < 2) return;
  const a = pick(slots);
  const b = pick(slots.filter((s) => s !== a));
  const ia = inv.getItem(a);
  const ib = inv.getItem(b);
  inv.setItem(a, ib);
  inv.setItem(b, ia);
  sound(player, "random.pop", undefined, 0.5, 0.5);
}

const EVENTS = [
  { id: "thunder", loss: 6, run: (p) => {
      sound(p, "ambient.weather.thunder", ahead(p, 18), 1, 0.9);
      runAs(p, "camerashake add @s 0.25 1.5 positional");
      p.onScreenDisplay.setActionBar("§7ฟ้าผ่าลงมาใกล้ๆ ทั้งที่ฟ้าโปร่ง...");
    } },
  { id: "footsteps", loss: 5, run: (p) => {
      for (let i = 0; i < 6; i++) later(i * 8, () => sound(p, "step.gravel", ahead(p, -2.5 - i * 0.2), 0.9, 0.8));
      later(50, () => p.onScreenDisplay.setActionBar("§7...มีใครเดินตามมาหรือเปล่า"));
    } },
  { id: "knock", loss: 5, run: (p) => {
      for (let i = 0; i < 3; i++) later(i * 14, () => sound(p, "dig.wood", ahead(p, -4), 1, 0.7));
      later(44, () => p.onScreenDisplay.setActionBar("§7ก๊อก... ก๊อก... ก๊อก..."));
    } },
  { id: "cave", loss: 4, run: (p) => sound(p, "ambient.cave", ahead(p, -3), 1, 0.8) },
  { id: "creeper", loss: 8, run: (p) => sound(p, "random.fuse", ahead(p, -1.5), 1, 1) },
  { id: "stare", loss: 6, run: (p) => sound(p, "mob.endermen.stare", undefined, 0.8, 0.6) },
  { id: "heartbeat", loss: 5, run: (p) => {
      for (let i = 0; i < 6; i++) later(i * 18, () => sound(p, "mob.warden.heartbeat", undefined, 1, 1));
      p.onScreenDisplay.setActionBar("§4หัวใจเต้นแรงผิดปกติ...");
    } },
  { id: "bells", loss: 4, run: (p) => {
      for (let i = 0; i < 3; i++) later(i * 30, () => sound(p, "block.bell.hit", ahead(p, 25), 0.8, 0.5));
      later(20, () => p.onScreenDisplay.setActionBar("§7ระฆังดังมาจากที่ไหนสักแห่ง..."));
    } },
  { id: "moan", loss: 6, run: (p) => sound(p, "mob.ghast.moan", ahead(p, -6), 0.7, 0.5) },
  { id: "shadow", loss: 10, run: (p) => shadowFigure(p) },
  { id: "red_fog", loss: 8, run: (p) => {
      runAs(p, `fog @s push succubi:red_fog ${EVENT_FOG_ID}`);
      p.onScreenDisplay.setActionBar("§4ท้องฟ้ากลายเป็นสีแดง...");
      later(20 * 60, () => runAs(p, `fog @s remove ${EVENT_FOG_ID}`));
    } },
  { id: "whisper", loss: 5, run: (p) => p.sendMessage(`§8§o<???> §7${p.name}... ${pick(["หันหลังมาสิ", "เราเห็นนายนะ", "อย่าไปไหนเลย", "นายลืมอะไรไว้"])}`) },
  { id: "tea_voice", loss: 4, run: (p) => {
      sound(p, "kiosk.haruto_tea.announcement", ahead(p, -8), 0.5, 0.7);
      later(20 * 12, () => runAs(p, "stopsound @s kiosk.haruto_tea.announcement"));
    } },
  { id: "animals", loss: 4, run: (p) => {
      for (const e of p.dimension.getEntities({ location: p.location, maxDistance: 16 })) {
        if (!ANIMALS.includes(e.typeId)) continue;
        const dx = e.location.x - p.location.x, dz = e.location.z - p.location.z, len = Math.hypot(dx, dz) || 1;
        try {
          e.applyKnockback(dx / len, dz / len, 1.4, 0.35);
        } catch (err) {}
      }
      p.onScreenDisplay.setActionBar("§7สัตว์รอบตัวแตกตื่นหนีไปหมด...");
    } },
  { id: "glass", loss: 5, run: (p) => sound(p, "random.glass", ahead(p, -3), 1, 0.8) },
  { id: "growl", loss: 5, run: (p) => {
      sound(p, "mob.wolf.growl", ahead(p, -2), 1, 0.6);
      runAs(p, "camerashake add @s 0.15 1 rotational");
    } },
  { id: "text", loss: 3, run: (p) => p.onScreenDisplay.setActionBar(pick(["§7อย่าหันหลังไป", "§8มันอยู่ใกล้กว่าที่คิด", "§7ได้ยินเสียงนั่นไหม?", "§8มีบางอย่างมองอยู่"])) },
  { id: "zombie", loss: 5, run: (p) => sound(p, "mob.zombie.say", ahead(p, -2), 1, 0.7) },
  { id: "wither_spawn", loss: 8, run: (p) => {
      sound(p, "mob.wither.spawn", ahead(p, -30), 0.35, 0.6);
      later(40, () => p.onScreenDisplay.setActionBar("§7เสียงคำรามก้องมาจากใต้ดิน..."));
    } },
  { id: "elder_curse", loss: 7, run: (p) => {
      sound(p, "mob.elderguardian.curse", undefined, 1, 0.9);
      p.addEffect("mining_fatigue", 20 * 20, { amplifier: 0, showParticles: false });
    } },
  { id: "door_break", loss: 7, run: (p) => {
      for (let i = 0; i < 3; i++) later(i * 16, () => sound(p, "mob.zombie.woodbreak", ahead(p, -5), 0.9, 0.8));
      later(50, () => p.onScreenDisplay.setActionBar("§7มีอะไรพยายามพังประตู..."));
    } },
  { id: "chest", loss: 4, run: (p) => {
      sound(p, "random.chestopen", ahead(p, -3), 1, 0.8);
      later(30, () => sound(p, "random.chestclosed", ahead(p, -3), 1, 0.8));
    } },
  { id: "doors_toggle", loss: 6, run: (p) => {
      toggleDoors(p);
      p.onScreenDisplay.setActionBar("§7ประตูแถวนี้ขยับเอง...");
    } },
  { id: "levitate", loss: 6, run: (p) => {
      p.addEffect("levitation", 30, { amplifier: 0, showParticles: false });
      p.onScreenDisplay.setActionBar("§7มีบางอย่างยกตัวคุณขึ้น...");
    } },
  { id: "heavy", loss: 4, run: (p) => {
      p.addEffect("slowness", 10 * 20, { amplifier: 1, showParticles: false });
      p.onScreenDisplay.setActionBar("§7ขาหนักอึ้งเหมือนมีมือจับไว้...");
    } },
  { id: "tremble", loss: 4, run: (p) => {
      p.addEffect("mining_fatigue", 15 * 20, { amplifier: 0, showParticles: false });
      runAs(p, "camerashake add @s 0.1 3 rotational");
      p.onScreenDisplay.setActionBar("§7มือสั่นไม่หยุด...");
    } },
  { id: "sudden_hunger", loss: 3, run: (p) => {
      p.addEffect("hunger", 8 * 20, { amplifier: 1, showParticles: false });
      p.onScreenDisplay.setActionBar("§7ท้องร้องกะทันหัน ทั้งที่เพิ่งกิน...");
    } },
  { id: "shadow_circle", loss: 12, run: (p) => {
      for (let i = 0; i < 4; i++) {
        const a = (Math.PI / 2) * i + Math.random() * 0.5;
        shadowAt(p, { x: p.location.x + Math.cos(a) * 12, y: p.location.y, z: p.location.z + Math.sin(a) * 12 }, 100);
      }
      sound(p, "mob.endermen.stare", undefined, 0.7, 0.4);
      p.onScreenDisplay.setActionBar("§4คุณถูกล้อมรอบ...");
    } },
  { id: "shadow_run", loss: 8, run: (p) => {
      const d = p.getViewDirection();
      const len = Math.hypot(d.x, d.z) || 1;
      const side = { x: -d.z / len, z: d.x / len };
      const base = ahead(p, 10);
      const from = { x: base.x - side.x * 8, y: base.y, z: base.z - side.z * 8 };
      const shadow = shadowAt(p, from, 40);
      for (let i = 1; i <= 8; i++) later(i * 3, () => shadow?.teleport({ x: from.x + side.x * i * 2, y: from.y, z: from.z + side.z * i * 2 }));
      sound(p, "mob.phantom.swoop", base, 1, 0.6);
      later(30, () => p.onScreenDisplay.setActionBar("§7อะไรวิ่งผ่านไปเมื่อกี้?"));
    } },
  { id: "footprints", loss: 6, run: (p) => {
      for (let i = 0; i < 8; i++) later(i * 6, () => {
        const at = ahead(p, -(10 - i * 1.1));
        particle(p, "minecraft:basic_smoke_particle", { x: at.x, y: p.location.y + 0.1, z: at.z });
        sound(p, "step.stone", at, 0.6, 0.7);
      });
      later(50, () => p.onScreenDisplay.setActionBar("§7รอยเท้าเดินเข้ามาหาคุณ..."));
    } },
  { id: "souls", loss: 5, run: (p) => {
      for (let i = 0; i < 16; i++) {
        const a = (Math.PI * 2 * i) / 16;
        particle(p, "minecraft:soul_particle", { x: p.location.x + Math.cos(a) * 3, y: p.location.y + 1, z: p.location.z + Math.sin(a) * 3 });
      }
      sound(p, "ambient.soulsand_valley.mood", undefined, 0.8, 1);
      p.onScreenDisplay.setActionBar("§bวิญญาณล่องลอยอยู่รอบตัว...");
    } },
  { id: "green_fog", loss: 6, run: (p) => {
      runAs(p, `fog @s push succubi:green_fog ${EVENT_FOG_ID}`);
      p.onScreenDisplay.setActionBar("§2หมอกสีเขียวคลุ้งขึ้นมา...");
      later(20 * 45, () => runAs(p, `fog @s remove ${EVENT_FOG_ID}`));
    } },
  { id: "white_fog", loss: 5, run: (p) => {
      runAs(p, `fog @s push succubi:white_fog ${EVENT_FOG_ID}`);
      p.onScreenDisplay.setActionBar("§fหมอกขาวหนาทึบจนมองไม่เห็นทาง...");
      later(20 * 60, () => runAs(p, `fog @s remove ${EVENT_FOG_ID}`));
    } },
  { id: "midnight_bells", loss: 8, run: (p) => {
      for (let i = 0; i < 12; i++) later(i * 22, () => sound(p, "block.bell.hit", ahead(p, 30), 0.9, 0.45));
      p.onScreenDisplay.setActionBar("§7นาฬิกาตีเที่ยงคืน... ทั้งที่ยังไม่ถึงเวลา");
    } },
  { id: "music_box", loss: 4, run: (p) => {
      [1.19, 1.06, 0.94, 0.89, 0.94, 0.79, 0.71, 0.75].forEach((pitch, i) => later(i * 7, () => sound(p, "note.harp", ahead(p, -2), 0.8, pitch)));
      later(60, () => p.onScreenDisplay.setActionBar("§7เสียงกล่องดนตรีดังมาจากที่ไหนสักแห่ง..."));
    } },
  { id: "phantom", loss: 5, run: (p) => {
      sound(p, "mob.phantom.swoop", { x: p.location.x, y: p.location.y + 4, z: p.location.z }, 1, 0.8);
      p.onScreenDisplay.setActionBar("§7มีอะไรบินโฉบเหนือหัว...");
    } },
  { id: "cat_hiss", loss: 4, run: (p) => sound(p, "mob.cat.hiss", ahead(p, -2), 1, 0.9) },
  { id: "giggles", loss: 5, run: (p) => {
      for (let i = 0; i < 3; i++) later(i * 12, () => sound(p, "mob.vex.ambient", ahead(p, i % 2 ? 3 : -3), 1, 1.3));
      later(40, () => p.onScreenDisplay.setActionBar("§7เสียงหัวเราะเล็กๆ ดังรอบตัว..."));
    } },
  { id: "roar", loss: 7, run: (p) => {
      sound(p, "mob.ravager.roar", ahead(p, 24), 0.8, 0.7);
      p.onScreenDisplay.setActionBar("§7เสียงคำรามดังมาจากป่า...");
    } },
  { id: "sniff", loss: 9, run: (p) => {
      sound(p, "mob.warden.sniff", ahead(p, -1.5), 1, 1);
      later(30, () => sound(p, "mob.warden.heartbeat", undefined, 1, 1));
      later(40, () => p.onScreenDisplay.setActionBar("§4มีบางอย่างกำลังดมกลิ่นคุณ..."));
    } },
  { id: "scream", loss: 8, run: (p) => sound(p, "mob.ghast.scream", ahead(p, -10), 0.8, 0.8) },
  { id: "anvil", loss: 5, run: (p) => {
      sound(p, "random.anvil_land", { x: p.location.x, y: p.location.y + 3, z: p.location.z }, 0.8, 0.6);
      runAs(p, "camerashake add @s 0.3 0.4 positional");
    } },
  { id: "far_blast", loss: 5, run: (p) => {
      sound(p, "random.explode", ahead(p, 40), 0.6, 0.6);
      runAs(p, "camerashake add @s 0.2 1 positional");
      p.onScreenDisplay.setActionBar("§7เสียงระเบิดดังมาจากไกลๆ...");
    } },
  { id: "hotbar_swap", loss: 4, run: (p) => {
      swapHotbar(p);
      p.onScreenDisplay.setActionBar("§7ของในมือ... ย้ายที่เอง?");
    } },
  { id: "name_call", loss: 4, run: (p) => {
      sound(p, "mob.villager.idle", ahead(p, -6), 0.8, 0.6);
      p.onScreenDisplay.setActionBar(`§7"${p.name}..." มีคนเรียกชื่อคุณ`);
    } },
  { id: "ghost_player", loss: 5, run: (p) => {
      p.sendMessage("§e??? เข้าร่วมเกม");
      later(20 * 12, () => p.sendMessage("§8§o<???> §7เห็นเธอแล้วนะ"));
      later(20 * 20, () => p.sendMessage("§e??? ออกจากเกม"));
    } },
  { id: "fake_death", loss: 6, run: (p) => {
      const others = world.getAllPlayers().filter((o) => o.id !== p.id);
      const who = others.length ? pick(others).name : "ใครบางคน";
      p.sendMessage(`§f${who} ถูกบางอย่างลากเข้าไปในความมืด`);
      later(20 * 8, () => p.sendMessage("§8§o...ล้อเล่นน่า"));
    } },
  { id: "whisper_chain", loss: 6, run: (p) => {
      ["ได้ยินไหม", "ข้างหลังนาย", "ช้าไปแล้ว"].forEach((t, i) => later(i * 20 * 8, () => p.sendMessage(`§8§o<???> §7${t}`)));
    } },
  { id: "lightning_flash", loss: 5, run: (p) => {
      runAs(p, "camera @s fade time 0.05 0.1 0.4 color 255 255 255");
      sound(p, "ambient.weather.lightning.impact", ahead(p, 12), 1, 1);
    } },
  { id: "not_alone", loss: 4, run: (p) => {
      p.onScreenDisplay.setActionBar("§4คุณไม่ได้อยู่คนเดียว");
      for (let i = 0; i < 3; i++) later(i * 18, () => sound(p, "mob.warden.heartbeat", undefined, 1, 1));
    } },
  { id: "enderman_scream", loss: 6, run: (p) => sound(p, "mob.endermen.scream", ahead(p, -4), 0.9, 0.8) },
  { id: "spider_crawl", loss: 5, run: (p) => {
      sound(p, "mob.spider.say", { x: p.location.x, y: p.location.y + 2.5, z: p.location.z }, 1, 0.8);
      for (let i = 0; i < 4; i++) later(i * 5, () => sound(p, "mob.spider.step", ahead(p, -1), 0.8, 1));
      p.onScreenDisplay.setActionBar("§7มีอะไรไต่อยู่บนเพดาน...");
    } },
  { id: "drowned", loss: 5, run: (p) => sound(p, "mob.drowned.say", ahead(p, -3), 1, 0.7) },
  { id: "bones", loss: 4, run: (p) => sound(p, "mob.skeleton.say", ahead(p, -2), 1, 0.7) },
  { id: "sculk", loss: 5, run: (p) => {
      for (let i = 0; i < 3; i++) later(i * 10, () => sound(p, "block.sculk_sensor.clicking", ahead(p, -2), 1, 0.9));
      particle(p, "minecraft:sculk_soul_particle", ahead(p, 2));
      p.onScreenDisplay.setActionBar("§3เสียงคลิกดังมาจากใต้พื้น...");
    } },
  { id: "dropped", loss: 3, run: (p) => {
      sound(p, "random.pop", ahead(p, -2), 1, 0.6);
      p.onScreenDisplay.setActionBar("§7มีอะไรหล่นอยู่ข้างหลัง...");
    } },
  { id: "whine", loss: 3, run: (p) => sound(p, "mob.wolf.whine", ahead(p, 18), 0.8, 0.6) },
  { id: "bats", loss: 5, run: (p) => {
      for (let i = 0; i < 3; i++) {
        try {
          p.dimension.spawnEntity("minecraft:bat", { x: p.location.x + rand(-2, 2), y: p.location.y + 2, z: p.location.z + rand(-2, 2) });
        } catch (e) {}
      }
      sound(p, "mob.bat.takeoff", undefined, 1, 0.9);
      p.onScreenDisplay.setActionBar("§7ค้างคาวแตกฝูงออกมาจากความมืด!");
    } }
];
const SHARED = ["thunder", "red_fog", "bells", "midnight_bells", "white_fog", "shadow_circle", "wither_spawn"];
export const EVENT_NAMES = {
  wither_spawn: "เสียงคำรามใต้ดิน",
  elder_curse: "คำสาปจากท้องทะเล",
  door_break: "เสียงพังประตู",
  chest: "หีบเปิดเอง",
  doors_toggle: "ประตูขยับเอง",
  levitate: "ตัวลอย",
  heavy: "ขาหนักอึ้ง",
  tremble: "มือสั่น",
  sudden_hunger: "หิวกะทันหัน",
  shadow_circle: "เงาดำล้อมรอบ",
  shadow_run: "เงาวิ่งผ่าน",
  footprints: "รอยเท้าเดินเข้ามา",
  souls: "วิญญาณล่องลอย",
  green_fog: "หมอกเขียว 45 วิ",
  white_fog: "หมอกขาว 1 นาที",
  midnight_bells: "นาฬิกาตีเที่ยงคืน",
  music_box: "กล่องดนตรี",
  phantom: "อะไรบินโฉบหัว",
  cat_hiss: "แมวขู่",
  giggles: "เสียงหัวเราะเล็กๆ",
  roar: "เสียงคำรามจากป่า",
  sniff: "มีอะไรดมกลิ่น",
  scream: "เสียงกรีดร้อง",
  anvil: "ของหนักตก",
  far_blast: "ระเบิดไกลๆ",
  hotbar_swap: "ของย้ายที่เอง",
  name_call: "มีคนเรียกชื่อ",
  ghost_player: "ผู้เล่นปริศนา",
  fake_death: "ข่าวร้ายปลอม",
  whisper_chain: "กระซิบ 3 ครั้ง",
  lightning_flash: "ฟ้าแลบวาบ",
  not_alone: "คุณไม่ได้อยู่คนเดียว",
  enderman_scream: "เสียงกรีดแหลม",
  spider_crawl: "อะไรไต่เพดาน",
  drowned: "เสียงคนจมน้ำ",
  bones: "กระดูกลั่น",
  sculk: "เสียงคลิกใต้พื้น",
  dropped: "มีอะไรหล่น",
  whine: "หมาหอนไกลๆ",
  bats: "ค้างคาวแตกฝูง",
  thunder: "ฟ้าผ่าข้างหู", footsteps: "เสียงฝีเท้าตามหลัง", knock: "เสียงเคาะ 3 ที", cave: "เสียงถ้ำ", creeper: "ครีปเปอร์ปลอม",
  stare: "เสียงเอนเดอร์แมนจ้อง", heartbeat: "หัวใจเต้นแรง", bells: "ระฆังดังไกลๆ", moan: "เสียงครวญคราง", shadow: "เงาดำยืนมอง",
  red_fog: "หมอกแดง 1 นาที", whisper: "ข้อความกระซิบ ???", tea_voice: "เสียงประกาศร้านชาผี", animals: "สัตว์แตกตื่น",
  glass: "กระจกแตกข้างหลัง", growl: "เสียงคำราม + จอสั่น", text: "ข้อความปริศนา", zombie: "เสียงซอมบี้ข้างหลัง"
};
export const EVENT_IDS = EVENTS.map((e) => e.id);

function shadowFigure(player) {
  const at = ahead(player, rand(16, 22));
  try {
    const top = player.dimension.getTopmostBlock({ x: at.x, z: at.z });
    if (top) at.y = top.location.y + 1;
  } catch (e) {}
  let shadow;
  try {
    shadow = player.dimension.spawnEntity("succubi:shadow_figure", at);
    shadow.teleport(at, { facingLocation: player.location });
  } catch (e) {
    return;
  }
  sound(player, "mob.endermen.stare", at, 0.6, 0.4);
  let t = 0;
  const id = system.runInterval(() => {
    t += 5;
    let gone = t > 120;
    try {
      const dx = shadow.location.x - player.location.x, dz = shadow.location.z - player.location.z;
      if (Math.hypot(dx, dz) < 8) gone = true; // walks up to it -> vanishes
      if (!gone) shadow.teleport(shadow.location, { facingLocation: player.location });
    } catch (e) {
      gone = true;
    }
    if (gone) {
      system.clearRun(id);
      try {
        shadow.remove();
      } catch (e) {}
    }
  }, 5);
}

export function runEvent(player, id) {
  if (!enabled("horror")) return; // Rule of Horror off: nothing strange happens, from any source
  const ev = id ? EVENTS.find((e) => e.id === id) : pick(EVENTS.filter((e) => e.id !== lastEvent.get(player.id)));
  if (!ev) return;
  lastEvent.set(player.id, ev.id);
  try {
    ev.run(player);
  } catch (e) {}
  addSanity(player, -ev.loss * product(HOOKS.eventLoss, player));
}

// about event_minutes of play (±25 %); the one that hits everyone ~3x rarer
const nextDelay = () => Math.floor(num("event_minutes") * rand(0.75, 1.25) * 60);
const worldDelay = () => Math.floor(num("event_minutes") * rand(2.3, 3.7) * 60);

// ---------------------------------------------------------------- per second
function tick(player) {
  if (!enabled("sanity")) {
    if ((fogLevel.get(player.id) ?? -1) >= 0) updateFog(player, SANITY_MAX, true);
    return;
  }
  if (exempt(player)) return;
  const loc = player.location;
  const dim = player.dimension;
  let delta = 0;
  let threat = false;

  let monsters = 0;
  let boss = false;
  try {
    for (const e of dim.getEntities({ location: loc, maxDistance: 32, excludeTypes: ["minecraft:player", "minecraft:item"] })) {
      if (BOSSES.includes(e.typeId)) boss = true;
      else if (e.matches?.({ families: ["monster"] }) && Math.hypot(e.location.x - loc.x, e.location.y - loc.y, e.location.z - loc.z) <= 12) monsters++;
    }
  } catch (e) {}
  if (boss) delta -= 0.8;
  if (monsters > 0) delta -= Math.min(0.6, 0.15 * monsters);
  threat = boss || monsters > 0;

  if (dim.id === "minecraft:nether") delta -= 0.05;
  if (dim.id === "minecraft:the_end") delta -= 0.03;

  if (player.isSleeping) {
    delta += 0.6;
    sleeping.set(player.id, true);
  } else if (sleeping.get(player.id)) {
    sleeping.set(player.id, false);
    delta += 10;
    player.onScreenDisplay.setActionBar("§aนอนเต็มอิ่ม สติกลับมาแล้ว");
  }

  try {
    const friends = dim.getPlayers({ location: loc, maxDistance: 8 }).length - 1;
    if (friends > 0) delta += 0.03;
    if (dim.getEntities({ type: TEA_KIOSK, location: loc, maxDistance: 12 }).length > 0) delta += 0.1;
  } catch (e) {}
  if (!threat && dim.id === "minecraft:overworld") delta += 0.01;

  if (delta !== 0) addSanity(player, delta);

  if (!eventsOn()) return;
  const next = player.getDynamicProperty(NEXT);
  const left = typeof next === "number" ? next - product(HOOKS.eventRate, player) : nextDelay();
  if (left <= 0) {
    if (!anyTrue(HOOKS.eventBlock, player)) runEvent(player);
    player.setDynamicProperty(NEXT, nextDelay());
  } else {
    player.setDynamicProperty(NEXT, left);
  }
}

function worldTick(players) {
  if (players.length === 0 || !enabled("sanity") || !eventsOn()) return;
  const next = world.getDynamicProperty(WORLD_NEXT);
  const left = typeof next === "number" ? next - 1 : worldDelay();
  if (left > 0) return world.setDynamicProperty(WORLD_NEXT, left);
  world.setDynamicProperty(WORLD_NEXT, worldDelay());
  const id = pick(SHARED);
  for (const p of players) if (!exempt(p)) runEvent(p, id);
}

export function initSanity() {
  world.afterEvents.itemCompleteUse.subscribe((event) => {
    if (!enabled("sanity")) return;
    const gain = SANITY_BY_ID[event.itemStack?.typeId];
    if (event.source?.typeId === "minecraft:player" && gain) addSanity(event.source, gain);
  });

  world.afterEvents.itemUse.subscribe((event) => {
    if (event.itemStack?.typeId !== TEDDY_ID || !enabled("sanity")) return;
    const p = event.source;
    const lastHug = Number(p.getDynamicProperty("succubi:teddy_hug")) || 0;
    if (Date.now() - lastHug < 90000) {
      p.onScreenDisplay.setActionBar("§7กอดไปเมื่อกี้แล้ว รอสักพักนะ");
      return;
    }
    p.setDynamicProperty("succubi:teddy_hug", Date.now());
    addSanity(p, 12);
    p.playSound("random.pop");
    p.onScreenDisplay.setActionBar("§dกอดตุ๊กตาแน่นๆ อุ่นใจขึ้นเยอะ");
  });

  world.afterEvents.entityHurt.subscribe(
    (event) => {
      const p = event.hurtEntity;
      if (exempt(p) || !enabled("sanity")) return;
      const fromMonster = event.damageSource?.damagingEntity?.matches?.({ families: ["monster"] }) ?? false;
      addSanity(p, -Math.min(8, event.damage * 0.6 + (fromMonster ? 1 : 0)));
    },
    { entityTypes: ["minecraft:player"] }
  );

  world.afterEvents.playerSpawn.subscribe((event) => {
    const p = event.player;
    if (!p) return;
    if (!event.initialSpawn) setSanity(p, Math.max(getSanity(p), 70));
    fogLevel.delete(p.id);
    runAs(p, `fog @s remove ${EVENT_FOG_ID}`);
    runAs(p, "fog @s remove succubi_bloodmoon"); // the blood moon is gone (v1.1.6): clear a fog left from an old night
    updateFog(p, getSanity(p), true);
  });

  world.afterEvents.playerLeave.subscribe((event) => {
    fogLevel.delete(event.playerId);
    sleeping.delete(event.playerId);
  });

  system.runInterval(() => {
    const players = world.getAllPlayers();
    for (const p of players) {
      try {
        tick(p);
      } catch (e) {}
    }
    try {
      worldTick(players);
    } catch (e) {}
  }, 20);
}
