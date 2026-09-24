"""40 more strange events + hooks (amulets / books / blood moon change how often events come and how much they cost)."""

HOOKS_JS = '''// Other systems plug into sanity here without importing each other
//  eventRate(player)  -> multiplier for how fast the next strange event comes (2 = twice as often)
//  eventLoss(player)  -> multiplier for sanity lost to strange events
//  eventBlock(player) -> true = cancel this player's next strange event
export const HOOKS = { eventRate: [], eventLoss: [], eventBlock: [] };

export function product(list, ...args) {
  let m = 1;
  for (const f of list) {
    try {
      const v = f(...args);
      if (typeof v === "number" && v >= 0) m *= v;
    } catch (e) {}
  }
  return m;
}

export function anyTrue(list, ...args) {
  for (const f of list) {
    try {
      if (f(...args)) return true;
    } catch (e) {}
  }
  return false;
}
'''

# inserted into the EVENTS array of sanity.js (before the closing "];")
NEW_EVENTS_JS = r'''
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
    } },
'''

HELPERS_JS = r'''
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
'''

NEW_NAMES = {
    "wither_spawn": "เสียงคำรามใต้ดิน", "elder_curse": "คำสาปจากท้องทะเล", "door_break": "เสียงพังประตู", "chest": "หีบเปิดเอง",
    "doors_toggle": "ประตูขยับเอง", "levitate": "ตัวลอย", "heavy": "ขาหนักอึ้ง", "tremble": "มือสั่น", "sudden_hunger": "หิวกะทันหัน",
    "shadow_circle": "เงาดำล้อมรอบ", "shadow_run": "เงาวิ่งผ่าน", "footprints": "รอยเท้าเดินเข้ามา", "souls": "วิญญาณล่องลอย",
    "green_fog": "หมอกเขียว 45 วิ", "white_fog": "หมอกขาว 1 นาที", "midnight_bells": "นาฬิกาตีเที่ยงคืน", "music_box": "กล่องดนตรี",
    "phantom": "อะไรบินโฉบหัว", "cat_hiss": "แมวขู่", "giggles": "เสียงหัวเราะเล็กๆ", "roar": "เสียงคำรามจากป่า",
    "sniff": "มีอะไรดมกลิ่น", "scream": "เสียงกรีดร้อง", "anvil": "ของหนักตก", "far_blast": "ระเบิดไกลๆ", "hotbar_swap": "ของย้ายที่เอง",
    "name_call": "มีคนเรียกชื่อ", "ghost_player": "ผู้เล่นปริศนา", "fake_death": "ข่าวร้ายปลอม", "whisper_chain": "กระซิบ 3 ครั้ง",
    "lightning_flash": "ฟ้าแลบวาบ", "not_alone": "คุณไม่ได้อยู่คนเดียว", "enderman_scream": "เสียงกรีดแหลม", "spider_crawl": "อะไรไต่เพดาน",
    "drowned": "เสียงคนจมน้ำ", "bones": "กระดูกลั่น", "sculk": "เสียงคลิกใต้พื้น", "dropped": "มีอะไรหล่น", "whine": "หมาหอนไกลๆ",
    "bats": "ค้างคาวแตกฝูง",
}
