// A small stand-in for @minecraft/server so the pack's scripts can be loaded and exercised in Node.
// Only what the scripts touch is here; anything else throws loudly so a missing API shows up in the tests.
const signals = new Map();
function signal(name) {
  if (!signals.has(name)) {
    const subs = [];
    signals.set(name, {
      subs,
      subscribe(fn) {
        subs.push(fn);
        return fn;
      },
      unsubscribe() {}
    });
  }
  return signals.get(name);
}
const events = (prefix) => new Proxy({}, { get: (_, key) => signal(`${prefix}.${String(key)}`) });

export function fire(name, event) {
  for (const fn of signal(name).subs) fn(event);
}

// ---------------------------------------------------------------- system
const timers = [];
export const system = {
  currentTick: 0,
  run(fn) {
    return system.runTimeout(fn, 1);
  },
  runTimeout(fn, ticks = 1) {
    timers.push({ at: system.currentTick + Math.max(1, ticks), fn, every: 0 });
    return timers.length;
  },
  runInterval(fn, ticks = 1) {
    timers.push({ at: system.currentTick + ticks, fn, every: ticks });
    return timers.length;
  },
  clearRun() {},
  afterEvents: events("system.after"),
  beforeEvents: events("system.before")
};
export function advance(ticks) {
  for (let i = 0; i < ticks; i++) {
    system.currentTick++;
    for (const t of timers.filter((x) => x.at === system.currentTick)) {
      t.fn();
      if (t.every) t.at += t.every;
      else t.at = -1;
    }
  }
}

// ---------------------------------------------------------------- blocks
export const BlockTypes = { get: (id) => (String(id).startsWith("minecraft:") ? { id } : undefined), getAll: () => [] };
export class MolangVariableMap {
  constructor() {
    this.values = {};
  }
  setFloat(k, v) {
    this.values[k] = v;
  }
}
export class BlockVolume {
  constructor(from, to) {
    this.from = from;
    this.to = to;
  }
}

// ---------------------------------------------------------------- dimension / world
export class Dimension {
  constructor(id) {
    this.id = `minecraft:${id}`;
    this.lightNear = false;
    this.campfireNear = false;
    this.topY = -64;
    this.spawned = [];
    this.weather = "Clear";
  }
  containsBlock(volume, filter) {
    if (filter.includeTypes.includes("minecraft:torch")) return this.lightNear || this.campfireNear;
    return this.campfireNear;
  }
  getTopmostBlock(xz) {
    return { location: { x: xz.x, y: this.topY, z: xz.z } };
  }
  getBlock(at) {
    return { isAir: at.y >= 70, typeId: at.y >= 70 ? "minecraft:air" : "minecraft:stone", location: at }; // ground at y 69
  }
  getEntities() {
    return this.spawned.filter((e) => e.alive);
  }
  getPlayers() {
    return world.getAllPlayers().filter((p) => p.dimension === this);
  }
  spawnEntity(type, at) {
    const e = new Entity(type, this, { ...at });
    this.spawned.push(e);
    return e;
  }
  spawnParticle() {}
  runCommandAsync(cmd) {
    world.commands.push(cmd);
    return Promise.resolve({});
  }
  setWeather(w) {
    this.weather = w;
  }
}
const dims = { overworld: new Dimension("overworld"), nether: new Dimension("nether"), the_end: new Dimension("the_end") };

class Scoreboard {
  constructor() {
    this.objectives = new Map();
  }
  getObjective(id) {
    return this.objectives.get(id);
  }
  addObjective(id) {
    const scores = new Map();
    const o = {
      id,
      getScore: (who) => scores.get(typeof who === "string" ? who : who.id),
      setScore: (who, v) => scores.set(typeof who === "string" ? who : who.id, v)
    };
    this.objectives.set(id, o);
    return o;
  }
}

export const world = {
  props: new Map(),
  players: [],
  commands: [],
  absoluteTime: 0,
  gameRules: { naturalRegeneration: true, doDayLightCycle: true, playersSleepingPercentage: 100 },
  scoreboard: new Scoreboard(),
  afterEvents: events("world.after"),
  beforeEvents: events("world.before"),
  getDynamicProperty(k) {
    return this.props.get(k);
  },
  setDynamicProperty(k, v) {
    if (v === undefined) this.props.delete(k);
    else this.props.set(k, v);
  },
  getAllPlayers() {
    return this.players;
  },
  getPlayers() {
    return this.players;
  },
  getDimension(id) {
    return dims[String(id).replace("minecraft:", "")];
  },
  getAbsoluteTime() {
    return this.absoluteTime;
  },
  setAbsoluteTime(t) {
    this.absoluteTime = t;
  },
  getTimeOfDay() {
    return this.absoluteTime % 24000;
  },
  setTimeOfDay(t) {
    this.absoluteTime = this.absoluteTime - (this.absoluteTime % 24000) + t;
  },
  getDay() {
    return Math.floor(this.absoluteTime / 24000);
  },
  sendMessage() {},
  playMusic() {},
  getEntity() {
    return undefined;
  }
};

