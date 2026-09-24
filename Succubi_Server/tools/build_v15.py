"""v1.0.15: HUD hides with F1 (vanilla #hud_visible), in creative / spectator, and no longer shows money."""
import json
from build_food import wjson
from build_scripts import edit


def build(bp, rp, log):
    # 1) F1: put the Succubi HUD under a panel bound to the game's own "HUD visible" flag
    p = f'{rp}/ui/hud_screen.json'
    h = json.load(open(p))
    ctr = h['hud_content_bg']['controls']
    i = next(k for k, c in enumerate(ctr) if 'succubi_hud@succubi_hud.hud_root' in c)
    ctr[i] = {"succubi_hud_gate": {
        "type": "panel", "size": ["100%", "100%"],
        "controls": [{"succubi_hud@succubi_hud.hud_root": {}}],
        "bindings": [{"binding_name": "#hud_visible", "binding_name_override": "#visible", "binding_type": "global"}]}}
    wjson(p, h)

    # 3) no money pill on the HUD
    p = f'{rp}/ui/succubi_hud.json'
    h = json.load(open(p))
    root = h['hud_root']
    root['controls'] = [c for c in root['controls'] if 'money' not in c]
    root['size'] = [92, root['size'][1]]
    wjson(p, h)

    # 2) creative / spectator: HUD hidden like the "hide_hud" tag; money no longer sent
    hj = f'{bp}/scripts/succubi/hud.js'
    edit(hj, '  if (player.hasTag("hide_hud")) {', '  if (player.hasTag("hide_hud") || hiddenMode(player)) {')
    edit(hj, "export function updateHud(player, tick) {",
         "// Creative / spectator players don't need survival stats on screen\n"
         "function hiddenMode(player) {\n  try {\n    const mode = String(player.getGameMode?.()).toLowerCase();\n"
         "    return mode === \"creative\" || mode === \"spectator\";\n  } catch (e) {\n    return false;\n  }\n}\n\n"
         "export function updateHud(player, tick) {")
    edit(hj, "  const subtitle = `§l§f${formatBaht(getBalance(player))} §eบาท`;", '  const subtitle = " "; // money is no longer shown on the HUD')
    log('v1.0.15: HUD follows F1 / creative / spectator, money removed')
