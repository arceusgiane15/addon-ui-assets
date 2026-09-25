// Kotarus Height Adjuster with Dynamic HP Scaling
export const CONFIG = {
  // v1.1.12: the height adjuster item is gone - heights are changed from the wallet (ตั้งค่า -> ปรับส่วนสูง)

  // Steve is 1.8 blocks tall = 180 cm (Scale 1.0). Body size always follows cm / 180; the standard height for
  // stats (normal HP / speed / strength) is a setting (h_std) and can differ.
  baseCm: 180,
  // Full range: admins, or everyone when the admin switch "ส่วนสูงอิสระ" is on
  minCm: 1,
  maxCm: 500,
  // Normal players: the range (h_min - h_max), the minutes between changes (h_cooldown) and the lock after a
  // fight (h_fight_lock) are settings (settings item -> สเตตัสพื้นฐาน -> ส่วนสูง)

  // Collision box stepping
  hitboxStepCm: 10,
  applyHitbox: true,

  propHeight: "kotarus:height_cm",
  propMaxHp: "kotarus:max_hp",
  propNextChange: "kotarus:height_next", // Date.now() ms when the next change is allowed

  reapplyIntervalTicks: 40,
  heightTagPrefix: "kotarus:height_"

  // HP, speed, strength, fall damage, hunger and damage taken come from body.js (three points set in the settings)
};
