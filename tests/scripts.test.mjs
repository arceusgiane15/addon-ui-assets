// Loads the whole Succubi Server BP script (main.js) against tests/mock and checks the v1.1.9 behaviour.
// Run: node --import ./tests/register.mjs --test tests/
import { test } from "node:test";
import assert from "node:assert/strict";
import * as mc from "./mock/server.js";
import * as ui from "./mock/server-ui.js";

const BP = "../addon/Succubi Server BP/scripts/";
const player = new mc.Player("Duck");
mc.world.players.push(player);

await import(BP + "main.js");
const body = await import(BP + "height/body.js");
const height = await import(BP + "height/height.js");
const heightUi = await import(BP + "height/ui.js");
const store = await import(BP + "succubi/settings_store.js");
const hud = await import(BP + "succubi/hud.js");
const daytime = await import(BP + "succubi/daytime.js");
const music = await import(BP + "succubi/music.js");
const ds = await import(BP + "succubi/ds_sanity.js");
const sanity = await import(BP + "succubi/sanity.js");

const settle = async (ticks = 2) => {
  mc.advance(ticks);
  await new Promise((r) => setImmediate(r));
};

test("defaults: 140 / 180 / 220 cm give the old numbers", () => {
  assert.deepEqual(body.heightPoints(), { lo: 140, std: 180, hi: 220 });
  assert.equal(body.hpFor(140), 50);
  assert.equal(body.hpFor(180), 100);
  assert.equal(body.hpFor(220), 200);
  assert.equal(body.hpFor(200), 150); // straight line now (was 141 on the old curve)
  assert.equal(body.speedPercent(140), 115);
  assert.equal(body.speedPercent(220), 87);
  assert.equal(Math.round(body.damageFor(140) * 100), 77);
  assert.equal(Math.round(body.fallFor(220) * 100), 125);
  assert.equal(body.hungerPercent(220), 120);
  assert.equal(Math.round(body.hurtFor(140) * 100), 110);
  // outside the player range (admins) the end values hold
  assert.equal(body.hpFor(500), 200);
  assert.equal(body.hpFor(1), 50);
});

test("settings move the three points and the values", () => {
  store.setMany({ h_min: 100, h_std: 170, h_max: 260, hp_short: 30, hp_base: 120, hp_tall: 300 }, {}, "h_range");
  assert.equal(body.hpFor(100), 30);
  assert.equal(body.hpFor(170), 120);
  assert.equal(body.hpFor(260), 300);
  assert.equal(body.hpFor(215), 210);
  store.setEnabled("height_hp", false);
  assert.equal(body.hpFor(260), 120);
  store.resetNums(Object.keys(store.NUMS), store.HEIGHT_SWITCHES);
  assert.equal(body.hpFor(220), 200);
});

test("HP group: max follows the height, the HP number is kept (not refilled)", async () => {
  player.health.currentValue = 60;
  height.setHeightCm(player, 220);
  await settle(4);
  assert.ok(player.events.includes("succubi:set_hp_200"), "HP group sent");
  assert.equal(player.health.effectiveMax, 200);
  assert.equal(player.health.currentValue, 60, "HP put back after the group filled it");
  assert.equal(height.shownHp(player, 200), 200, "nothing pending any more");
  // shorter: capped at the new max
  height.setHeightCm(player, 140);
  await settle(4);
  assert.equal(player.health.effectiveMax, 50);
  assert.equal(player.health.currentValue, 50);
  // regeneration can now go past 100 on a tall body
  height.setHeightCm(player, 220);
  await settle(4);
  player.health.setCurrentValue(150);
  assert.equal(player.health.currentValue, 150);
  assert.ok(player.events.some((e) => e.startsWith("succubi:set_spdp_")), "speed group sent");
  assert.ok(player.events.includes("succubi:set_hun_120"), "hunger group sent");
});

test("player.json carries every group the script can ask for", async () => {
  const fs = await import("node:fs");
  for (const pack of ["Succubi Server BP", "Succubi Guns BP"]) {
    const e = JSON.parse(fs.readFileSync(new URL(`../addon/${pack}/entities/player.json`, import.meta.url)))["minecraft:entity"];
    for (let hp = 10; hp <= 400; hp += 5) assert.ok(e.events[`succubi:set_hp_${String(hp).padStart(3, "0")}`], `${pack} hp ${hp}`);
    for (let s = 50; s <= 150; s++) assert.ok(e.events[`succubi:set_spdp_${String(s).padStart(3, "0")}`], `${pack} spd ${s}`);
    for (let h = 50; h <= 200; h += 5) assert.ok(e.events[`succubi:set_hun_${String(h).padStart(3, "0")}`], `${pack} hun ${h}`);
    for (const [name, ev] of Object.entries(e.events)) {
      for (const g of [...(ev.add?.component_groups ?? []), ...(ev.remove?.component_groups ?? [])]) {
        assert.ok(e.component_groups[g], `${pack}: ${name} uses missing group ${g}`);
      }
    }
  }
});

