import { world, system, ItemStack, MolangVariableMap } from "@minecraft/server";
import { enabled } from "./settings_store.js";
import { getSanity, addSanity } from "./sanity.js";

// Don't Starve: when sanity falls below 15 % the shadows stop pretending (settings: สติ -> เงากลายเป็นของจริง,
// and only while Rule of Horror is on). One shadow comes for each such player and hunts only players who have
// lost their mind (tag succubi_insane).
//
// Only the mad can see it. The body in the world (succubi:shadow_creature) is invisible - no model, the
// invisibility effect (no ground shadow), no sounds, no loot. Its shape is drawn every few ticks with
// Player.spawnParticle, which only that player sees (RP particles/succubi: smoke body, red eyes, wisps, embers).
// Hits are counted here (the body has lots of real health), so it never plays the game's death smoke that
// everyone would see: at 0 it bursts apart for the mad, the killer gets +15 sanity and nightmare fuel in hand.
// Once its player is back above 20 % (or leaves, changes dimension, gets far away) it melts away.
const TYPE = "succubi:shadow_creature";
const TAG = "succubi_insane";
const OWNER = "succubi:shadow_owner";
const HP_PROP = "succubi:shadow_hp";
const INSANE = 15;
const CALM = 20; // hysteresis: in at < 15, out at >= 20
const SHADOW_HP = 30;
const KILL_GAIN = 15;
const FUEL = "succubi:nightmare_fuel";
const DRAW_TICKS = 3;
const DIMENSIONS = ["overworld", "nether", "the_end"];
const nextSpawn = new Map(); // player id -> tick

const rand = (a, b) => a + Math.random() * (b - a);
const active = () => enabled("sanity") && enabled("shadows_real") && enabled("horror");

function exempt(player) {
  try {
    const mode = String(player.getGameMode()).toLowerCase();
    return mode === "creative" || mode === "spectator";
  } catch (e) {
    return false;
  }
}

function sound(player, id, volume = 1, pitch = 1) {
  try {
    player.playSound(id, { volume, pitch });
  } catch (e) {}
}

// ---------------------------------------------------------------- drawing (only for the mad)
function viewersOf(entity) {
  try {
    return entity.dimension
      .getPlayers({ location: entity.location, maxDistance: 48 })
      .filter((p) => p.hasTag(TAG));
  } catch (e) {
    return [];
  }
}

function vars(values) {
  const m = new MolangVariableMap();
  for (const [k, v] of Object.entries(values)) m.setFloat(`variable.${k}`, v);
  return m;
}

function show(viewers, effect, at, values) {
  const map = values ? vars(values) : undefined;
  for (const p of viewers) {
    try {
      p.spawnParticle(effect, at, map);
    } catch (e) {}
  }
}

// A tall thin figure of smoke: long dangling arms, a head with two red eyes, legs that melt into mist.
// It faces the player it hunts, sways a little and flickers now and then.
export function drawShadow(entity, viewers, tick) {
  if (!viewers.length) return;
  const l = entity.location;
  const owner = world.getAllPlayers().find((p) => p.id === entity.getDynamicProperty(OWNER)) ?? viewers[0];
  let fx = owner.location.x - l.x;
  let fz = owner.location.z - l.z;
  const len = Math.hypot(fx, fz) || 1;
  fx /= len;
  fz /= len;
  const rx = fz;
  const rz = -fx; // right hand side
  const t = tick / 20;
  const sway = Math.sin(t * 1.7) * 0.06;
  const at = (side, up, fwd = 0) => ({
    x: l.x + rx * (side + sway * up * 0.4) + fx * fwd,
    y: l.y + up,
    z: l.z + rz * (side + sway * up * 0.4) + fz * fwd
  });
  show(viewers, "succubi:shadow_body", at(0, 0.45), { hx: 0.15, hy: 0.42, hz: 0.15, n: 5 }); // legs into mist
  show(viewers, "succubi:shadow_body", at(0, 1.2), { hx: 0.18, hy: 0.32, hz: 0.12, n: 8 }); // chest
  show(viewers, "succubi:shadow_body", at(0, 1.76 + Math.sin(t * 2.3) * 0.02), { hx: 0.11, hy: 0.12, hz: 0.11, n: 4 });
  for (const side of [-1, 1]) {
    const swing = Math.sin(t * 1.3 + side) * 0.05;
    show(viewers, "succubi:shadow_body", at(side * (0.34 + swing), 1.02), { hx: 0.05, hy: 0.42, hz: 0.05, n: 4 });
  }
  const blink = tick % 70 < 4; // the eyes close now and then
  if (!blink) {
    for (const side of [-1, 1]) show(viewers, "succubi:shadow_eye", at(side * 0.065, 1.8, 0.14));
  }
  if (tick % 6 === 0) show(viewers, "succubi:shadow_wisp", at(0, 0));
  if (tick % 9 === 0) show(viewers, "succubi:shadow_ember", at(0, 1.1));
}

// ---------------------------------------------------------------- the invisible body
function vanish(entity, burst = true) {
  try {
    if (burst) {
      const viewers = viewersOf(entity);
      show(viewers, "succubi:shadow_burst", entity.location);
      for (const p of viewers) sound(p, "mob.endermen.portal", 0.7, 0.5);
    }
    entity.remove(); // no death animation, no smoke for the sane
  } catch (e) {}
}

function hide(entity) {
  try {
    entity.addEffect("invisibility", 20 * 60, { amplifier: 0, showParticles: false });
  } catch (e) {}
}

