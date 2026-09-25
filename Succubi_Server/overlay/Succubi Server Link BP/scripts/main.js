// Succubi Server Link BP
// The main pack runs @minecraft/server 1.19.0, which cannot read or change hunger. This small pack (2.0.0, stable):
//  - copies each player's hunger (0-20) to the "succubi_food" scoreboard for the HUD, regeneration and pressure sounds
//  - drains food a little over time when the base-stat setting "อาหารลดเพิ่ม" is on: the main pack puts the
//    seconds per point in scoreboard "succubi_cfg", player "food_drain" (0 = off, only the game's own hunger).
//    Saturation goes first, like the game's own hunger.
import { world, system } from "@minecraft/server";

const OBJECTIVE = "succubi_food";
const CFG = "succubi_cfg";
const owed = new Map(); // player id -> food points owed to the drain (fractions add up)

function drainSeconds() {
  try {
    const v = world.scoreboard.getObjective(CFG)?.getScore("food_drain");
    return typeof v === "number" && v > 0 ? v : 0;
  } catch (e) {
    return 0;
  }
}

function survival(player) {
  try {
    const m = String(player.getGameMode()).toLowerCase();
    return m !== "creative" && m !== "spectator";
  } catch (e) {
    return true;
  }
}

function drain(player, seconds, dt) {
  const due = (owed.get(player.id) ?? 0) + dt / seconds;
  const whole = Math.floor(due);
  owed.set(player.id, due - whole);
  if (whole <= 0) return;
  const saturation = player.getComponent("minecraft:player.saturation");
  const hunger = player.getComponent("minecraft:player.hunger");
  let left = whole;
  if (saturation && saturation.currentValue > 0) {
    const take = Math.min(left, saturation.currentValue);
    saturation.setCurrentValue(saturation.currentValue - take);
    left -= take;
  }
  if (left > 0 && hunger) hunger.setCurrentValue(Math.max(0, hunger.currentValue - left));
}

system.runInterval(() => {
  let objective;
  try {
    objective = world.scoreboard.getObjective(OBJECTIVE) ?? world.scoreboard.addObjective(OBJECTIVE, "Food");
  } catch (e) {
    return;
  }
  const seconds = drainSeconds();
  for (const player of world.getAllPlayers()) {
    try {
      if (seconds > 0 && survival(player)) drain(player, seconds, 0.5);
    } catch (e) {}
    try {
      const hunger = player.getComponent("minecraft:player.hunger");
      if (!hunger) continue;
      const value = Math.max(0, Math.min(20, Math.round(hunger.currentValue)));
      if (objective.getScore(player) !== value) objective.setScore(player, value);
    } catch (e) {}
  }
}, 10);

world.afterEvents.playerLeave.subscribe((e) => owed.delete(e.playerId));
