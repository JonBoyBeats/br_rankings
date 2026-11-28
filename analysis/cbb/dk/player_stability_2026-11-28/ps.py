"""Player stability: bias vs volatility (pre-registered in ../player_stability_2026-11-28.md).
Usage: python3 ps.py [--brr ../../../../../battle-royale-research]   (path to the battle-royale-research checkout)"""
import csv, glob, json, math, os, sys, statistics as st
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DK = os.path.dirname(HERE)
BRR = sys.argv[sys.argv.index("--brr") + 1] if "--brr" in sys.argv else "/home/user/battle-royale-research"
BOX = os.path.join(BRR, "data/cbb/box/2026-27")
Z10, Z90, ZSD = -1.42, 1.71, 1.25

def dkpts(g):
    n10 = sum(g[k] >= 10 for k in ("pts", "reb", "ast", "stl", "blk"))
    return g["pts"] + .5 * g["tpm"] + 1.25 * g["reb"] + 1.5 * g["ast"] + 2 * g["stl"] + 2 * g["blk"] - .5 * g["to"] + 1.5 * (n10 >= 2) + 3 * (n10 >= 3)

# game logs: espn id -> [(date, min, dk, starter)]
logs = {}
for f in glob.glob(os.path.join(BOX, "*.json")):
    d = json.load(open(f))
    for pid, g in (d.get("p") or {}).items():
        if not g.get("min"): continue
        logs.setdefault(pid, []).append((d["date"], g["min"], dkpts(g), bool(g.get("st"))))
for v in logs.values(): v.sort()

files = sorted(glob.glob(os.path.join(DK, "2026-1*_1*.csv")))
FIT = [os.path.basename(f)[:-4] for f in files[:14]]
rows = []
for f in files:
    sk = os.path.basename(f)[:-4]; day = sk[:10]; cut = day + "T12:00Z"
    for r in csv.DictReader(open(f)):
        if r["status"] == "Out" or not r["fp_dk"] or float(r["fp_dk"]) < 5: continue
        G = [g for g in logs.get(r["espn"], []) if g[0] < cut]
        mins = [g[1] for g in G]; ppm = [g[2] / g[1] for g in G if g[1] >= 5]
        sd = lambda x: st.pstdev(x) if len(x) >= 2 else None
        mean = lambda x: st.mean(x) if x else None
        last3 = mean(mins[-3:]) if len(mins) >= 3 else None
        sal = int(r["salary"])
        x = dict(min_sd5=sd(mins[-5:]), min_mean5=mean(mins[-5:]), min_sd10=sd(mins[-10:]), min_mean10=mean(mins[-10:]),
                 min_trend=(st.mean(mins[-3:]) - st.mean(mins[-10:-3])) if len(mins) >= 5 else None,
                 starter_share=(sum(g[3] for g in G) / len(G)) if G else None, gp=len(G),
                 role_change=(1.0 if abs(last3 - st.mean(mins)) >= 6 else 0.0) if last3 is not None else None,
                 abs_spread=abs(float(r["spread"])) if r["spread"] else None, total=float(r["ou"]) if r["ou"] else None,
                 questionable=1.0 if r["status"] in ("Q", "Questionable") else 0.0,
                 tier=0 if sal < 5000 else (1 if sal < 7000 else 2), proj=float(r["fp_dk"]), ppm_sd10=sd(ppm[-10:]))
        e = float(r["actual_dk"] or 0) - float(r["fp_dk"])
        rows.append(dict(slate=sk, fit=sk in FIT, x=x, e=e, m=float(r["min"] or 0) - float(r["min_proj"] or 0),
                         miss_dk=float(r["miss_dk"]), proj=float(r["fp_dk"]), minp=float(r["min_proj"] or 0)))
SL = [os.path.basename(f)[:-4] for f in files]; LATE = [s for s in SL if s not in FIT]
FEATS = ["min_sd5", "min_mean5", "min_sd10", "min_mean10", "min_trend", "starter_share", "gp", "role_change",
         "abs_spread", "total", "questionable", "tier", "proj", "ppm_sd10"]
