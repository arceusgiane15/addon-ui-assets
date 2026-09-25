titleraw @s[scores={glock18=11..}] actionbar {"rawtext":[{"text":"[ §7"},{"score":{"name":"@s","objective":"glock18"}},{"text":"§r/17 ]"}]}
titleraw @s[scores={glock18=1..10}] actionbar {"rawtext":[{"text":"[ §c"},{"score":{"name":"@s","objective":"glock18"}},{"text":"§r/17 ]"}]}
titleraw @s[scores={glock18=..0}] actionbar {"rawtext":[{"text":"[ §4"},{"score":{"name":"@s","objective":"glock18"}},{"text":"§r/17 ]"}]}

execute if score @s glock18 matches ..0 run event entity @s trenbankai:set_ammo_0
execute if score @s glock18 matches 1.. run event entity @s trenbankai:set_ammo_1