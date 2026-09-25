## v1.1.8:

- Rewrote the entire gun rendering system, now using attachables. Replacing player-entity-based rendering with true 3D items.
- Rewrote the entire gun firing system to be time-based (like in Project Walker), eliminating FPS-dependent fire rates and animation-based delays (in development).
- Added new guns AK-74, AKM, AKs-74u, M1014, ParaFAL.
- Added new 6B13 assault armor and BNTI Gzhel-K body armor.
- Added ACOG Sight.
- Added Predator V4 Red Dot to pistols.
- Added support for sights attachments on the LMG M249.
- Added item groups to attachments and ammunition types.
- Added attachments items back.
- Added gunmental block.
- Added item descriptions to attachments and guns.
- Added 3d grenades rendering in first person.
- Fixed nametag subpack not working.
- Fixed spotlight block pivot in y-position.
- Fixed Juggernaut overlay hiding first-person things.
- Fixed wall detection and leaning not working correctly with the Mossberg.
- Reduced bullet impact particles for better performance and visibility.
- Reduced smoke grenade opacity to better support stealth-based gameplay.
- Reduced sneaking damage bonus from 1.5 to 1.25.
- Reduced silencer damage penalty from -2 to -1.
- Reduced 50.0% of M249 power.
- Improved attachment system, instead of using the blueprint, you will use the necessary attachment ​​item.
- Reverted to Minecraft's default model rendering to fully support slim, default, and Marketplace skins. (Note: Item pivot misalignment is a known issue when using Marketplace skins.)
- Removed experimental leaning system, the early-stage, out-of-date leaning mechanic has been permanently removed as it was dysfunctional and did not meet core feature standards.

## v1.1.7:

- Added subpack to enable/disable nametags.
- Added beta "Leaning" feature to the Settings menu.
- Added back the Attachment Workbench.
- Added distant post-fire sound effects.
- Added Juggernaut overlay UI.
- Added Aluminum and Steel, along with their derived forms such as ores and ore blocks.
- Improved third-person running animations for pistols.
- Improved scripting API performance with modular enhancements.
- Improved textures for several wearable items.
- Improved landmine item texture.
- Improved sights UI clarity and visuals.
- Fixed Mossberg recipe using wood stock instead of polymer stock.
- Fixed issue where reloading was possible even with a full magazine.
- Fixed AWP ejecting two bullets per shot.
- Fixed incorrect silenced sound on the FNFAL.
- Fixed "undefined" gun name in death messages.
- Fixed M249 arm glitch when equipping attachments.
- Fixed missing empty bucket when crafting plastic mass.
- Fixed invisible items in third-person view.
- Fixed numerous other bugs and minor issues not listed here.
- Fixed armor o longr get damage from bullets in creative mode.

## v1.1.6:

- Added RPG-7.
- Added 6B13 Assault Armor.
- Added BNTI Gzhel-K Body Armor.
- Added more translations.
- Added new mechanic: you now take 1 heart of damage when using a shield and getting shot.
- Added new bullet damage falloff system.
- Added new NVG attachment for helmets.
- Added new impact effects system (with accurate block sounds).
- Added new recoil system for snipers (thanks to Azoz/ActualGuns for that).
- Added enchantment materials to wearables.
- Added barbed wire prop block.
- Added corrugated metal prop block.
- Added military wall prop block.
- Added spotlight prop block.
- Added ceiling light prop block.
- Added container prop blocks.
- Added hesco prop blocks.
- Added side mount to AK-47 when using sights.
- Improved indoor sound design.
- Improved reflection and distance-based sound design.
- Improved all gun models and textures.
- Improved all wearable models and textures.
- Improved armor mechanics: now armor takes damage from bullets.
- Improved animation controller performance.
- Improved scripting API performance.
- Improved muzzle smoke, hot and lensflare particle effects.
- Improved all third person animations.
- Changed gun standby pose delay.
- Changed gun standby pose animation.
- Changed pack UUIDs/IDs.
- Changed silenced shots to reduce damage by 2.
- Changed guns to now auto-reload.
- Fixed nametags to always display.
- Fixed a typo in the death message.
- Fixed FN FAL muzzle pivot point.
- Fixed bullets breaking barrier blocks.
- Updated Scripts API version.
- Updated mechanics for breakable blocks by bullets.
- Refactored bullet code.
- Removed title command conflicts: you can now use the title command with the add-on without issues.
- Removed the crosshair when ADS.
- Removed attachment workbench, now you can attach using attachment blueprint on your off-hand.

## v1.1.5:

- Improved performance in bullets.
- Fixed nametags to always display.
- Fixed a typo in the death message.
- Fixed camera shake in grenade impacts.

