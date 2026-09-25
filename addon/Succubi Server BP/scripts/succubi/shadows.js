import { world, system } from "@minecraft/server";
import { enabled } from "./settings_store.js";
import { getSanity, addSanity } from "./sanity.js";

// Don't Starve: when sanity falls below 15 % the shadows stop pretending (settings: สติ -> เงากลายเป็นของจริง,
// and only while Rule of Horror is on). Shadow creatures come for that player - one or two, three below 5 % -
// and only hunt players who have lost their mind (tag succubi_insane). Everyone can see and hit them.
// Killing one gives the killer +15 sanity and drops nightmare fuel. Once the player is back above 20 % (or
// leaves, changes dimension, gets far away) that player's shadows melt away.
const TYPE = "succubi:shadow_creature";
const TAG = "succubi_insane";
const OWNER = "succubi:shadow_owner";
const INSANE = 15;
const CALM = 20; // hysteresis: in at < 15, out at >= 20
const KILL_GAIN = 15;
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

function smoke(dim, at) {
  for (let i = 0; i < 6; i++) {
    try {
      dim.spawnParticle("minecraft:large_explosion", { x: at.x + rand(-0.4, 0.4), y: at.y + rand(0.2, 1.8), z: at.z + rand(-0.4, 0.4) });
    } catch (e) {}
  }
}

function vanish(entity) {
  try {
    smoke(entity.dimension, entity.location);
    entity.remove();
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
    smoke(player.dimension, at);
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
        nextSpawn.set(p.id, now + Math.floor(rand(500, 900)));
        if (ownedBy(p) < (sanity < 5 ? 3 : 2)) spawnFor(p);
      }
    } catch (e) {}
  }

  // shadows whose player is sane again, gone, elsewhere or far away melt away
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
      } catch (e2) {}
    }
  }
}

export function initShadows() {
  world.afterEvents.entityDie.subscribe(
    (event) => {
      const killer = event.damageSource?.damagingEntity;
      if (killer?.typeId !== "minecraft:player") return;
      try {
        addSanity(killer, KILL_GAIN);
        killer.onScreenDisplay.setActionBar("§dเงาสลายไป... ใจชื้นขึ้นมาหน่อย");
      } catch (e) {}
    },
    { entityTypes: [TYPE] }
  );
  world.afterEvents.playerLeave.subscribe((e) => nextSpawn.delete(e.playerId));
  system.runInterval(() => {
    try {
      tick();
    } catch (e) {}
  }, 20);
}
