"""QMIN study, the same-seed banks (scripts/dk_qmin_bank.js) scored on real standings: top-10% line, cash line and
percentile, today vs the candidate.

  python3 scripts/dk_qmin_bank_score.py WORKDIR REPO OUT.json
"""
import sys, os, json, csv, math, statistics as S
W, REPO = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(REPO, "scripts"))
import dk_eval as E, dk_bank_noise_study as BN
res = {}
for key, date, g, cid in BN.NIGHTS:
    f = os.path.join(W, "bank", "qbank_%s.json" % key)
    if not os.path.exists(f):
        continue
    N = json.load(open(os.path.join(W, "bank", key + ".json"))); B = json.load(open(f))
    P = {r["dk_id"]: r for r in csv.DictReader(open(os.path.join(E.DK, "%s_%s.csv" % (date, g))))}
    act = {k: float(r["actual_dk"] or 0) for k, r in P.items()}
    ents, _ = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
    pts = sorted([e["points"] for e in ents], reverse=True)
    t10, cash = pts[math.ceil(0.1 * len(pts)) - 1], pts[min(max(E.pay_table(N["contest"]["payouts"])), len(pts)) - 1]
    asc = sorted(pts); pctl = lambda x: sum(1 for p in asc if p < x) / len(asc)
    res[key] = {}
    for v, L in B["banks"].items():
        sc = [sum(act.get(x, 0) for x in ids) for ids in L]
        res[key][v] = {"t10": S.mean(x >= t10 for x in sc), "cash": S.mean(x >= cash for x in sc), "pctl": S.mean(pctl(x) for x in sc), "moved": B["moved"][v]}
out = {"nights": res}
for k in ("t10", "cash", "pctl"):
    d = [res[n]["cand"][k] - res[n]["cur"][k] for n in res]
    out[k] = {"cur": S.mean(res[n]["cur"][k] for n in res), "cand": S.mean(res[n]["cand"][k] for n in res), "better": sum(x > 1e-9 for x in d), "worse": sum(x < -1e-9 for x in d), "of": len(d), "mean_d": S.mean(d), "se": S.stdev(d) / math.sqrt(len(d))}
json.dump(out, open(os.path.join(W, sys.argv[3]), "w"), indent=1)
for n, r in res.items():
    print(n, {v: {k: round(x * 100, 1) if k != "moved" else x for k, x in r[v].items()} for v in r})
for k in ("t10", "cash", "pctl"):
    print(k, {a: (round(b * 100, 2) if isinstance(b, float) else b) for a, b in out[k].items()})
