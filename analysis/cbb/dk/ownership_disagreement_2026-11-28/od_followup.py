"""Ownership disagreement follow-up (2026-11-28, analysis only, HELD).

(a) Finer tiers: salary < $4k, 4-5, 5-6, 6-7, 7-8, 8k+, and projection bands. Per tier, per slate: loved (d >= 10)
    and faded (d <= -10) players' mean actual - projection minus the within-10 players' (same slate, all tiers), and
    r(d, act - proj) inside the tier; mean +- SE over slates. "Field right" = loved beat / faded missed our projection.
(b) The operator's DIRECTIONAL candidate as a kept-pool re-ranking, held out by slate. Pre-lock, real ownership is
    unknown, so d is replaced by d_hat, the leave-one-slate-out least-squares prediction of d from the signals that
    predicted it (od3: pval, last1, checks, min_gap; missing -> 0), fitted on the OTHER slates only. Each kept lineup
    gets   score = sum over its cheap / rotation players (salary < CROSS) of d_hat      (don't fade the field's
                                                                                          likely-loved cheap players)
                 - sum over its $CROSS+ players of d_hat                                  (lean into our disagreements
                                                                                          on stars)
    and the candidate keeps the top half of the kept pool by score. Compared with all kept (today) on the same nights
    and contests (100+ entries): mean real finish percentile and mean payout per lineup ($, from the contest's
    table). An oracle with the real d (hindsight) is shown as the ceiling. CROSS is set from (a) before (b) is run.
"""
import json, os, sys, math, random, statistics as S, bisect, csv, glob
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "od2.py")).read()
ns = {"__file__": os.path.join(HERE, "od2.py")}
exec(src.split("SIG = [")[0], ns)
rows, SL, ms, E = ns["rows"], ns["SL"], ns["ms"], ns["E"]
import numpy as np
CROSS = 7000
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
A = [r for r in rows if max(r["ours"], r["real"]) >= 5]

# ---------- (a) tiers
P("## (a) Finer tiers: per slate, loved / faded act - proj minus the slate's within-10 mean; r(d, act - proj) in the tier")
within = {s: S.mean(r["res"] for r in A if r["slate"] == s and abs(r["d"]) < 10) for s in SL}
TIERS = [("salary < $4k", lambda r: r["sal"] < 4000), ("$4-5k", lambda r: 4000 <= r["sal"] < 5000), ("$5-6k", lambda r: 5000 <= r["sal"] < 6000),
         ("$6-7k", lambda r: 6000 <= r["sal"] < 7000), ("$7-8k", lambda r: 7000 <= r["sal"] < 8000), ("$8k+", lambda r: r["sal"] >= 8000),
         ("proj 10-15", lambda r: 10 <= r["fp"] < 15), ("proj 15-20", lambda r: 15 <= r["fp"] < 20), ("proj 20-25", lambda r: 20 <= r["fp"] < 25),
         ("proj 25-30", lambda r: 25 <= r["fp"] < 30), ("proj 30+", lambda r: r["fp"] >= 30)]
def corr(x, y): return ns["corr"](x, y)
for lab, f in TIERS:
    rs = [r for r in A if f(r)]
    lv = defaultdict(list); fd = defaultdict(list); rr = []
    for r in rs:
        if r["d"] >= 10: lv[r["slate"]].append(r["res"])
        elif r["d"] <= -10: fd[r["slate"]].append(r["res"])
    for s in SL:
        v = [r for r in rs if r["slate"] == s]
        rr.append(corr([x["d"] for x in v], [x["res"] for x in v]))
    # "field right" score: loved - within (positive = field right) and within - faded (positive = field right)
    lvd = [S.mean(v) - within[s] for s, v in lv.items()]; fdd = [within[s] - S.mean(v) for s, v in fd.items()]
    both = [x for x in lvd] + [x for x in fdd]
    P("%-13s n=%3d | loved (%2d) act-proj vs within %s | faded (%2d) within - faded %s | field-right pooled %s | r %s" % (
        lab, len(rs), sum(len(v) for v in lv.values()), ms(lvd), sum(len(v) for v in fd.values()), ms(fdd), ms(both), ms(rr)))

