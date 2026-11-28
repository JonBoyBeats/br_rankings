import sys, json, os, math, statistics as S
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_proj_grade as PG
num = PG.num; BRR = "/home/user/battle-royale-research"
def ms(v):
    v = [x for x in v if x is not None]; return "%+.2f ± %.2f (%d)" % (S.mean(v), S.stdev(v)/math.sqrt(len(v)) if len(v) > 1 else float('nan'), len(v))
g = defaultdict(lambda: defaultdict(list))
for name, rows in PG.slates():
    f = f"{BRR}/data/dk/cbb/{name}_proj.json"
    if not os.path.exists(f): continue
    P = json.load(open(f))
    outs = defaultdict(int)
    for p in P.values():
        if p.get("status") == "Out" and (num(p.get("min_avg")) or 0) >= 15: outs[p.get("team")] += 1
    for r in PG.band(PG.graded(rows), *PG.ROTATION):
        if num(r.get("min")) is None or num(r.get("min_proj")) is None: continue
        a = num(r["min"]); k = "teammate out" if outs.get(r["team"]) else "full roster"
        g[k][name].append((abs(a - num(r["min_proj"])), abs(a - num(r["min_old"])) if num(r.get("min_old")) is not None else None, abs(a - num(r["ruler_min"])) if num(r.get("ruler_min")) is not None else None))
for k, d in g.items():
    print(k, "rows", sum(len(v) for v in d.values()), "LIVE", ms([S.mean(x[0] for x in v) for v in d.values()]),
          "LIVE-PREV", ms([S.mean(x[0]-x[1] for x in v if x[1] is not None) if any(x[1] is not None for x in v) else None for v in d.values()]),
          "LIVE-RULER", ms([S.mean(x[0]-x[2] for x in v if x[2] is not None) if any(x[2] is not None for x in v) else None for v in d.values()]))
