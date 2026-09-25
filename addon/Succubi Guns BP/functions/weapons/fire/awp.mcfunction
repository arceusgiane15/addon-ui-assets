# sounds
execute as @s[tag=!underground] run playsound weapon.awp.fire @a[r=400] ^^^1.5 100 1 0.01
execute as @s[tag=underground] run playsound weapon.awp.fire.indoor @a[r=200] ^^^1.5 100 1 0.01

# anims
playanimation @s animation.awp.fire fire 0 "!q.is_item_name_any('slot.weapon.mainhand', 0, 'trenbankai:awp')"

# recoil
camerashake add @s[tag=sneaking] 0.04 0.22 rotational
camerashake add @s[tag=!sneaking] 0.1 0.22 rotational

# core
scoreboard players remove @s[scores={awp=1..}] awp 1
function effect/shot_light
event entity @s trenbankai:awp_fire
