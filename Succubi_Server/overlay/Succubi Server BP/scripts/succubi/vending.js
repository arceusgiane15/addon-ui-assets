import { world, system, ItemStack } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { DRINKS, SNACKS } from "./products.js";
import { cashValue, breakdown } from "./money.js";
import { formatBaht } from "./economy.js";
import { SHOPS, FACE_ON_PLACE } from "./shops.js";
import { priceFor } from "./amulets.js";
import { isAdmin } from "./settings_store.js";

// Right-click a machine -> machine screen. Money goes in as cash items (not from the wallet balance);
// the credit sits in the machine until spent, and whatever is left is paid back as change on close.
// Invisible colour codes in the title pick the skin RP ui/server_form.json draws.
export const MACHINES = {
  "succubi:drink_vending_machine": { flag: "§0§9§8§4", title: "ตู้กดน้ำ", products: DRINKS, prefix: "drink" },
  "succubi:snack_vending_machine": { flag: "§0§9§8§3", title: "ตู้ขนม", products: SNACKS, prefix: "snack" }
};
export const COIN_SLOTS = [1, 5, 10, 20, 50, 100]; // what the machine accepts, like a real one
const CASH_ID = { 1: "succubi:coin_1", 5: "succubi:coin_5", 10: "succubi:coin_10", 20: "succubi:banknote_20", 50: "succubi:banknote_50", 100: "succubi:banknote_100", 500: "succubi:banknote_500", 1000: "succubi:banknote_1000" };
const CREDIT = "succubi:vend_credit";
const VT = "textures/ui/succubi_vending/";
const WT = "textures/ui/succubi_wallet/";

const inventoryOf = (player) => player.getComponent("minecraft:inventory")?.container;
export const getCredit = (player) => Number(player.getDynamicProperty(CREDIT)) || 0;
const setCredit = (player, value) => player.setDynamicProperty(CREDIT, Math.max(0, Math.floor(value)));

function countOf(container, typeId) {
  let n = 0;
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    if (item?.typeId === typeId) n += item.amount;
  }
  return n;
}

function give(player, stack) {
  const leftover = inventoryOf(player)?.addItem(stack);
  if (leftover) player.dimension.spawnItem(leftover, player.location);
}

export function makeProduct(product, amount = 1) {
  const stack = new ItemStack(product.id, amount);
  stack.setLore(product.lore);
  return stack;
}

// Feed one note/coin of this value into the machine
export function insertOne(player, value) {
  const container = inventoryOf(player);
  if (!container) return false;
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    if (item?.typeId !== CASH_ID[value]) continue;
    if (item.amount > 1) {
      item.amount -= 1;
      container.setItem(i, item);
    } else {
      container.setItem(i, undefined);
    }
    setCredit(player, getCredit(player) + value);
    return true;
  }
  return false;
}

// Feed every accepted note/coin (100 baht and below)
export function insertAll(player, slots = COIN_SLOTS) {
  const container = inventoryOf(player);
  if (!container) return 0;
  let total = 0;
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    const value = item ? cashValue(item.typeId) : 0;
    if (!slots.includes(value)) continue;
    total += value * item.amount;
    container.setItem(i, undefined);
  }
  if (total > 0) setCredit(player, getCredit(player) + total);
  return total;
}

export function buy(player, product) {
  const credit = getCredit(player);
  const price = priceFor(player, product);
  if (credit < price) return { ok: false, need: price - credit };
  setCredit(player, credit - price);
  give(player, makeProduct(product));
  return { ok: true };
}

export function returnChange(player) {
  const credit = getCredit(player);
  if (credit <= 0) return 0;
  setCredit(player, 0);
  for (const part of breakdown(credit)) {
    for (let left = part.count; left > 0; left -= 64) give(player, new ItemStack(part.id, Math.min(64, left)));
  }
  return credit;
}

async function show(form, player) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const response = await form.show(player);
    if (!response.canceled || response.cancelationReason !== "UserBusy") return response;
    await new Promise((resolve) => system.runTimeout(resolve, 10));
  }
  return undefined;
}

function closeMachine(player, machine) {
  const back = returnChange(player);
  if (back > 0) {
    player.sendMessage(`§e[${machine?.who ?? "ตู้"}] ทอนเงิน ${formatBaht(back)} บาท`);
    player.playSound("random.orb");
  }
}

