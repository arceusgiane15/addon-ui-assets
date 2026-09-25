import { world, system, ItemStack, EquipmentSlot } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { HOOKS } from "./hooks.js";
import { addSanity } from "./sanity.js";
import { enabled } from "./settings_store.js";

// Amulets (เครื่องราง): up to 4 worn from the wallet screen. Worn amulets live in a player property, not the inventory.
export const AMULET_FLAG = "§0§9§5§2"; // skin in RP ui/server_form.json
export const PICKER_FLAG = "§0§9§5§3";
const PROP = "succubi:amulets";
const SLOTS = 4;
const TEX = "textures/ui/succubi_shops/";
export const AMULETS = {
  "luang_por": {
    "id": "succubi:amulet_luang_por",
    "name": "พระเครื่องหลวงพ่อ",
    "short": "พระหลวงพ่อ",
    "effect": "ฟื้นเลือด +1 ทุก 4 วินาที"
  },
  "takrut": {
    "id": "succubi:amulet_takrut",
    "name": "ตะกรุดโทน",
    "short": "ตะกรุดโทน",
    "effect": "สติฟื้นเอง +3/นาที, เรื่องแปลกเสียสติน้อยลง 30%"
  },
  "bia_kae": {
    "id": "succubi:amulet_bia_kae",
    "name": "เบี้ยแก้",
    "short": "เบี้ยแก้",
    "effect": "ล้างพิษ คลื่นไส้ และอาการเหี่ยวเฉาเองอัตโนมัติ"
  },
  "pha_yant": {
    "id": "succubi:amulet_pha_yant",
    "name": "ผ้ายันต์ห้าแถว",
    "short": "ผ้ายันต์",
    "effect": "ทนทาน (Resistance I) ตลอดเวลา"
  },
  "khiao_suea": {
    "id": "succubi:amulet_khiao_suea",
    "name": "เขี้ยวเสือ",
    "short": "เขี้ยวเสือ",
    "effect": "วิ่งเร็ว (Speed I) ตลอดเวลา"
  },
  "nang_kwak": {
    "id": "succubi:amulet_nang_kwak",
    "name": "นางกวัก",
    "short": "นางกวัก",
    "effect": "ลดราคาทุกร้าน 10%"
  },
  "kuman_thong": {
    "id": "succubi:amulet_kuman_thong",
    "name": "กุมารทอง",
    "short": "กุมารทอง",
    "effect": "ทุก 15 นาทีได้เงินสด 10-60 บาท"
  },
  "ta_thip": {
    "id": "succubi:amulet_ta_thip",
    "name": "ตาทิพย์",
    "short": "ตาทิพย์",
    "effect": "มองในที่มืด (Night Vision) ตลอดเวลา"
  },
  "cursed_doll": {
    "id": "succubi:amulet_cursed_doll",
    "name": "ตุ๊กตาสาปแช่ง",
    "short": "ตุ๊กตาสาป",
    "effect": "คนรอบตัว 20 บล็อกเจอเรื่องแปลกเร็วขึ้น 2 เท่า (ผู้ใส่เสียสติช้าๆ)"
  },
  "yant_kan_phi": {
    "id": "succubi:amulet_yant_kan_phi",
    "name": "ยันต์กันผี",
    "short": "ยันต์กันผี",
    "effect": "เรื่องแปลกช้าลงครึ่งหนึ่ง เสียสติน้อยลงครึ่ง กันคำสาปตุ๊กตา"
  },
  "lek_lai": {
    "id": "succubi:amulet_lek_lai",
    "name": "เหล็กไหล",
    "short": "เหล็กไหล",
    "effect": "ทนไฟ (Fire Resistance) ตลอดเวลา"
  },
  "moon": {
    "id": "succubi:amulet_moon",
    "name": "ลูกแก้วจันทรา",
    "short": "แก้วจันทรา",
    "effect": "กลางคืนสติฟื้นเอง +6/นาที"
  },
  "hanuman": {
    "id": "succubi:amulet_hanuman",
    "name": "หนุมานเชิญธง",
    "short": "หนุมาน",
    "effect": "แรงขึ้น (Strength I) ตลอดเวลา"
  },
  "mae_pho": {
    "id": "succubi:amulet_mae_pho",
    "name": "แม่โพสพ",
    "short": "แม่โพสพ",
    "effect": "อิ่มนาน: เติมความอิ่มนิดหน่อยทุกนาที"
  }
};
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
    if (key) form.button(`§f${AMULETS[key].short}\n§eแตะเพื่อถอด`, `${TEX}p_amuletui_${key}`);
    else form.button("§fช่องว่าง\n§eแตะเพื่อใส่", `${TEX}p_amuletui_empty`);
  }
  form.button("§lปิด", `${TEX}amt_close_am`);
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
  const form = new ActionFormData().title(`§lเลือกเครื่องราง${PICKER_FLAG}`).body("§eเลือกชิ้นที่\nจะใส่");
  for (const key of keys.slice(0, 18)) form.button(`§f${AMULETS[key].short}\n§eแตะเพื่อใส่`, `${TEX}p_amuletui_${key}`);
  form.button("§lกลับ", `${TEX}amt_back_am`);
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
