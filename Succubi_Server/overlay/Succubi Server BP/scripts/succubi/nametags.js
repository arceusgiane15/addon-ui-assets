import { world, system } from "@minecraft/server";
import { enabled } from "./settings_store.js";

// Player name tags: "always" (vanilla) or "near" = only while someone looks straight at you.
// Replaces the old "No Nametag" subpack; admins switch it in the settings item, no pack reload needed.
// player.json (both the Succubi and the Succubi Guns one) has the matching component group + events.
export function applyNametag(player) {
  try {
    player.triggerEvent(enabled("nametag_near") ? "succubi:nametag_near" : "succubi:nametag_always");
  } catch (e) {}
}

export function applyNametagsToAll() {
  for (const player of world.getAllPlayers()) applyNametag(player);
}

export function initNametags() {
  world.afterEvents.playerSpawn.subscribe((event) => {
    if (event.player) system.runTimeout(() => applyNametag(event.player), 5);
  });
}
