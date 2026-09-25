import { world } from "@minecraft/server";

// Wallet balance = the "money" scoreboard (the vending machine uses the same one). Unit: baht.
export const MONEY_OBJECTIVE = "money";
export const STARTING_BALANCE = 100; // what new players start with (same as before)
const MAX_BALANCE = 2000000000;

function objective() {
  return world.scoreboard.getObjective(MONEY_OBJECTIVE) ?? world.scoreboard.addObjective(MONEY_OBJECTIVE, "Baht");
}

export function getBalance(player) {
  try {
    const obj = objective();
    let score;
    try {
      score = obj.getScore(player);
    } catch (e) {
      score = undefined;
    }
    if (typeof score === "number") return score;
    obj.setScore(player, STARTING_BALANCE);
    return STARTING_BALANCE;
  } catch (e) {
    return 0;
  }
}

export function setBalance(player, value) {
  const safe = Math.max(0, Math.min(MAX_BALANCE, Math.floor(Number(value) || 0)));
  try {
    objective().setScore(player, safe);
    return true;
  } catch (e) {
    return false;
  }
}

export function addBalance(player, delta) {
  return setBalance(player, getBalance(player) + delta);
}

export function formatBaht(value) {
  return String(Math.floor(Number(value) || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
