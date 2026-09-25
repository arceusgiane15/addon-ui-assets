# sounds
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.ak12.fire @a[rm=0, r=80] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.ak12.fire.dist @a[rm=80, r=200] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=silencer] run playsound weapon.ak12.fire_silenced @a[r=50] ^^^1.5 100 1 0.01

execute as @s[tag=underground, tag=!silencer] run playsound weapon.ak12.fire.indoor @a[r=100] ^^^1.5 100 1 0.01
execute as @s[tag=underground, tag=silencer] run playsound weapon.ak12.fire_silenced.indoor @a[r=25] ^^^1.5 100 1 0.01

# anims
playanimation @s[tag=silencer] animation.ak12.fire.silenced fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:ak12')"
playanimation @s[tag=!silencer] animation.ak12.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:ak12')"

# recoil without grip
camerashake add @s[tag=sneaking, tag=!foregrip] 0.015 0.2 rotational
camerashake add @s[tag=!sneaking, tag=!foregrip] 0.035 0.2 rotational
# recoil with grip
camerashake add @s[tag=sneaking, tag=foregrip] 0.01 0.1 rotational
camerashake add @s[tag=!sneaking, tag=foregrip] 0.015 0.1 rotational

# core
scoreboard players remove @s[scores={ak12=1..}] ak12 1
function effect/shot_light
event entity @s trenbankai:ak12_fire
