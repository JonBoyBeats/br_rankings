"""The concentration miss (Friday review section 3, fr_own2's 200+ entry version) recomputed on own_eval.csv as it
stands: per contest of 200+ entries, the field's top-8 real ownership sum minus our raw top-8 sum (and the real
ownership of OUR top 8 minus ours), per slate, then mean +- SE over slates."""
import sys, os, math, statistics as S
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "scripts"))
import dk_eval as E
byc = defaultdict(list)
for r in E.own_grade_rows():
    if r["n"] >= 200: byc[(str(r["draft_group"]), r["contest_id"])].append(r)
per = defaultdict(list)
for (g, c), rs in byc.items():
    a8 = sum(sorted((r["a"] for r in rs), reverse=True)[:8]); p8 = sum(sorted((r["raw"] for r in rs), reverse=True)[:8])
    ours8 = sorted(rs, key=lambda r: -r["raw"])[:8]
    per[g].append((a8 - p8, sum(r["a"] for r in ours8) - p8))
f = lambda d: "%+.1f ± %.1f (%d), positive on %d" % (S.mean(d), S.stdev(d) / math.sqrt(len(d)), len(d), sum(x > 0 for x in d))
print("real top8 - raw top8:", f([S.mean(x[0] for x in v) for v in per.values()]))
print("real own of our top8 - raw:", f([S.mean(x[1] for x in v) for v in per.values()]))