function isAir(dim, at) {
  try {
    const b = dim.getBlock(at);
    return !b || b.isAir;
  } catch (e) {
    return false;
  }
}

// somewhere 10-16 blocks away with room to stand
function spawnSpot(player) {
  const dim = player.dimension;
  const l = player.location;
  for (let attempt = 0; attempt < 8; attempt++) {
    const a = Math.random() * Math.PI * 2;
    const r = rand(10, 16);
    const at = { x: l.x + Math.cos(a) * r, y: l.y, z: l.z + Math.sin(a) * r };
    for (const dy of [0, 1, -1, 2, -2, 3, -3]) {
      const p = { x: Math.floor(at.x) + 0.5, y: Math.floor(at.y) + dy, z: Math.floor(at.z) + 0.5 };
      if (isAir(dim, p) && isAir(dim, { x: p.x, y: p.y + 1, z: p.z }) && !isAir(dim, { x: p.x, y: p.y - 1, z: p.z })) return p;
    }
  }
  return undefined;
}

function spawnFor(player) {
  const at = spawnSpot(player);
  if (!at) return;
  try {
    const e = player.dimension.spawnEntity(TYPE, at);
    e.setDynamicProperty(OWNER, player.id);
    e.setDynamicProperty(HP_PROP, SHADOW_HP);
    hide(e);
    player.spawnParticle("succubi:shadow_gather", at);
    sound(player, "succubi.whisper", 0.9, 0.7);
  } catch (e) {}
}

function ownedBy(player) {
  try {
    return player.dimension
      .getEntities({ type: TYPE, location: player.location, maxDistance: 64 })
      .filter((e) => e.getDynamicProperty(OWNER) === player.id).length;
  } catch (e) {
    return 0;
  }
}

function reward(killer) {
  try {
    addSanity(killer, KILL_GAIN);
    const leftover = killer.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(FUEL, 1));
    if (leftover) killer.dimension.spawnItem(leftover, killer.location);
    killer.onScreenDisplay.setActionBar("§dเงาสลายไป... ใจชื้นขึ้นมาหน่อย §8(+ เชื้อเพลิงฝันร้าย)");
  } catch (e) {}
}

// A hit on the body: count it here, keep the real health full, let the mad see it flinch
export function hitShadow(event) {
  const e = event.hurtEntity;
  if (e?.typeId !== TYPE || !(event.damage > 0)) return;
  try {
    const left = (Number(e.getDynamicProperty(HP_PROP)) || SHADOW_HP) - event.damage;
    const health = e.getComponent("minecraft:health");
    if (health) health.setCurrentValue(health.effectiveMax);
    if (left > 0) {
      e.setDynamicProperty(HP_PROP, left);
      show(viewersOf(e), "succubi:shadow_wisp", { x: e.location.x, y: e.location.y + 1, z: e.location.z });
      return;
    }
    const killer = event.damageSource?.damagingEntity;
    if (killer?.typeId === "minecraft:player") reward(killer);
    vanish(e);
  } catch (err) {}
}

// ---------------------------------------------------------------- per second: who is mad, who gets a shadow
function tick() {
  const now = system.currentTick;
  const on = active();
  const players = world.getAllPlayers();
  const byId = new Map(players.map((p) => [p.id, p]));

  for (const p of players) {
    try {
      const sanity = getSanity(p);
      const was = p.hasTag(TAG);
      const insane = on && !exempt(p) && sanity < (was ? CALM : INSANE);
      if (insane && !was) {
        p.addTag(TAG);
        nextSpawn.set(p.id, now + Math.floor(rand(200, 400)));
        sound(p, "succubi.tinnitus", 0.8, 0.8);
        p.onScreenDisplay.setActionBar("§5เงาพวกนั้น... มันขยับได้");
      } else if (!insane && was) {
        p.removeTag(TAG);
        nextSpawn.delete(p.id);
      }
      if (insane && now >= (nextSpawn.get(p.id) ?? 0)) {
        nextSpawn.set(p.id, now + Math.floor(rand(300, 600)));
        if (ownedBy(p) < 1) spawnFor(p); // one shadow per player
      }
    } catch (e) {}
  }

  for (const id of DIMENSIONS) {
    let list = [];
    try {
      list = world.getDimension(id).getEntities({ type: TYPE });
    } catch (e) {}
    for (const e of list) {
      try {
        const owner = byId.get(e.getDynamicProperty(OWNER));
        const l = e.location;
        const far = owner && Math.hypot(owner.location.x - l.x, owner.location.y - l.y, owner.location.z - l.z) > 56;
        if (!on || !owner || !owner.hasTag(TAG) || owner.dimension.id !== e.dimension.id || far) vanish(e);
        else if (now % 600 < 20) hide(e); // keep the invisibility going
      } catch (e2) {}
    }
  }
}

function draw() {
  const now = system.currentTick;
  for (const id of DIMENSIONS) {
    let list = [];
    try {
      list = world.getDimension(id).getEntities({ type: TYPE });
    } catch (e) {}
    for (const e of list) {
      try {
        drawShadow(e, viewersOf(e), now);
      } catch (err) {}
    }
  }
}

export function initShadows() {
  world.afterEvents.entityHurt.subscribe(hitShadow, { entityTypes: [TYPE] });
  world.afterEvents.playerLeave.subscribe((e) => nextSpawn.delete(e.playerId));
  system.runInterval(() => {
    try {
      tick();
    } catch (e) {}
  }, 20);
  system.runInterval(() => {
    try {
      draw();
    } catch (e) {}
  }, DRAW_TICKS);
}
