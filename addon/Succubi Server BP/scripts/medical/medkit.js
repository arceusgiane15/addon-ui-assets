import { EquipmentSlot, ItemStack, world, system } from "@minecraft/server";
import { runAs } from "../succubi/cmd.js";

const REVIVE_TICKS = 70; // 3.5 seconds @ 20 TPS
const MAX_DISTANCE = 3.5; // Max distance in blocks between medic and downed player

// Active channeling revives: Map<medicId, ReviveSession>
const activeRevives = new Map();

export const DUR_LORE_PREFIX = "§r§7ความทนทาน: §f";
export const DUR_PROP = "kotarus:durability_damage";
export const DUR_TAG_PREFIX = "§r§8[kotarus_dur:";

/**
 * Updates durability damage and syncs with Dynamic Property and Lore metadata
 */
export function updateItemDurability(item, damage, maxDurability) {
    if (!item) return;
    const durComp = item.getComponent("minecraft:durability");
    if (durComp) {
        durComp.damage = damage;
    }
    try {
        item.setDynamicProperty(DUR_PROP, damage);
    } catch (e) {}

    const max = maxDurability || durComp?.maxDurability || 20;
    const remaining = Math.max(0, max - damage);
    const currentLore = (item.getLore() || []).filter(line => 
        !line.startsWith(DUR_LORE_PREFIX) && !line.startsWith(DUR_TAG_PREFIX)
    );
    currentLore.unshift(`${DUR_LORE_PREFIX}${remaining}/${max}`);
    currentLore.push(`${DUR_TAG_PREFIX}${damage}]`);
    item.setLore(currentLore);
}

/**
 * Restores durability damage from Dynamic Property or Lore metadata
 */
export function restoreItemDurabilityFromMetadata(item) {
    if (!item) return;
    const durComp = item.getComponent("minecraft:durability");
    if (!durComp) return;

    let savedDamage = null;

    // 1. Try dynamic property
    try {
        const propVal = item.getDynamicProperty(DUR_PROP);
        if (typeof propVal === "number" && !isNaN(propVal)) {
            savedDamage = propVal;
        }
    } catch (e) {}

    // 2. Try lore tag
    if (savedDamage === null) {
        const lore = item.getLore() || [];
        for (const line of lore) {
            if (line.startsWith(DUR_TAG_PREFIX)) {
                const numStr = line.substring(DUR_TAG_PREFIX.length).replace("]", "").trim();
                const parsed = parseInt(numStr, 10);
                if (!isNaN(parsed)) {
                    savedDamage = parsed;
                    break;
                }
            }
        }
    }

    if (savedDamage !== null && savedDamage >= 0) {
        durComp.damage = savedDamage;
        try {
            item.setDynamicProperty(DUR_PROP, savedDamage);
        } catch (e) {}
    }
}

/**
 * Starts or updates a medkit revive channeling session
 * @param {Player} player - The medic performing the revive
 * @param {Player} target - The downed teammate
 */
