"""Context: the primary on section 6's own contest set (the shadow contest of each slate, the one eval.csv logs
sim_cash for), R1-R3 and R1-R4. python3 shadow_subset.py"""
import json, math, statistics as S
for lab, f in (("R1-R3", "grade_rows.json"), ("R1-R4", "grade_rows_r4.json")):
    R = [r for r in json.load(open(f)) if r["shadow"] and r["entries"] >= 100]
    v = [abs(r["prev"]["cash"] - r["field_cash"]) - abs(r["cand"]["cash"] - r["field_cash"]) for r in R]
    print("%s shadow contests: %d slates, |cash gap| gain %+.2f ± %.2f, better on %d" % (lab, len(v), S.mean(v), S.stdev(v) / math.sqrt(len(v)), sum(x > 0 for x in v)))