// Grid 4 x 5: products 0-10, change 11, insert +1..+100 12-17, insert all 18, close 19
// Shops with names (kiosks, pharmacy, store shelves, books, amulets): 3 columns + scrolling list.
// Buttons: 0 change, 1 insert all cash, 2 close, then the products.
async function openShop3(player, machine, note = "") {
  const credit = getCredit(player);
  const container = inventoryOf(player);
  const slots = machine.slots ?? COIN_SLOTS;
  const hasCash = (value) => !!container && countOf(container, CASH_ID[value]) > 0;
  const anyCash = slots.some(hasCash);
  const T = machine.btnTex;
  const form = new ActionFormData()
    .title(`§l${machine.title}${machine.flag}`)
    .body(`§fเงินที่ใส่\n§l§a${formatBaht(credit)} บาท§r${note ? `\n\n${note}` : ""}`);
  form.button(credit > 0 ? "§lทอนเงิน" : "§7ทอนเงิน", `${T}btn_change${credit > 0 ? "" : "_off"}`);
  form.button(anyCash ? "§lใส่เงินหมด" : "§7ใส่เงินหมด", `${T}btn_insert_all${anyCash ? "" : "_off"}`);
  form.button("§lปิด", `${T}amt_close`);
  for (const p of machine.products) {
    const price = priceFor(player, p);
    const ok = credit >= price;
    form.button(`§f${p.short ?? p.name}\n${ok ? "§e§l" : "§7"}${price}.-`, `${machine.tex ?? VT}p_${machine.prefix}_${p.key}${ok ? "" : "_off"}`);
  }
  const response = await show(form, player);
  if (!response || response.canceled) return closeMachine(player, machine);
  const index = response.selection;
  let message = "";
  if (index === 0) {
    const back = returnChange(player);
    if (back > 0) player.playSound("random.orb");
    message = back > 0 ? `§fทอนเงิน\n${formatBaht(back)} บาท` : "§fยังไม่ได้ใส่เงิน";
  } else if (index === 1) {
    const total = insertAll(player, slots);
    if (total > 0) player.playSound("random.click");
    message = total > 0 ? `§fใส่เงิน\n${formatBaht(total)} บาท` : "§cไม่มีเงินสด\nในตัว";
  } else {
    const product = machine.products[index - 3];
    if (!product) return closeMachine(player, machine);
    const result = buy(player, product);
    if (result.ok) player.playSound("random.pop");
    message = result.ok ? `§fได้รับ\n§e${product.short ?? product.name}` : `§cใส่เพิ่มอีก\n${result.need} บาท`;
  }
  return openShop3(player, machine, message);
}

export async function openMachine(player, machine, note = "") {
  if (machine.names) return openShop3(player, machine, note);
  const credit = getCredit(player);
  const container = inventoryOf(player);
  const slots = machine.slots ?? COIN_SLOTS; // notes/coins this machine takes
  const buttons = machine.coinButtons === false ? [] : slots; // coin buttons shown on the screen
  const art = (vendingPath, name) => (machine.btnTex ? `${machine.btnTex}${name}` : vendingPath);
  const hasCash = (value) => !!container && countOf(container, CASH_ID[value]) > 0;
  const anyCash = slots.some(hasCash);
  const form = new ActionFormData()
    .title(`§l${machine.title}${machine.flag}`)
    .body(`§2เงินที่ใส่\n§l§a${formatBaht(credit)} บาท§r${note ? `\n\n${note}` : ""}`);
  for (const p of machine.products) {
    const price = priceFor(player, p);
    const affordable = credit >= price;
    const text = machine.names
      ? `${affordable ? "§f" : "§7"}${p.short ?? p.name}\n${affordable ? "§e§l" : "§8"}${price}.-`
      : `${affordable ? "§l" : "§7"}${price}.-`;
    form.button(text, `${machine.tex ?? VT}p_${machine.prefix}_${p.key}${affordable ? "" : "_off"}`);
  }
  form.button(credit > 0 ? "§lทอน" : "§7ทอน", art(`${VT}btn_change`, "btn_change") + (credit > 0 ? "" : "_off"));
  for (const value of buttons) {
    const has = hasCash(value);
    form.button(`${has ? "§l" : "§7"}+${value}`, art(`${WT}amt_${value}`, `amt_${value}`) + (has ? "" : "_off"));
  }
  form.button(anyCash ? "§lใส่หมด" : "§7ใส่หมด", art(`${VT}btn_insert_all`, "btn_insert_all") + (anyCash ? "" : "_off"));
  form.button("", art(`${WT}amt_close`, "amt_close"));

  const response = await show(form, player);
  if (!response || response.canceled) return closeMachine(player, machine);
  const index = response.selection;
  const count = machine.products.length;
  let message = "";
  if (index < count) {
    const product = machine.products[index];
    const result = buy(player, product);
    if (result.ok) player.playSound("random.pop");
    message = result.ok ? `§7ได้รับ\n§f${product.name}` : `§cใส่เพิ่มอีก\n${result.need} บาท`;
  } else if (index === count) {
    const back = returnChange(player);
    if (back > 0) player.playSound("random.orb");
    message = back > 0 ? `§7ทอนเงิน\n${formatBaht(back)} บาท` : "§7ยังไม่ได้ใส่เงิน";
  } else if (index <= count + buttons.length) {
    const value = buttons[index - count - 1];
    const ok = insertOne(player, value);
    if (ok) player.playSound("random.click");
    message = ok ? `§7ใส่ ${value} บาท` : `§cไม่มี${value >= 20 ? "แบงก์" : "เหรียญ"}\n${value} บาท`;
  } else if (index === count + buttons.length + 1) {
    const total = insertAll(player, slots);
    if (total > 0) player.playSound("random.click");
    message = total > 0 ? `§7ใส่เงิน\n${formatBaht(total)} บาท` : "§cไม่มีเงินสดในตัว";
  } else {
    return closeMachine(player, machine);
  }
  return openMachine(player, machine, message);
}

