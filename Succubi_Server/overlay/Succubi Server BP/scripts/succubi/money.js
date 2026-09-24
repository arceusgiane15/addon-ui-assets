import { world, system, ItemStack, EquipmentSlot, ItemLockMode } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";
import { getBalance, setBalance, formatBaht } from "./economy.js";
import { openAmulets } from "./amulets.js";
import { openPersonal } from "./personal.js";

export const WALLET_ID = "succubi:wallet";
// Invisible colour codes in a form title pick the skin RP ui/server_form.json draws
export const WALLET_FLAG = "§0§9§8§7";
export const WITHDRAW_FLAG = "§0§9§8§6";
export const WITHDRAW_AMOUNTS = [1, 5, 10, 20, 50, 100, 500, 1000];

// Largest first: a withdrawal is paid out with as few notes/coins as possible
export const CASH = [
  { id: "succubi:banknote_1000", value: 1000 },
  { id: "succubi:banknote_500", value: 500 },
  { id: "succubi:banknote_100", value: 100 },
  { id: "succubi:banknote_50", value: 50 },
  { id: "succubi:banknote_20", value: 20 },
  { id: "succubi:coin_10", value: 10 },
  { id: "succubi:coin_5", value: 5 },
  { id: "succubi:coin_1", value: 1 }
];
const VALUE = new Map(CASH.map((c) => [c.id, c.value]));
const STACK = 64;

export const cashValue = (typeId) => VALUE.get(typeId) ?? 0;
const inventoryOf = (player) => player.getComponent("minecraft:inventory")?.container;

export function breakdown(amount) {
  let left = Math.floor(amount);
  const parts = [];
  for (const c of CASH) {
    const count = Math.floor(left / c.value);
    if (count > 0) {
      parts.push({ id: c.id, value: c.value, count });
      left -= count * c.value;
    }
  }
  return parts;
}

export function hasWallet(player) {
  const container = inventoryOf(player);
  if (container) {
    for (let i = 0; i < container.size; i++) {
      if (container.getItem(i)?.typeId === WALLET_ID) return true;
    }
  }
  try {
    return player.getComponent("minecraft:equippable")?.getEquipment(EquipmentSlot.Offhand)?.typeId === WALLET_ID;
  } catch (e) {
    return false;
  }
}

export function countCash(player) {
  const container = inventoryOf(player);
  let total = 0;
  if (!container) return 0;
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    if (item) total += cashValue(item.typeId) * item.amount;
  }
  return total;
}

// Moves every note/coin in the inventory into the wallet balance
export function depositAllCash(player) {
  const container = inventoryOf(player);
  if (!container) return 0;
  let total = 0;
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    const value = item ? cashValue(item.typeId) : 0;
    if (!value) continue;
    total += value * item.amount;
    container.setItem(i, undefined);
  }
  if (total > 0) setBalance(player, getBalance(player) + total);
  return total;
}

// Can all stacks be added (topping up existing stacks first, then empty slots)?
export function canFit(container, parts) {
  let empty = 0;
  const room = new Map();
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    if (!item) {
      empty++;
    } else if (VALUE.has(item.typeId)) {
      room.set(item.typeId, (room.get(item.typeId) ?? 0) + (item.maxAmount - item.amount));
    }
  }
  let stacks = 0;
  for (const p of parts) stacks += Math.ceil(Math.max(0, p.count - (room.get(p.id) ?? 0)) / STACK);
  return stacks <= empty;
}

export function withdraw(player, amount) {
  if (!Number.isInteger(amount) || amount <= 0) return { ok: false, reason: "invalid" };
  const balance = getBalance(player);
  if (amount > balance) return { ok: false, reason: "balance" };
  const container = inventoryOf(player);
  if (!container) return { ok: false, reason: "inventory" };
  const parts = breakdown(amount);
  if (!canFit(container, parts)) return { ok: false, reason: "space" };
  setBalance(player, balance - amount);
  for (const p of parts) {
    for (let left = p.count; left > 0; left -= STACK) {
      const leftover = container.addItem(new ItemStack(p.id, Math.min(STACK, left)));
      if (leftover) player.dimension.spawnItem(leftover, player.location);
    }
  }
  return { ok: true, parts };
}

async function show(form, player) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const response = await form.show(player);
    if (!response.canceled || response.cancelationReason !== "UserBusy") return response;
    await new Promise((resolve) => system.runTimeout(resolve, 10));
  }
  return undefined;
}

const FAIL_TEXT = {
  invalid: "จำนวนไม่ถูกต้อง",
  balance: "เงินในกระเป๋าไม่พอ",
  space: "ช่องเก็บของไม่พอ เคลียร์ช่องก่อน",
  inventory: "เปิดช่องเก็บของไม่ได้"
};

