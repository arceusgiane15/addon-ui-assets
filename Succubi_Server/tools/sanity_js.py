SANITY_JS = r'''import { world, system } from "@minecraft/server";
import { runAs } from "./cmd.js";
import { SANITY_BY_ID, TEDDY_ID } from "./sanity_values.js";

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

export const addSanity = (player, delta) => setSanity(player, getSanity(player) + delta);

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
  { id: "zombie", loss: 5, run: (p) => sound(p, "mob.zombie.say", ahead(p, -2), 1, 0.7) }
];
const SHARED = ["thunder", "red_fog", "bells"];

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

function runEvent(player, id) {
  const ev = id ? EVENTS.find((e) => e.id === id) : pick(EVENTS.filter((e) => e.id !== lastEvent.get(player.id)));
  if (!ev) return;
  lastEvent.set(player.id, ev.id);
  try {
    ev.run(player);
  } catch (e) {}
  addSanity(player, -ev.loss);
}

const nextDelay = () => Math.floor(rand(50, 80) * 60); // 50-80 minutes of play
const worldDelay = () => Math.floor(rand(150, 240) * 60); // 2.5-4 hours

// ---------------------------------------------------------------- per second
function tick(player) {
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

  const next = player.getDynamicProperty(NEXT);
  const left = typeof next === "number" ? next - 1 : nextDelay();
  if (left <= 0) {
    runEvent(player);
    player.setDynamicProperty(NEXT, nextDelay());
  } else {
    player.setDynamicProperty(NEXT, left);
  }
}

function worldTick(players) {
  if (players.length === 0) return;
  const next = world.getDynamicProperty(WORLD_NEXT);
  const left = typeof next === "number" ? next - 1 : worldDelay();
  if (left > 0) return world.setDynamicProperty(WORLD_NEXT, left);
  world.setDynamicProperty(WORLD_NEXT, worldDelay());
  const id = pick(SHARED);
  for (const p of players) if (!exempt(p)) runEvent(p, id);
}

export function initSanity() {
  world.afterEvents.itemCompleteUse.subscribe((event) => {
    const gain = SANITY_BY_ID[event.itemStack?.typeId];
    if (event.source?.typeId === "minecraft:player" && gain) addSanity(event.source, gain);
  });

  world.afterEvents.itemUse.subscribe((event) => {
    if (event.itemStack?.typeId !== TEDDY_ID) return;
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
      if (exempt(p)) return;
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
'''