// ---------------------------------------------------------------- entities
let nextId = 1;
export class Entity {
  constructor(typeId, dimension, location) {
    this.typeId = typeId;
    this.id = String(nextId++);
    this.dimension = dimension;
    this.location = location;
    this.props = new Map();
    this.tags = new Set();
    this.alive = true;
    this.events = [];
  }
  isValid() {
    return this.alive;
  }
  getDynamicProperty(k) {
    return this.props.get(k);
  }
  setDynamicProperty(k, v) {
    if (v === undefined) this.props.delete(k);
    else this.props.set(k, v);
  }
  hasTag(t) {
    return this.tags.has(t);
  }
  addTag(t) {
    this.tags.add(t);
    return true;
  }
  removeTag(t) {
    return this.tags.delete(t);
  }
  getTags() {
    return [...this.tags];
  }
  triggerEvent(id) {
    this.events.push(id);
  }
  remove() {
    this.alive = false;
  }
  kill() {
    this.alive = false;
  }
  teleport(at) {
    this.location = { ...at };
  }
  getComponent(id) {
    if (id === "minecraft:health") return (this.health ??= new Health(1000, 1000));
    return undefined;
  }
  getViewDirection() {
    return { x: 0, y: 0, z: 1 };
  }
  matches() {
    return false;
  }
  addEffect(id) {
    this.effects = [...(this.effects ?? []), id];
  }
  getEffect() {
    return undefined;
  }
  applyDamage() {}
}

class Health {
  constructor(value, max) {
    this.currentValue = value;
    this.effectiveMax = max;
    this.effectiveMin = 0;
    this.defaultValue = value;
  }
  setCurrentValue(v) {
    this.currentValue = Math.max(0, Math.min(this.effectiveMax, v));
    return true;
  }
}

export class Player extends Entity {
  constructor(name = "Tester") {
    super("minecraft:player", dims.overworld, { x: 0.5, y: 70, z: 0.5 });
    this.name = name;
    // the group families in player.json: adding an HP group sets max and fills health, like the game does
    this.health = new Health(100, 200);
    this.gameMode = "survival";
    this.isSneaking = false;
    this.isSleeping = false;
    this.isSprinting = false;
    this.rotation = { x: 0, y: 0 };
    this.mainhand = undefined;
    this.music = [];
    this.sounds = [];
    this.particles = [];
    this.items = [];
    this.title = "";
    this.actionbar = "";
    this.onScreenDisplay = {
      setTitle: (t) => (this.title = t),
      setActionBar: (t) => (this.actionbar = t)
    };
    this.camera = {};
  }
  triggerEvent(id) {
    super.triggerEvent(id);
    const m = /^succubi:set_hp_(\d+)$/.exec(id);
    if (m) {
      this.health.effectiveMax = Number(m[1]);
      this.health.currentValue = Number(m[1]);
    }
  }
  getComponent(id) {
    if (id === "minecraft:health") return this.health;
    if (id === "minecraft:inventory")
      return { container: { addItem: (stack) => void this.items.push(stack), size: 36, getItem: () => undefined } };
    if (id === "minecraft:equippable")
      return { getEquipment: (slot) => (slot === "Mainhand" && this.mainhand ? { typeId: this.mainhand } : undefined) };
    return undefined;
  }
  getGameMode() {
    return this.gameMode;
  }
  getRotation() {
    return this.rotation;
  }
  sendMessage() {}
  playSound(id) {
    this.sounds.push(id);
  }
  spawnParticle(id, at, vars) {
    this.particles.push([id, at, vars]);
  }
  playMusic(id, options) {
    this.music.push([id, options]);
  }
  stopMusic() {
    this.music.push(["<stop>"]);
  }
  getProperty() {
    return undefined;
  }
}

// ---------------------------------------------------------------- misc
export const EquipmentSlot = { Mainhand: "Mainhand", Offhand: "Offhand", Head: "Head", Chest: "Chest", Legs: "Legs", Feet: "Feet" };
export const ItemLockMode = { none: "none", inventory: "inventory", slot: "slot" };
export const ItemTypes = { get: () => undefined };
export class ItemStack {
  constructor(typeId, amount = 1) {
    this.typeId = typeId;
    this.amount = amount;
  }
  getLore() {
    return [];
  }
  setLore() {}
}
