# vfx
execute if score @s m249 matches 5.. as @s[tag=!underground] run playsound weapon.m249.fire.belt @a[r=200] ^^^1.5 100 1 0.01
execute if score @s m249 matches 5.. as @s[tag=underground] run playsound weapon.m249.fire.belt.indoor @a[r=200] ^^^1.5 100 1 0.01
execute if score @s m249 matches ..4 as @s[tag=!underground] run playsound weapon.m249.fire @a[r=200] ^^^1.5 100 1 0.01
execute if score @s m249 matches ..4 as @s[tag=underground] run playsound weapon.m249.fire.indoor @a[r=200] ^^^1.5 100 1 0.01

# vfx
playanimation @s animation.m249.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:m249')"

# shake
camerashake add @s[tag=sneaking] 0.02 0.2 rotational
camerashake add @s[tag=!sneaking] 0.06 0.2 rotational

# core
scoreboard players remove @s[scores={m249=1..}] m249 1
function effect/shot_light
event entity @s trenbankai:m249_fire