test("height menu: 3 buttons, slider has confirm, cancel changes nothing", async () => {
  height.setHeightCm(player, 180);
  player.setDynamicProperty("kotarus:height_next", 0);
  ui.shown.length = 0;
  ui.answers.push({ canceled: false, selection: 0 }, { canceled: true, cancelationReason: "UserClosed" });
  await heightUi.openHeightForm(player);
  const [menu, slider] = ui.shown;
  assert.deepEqual(menu.parts.filter((p) => p[0] === "button").map((p) => p[1]), ["ปรับส่วนสูง", "รีเซ็ต", "ยกเลิก"]);
  assert.ok(slider.parts.some((p) => p[0] === "submit" && p[1] === "ยืนยัน"));
  assert.equal(height.getHeightCm(player), 180, "cancel keeps the height");
  // confirm 200
  ui.answers.push({ canceled: false, selection: 0 }, { canceled: false, formValues: [200] });
  await heightUi.openHeightForm(player);
  assert.equal(height.getHeightCm(player), 200);
  // now on cooldown: reset refused
  ui.answers.push({ canceled: false, selection: 1 });
  await heightUi.openHeightForm(player);
  assert.equal(height.getHeightCm(player), 200);
  assert.match(player.actionbar, /เปลี่ยนได้อีกครั้ง/);
  // cooldown over: reset asks, then goes back to the standard height
  player.setDynamicProperty("kotarus:height_next", 0);
  ui.answers.push({ canceled: false, selection: 1 }, { canceled: false, selection: 0 });
  await heightUi.openHeightForm(player);
  assert.equal(height.getHeightCm(player), 180);
});

test("wallet settings: only the height, old personal switches cleared on join", async () => {
  const personal = await import(BP + "succubi/personal.js");
  ui.shown.length = 0;
  await personal.openPersonal(player);
  const buttons = ui.shown[0].parts.filter((p) => p[0] === "button").map((p) => p[1]);
  assert.equal(buttons.length, 2);
  assert.match(buttons[0], /ปรับส่วนสูง/);
  player.addTag("hide_hud");
  player.addTag("no_tension_music");
  mc.fire("world.after.playerSpawn", { player, initialSpawn: true });
  assert.ok(!player.hasTag("hide_hud") && !player.hasTag("no_tension_music"));
});

test("fall damage and hits follow the victim's height", async () => {
  const main = await import(BP + "height/main.js");
  height.setHeightCm(player, 220);
  const f = main.hitFactor({ damageSource: { cause: "fall" }, hurtEntity: player });
  assert.equal(Math.round(f * 100), 125);
  const h = main.hitFactor({ damageSource: { cause: "projectile" }, hurtEntity: player });
  assert.equal(Math.round(h * 100), 90);
});

test("HUD: static tiers, arrows, clock", () => {
  assert.equal(hud.staticTier(100), 0);
  assert.equal(hud.staticTier(69), 1);
  assert.equal(hud.staticTier(49), 2);
  assert.equal(hud.staticTier(29), 3);
  assert.equal(hud.staticTier(14), 4);
  const cfg = hud.RATE.s;
  // sleeping: +0.6 sanity per second = 36 %/min -> 3 arrows up
  const up = [];
  for (let i = 0; i < 20; i++) up.push([i * 5, 0.0015]);
  assert.equal(hud.rateCode(up, 100, cfg), 3);
  assert.equal(hud.rateCode(up.map(([t, d]) => [t, -d / 10]), 100, cfg), 4);
  assert.equal(hud.rateCode([], 100, cfg), 0);
  assert.equal(daytime.clockTokens(0, 1), "Rk00Rn1R51");
  assert.equal(daytime.clockTokens(6000, 42), "Rk12Rn2R54R62");
  assert.equal(daytime.clockTokens(23999, 1234), "Rk47Rn4R51R62R73R84");
  assert.equal(daytime.clockTime(0), "06:00");
  assert.equal(daytime.clockTime(18000), "00:00");
  assert.equal(daytime.phaseOf(13000), "dusk");
});

