"""QMIN study, the banded proxy lenses (dk_eval.py projaudit) for (b) against today: the held-out minutes from
out.json applied to copies of the slate files, points per minute held.

  python3 scripts/dk_qmin_lenses.py WORKDIR REPO BRR [fixed]   (fixed: band membership by today's projection)
"""
import sys, os, json, glob, csv, shutil, io, contextlib
W = sys.argv[1]; REPO = sys.argv[2]; BRR = sys.argv[3]; FIXED = len(sys.argv) > 4
sys.path.insert(0, os.path.join(REPO, "scripts"))
import dk_qmin_study as q
cn = q.load_nightly(BRR)
games = [g for g in (q.parse(f) for f in sorted(glob.glob(os.path.join(W, "data", "sum", "*.json")))) if g]
pp_box = q.all_box_games(games)
o = json.load(open(os.path.join(W, "out.json")))
params = {r["slate"]: r["params"] for r in o["held"]["b"]["per_slate"]}
DKD = os.path.join(REPO, "analysis", "cbb", "dk")
tmp = os.path.join(W, "dk_b"); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
for f in glob.glob(os.path.join(DKD, "*.csv")):
    shutil.copy(f, tmp)
dump = {}
for name, proj, rc in q.slate_rows(BRR):
    ma, _ = q.project_slate(cn, proj, "a", {}, pp_box, {}, {})
    mb, _ = q.project_slate(cn, proj, "b", {}, pp_box, {}, params[name])
    dump[name] = {k: [mb.get(k), ma.get(k)] for k in ma}
    p = os.path.join(tmp, name + ".csv")
    rows = list(csv.DictReader(open(p))); fn = list(rows[0].keys())
    for r in rows:
        k = r["dk_id"]
        if k in ma and ma[k] and mb.get(k) is not None and r.get("fp_dk") not in ("", None):
            f = mb[k] / ma[k]
            r["fp_band"] = r["fp_dk"]
            r["fp_dk"] = round(float(r["fp_dk"]) * f, 2)
            r["min_proj"] = round(mb[k], 1)
            if r.get("value") not in ("", None) and float(r["salary"] or 0):
                r["value"] = round(float(r["fp_dk"]) / (float(r["salary"]) / 1000), 2)
    if FIXED:
        fn = fn + ["fp_band"]
    else:
        for r in rows: r.pop("fp_band", None)
    w = csv.DictWriter(open(p, "w", newline=""), fieldnames=fn, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
json.dump(dump, open(os.path.join(W, "b_mins.json"), "w"))
import types
src = open(os.path.join(REPO, "scripts", "dk_eval.py")).read()
a_ = 'pband = lambda r: next((b for b, lo, hi in PROJ_BANDS if lo <= (num(r.get("fp_dk")) or 0) < hi), None)'
assert src.count(a_) == 1
src = src.replace(a_, 'pband = lambda r: next((b for b, lo, hi in PROJ_BANDS if lo <= (num(r.get("fp_band") or r.get("fp_dk")) or 0) < hi), None)')
a2 = 'inb = (lambda lo, hi: lambda r: lo <= (num(r.get("fp_dk")) or 0) < hi)(lo, hi)'
assert src.count(a2) == 1
src = src.replace(a2, 'inb = (lambda lo, hi: lambda r: lo <= (num(r.get("fp_band") or r.get("fp_dk")) or 0) < hi)(lo, hi)')
de = types.ModuleType("dk_eval"); de.__file__ = os.path.join(REPO, "scripts", "dk_eval.py")
exec(compile(src, de.__file__, "exec"), de.__dict__)
def run(d):
    de.DK = d; de.EVAL = os.path.join(d, "eval.csv"); de.PROJ_AUDIT = os.path.join(d, "proj_audit.csv")
    class A: pass
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        de.projaudit(A())
    return list(csv.DictReader(open(de.PROJ_AUDIT)))
orig = os.path.join(W, "dk_a"); shutil.rmtree(orig, ignore_errors=True); os.makedirs(orig)
for f in glob.glob(os.path.join(DKD, "*.csv")):
    shutil.copy(f, orig)
ra, rb = run(orig), run(tmp)
cols = [c for c in ra[0] if c.startswith("rot_") or c.startswith("stars_")]
print(cols)
import statistics as S, math
for c in cols:
    d = []
    for x, y in zip(ra, rb):
        try: d.append(float(y[c]) - float(x[c]))
        except (TypeError, ValueError): pass
    if d:
        se = S.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0
        print(f"{c:22} mean(b-a) {S.mean(d):+.3f}  se {se:.3f}  n {len(d)}  up {sum(x>0 for x in d)} down {sum(x<0 for x in d)}")
