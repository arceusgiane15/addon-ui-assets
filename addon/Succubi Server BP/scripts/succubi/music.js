import { world, system } from "@minecraft/server";
import { enabled } from "./settings_store.js";
import { getSanity, SANITY_MAX } from "./sanity.js";

// Tension music: while a player is in danger the game's own calm music must not play over the red screen and
// the heartbeat. A track played with Player.playMusic takes the music channel for that player only, so the game's
// music stays quiet until ours is done.
//   danger  (RP succubi.music.danger)  health <= 50 %, or <= 75 % while being hit (within 15 s)
//           ends when health is back to 90 %, or above 50 % with nothing hitting for 30 s
//   madness (RP succubi.music.madness) sanity <= 50 % (the fog and whispers start there); ends at 60 %
//   danger wins when both apply. Back to calm = a short silent track fades ours out; the game's music returns
//   on its own afterwards. Off for everyone: settings -> สถานะและ HUD; for one player: wallet -> ตั้งค่า (tag no_tension_music)
const TRACK = { danger: "succubi.music.danger", madness: "succubi.music.madness" };
const SILENCE = "succubi.music.silence";
const TICKS = 10;
const mood = new Map(); // player id -> "calm" | "danger" | "madness"
const lastHurt = new Map(); // player id -> tick of the last hit taken

export function moodFor(hpRatio, sanityRatio, ticksSinceHurt, current = "calm") {
  const danger = current === "danger"
    ? !(hpRatio >= 0.9 || (hpRatio > 0.5 && ticksSinceHurt > 600))
    : hpRatio <= 0.5 || (hpRatio <= 0.75 && ticksSinceHurt <= 300);
  if (danger) return "danger";
  const mad = current === "madness" ? sanityRatio < 0.6 : sanityRatio <= 0.5;
  return mad ? "madness" : "calm";
}

function quiet(player) {
  try {
    const m = String(player.getGameMode()).toLowerCase();
    if (m === "creative" || m === "spectator") return true;
  } catch (e) {}
  return !enabled("tension_music") || player.hasTag("no_tension_music");
}

function play(player, next) {
  try {
    if (next === "calm") player.playMusic(SILENCE, { fade: 3, loop: false });
    else player.playMusic(TRACK[next], { fade: 2.5, loop: true, volume: 1 });
  } catch (e) {}
}

function check(player, tick) {
  const current = mood.get(player.id) ?? "calm";
  let next = "calm";
  if (!quiet(player)) {
    const health = player.getComponent("minecraft:health");
    const maxHp = Number(player.getDynamicProperty("kotarus:max_hp")) || health?.effectiveMax || 100;
    const hp = health?.currentValue ?? maxHp;
    if (!(hp > 0)) return; // dead: leave the music as it is until the respawn
    const sanity = enabled("sanity") ? getSanity(player) / SANITY_MAX : 1;
    next = moodFor(hp / maxHp, sanity, tick - (lastHurt.get(player.id) ?? -100000), current);
  }
  if (next === current) return;
  mood.set(player.id, next);
  play(player, next);
}

export function initMusic() {
  world.afterEvents.entityHurt.subscribe(
    (event) => {
      if (event.damage > 0) lastHurt.set(event.hurtEntity.id, system.currentTick);
    },
    { entityTypes: ["minecraft:player"] }
  );
  world.afterEvents.playerLeave.subscribe((e) => {
    mood.delete(e.playerId);
    lastHurt.delete(e.playerId);
  });
  world.afterEvents.playerSpawn.subscribe((e) => {
    // a fresh join starts calm; after a death the music is faded out by the next check (health is full)
    if (e.initialSpawn && e.player) mood.delete(e.player.id);
  });
  system.runInterval(() => {
    const tick = system.currentTick;
    for (const player of world.getAllPlayers()) {
      try {
        check(player, tick);
      } catch (e) {}
    }
  }, TICKS);
}
