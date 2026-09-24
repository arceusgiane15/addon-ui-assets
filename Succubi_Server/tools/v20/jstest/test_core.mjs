// Behaviour checks for the core scripts, run in the sandbox made by setup.sh (node test_core.mjs)
import assert from "node:assert/strict";
import { world, system, subs, timers } from "@minecraft/server";

let pass = 0;
const ok = (name) => { pass++; console.log("  ok -", name); };

export function makePlayer(opts = {}) {
  const dyn = new Map();
  const tags = new Set(opts.tags ?? []);
  const p = {
    id: opts.id ?? "-100", name: opts.name ?? "Tester", typeId: "minecraft:player", isValid: () => true,
    location: { x: 0, y: 64, z: 0 }, isSneaking: false,
    mode: opts.mode ?? "survival", titles: [], messages: [], bars: [], events: [], sounds: [],
    hp: opts.hp ?? 100, equipment: opts.equipment ?? {}, effects: opts.effects ?? [],
    getGameMode() { return this.mode; },
    getDynamicProperty: (k) => dyn.get(k), setDynamicProperty: (k, v) => dyn.set(k, v),
    hasTag: (t) => tags.has(t), addTag: (t) => tags.add(t), removeTag: (t) => tags.delete(t), getTags: () => [...tags],
    sendMessage(m) { this.messages.push(m); }, playSound(s) { this.sounds.push(s); },
    triggerEvent(e) { this.events.push(e); },
    getProperty: (k) => opts.props?.[k],
    getEffect(id) { return this.effects.includes(id) ? { typeId: id } : undefined; },
    onScreenDisplay: { setTitle: (t) => p.titles.push(t), setActionBar: (t) => p.bars.push(t), clearTitle() {} },
    getComponent(c) {
      if (c === "minecraft:health") return { currentValue: p.hp, effectiveMax: 200, setCurrentValue: (v) => (p.hp = v) };
      if (c === "minecraft:equippable") return { getEquipment: (s) => p.equipment[s] ? { typeId: p.equipment[s] } : undefined };
      if (c === "minecraft:scale") return { value: 1 };
      return undefined;
    },
    dimension: { id: "minecraft:overworld", getPlayers: () => [], getEntities: () => [], spawnItem() {} }
  };
  return p;
}

const answers = [];
globalThis.__answer = (form) => {
  const a = answers.shift();
  return a === undefined ? { canceled: true } : { canceled: false, selection: a, formValues: [] };
};

await import("./main.js");

// ---------------------------------------------------------------- HUD payload
{
  const { buildPayload } = await import("./succubi/hud.js");
  const p = makePlayer({ hp: 86, equipment: { Chest: "minecraft:iron_chestplate", Head: "minecraft:iron_helmet" } });
  const s = buildPayload(p);
  assert.match(s, /^shud:H17F20T20S20PnX0Y8Z6AyB0C8$/, s);
  ok("payload normal: " + s);
  p.hp = 20; p.effects = ["poison"];
  const low = buildPayload(p);
  assert.match(low, /H04.*Pp.*X0Y2Z0.*!h/, low);
  ok("payload low+poison: " + low);
  const naked = buildPayload(makePlayer({ hp: 100 }));
  assert.ok(naked.includes("An") && !naked.includes("!"), naked);
  ok("payload no armor: " + naked);
}

// ---------------------------------------------------------------- HUD change flashes and status effects
{
  const { buildPayload } = await import("./succubi/hud.js");
  const p = makePlayer({ id: "-150", hp: 100 });
  buildPayload(p, 1000);
  p.hp = 70;
  const hit = buildPayload(p, 1005);
  assert.ok(hit.includes("-h") && hit.includes("G20"), hit);
  ok("hit: red flash + damage trail from the old ring: " + hit);
  p.hp = 60;
  const hit2 = buildPayload(p, 1010);
  assert.ok(hit2.includes("G20"), "trail keeps the level before the first hit: " + hit2);
  ok("combo hits keep one trail");
  const later = buildPayload(p, 1100);
  assert.ok(!later.includes("-h") && !later.includes("G"), later);
  ok("flash and trail clear after 1.5 s");
  p.hp = 75;
  assert.ok(buildPayload(p, 1105).includes("+h"));
  ok("healing pops the heart");
  p.hp = 76;
  assert.ok(!buildPayload(p, 1200).includes("+h"));
  ok("slow natural regen does not flash");
  p.effects = ["regeneration", "absorption", "hunger"];
  const fx = buildPayload(p, 1300);
  assert.ok(fx.includes("Er") && fx.includes("Ea") && fx.includes("Qh"), fx);
  ok("status effects: " + fx);
}

