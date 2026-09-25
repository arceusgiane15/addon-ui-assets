# System designed by HardSK, all copyrights to our team.

# left
execute as @s[tag=!lean_left] anchored eyes unless block ^0.5^^0.8 air run event entity @s trenbankai:add_lean_left
execute as @s[tag=lean_left] anchored eyes if block ^0.5^^0.8 air run event entity @s trenbankai:remove_lean
execute as @s[tag=!lean_left] anchored eyes unless block ^0.5^^0.8 air run tag @s add lean_left
execute as @s[tag=lean_left] anchored eyes if block ^0.5^^0.8 air run tag @s remove lean_left
# right
execute as @s[tag=!lean_right] anchored eyes unless block ^-0.5^^0.8 air run event entity @s trenbankai:add_lean_right
execute as @s[tag=lean_right] anchored eyes if block ^-0.5^^0.8 air run event entity @s trenbankai:remove_lean
execute as @s[tag=!lean_right] anchored eyes unless block ^-0.5^^0.8 air run tag @s add lean_right
execute as @s[tag=lean_right] anchored eyes if block ^-0.5^^0.8 air run tag @s remove lean_right