out = []
def P(*a): s = " ".join(str(x) for x in a); print(s); out.append(s)
def mse(vals):  # mean +- SE over slates, k positive
    v = [x for x in vals if x is not None]
    if not v: return "n/a"
    m = st.mean(v); se = st.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
    return f"{m:+.2f} ± {se:.2f} ({sum(x > 0 for x in v)} of {len(v)})"
def mse_num(vals):
    v = [x for x in vals if x is not None]
    if not v: return float("nan"), float("nan"), 0, 0
    m = st.mean(v); se = st.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
    return m, se, sum(x > 0 for x in v), len(v)

P(f"rows {len(rows)} on {len(SL)} slate files; fit {len(FIT)} ({sum(r['fit'] for r in rows)} rows), last 6 {len(LATE)} ({sum(not r['fit'] for r in rows)} rows)")
P(f"overall bias mean {st.mean(r['e'] for r in rows):+.2f}; fit {st.mean(r['e'] for r in rows if r['fit']):+.2f}; last6 {st.mean(r['e'] for r in rows if not r['fit']):+.2f}")

# ---------- A ----------
P("\n== A. descriptive by bin: bias e / volatility v / minutes miss m, per-slate means, mean ± SE over slates (k positive) ==")
def bins_for(f):
    if f in ("role_change", "questionable"): return ("lvl", [0.0, 1.0])
    if f == "tier": return ("lvl", [0, 1, 2])
    vals = sorted(r["x"][f] for r in rows if r["fit"] and r["x"][f] is not None)
    return ("q", [vals[int(len(vals) * q / 5)] for q in range(1, 5)])
def bin_of(f, val, spec):
    if val is None: return "missing"
    kind, c = spec
    if kind == "lvl": return str(val)
    return "Q" + str(1 + sum(val >= t for t in c))
A = {}
for f in FEATS:
    spec = bins_for(f); groups = {}
    for r in rows: groups.setdefault(bin_of(f, r["x"][f], spec), []).append(r)
    fitbias = {b: st.mean(r["e"] for r in g if r["fit"]) if any(r["fit"] for r in g) else 0 for b, g in groups.items()}
    P(f"-- {f}  cuts {[round(c,2) for c in spec[1]] if spec[0]=='q' else spec[1]}")
    A[f] = {}
    for b in sorted(groups):
        g = groups[b]
        def per(sub, key):
            res = []
            for s in sub:
                rs = [r for r in g if r["slate"] == s]
                if len(rs) < 3: res.append(None); continue
                if key == "v": res.append(st.mean(abs(r["e"] - fitbias[b]) for r in rs))
                else: res.append(st.mean(r[key] for r in rs))
            return res
        A[f][b] = {w: {k: per(S, k) for k in ("e", "v", "m")} for w, S in (("fit", FIT), ("late", LATE))}
        P(f"   {b:8s} n={len(g):4d} | fit: e {mse(A[f][b]['fit']['e'])}  v {mse(A[f][b]['fit']['v'])}  m {mse(A[f][b]['fit']['m'])} | last6: e {mse(A[f][b]['late']['e'])}  v {mse(A[f][b]['late']['v'])}  m {mse(A[f][b]['late']['m'])}")