// First few shop clicks of each kind go to the content log, so a broken path can be told apart from a broken screen
const logged = new Map();
function shopLog(path, id) {
  const n = logged.get(path) ?? 0;
  if (n >= 3) return;
  logged.set(path, n + 1);
  console.warn(`[Succubi shop] ${path}: ${id}`);
}

const lastOpen = new Map(); // player id -> tick of the last shop screen, so both events don't open it twice
const alive = (e) => { try { return typeof e.isValid === "function" ? e.isValid() : e.isValid; } catch (err) { return false; } };

function openFor(player, entity) {
  const machine = MACHINES[entity?.typeId] ?? SHOPS[entity?.typeId];
  if (!machine || !player) return;
  const now = system.currentTick;
  if (now - (lastOpen.get(player.id) ?? -100) < 10) return;
  lastOpen.set(player.id, now);
  system.run(() => {
    openMachine(player, machine).catch(() => {});
  });
}

// Entity events don't say who clicked: the player looking at the shop, else the closest one
function whoUsed(entity) {
  try {
    const near = entity.dimension.getPlayers({ location: entity.location, maxDistance: 10 });
    for (const p of near) {
      try {
        if (p.getEntitiesFromViewDirection({ maxDistance: 10 }).some((hit) => hit.entity?.id === entity.id)) return p;
      } catch (e) {}
    }
    return entity.dimension.getPlayers({ location: entity.location, closest: 1, maxDistance: 10 })[0];
  } catch (e) {
    return undefined;
  }
}

// ---------------------------------------------------------------- ownership
// Whoever places a shop owns it. Only the owner or an admin may pick it up again.
// Shops placed before v1.1.0 have no owner: admins only.
const OWNER = "succubi:owner";
const OWNER_NAME = "succubi:owner_name";
const pendingPlace = new Map(); // player id -> { id: entity type, tick, at }

const placedType = (itemId) => (itemId?.endsWith("_placer") ? itemId.slice(0, -"_placer".length) : itemId);

export function ownerName(entity) {
  try {
    return entity.getDynamicProperty(OWNER_NAME);
  } catch (e) {
    return undefined;
  }
}

export function canPickUp(player, entity) {
  if (!player) return false;
  if (isAdmin(player)) return true;
  try {
    return entity.getDynamicProperty(OWNER) === player.id;
  } catch (e) {
    return false;
  }
}

function claim(entity, placed) {
  const now = system.currentTick;
  let best;
  for (const [pid, p] of pendingPlace) {
    if (now - p.tick > 40 || p.id !== entity.typeId) continue;
    const d = Math.hypot(p.at.x - entity.location.x, p.at.z - entity.location.z);
    if (d < 6 && (!best || d < best.d)) best = { pid, d, name: p.name };
  }
  if (best) {
    pendingPlace.delete(best.pid);
  } else if (placed) {
    // placed, but the item-use event was not seen: whoever stands closest placed it
    try {
      const p = entity.dimension.getPlayers({ location: entity.location, closest: 1, maxDistance: 8 })[0];
      if (p) best = { pid: p.id, name: p.name };
    } catch (e) {}
  }
  if (!best) return;
  try {
    entity.setDynamicProperty(OWNER, best.pid);
    entity.setDynamicProperty(OWNER_NAME, best.name);
  } catch (e) {}
}

