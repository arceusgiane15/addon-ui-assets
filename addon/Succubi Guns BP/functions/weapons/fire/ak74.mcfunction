# sounds
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.ak47.fire @a[rm=0, r=80] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.ak47.fire.dist @a[rm=80, r=200] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=silencer] run playsound weapon.ak12.fire_silenced @a[r=50] ^^^1.5 100 1 0.01

execute as @s[tag=underground, tag=!silencer] run playsound weapon.ak47.fire.indoor @a[r=100] ^^^1.5 100 1 0.01
execute as @s[tag=underground, tag=silencer] run playsound weapon.ak12.fire_silenced.indoor @a[r=25] ^^^1.5 100 1 0.01

# anims
playanimation @s[tag=silencer] animation.ak74.fire.silenced fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:ak74')"
playanimation @s[tag=!silencer] animation.ak74.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:ak74')"

# recoil
camerashake add @s[tag=sneaking] 0.02 0.18 rotational
camerashake add @s[tag=!sneaking] 0.05 0.18 rotational

# core
scoreboard players remove @s[scores={ak74=1..}] ak74 1
function effect/shot_light
event entity @s trenbankai:ak74_fire
