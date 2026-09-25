# Adds the curse skin (§0§9§4§3) to RP ui/succubi_ui.json next to the settings / horror skins (idempotent).
import copy, json, os, sys
RP = sys.argv[1] if len(sys.argv) > 1 else "Succubi Server RP"
p = os.path.join(RP, "ui/succubi_ui.json")
d = json.load(open(p))
H, C = "§0§9§4§2", "§0§9§4§3"
DEFAULT = "(((#title_text - '§0§9§4§1') = #title_text) and ((#title_text - '§0§9§4§2') = #title_text))"
NEW_DEFAULT = "(((#title_text - '§0§9§4§1') = #title_text) and ((#title_text - '§0§9§4§2') = #title_text) and ((#title_text - '§0§9§4§3') = #title_text))"
added = 0

def walk(node):
    global added
    if isinstance(node, dict):
        for c in node.get("controls", []) if isinstance(node.get("controls"), list) else []:
            pass
        ctrls = node.get("controls")
        if isinstance(ctrls, list):
            names = {k for c in ctrls for k in c}
            extra = []
            for c in ctrls:
                for k, v in c.items():
                    if not isinstance(v, dict):
                        continue
                    for b in v.get("bindings", []):
                        if b.get("source_property_name") == DEFAULT:
                            b["source_property_name"] = NEW_DEFAULT
                    horror = any(H in str(b.get("source_property_name", "")) and "not" in str(b.get("source_property_name", "")) for b in v.get("bindings", []))
                    if horror and "horror" in k:
                        nk = k.replace("horror", "curse")
                        if nk in names:
                            continue
                        nv = json.loads(json.dumps(v, ensure_ascii=False).replace(H, C).replace("_horror", "_curse"))
                        extra.append({nk: nv})
                        added += 1
            ctrls.extend(extra)
        for v in node.values():
            walk(v)
    elif isinstance(node, list):
        for v in node:
            walk(v)

walk(d)
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
print("curse variants added:", added)
