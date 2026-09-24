// Kotarus Height Adjuster with Dynamic HP Scaling
export const CONFIG = {
  itemId: "kotarus:height_adjuster",

  // Steve is 1.8 blocks tall = 180 cm (Scale 1.0)
  baseCm: 180,
  // Full range: admins, or everyone when the admin switch "ส่วนสูงอิสระ" is on
  minCm: 1,
  maxCm: 500,
  // Normal players: a believable range, so nobody hides in a 10 cm hitbox or tanks with 200 HP
  playerMinCm: 140,
  playerMaxCm: 220,
  // Normal players: one change every 5 minutes, and never within 15 s of a fight
  cooldownSeconds: 300,
  combatLockSeconds: 15,

  // Collision box stepping
  hitboxStepCm: 10,
  applyHitbox: true,

  propHeight: "kotarus:height_cm",
  propMaxHp: "kotarus:max_hp",
  propNextChange: "kotarus:height_next", // Date.now() ms when the next change is allowed

  reapplyIntervalTicks: 40,
  heightTagPrefix: "kotarus:height_",

  // HP: 100 at 180 cm, +1 HP per cm taller, -1 per cm shorter, clamped 50-200
  // (player range 140-220 cm = 60-140 HP)
  baseHp: 100,
  hpPerCm: 1,
  minHp: 50,
  maxHp: 200
};
