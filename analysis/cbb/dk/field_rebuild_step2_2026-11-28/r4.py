"""R4 (pre-registered add-on, triggered: R1-R3 left our projected points per lineup above the real field's). A share s
of each type's R1-R3 field is replaced by lineups drawn uniformly from a second pool built with every build style's
noise x2 (gen.py --noise-x 2), s fit per type held out (other slates only) on the R1-R3 loss plus (d_proj / 2)^2,
the R1-R3 parameters being the held-out slate's own. Writes <data>/<slate>_cand_r4.json, construction_r4.json.
python3 r4.py --data <dir> --out <dir>"""
import argparse, glob, json, os, statistics as St
import numpy as np
from fit import GAMMA, FORMS, N, SCALE, sharpen, ipf, draw, metrics
ap = argparse.ArgumentParser(); ap.add_argument("--data"); ap.add_argument("--out"); a = ap.parse_args()
SHARE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
chosen = json.load(open(os.path.join(a.out, "construction.json")))["chosen"]
D = {}
for f in sorted(f for f in glob.glob(os.path.join(a.data, "20*_*.json")) if not f.endswith(("_pool.json", "_cand.json", "_pool_r4.json", "_cand_r4.json"))):
    key = os.path.basename(f)[:-5]
    s = json.load(open(f)); P = json.load(open(f.replace(".json", "_pool.json"))); P4 = json.load(open(f.replace(".json", "_pool_r4.json")))
    D[key] = {"s": s, "pool": [tuple(str(i) for i in L) for L in P["pool"]], "noisy": [tuple(sorted(str(i) for i in L)) for L in P4["pool"]],
              "own": {str(k): v for k, v in P["own"].items()},
              "contests": [dict(c, real=[tuple(sorted(str(i) for i in x)) for x in c["real"]]) for c in s["contests"] if len(c["real"]) >= 20]}
W, F123 = {}, {}
def field123(k, g, form):
    if (k, g) not in W: W[(k, g)] = ipf(D[k]["pool"], sharpen(D[k]["own"], g))
    if (k, g, tuple(form)) not in F123:
        F123[(k, g, tuple(form))] = draw(D[k]["pool"], W[(k, g)], tuple(form), seed=7 + 100 * GAMMA.index(g) + FORMS.index(tuple(form)))
    return F123[(k, g, tuple(form))]
def mix(k, F, s):
    m = int(round(s * N))
    if not m: return F
    rng = np.random.default_rng(11)
    return F[: N - m] + [D[k]["noisy"][i] for i in rng.choice(len(D[k]["noisy"]), size=m, replace=True)]
def loss(rs):
    return St.mean(sum((r["d_" + q] / SCALE[q]) ** 2 for q in SCALE) + (r["d_proj"] / 2.0) ** 2 for r in rs)
cons, picked = [], {}
for h in D:
    picked[h] = {}
    cand = {}
    for t, p in chosen[h].items():
        best = None
        for s in SHARE:
            rs = []
            for k in D:
                if k == h: continue
                F = mix(k, field123(k, p["gamma"], p["form"]), s)
                for c in D[k]["contests"]:
                    if c["type"] == t or p["pooled"]:
                        fm, rm = metrics(F, c["real"], D[k]["s"]["players"])
                        rs.append({"d_" + q: fm[q] - rm[q] for q in fm})
            if rs and (best is None or loss(rs) < best[0]): best = (loss(rs), s)
        picked[h][t] = best[1]
        cand[t] = mix(h, field123(h, p["gamma"], p["form"]), best[1])
    json.dump({"params": {t: dict(chosen[h][t], r4_share=picked[h][t]) for t in chosen[h]}, "fields": {t: [list(x) for x in F] for t, F in cand.items()}},
              open(os.path.join(a.data, h + "_cand_r4.json"), "w"))
    for c in D[h]["contests"]:
        fm, rm = metrics(cand[c["type"]], c["real"], D[h]["s"]["players"])
        cons.append({"slate": h, "cid": c["id"], "type": c["type"], "entries": c["entries"], "real": rm, "cand": fm})
    print("held out", h, picked[h], flush=True)
json.dump({"r4_share": picked, "construction": cons}, open(os.path.join(a.out, "construction_r4.json"), "w"), indent=0)
