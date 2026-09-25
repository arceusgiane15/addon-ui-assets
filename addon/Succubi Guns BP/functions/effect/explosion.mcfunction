execute as @s[tag=!underground] run playsound effect.weapon.echo @a[r=200] ~~~ 100 1 0.01
execute as @a[r=20] run playsound effect.player.blind @s

execute as @s[tag=!underground] run playsound effect.explosion.explode @a[r=50] ~~~ 100 1 0.01
execute as @s[tag=underground] run playsound effect.explosion.indoors @a[r=50] ~~~ 100 1 0.01

playsound effect.explosion.debris @a[r=40] ~~~ 10 1 0.01
playsound effect.explosion.distant @a[rm=15, r=400] ~~~ 200 1 0.01

camerashake add @a[rm=0, r=4] 0.6 0.25 rotational
camerashake add @a[rm=4, r=8] 0.4 0.25 rotational
camerashake add @a[rm=8, r=12] 0.2 0.15 rotational

damage @e[rm=0, r=4] 150 entity_explosion
damage @e[rm=4, r=6] 15 entity_explosion
damage @e[rm=6, r=8] 5 entity_explosion
