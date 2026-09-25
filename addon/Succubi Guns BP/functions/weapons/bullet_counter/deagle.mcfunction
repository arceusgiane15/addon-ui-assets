titleraw @s[scores={deagle=6..}] actionbar {"rawtext":[{"text":"[ §7"},{"score":{"name":"@s","objective":"deagle"}},{"text":"§r/10 ]"}]}
titleraw @s[scores={deagle=1..5}] actionbar {"rawtext":[{"text":"[ §c"},{"score":{"name":"@s","objective":"deagle"}},{"text":"§r/10 ]"}]}
titleraw @s[scores={deagle=..0}] actionbar {"rawtext":[{"text":"[ §4"},{"score":{"name":"@s","objective":"deagle"}},{"text":"§r/10 ]"}]}

execute if score @s deagle matches ..0 run event entity @s trenbankai:set_ammo_0
execute if score @s deagle matches 1.. run event entity @s trenbankai:set_ammo_1