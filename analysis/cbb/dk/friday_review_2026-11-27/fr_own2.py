import sys, statistics as S, math
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E
rows = E.own_grade_rows()
byc = defaultdict(list)
for r in rows: byc[(str(r["draft_group"]), r["contest_id"])].append(r)
for (g, c), rs in byc.items():
    if g == "157382":
        for r in rs:
            if any(k in r["name"] for k in ("Avila", "Hall", "Allen", "West")): print(g, c, rs[0]["n"], r["name"], round(r["raw"],1), round(r["p"],1), round(r["a"],1))
# concentration: actual share held by the 8 most-owned (actual) vs our raw for the top 8 by our raw, per slate (mean over contests)
per = defaultdict(list)
for (g, c), rs in byc.items():
    a8 = sum(sorted((r["a"] for r in rs), reverse=True)[:8]); p8 = sum(sorted((r["raw"] for r in rs), reverse=True)[:8])
    per[g].append((a8, p8, rs[0]["date"]))
print("\nslate: real top-8 own sum vs our raw top-8 sum (mean over contests)")
d = []
for g, v in sorted(per.items(), key=lambda kv: kv[1][0][2]):
    a, p = S.mean(x[0] for x in v), S.mean(x[1] for x in v); d.append(a - p)
    print(v[0][2], g, len(v), "real %.0f ours %.0f diff %+.0f" % (a, p, a - p))
print("mean diff %+.1f ± %.1f (%d)" % (S.mean(d), S.stdev(d)/math.sqrt(len(d)), len(d)))
