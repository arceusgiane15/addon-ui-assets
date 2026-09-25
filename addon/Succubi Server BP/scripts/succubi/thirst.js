import { world, system } from "@minecraft/server";
import { PRODUCT_BY_ID } from "./products.js";
import { enabled, num } from "./settings_store.js";
import { getHeightCm } from "../height/height.js";
import { hungerPercent } from "../height/body.js";

// Max water and how fast it drains are base stats (settings item -> สเตตัสพื้นฐาน -> น้ำ)
export const THIRST_MAX = 20; // the default max
export const thirstMax = () => num("thirst_max");
const PROP = "succubi:thirst";
const SPRINT_MULTIPLIER = 2.2;
const NETHER_MULTIPLIER = 1.6;
const LOW = 0.3; // 30%: slowness
const CRITICAL = 0.1; // 10%: slowness + weakness
const EMPTY_DAMAGE = 2; // every 4 seconds while at 0

// Thirst restored when the item is finished (drunk / eaten)
const DRINKS = {
  "minecraft:potion": 7,
  "minecraft:milk_bucket": 10,
  "minecraft:honey_bottle": 5,
  "minecraft:melon_slice": 3,
  "minecraft:mushroom_stew": 4,
  "minecraft:beetroot_soup": 4,
  "minecraft:rabbit_stew": 4,
  "minecraft:suspicious_stew": 4,
  "minecraft:sweet_berries": 1,
  "minecraft:glow_berries": 1,
  "minecraft:apple": 2,
  "minecraft:golden_apple": 3,
  "minecraft:enchanted_golden_apple": 6
};
const VENDING_DRINK = 10; // vending machine drinks are apples renamed with §e

export function getThirst(player) {
  const value = player.getDynamicProperty(PROP);
  const max = thirstMax();
  return typeof value === "number" ? Math.max(0, Math.min(max, value)) : max;
}

export function setThirst(player, value) {
  const clamped = Math.max(0, Math.min(thirstMax(), value));
  try {
    player.setDynamicProperty(PROP, clamped);
  } catch (e) {}
  return clamped;
}

export function thirstGain(item) {
  const product = PRODUCT_BY_ID.get(item.typeId);
  if (product) return product.thirst || 0;
  if (item.typeId === "minecraft:apple" && typeof item.nameTag === "string" && item.nameTag.startsWith("§e")) return VENDING_DRINK;
  return DRINKS[item.typeId] ?? 0;
}

function isExempt(player) {
  try {
    if (typeof player.getGameMode === "function") {
      const mode = String(player.getGameMode()).toLowerCase();
      return mode === "creative" || mode === "spectator";
    }
  } catch (e) {}
  return false;
}

export function tickThirst(player, second) {
  if (isExempt(player) || !enabled("thirst")) return;
  const before = getThirst(player);
  const max = thirstMax();
  let drain = 1 / num("thirst_seconds");
  drain *= hungerPercent(getHeightCm(player)) / 100; // tall bodies dry out faster (settings: ส่วนสูง -> หิวและน้ำ)
  if (player.isSprinting) drain *= SPRINT_MULTIPLIER;
  if (player.dimension.id === "minecraft:nether") drain *= NETHER_MULTIPLIER;
  const now = setThirst(player, before - drain);

  if (before > max * LOW && now <= max * LOW) player.onScreenDisplay.setActionBar("§eคอแห้งแล้ว รีบหาน้ำดื่ม");
  if (before > 0 && now <= 0) player.onScreenDisplay.setActionBar("§cขาดน้ำ! เลือดจะลดจนกว่าจะได้ดื่มน้ำ");

  if (now <= max * LOW) player.addEffect("slowness", 40, { amplifier: 0, showParticles: false });
  if (now <= max * CRITICAL) player.addEffect("weakness", 40, { amplifier: 0, showParticles: false });
  if (now <= 0 && second % 4 === 0) player.applyDamage(EMPTY_DAMAGE, { cause: "starve" });
}

let secondsElapsed = 0;

export function initThirstSystem() {
  world.afterEvents.itemCompleteUse.subscribe((event) => {
    const player = event.source;
    const item = event.itemStack;
    if (!player || !item) return;
    if (!enabled("thirst")) return;
    const gain = thirstGain(item);
    if (gain !== 0) setThirst(player, getThirst(player) + gain);
    if (gain < 0) player.onScreenDisplay.setActionBar("§cเผ็ดจนคอแห้ง! หาน้ำดื่มด้วย");
  });

  world.afterEvents.playerSpawn.subscribe((event) => {
    if (event.player && !event.initialSpawn) setThirst(event.player, thirstMax());
  });

  system.runInterval(() => {
    secondsElapsed++;
    for (const player of world.getAllPlayers()) {
      try {
        tickThirst(player, secondsElapsed);
      } catch (e) {}
    }
  }, 20);
}