function refusePickUp(player, entity) {
  const who = ownerName(entity);
  player.onScreenDisplay.setActionBar(who ? `§cร้านนี้เป็นของ ${who} · เก็บได้เฉพาะเจ้าของหรือแอดมิน` : "§cร้านนี้เก็บได้เฉพาะแอดมิน");
  player.playSound("note.bass");
}

// Picked-up shop goes back into the inventory as the item that places it
export function pickUp(player, entity, quiet = false) {
  if (!alive(entity)) return;
  if (!canPickUp(player, entity)) {
    if (player && !quiet) refusePickUp(player, entity);
    return;
  }
  const id = entity.typeId;
  const item = id.startsWith("kiosk:") ? id : `${id}_placer`;
  const where = entity.location;
  const dim = entity.dimension;
  entity.remove();
  try {
    const leftover = player?.getComponent("minecraft:inventory")?.container?.addItem(new ItemStack(item, 1));
    if (leftover || !player) dim.spawnItem(leftover ?? new ItemStack(item, 1), where);
  } catch (e) {
    try {
      dim.spawnItem(new ItemStack(item, 1), where);
    } catch (err) {}
  }
  player?.sendMessage("§e[ร้าน] เก็บร้านเข้ากระเป๋าแล้ว");
  player?.playSound("random.pop");
}

export function initVending() {
  world.afterEvents.playerInteractWithEntity.subscribe((event) => {
    const id = event.target?.typeId;
    if (!MACHINES[id] && !SHOPS[id]) return;
    shopLog("interact", id);
    if (SHOPS[id] && event.player.isSneaking) {
      system.run(() => pickUp(event.player, event.target));
      return;
    }
    openFor(event.player, event.target);
  });

  // Same click seen through the entity's own event (works even when the interact event above is not sent)
  try {
  world.afterEvents.dataDrivenEntityTrigger.subscribe(
    (event) => {
      const entity = event.entity;
      if (!alive(entity)) return;
      shopLog(event.eventId, entity.typeId);
      const player = whoUsed(entity);
      if (event.eventId === "succubi:shop_pickup") {
        // the interact event above names the real player; this guess only helps when that event is missing
        if (SHOPS[entity.typeId]) system.runTimeout(() => pickUp(player, entity, true), 2);
      } else {
        openFor(player, entity);
      }
    },
    { eventTypes: ["succubi:shop_use", "succubi:shop_pickup"] }
  );
  } catch (e) {
    console.warn("[Succubi] dataDrivenEntityTrigger unavailable: " + e);
  }

  // Remember who is placing a shop, so the spawned entity can be given an owner
  world.afterEvents.itemUseOn.subscribe((event) => {
    const type = placedType(event.itemStack?.typeId);
    if (!event.source || (!MACHINES[type] && !SHOPS[type])) return;
    const b = event.block?.location ?? event.source.location;
    pendingPlace.set(event.source.id, { id: type, tick: system.currentTick, at: b, name: event.source.name });
  });
  world.afterEvents.playerLeave.subscribe((event) => pendingPlace.delete(event.playerId));

  // A freshly placed machine turns to face whoever placed it
  world.afterEvents.entitySpawn.subscribe((event) => {
    const entity = event.entity;
    if (!entity || (!MACHINES[entity.typeId] && !SHOPS[entity.typeId])) return;
    // "Loaded" = an existing shop coming back with its chunk: it keeps its owner and its facing
    if (event.cause === "Loaded") return;
    const placed = event.cause === "Spawned";
    try {
      if (entity.getDynamicProperty(OWNER) === undefined) claim(entity, placed);
    } catch (e) {}
    if (!MACHINES[entity.typeId] && !FACE_ON_PLACE.includes(entity.typeId)) return;
    system.runTimeout(() => {
      try {
        const player = entity.dimension.getPlayers({ location: entity.location, closest: 1, maxDistance: 12 })[0];
        if (player) entity.teleport(entity.location, { facingLocation: { x: player.location.x, y: entity.location.y, z: player.location.z } });
      } catch (e) {}
    }, 1);
  });

  // Creative + sneak + hit = pick the machine up
  world.afterEvents.entityHitEntity.subscribe((event) => {
    const machine = event.hitEntity;
    const player = event.damagingEntity;
    if (!(MACHINES[machine?.typeId] || SHOPS[machine?.typeId]) || player?.typeId !== "minecraft:player") return;
    shopLog("hit", machine.typeId);
    try {
      if (player.isSneaking && String(player.getGameMode?.()).toLowerCase() === "creative") return pickUp(player, machine);
      if (!player.isSneaking) openFor(player, machine); // hitting a shop opens it too
    } catch (e) {}
  });
}
