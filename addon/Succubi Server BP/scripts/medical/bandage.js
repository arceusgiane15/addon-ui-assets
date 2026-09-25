import { EquipmentSlot, ItemStack, system } from "@minecraft/server";

const activeBandaging = new Set();

export function handleBandageHeal(player, targetPlayer = null) {
    const recipient = targetPlayer || player;
    const isSelf = recipient.id === player.id;

    if (recipient.hasTag("kotarus:downed")) {
        player.onScreenDisplay.setActionBar("§cผ้าพันแผลไม่สามารถใช้ชุบคนล้มได้!");
        return;
    }

    const health = recipient.getComponent("minecraft:health");
    if (!health) return;

    const maxAllowed = recipient.getDynamicProperty("kotarus:max_hp") || 100;
    if (health.currentValue >= maxAllowed) {
        player.onScreenDisplay.setActionBar("§eเลือดเต็มอยู่แล้ว ไม่จำเป็นต้องพันแผล");
        return;
    }

    if (isSelf) {
        if (activeBandaging.has(player.id)) return;
        activeBandaging.add(player.id);

        // Wrapping sound at tick 5
        system.runTimeout(() => {
            if (player.isValid()) {
                player.dimension.playSound("medic.bandage", player.location, { volume: 0.8, pitch: 1.0 });
            }
        }, 5);

        // Apply heal at tick 20 (during wrapping)
        system.runTimeout(() => {
            if (!player.isValid() || !recipient.isValid()) {
                activeBandaging.delete(player.id);
                return;
            }
            executeBandageHeal(player, recipient, true);
        }, 20);

        // Animation completes at tick 30 (engine.js handles single bandage deduction)
        system.runTimeout(() => {
            activeBandaging.delete(player.id);
        }, 30);

    } else {
        // Interacting with teammate: instant application & manual consumption
        executeBandageHeal(player, recipient, false);
        consumeHeldItem(player);
    }
}

function executeBandageHeal(player, recipient, isSelf) {
    const health = recipient.getComponent("minecraft:health");
    if (!health) return;

    // Instant 100 HP restore
    const maxAllowed = recipient.getDynamicProperty("kotarus:max_hp") || 100;
    const healAmount = 100;
    const newHealth = Math.min(maxAllowed, health.currentValue + healAmount);
    health.setCurrentValue(newHealth);

    // Feedback
    recipient.dimension.playSound("medic.bandage", recipient.location);
    recipient.dimension.spawnParticle("minecraft:villager_happy", {
        x: recipient.location.x,
        y: recipient.location.y + 1.0,
        z: recipient.location.z
    });

    if (isSelf) {
        player.sendMessage(`§aพันแผลสำเร็จ! ฟื้นฟูเลือด +${healAmount} HP`);
    } else {
        player.sendMessage(`§aพันแผลให้เพื่อนสำเร็จ! ฟื้นฟูเลือด +${healAmount} HP`);
        recipient.sendMessage(`§aเพื่อนร่วมหน่วยได้พันแผลให้คุณ! ฟื้นฟูเลือด +${healAmount} HP`);
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
