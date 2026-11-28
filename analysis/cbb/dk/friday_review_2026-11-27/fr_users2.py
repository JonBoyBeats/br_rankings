"""Section 5 actionable test: does a construction trait predict real results held out? Entries binned within each
contest by own_sum quintile (real ownership summed) and by salary left; per slate the bin's mean finish pct, top-10% and
top-1% rates and ROI (payout / fees - 1). Held out: the best bin chosen on alternate slates, scored on the others."""
import math, statistics as S
from collections import defaultdict
src = open(__file__.replace("fr_users2.py", "fr_users.py")).read().split("# ---- WHO")[0]
exec(src)
def qbin(vals, v):
    s = sorted(vals); r = sum(x < v for x in s) / len(s); return min(4, int(5 * r))
byc = defaultdict(list)
for e in E_rows: byc[e["cid"]].append(e)
for cid, es in byc.items():
    os_ = [e["own_sum"] for e in es]
    for e in es:
        e["own_q"] = qbin(os_, e["own_sum"])
        e["sal_b"] = 0 if e["sal_left"] <= 100 else 1 if e["sal_left"] <= 400 else 2
def table(key, nb, lab):
    print("\n== %s bins (per slate means, then mean ± SE over slates)" % lab)
    per = defaultdict(lambda: defaultdict(list))
    for e in E_rows: per[e[key]][e["slate"]].append(e)
    res = {}
    for b in range(nb):
        sl = per[b]
        pct = [S.mean(x["pct"] for x in v) for v in sl.values()]
        t1 = [S.mean(x["top1"] for x in v) for v in sl.values()]
        t10 = [S.mean(x["top10"] for x in v) for v in sl.values()]
        roi = [sum(x["pay"] for x in v) / sum(x["fee"] for x in v) - 1 for v in sl.values() if sum(x["fee"] for x in v)]
        res[b] = {s: (S.mean(x["pct"] for x in v), sum(x["pay"] for x in v) / max(1e-9, sum(x["fee"] for x in v)) - 1) for s, v in sl.items()}
        se = lambda a: S.stdev(a) / math.sqrt(len(a))
        print("bin %d: entries %5d | pct %.1f ± %.1f | top10 %.3f | top1 %.4f | ROI %+.0f%% ± %.0f (slates %d)" % (b, sum(len(v) for v in sl.values()), S.mean(pct), se(pct), S.mean(t10), S.mean(t1), 100 * S.mean(roi), 100 * se(roi), len(roi)))
    sl_all = sorted({e["slate"] for e in E_rows})
    for metric, mi in (("pct", 0), ("ROI", 1)):
        for A, B in ((set(sl_all[0::2]), set(sl_all[1::2])), (set(sl_all[1::2]), set(sl_all[0::2]))):
            best = max(range(nb), key=lambda b: S.mean(v[mi] for s, v in res[b].items() if s in A))
            allb = {s: S.mean(res[b][s][mi] for b in range(nb) if s in res[b]) for s in B}
            d = [res[best][s][mi] - allb[s] for s in B if s in res[best]]
            print("  held out on %s: best bin on fit half = %d; test half, bin minus mean of bins %+.3f ± %.3f (%d), positive on %d" % (metric, best, S.mean(d), S.stdev(d) / math.sqrt(len(d)), len(d), sum(x > 0 for x in d)))
table("own_q", 5, "own_sum quintile within contest (0 = least owned)")
table("sal_b", 3, "salary left (0: <=$100, 1: $101-400, 2: >$400)")
us = [e for e in E_rows if e["user"] == "us"]
from collections import Counter
print("\nour entries by own_sum quintile:", dict(sorted(Counter(e["own_q"] for e in us).items())), "| field share per quintile is 20% by construction")
print("our entries by salary-left bin:", dict(sorted(Counter(e["sal_b"] for e in us).items())), "| field:", dict(sorted(Counter(e["sal_b"] for e in E_rows).items())))
