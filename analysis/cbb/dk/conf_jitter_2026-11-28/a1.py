"""A1: greens vs matched non-greens on the absolute and relative miss of our lock projection (pre-registered in
conf_jitter_2026-11-28.md). Rows: analysis/cbb/dk/<slate>.csv; greens: bank_recipe_2026-11-28/greens_by_slate.json;
rotation filter from the lock file (battle-royale-research data/dk/cbb/<slate>_proj.json): min_avg >= 15, gp >= 3, not Out.
  python3 a1.py --brr ../../../../../battle-royale-research > a1.out"""
import argparse, csv, json, math, os, statistics as St
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); DK = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument("--brr", required=True); a = ap.parse_args()
G = json.load(open(os.path.join(DK, "bank_recipe_2026-11-28", "greens_by_slate.json")))
num = lambda x: float(x) if x not in (None, "") else None
per = []
for tag, gl in sorted(G.items()):
    P = json.load(open(os.path.join(a.brr, "data", "dk", "cbb", tag + "_proj.json"))); gs = set(gl); rows = []
    for r in csv.DictReader(open(os.path.join(DK, tag + ".csv"))):
        p, act, fp = P.get(r["dk_id"]), num(r["actual_dk"]), num(r["fp_dk"])
        if not p or act is None or fp is None or p.get("status") == "Out" or (p.get("min_avg") or 0) < 15 or (p.get("gp") or 0) < 3:
            continue
        s = p["salary"]
        rows.append(dict(g=r["dk_id"] in gs, sb=0 if s < 5000 else 1 if s < 7000 else 2, pb=0 if fp < 10 else 1 if fp < 25 else 2,
                         ab=abs(act - fp), rel=abs(act - fp) / fp if fp >= 5 else None))
    d = {"ab": [], "rel": []}; w = {"ab": [], "rel": []}
    for sb in range(3):
        for pb in range(3):
            g = [r for r in rows if r["g"] and r["sb"] == sb and r["pb"] == pb]; n = [r for r in rows if not r["g"] and r["sb"] == sb and r["pb"] == pb]
            if g and n:
                d["ab"].append(St.mean(r["ab"] for r in g) - St.mean(r["ab"] for r in n)); w["ab"].append(len(g))
                gr = [r["rel"] for r in g if r["rel"] is not None]; nr = [r["rel"] for r in n if r["rel"] is not None]
                if gr and nr:
                    d["rel"].append(St.mean(gr) - St.mean(nr)); w["rel"].append(len(gr))
    if not w["ab"]:
        print("%-18s no matched greens" % tag); continue
    x = {k: float(np.average(d[k], weights=w[k])) for k in d if w[k]}
    per.append((tag, x, sum(w["ab"])))
    print("%-18s matched greens %3d | |miss| %+6.2f | |miss|/proj %+6.3f" % (tag, sum(w["ab"]), x["ab"], x.get("rel", float("nan"))))
def ms(v): return "%+.3f ± %.3f over %d slates, negative (greens miss less) on %d" % (St.mean(v), St.stdev(v) / math.sqrt(len(v)), len(v), sum(1 for z in v if z < 0))
for lab, t in (("all 18 slates", lambda s: True), ("fit slates (to 11-23)", lambda s: s[:10] <= "2026-11-23"), ("after the fit (11-24 on)", lambda s: s[:10] >= "2026-11-24")):
    R = [x for s, x, _ in per if t(s)]
    print("\n%s\n  |actual - proj|      green - matched non-green: %s\n  |actual - proj|/proj green - matched non-green: %s" % (lab, ms([x["ab"] for x in R]), ms([x["rel"] for x in R if "rel" in x])))
