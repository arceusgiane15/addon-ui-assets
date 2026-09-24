// Minimal stand-in for @minecraft/server / @minecraft/server-ui so the scripts can be imported and
// exercised in Node. Anything not modelled is a "deep proxy" that swallows calls.
const deep = () => {
  const fn = function () {};
  return new Proxy(fn, {
    get(t, k) {
      if (k === Symbol.toPrimitive) return () => "";
      if (k === "then") return undefined;
      if (!(k in t)) t[k] = deep();
      return t[k];
    },
    apply() { return deep(); },
    construct() { return deep(); }
  });
};
export const subs = {};
const events = (kind) => new Proxy({}, {
  get(t, name) {
    return { subscribe: (fn) => { (subs[`${kind}.${name}`] ||= []).push(fn); return fn; }, unsubscribe() {} };
  }
});
const dyn = new Map();
export const timers = [];
export const world = {
  afterEvents: events("after"), beforeEvents: events("before"),
  getDynamicProperty: (k) => dyn.get(k), setDynamicProperty: (k, v) => dyn.set(k, v),
  getAllPlayers: () => globalThis.__players ?? [], sendMessage() {},
  scoreboard: { getObjective: () => undefined, addObjective: () => deep() },
  getDimension: () => ({ getEntities: () => [], getPlayers: () => [] }),
  getTimeOfDay: () => 1000, setTimeOfDay() {}, getDay: () => 1, getAbsoluteTime: () => 1000,
  getDefaultSpawnLocation: () => ({ x: 0, y: 64, z: 0 })
};
export const system = {
  currentTick: 0, afterEvents: events("system"), beforeEvents: events("sysbefore"),
  // one-shot timers run soon (so awaited waits resolve); intervals are only recorded
  run: (fn) => setTimeout(fn, 0), runTimeout: (fn, t) => setTimeout(fn, 0),
  runInterval: (fn, t) => (timers.push([t, fn, "interval"]), timers.length), clearRun() {}
};
export class ItemStack { constructor(typeId, amount = 1) { this.typeId = typeId; this.amount = amount; this.lore = []; } setLore(l) { this.lore = l; } getLore() { return this.lore; } }
export const EquipmentSlot = { Head: "Head", Chest: "Chest", Legs: "Legs", Feet: "Feet", Mainhand: "Mainhand", Offhand: "Offhand" };
export const ItemLockMode = { none: "none", slot: "slot", inventory: "inventory" };
export const ItemTypes = { get: (id) => (globalThis.__itemTypes ?? []).includes(id) ? { id } : undefined };
export const GameMode = { survival: "survival", creative: "creative", adventure: "adventure", spectator: "spectator" };
export const EntityDamageCause = deep();
export default { world, system };
