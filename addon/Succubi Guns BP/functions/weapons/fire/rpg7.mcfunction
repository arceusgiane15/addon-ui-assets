# sounds
execute as @s[tag=!underground] run playsound weapon.rpg7.fire @a[r=300] ^^^1.5 100 1 0.01
execute as @s[tag=underground]  run playsound weapon.rpg7.fire.indoor @a[r=200] ^^^1.5 100 1 0.01

# anims
playanimation @s animation.rpg7.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:rpg7')"

# recoil
camerashake add @s[tag=sneaking, tag=foregrip] 0.01 0.1 rotational
camerashake add @s[tag=!sneaking, tag=foregrip] 0.015 0.1 rotational

# effects
execute positioned ^^^-2 as @e[r=1.5] run damage @s 4 entity_explosion entity @s
execute anchored feet run particle trenbankai:rpg7_smoke_ground ~~~
execute anchored feet run particle trenbankai:rpg7_smoke_ground ~~~

# core
scoreboard players remove @s[scores={rpg7=1..}] rpg7 1
function effect/shot_light
event entity @s trenbankai:rpg7_fire
