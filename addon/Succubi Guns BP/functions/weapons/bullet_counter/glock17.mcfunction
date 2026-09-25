titleraw @s[scores={glock17=11..}] actionbar {"rawtext":[{"text":"[ §7"},{"score":{"name":"@s","objective":"glock17"}},{"text":"§r/17 ]"}]}
titleraw @s[scores={glock17=1..10}] actionbar {"rawtext":[{"text":"[ §c"},{"score":{"name":"@s","objective":"glock17"}},{"text":"§r/17 ]"}]}
titleraw @s[scores={glock17=..0}] actionbar {"rawtext":[{"text":"[ §4"},{"score":{"name":"@s","objective":"glock17"}},{"text":"§r/17 ]"}]}

execute if score @s glock17 matches ..0 run event entity @s trenbankai:set_ammo_0
execute if score @s glock17 matches 1.. run event entity @s trenbankai:set_ammo_1