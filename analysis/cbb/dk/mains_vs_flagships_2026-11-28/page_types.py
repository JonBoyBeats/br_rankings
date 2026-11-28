"""Reclassify by the DK page's contest profile (scripts/dk_flagship_compare.js line 27): flagship = Pull Up Jumper, or 100-799
entries and not Dime Time / And-One / Quarter Jukebox / qualifier / satellite. Rewrites the type in mf_rows_page.json and fr_fill_page.json."""
import json, re
def page_type(name, n):
    if re.search("qualifier|satellite", name, re.I) or n < 100: return "qualifier/small"
    if re.search("pull up jumper", name, re.I) or (not re.search("dime time|and-one|quarter jukebox", name, re.I) and 100 <= n < 800): return "flagship"
    return "main"
R = json.load(open("mf_rows.json")); names = {r["cid"]: (r["name"], r["n"]) for r in R}
moved = [(r["name"], r["n"], r["type"]) for r in R if page_type(r["name"], r["n"]) != r["type"]]
for r in R: r["type"] = page_type(r["name"], r["n"])
json.dump(R, open("mf_rows_page.json", "w"))
F = json.load(open("fr_fill.json"))
for r in F: r["type"] = page_type(*names[r["cid"]])
json.dump(F, open("fr_fill_page.json", "w"))
print("contests that change type under the page profile:", len(moved)); [print("  ", m) for m in sorted(set(moved))]
