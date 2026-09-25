# sounds
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.glock.fire @a[r=200] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=silencer] run playsound weapon.glock.fire_silenced @a[r=50] ^^^1.5 100 1 0.01

execute as @s[tag=underground, tag=!silencer] run playsound weapon.glock.fire.indoor @a[r=100] ^^^1.5 100 1 0.01
execute as @s[tag=underground, tag=silencer] run playsound weapon.glock.fire_silenced.indoor @a[r=25] ^^^1.5 100 1 0.01

# anims
playanimation @s[tag=silencer] animation.glock17.fire.silenced fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:glock17')"
playanimation @s[tag=!silencer] animation.glock17.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:glock17')"

# recoil
camerashake add @s[tag=sneaking] 0.02 0.2 rotational
camerashake add @s[tag=!sneaking] 0.04 0.2 rotational

# core
scoreboard players remove @s[scores={glock17=1..}] glock17 1
function effect/shot_light
event entity @s trenbankai:glock_fire
