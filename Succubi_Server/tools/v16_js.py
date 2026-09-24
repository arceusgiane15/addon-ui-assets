"""v1.0.16 scripts (as templates; __DATA__ markers are filled in by build_v16)."""

AMULETS_JS = r'''import { world, system, ItemStack, EquipmentSlot } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { HOOKS } from "./hooks.js";
import { addSanity } from "./sanity.js";
import { enabled } from "./settings_store.js";

// Amulets (เครื่องราง): up to 4 worn from the wallet screen. Worn amulets live in a player property, not the inventory.
export const AMULET_FLAG = "§0§9§5§2"; // skin in RP ui/server_form.json
const PROP = "succubi:amulets";
const SLOTS = 4;
const TEX = "textures/ui/succubi_shops/";
export const AMULETS = __DATA__;
const KEY_BY_ID = new Map(Object.entries(AMULETS).map(([k, a]) => [a.id, k]));

const cache = new Map(); // player id -> worn keys
export function equipped(player) {
  if (cache.has(player.id)) return cache.get(player.id);
  let list = [];
  try {
    const v = JSON.parse(player.getDynamicProperty(PROP) ?? "[]");
    if (Array.isArray(v)) list = v.filter((k) => AMULETS[k]).slice(0, SLOTS);
  } catch (e) {}
  cache.set(player.id, list);
  return list;
}
function save(player, list) {
  cache.set(player.id, list);
  player.setDynamicProperty(PROP, JSON.stringify(list));
}
export const wears = (player, key) => equipped(player).includes(key);

// Nang Kwak: 10% off in every shop
export function priceFor(player, product) {
  return wears(player, "nang_kwak") ? Math.max(1, Math.ceil(product.price * 0.9)) : product.price;
}

// ---------------------------------------------------------------- hooks into the sanity system
const calm = (player) => (Number(player.getDynamicProperty("succubi:calm_until")) || 0) > Date.now();
function cursedNearby(player) {
  if (wears(player, "yant_kan_phi") || calm(player)) return false;
  try {
    for (const o of player.dimension.getPlayers({ location: player.location, maxDistance: 20 })) {
      if (o.id !== player.id && wears(o, "cursed_doll")) return true;
    }
  } catch (e) {}
  return false;
}
HOOKS.eventRate.push((p) => (wears(p, "yant_kan_phi") ? 0.5 : 1) * (cursedNearby(p) ? 2 : 1));
HOOKS.eventLoss.push((p) => (wears(p, "takrut") ? 0.7 : 1) * (wears(p, "yant_kan_phi") ? 0.5 : 1));

// ---------------------------------------------------------------- passive effects (every second)
const PERMANENT = { pha_yant: "resistance", khiao_suea: "speed", ta_thip: "night_vision", lek_lai: "fire_resistance", hanuman: "strength" };
const isNight = () => {
  const t = world.getTimeOfDay();
  return t >= 13000 && t < 23000;
};

function heal(player, amount) {
  const health = player.getComponent("minecraft:health");
  if (!health) return;
  const max = Number(player.getDynamicProperty("kotarus:max_hp")) || health.effectiveMax || 100;
  if (health.currentValue < max) health.setCurrentValue(Math.min(max, health.currentValue + amount));
}

function giveCoins(player, amount) {
  const inv = player.getComponent("minecraft:inventory")?.container;
  const parts = [["succubi:coin_10", Math.floor(amount / 10)], ["succubi:coin_5", Math.floor((amount % 10) / 5)], ["succubi:coin_1", amount % 5]];
  for (const [id, n] of parts) {
    if (n <= 0) continue;
    const stack = new ItemStack(id, n);
    const left = inv?.addItem(stack);
    if (left || !inv) player.dimension.spawnItem(left ?? stack, player.location);
  }
}

let second = 0;
function tick() {
  second++;
  for (const p of world.getAllPlayers()) {
    const list = equipped(p);
    if (list.length === 0) continue;
    try {
      if (second % 5 === 0) {
        for (const [key, effect] of Object.entries(PERMANENT)) {
          if (list.includes(key)) p.addEffect(effect, effect === "night_vision" ? 20 * 16 : 20 * 12, { amplifier: 0, showParticles: false });
        }
      }
      if (list.includes("luang_por") && second % 4 === 0) heal(p, 1);
      if (list.includes("bia_kae")) {
        for (const e of ["poison", "fatal_poison", "nausea", "wither"]) {
          try {
            if (p.getEffect(e)) p.removeEffect(e);
          } catch (err) {}
        }
      }
      if (enabled("sanity")) {
        if (list.includes("takrut")) addSanity(p, 0.05);
        if (list.includes("moon") && isNight()) addSanity(p, 0.1);
        if (list.includes("cursed_doll")) addSanity(p, -0.02);
      }
      if (list.includes("mae_pho") && second % 60 === 0) p.addEffect("saturation", 1, { amplifier: 0, showParticles: false });
      if (list.includes("kuman_thong")) {
        const left = (Number(p.getDynamicProperty("succubi:kuman_left")) || 900) - 1;
        if (left <= 0) {
          const amount = 10 + Math.floor(Math.random() * 51);
          giveCoins(p, amount);
          p.onScreenDisplay.setActionBar(`§6กุมารทองหาเงินมาให้ ${amount} บาท`);
          p.playSound("random.orb");
          p.setDynamicProperty("succubi:kuman_left", 900);
        } else p.setDynamicProperty("succubi:kuman_left", left);
      }
    } catch (e) {}
  }
}

// ---------------------------------------------------------------- screens
async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

const inventory = (player) => player.getComponent("minecraft:inventory")?.container;

function ownedKeys(player) {
  const inv = inventory(player);
  const worn = equipped(player);
  const keys = [];
  if (!inv) return keys;
  for (let i = 0; i < inv.size; i++) {
    const key = KEY_BY_ID.get(inv.getItem(i)?.typeId);
    if (key && !worn.includes(key) && !keys.includes(key)) keys.push(key);
  }
  return keys;
}

function takeOne(player, key) {
  const inv = inventory(player);
  if (!inv) return false;
  for (let i = 0; i < inv.size; i++) {
    const it = inv.getItem(i);
    if (it?.typeId !== AMULETS[key].id) continue;
    if (it.amount > 1) {
      it.amount -= 1;
      inv.setItem(i, it);
    } else inv.setItem(i, undefined);
    return true;
  }
  return false;
}

export function equip(player, key) {
  const list = [...equipped(player)];
  if (list.includes(key) || list.length >= SLOTS) return false;
  if (!takeOne(player, key)) return false;
  list.push(key);
  save(player, list);
  return true;
}

export function unequip(player, key) {
  const list = equipped(player).filter((k) => k !== key);
  save(player, list);
  const stack = new ItemStack(AMULETS[key].id, 1);
  const left = inventory(player)?.addItem(stack);
  if (left) player.dimension.spawnItem(left, player.location);
}

export async function openAmulets(player, note = "") {
  const list = equipped(player);
  const form = new ActionFormData()
    .title(`§lเครื่องราง${AMULET_FLAG}`)
    .body(`§eใส่อยู่ ${list.length}/${SLOTS}${note ? `\n\n${note}` : ""}`);
  for (let i = 0; i < SLOTS; i++) {
    const key = list[i];
    if (key) form.button(`§f${AMULETS[key].short}\n§7แตะเพื่อถอด`, `${TEX}p_amuletui_${key}`);
    else form.button("§7ช่องว่าง\n§8แตะเพื่อใส่", `${TEX}p_amuletui_empty`);
  }
  form.button("", `${TEX}amt_close`);
  const r = await show(form, player);
  if (!r || r.canceled || r.selection >= SLOTS) return;
  const key = list[r.selection];
  if (key) {
    unequip(player, key);
    player.playSound("random.pop");
    return openAmulets(player, `§7ถอดแล้ว\n§f${AMULETS[key].short}`);
  }
  return openPicker(player);
}

async function openPicker(player) {
  const keys = ownedKeys(player);
  if (keys.length === 0) return openAmulets(player, "§cไม่มีเครื่องราง\n§7ในกระเป๋า");
  const form = new ActionFormData().title(`§lเลือกเครื่องราง${AMULET_FLAG}`).body("§eเลือกชิ้นที่\nจะใส่");
  for (const key of keys.slice(0, 18)) form.button(`§f${AMULETS[key].short}\n§7แตะเพื่อใส่`, `${TEX}p_amuletui_${key}`);
  form.button("", `${TEX}amt_back`);
  const r = await show(form, player);
  if (!r || r.canceled) return;
  const key = keys[r.selection];
  if (!key) return openAmulets(player);
  const ok = equip(player, key);
  if (ok) {
    player.playSound("random.orb");
    player.sendMessage(`§6[เครื่องราง] ใส่ ${AMULETS[key].name}: §f${AMULETS[key].effect}`);
  }
  return openAmulets(player, ok ? `§aใส่แล้ว\n§f${AMULETS[key].short}` : "§cใส่ไม่ได้");
}

export function initAmulets() {
  // right-click an amulet = wear it straight away (or open the screen when all slots are full)
  world.afterEvents.itemUse.subscribe((event) => {
    const key = KEY_BY_ID.get(event.itemStack?.typeId);
    if (!key) return;
    const player = event.source;
    system.run(() => {
      if (!wears(player, key) && equipped(player).length < SLOTS && equip(player, key)) {
        player.playSound("random.orb");
        player.onScreenDisplay.setActionBar(`§6ใส่${AMULETS[key].name}แล้ว`);
        player.sendMessage(`§6[เครื่องราง] ${AMULETS[key].name}: §f${AMULETS[key].effect}`);
      } else openAmulets(player, wears(player, key) ? "§7ใส่ชิ้นนี้\n§7อยู่แล้ว" : "§cช่องเต็ม").catch(() => {});
    });
  });
  world.afterEvents.playerLeave.subscribe((e) => cache.delete(e.playerId));
  system.runInterval(tick, 20);
}
'''