## v1.1.4:

- Updated core addon to use stable scripts (only needed if you use another Aplok Guns downloadable pack).
- Added crafting for FN FAL 20rnd Mag.
- Added translation for death messages in PT-BR.
- Added green laser.
- Increased Juggernaut durability.
- Increased AWP damage.
- Decreased M249 fire rate.
- Decreased the value of the headshot multiplier.
- Balanced some ammo recipes.
- Fixed some performance issues.
- Fixed wall detection and scope animation cancellation.
- Fixed juggernaut arms glitch again.
- Fixed attachments not working in nether and the_end.
- Fixed HK MP5-A5 camera shake.
- Fixed death message when you still alive.
- Improved guns performance.
- Changed the recline/lean feature to experimental (needs to be enable with additional commands with "Aplok Guns Experimental Commands pack").
- And several other changes not included in the changelog.

## v1.1.3:

- Fixed juggernaut bullet sparks position.
- Fixed juggernaut arms glitch.
- Fixed juggernaut knockback.
- Fixed juggernaut explosion.
- Fixed sight ui issue.
- Fixed sandbag clearing inventory.
- Fixed mossberg reload.
- Increased mossberg spread when aiming.
- Fixed item in tpp.

## v1.1.2:

- Added deaths & kills scoreboard.
- Added new attachment system.
- Added new attachment workbench.
- Added wall collision to guns.
- Added recline feature to guns.
- Added headshot to humanoids entities.
- Added new damage reducion system when using armors or shield.
- Added now each gun will have they own attachment.
- Added now you can share your modded gun with your friends and they will have the attachments.
- Added laser support to pistols.
- Added Predator V4 Red Dot to pistols.
- Added new M249 LMG.
- Added reload when you attack sneaking (without emptying your gun).
- Added new gunparts to make guns.
- Added sulfur powder.
- Added bucket of petroleum.
- Added plastic mass and plastic plate.
- Added new third person animations to guns.
- Changed guns recipes.
- Changed gun workbench interface.
- Changed recipes to use plastic material.
- Changed events to custom components (No need holiday creator features nomore).
- Improved client animation controller reduced usage in 18%.
- Improved standby (arms down) animation sync with tpp and multiplayer.
- Fixed duplicated bullet casing when paperdoll is enabled (thank you @HSK for the help).
- Fixed reloading issue when u die.
- Fixed some issues in dropped items.
- Fixed landmine explosion.
- Fixed landmine placing sfx.
- Fixed now doubled sandbag drop two items instead of one.
- Removed 3d drop item.

## v1.1.1:

- Ported the core addon engine to 1.21.
- Added 3D dropped items.
- Added now you can get magazines in wandering trader and weapon smith villagers.
- Improved new gun system, more stable and optimized.
- Improved AK-12 with new model and animations.
- Improved AK-47 with new model and animations.
- Improved AWP with new template and animations.
- Improved Desert Eagle model and animations.
- Improved FN Fal with new model and animations.
- Improved Glock 17 and Glock 18 model and animations.
- Improved M4A1 with new model and animations.
- Improved Mossberg 500 with new model and animations.
- Improved HK MP5 A5 with new model and animations.
- Improved cycled guns system and fixed some issues on it.
- Improved now attachments are synced with the client (your friends can see your gun attachments).
- Improved bullet spread when hipfiring, moving or aiming.
- Improved grenade physics.
- Changed item ID "desert_eagle" to "deagle".
- Changed "helmet_military" to "helmet_6b47".
- Fixed some issues with attachments.
- Fixed some missing sounds (bullet ricochet and grenade drop).
- Removed some blocks.
- Removed HK MP5 A5 foregrip support (temporary).
- Removed Juggernaut (temporary).
- Removed magazines crafting (temporary).

## v1.1.0:

- Added support to minecraft 1.20.80.
- Fixed invisible landmine item.

## v1.0.9:

- Added support to minecraft 1.20.70/71.
- Decreased Mossberg bullet damage.
- Improved bullet damage type to "override" to compatibility with amor protection.
- Removed knockback from bullets.

## v1.0.8:

