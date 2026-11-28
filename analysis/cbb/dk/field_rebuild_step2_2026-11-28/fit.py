"""Step 2: fit R2 (gamma) and R3 (its form and value) per contest type, leave one slate out, on construction only (never on cash
lines), and build each held-out slate's candidate field per type. Pre-registration: field_rebuild_step1 (92800a0).
  R2: target own_t = own^gamma, renormalised to 800 (clipped at 100), own = today's corrected ownership of the pool
  R3: the rake's iterative-proportional-fitting weights toward own_t, then one of R3's two registered draw forms (FORMS)
Loss per training contest: (d_own_total/10)^2 + (d_top8/20)^2 + (d_dup/5)^2 + (d_top_pair/5)^2 (scales fixed before
any grading). Types with fewer than 3 training slates use the parameters fit on all types pooled.
python3 fit.py --data <dir>  ->  <dir>/<slate>_cand.json, fit_rows.json, construction.json"""
import argparse, glob, json, os, statistics as S
from collections import Counter
from itertools import combinations
import numpy as np

GAMMA = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
BETA = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
COPY = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4]
# R3's two registered forms (field_rebuild_step1: "weights raised to a power (or a fixed copy share) fit per type"):
#   ("pow", beta): FIELD_N drawn with replacement, P proportional to weight^beta
#   ("copy", c):   (1 - c) x FIELD_N drawn without replacement by weight (the rake's draw), c x FIELD_N copies of them
#                  drawn with replacement by weight. The fit picks the form and its value per type, held out.
FORMS = [("pow", b) for b in BETA] + [("copy", c) for c in COPY]
N = 1000
SCALE = {"own": 10.0, "top8": 20.0, "dup": 5.0, "pair": 5.0}

def sharpen(own, g):
    v = {k: max(x, 0.0) ** g for k, x in own.items()}
    for _ in range(50):
        s = sum(v.values()) or 1.0
        v = {k: x * 800.0 / s for k, x in v.items()}
        over = [k for k, x in v.items() if x > 100.0]
        if not over: break
        for k in over: v[k] = 100.0
    return v

def ipf(pool, target, iters=60):          # the rake's weighting (dk_cbb_field.rake), returns weights
    w = np.ones(len(pool)); idx = {}
    for i, L in enumerate(pool):
        for k in L: idx.setdefault(k, []).append(i)
    keys = list(idx); kpos = {k: j for j, k in enumerate(keys)}
    M = np.zeros((len(pool), len(keys)))
    for i, L in enumerate(pool):
        for k in L: M[i, kpos[k]] = 1
    tgt = np.array([max(target.get(k, 0.0), 1e-3) for k in keys])
    for _ in range(iters):
        share = 100 * (M.T @ w) / w.sum()
        lf = np.log(tgt / np.maximum(share, 1e-9))
        w = w * np.exp((M @ lf) / 8.0)
        w = np.minimum(w, 50 * w.mean())
    return w

def draw(pool, w, form, seed):
    rng = np.random.default_rng(seed)
    kind, v = form
    if kind == "pow":
        p = w ** v; p = p / p.sum()
        return [tuple(sorted(pool[i])) for i in rng.choice(len(pool), size=N, replace=True, p=p)]
    m = int(round((1 - v) * N))
    keys = rng.random(len(pool)) ** (1.0 / np.maximum(w, 1e-12))
    base = list(np.argsort(-keys)[:m])
    p = w[base] / w[base].sum()
    extra = list(rng.choice(base, size=N - m, replace=True, p=p)) if N > m else []
    return [tuple(sorted(pool[i])) for i in base + extra]

def pj(r):                                 # our projection at lock through the gate, as dk_eval fieldcheck reads it
    return r["fp_gate"] if r.get("fp_gate") is not None else (r.get("fp_dk") or 0)

