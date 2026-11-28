"""Ownership disagreement test, part 3: could the pre-lock signals that predict d (real - ours) improve OUR OWNERSHIP?
LOSO: fit d ~ signals by least squares on the other slates (every player with a 100+ entry real ownership and all
signals present), predict ours + fitted d on the held-out slate (floored at 0), score the chalk band (max(real, ours,
new) >= 15) MAE and the all-player MAE against ours. Reuses od2.py's signal build."""
import math, statistics as S, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "od2.py")).read()
ns = {"__file__": os.path.join(HERE, "od2.py")}
exec(src.split("SIG = [")[0], ns)
rows = ns["rows"]; SL = ns["SL"]; ms = ns["ms"]
import numpy as np
SETS = [["pval"], ["last1"], ["checks"], ["min_gap"], ["pval", "last1", "checks", "min_gap"], ["pval", "last1", "checks", "min_gap", "dk_avg"]]
R = [r for r in rows if "sg" in r]
for sigs in SETS:
    use = [r for r in R if all(r["sg"].get(k) is not None for k in sigs)]
    gc, ga = [], []
    for h in SL:
        tr = [r for r in use if r["slate"] != h]; te = [r for r in use if r["slate"] == h]
        if len(te) < 5: continue
        X = np.array([[1.0] + [r["sg"][k] for k in sigs] for r in tr]); y = np.array([r["d"] for r in tr])
        b = np.linalg.lstsq(X, y, rcond=None)[0]
        new = [max(0.0, r["ours"] + float(np.dot(b, [1.0] + [r["sg"][k] for k in sigs]))) for r in te]
        ch = [(r, n) for r, n in zip(te, new) if max(r["real"], r["ours"], n) >= 15]
        if ch: gc.append(S.mean(abs(r["real"] - r["ours"]) for r, n in ch) - S.mean(abs(r["real"] - n) for r, n in ch))
        ga.append(S.mean(abs(r["real"] - r["ours"]) for r in te) - S.mean(abs(r["real"] - n) for r, n in zip(te, new)))
    print("%-45s rows %4d | chalk-band MAE gain %s | all-player MAE gain %s" % ("+".join(sigs), len(use), ms(gc), ms(ga)))