// Withdraw screen: one button per amount, greyed out when the balance is short.
// The screen reopens after every press, so players can tap as many times as they like.
export async function openWithdraw(player, note = "") {
  const balance = getBalance(player);
  const form = new ActionFormData()
    .title(`§lถอนเงิน${WITHDRAW_FLAG}`)
    .body(`§8ยอดในกระเป๋า §l§1${formatBaht(balance)} บาท§r\n${note || "§8กดจำนวนที่จะถอน กดซ้ำได้เรื่อย ๆ"}`);
  for (const amount of WITHDRAW_AMOUNTS) {
    const enough = balance >= amount;
    form.button(`${enough ? "§l" : "§7"}${formatBaht(amount)}`, `textures/ui/succubi_wallet/amt_${amount}${enough ? "" : "_off"}`);
  }
  form.button("§lกลับ", "textures/ui/succubi_wallet/amt_back");
  form.button("§lปิด", "textures/ui/succubi_wallet/amt_close");
  const response = await show(form, player);
  if (!response || response.canceled) return;
  const index = response.selection;
  if (index < WITHDRAW_AMOUNTS.length) {
    const amount = WITHDRAW_AMOUNTS[index];
    const result = withdraw(player, amount);
    if (result.ok) player.playSound("random.pop");
    return openWithdraw(player, result.ok ? `§1ถอนแล้ว ${formatBaht(amount)} บาท` : `§4${FAIL_TEXT[result.reason]}`);
  }
  if (index === WITHDRAW_AMOUNTS.length) return openWallet(player);
}

export async function openWallet(player, note = "") {
  const form = new ActionFormData()
    .title(`§lกระเป๋าตังค์${WALLET_FLAG}`)
    .body(`§8ยอดในกระเป๋า\n§l§1${formatBaht(getBalance(player))} บาท§r\n\n§8เงินสดในตัว\n§l§4${formatBaht(countCash(player))} บาท${note ? `§r\n\n${note}` : ""}`)
    .button("ฝากเงิน", "textures/ui/succubi_wallet/btn_deposit_s")
    .button("ถอนเงิน", "textures/ui/succubi_wallet/btn_withdraw_s")
    .button("เครื่องราง", "textures/ui/succubi_wallet/btn_amulet_s")
    .button("ตั้งค่า", "textures/ui/succubi_wallet/btn_settings_s"); // close = the X in the corner
  const response = await show(form, player);
  if (!response || response.canceled) return;
  if (response.selection === 0) {
    const total = depositAllCash(player);
    if (total > 0) player.playSound("random.orb");
    return openWallet(player, total > 0 ? `§1ฝากแล้ว +${formatBaht(total)} บาท` : "§4ไม่มีเงินสดในตัว");
  }
  if (response.selection === 1) return openWithdraw(player);
  if (response.selection === 2) return openAmulets(player);
  if (response.selection === 3) return openPersonal(player);
}

// Right-click with notes/coins in hand = put that stack straight into the wallet
function quickDeposit(player) {
  const equippable = player.getComponent("minecraft:equippable");
  const held = equippable?.getEquipment(EquipmentSlot.Mainhand);
  const value = held ? cashValue(held.typeId) : 0;
  if (!value) return;
  if (!hasWallet(player)) {
    player.onScreenDisplay.setActionBar("§eต้องมีกระเป๋าตังค์ในตัวก่อนถึงจะเก็บเงินได้");
    return;
  }
  const total = value * held.amount;
  equippable.setEquipment(EquipmentSlot.Mainhand, undefined);
  setBalance(player, getBalance(player) + total);
  player.onScreenDisplay.setActionBar(`§a+${formatBaht(total)} บาท เข้ากระเป๋าแล้ว`);
  player.playSound("random.orb");
}

// Every player carries a wallet locked into the right-most hotbar slot (kept on death)
export function ensureWallet(player) {
  const container = inventoryOf(player);
  if (!container) return false;
  const current = container.getItem(8);
  if (current?.typeId === WALLET_ID && current.lockMode === ItemLockMode.slot) return false;
  const wallet = new ItemStack(WALLET_ID, 1);
  wallet.lockMode = ItemLockMode.slot;
  wallet.keepOnDeath = true;
  container.setItem(8, wallet);
  if (current && current.typeId !== WALLET_ID) {
    const leftover = container.addItem(current);
    if (leftover) player.dimension.spawnItem(leftover, player.location);
  }
  return true;
}

export function initMoneySystem() {
  world.afterEvents.playerSpawn.subscribe((event) => {
    system.runTimeout(() => {
      try {
        ensureWallet(event.player);
      } catch (e) {}
    }, 20);
  });
  world.afterEvents.itemUse.subscribe((event) => {
    const player = event.source;
    const item = event.itemStack;
    if (!player || !item) return;
    if (item.typeId === WALLET_ID) {
      system.run(() => {
        openWallet(player).catch(() => {});
      });
    } else if (VALUE.has(item.typeId)) {
      system.run(() => {
        try {
          quickDeposit(player);
        } catch (e) {}
      });
    }
  });
}
