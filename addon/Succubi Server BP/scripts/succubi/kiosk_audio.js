import { world, system } from "@minecraft/server";
import { runAs } from "./cmd.js";

// Haruto tea kiosk plays music + announcements from its RP animation.
// When the last kiosk is removed / dismantled, stop what is still playing.
const TEA_KIOSK = "kiosk:haruto_tea_kiosk";
const SOUNDS = ["kiosk.haruto_tea.bgm", "kiosk.haruto_tea.announcement"];

function stopFor(player) {
  for (const sound of SOUNDS) runAs(player, `stopsound @s ${sound}`); // server source: works without cheats
}

function anyTeaKiosk() {
  for (const id of ["overworld", "nether", "the_end"]) {
    try {
      if (world.getDimension(id).getEntities({ type: TEA_KIOSK }).length > 0) return true;
    } catch (e) {}
  }
  return false;
}

export function initKioskAudio() {
  world.afterEvents.entityDie.subscribe((event) => {
    const dead = event.deadEntity;
    if (dead?.typeId !== TEA_KIOSK) return;
    try {
      for (const player of dead.dimension.getPlayers({ location: dead.location, maxDistance: 48 })) stopFor(player);
    } catch (e) {
      for (const player of world.getAllPlayers()) stopFor(player);
    }
  });
  let hadKiosk = true;
  system.runInterval(() => {
    const has = anyTeaKiosk();
    if (!has && hadKiosk) for (const player of world.getAllPlayers()) stopFor(player);
    hadKiosk = has;
  }, 40);
}
