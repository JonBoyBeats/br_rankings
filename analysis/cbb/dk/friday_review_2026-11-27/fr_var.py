"""Pool headline with and without the Variants of the top lineups, same nights (the PREVIOUS a variants change would log)."""
import json, glob, csv, os, sys, math, statistics as S, bisect
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E
DK = "/home/user/br_rankings/analysis/cbb/dk"
ev = defaultdict(dict)
for r in csv.DictReader(open(DK + "/eval.csv")): ev[r["draft_group"]][r["contest_id"]] = int(float(r["entries"]))
d = []; dk = []
for f in sorted(glob.glob(DK + "/builds/*.json")):
    name = os.path.basename(f)[8:-5]; g = name.split("_")[1]; rec = os.path.join(DK, name + ".csv")
    if not os.path.exists(rec): continue
    pts = {r["dk_id"]: E.num(r.get("actual_dk")) for r in E.read(rec)}
    if not any(v is not None for v in pts.values()): continue
    b = json.load(open(f)); kept = sorted(set(b.get("final") or [])); groups = b.get("groups") or {}
    isvar = lambda i: any(str(t).startswith("variant of") or groups.get(t) == "Variants of the top" for t in (b["tags"][i] if isinstance(b["tags"][i], list) else [b["tags"][i]]))
    nv = [i for i in kept if not isvar(i)]
    if len(nv) == len(kept): continue
    a, w, bk = [], [], []
    for cid, n in ev[g].items():
        if n < 100: continue
        sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(sf): continue
        field = sorted(e["points"] for e in E.standings_rows(open(sf, encoding="utf-8-sig"))[0]); N = len(field)
        pct = lambda L: 100 * bisect.bisect_right(field, sum((pts.get(str(i)) or 0) for i in L)) / N
        P = {i: pct(b["pool"][i]) for i in range(len(b["pool"]))}
        a.append(S.mean(P[i] for i in kept)); w.append(S.mean(P[i] for i in nv)); bk.append(S.mean(P.values()))
    if not a: continue
    print(name, "variants kept %d of %d | kept-bank with variants %+.2f, without %+.2f" % (len(kept) - len(nv), len(kept), S.mean(a) - S.mean(bk), S.mean(w) - S.mean(bk)))
    d.append(S.mean(a) - S.mean(w))
print("pool headline, with variants minus without (same nights): %+.2f ± %.2f (%d slates), positive on %d" % (S.mean(d), S.stdev(d) / math.sqrt(len(d)), len(d), sum(x > 0 for x in d)))
