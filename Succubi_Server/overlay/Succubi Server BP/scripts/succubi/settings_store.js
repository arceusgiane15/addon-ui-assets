import { world } from "@minecraft/server";

// World-wide switches set from the settings item
const KEYS = {
  sanity: "succubi:cfg_sanity",
  thirst: "succubi:cfg_thirst",
  events: "succubi:cfg_events",
  rules: "succubi:cfg_rules",
  bloodmoon: "succubi:cfg_bloodmoon",
  nametag_near: "succubi:cfg_nametag_near", // player names only while looking at them (old "No Nametag" subpack)
  height_free: "succubi:cfg_height_free" // players may pick any height, no cooldown (old behaviour)
};
const DEFAULT_OFF = new Set(["nametag_near", "height_free"]);

export function enabled(key) {
  try {
    const v = world.getDynamicProperty(KEYS[key]);
    return v === undefined ? !DEFAULT_OFF.has(key) : v === true;
  } catch (e) {
    return !DEFAULT_OFF.has(key);
  }
}

export function setEnabled(key, value) {
  world.setDynamicProperty(KEYS[key], !!value);
}

// Admins: creative mode or the tag "succubi_admin" (/tag <name> add succubi_admin)
export function isAdmin(player) {
  try {
    if (player.hasTag("succubi_admin")) return true;
    return String(player.getGameMode?.()).toLowerCase() === "creative";
  } catch (e) {
    return false;
  }
}