# fragile signal check: top vs bottom bin bias difference, per slate
P("\n-- A fragile check: top bin minus bottom bin bias (per slate), fit and last 6")
for f in FEATS:
    spec = bins_for(f)
    present = sorted({bin_of(f, r["x"][f], spec) for r in rows} - {"missing"})
    lo, hi = present[0], present[-1]   # lowest and highest bin present (ties in a discrete feature collapse quintiles)
    def diffs(S):
        d = []
        for s in S:
            a = [r["e"] for r in rows if r["slate"] == s and bin_of(f, r["x"][f], spec) == hi]
            b = [r["e"] for r in rows if r["slate"] == s and bin_of(f, r["x"][f], spec) == lo]
            d.append(st.mean(a) - st.mean(b) if len(a) >= 3 and len(b) >= 3 else None)
        return d
    df, dl = diffs(FIT), diffs(LATE)
    m, se, k, n = mse_num(df)
    ml = st.mean([x for x in dl if x is not None]) if any(x is not None for x in dl) else float("nan")
    ok = (abs(m) > 2 * se) and (math.copysign(1, m) == math.copysign(1, ml))
    P(f"   {f:14s} {hi}-{lo}: fit {m:+.2f} ± {se:.2f} ({k} of {n} +) | last6 {mse(dl)} | signal: {'YES' if ok else 'no'}")

# ---------- design matrix ----------
def design(train, test):
    med = {f: np.median([r["x"][f] for r in train if r["x"][f] is not None]) for f in FEATS}
    def mk(rs):
        cols = []
        for f in FEATS:
            cols.append([r["x"][f] if r["x"][f] is not None else med[f] for r in rs])
            if any(r["x"][f] is None for r in rows): cols.append([1.0 if r["x"][f] is None else 0.0 for r in rs])
        return np.array(cols, dtype=float).T
    Xtr, Xte = mk(train), mk(test)
    mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
    return np.c_[np.ones(len(Xtr)), Xtr], np.c_[np.ones(len(Xte)), Xte]
def ols(X, y, lam=1.0):  # tiny ridge for stability, intercept unpenalised
    I = np.eye(X.shape[1]); I[0, 0] = 0
    return np.linalg.solve(X.T @ X + lam * I, X.T @ y)

# ---------- C: bias model (LOSO + fit14->late6) ----------
P("\n== C. bias model: held-out MAE of fp_dk alone minus MAE of fp_dk + predicted bias (positive = correction helps) ==")
bhat = {}
def bias_run(train_s, test_s, key="e"):
    tr = [r for r in rows if r["slate"] in train_s]; te = [r for r in rows if r["slate"] in test_s]
    Xtr, Xte = design(tr, te); w = ols(Xtr, np.array([r[key] for r in tr]))
    return te, Xte @ w
loso_gain, loso_gain_m = [], []
for s in SL:
    te, p = bias_run([x for x in SL if x != s], [s])
    for r, b in zip(te, p): bhat[id(r)] = b
    loso_gain.append(st.mean(abs(r["e"]) for r in te) - st.mean(abs(r["e"] - b) for r, b in zip(te, p)))
    te, pm = bias_run([x for x in SL if x != s], [s], "m")
    loso_gain_m.append(st.mean(abs(r["m"]) for r in te) - st.mean(abs(r["m"] - b) for r, b in zip(te, pm)))
late_gain = []
te, p = bias_run(FIT, LATE)
for s in LATE:
    idx = [i for i, r in enumerate(te) if r["slate"] == s]
    late_gain.append(st.mean(abs(te[i]["e"]) for i in idx) - st.mean(abs(te[i]["e"] - p[i]) for i in idx))
late_gain_m = []
te, pm = bias_run(FIT, LATE, "m")
for s_ in LATE:
    idx = [i for i, r in enumerate(te) if r["slate"] == s_]
    late_gain_m.append(st.mean(abs(te[i]["m"]) for i in idx) - st.mean(abs(te[i]["m"] - pm[i]) for i in idx))
