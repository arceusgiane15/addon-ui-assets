import { world, system } from "@minecraft/server";
import { CONFIG } from "./config.js";
import { applyHeight, getHeightCm, forget, markFight, enforceLimits } from "./height.js";
import { openHeightForm } from "./ui.js";

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
        if (getHeightCm(player) === CONFIG.baseCm) continue;
        applyHeight(player, true);
      } catch (e) {}
    }
  }, CONFIG.reapplyIntervalTicks);

  console.warn(
    `[Kotarus Height + HP System] players ${CONFIG.playerMinCm}-${CONFIG.playerMaxCm} cm (admins ${CONFIG.minCm}-${CONFIG.maxCm}), ` +
      `change every ${CONFIG.cooldownSeconds}s, ${CONFIG.baseCm} cm = ${CONFIG.baseHp} HP`
  );
}