export function handleMedkitRevive(player, target) {
    if (!target || target.typeId !== "minecraft:player") {
        return;
    }

    if (!target.hasTag("kotarus:downed")) {
        // Field Triage: Heal injured teammate if not in downed state
        const healthComp = target.getComponent("minecraft:health");
        const maxHp = target.getDynamicProperty("kotarus:max_hp") || 100;
        if (healthComp && healthComp.currentValue < maxHp) {
            const healAmt = 50;
            const newHp = Math.min(maxHp, healthComp.currentValue + healAmt);
            healthComp.setCurrentValue(newHp);

            // Audio & Particle feedback
            target.dimension.playSound("armor.equip_leather", target.location);
            target.dimension.playSound("random.levelup", target.location, { volume: 0.6, pitch: 1.5 });
            target.dimension.spawnParticle("minecraft:villager_happy", {
                x: target.location.x,
                y: target.location.y + 1.0,
                z: target.location.z
            });

            player.sendMessage(`§a[กล่องพยาบาล] ทำการรักษาฉุกเฉินให้ ${target.name || "เพื่อนร่วมทีม"} สำเร็จ! (+${healAmt} HP)`);
            target.sendMessage(`§a[กล่องพยาบาล] ${player.name || "เพื่อนร่วมทีม"} ได้ทำการรักษาให้คุณ! (+${healAmt} HP)`);

            // Apply durability damage (1 use)
            const equippable = player.getComponent("minecraft:equippable");
            const held = equippable?.getEquipment(EquipmentSlot.Mainhand);
            if (held) {
                const curDam = (held.getDynamicProperty(DUR_PROP) || 0) + 1;
                if (curDam >= 20) {
                    equippable.setEquipment(EquipmentSlot.Mainhand, undefined);
                    player.dimension.playSound("random.break", player.location);
                    player.onScreenDisplay.setActionBar("§cอุปกรณ์ชุบชีวิตพังและหายไปแล้ว!");
                } else {
                    updateItemDurability(held, curDam, 20);
                    equippable.setEquipment(EquipmentSlot.Mainhand, held);
                }
            }
            return;
        } else {
            player.onScreenDisplay.setActionBar("§eเพื่อนร่วมทีมเลือดเต็มอยู่แล้ว!");
            return;
        }
    }

    // Prevent multiple concurrent revives by the same medic
    if (activeRevives.has(player.id)) {
        player.onScreenDisplay.setActionBar("§eคุณกำลังทำการปฐมพยาบาลอยู่แล้ว...");
        return;
    }

    // Check if target is already being revived by someone else
    for (const [medicId, session] of activeRevives.entries()) {
        if (session.targetId === target.id) {
            player.onScreenDisplay.setActionBar("§eมีเพื่อนร่วมหน่วยกำลังปฐมพยาบาลเป้าหมายนี้อยู่แล้ว!");
            return;
        }
    }

    const equipment = player.getComponent("minecraft:equippable");
    if (!equipment) return;
    const mainhand = equipment.getEquipment(EquipmentSlot.Mainhand);
    if (!mainhand || !mainhand.typeId.startsWith("kotarus:medkit_") || mainhand.typeId.includes(":medkit_broken_")) {
        player.onScreenDisplay.setActionBar("§cกล่องพยาบาลชำรุดหรือไม่ถูกต้อง!");
        return;
    }
    restoreItemDurabilityFromMetadata(mainhand);

    const initialPos = { x: player.location.x, y: player.location.y, z: player.location.z };
    const targetPos = { x: target.location.x, y: target.location.y, z: target.location.z };

    // Trigger full revive animation on player body
    try {
        runAs(player, 'playanimation @s animation.medkit_blackpowder.revive_body none 0.0 "" wa_medkitblackpowder_hit');
        runAs(player, 'playanimation @s animation.medkit_blackpowder.revive none 0.0 "" wa_medkitblackpowder_hit');
    } catch (e) {}

    // Audio feedback: unzipping / placing medkit on ground
    player.dimension.playSound("armor.equip_leather", player.location, { volume: 1.0, pitch: 0.9 });
    player.dimension.playSound("block.barrel.open", player.location, { volume: 0.8, pitch: 1.2 });

    let elapsed = 0;

    const intervalId = system.runInterval(() => {
        elapsed++;

        // 1. Check if players are still valid and connected
        if (!player.isValid() || !target.isValid()) {
            cancelRevive(player.id, "การปฐมพยาบาลถูกยกเลิก (ผู้เล่นตัดการเชื่อมต่อ)");
            return;
        }

        // 2. Check if target is still downed
        if (!target.hasTag("kotarus:downed")) {
            cancelRevive(player.id, "เป้าหมายได้รับการชุบชีวิตแล้ว");
            return;
        }

        // 3. Check distance limit
        const curPos = player.location;
        const curTargetPos = target.location;
        const distSq = (curPos.x - initialPos.x) ** 2 + (curPos.z - initialPos.z) ** 2;
        const targetDistSq = (curPos.x - curTargetPos.x) ** 2 + (curPos.y - curTargetPos.y) ** 2 + (curPos.z - curTargetPos.z) ** 2;

        if (distSq > (MAX_DISTANCE ** 2) || targetDistSq > (MAX_DISTANCE ** 2)) {
            cancelRevive(player.id, "§cการปฐมพยาบาลถูกยกเลิก (ขยับออกห่างเกินระยะ)");
            return;
        }

        // 4. Check held item
        const curEq = player.getComponent("minecraft:equippable");
        const curMain = curEq ? curEq.getEquipment(EquipmentSlot.Mainhand) : null;
        if (!curMain || (!curMain.typeId.startsWith("kotarus:medkit_") && !curMain.typeId.includes("use_skill1"))) {
            cancelRevive(player.id, "§cการปฐมพยาบาลถูกยกเลิก (เปลี่ยนไอเทมในมือ)");
            return;
        }

        // 5. Sound cues during CPR compressions
        if (elapsed === 16) {
            // Clamshell case pops open
            player.dimension.playSound("block.iron_trapdoor.open", player.location, { volume: 0.9, pitch: 1.3 });
        } else if (elapsed === 34 || elapsed === 48) {
            // CPR compression beats
            target.dimension.playSound("block.honey_block.step", target.location, { volume: 1.0, pitch: 0.8 });
            target.dimension.playSound("armor.equip_leather", target.location, { volume: 0.7, pitch: 1.1 });
        } else if (elapsed === 60) {
            // Case snaps shut
            player.dimension.playSound("block.iron_trapdoor.close", player.location, { volume: 0.8, pitch: 1.2 });
        }

        // 6. Actionbar progress bar
        const pct = Math.min(100, Math.floor((elapsed / REVIVE_TICKS) * 100));
        const filled = Math.floor(pct / 10);
        const empty = 10 - filled;
        const bar = "█".repeat(filled) + "░".repeat(empty);

        player.onScreenDisplay.setActionBar(`§eกำลังปฐมพยาบาล: §a[${bar}] §f${pct}%`);
        target.onScreenDisplay.setActionBar(`§eเพื่อนร่วมหน่วยกำลังปฐมพยาบาลคุณ: §a[${bar}] §f${pct}%`);

        // 7. Complete revive
        if (elapsed >= REVIVE_TICKS) {
            system.clearRun(intervalId);
            activeRevives.delete(player.id);
            completeRevive(player, target);
        }
    }, 1);

    activeRevives.set(player.id, {
        targetId: target.id,
        intervalId: intervalId
    });
}