- Added AK-12 assault rifle.
- Added 5.45x39mm bullet.
- Added nametag always show back.
- Added new NVG material.
- Added recipe to NVG.
- Added new damage values to individual guns (the old is based on caliber).
- Improved inspection animations.
- Improved new AK-47 model & texture & animations.
- Improved new AWP model & texture & animations.
- Improved new M4A1 model & texture.
- Improved all gun fire reverb sounds.
- Improved recipes to more difficult crafting for various items/blocks.
- Improved deco blocks now only can be placed in they respective filters (up, down, side...).
- Improved wooden barricade can be placed in up and down blocks.
- Improved rewrite bullet code to fix the chuck load crashing.
- Improved grenade explosion.
- Improved blocks rotation code.
- Improved updated engine compatibility to 1.20.60+.
- Improved rewrite and optimized the commands season in the addon core.
- Improved the recoil (We need some feedback to know how to improve this).
- Improved optimized explosion particles.
- Improved now the magazine recipe is empty (zero bullets).
- Improved Juggernaut protection.
- Fixed FN Fal fire bolt pulling.
- Fixed HK MP5-A5 Foregrip animation.
- Removed custom biomes.
- Removed heart beat and blood.
- Removed immersive jump feature.
- Removed custom hotbar.
- Removed custom tooltip.
- Removed player custom animations.
- Removed gasmask.

## v1.0.7:

- We're releasing the v1.0.7 with various improvements, changes and bug fixes!
- Added: Explosion effect now occurs by default with all other explosions! (like creeper, TNT etc.)
- Fixed: Guns Fixer item not working.
- Fixed: Nickname not showing.
- Fixed: Increased bullet velocity.
- Fixed: Decreased bullet physical gravity.
- Fixed: Run state machine glitch when player walk in snow biomes.
- Fixed: Slim skin can now be used without the strange arm bug.
- Removed: Resistance effect from juggernaut.
- Changed: Decreased item stack drop from ammunition crate.
- Changed: Increased guns resetting position delay.
- Changed: Descreased landmine explosion range.
- Improved: Explosions effects optimized to low-end devices.
- Improved: Decreased muzzle light emission when fire silenced.
- Improved: Rewrite some state machines to optimize the client and server processors.
- Improved: New running animations.
- Improved: New animations state machines transitions to more fluid experience.
- Improved: Rewrite some bullet core system to more performance.

## v1.0.6:

- We introduce the 1.0.6 update with improvements and bug fixes!
- Added: Holding animation with Foregrip for the HK MP5A5.
- Added: Chinese language support by WshtxLonely.
- Added: Russian language support by Gabriel Aplok.
- Fixed: AK-47 Mag caliber name.
- Fixed: Muzzle Light block overlaps with farmland block and player also overlap too.
- Improved: Decreased the overrated camera shake when jumping.
- Improved: Decreased the overated bullet damage.
- Improved: Decreased the bullet velocity to fix bullet tracers.

## v1.0.5:

- We introduce the 1.0.5 with various optimizations and bug fixes!
- Added: New Foregrip Attachment.
- Added: New HK MP5A5 Gun.
- Added: New HK MP5A5 30rnd Magazine.
- Added: New Czech Hedgehog block.
- Added: New Sandbag and Doubled Sandbag block.
- Added: New Camera shakes when you reload your gun for an immersive experience.
- Added: New Echo SFX when you fire without an silencer.
- Added: Land SFX when place a landmine.
- Fixed: When the player dies, night vision doesn't return.
- Fixed: Explosions underwater particles fixed.
- Fixed: Wooden blocks burn when in contact with fire.
- Fixed: Bullet's physical gravity was decaying too fast and the bullet didn't hit the right place after 16 blocks.
- Improved: ADS Animation transition delay increased.
- Improved: New landmine model.
- Improved: Vanilla biomes to enjoy a "Soviet" environment experience.
- Improved: When shooting with a silenced gun, the muzzle light emitted is very reduced.
- Improved: Explosions distance blind SFX, and atmosphere far SFX.

## v1.0.4:

