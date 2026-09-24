"""Script side: shop menus, right-click shops, spicy food thirst, kiosk music cleanup."""
import json, os
from data import SHOPS, FOODS, SUCCUBI
from build_food import lore


def edit(path, old, new, count=1):
    s = open(path, encoding='utf-8').read()
    assert s.count(old) == count, (path, old[:60], s.count(old))
    open(path, 'w', encoding='utf-8').write(s.replace(old, new))


def build(bp, menus, log):
    sd = f'{bp}/scripts/succubi'

    # ---- products.js: kiosk foods + shop menus
    foods = []
    for f in FOODS:
        foods.append({"key": f['key'], "id": f"food:{f['key']}", "name": f['name'], "price": f['price'],
                      "food": f['food'], "saturation": f['sat'], "thirst": f['thirst'],
                      "effects": [{"effect": e, "seconds": s, "amplifier": a} for e, s, a in f['effects']],
                      "lore": lore(f)})
    js = open(f'{sd}/products.js', encoding='utf-8').read()
    old = "export const PRODUCT_BY_ID = new Map([...DRINKS, ...SNACKS].map((p) => [p.id, p]));"
    assert old in js
    menu_js = []
    for s in SHOPS:
        entries = ", ".join(f'["{it["ref"]}", {it["price"]}]' for it in menus[s['key']])
        menu_js.append(f'  {s["key"]}: menu([{entries}])')
    js = js.replace(old, (
        "// GENERATED - dishes sold by the kiosk shops (models from the Food Items pack)\n"
        f"export const KIOSK_FOODS = {json.dumps(foods, ensure_ascii=False, indent=2)};\n\n"
        "export const PRODUCT_BY_ID = new Map([...DRINKS, ...SNACKS, ...KIOSK_FOODS].map((p) => [p.id, p]));\n\n"
        "// Shop menu = product + the price that shop charges (vending drinks cost a little more at a stall)\n"
        "const menu = (entries) => entries.map(([id, price]) => ({ ...PRODUCT_BY_ID.get(id), price }));\n"
        "export const SHOP_MENUS = {\n" + ",\n".join(menu_js) + "\n};\n"))
    open(f'{sd}/products.js', 'w', encoding='utf-8').write(js)

    # ---- shops.js: which kiosk opens which menu / skin
    lines = ['import { SHOP_MENUS } from "./products.js";', '',
             '// Kiosk shops: right-click = shop screen (same cash / change flow as the vending machines),',
             '// sneak + right-click = dismantle (handled by the entity). The flag picks the skin in RP ui/server_form.json.',
             'export const SHOPS = {']
    for s in SHOPS:
        lines.append(f'  "{s["entity"]}": {{ flag: "{s["flag"]}", title: "{s["title"]}", products: SHOP_MENUS.{s["key"]}, prefix: "{s["key"]}", tex: "textures/ui/succubi_shops/", who: "ร้าน", slots: [1, 5, 10, 20, 50, 100, 500, 1000] }},')
    lines[-1] = lines[-1].rstrip(',')
    lines += ['};', '']
    open(f'{sd}/shops.js', 'w', encoding='utf-8').write('\n'.join(lines))

    # ---- vending.js: shops reuse the machine screen
    v = f'{sd}/vending.js'
    edit(v, 'import { formatBaht } from "./economy.js";\n', 'import { formatBaht } from "./economy.js";\nimport { SHOPS } from "./shops.js";\n')
    edit(v, "function closeMachine(player) {\n  const back = returnChange(player);\n  if (back > 0) {\n    player.sendMessage(`§e[${\"ตู้\"}] ทอนเงิน ${formatBaht(back)} บาท`);",
         "function closeMachine(player, machine) {\n  const back = returnChange(player);\n  if (back > 0) {\n    player.sendMessage(`§e[${machine?.who ?? \"ตู้\"}] ทอนเงิน ${formatBaht(back)} บาท`);")
    edit(v, "  if (!response || response.canceled) return closeMachine(player);", "  if (!response || response.canceled) return closeMachine(player, machine);")
    edit(v, "  } else {\n    return closeMachine(player);\n  }", "  } else {\n    return closeMachine(player, machine);\n  }")
    edit(v, "    form.button(`${affordable ? \"§l\" : \"§7\"}${p.price}.-`, `${VT}p_${machine.prefix}_${p.key}${affordable ? \"\" : \"_off\"}`);",
         "    form.button(`${affordable ? \"§l\" : \"§7\"}${p.price}.-`, `${machine.tex ?? VT}p_${machine.prefix}_${p.key}${affordable ? \"\" : \"_off\"}`);")
    edit(v, "    const machine = MACHINES[event.target?.typeId];\n    if (!machine) return;\n",
         "    const machine = MACHINES[event.target?.typeId] ?? SHOPS[event.target?.typeId];\n    if (!machine) return;\n"
         "    if (SHOPS[event.target.typeId] && event.player.isSneaking) return; // sneak + right-click dismantles the kiosk\n")

    # shops also take 500 / 1000 notes (their meals can cost more than 100)
    edit(v, 'const CASH_ID = { 1: "succubi:coin_1", 5: "succubi:coin_5", 10: "succubi:coin_10", 20: "succubi:banknote_20", 50: "succubi:banknote_50", 100: "succubi:banknote_100" };',
         'const CASH_ID = { 1: "succubi:coin_1", 5: "succubi:coin_5", 10: "succubi:coin_10", 20: "succubi:banknote_20", 50: "succubi:banknote_50", 100: "succubi:banknote_100", 500: "succubi:banknote_500", 1000: "succubi:banknote_1000" };')
    edit(v, "export function insertAll(player) {", "export function insertAll(player, slots = COIN_SLOTS) {")
    edit(v, "    if (!COIN_SLOTS.includes(value)) continue;", "    if (!slots.includes(value)) continue;")
    edit(v, "  const credit = getCredit(player);\n  const container = inventoryOf(player);\n  const form = new ActionFormData()",
         "  const credit = getCredit(player);\n  const container = inventoryOf(player);\n  const slots = machine.slots ?? COIN_SLOTS;\n  const form = new ActionFormData()")
    edit(v, "  for (const value of COIN_SLOTS) {", "  for (const value of slots) {")
    edit(v, "  } else if (index <= count + COIN_SLOTS.length) {\n    const value = COIN_SLOTS[index - count - 1];",
         "  } else if (index <= count + slots.length) {\n    const value = slots[index - count - 1];")
    edit(v, "  } else if (index === count + COIN_SLOTS.length + 1) {\n    const total = insertAll(player);",
         "  } else if (index === count + slots.length + 1) {\n    const total = insertAll(player, slots);")

    # ---- thirst.js: salty / spicy dishes make you thirsty
    t = f'{sd}/thirst.js'
    edit(t, "    const gain = thirstGain(item);\n    if (gain > 0) setThirst(player, getThirst(player) + gain);",
         "    const gain = thirstGain(item);\n    if (gain !== 0) setThirst(player, getThirst(player) + gain);\n"
         "    if (gain < 0) player.onScreenDisplay.setActionBar(\"§cเผ็ดจนคอแห้ง! หาน้ำดื่มด้วย\");")

    # ---- kiosk_audio.js: the tea kiosk music stops when the kiosk is gone (from the kiosk pack)
    open(f'{sd}/kiosk_audio.js', 'w', encoding='utf-8').write(KIOSK_AUDIO)

    m = f'{bp}/scripts/main.js'
    edit(m, 'import { initConsumables } from "./succubi/consumables.js";\n',
         'import { initConsumables } from "./succubi/consumables.js";\nimport { initKioskAudio } from "./succubi/kiosk_audio.js";\n')
    edit(m, "initConsumables();\n", "initConsumables();\ninitKioskAudio();\n")
    log('scripts updated')