# ---------- (b) candidate on the builds
P("\n## (b) The candidate: re-rank the kept pool by score (cheap / rotation: + d_hat; $%dk+: - d_hat), keep the top half; held out by slate" % (CROSS // 1000))
SIGS = ["pval", "last1", "checks", "min_gap"]
R = [r for r in rows if "sg" in r]
dhat = {}
for h in SL:
    tr = [r for r in R if r["slate"] != h]
    X = np.array([[1.0] + [r["sg"].get(k) or 0.0 for k in SIGS] for r in tr]); y = np.array([r["d"] for r in tr])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    for r in R:
        if r["slate"] == h: dhat[(h, r["id"])] = float(np.dot(b, [1.0] + [r["sg"].get(k) or 0.0 for k in SIGS]))
realD = {(r["slate"], r["id"]): r["d"] for r in rows}
sal = {(r["slate"], r["id"]): r["sal"] for r in rows}
M = E.Mirror("/home/user/br-adp-mirror")
ev = defaultdict(set)
for r in csv.DictReader(open("/home/user/br_rankings/analysis/cbb/dk/eval.csv")): ev[r["draft_group"]].add((r["contest_id"], int(float(r["entries"]))))
res = []
for f in sorted(glob.glob("/home/user/br_rankings/analysis/cbb/dk/builds/*.json")):
    name = os.path.basename(f)[8:-5]; g = name.split("_")[1]
    if name not in SL: continue
    b = json.load(open(f)); pool = b["pool"]; kept = sorted(set(b.get("final") or []))
    if not kept: continue
    recf = "/home/user/br_rankings/analysis/cbb/dk/%s.csv" % name
    pts = {r["dk_id"]: E.num(r.get("actual_dk")) for r in E.read(recf)}
    salr = {r["dk_id"]: E.num(r.get("salary")) for r in E.read(recf)}
    def score(L, D):
        s_ = 0.0
        for i in L:
            k = (name, str(i)); v = D.get(k, 0.0)
            s_ += v if (salr.get(str(i)) or 0) < CROSS else -v
        return s_
    sc = {k: score(pool[k], dhat) for k in kept}; so = {k: score(pool[k], realD) for k in kept}
    top = sorted(kept, key=lambda k: -sc[k])[:len(kept) // 2]; topo = sorted(kept, key=lambda k: -so[k])[:len(kept) // 2]
    bot = sorted(kept, key=lambda k: sc[k])[:len(kept) // 2]
    per = {"all": [], "cand": [], "oracle": [], "bottom": []}; pay = {k: [] for k in per}
    for cid, n in ev[g]:
        if n < 100: continue
        sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(sf): continue
        entries, players = E.standings(sf)
        _, slate, _ = E.slate_for(M, cid)
        contest = next((c for c in (slate or {}).get("contests", []) if str(c["id"]) == cid), None) if slate else None
        if not contest: continue
        table = E.pay_table(contest.get("payouts")); fdesc = sorted((e["points"] for e in entries), reverse=True); N = len(fdesc)
        def pp(k):
            v = sum(pts.get(str(i)) or 0 for i in pool[k]); pl = E.placed(v, fdesc); return 100 * (N - (pl - 1)) / N, table.get(pl, 0)
        Pk = {k: pp(k) for k in kept}
        for lab, ks in (("all", kept), ("cand", top), ("oracle", topo), ("bottom", bot)):
            per[lab].append(S.mean(Pk[k][0] for k in ks)); pay[lab].append(S.mean(Pk[k][1] for k in ks))
    if not per["all"]: continue
    res.append({"slate": name, **{"pct_" + k: S.mean(v) for k, v in per.items()}, **{"pay_" + k: S.mean(v) for k, v in pay.items()}})
for r in res:
    P("%s | finish pct all %.1f, candidate %.1f, oracle %.1f, bottom half %.1f | $ per lineup per contest all %.2f, candidate %.2f, oracle %.2f" % (
        r["slate"], r["pct_all"], r["pct_cand"], r["pct_oracle"], r["pct_bottom"], r["pay_all"], r["pay_cand"], r["pay_oracle"]))
for lab in ("cand", "oracle", "bottom"):
    P("%-7s - all kept: finish pct %s | $ per lineup %s" % (lab, ms([r["pct_" + lab] - r["pct_all"] for r in res]), ms([r["pay_" + lab] - r["pay_all"] for r in res])))
P("candidate top half - bottom half (the score's spread): finish pct %s" % ms([r["pct_cand"] - r["pct_bottom"] for r in res]))
print("\n".join(OUT))