- We introduce the 1.0.4 update with new features, bug fixes and improvements!
- Added: New Inactivity position, inactivity with the gun causes player hands down.
- Added: New medical Bandage and Military Bandage items.
- Added: New decoration Harzard Block, Landmine, Metal Rack, Wooden Barricade and Wooden Crate blocks (all craftable).
- Added: New Laser and Silencer attachments.
- Added: NEW COMMANDS! You can toggle the empty mags when empty gun with this commands "!disable empty_mags" and "!enable empty_mags"
- Added: New Night Vision Goggles!
- Added: New SFX when you attach a attachment in your gun!
- Fixed: Ammo/Explosive Crates drops they respective items and not the own block.
- Fixed: Blood particles not showing (only available for players).
- Improved: New Reverb and Far SFX!
- Improved: New Gun Actions SFX!
- Improved: Mossberg 500 Pump Animation.
- Improved: NEW DAMAGE SYSTEM! Removed the bullet hit delay in combat and when you sneak the damage is multiplied by 1.25!
- Improved: Gunmetal crafting recipes like "Steel" with copper nugget, iron nugget and coal, and spend less material.
- Improved: Gunparts upgrade now use less iron nugget, saving more material.
- Improved: Pistol recipes no longer use stocks. (that didn't make sense).
- Improved: 12 Gauge spread increased.

## v1.0.3:

- Added: Eject/Bounce SFX for guns.
- Added: Damage Screen VFX for gameplay immersion.
- Added: Heartbeat SFX.
- Added: Player Only Blood VFX.
- Added: Explosion VFX and SFX.
- Added: Explosive Crate (If you shoot it explodes).
- Added: Shooting Range Target.
- Added: New Pull Back Action System for guns like AWP and Mossberg 500.
- Added: New Materials (Gunmetal, Copper Nugget, Blueprint Bundle and Bullet Gunpowder).
- Added: Bullet Impact body SFX.
- Added: Hitmarker SFX.
- Added: EOTech, ACOG, HP Scope, LP Scope Attachments.
- Added: Reload mags with bullets per bullets system.
- Added: Glock 17 Pistol.
- Added: Desert Eagle Pistol.
- Added: AWP Sniper Rifle.
- Added: FN FAL Battle Rifle.
- Added: M67 Grenade.
- Added: Holding, Aiming and Standing (Same Reloading) Third Person animation.
- Added: New UI for the Gun Workbench.
- Added: Recipe for Ammunition Box.
- Fixed: M4A1 item name with mistake.
- Fixed: Vanilla 3D items rendering bug.
- Fixed: ADS vignette not hiding when holding off the gun.
- Fixed: Player start draw animation when holding off the gun.
- Removed: Foliage summer color-map.
- Improved: Mags and Bullets recipes now is in the Stonecutter, yes (Gunmetal Ingot for 2x Mags and Bullet Gunpowder for 6x Bullets).
- Improved: The Gun Workbench recipe is now simplified.
- Improved: New Muzzle Flash and Smoke VFX.
- Improved: New bullets casing VFX/Physics.
- Improved: AK-47 Model to fix the floating trigger guard.
- Improved: Renamed "Glock 18" to "Glock 18c".
- Improved: Now the amor can be enchanted.
- Improved: VFX Design/Physics/Performance.
- Improved: Rewrite the Guns system stable for performance and compatibility with the new mag bullets reload system.
- Improved: New recipes for guns and gun parts.
- Improved: Now you can cancel the reload action when holding off the gun.
- Improved: New Juggernaut armor.

## v1.0.2:

- Added: Welcome & Info message in-game on every update.
- Added: Glock 18 Pistol.
- Added: Mossberg 500 shotgun.
- Added: 6B3 body armor.
- Added: Military Helmet.
- Added: Juggernaut Armor.
- Added: New splashes.
- Added: Bullet tracers.
- Added: Bullet hole by @GabrielMODGuy.
- Added: Smoke VFX for light, medium and heavy gun fire.
- Added: Water and solid impact VFX.
- Added: Sparks VFX when impacting metal.
- Added: inspection animations.
- Added: ADS (Aim Down Sight) Vignette.
- Added: New gun parts for recipes.
- Fixed: some bugs.
- Fixed: Workbench block rotation.
- Updated: API for Bedrock Engine 1.20.30
- Improved: Impact SFX system.
- Improved: Now the gun looks for ammo in the entire inventory, and no longer the off-hand.
- Improved: New SFX effects again (I love this).
- Improved: New animations again ( I love improving this).
- Improved: Performance and smoothness.
- Improved: all textures have been remastered.
- Improved: new 3d models for some things.
- Improved: Muzzle light (block) performance.
- Improved: More efficient armament and ballistic system.
- Improved: New atmospheric SFX.
- Improved: New bullet recipes.
- Removed: M4A1 Tactical (Temporary) cuz I working on attachments system.
- Removed: Detailed third-person animations.
- Removed: The summer color-map and fog darkness, cuz this is not an apocalypse mod (Download Mini Apocalypse lol).

## v1.0.1:

- Added: Gasmask for protection from nausea and poison.
- Added: Mask filter and your recipes for Gasmask.
- Added: AK-47 Assault Rifle.
- Added: More parts for AK-47 workbench recipe.
- Added: Atmospheric guns SFX.
- Added: Impact, snap and whizby bullets SFX.
- Fixed: Blocks multiple mesh render glitch.
- Fixed: Multiplayer sprinting glitch.
- Fixed: Duplicate reload SFX.
- Fixed: Vanilla player animations.
- Improved: Both M4A1's fire rate has been increased to the real life fire rate.
- Improved: Some reworked textures.
- Improved: All guns transitions.
- Improved: All guns animations.
- Improved: All guns SFX.

## v1.0.0:

- First release.
