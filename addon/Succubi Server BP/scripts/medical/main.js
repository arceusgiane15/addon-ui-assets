import { world, system } from "@minecraft/server";
import { handleBandageHeal } from "./bandage.js";
import { handleMedkitRevive } from "./medkit.js";
import { handleSyringeInject } from "./syringe.js";
import "./weaponanim/engine.js";

export function initMedicalSystem() {
  world.afterEvents.itemUse.subscribe((event) => {
    const player = event.source;
    const item = event.itemStack;
    if (!player || !item) return;

    const id = item.typeId;
    if (id === "kotarus:bandage_blackpowder") {
      handleBandageHeal(player);
    } else if (id === "kotarus:syringe_blackpowder") {
      handleSyringeInject(player);
    } else if (id === "kotarus:medkit_blackpowder") {
      player.onScreenDisplay.setActionBar("§e[อุปกรณ์พยาบาล] คลิกขวาใส่เพื่อนเพื่อรักษา/ชุบชีวิต!");
    }
  });

  world.afterEvents.playerInteractWithEntity.subscribe((event) => {
    const player = event.player;
    const target = event.target;
    const item = event.itemStack;
    if (!player || !target || !item) return;
    if (target.typeId !== "minecraft:player") return;

    const id = item.typeId;
    if (id.startsWith("kotarus:medkit_") && !id.includes(":medkit_broken_")) {
      handleMedkitRevive(player, target);
    } else if (id.startsWith("kotarus:bandage_")) {
      handleBandageHeal(player, target);
    } else if (id.startsWith("kotarus:syringe_")) {
      handleSyringeInject(player, target);
    }
  });


  console.warn("[Medical System] Initialized (Bandage, Revival/Heal Medkit, Syringe)");
}
