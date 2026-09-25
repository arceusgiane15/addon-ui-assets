# sounds
execute as @s[tag=!underground, tag=!silencer] run playsound weapon.m4a1.fire @a[r=200] ^^^1.5 100 1 0.01
execute as @s[tag=!underground, tag=silencer] run playsound weapon.m4a1.fire_silenced @a[r=50] ^^^1.5 100 1 0.01

execute as @s[tag=underground, tag=!silencer] run playsound weapon.m4a1.fire.indoor @a[r=100] ^^^1.5 100 1 0.01
execute as @s[tag=underground, tag=silencer] run playsound weapon.m4a1.fire_silenced.indoor @a[r=25] ^^^1.5 100 1 0.01

# anims
playanimation @s[tag=silencer] animation.m4a1.fire.silenced fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:m4a1')"
playanimation @s[tag=!silencer] animation.m4a1.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:m4a1')"

# recoil without grip
camerashake add @s[tag=sneaking, tag=!foregrip] 0.018 0.2 rotational
camerashake add @s[tag=!sneaking, tag=!foregrip] 0.04 0.2 rotational
# recoil with grip
camerashake add @s[tag=sneaking, tag=foregrip] 0.012 0.1 rotational
camerashake add @s[tag=!sneaking, tag=foregrip] 0.016 0.1 rotational

# core
scoreboard players remove @s[scores={m4a1=1..}] m4a1 1
function effect/shot_light
event entity @s trenbankai:m4a1_fire
