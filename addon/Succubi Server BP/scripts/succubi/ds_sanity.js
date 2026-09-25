import { world, BlockTypes, BlockVolume, EquipmentSlot } from "@minecraft/server";
import { phaseOf } from "./daytime.js";

// Don't Starve style sanity from the world around the player (settings: สติ -> "สติแบบ Don't Starve").
// Values are sanity per second (sanity is 0-100); sanity.js adds them to its own per-second change.
//   overworld, under the open sky: dusk -0.02 · night -0.05 (not while asleep)
//   in the dark (anywhere at night, or deep underground by day) with no light nearby and none in hand: -0.08
//   next to a campfire: +0.05, and it counts as light
//   picking flowers: +3 each (at most 20 per 5 minutes), a wither rose: -5
//   raw meat / fish: -2 to -4, cooked meat / fish and stews: +2 to +5 (on top of the pack's own food list)
const CAMPFIRES = ["minecraft:campfire", "minecraft:soul_campfire"];
const LIGHT_BLOCKS = [
  "minecraft:torch", "minecraft:soul_torch", "minecraft:redstone_torch", "minecraft:lantern", "minecraft:soul_lantern",
  "minecraft:campfire", "minecraft:soul_campfire", "minecraft:glowstone", "minecraft:sea_lantern",
  "minecraft:shroomlight", "minecraft:lit_pumpkin", "minecraft:lit_redstone_lamp", "minecraft:beacon",
  "minecraft:end_rod", "minecraft:fire", "minecraft:soul_fire", "minecraft:lava", "minecraft:flowing_lava",
  "minecraft:ochre_froglight", "minecraft:verdant_froglight", "minecraft:pearlescent_froglight",
  "minecraft:lit_furnace", "minecraft:lit_smoker", "minecraft:lit_blast_furnace"
];
const HAND_LIGHTS = new Set([
  "minecraft:torch", "minecraft:soul_torch", "minecraft:redstone_torch", "minecraft:lantern", "minecraft:soul_lantern",
  "minecraft:glowstone", "minecraft:sea_lantern", "minecraft:shroomlight", "minecraft:lit_pumpkin",
  "minecraft:ochre_froglight", "minecraft:verdant_froglight", "minecraft:pearlescent_froglight", "minecraft:lava_bucket"
]);

// only ids this game version knows (an unknown id would make the whole block search fail)
let known;
function lights() {
  if (!known) {
    known = { lights: LIGHT_BLOCKS.filter((id) => BlockTypes.get(id)), fires: CAMPFIRES.filter((id) => BlockTypes.get(id)) };
  }
  return known;
}

const fl = Math.floor;
// true / false, or undefined when the area cannot be searched (unloaded, error): callers treat that as "lit"
function nearAny(dim, loc, types, r, down, up) {
  if (!types.length) return undefined;
  try {
    const volume = new BlockVolume(
      { x: fl(loc.x) - r, y: fl(loc.y) - down, z: fl(loc.z) - r },
      { x: fl(loc.x) + r, y: fl(loc.y) + up, z: fl(loc.z) + r }
    );
    return dim.containsBlock(volume, { includeTypes: types });
  } catch (e) {
    return undefined;
  }
}

function holdsLight(player) {
  try {
    const eq = player.getComponent("minecraft:equippable");
    return [EquipmentSlot.Mainhand, EquipmentSlot.Offhand].some((slot) => HAND_LIGHTS.has(eq?.getEquipment(slot)?.typeId));
  } catch (e) {
    return false;
  }
}

// how many blocks of cover are above the head (below 1 = open sky). There is no light-level API in this
// script version, so "deep underground" = 6+ blocks of cover below y 55 (a roof or a tree is not a cave)
function cover(dim, loc) {
  try {
    const top = dim.getTopmostBlock({ x: loc.x, z: loc.z });
    return top ? top.location.y - loc.y : -64;
  } catch (e) {
    return -64;
  }
}

export function worldSanity(player, dim, loc) {
  const { lights: lightTypes, fires } = lights();
  let d = 0;
  const campfire = nearAny(dim, loc, fires, 4, 2, 2) === true;
  if (campfire) d += 0.05;
  if (dim.id !== "minecraft:overworld" || player.isSleeping) return d;
  let phase = "day";
  try {
    phase = phaseOf(world.getTimeOfDay());
  } catch (e) {}
  const depth = cover(dim, loc);
  const sky = depth < 1;
  if (sky && phase === "night") d -= 0.05;
  else if (sky && phase === "dusk") d -= 0.02;
  const needsLight = phase === "night" || (depth >= 6 && loc.y < 55);
  if (needsLight && !campfire && !holdsLight(player) && nearAny(dim, loc, lightTypes, 5, 2, 3) === false) d -= 0.08;
  return d;
}

// ---------------------------------------------------------------- flowers
const FLOWERS = new Set([
  "minecraft:dandelion", "minecraft:yellow_flower", "minecraft:poppy", "minecraft:red_flower", "minecraft:blue_orchid",
  "minecraft:allium", "minecraft:azure_bluet", "minecraft:red_tulip", "minecraft:orange_tulip", "minecraft:white_tulip",
  "minecraft:pink_tulip", "minecraft:oxeye_daisy", "minecraft:cornflower", "minecraft:lily_of_the_valley",
  "minecraft:sunflower", "minecraft:lilac", "minecraft:rose_bush", "minecraft:peony", "minecraft:double_plant",
  "minecraft:torchflower", "minecraft:pink_petals", "minecraft:pitcher_plant", "minecraft:flowering_azalea",
  "minecraft:spore_blossom"
]);
const FLOWER_GAIN = 3;
const FLOWER_CAP = 20; // per 5 minutes, so a bone meal flower farm is not a sanity fountain
const FLOWER_WINDOW = 5 * 60 * 1000;
const picked = new Map(); // player id -> [[Date.now(), gain]]

export function flowerSanity(player, blockId) {
  if (blockId === "minecraft:wither_rose") return -5;
  if (!FLOWERS.has(blockId)) return 0;
  const now = Date.now();
  const list = (picked.get(player.id) ?? []).filter(([t]) => now - t < FLOWER_WINDOW);
  const got = list.reduce((sum, [, g]) => sum + g, 0);
  const gain = Math.max(0, Math.min(FLOWER_GAIN, FLOWER_CAP - got));
  if (gain > 0) list.push([now, gain]);
  picked.set(player.id, list);
  return gain;
}

export const forgetFlowers = (playerId) => picked.delete(playerId);

// ---------------------------------------------------------------- food (only with the switch on)
export const DS_FOOD = {
  "minecraft:beef": -3,
  "minecraft:porkchop": -3,
  "minecraft:chicken": -4,
  "minecraft:mutton": -3,
  "minecraft:rabbit": -3,
  "minecraft:cod": -2,
  "minecraft:salmon": -2,
  "minecraft:tropical_fish": -2,
  "minecraft:cooked_mutton": 2,
  "minecraft:cooked_rabbit": 2,
  "minecraft:cooked_cod": 2,
  "minecraft:cooked_salmon": 2,
  "minecraft:rabbit_stew": 5,
  "minecraft:mushroom_stew": 3,
  "minecraft:beetroot_soup": 3
};