/**
 * Cancels an ongoing revive session
 */
export function cancelRevive(medicId, reason = "§cการปฐมพยาบาลถูกยกเลิก!") {
    const session = activeRevives.get(medicId);
    if (!session) return;

    system.clearRun(session.intervalId);
    activeRevives.delete(medicId);

    const medic = world.getPlayers().find(p => p.id === medicId);
    if (medic && medic.isValid()) {
        medic.onScreenDisplay.setActionBar(reason);
        medic.dimension.playSound("random.break", medic.location, { volume: 0.6, pitch: 1.2 });
        try {
            runAs(medic, "stopanimation @s animation.medkit_blackpowder.revive_body");
            runAs(medic, "stopanimation @s animation.medkit_blackpowder.revive");
        } catch (e) {}
    }
}

/**
 * Handles damage interruption to cancel revive if medic or target is hurt
 */
export function handleMedkitDamageInterruption(hurtEntity) {
    if (!hurtEntity || hurtEntity.typeId !== "minecraft:player") return;

    // Check if hurtEntity is a medic channeling
    if (activeRevives.has(hurtEntity.id)) {
        cancelRevive(hurtEntity.id, "§cการปฐมพยาบาลถูกขัดจังหวะจากการถูกโจมตี!");
        return;
    }

    // Check if hurtEntity is a target currently being revived
    for (const [medicId, session] of activeRevives.entries()) {
        if (session.targetId === hurtEntity.id) {
            cancelRevive(medicId, "§cการปฐมพยาบาลถูกขัดจังหวะ! เป้าหมายได้รับความเสียหาย");
            return;
        }
    }
}

/**
 * Finalizes successful revival
 */
function completeRevive(player, target) {
    // 1. Revive the downed target
    target.removeTag("kotarus:downed");

    const targetHealth = target.getComponent("minecraft:health");
    if (targetHealth) {
        targetHealth.setCurrentValue(10);
    }

    // 2. Audio & Visual Feedback
    target.dimension.playSound("medic.revive", target.location);
    player.dimension.playSound("medic.revive", player.location);
    target.dimension.spawnParticle("minecraft:heart_particle", {
        x: target.location.x,
        y: target.location.y + 0.5,
        z: target.location.z
    });
    target.dimension.spawnParticle("minecraft:villager_happy", {
        x: target.location.x,
        y: target.location.y + 1.0,
        z: target.location.z
    });

    player.sendMessage("§aชุบชีวิตเพื่อนร่วมหน่วยสำเร็จ! (เลือดฟื้นฟู 10 HP)");
    target.sendMessage("§aคุณได้รับการชุบชีวิตโดยเพื่อนร่วมหน่วย! (เลือดฟื้นฟู 10 HP)");

    // 3. Durability deduction
    const equipment = player.getComponent("minecraft:equippable");
    if (!equipment) return;

    const mainhand = equipment.getEquipment(EquipmentSlot.Mainhand);
    if (!mainhand || !mainhand.typeId.startsWith("kotarus:medkit_")) return;

    restoreItemDurabilityFromMetadata(mainhand);
    const durability = mainhand.getComponent("minecraft:durability");
    if (durability) {
        const nextDamage = durability.damage + 1;
        if (nextDamage >= durability.maxDurability) {
            // Worn out: the kit is used up and disappears
            equipment.setEquipment(EquipmentSlot.Mainhand, undefined);
            player.sendMessage("§cอุปกรณ์ชุบชีวิตพังและหายไปแล้ว!");
            player.dimension.playSound("random.break", player.location);
        } else {
            updateItemDurability(mainhand, nextDamage, durability.maxDurability);
            equipment.setEquipment(EquipmentSlot.Mainhand, mainhand);
        }
    }
}