test("new HUD tokens never create or hide an old one", async () => {
  const fs = await import("node:fs");
  const raw = fs.readFileSync(new URL("../addon/Succubi Server RP/ui/succubi_hud.json", import.meta.url), "utf8");
  const tokens = [...new Set([...raw.matchAll(/#preserved_text - '([^']+)'\)/g)].map((m) => m[1]))];
  const newOnes = (t) => /^(R[gkn5-8]|J[hfts])/.test(t);
  const old = tokens.filter((t) => !newOnes(t) && t !== "shud:off");
  let checked = 0;
  for (let i = 0; i < 400; i++) {
    player.health.currentValue = 1 + Math.random() * 199;
    sanity.setSanity(player, Math.random() * 100);
    mc.world.absoluteTime = Math.floor(Math.random() * 24000 * 3000);
    const full = hud.buildPayload(player, 1000 + i * 5);
    const plain = full.replace(/R[gk]\d+|Rn\d|R[5-8]\d|J[hfts]\d/g, "");
    for (const f of [(s) => s, (s) => s.toLowerCase()]) {
      // the new tokens change no old condition, and the old payload never switches a new element on
      for (const t of old) assert.equal(f(full).includes(f(t)), f(plain).includes(f(t)), `token ${t} in ${full}`);
      for (const t of tokens.filter(newOnes)) assert.ok(!f(plain).includes(f(t)), `new ${t} inside ${plain}`);
    }
    checked++;
  }
  assert.equal(checked, 400);
});

test("time: 1 real hour from morning to evening", async () => {
  assert.ok(Math.abs(daytime.timeRate() - 1 / 6) < 1e-9);
  assert.equal(mc.world.gameRules.doDayLightCycle, false, "the pack took the daylight cycle");
  mc.world.absoluteTime = 0;
  await settle(20 * 60 * 60); // one real hour
  assert.ok(Math.abs(mc.world.getTimeOfDay() - 12000) <= 2, `at ${mc.world.getTimeOfDay()}`);
  store.setEnabled("time_custom", false);
  assert.equal(mc.world.gameRules.doDayLightCycle, true, "handed back to the game");
  store.setEnabled("time_custom", true);
});

test("music: danger / madness / calm with hysteresis", () => {
  assert.equal(music.moodFor(0.4, 1, 99999), "danger");
  assert.equal(music.moodFor(0.7, 1, 100), "danger");
  assert.equal(music.moodFor(0.7, 1, 99999), "calm");
  assert.equal(music.moodFor(0.7, 1, 100, "danger"), "danger");
  assert.equal(music.moodFor(0.7, 1, 700, "danger"), "calm");
  assert.equal(music.moodFor(0.95, 0.3, 0, "danger"), "madness");
  assert.equal(music.moodFor(1, 0.55, 99999, "madness"), "madness");
  assert.equal(music.moodFor(1, 0.55, 99999, "calm"), "calm");
});

test("music follows the player's state", async () => {
  sanity.setSanity(player, 100);
  player.health.currentValue = player.health.effectiveMax;
  await settle(20);
  player.music.length = 0;
  player.health.currentValue = player.health.effectiveMax * 0.3;
  await settle(20);
  assert.equal(player.music.at(-1)?.[0], "succubi.music.danger");
  player.health.currentValue = player.health.effectiveMax;
  await settle(20);
  assert.equal(player.music.at(-1)?.[0], "succubi.music.silence");
  sanity.setSanity(player, 20);
  await settle(20);
  assert.equal(player.music.at(-1)?.[0], "succubi.music.madness");
  sanity.setSanity(player, 100);
  await settle(20);
});

test("Don't Starve sanity: night, darkness, campfire, flowers", () => {
  const dim = mc.world.getDimension("overworld");
  mc.world.absoluteTime = 18000; // midnight
  dim.topY = 60; // open sky
  assert.equal(Math.round(ds.worldSanity(player, dim, player.location) * 100), -13); // night + dark
  dim.lightNear = true;
  assert.equal(Math.round(ds.worldSanity(player, dim, player.location) * 100), -5);
  dim.campfireNear = true;
  assert.equal(Math.round(ds.worldSanity(player, dim, player.location) * 100), 0);
  dim.lightNear = dim.campfireNear = false;
  mc.world.absoluteTime = 6000; // noon, in the open: nothing
  assert.equal(ds.worldSanity(player, dim, player.location), 0);
  assert.equal(ds.flowerSanity(player, "minecraft:poppy"), 3);
  assert.equal(ds.flowerSanity(player, "minecraft:wither_rose"), -5);
  let total = 3;
  for (let i = 0; i < 10; i++) total += ds.flowerSanity(player, "minecraft:dandelion");
  assert.equal(total, 20, "capped at 20 per 5 minutes");
});

test("shadows: one per player, only the mad see them, hits counted, melt away above 20 %", async () => {
  const shadowsMod = await import(BP + "succubi/shadows.js");
  store.setEnabled("shadows_real", true);
  const friend = new mc.Player("Sane friend");
  friend.location = { x: 3.5, y: 70, z: 0.5 };
  mc.world.players.push(friend);
  sanity.setSanity(friend, 100);
  player.gameMode = "survival";
  sanity.setSanity(player, 5);
  await settle(20 * 40);
  assert.ok(player.hasTag("succubi_insane"));
  assert.ok(!friend.hasTag("succubi_insane"));
  const dim = player.dimension;
  const shadows = () => dim.spawned.filter((e) => e.alive && e.typeId === "succubi:shadow_creature");
  assert.equal(shadows().length, 1, "exactly one shadow");
  assert.ok(shadows()[0].effects.includes("invisibility"), "its body is invisible");
  const drawn = new Set(player.particles.map(([id]) => id));
  for (const id of ["succubi:shadow_body", "succubi:shadow_eye", "succubi:shadow_wisp", "succubi:shadow_gather"]) assert.ok(drawn.has(id), id);
  assert.equal(friend.particles.length, 0, "the sane friend sees nothing");
  // hits: 29 damage is not enough, the 30th point destroys it
  const s = shadows()[0];
  const fuelBefore = player.items.length;
  const sanityBefore = sanity.getSanity(player);
  shadowsMod.hitShadow({ hurtEntity: s, damage: 29, damageSource: { damagingEntity: player } });
  assert.ok(s.alive);
  assert.equal(s.getComponent("minecraft:health").currentValue, 1000, "real health kept full");
  shadowsMod.hitShadow({ hurtEntity: s, damage: 5, damageSource: { damagingEntity: player } });
  assert.ok(!s.alive, "destroyed");
  assert.equal(player.items.length, fuelBefore + 1, "nightmare fuel in hand");
  assert.ok(sanity.getSanity(player) >= sanityBefore + 14.9);
  assert.equal(friend.particles.length, 0, "the burst was not shown to the sane friend either");
  sanity.setSanity(player, 25);
  await settle(40);
  assert.ok(!player.hasTag("succubi_insane"));
  assert.equal(shadows().length, 0);
  mc.world.players.pop();
});

test("admin settings: height page, rules, preset, time speed", async () => {
  const settings = await import(BP + "succubi/settings.js");
  player.gameMode = "creative";
  ui.shown.length = 0;
  ui.answers.push(
    { canceled: false, selection: 2 }, // สเตตัสพื้นฐาน
    { canceled: false, selection: 4 }, // ส่วนสูง
    { canceled: false, selection: 0 }, // ช่วงส่วนสูงและกติกา
    { canceled: false, formValues: [230, 175, 150, 3, 10, false] }, // out of order on purpose
    { canceled: false, selection: 7 }, // พรีเซ็ต
    { canceled: false, selection: 1 } // ต่างกันมาก
  );
  await settings.openSettings(player);
  assert.equal(store.num("h_min"), 150);
  assert.equal(store.num("h_std"), 175);
  assert.equal(store.num("h_max"), 230);
  assert.equal(store.num("h_cooldown"), 3);
  assert.equal(store.num("hp_tall"), 250);
  assert.equal(store.num("spd_short"), 125);
  const table = ui.shown.find((f) => f.parts.some((p) => p[0] === "body" && String(p[1]).includes("ซม.")) && f.parts[0][1].includes("ส่วนสูง"));
  assert.ok(table, "height table shown");
  ui.answers.push({ canceled: false, selection: 4 }, { canceled: false, selection: 0 }, { canceled: false, formValues: [7] });
  await settings.openSettings(player);
  assert.equal(store.num("halfday_minutes"), 120);
  assert.ok(Math.abs(daytime.timeRate() - 1 / 12) < 1e-9);
  store.resetNums(Object.keys(store.NUMS), store.HEIGHT_SWITCHES);
  player.gameMode = "survival";
});

test("vending machine: shop screen with product names, pays from credit", async () => {
  const vending = await import(BP + "succubi/vending.js");
  const machine = vending.MACHINES["succubi:drink_vending_machine"];
  player.setDynamicProperty("succubi:vend_credit", 100);
  player.items.length = 0;
  ui.shown.length = 0;
  ui.answers.push({ canceled: false, selection: 4 }, { canceled: true, cancelationReason: "UserClosed" }); // 2nd product
  await vending.openMachine(player, machine);
  const form = ui.shown[0];
  const buttons = form.parts.filter((p) => p[0] === "button");
  assert.match(form.parts[0][1], /ตู้กดน้ำ§0§9§8§4/);
  assert.deepEqual(buttons.slice(0, 3).map((b) => b[2].split("/").pop()), ["btn_change", "btn_insert_all_off", "amt_close"]);
  assert.match(buttons[3][1], /น้ำดื่ม/); // names, not just prices
  assert.match(buttons[4][1], /เป๊ปซี่/);
  assert.equal(buttons[4][2], "textures/ui/succubi_shops/p_seven_drink_pepsi");
  assert.equal(player.items.at(0)?.typeId, "succubi:drink_pepsi", "bought");
  // closing pays the change back
  assert.equal(player.getDynamicProperty("succubi:vend_credit"), 0);
});
