import json, glob, csv, os, sys, math, statistics as S, bisect
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E
DK = "/home/user/br_rankings/analysis/cbb/dk"
ev = defaultdict(dict)
for r in csv.DictReader(open(DK + "/eval.csv")): ev[r["draft_group"]][r["contest_id"]] = int(float(r["entries"]))
res = defaultdict(dict)
for f in sorted(glob.glob(DK + "/builds/*.json")):
    name = os.path.basename(f)[8:-5]; g = name.split("_")[1]; rec = os.path.join(DK, name + ".csv")
    if not os.path.exists(rec): continue
    pts = {r["dk_id"]: E.num(r.get("actual_dk")) for r in E.read(rec)}
    if not any(v is not None for v in pts.values()): continue
    b = json.load(open(f)); kept = list(b.get("final") or [])
    vals = ((b.get("cut_state") or {}).get("board") or {}).get("values") or (b.get("idea_board") or {}).get("values")
    if not vals or len(vals) != len(kept): print(name, "no board values aligned", len(vals or []), len(kept)); continue
    order = [k for _, k in sorted(zip([-v[0] if isinstance(v, list) else -v for v in vals], kept))]
    for cid, n in ev[g].items():
        if n < 100: continue
        sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(sf): continue
        field = sorted(e["points"] for e in E.standings_rows(open(sf, encoding="utf-8-sig"))[0]); N = len(field)
        pct = lambda L: 100 * bisect.bisect_right(field, sum((pts.get(str(i)) or 0) for i in L)) / N
        P = {i: pct(b["pool"][i]) for i in set(kept)}
        bank = S.mean(pct(L) for L in b["pool"])
        row = {"bank": bank}
        for q in (0.1, 0.25, 0.5, 0.75, 1.0):
            k = order[:max(1, round(q * len(order)))]; row[q] = S.mean(P[i] for i in k)
        for k_, v in row.items(): res[name].setdefault(k_, []).append(v)
print("per slate (mean over 100+ contests): bank | kept top 10% / 25% / 50% / 75% / all kept (by the board's sim value)")
D = defaultdict(list)
for name, r in sorted(res.items()):
    m = {k: S.mean(v) for k, v in r.items()}
    print(name, "%.1f | %.1f / %.1f / %.1f / %.1f / %.1f" % (m["bank"], m[0.1], m[0.25], m[0.5], m[0.75], m[1.0]))
    D["kept - bank"].append(m[1.0] - m["bank"])
    for q in (0.1, 0.25, 0.5, 0.75): D["top %d%% - all kept" % (q * 100)].append(m[q] - m[1.0])
for k, v in D.items(): print("%-20s %+.2f ± %.2f (%d slates), positive on %d" % (k, S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 0 for x in v)))
