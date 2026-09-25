import { world, system, EquipmentSlot } from "@minecraft/server";

// Negative status effects (Debuffs) to cleanse
// Positive buffs (regeneration, strength, speed, resistance, absorption, etc.) are NOT in this list and will NEVER be removed!
const DEBUFF_EFFECTS = [
    "poison",
    "fatal_poison",
    "wither",
    "slowness",
    "weakness",
    "nausea",
    "blindness",
    "darkness",
    "hunger",
    "mining_fatigue",
    "levitation",
    "bad_omen"
];

// Buff effects applied upon injection
const BUFF_DURATION_TICKS = 20 * 20; // 20 seconds (400 ticks)
const SPEED_AMPLIFIER = 1; // Speed II
const RESISTANCE_AMPLIFIER = 1; // Resistance II

// Set of players currently undergoing self-injection animation to prevent duplicate spam
const activeInjections = new Set();

/**
 * Handles selective debuff cleansing via tactical auto-injector syringe
 * @param {Player} player - The user who clicked to inject
 * @param {Player|null} target - Teammate target player if interacting, or null for self
 */
export function handleSyringeInject(player, target) {
    const recipient = target || player;
    const isSelf = recipient.id === player.id;

    if (isSelf) {
        if (activeInjections.has(player.id)) return;
        activeInjections.add(player.id);

        // Sound cue: pulling the safety pin ring at ~0.25s (tick 5)
        system.runTimeout(() => {
            if (player.isValid()) {
                player.dimension.playSound("block.beehive.shear", player.location, { volume: 0.7, pitch: 1.5 });
            }
        }, 5);

        // Injection peak: needle plunges into arm at ~0.8s (tick 16)
        system.runTimeout(() => {
            if (!player.isValid() || !recipient.isValid()) {
                activeInjections.delete(player.id);
                return;
            }

            executeCleanse(player, recipient, true);
        }, 16);

        // Animation completes at 1.5s (tick 30) - release lock (engine.js handles single-use consumption)
        system.runTimeout(() => {
            activeInjections.delete(player.id);
        }, 30);

    } else {
        // Interacting with teammate: instantaneous injection & manual item consumption
        executeCleanse(player, recipient, false);
        consumeHeldItem(player);
    }
}

function executeCleanse(player, recipient, isSelf) {
    let removedCount = 0;
    const removedNames = [];

    // 1. Cleanse negative debuffs
    for (const debuff of DEBUFF_EFFECTS) {
        try {
            const effect = recipient.getEffect(debuff);
            if (effect) {
                recipient.removeEffect(debuff);
                removedCount++;
                removedNames.push(debuff);
            }
        } catch (e) {
            // Ignored if effect not present
        }
    }

    // 2. Apply Speed II & Resistance II combat stim buffs
    try {
        recipient.addEffect("speed", BUFF_DURATION_TICKS, { amplifier: SPEED_AMPLIFIER, showParticles: true });
        recipient.addEffect("resistance", BUFF_DURATION_TICKS, { amplifier: RESISTANCE_AMPLIFIER, showParticles: true });
    } catch (e) {}

    // 3. Play enhanced injection audio & visual feedback
    recipient.dimension.playSound("random.fizz", recipient.location, { volume: 1.0, pitch: 1.2 });
    recipient.dimension.playSound("block.beehive.shear", recipient.location, { volume: 0.9, pitch: 0.9 });
    recipient.dimension.playSound("beacon.power", recipient.location, { volume: 0.7, pitch: 1.5 });

    try {
        recipient.dimension.spawnParticle("minecraft:villager_happy", {
            x: recipient.location.x,
            y: recipient.location.y + 1.2,
            z: recipient.location.z
        });
        recipient.dimension.spawnParticle("minecraft:totem_particle", {
            x: recipient.location.x,
            y: recipient.location.y + 1.0,
            z: recipient.location.z
        });
    } catch (e) {}

    // 4. Action bar display
    const cleanseText = removedCount > 0 ? ` + ล้าง ${removedCount} สถานะเสีย` : "";
    if (isSelf) {
        player.onScreenDisplay.setActionBar(`§a✔ ฉีดเซรั่มกระตุ้นสำเร็จ! วิ่งเร็วขึ้น + ทนทานขึ้น (20 วินาที)${cleanseText}`);
    } else {
        const targetName = recipient.nameTag || "เพื่อนร่วมทีม";
        player.onScreenDisplay.setActionBar(`§a✔ ฉีดเซรั่มกระตุ้นให้ ${targetName} สำเร็จ! [Speed II + Res II 20s]${cleanseText}`);
        recipient.onScreenDisplay.setActionBar(`§a✔ ได้รับเซรั่มกระตุ้นจาก ${player.nameTag || "เพื่อนร่วมทีม"}! [Speed II + Res II 20s]`);
    }
}

function consumeHeldItem(player) {
    const equipment = player.getComponent("minecraft:equippable");
    if (!equipment) return;

    const mainhand = equipment.getEquipment(EquipmentSlot.Mainhand);
    if (!mainhand) return;

    if (mainhand.amount > 1) {
        mainhand.amount -= 1;
        equipment.setEquipment(EquipmentSlot.Mainhand, mainhand);
    } else {
        equipment.setEquipment(EquipmentSlot.Mainhand, undefined);
    }
}
