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
      if (c === "minecraft:equippable") return {
        getEquipment: (s) => (typeof p.equipment[s] === "string" ? { typeId: p.equipment[s] } : p.equipment[s]),
        setEquipment: (s, it) => (p.equipment[s] = it)
      };
      if (c === "minecraft:inventory") return { container: { addItem: (it) => ((p.inv ||= []).push(it), undefined) } };
      if (c === "minecraft:scale") return { value: 1 };
      return undefined;
    },
    dimension: { id: "minecraft:overworld", getPlayers: () => [], getEntities: () => [], spawnItem() {} }
  };
  return p;
}

const answers = [];
// an answer is a button index, or { formValues: [...] } for a modal form
globalThis.__answer = (form) => {
  const a = answers.shift();
  if (a === undefined) return { canceled: true };
  if (typeof a === "object") return { canceled: false, selection: a.selection, formValues: a.formValues ?? [] };
  return { canceled: false, selection: a, formValues: [] };
};

await import("./main.js");

// ---------------------------------------------------------------- HUD payload
{
  const { buildPayload } = await import("./succubi/hud.js");
  const p = makePlayer({ hp: 86, equipment: { Chest: "minecraft:iron_chestplate", Head: "minecraft:iron_helmet" } });
  const s = buildPayload(p);
  assert.match(s, /^shud:H17F20T20S20PnX0Y8Z6Of1Mf0Kf0Ot1Mt0Kt0Os1Ms0Ks0AyB0C8Vh4Vf4Vt4Vs4IhIfItIs$/, s);
  ok("payload normal: " + s);
  p.hp = 20; p.effects = ["poison"];
  const low = buildPayload(p);
  assert.match(low, /H04.*Pp.*X0Y2Z0.*Lh/, low);
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
  assert.ok(hit.includes("Dh") && hit.includes("G20"), hit);
  ok("hit: red flash + damage trail from the old ring: " + hit);
  p.hp = 60;
  const hit2 = buildPayload(p, 1010);
  assert.ok(hit2.includes("G20"), "trail keeps the level before the first hit: " + hit2);
  ok("combo hits keep one trail");
  const later = buildPayload(p, 1100);
  assert.ok(!later.includes("Dh") && !later.includes("G"), later);
  ok("flash and trail clear after 1.5 s");
  p.hp = 75;
  assert.ok(buildPayload(p, 1105).includes("Uh"));
  ok("healing pops the heart");
  p.hp = 76;
  assert.ok(!buildPayload(p, 1200).includes("Uh"));
  ok("slow natural regen does not flash");
  p.effects = ["regeneration", "absorption", "hunger"];
  const fx = buildPayload(p, 1300);
  assert.ok(fx.includes("Er") && fx.includes("Ea") && fx.includes("Qh"), fx);
  ok("status effects: " + fx);
  // the UI only reads plain tokens: nothing but letters and digits after the marker, in every state
  for (const payload of [hit, hit2, later, fx, buildPayload(makePlayer({ id: "-151", hp: 5 }), 1400)]) {
    assert.match(payload, /^shud:[A-Za-z0-9]+$/, payload);
  }
  ok("payload tokens are letters and digits only");
  assert.ok(hit.includes("Dh") && !hit.includes("Ih") && hit.includes("If"), "a hit replaces the at-rest token: " + hit);
  assert.ok(later.includes("Ih"), later);
  ok("at-rest token Ix only while no flash is on");
  const { percentDigits } = await import("./succubi/hud.js");
  assert.deepEqual([percentDigits("f", 20, 20), percentDigits("t", 9, 20), percentDigits("s", 3.4, 100), percentDigits("s", 0, 100)],
    ["Of1Mf0Kf0", "Ot0Mt4Kt5", "Os0Ms0Ks3", "Os0Ms0Ks0"]);
  ok("food / thirst / sanity numbers in %");
}

// ---------------------------------------------------------------- icon stages (Don't Starve style)
{
  const { stage, buildPayload } = await import("./succubi/hud.js");
  assert.deepEqual([1, 0.75, 0.6, 0.5, 0.35, 0.3, 0.2, 0.15, 0.1, 0].map(stage), [4, 4, 3, 3, 2, 2, 1, 1, 0, 0]);
  ok("stages: >=75% 4, >=50% 3, >=30% 2, >=15% 1, below 0");
  const p = makePlayer({ id: "-160", hp: 12 });
  const s = buildPayload(p, 2000);
  assert.ok(s.includes("Vh0") && s.includes("Vf4"), s);
  ok("dying heart is stage 0 while food is still full: " + s);
}

