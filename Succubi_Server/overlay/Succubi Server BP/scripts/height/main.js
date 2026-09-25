import { world, system, EquipmentSlot } from "@minecraft/server";
import { CONFIG } from "./config.js";
import { applyHeight, getHeightCm, forget, markFight, enforceLimits, bodyStats } from "./height.js";
import { onSettingChange } from "../succubi/settings_store.js";
import { openHeightForm } from "./ui.js";

const GUN_NAMESPACES = ["trenbankai:", "c7afd424"];

function holdsGun(player) {
  try {
    const id = player.getComponent("minecraft:equippable")?.getEquipment(EquipmentSlot.Mainhand)?.typeId ?? "";
    return GUN_NAMESPACES.some((ns) => id.startsWith(ns));
  } catch (e) {
    return false;
  }
}

// Melee hits follow the hitter's height: short players hit lighter, tall players harder (no potion effects).
// The game has already applied the normal damage; the difference is taken from / given back to the victim.
// Guns and arrows keep their own damage.
export function scaleHit(event) {
  const src = event.damageSource;
  const hitter = src?.damagingEntity;
  if (!hitter || hitter.typeId !== "minecraft:player" || src.cause !== "entityAttack" || src.damagingProjectile) return;
  if (!(event.damage > 0) || holdsGun(hitter)) return;
  const factor = bodyStats(getHeightCm(hitter)).damage;
  if (Math.abs(factor - 1) < 0.005) return;
  const victim = event.hurtEntity;
  try {
    if (!victim?.isValid()) return;
    const health = victim.getComponent("minecraft:health");
    if (!health || !(health.currentValue > 0)) return; // already dead: nothing to give back or take
    const next = Math.max(0, Math.min(health.effectiveMax, health.currentValue - event.damage * (factor - 1)));
    health.setCurrentValue(next);
    if (next <= 0) {
      // the heavier hit is lethal: make sure the victim really goes down
      system.runTimeout(() => {
        try {
          if (victim.isValid() && (victim.getComponent("minecraft:health")?.currentValue ?? 1) <= 0) victim.kill();
        } catch (e) {}
      }, 2);
    }
  } catch (e) {}
}

export function initHeightSystem() {
  world.afterEvents.itemUse.subscribe((event) => {
    const player = event.source;
    const item = event.itemStack;
    if (!player || !item || item.typeId !== CONFIG.itemId) return;
    system.run(() => {
      openHeightForm(player).catch(() => {});
    });
  });

  world.afterEvents.playerSpawn.subscribe((event) => {
    const player = event.player;
    if (!player) return;
    forget(player.id);
    system.runTimeout(() => {
      try {
        enforceLimits(player);
        applyHeight(player, true);
      } catch (e) {}
    }, 10);
  });

  world.afterEvents.playerLeave.subscribe((event) => {
    forget(event.playerId);
  });

  // Fights lock height changes for a few seconds (both the one hit and the one hitting)
  world.afterEvents.entityHurt.subscribe((event) => {
    markFight(event.hurtEntity);
    markFight(event.damageSource?.damagingEntity);
    scaleHit(event);
  });

  try {
    world.afterEvents.playerDimensionChange.subscribe((event) => {
      const player = event.player;
      if (!player) return;
      forget(player.id, true);
      system.runTimeout(() => {
        try {
          applyHeight(player, true);
        } catch (e) {}
      }, 10);
    });
  } catch (e) {}

  system.runInterval(() => {
    for (const player of world.getAllPlayers()) {
      try {
        applyHeight(player, getHeightCm(player) !== CONFIG.baseCm, true);
      } catch (e) {}
    }
  }, CONFIG.reapplyIntervalTicks);

  // base HP or the height switches changed in the settings: everyone's HP and speed follow at once
  onSettingChange((name) => {
    if (!["hp_base", "height_hp", "height_speed", "height_damage", "*"].includes(name)) return;
    for (const player of world.getAllPlayers()) {
      try {
        applyHeight(player, true);
      } catch (e) {}
    }
  });

  console.warn(
    `[Kotarus Height + HP System] players ${CONFIG.playerMinCm}-${CONFIG.playerMaxCm} cm (admins ${CONFIG.minCm}-${CONFIG.maxCm}), ` +
      `change every ${CONFIG.cooldownSeconds}s, height sets HP (half to double the base), speed and melee strength`
  );
}
