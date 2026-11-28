"""Addendum 2026-11-28: fill proposal 1 on the unified contest types, from fr_fill.json (fr_fill.py; seeded random
draws, 1,000 sets per contest). Per slate, summed over that type's contests: random from the board's top half / 25% /
10% minus entered (mean $), the median of the top-half draws minus entered, and entered minus plain random kept.
11-27 (157547) is included automatically once its standings and night record are on hand and fr_fill.py is re-run."""
import json, math, os, statistics as S
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "fr_fill.json")))
def line(lbl, d):
    m, se = S.mean(d), S.stdev(d) / math.sqrt(len(d)); k = sum(x > 0 for x in d)
    return "  %-34s %+.2f ± %.2f, ahead %d of %d, 2xSE %.2f -> %s" % (lbl, m, se, k, len(d), 2 * se, "clears" if m > 2 * se else "does not clear")
for t in ("flagship", "main"):
    for per, pf in (("since 11-24", lambda r: r["day"] >= "2026-11-24"), ("all slates", lambda r: True)):
        R = [r for r in rows if r["type"] == t and pf(r) and "top50" in r]
        if not R: continue
        by = defaultdict(list)
        for r in R: by[r["g"]].append(r)
        print("== %s, %s: %d contests on %d slates (%s)" % (t, per, len(R), len(by), ", ".join(sorted({r["day"] + "_" + r["g"] for r in R}))))
        for k, lbl in (("top50", "top-half random - entered"), ("top25", "top-25% random - entered"), ("top10", "top-10% random - entered")):
            print(line(lbl + " (mean $)", [sum(x[k][0] - x["ent_d"] for x in v) for v in by.values()]))
        print(line("top-half median $ - entered", [sum(x["top50"][1] - x["ent_d"] for x in v) for v in by.values()]))
        print(line("entered - plain random kept (mean $)", [sum(x["ent_d"] - x["rand"][0] for x in v) for v in by.values()]))
