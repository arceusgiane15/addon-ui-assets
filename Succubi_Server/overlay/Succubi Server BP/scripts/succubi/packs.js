import { world, system, ItemTypes } from "@minecraft/server";
import { isAdmin } from "./settings_store.js";

// Guns are a separate pair of packs ("Succubi Guns BP/RP") so they can be removed without breaking anything.
// Both packs define the player (minecraft:player); the gun one must sit ABOVE this one in the world's
// behavior pack list, otherwise guns lose ammo / reload / attachments. Tell admins when that is wrong.
const TIP_SHOWN = "succubi:tip_guns_split";

export function gunsInstalled() {
  try {
    return !!ItemTypes.get("trenbankai:ak47");
  } catch (e) {
    return false;
  }
}

// The gun player.json defines the trenbankai:* properties; ours does not
function gunPlayerActive(player) {
  try {
    return player.getProperty("trenbankai:ammo") !== undefined;
  } catch (e) {
    return false;
  }
}

function check(player) {
  if (!isAdmin(player)) return;
  const guns = gunsInstalled();
  if (guns && !gunPlayerActive(player)) {
    player.sendMessage(
      "§c[Succubi] ลำดับแพ็คไม่ถูก: ให้ย้าย §fSuccubi Guns BP§c ไว้ §lเหนือ§r§c Succubi Server BP ในหน้า Behavior Packs ของโลก ไม่งั้นปืนจะยิง/รีโหลดไม่ได้"
    );
  } else if (!guns && world.getDynamicProperty(TIP_SHOWN) !== true) {
    world.setDynamicProperty(TIP_SHOWN, true);
    player.sendMessage(
      "§d[Succubi]§r ตั้งแต่ v1.1.0 ปืนแยกเป็นแพ็ค §fSuccubi Guns§r แล้ว ถ้าอยากมีปืนในโลกนี้ ให้เปิด Succubi Guns BP ในการตั้งค่าโลก (ปิดไว้ก็เล่นได้ปกติ)"
    );
  }
}

export function initPackCheck() {
  world.afterEvents.playerSpawn.subscribe((event) => {
    if (event.initialSpawn && event.player) system.runTimeout(() => check(event.player), 60);
  });
}
