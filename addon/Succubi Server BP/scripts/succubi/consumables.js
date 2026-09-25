import { world, system } from "@minecraft/server";
import { PRODUCT_BY_ID } from "./products.js";

// Effects of drinks (thirst itself is handled in thirst.js)
export function applyProduct(player, item) {
  const product = PRODUCT_BY_ID.get(item.typeId);
  if (!product) return false;
  for (const e of product.effects) player.addEffect(e.effect, e.seconds * 20, { amplifier: e.amplifier, showParticles: true });
  for (const id of product.cure ?? []) {
    try {
      player.removeEffect(id);
    } catch (e) {}
  }
  if (product.heal > 0) {
    const health = player.getComponent("minecraft:health");
    const max = Number(player.getDynamicProperty("kotarus:max_hp")) || health?.effectiveMax || 100;
    if (health) health.setCurrentValue(Math.min(max, health.currentValue + product.heal));
  }
  return true;
}

// Items from /give or the creative menu get the same lore as the ones from the machines
function syncLore(player) {
  const container = player.getComponent("minecraft:inventory")?.container;
  if (!container) return;
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    const product = item && PRODUCT_BY_ID.get(item.typeId);
    if (!product) continue;
    const lore = item.getLore();
    if (lore.length === product.lore.length && lore.every((line, j) => line === product.lore[j])) continue;
    item.setLore(product.lore);
    container.setItem(i, item);
  }
}

export function initConsumables() {
  world.afterEvents.itemCompleteUse.subscribe((event) => {
    if (event.source && event.itemStack) {
      try {
        applyProduct(event.source, event.itemStack);
      } catch (e) {}
    }
  });
  system.runInterval(() => {
    for (const player of world.getAllPlayers()) {
      try {
        syncLore(player);
      } catch (e) {}
    }
  }, 40);
}
