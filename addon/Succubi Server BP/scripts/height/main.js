import { world, system, EquipmentSlot } from "@minecraft/server";
import { CONFIG } from "./config.js";
import { applyHeight, getHeightCm, forget, markFight, enforceLimits, bodyStats } from "./height.js";
import { heightPoints } from "./body.js";
import { onSettingChange, isHeightSetting, num } from "../succubi/settings_store.js";
import { onAdjusterUse, initTiltMode } from "./ui.js";

const GUN_NAMESPACES = ["trenbankai:", "c7afd424"];
const HIT_CAUSES = ["entityAttack", "projectile"];

function holdsGun(player) {
  try {
    const id = player.getComponent("minecraft:equippable")?.getEquipment(EquipmentSlot.Mainhand)?.typeId ?? "";
    return GUN_NAMESPACES.some((ns) => id.startsWith(ns));
  } catch (e) {
    return false;
  }
}

// How much of this hit the height rules change (1 = as the game dealt it):
//  - the hitter's melee strength (short players hit lighter, tall players harder; guns and arrows keep theirs)
//  - the victim's damage taken from hits, and fall damage
export function hitFactor(event) {
  const src = event.damageSource;
  const cause = src?.cause;
  let factor = 1;
  const hitter = src?.damagingEntity;
  if (hitter?.typeId === "minecraft:player" && cause === "entityAttack" && !src.damagingProjectile && !holdsGun(hitter)) {
    factor *= bodyStats(getHeightCm(hitter)).damage;
  }
  const victim = event.hurtEntity;
  if (victim?.typeId === "minecraft:player") {
    const st = bodyStats(getHeightCm(victim));
    if (cause === "fall") factor *= st.fall;
    else if (HIT_CAUSES.includes(cause)) factor *= st.hurt;
  }
  return factor;
}

// The game has already applied the normal damage; the difference is taken from / given back to the victim
// (no potion effects). A hit the game already made lethal cannot be undone.
export function scaleHit(event) {
  if (!(event.damage > 0)) return;
  const factor = hitFactor(event);
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
    system.run(() => onAdjusterUse(player));
  });

  world.afterEvents.playerSpawn.subscribe((event) => {
    const player = event.player;
    if (!player) return;
    forget(player.id);
    system.runTimeout(() => {
      try {
        enforceLimits(player);
        applyHeight(player, true, false, true);
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
      forget(player.id, true, true);
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

  // height settings changed: everyone's HP, speed and hunger follow at once, heights outside a new range are pulled in
  onSettingChange((name) => {
    if (!isHeightSetting(name)) return;
    for (const player of world.getAllPlayers()) {
      try {
        enforceLimits(player);
        applyHeight(player, true);
      } catch (e) {}
    }
  });

  initTiltMode();

  const { lo, std, hi } = heightPoints();
  console.warn(
    `[Kotarus Height + HP System] players ${lo}-${hi} cm (standard ${std}, admins ${CONFIG.minCm}-${CONFIG.maxCm}), ` +
      `change every ${num("h_cooldown")} min; height sets HP, speed, strength, fall damage, hunger and damage taken`
  );
}
