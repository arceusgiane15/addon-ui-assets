# sounds
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.fnfal.fire @a[r=200] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=silencer] run playsound weapon.ak12.fire_silenced @a[r=50] ^^^1.5 100 1 0.01

execute as @s[tag=underground, tag=!silencer] run playsound weapon.fnfal.fire.indoor @a[r=100] ^^^1.5 100 1 0.01
execute as @s[tag=underground, tag=silencer] run playsound weapon.ak12.fire_silenced.indoor @a[r=25] ^^^1.5 100 1 0.01

# anims
playanimation @s[tag=silencer] animation.fnfal.fire.silenced fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:fnfal')"
playanimation @s[tag=!silencer] animation.fnfal.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:fnfal')"

# recoil
camerashake add @s[tag=sneaking] 0.04 0.2 rotational
camerashake add @s[tag=!sneaking] 0.08 0.2 rotational

# core
scoreboard players remove @s[scores={fnfal=1..}] fnfal 1
function effect/shot_light
event entity @s trenbankai:fnfal_fire
