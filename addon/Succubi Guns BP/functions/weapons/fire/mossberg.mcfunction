# sounds
execute as @s[tag=!underground] run playsound weapon.mossberg.fire @a[r=200] ^^^1.5 100 1 0.01
execute as @s[tag=underground] run playsound weapon.mossberg.fire.indoor @a[r=100] ^^^1.5 100 1 0.01

# vfx
playanimation @s animation.mossberg.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:mossberg')"

# recoil
camerashake add @s[tag=sneaking] 0.06 0.2 rotational
camerashake add @s[tag=!sneaking] 0.12 0.2 rotational

# core
scoreboard players remove @s[scores={mossberg=1..}] mossberg 1
function effect/shot_light
event entity @s trenbankai:mossberg_fire
