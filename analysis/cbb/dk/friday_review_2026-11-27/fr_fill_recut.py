"""Correction 2026-11-28: section 9 re-cut on the unified contest types (scripts/dk_contest_type.py). Reads fr_fill.json
(fr_fill.py, which now imports the one definition; its random draws are seeded, so the values are the same as the
review's) and prints each figure under the OLD by-size split and the NEW page profile, for all slates and since 11-24."""
import csv, json, math, os, re, statistics as S
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "fr_fill.json")))
names = {}
for r in csv.DictReader(open(os.path.join(HERE, "..", "field_lineups.csv"))):
    names.setdefault(r["contest_id"], r["contest"])
def old(name, n):       # the review's original fr_fill.py rule
    if re.search("qualifier|satellite", name, re.I) or n < 100: return "qualifier/small"
    if re.search("pull up jumper", name, re.I) or 100 <= n < 800: return "flagship"
    return "main"
def ms(v):
    return "%+.2f ± %.2f (%d)" % (S.mean(v), S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan"), len(v)) if v else "n/a"
def per_slate(R, f):
    by = defaultdict(list)
    for r in R: by[r["g"]].append(r)
    return [f(v) for v in by.values()]
for lab, tf in (("OLD (by size)", lambda r: old(names.get(r["cid"], ""), r["n"])), ("NEW (page profile)", lambda r: r["type"])):
    print("==", lab)
    for t in ("flagship", "main", "qualifier/small"):
        for per, pf in (("all slates", lambda r: True), ("since 11-24", lambda r: r["day"] >= "2026-11-24"), ("before 11-24", lambda r: r["day"] < "2026-11-24")):
            R = [r for r in rows if tf(r) == t and pf(r)]
            if not R: continue
            d = per_slate(R, lambda v: sum(x["ent_d"] - x["rand"][0] for x in v))
            dm = per_slate(R, lambda v: sum(x["ent_d"] - x["rand"][1] for x in v))
            line = "%-16s %-12s contests %2d | entered - random mean $ %s, ahead %d of %d | median $ %s" % (
                t, per, len(R), ms(d), sum(x > 0 for x in d), len(d), ms(dm))
            RR = [r for r in R if "top50" in r]
            if RR:
                h = per_slate(RR, lambda v: sum(x["top50"][0] - x["ent_d"] for x in v))
                hm = per_slate(RR, lambda v: sum(x["top50"][1] - x["ent_d"] for x in v))
                line += " || top-half random - entered mean $ %s, ahead %d of %d; median $ %s" % (ms(h), sum(x > 0 for x in h), len(h), ms(hm))
            print(line)
