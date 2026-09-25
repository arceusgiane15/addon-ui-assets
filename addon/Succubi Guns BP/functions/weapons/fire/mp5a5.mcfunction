# sounds
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.mp5a5.fire @a[r=200] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=silencer] run playsound weapon.mp5a5.fire_silenced @a[r=50] ^^^1.5 100 1 0.01

execute as @s[tag=underground, tag=!silencer] run playsound weapon.mp5a5.fire.indoor @a[r=100] ^^^1.5 100 1 0.01
execute as @s[tag=underground, tag=silencer] run playsound weapon.mp5a5.fire_silenced.indoor @a[r=25] ^^^1.5 100 1 0.01

# vfx
playanimation @s[tag=silencer] animation.mp5a5.fire.silenced fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:mp5a5')"
playanimation @s[tag=!silencer] animation.mp5a5.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:mp5a5')"

# recoil without grip
camerashake add @s[tag=sneaking, tag=!foregrip] 0.02 0.2 rotational
camerashake add @s[tag=!sneaking, tag=!foregrip] 0.06 0.22 rotational
# recoil with grip
camerashake add @s[tag=sneaking, tag=foregrip] 0.01 0.1 rotational
camerashake add @s[tag=!sneaking, tag=foregrip] 0.02 0.12 rotational

# core
scoreboard players remove @s[scores={mp5a5=1..}] mp5a5 1
function effect/shot_light
event entity @s trenbankai:mp5a5_fire