KIOSK_AUDIO = '''import { world, system } from "@minecraft/server";
import { runAs } from "./cmd.js";

// Haruto tea kiosk plays music + announcements from its RP animation.
// When the last kiosk is removed / dismantled, stop what is still playing.
const TEA_KIOSK = "kiosk:haruto_tea_kiosk";
const SOUNDS = ["kiosk.haruto_tea.bgm", "kiosk.haruto_tea.announcement"];

function stopFor(player) {
  for (const sound of SOUNDS) runAs(player, `stopsound @s ${sound}`); // server source: works without cheats
}

function anyTeaKiosk() {
  for (const id of ["overworld", "nether", "the_end"]) {
    try {
      if (world.getDimension(id).getEntities({ type: TEA_KIOSK }).length > 0) return true;
    } catch (e) {}
  }
  return false;
}

export function initKioskAudio() {
  world.afterEvents.entityDie.subscribe((event) => {
    const dead = event.deadEntity;
    if (dead?.typeId !== TEA_KIOSK) return;
    try {
      for (const player of dead.dimension.getPlayers({ location: dead.location, maxDistance: 48 })) stopFor(player);
    } catch (e) {
      for (const player of world.getAllPlayers()) stopFor(player);
    }
  });
  let hadKiosk = true;
  system.runInterval(() => {
    const has = anyTeaKiosk();
    if (!has && hadKiosk) for (const player of world.getAllPlayers()) stopFor(player);
    hadKiosk = has;
  }, 40);
}
'''
