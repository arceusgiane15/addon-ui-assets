import { world, system } from "@minecraft/server";
import { num, onSettingChange } from "./settings_store.js";

// Health regeneration (base stats). regen_seconds = 0: the game's own natural regeneration, untouched.
// Above 0: the game rule naturalRegeneration is switched off and players heal 1 HP every regen_seconds
// while their food is at least regen_food. Setting it back to 0 turns the game rule on again
// (only if this pack was the one that turned it off).
const OWNED = "succubi:regen_owned";
const FOOD_OBJECTIVE = "succubi_food"; // written by the Link BP
const CFG_OBJECTIVE = "succubi_cfg"; // numbers the Link BP reads (it cannot see this pack's world properties)
const TICKS = 5;
const carry = new Map(); // player id -> HP owed (fractions add up)

export function readFood(player) {
  try {
    const score = world.scoreboard.getObjective(FOOD_OBJECTIVE)?.getScore(player);
    if (typeof score === "number") return Math.max(0, Math.min(20, Math.round(score)));
  } catch (e) {}
  return 20; // link pack not running: treat as full
}

export function linkPackRunning() {
  try {
    return !!world.scoreboard.getObjective(FOOD_OBJECTIVE);
  } catch (e) {
    return false;
  }
}

function syncGameRule() {
  try {
    const rules = world.gameRules;
    if (num("regen_seconds") > 0) {
      if (rules.naturalRegeneration) {
        rules.naturalRegeneration = false;
        world.setDynamicProperty(OWNED, true);
      }
    } else if (world.getDynamicProperty(OWNED) === true) {
      rules.naturalRegeneration = true;
      world.setDynamicProperty(OWNED, false);
    }
  } catch (e) {}
}

// food drain runs in the Link BP (only its newer API can change hunger): hand it the number
export function syncLinkConfig() {
  try {
    const obj = world.scoreboard.getObjective(CFG_OBJECTIVE) ?? world.scoreboard.addObjective(CFG_OBJECTIVE, "Succubi config");
    obj.setScore("food_drain", Math.round(num("food_drain_seconds")));
  } catch (e) {}
}

const survival = (p) => {
  try {
    const m = String(p.getGameMode?.()).toLowerCase();
    return m !== "creative" && m !== "spectator";
  } catch (e) {
    return true;
  }
};

export function regenTick(players, dt = TICKS / 20) {
  const seconds = num("regen_seconds");
  if (!(seconds > 0)) return;
  const needFood = num("regen_food");
  for (const p of players) {
    try {
      if (!survival(p)) continue;
      const health = p.getComponent("minecraft:health");
      const maxHp = Number(p.getDynamicProperty("kotarus:max_hp")) || 100;
      if (!health || !(health.currentValue > 0) || health.currentValue >= maxHp || readFood(p) < needFood) {
        carry.delete(p.id);
        continue;
      }
      const owed = (carry.get(p.id) ?? 0) + dt / seconds;
      const whole = Math.floor(owed);
      carry.set(p.id, owed - whole);
      if (whole > 0) health.setCurrentValue(Math.min(maxHp, health.currentValue + whole));
    } catch (e) {}
  }
}

export function initRegen() {
  system.run(() => {
    syncGameRule();
    syncLinkConfig();
  });
  onSettingChange((name) => {
    if (name === "regen_seconds" || name === "*") syncGameRule();
    if (name === "food_drain_seconds" || name === "*") syncLinkConfig();
  });
  world.afterEvents.playerLeave.subscribe((e) => carry.delete(e.playerId));
  system.runInterval(() => regenTick(world.getAllPlayers()), TICKS);
}