BOOKS_JS = r'''import { world, system, EquipmentSlot } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { addSanity, runEvent } from "./sanity.js";
import { enabled } from "./settings_store.js";
import { HOOKS } from "./hooks.js";

// Books: right-click to read page by page on a paper screen; finishing gives sanity (once per cooldown).
export const PAPER_FLAG = "§0§9§5§1"; // skin in RP ui/server_form.json
const BTN = "textures/ui/succubi_paper/";
export const BOOKS = __DATA__;
const NEWS = __NEWS__;

// Prayer book: the next strange event is cancelled
HOOKS.eventBlock.push((p) => {
  if (p.getDynamicProperty("succubi:ward") !== true) return false;
  p.setDynamicProperty("succubi:ward", false);
  p.onScreenDisplay.setActionBar("§eบทสวดมนต์คุ้มครองคุณจากสิ่งแปลกประหลาด");
  return true;
});

async function show(form, player) {
  for (let i = 0; i < 5; i++) {
    const r = await form.show(player);
    if (!r.canceled || r.cancelationReason !== "UserBusy") return r;
    await new Promise((res) => system.runTimeout(res, 10));
  }
  return undefined;
}

function newsPages() {
  const names = world.getAllPlayers().map((p) => p.name);
  const who = () => (names.length ? names[Math.floor(Math.random() * names.length)] : "ชาวบ้าน");
  const pick = () => NEWS[Math.floor(Math.random() * NEWS.length)].replace("{who}", who());
  return [pick(), pick(), pick()];
}

export async function readBook(player, id, page = 0, pages = undefined) {
  const book = BOOKS[id];
  if (!book) return;
  if (!pages) pages = book.special === "news" ? newsPages() : book.pages;
  const last = page >= pages.length - 1;
  const form = new ActionFormData()
    .title(`§l${book.name}${PAPER_FLAG}`)
    .body(`${pages[page]}\n\n§8— หน้า ${page + 1}/${pages.length} —`)
    .button(last ? "§2อ่านจบ" : "§0หน้าถัดไป »", `${BTN}${last ? "btn_done" : "btn_next"}`)
    .button("§4ปิดหนังสือ", `${BTN}btn_close`);
  const r = await show(form, player);
  if (!r || r.canceled || r.selection === 1) return;
  if (!last) return readBook(player, id, page + 1, pages);
  finish(player, id, book);
}

function removeFromHand(player, id) {
  const eq = player.getComponent("minecraft:equippable");
  const held = eq?.getEquipment(EquipmentSlot.Mainhand);
  if (held?.typeId !== id) return;
  if (held.amount > 1) {
    held.amount -= 1;
    eq.setEquipment(EquipmentSlot.Mainhand, held);
  } else eq.setEquipment(EquipmentSlot.Mainhand, undefined);
}

function finish(player, id, book) {
  const prop = `succubi:read_${book.key}`;
  const last = Number(player.getDynamicProperty(prop)) || 0;
  const wait = book.cooldown * 60000 - (Date.now() - last);
  if (book.consumed) removeFromHand(player, id);
  if (wait > 0) {
    player.onScreenDisplay.setActionBar(`§7เพิ่งอ่านเล่มนี้ไป อีก ${Math.ceil(wait / 60000)} นาทีถึงจะรู้สึกดีขึ้นอีก`);
    return;
  }
  player.setDynamicProperty(prop, Date.now());
  if (enabled("sanity")) addSanity(player, book.sanity);
  player.playSound(book.sanity >= 0 ? "random.orb" : "mob.elderguardian.curse");
  let msg = book.sanity >= 0 ? `§aอ่านจบ รู้สึกดีขึ้น (สติ +${book.sanity})` : `§4อ่านจบ... มีบางอย่างผิดปกติ (สติ ${book.sanity})`;
  if (book.special === "calm") {
    player.setDynamicProperty("succubi:calm_until", Date.now() + 30 * 60000);
    msg += " §eไม่หวั่นคำสาป 30 นาที";
  } else if (book.special === "ward") {
    player.setDynamicProperty("succubi:ward", true);
    msg += " §eคุ้มครองเรื่องแปลกครั้งถัดไป";
  } else if (book.special === "cursed") {
    player.addEffect("night_vision", 20 * 60, { amplifier: 0, showParticles: false });
    system.runTimeout(() => {
      try {
        if (enabled("sanity") && enabled("events")) runEvent(player);
      } catch (e) {}
    }, 40);
  }
  player.onScreenDisplay.setActionBar(msg);
}

export function initBooks() {
  world.afterEvents.itemUse.subscribe((event) => {
    if (!BOOKS[event.itemStack?.typeId]) return;
    const player = event.source;
    const id = event.itemStack.typeId;
    system.run(() => {
      readBook(player, id).catch(() => {});
    });
  });
}
'''

