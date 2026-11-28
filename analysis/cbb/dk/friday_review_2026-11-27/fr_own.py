import sys, os, math, statistics as S, glob
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E, dk_chalk_miss as C, dk_own_review as R
MIR = "/home/user/br-adp-mirror"
bigs = R.big_game_flags(MIR)
recs = {}
for f in glob.glob(os.path.join(C.DK, "????-??-??_*.csv")):
    rec = E.read(f)
    if rec:
        for r in rec:
            if E.num(r.get("own_raw")) is not None: r["own"] = r["own_raw"]   # raw: features and base on the uncorrected
        recs[str(rec[0]["draft_group"])] = rec
feats = {g: C.slate_features(rec, bigs.get(g) or set()) for g, rec in recs.items()}
rows = []
for r in E.own_grade_rows():
    g = str(r["draft_group"]); x = (feats.get(g) or {}).get(r["dk_id"])
    if x and all(x[k] is not None for k in C.FEATS):
        rows.append(dict(x, g=g, date=r["date"], cid=r["contest_id"], name=r["name"], p=r["raw"], a=r["a"], n=r["n"], live=r["p"]))
print("rows", len(rows), "slates", len({r['g'] for r in rows}))
def show(lab, res):
    s = C.summary(res); print("%-28s raw MAE %.2f -> %.2f gain %+.2f (2xSE %.2f) better %d/%d off10 %.1f%%->%.1f%% %s" % (lab, s["ours"], s["cand"], s["gain"], 2*s["se"], s["better"], s["n"], 100*s["off0"], 100*s["off1"], "PASS" if s["pass"] else ""))
for terms in (["chalk_team", "big"], ["chalk_team"], ["big"], ["chalk_team", "q"], ["chalk_team", "ou"], ["q"], ["own_rank"], ["chalk_team","big","q"]):
    show("+".join(terms), C.run(rows, terms, "B"))
# fixed shipped coefficients (no renorm) held on all slates
fixed = lambda r: max(0.0, r["p"] + 0.53 - 1.27 * r["chalk_team"] + 8.44 * r["big"]) if r["p"] >= 10 else r["p"]
res = []
for g in sorted({r["g"] for r in rows}):
    te = [r for r in rows if r["g"] == g]; m0, o0 = C.grade(te, lambda r: r["p"]); m1, o1 = C.grade(te, fixed)
    if m0 is not None: res.append((g, m0, m1, o0, o1))
show("shipped coefs (no renorm)", res)
show("  since 157026 only", [x for x in res if x[0] in ("157026","157293","157295","157380","157382")])
# refit on all slates
tr = [r for r in rows if r["p"] >= 10]
for terms in (["chalk_team", "big"], ["chalk_team", "big", "q"]):
    c = C.ols([[r[t] for t in terms] for r in tr], [r["a"] - r["p"] for r in tr]); print("refit all", terms, [round(x, 2) for x in c])
    tr2 = [r for r in tr if r["g"] in ("157026","157293","157295","157380","157382")]
    c = C.ols([[r[t] for t in terms] for r in tr2], [r["a"] - r["p"] for r in tr2]); print("  fit since 157026 only", [round(x, 2) for x in c], len(tr2))
# big-game flag counts by slate and mean signed miss
for g in sorted({r["g"] for r in rows}):
    b = [r for r in rows if r["g"] == g and r["big"] and r["p"] >= 10]
    if b: print("big", g, len(b), "mean a-raw %+.1f" % S.mean(r["a"] - r["p"] for r in b))
# 11-26 main misses
print("\n11-26 main (157382) chalk misses: name, raw, live, actual(mean over contests), features")
rec = {r["dk_id"]: r for r in recs["157382"]}
from collections import defaultdict
agg = defaultdict(list)
for r in rows:
    if r["g"] == "157382": agg[r["name"]].append(r)
top = sorted(agg.items(), key=lambda kv: -(S.mean(x["a"] for x in kv[1]) - S.mean(x["live"] for x in kv[1])))[:12]
for nm, rs in top:
    x = rs[0]
    print("%-22s raw %5.1f live %5.1f act %5.1f | sal %.1f val_rank %d chalk_team %d chalk_game %d own_rank %d big %d q %d ou %s spread %s" % (
        nm, S.mean(r["p"] for r in rs), S.mean(r["live"] for r in rs), S.mean(r["a"] for r in rs), x["salary"], x["val_rank"], x["chalk_team"], x["chalk_game"], x["own_rank"], x["big"], x["q"], x["ou"], x["spread"]))
qq = [r for r in rows if r["q"] and r["p"] >= 10]
print("\nQ at lock, raw 10%+: player-contests", len(qq), "players", len({(r['g'], r['name']) for r in qq}), "slates", len({r['g'] for r in qq}), "mean a - raw %+.1f" % S.mean(r["a"] - r["p"] for r in qq))
for g in sorted({r['g'] for r in qq}): print("  ", g, sorted({r['name'] for r in qq if r['g'] == g}), "%+.1f" % S.mean(r["a"] - r["p"] for r in qq if r["g"] == g))
