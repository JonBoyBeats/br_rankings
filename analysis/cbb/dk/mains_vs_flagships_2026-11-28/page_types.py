"""Reclassify by the DK page's contest profile (scripts/dk_flagship_compare.js line 27): flagship = Pull Up Jumper, or 100-799
entries and not Dime Time / And-One / Quarter Jukebox / qualifier / satellite. Rewrites the type in mf_rows_page.json and fr_fill_page.json."""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'scripts'))
def page_type(name, n):
    """The one definition (scripts/dk_contest_type.py, the DK page's profile; 2026-11-28). This script reported
    "qualifier/small"; it passes its own size argument, which the page reads as the lobby size."""
    import dk_contest_type
    t = dk_contest_type.contest_type(name, n)
    return "qualifier/small" if t == "qualifier" else t
R = json.load(open("mf_rows.json")); names = {r["cid"]: (r["name"], r["n"]) for r in R}
moved = [(r["name"], r["n"], r["type"]) for r in R if page_type(r["name"], r["n"]) != r["type"]]
for r in R: r["type"] = page_type(r["name"], r["n"])
json.dump(R, open("mf_rows_page.json", "w"))
F = json.load(open("fr_fill.json"))
for r in F: r["type"] = page_type(*names[r["cid"]])
json.dump(F, open("fr_fill_page.json", "w"))
print("contests that change type under the page profile:", len(moved)); [print("  ", m) for m in sorted(set(moved))]
