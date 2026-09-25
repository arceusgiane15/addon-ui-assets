# sounds
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.deagle.fire @a[r=200] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=silencer] run playsound weapon.deagle.fire_silenced @a[r=50] ^^^1.5 100 1 0.01

execute as @s[tag=underground, tag=!silencer] run playsound weapon.deagle.fire.indoor @a[r=100] ^^^1.5 100 1 0.01
execute as @s[tag=underground, tag=silencer] run playsound weapon.deagle.fire_silenced.indoor @a[r=25] ^^^1.5 100 1 0.01

# anims
playanimation @s[tag=silencer] animation.deagle.fire.silenced fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:deagle')"
playanimation @s[tag=!silencer] animation.deagle.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:deagle')"

# recoil
camerashake add @s[tag=sneaking] 0.06 0.2 rotational
camerashake add @s[tag=!sneaking] 0.1 0.2 rotational

# core
scoreboard players remove @s[scores={deagle=1..}] deagle 1
function effect/shot_light
event entity @s trenbankai:deagle_fire
