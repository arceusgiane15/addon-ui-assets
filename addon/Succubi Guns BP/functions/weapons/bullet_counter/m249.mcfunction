titleraw @s[scores={m249=51..}] actionbar {"rawtext":[{"text":"[ §7"},{"score":{"name":"@s","objective":"m249"}},{"text":"§r/200 ]"}]}
titleraw @s[scores={m249=6..50}] actionbar {"rawtext":[{"text":"[ §c"},{"score":{"name":"@s","objective":"m249"}},{"text":"§r/200 ]"}]}
titleraw @s[scores={m249=..5}] actionbar {"rawtext":[{"text":"[ §4"},{"score":{"name":"@s","objective":"m249"}},{"text":"§r/200 ]"}]}

execute if score @s m249 matches ..0 run event entity @s trenbankai:set_ammo_0
execute if score @s m249 matches 1 run event entity @s trenbankai:set_ammo_1
execute if score @s m249 matches 2 run event entity @s trenbankai:set_ammo_2
execute if score @s m249 matches 3 run event entity @s trenbankai:set_ammo_3
execute if score @s m249 matches 4 run event entity @s trenbankai:set_ammo_4
execute if score @s m249 matches 5 run event entity @s trenbankai:set_ammo_5
execute if score @s m249 matches 6 run event entity @s trenbankai:set_ammo_6
execute if score @s m249 matches 7 run event entity @s trenbankai:set_ammo_7
execute if score @s m249 matches 8.. run event entity @s trenbankai:set_ammo_8