mC = mse_num(loso_gain); P(f"   points, LOSO 20: {mse(loso_gain)}  2xSE {2*mC[1]:.2f}")
P(f"   points, fit 14 -> last 6: {mse(late_gain)}")
P(f"   minutes, LOSO 20: {mse(loso_gain_m)}  2xSE {2*mse_num(loso_gain_m)[1]:.2f}")
P(f"   minutes, fit 14 -> last 6: {mse(late_gain_m)}")
P("   context (not pre-registered): the A signals with players who didn't play removed")
for lab, cond in (("gp <= 3", lambda r: r["x"]["gp"] <= 3), ("gp = 4", lambda r: r["x"]["gp"] == 4), ("gp >= 5", lambda r: r["x"]["gp"] >= 5), ("Q", lambda r: r["x"]["questionable"] == 1.0), ("not Q", lambda r: r["x"]["questionable"] == 0.0)):
    g = [r for r in rows if cond(r)]; dnp = sum(1 for r in g if r["proj"] + r["e"] == 0 and r["m"] + r["minp"] == 0)
    played = [r for r in g if not (r["m"] + r["minp"] == 0)]
    P(f"     {lab:8s} n={len(g)} DNP {dnp} ({dnp/len(g):.0%}); bias all {st.mean(r['e'] for r in g):+.2f}, played only {st.mean(r['e'] for r in played):+.2f}")
w_all = ols(*[design(rows, rows)[0]], np.array([r["e"] for r in rows]))
names = []
for f in FEATS:
    names.append(f)
    if any(r["x"][f] is None for r in rows): names.append(f + "_missing")
P("   all-slate standardized coefficients (bias, points):", ", ".join(f"{n} {c:+.2f}" for n, c in sorted(zip(names, w_all[1:]), key=lambda t: -abs(t[1]))[:8]))

# ---------- B: volatility model ----------
P("\n== B. volatility model: held-out Gaussian log-likelihood per player, per-player sigma minus comparator (positive = per-player better) ==")
for r in rows: r["res"] = r["e"] - bhat[id(r)]
def ll(r, sig): return -0.5 * math.log(2 * math.pi * sig * sig) - r["res"] ** 2 / (2 * sig * sig)
def sig_tier(train):
    return {t: math.sqrt(math.pi / 2) * st.mean(abs(r["res"]) for r in train if r["x"]["tier"] == t) for t in (0, 1, 2)}
def vol_run(train_s, test_s):
    tr = [r for r in rows if r["slate"] in train_s]; te = [r for r in rows if r["slate"] in test_s]
    Xtr, Xte = design(tr, te); w = ols(Xtr, np.array([abs(r["res"]) for r in tr]))
    sh = np.maximum(1.0, math.sqrt(math.pi / 2) * (Xte @ w)); return te, sh, sig_tier(tr)
gT, gS, covP, covT, covS = [], [], [], [], []
sig_hat = {}
for s in SL:
    te, sh, stier = vol_run([x for x in SL if x != s], [s])
    lp = [ll(r, sg) for r, sg in zip(te, sh)]; lt = [ll(r, stier[r["x"]["tier"]]) for r in te]
    ls = [ll(r, max(1.0, ZSD * r["miss_dk"])) for r in te]
    gT.append(st.mean(lp) - st.mean(lt)); gS.append(st.mean(lp) - st.mean(ls))
    for r, sg in zip(te, sh): sig_hat[id(r)] = sg
    z = 1.2816
    covP.append(st.mean(1.0 if abs(r["res"]) <= z * sg else 0.0 for r, sg in zip(te, sh)))
    covT.append(st.mean(1.0 if abs(r["res"]) <= z * stier[r["x"]["tier"]] else 0.0 for r in te))
    covS.append(st.mean(1.0 if (r["proj"] + Z10 * r["miss_dk"] <= r["proj"] + r["e"] <= r["proj"] + Z90 * r["miss_dk"]) else 0.0 for r in te))
mB = mse_num(gT)
P(f"   vs per-tier sigma, LOSO 20: {mse(gT)}  2xSE {2*mB[1]:.3f}")
P(f"   vs sim sigma (1.25 x miss_dk), LOSO 20: {mse(gS)}")
te, sh, stier = vol_run(FIT, LATE); late_T = []
for s in LATE:
    idx = [i for i, r in enumerate(te) if r["slate"] == s]
    late_T.append(st.mean(ll(te[i], sh[i]) for i in idx) - st.mean(ll(te[i], stier[te[i]["x"]["tier"]]) for i in idx))