def metrics(F, real, players):
    """construction of a field F against a contest's real lineups (both sampled to the same n)"""
    rown = Counter(i for x in real for i in x); rown = {k: 100 * v / len(real) for k, v in rown.items()}
    n = min(len(real), len(F), N)
    rng = np.random.default_rng(len(real))
    Fs = [F[i] for i in rng.choice(len(F), size=n, replace=False)] if len(F) > n else F
    Rs = [real[i] for i in rng.choice(len(real), size=n, replace=False)] if len(real) > n else real
    def m(L):
        own = Counter(i for x in L for i in x)
        cnt = Counter(L); pairs = Counter()
        for x in L: pairs.update(combinations(x, 2))
        return {"own": S.mean(sum(rown.get(i, 0) for i in x) for x in L),
                "top8": sum(sorted((100 * v / len(L) for v in own.values()), reverse=True)[:8]),
                "dup": 100 * sum(c for c in cnt.values() if c > 1) / len(L),
                "pair": 100 * pairs.most_common(1)[0][1] / len(L),
                "proj": S.mean(sum(pj(players.get(i) or {}) for i in x) for x in L)}
    return m(Fs), m(Rs)

def main():
    global rows, fields
    ap = argparse.ArgumentParser(); ap.add_argument("--data"); ap.add_argument("--out"); a = ap.parse_args()
    slates = sorted(f for f in glob.glob(os.path.join(a.data, "20*_*.json")) if not f.endswith(("_pool.json", "_cand.json", "_pool_r4.json")))
    D = {}
    for f in slates:
        s = json.load(open(f)); P = json.load(open(f.replace(".json", "_pool.json")))
        key = os.path.basename(f)[:-5]
        pool = [tuple(str(i) for i in L) for L in P["pool"]]
        D[key] = {"s": s, "pool": pool, "own": {str(k): v for k, v in P["own"].items()},
                  "contests": [c for c in s["contests"] if len(c["real"]) >= 20]}
        for c in D[key]["contests"]:
            c["real"] = [tuple(sorted(str(i) for i in x)) for x in c["real"]]
        print("loaded", key, len(pool), flush=True)

    # the grid: every slate x gamma x R3 form, every contest's construction gap
    rows = []
    fields = {}
    for key, d in D.items():
        for gi, g in enumerate(GAMMA):
            w = ipf(d["pool"], sharpen(d["own"], g))
            for bi, b in enumerate(FORMS):
                F = draw(d["pool"], w, b, seed=7 + 100 * gi + bi)
                fields[(key, g, b)] = F
                for c in d["contests"]:
                    fm, rm = metrics(F, c["real"], d["s"]["players"])
                    rows.append({"slate": key, "cid": c["id"], "type": c["type"], "gamma": g, "form": list(b),
                                 **{"d_" + k: fm[k] - rm[k] for k in fm}})
        print("grid", key, flush=True)

    def loss(rs):
        return S.mean(sum((r["d_" + k] / SCALE[k]) ** 2 for k in SCALE) for r in rs)

    def fit(train, typ):
        best = None
        for g in GAMMA:
            for b in FORMS:
                rs = [r for r in rows if r["slate"] in train and (typ is None or r["type"] == typ) and r["gamma"] == g and tuple(r["form"]) == b]
                if not rs: continue
                l = loss(rs)
                if best is None or l < best[0]: best = (l, g, b)
        return best

    chosen, cons = {}, []
    for key, d in D.items():
        train = [k for k in D if k != key]
        pooled = fit(train, None)
        chosen[key] = {}
        for t in ("flagship", "main", "qualifier"):
            nslates = len({r["slate"] for r in rows if r["slate"] in train and r["type"] == t})
            p = fit(train, t) if nslates >= 3 else None
            p = p or pooled
            chosen[key][t] = {"gamma": p[1], "form": list(p[2]), "train_slates": nslates, "pooled": nslates < 3}
        cand = {t: fields[(key, v["gamma"], tuple(v["form"]))] for t, v in chosen[key].items()}
        json.dump({"params": chosen[key], "fields": {t: [list(x) for x in F] for t, F in cand.items()}},
                  open(os.path.join(a.data, key + "_cand.json"), "w"))
        prev = [tuple(sorted(str(i) for i in L)) for L in d["s"]["prev_field"]]
        for c in d["contests"]:
            fm, rm = metrics(cand[c["type"]], c["real"], d["s"]["players"])
            pm, _ = metrics(prev, c["real"], d["s"]["players"])
            cons.append({"slate": key, "cid": c["id"], "type": c["type"], "entries": c["entries"], "real": rm, "cand": fm, "prev": pm})
        print("held out", key, chosen[key], flush=True)
    json.dump(rows, open(os.path.join(a.out, "fit_rows.json"), "w"))
    json.dump({"chosen": chosen, "construction": cons}, open(os.path.join(a.out, "construction.json"), "w"), indent=0)


if __name__ == "__main__":
    main()