BLOODMOON_JS = r'''import { world, system } from "@minecraft/server";
import { HOOKS } from "./hooks.js";
import { enabled } from "./settings_store.js";
import { addSanity } from "./sanity.js";
import { runAs } from "./cmd.js";

// Blood moon (คืนพระจันทร์เลือด): about 1 night in 7. All night: red fog for everyone,
// strange events come 6x faster, sanity slowly drains. Ends at sunrise.
const ACTIVE = "succubi:bm_active";
const LAST_DAY = "succubi:bm_day";
const FOG = "succubi_bloodmoon";
export const isBloodMoon = () => world.getDynamicProperty(ACTIVE) === true;
function today() {
  try {
    return world.getDay();
  } catch (e) {
    return Math.floor(world.getAbsoluteTime() / 24000);
  }
}
const isNight = () => {
  const t = world.getTimeOfDay();
  return t >= 12800 && t < 23000;
};

HOOKS.eventRate.push(() => (isBloodMoon() ? 6 : 1));

const exempt = (p) => {
  try {
    const m = String(p.getGameMode?.()).toLowerCase();
    return m === "creative" || m === "spectator";
  } catch (e) {
    return false;
  }
};

function fogOn(player) {
  runAs(player, `fog @s remove ${FOG}`);
  runAs(player, `fog @s push succubi:blood_moon ${FOG}`);
}

export function startBloodMoon(forceNight = false) {
  if (forceNight && !isNight()) world.setTimeOfDay(13000);
  world.setDynamicProperty(ACTIVE, true);
  world.setDynamicProperty(LAST_DAY, today());
  for (const p of world.getAllPlayers()) {
    fogOn(p);
    runAs(p, "playsound mob.wither.spawn @s ~ ~ ~ 0.3 0.5");
    p.sendMessage("§4§lคืนพระจันทร์เลือด!§r §cคืนนี้เรื่องแปลกจะเกิดบ่อยขึ้นมาก หาที่ปลอดภัย อยู่ใกล้เพื่อนไว้");
  }
}

export function endBloodMoon() {
  world.setDynamicProperty(ACTIVE, false);
  for (const p of world.getAllPlayers()) {
    runAs(p, `fog @s remove ${FOG}`);
    p.sendMessage("§6พระอาทิตย์ขึ้นแล้ว... คืนพระจันทร์เลือดจบลง");
  }
}

export function initBloodMoon() {
  world.afterEvents.playerSpawn.subscribe((e) => {
    if (isBloodMoon() && e.player) system.runTimeout(() => fogOn(e.player), 20);
    else if (e.player) runAs(e.player, `fog @s remove ${FOG}`);
  });
  system.runInterval(() => {
    try {
      const t = world.getTimeOfDay();
      if (isBloodMoon()) {
        if (!enabled("bloodmoon") || !isNight()) return endBloodMoon();
        for (const p of world.getAllPlayers()) {
          if (!exempt(p) && enabled("sanity") && p.dimension.id === "minecraft:overworld") addSanity(p, -0.08);
        }
        return;
      }
      if (t >= 12800 && t < 13600 && world.getDynamicProperty(LAST_DAY) !== today()) {
        world.setDynamicProperty(LAST_DAY, today());
        if (enabled("bloodmoon") && world.getAllPlayers().length > 0 && Math.random() < 1 / 7) startBloodMoon();
      }
    } catch (e) {}
  }, 40);
}
'''
