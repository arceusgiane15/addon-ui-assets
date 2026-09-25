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

  // HP, speed and hit strength come from body.js (generated from tools/v20/common.py BODY) and the settings item
  // (base HP, and switches for each effect):
  // 140 cm = 50 HP, runs 15 % faster, hits 23 % lighter / 180 cm = 100 HP / 220 cm = 200 HP, 13 % slower, hits 30 % harder
  baseHp: 100
};
