titleraw @s[scores={rpg7=1..}] actionbar {"rawtext":[{"text":"[ §7"},{"score":{"name":"@s","objective":"rpg7"}},{"text":"§r/1 ]"}]}
titleraw @s[scores={rpg7=..0}] actionbar {"rawtext":[{"text":"[ §4"},{"score":{"name":"@s","objective":"rpg7"}},{"text":"§r/1 ]"}]}

execute if score @s rpg7 matches ..0 run event entity @s trenbankai:set_ammo_0
execute if score @s rpg7 matches 1.. run event entity @s trenbankai:set_ammo_1