// ---------------------------------------------------------------- height rules
{
  const { openHeightForm } = await import("./height/ui.js");
  const { getHeightCm, lockFor, markFight } = await import("./height/height.js");
  const p = makePlayer({ id: "-200" });
  // +10 (idx 3) -> preview only, then confirm (6), then close (7)
  answers.push(3, 3, 6, 7);
  await openHeightForm(p);
  assert.equal(getHeightCm(p), 200);
  assert.ok(lockFor(p).seconds > 290, "cooldown started");
  ok("player confirm applies 200 cm and starts 5 min cooldown");
  // try again: +1 then confirm -> refused by cooldown
  answers.push(2, 6, 7);
  await openHeightForm(p);
  assert.equal(getHeightCm(p), 200);
  ok("second change refused during cooldown");
  // player range capped at 220
  const q = makePlayer({ id: "-300" });
  answers.push(3, 3, 3, 3, 3, 3, 3, 3, 6, 7);
  await openHeightForm(q);
  assert.equal(getHeightCm(q), 220);
  ok("player capped at 220 cm");
  // fight lock
  const f = makePlayer({ id: "-400" });
  markFight(f);
  answers.push(0, 6, 7);
  await openHeightForm(f);
  assert.equal(getHeightCm(f), 180);
  ok("fight blocks the change");
  // admin free range, no cooldown
  const a = makePlayer({ id: "-500", tags: ["succubi_admin"] });
  answers.push(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 7);
  await openHeightForm(a);
  assert.equal(getHeightCm(a), 20);
  assert.equal(lockFor(a).seconds, 0);
  ok("admin can go to 20 cm with no cooldown");
}

// ---------------------------------------------------------------- shop ownership
{
  const { canPickUp, pickUp } = await import("./succubi/vending.js");
  const owner = makePlayer({ id: "-600", name: "Owner" });
  const other = makePlayer({ id: "-700", name: "Other" });
  const dyn = new Map([["succubi:owner", "-600"], ["succubi:owner_name", "Owner"]]);
  let removed = false;
  const shop = { typeId: "kiosk:ramen_kiosk", isValid: () => !removed, location: { x: 0, y: 0, z: 0 }, dimension: owner.dimension,
    getDynamicProperty: (k) => dyn.get(k), remove: () => (removed = true) };
  assert.equal(canPickUp(other, shop), false);
  pickUp(other, shop);
  assert.equal(removed, false);
  assert.ok(other.bars.some((b) => b.includes("Owner")), other.bars.join());
  ok("non-owner cannot pick up, is told who owns it");
  const legacy = { ...shop, getDynamicProperty: () => undefined };
  assert.equal(canPickUp(owner, legacy), false);
  ok("ownerless (old) shop: admins only");
  assert.equal(canPickUp(owner, shop), true);
  ok("owner can pick up");
}

// ---------------------------------------------------------------- ownership is claimed on placement only
{
  const spawn = subs["after.entitySpawn"];
  const useOn = subs["after.itemUseOn"];
  const placer = makePlayer({ id: "-900", name: "Placer" });
  const mk = () => {
    const dyn = new Map();
    return { typeId: "kiosk:ramen_kiosk", location: { x: 0, y: 64, z: 0 }, isValid: () => true, teleport() {},
      dimension: { getPlayers: () => [placer] }, getDynamicProperty: (k) => dyn.get(k), setDynamicProperty: (k, v) => dyn.set(k, v) };
  };
  const loaded = mk();
  for (const fn of spawn) fn({ entity: loaded, cause: "Loaded" });
  assert.equal(loaded.getDynamicProperty("succubi:owner"), undefined);
  ok("shop loaded with its chunk is not claimed by a bystander");
  for (const fn of useOn) fn({ source: placer, itemStack: { typeId: "kiosk:ramen_kiosk" }, block: { location: { x: 0, y: 63, z: 1 } } });
  const placed = mk();
  for (const fn of spawn) fn({ entity: placed, cause: "Spawned" });
  assert.equal(placed.getDynamicProperty("succubi:owner"), "-900");
  assert.equal(placed.getDynamicProperty("succubi:owner_name"), "Placer");
  ok("placed shop belongs to the player who placed it");
}

// ---------------------------------------------------------------- personal menu has no free items
{
  const { openPersonal } = await import("./succubi/personal.js");
  const p = makePlayer({ id: "-800" });
  globalThis.__shown = [];
  answers.push(0, 99);
  await openPersonal(p);
  assert.ok(p.hasTag("hide_hud"), "HUD toggled off");
  const labels = globalThis.__shown.flatMap((f) => f.buttons.map((b) => b.text)).join("|");
  assert.ok(!/ผ้าพันแผล|ชุบชีวิต|เข็ม/.test(labels), labels);
  ok("personal menu toggles HUD and hands out nothing");
}

console.log(`\n${pass} checks passed`);