P(f"   vs per-tier sigma, fit 14 -> last 6: {mse(late_T)}")
P(f"   10/90 coverage (target 0.80): per-player {st.mean(covP):.3f}, per-tier {st.mean(covT):.3f}, sim band {st.mean(covS):.3f}")
w_v = ols(*[design(rows, rows)[0]], np.array([abs(r["res"]) for r in rows]))
P("   all-slate standardized coefficients (volatility):", ", ".join(f"{n} {c:+.2f}" for n, c in sorted(zip(names, w_v[1:]), key=lambda t: -abs(t[1]))[:8]))

# ---------- D: sim calibration by bucket ----------
P("\n== D. sim calibration by bucket: realised SD of e vs sim stated spread (1.25 x miss_dk); sim 10/90 band coverage ==")
def bucket_report(label, keyf, nb=5):
    vals = sorted(keyf(r) for r in rows); cuts = [vals[int(len(vals) * q / nb)] for q in range(1, nb)]
    for b in range(nb):
        g = [r for r in rows if sum(keyf(r) >= c for c in cuts) == b]
        rat = []
        for s in SL:
            rs = [r for r in g if r["slate"] == s]
            if len(rs) >= 3:
                rat.append(st.pstdev([r["e"] for r in rs]) / st.mean(ZSD * r["miss_dk"] for r in rs))
        boot = []
        rng = np.random.default_rng(7)
        for _ in range(500):
            pick = rng.choice(SL, len(SL)); gg = [r for s in pick for r in g if r["slate"] == s]
            if len(gg) > 5: boot.append(st.pstdev([r["e"] for r in gg]) - st.mean(ZSD * r["miss_dk"] for r in gg))
        realised = st.pstdev([r["e"] for r in g]); stated = st.mean(ZSD * r["miss_dk"] for r in g)
        cov = st.mean(1.0 if (Z10 * r["miss_dk"] <= r["e"] <= Z90 * r["miss_dk"]) else 0.0 for r in g)
        bse = st.pstdev(boot) if boot else float("nan")
        flag = "TOO TIGHT" if realised - stated > 2 * bse else ("too wide" if stated - realised > 2 * bse else "")
        P(f"   {label} B{b+1} n={len(g):4d}: realised SD {realised:5.2f} vs stated {stated:5.2f} (ratio {realised/stated:.2f}; per-slate ratio {mse([x-1 for x in rat])} vs 1), 10/90 coverage {cov:.3f} {flag}")
bucket_report("held-out sigma-hat", lambda r: sig_hat[id(r)])
bucket_report("sim miss_dk/fp", lambda r: r["miss_dk"] / r["proj"])
for lab, cond in (("bench (min_proj<20)", lambda r: r["minp"] < 20), ("not bench", lambda r: r["minp"] >= 20)):
    g = [r for r in rows if cond(r)]
    realised = st.pstdev([r["e"] for r in g]); stated = st.mean(ZSD * r["miss_dk"] for r in g)
    cov = st.mean(1.0 if (Z10 * r["miss_dk"] <= r["e"] <= Z90 * r["miss_dk"]) else 0.0 for r in g)
    P(f"   {lab} n={len(g)}: realised SD {realised:.2f} vs stated {stated:.2f} (ratio {realised/stated:.2f}), 10/90 coverage {cov:.3f}")
allr = st.pstdev([r["e"] for r in rows]) / st.mean(ZSD * r["miss_dk"] for r in rows)
P(f"   overall ratio {allr:.2f}")
open(os.path.join(HERE, "ps.out"), "w").write("\n".join(out) + "\n")
json.dump([{k: v for k, v in r.items() if k not in ("x",)} | {"x": r["x"], "bhat": bhat[id(r)], "sig_hat": sig_hat[id(r)]} for r in rows],
          open(os.path.join(HERE, "ps_rows.json"), "w"))
