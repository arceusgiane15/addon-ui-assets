import { initHeightSystem } from "./height/main.js";
import { initMedicalSystem } from "./medical/main.js";
import { initMoneySystem } from "./succubi/money.js";
import { initThirstSystem } from "./succubi/thirst.js";
import { initHud } from "./succubi/hud.js";
import { initVending } from "./succubi/vending.js";
import { initConsumables } from "./succubi/consumables.js";
import { initKioskAudio } from "./succubi/kiosk_audio.js";
import { initSanity } from "./succubi/sanity.js";
import { initSettings } from "./succubi/settings.js";
import { initAmulets } from "./succubi/amulets.js";
import { initBooks } from "./succubi/books.js";
import { initHorror } from "./succubi/horror.js";
import { initNametags } from "./succubi/nametags.js";
import { initPackCheck } from "./succubi/packs.js";
import { initRegen } from "./succubi/regen.js";
import { initPressure } from "./succubi/pressure.js";

/**
 * Succubi Server v1.1.6 - core systems.
 * Guns live in the separate "Succubi Guns" packs; this pack works with or without them.
 * Menus: the wallet (always in the last hotbar slot) for players, the settings item for admins.
 */
initHeightSystem();
initMedicalSystem();
initMoneySystem();
initThirstSystem();
initHud();
initVending();
initConsumables();
initKioskAudio();
initSanity();
initSettings();
initAmulets();
initBooks();
initHorror();
initNametags();
initPackCheck();
initRegen();
initPressure();

console.warn("[Succubi Server] v1.1.6 loaded: wallet, shops, HUD, height, medical, thirst, sanity, regen, pressure sounds, Rule of Horror");