// ---------------------------------------------------------------- screen effects can be turned off per player
{
  const { buildPayload } = await import("./succubi/hud.js");
  const { openPersonal } = await import("./succubi/personal.js");
  const p = makePlayer({ id: "-170", hp: 20 });
  assert.ok(!buildPayload(p, 3000).includes("Nx"));
  answers.push(1, 99);
  await openPersonal(p);
  assert.ok(p.hasTag("no_screen_fx"));
  assert.ok(buildPayload(p, 3010).includes("Nx"));
  ok("personal menu turns the red aura / grey screen off (Nx)");
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

// ---------------------------------------------------------------- height: HP 50-200, speed, hit strength, switches
{
  const { calculateMaxHp, bodyStats, setHeightCm } = await import("./height/height.js");
  const { setNum, setEnabled, resetNums } = await import("./succubi/settings_store.js");
  assert.deepEqual([140, 160, 180, 200, 220].map(calculateMaxHp), [50, 71, 100, 141, 200]);
  assert.equal(calculateMaxHp(20), 50);
  assert.equal(calculateMaxHp(400), 200);
  ok("HP by height: 140 cm 50, 180 cm 100, 220 cm 200, never outside 50-200");
  const tall = bodyStats(220), short = bodyStats(140);
  assert.ok(Math.abs(tall.speed - 0.87) < 1e-9 && Math.abs(tall.damage - 1.3) < 1e-9, JSON.stringify(tall));
  assert.ok(Math.abs(short.speed - 1.15) < 1e-9 && Math.abs(short.damage - 0.77) < 1e-9, JSON.stringify(short));
  ok("short runs faster and hits lighter, tall walks slower and hits harder");
  setNum("hp_base", 80);
  assert.deepEqual([140, 180, 220].map(calculateMaxHp), [40, 80, 160]);
  setEnabled("height_hp", false);
  assert.deepEqual([140, 220].map(calculateMaxHp), [80, 80]);
  setEnabled("height_speed", false);
  assert.equal(bodyStats(140).speed, 1);
  ok("base HP setting and the height switches");
  resetNums();
  assert.equal(calculateMaxHp(140), 50);
  const p = makePlayer({ id: "-1000" });
  setHeightCm(p, 205);
  assert.ok(p.events.includes("kotarus:set_h_210") && p.events.includes("succubi:set_spd_210"), p.events.join());
  ok("height sets body size and the matching speed group: " + p.events.join(", "));
}

// ---------------------------------------------------------------- height: melee hits scale with the hitter's height
{
  const { scaleHit } = await import("./height/main.js");
  const { setHeightCm } = await import("./height/height.js");
  const { setEnabled } = await import("./succubi/settings_store.js");
  const victim = (hp) => ({ hp, isValid: () => true, getComponent: (c) => c === "minecraft:health" ? { currentValue: victim.last.hp, effectiveMax: 40, setCurrentValue: (v) => (victim.last.hp = v) } : undefined });
  const hit = (hitter, v, damage, extra = {}) => {
    victim.last = v;
    scaleHit({ hurtEntity: v, damage, damageSource: { cause: "entityAttack", damagingEntity: hitter, ...extra } });
    return v.hp;
  };
  const tall = makePlayer({ id: "-1010" });
  setHeightCm(tall, 220);
  assert.equal(hit(tall, victim(30), 10), 27);
  const short = makePlayer({ id: "-1011" });
  setHeightCm(short, 140);
  assert.ok(Math.abs(hit(short, victim(30), 10) - 32.3) < 1e-9);
  ok("a hit from a 220 cm player takes 30 % more, from 140 cm gives 23 % back");
  const gunner = makePlayer({ id: "-1012", equipment: { Mainhand: "trenbankai:m4a1" } });
  setHeightCm(gunner, 220);
  assert.equal(hit(gunner, victim(30), 10), 30);
  assert.equal(hit(tall, victim(30), 10, { cause: "projectile" }), 30);
  setEnabled("height_damage", false);
  assert.equal(hit(tall, victim(30), 10), 30);
  setEnabled("height_damage", true);
  ok("guns, arrows and the switched-off setting keep normal damage");
}

// ---------------------------------------------------------------- base stats: regeneration, thirst max
{
  const { regenTick } = await import("./succubi/regen.js");
  const { setNum, resetNums } = await import("./succubi/settings_store.js");
  const { getThirst, setThirst, thirstMax } = await import("./succubi/thirst.js");
  const p = makePlayer({ id: "-1100", hp: 50 });
  p.setDynamicProperty("kotarus:max_hp", 100);
  regenTick([p], 5);
  assert.equal(p.hp, 50);
  setNum("regen_seconds", 2);
  regenTick([p], 5);
  assert.equal(p.hp, 52);
  regenTick([p], 1);
  assert.equal(p.hp, 53);
  ok("custom regeneration: 1 HP every 2 s (off = the game's own)");
  setNum("thirst_max", 40);
  setThirst(p, 100);
  assert.equal(getThirst(p), 40);
  setNum("thirst_max", 10);
  assert.equal(thirstMax(), 10);
  assert.equal(getThirst(p), 10);
  resetNums();
  ok("water max follows the setting");
}

// ---------------------------------------------------------------- pressure sounds
{
  const { pressureFor } = await import("./succubi/pressure.js");
  const { setThirst } = await import("./succubi/thirst.js");
  const { setSanity } = await import("./succubi/sanity.js");
  const p = makePlayer({ id: "-1200", hp: 90 });
  p.setDynamicProperty("kotarus:max_hp", 100);
  assert.deepEqual(pressureFor(p, 1000), []);
  p.hp = 10;
  setThirst(p, 2);
  setSanity(p, 10);
  const ids = pressureFor(p, 2000).map((x) => x[0]);
  assert.ok(ids.includes("succubi.heartbeat") && ids.includes("succubi.pant") && ids.includes("succubi.tinnitus"), ids.join());
  const beat = pressureFor(p, 2001);
  assert.ok(!beat.some((x) => x[0] === "succubi.heartbeat"), "heartbeat waits for its tempo");
  const again = pressureFor(p, 2010).find((x) => x[0] === "succubi.heartbeat");
  assert.ok(again && again[1] > 0.7, JSON.stringify(again));
  ok("heartbeat near death (faster and louder), panting when dry, ringing when sanity is gone: " + ids.join(", "));
}

// ---------------------------------------------------------------- Rule of Horror master switch
{
  const { runEvent, getSanity, setSanity } = await import("./succubi/sanity.js");
  const { setEnabled } = await import("./succubi/settings_store.js");
  const p = makePlayer({ id: "-1300" });
  setSanity(p, 80);
  setEnabled("horror", false);
  runEvent(p, "knock");
  assert.equal(getSanity(p), 80);
  setEnabled("horror", true);
  runEvent(p, "knock");
  assert.ok(getSanity(p) < 80);
  ok("Rule of Horror off: no strange event happens at all");
}

// ---------------------------------------------------------------- rule board: admins edit from the board
{
  const { paginate } = await import("./succubi/horror.js");
  const pages = paginate(Array.from({ length: 14 }, (_, i) => `กฎข้อ ${i + 1} ` + "ก".repeat(30)));
  assert.ok(pages.length === 2 && pages.flat().length === 14, pages.map((x) => x.length).join());
  ok("long boards turn into pages");
}

// ---------------------------------------------------------------- the admin's writable book
{
  const { useCustomBook, bookSheets, CUSTOM_BOOK } = await import("./succubi/books.js");
  const { ItemStack } = await import("@minecraft/server");
  const mkItem = () => {
    const it = new ItemStack(CUSTOM_BOOK);
    const d = new Map();
    it.getDynamicProperty = (k) => d.get(k);
    it.setDynamicProperty = (k, v) => d.set(k, v);
    return it;
  };
  assert.deepEqual(bookSheets(["บรรทัดแรก//บรรทัดสอง"]), ["บรรทัดแรก\nบรรทัดสอง"]);
  assert.equal(bookSheets(["ก ".repeat(400)]).length, 2);
  ok("book pages: // is a new line, long pages split");
  const player = makePlayer({ id: "-1400", name: "Reader" });
  const blank = mkItem();
  globalThis.__shown = [];
  await useCustomBook(player, blank);
  assert.ok(/ว่าง/.test(player.bars.join()), player.bars.join());
  ok("players cannot write: a blank book is just empty");
  const admin = makePlayer({ id: "-1401", name: "Admin", mode: "creative" });
  const book = mkItem();
  admin.equipment.Mainhand = book;
  // editor rows: 0 title, 1 author, 2 + add page (after one page: 2 page 1, 3 + add, 4 sanity, 5 preview, 6 save)
  answers.push(0, { formValues: ["บันทึกลับ"] }, 2, { formValues: ["หน้าแรก//ยินดีต้อนรับ"] }, 6);
  await useCustomBook(admin, book);
  await new Promise((r) => setTimeout(r, 5));
  const id = book.getDynamicProperty("succubi:book_id");
  assert.ok(typeof id === "string" && book.nameTag.includes("บันทึกลับ"), String(id));
  globalThis.__shown = [];
  answers.push(0, 1);
  await useCustomBook(player, book);
  const page = globalThis.__shown.find((f) => f._title.includes("บันทึกลับ"));
  assert.ok(page && page._body.includes("ยินดีต้อนรับ"), page?._body);
  ok("an admin writes the book, the item takes its name, players read it");
}

// ---------------------------------------------------------------- strange events: no narration, players see it themselves
{
  const { runEvent, EVENT_IDS } = await import("./succubi/sanity.js");
  const VOICES = ["text", "name_call", "not_alone"]; // the voice IS the event
  const p = makePlayer({ id: "-1450" });
  p.getViewDirection = () => ({ x: 0, y: 0, z: 1 });
  p.getComponent = ((orig) => (c) => (c === "minecraft:inventory" ? { container: { getItem: () => undefined, setItem() {} } } : orig(c)))(p.getComponent);
  for (const id of EVENT_IDS.filter((x) => !VOICES.includes(x))) runEvent(p, id);
  await new Promise((r) => setTimeout(r, 20));
  assert.deepEqual(p.bars, [], p.bars.join(" | "));
  ok(`${EVENT_IDS.length - VOICES.length} strange events run without a single narration line`);
}

// ---------------------------------------------------------------- server settings: three categories
{
  const { openSettings } = await import("./succubi/settings.js");
  const { num, enabled, resetNums, setEnabled } = await import("./succubi/settings_store.js");
  const admin = makePlayer({ id: "-1500", name: "Admin", mode: "creative" });
  globalThis.__shown = [];
  answers.length = 0;
  // main -> status (toggle numbers) -> back; main -> horror -> master off -> back; main -> base -> blood (120 HP, 1 HP / 2 s, food 16) -> back x2
  answers.push(0, 2, 6, 1, 0, 5, 2, 0, { formValues: [120, 4, 16] }, 6, 4);
  await openSettings(admin);
  await new Promise((r) => setTimeout(r, 5));
  const titles = globalThis.__shown.map((f) => f._title.replace(/§./g, ""));
  assert.ok(titles.some((t) => t.startsWith("สถานะและ HUD")) && titles.some((t) => t.startsWith("Rule of Horror")) && titles.some((t) => t.startsWith("สเตตัสพื้นฐาน")), titles.join(" | "));
  assert.equal(enabled("hud_numbers"), false);
  assert.equal(enabled("horror"), false);
  assert.deepEqual([num("hp_base"), num("regen_seconds"), num("regen_food")], [120, 2, 16]);
  const base = globalThis.__shown.find((f) => f._title.includes("สเตตัสพื้นฐาน"));
  assert.ok(/Max HP/.test(base._body) && /ส่วนสูง/.test(base._body) && /สติ/.test(base._body), base._body);
  ok("settings: สถานะและ HUD / Rule of Horror / สเตตัสพื้นฐาน, values saved: " + titles.length + " screens");
  const { buildPayload } = await import("./succubi/hud.js");
  assert.ok(buildPayload(makePlayer({ id: "-1501" })).includes("Wn"));
  ok("numbers switched off reach the HUD (Wn)");
  resetNums();
  setEnabled("hud_numbers", true);
  setEnabled("horror", true);
}

console.log(`\n${pass} checks passed`);
