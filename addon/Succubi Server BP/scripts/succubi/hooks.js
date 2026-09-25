// Other systems plug into sanity here without importing each other
//  eventRate(player)  -> multiplier for how fast the next strange event comes (2 = twice as often)
//  eventLoss(player)  -> multiplier for sanity lost to strange events
//  eventBlock(player) -> true = cancel this player's next strange event
export const HOOKS = { eventRate: [], eventLoss: [], eventBlock: [] };

export function product(list, ...args) {
  let m = 1;
  for (const f of list) {
    try {
      const v = f(...args);
      if (typeof v === "number" && v >= 0) m *= v;
    } catch (e) {}
  }
  return m;
}

export function anyTrue(list, ...args) {
  for (const f of list) {
    try {
      if (f(...args)) return true;
    } catch (e) {}
  }
  return false;
}
