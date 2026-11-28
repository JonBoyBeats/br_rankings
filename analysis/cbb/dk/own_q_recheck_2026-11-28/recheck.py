"""Batch item 4's gate (2026-11-28): the ownership Q term (team + big + Q, refit on raw) re-checked held out by slate on
raw (leave one slate out, the Friday review's bar: dk_chalk_miss.summary pass = better on 70%+ of slates, gain > 2 x SE,
off-by-10 not worse), on every graded slate and on the 7 most recent. Ships only if both pass."""
import sys, os, glob, statistics as S
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dk_eval as E, dk_chalk_miss as C, dk_own_review as R  # noqa: E402
MIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), "br-adp-mirror")
bigs = R.big_game_flags(MIR)
recs, dates = {}, {}
for f in glob.glob(os.path.join(C.DK, "????-??-??_*.csv")):
    rec = E.read(f)
    if rec:
        for r in rec:
            if E.num(r.get("own_raw")) is not None:
                r["own"] = r["own_raw"]
        recs[str(rec[0]["draft_group"])] = rec
        dates[str(rec[0]["draft_group"])] = rec[0]["date"]
feats = {g: C.slate_features(rec, bigs.get(g) or set()) for g, rec in recs.items()}
rows = []
for r in E.own_grade_rows():
    g = str(r["draft_group"]); x = (feats.get(g) or {}).get(r["dk_id"])
    if x and all(x[k] is not None for k in C.FEATS):
        rows.append(dict(x, g=g, date=r["date"], cid=r["contest_id"], name=r["name"], p=r["raw"], a=r["a"], n=r["n"], live=r["p"]))
slates = sorted({r["g"] for r in rows}, key=lambda g: (dates.get(g, ""), g))
last7 = set(slates[-7:])
print("rows", len(rows), "graded slates", len(slates), "; last 7:", ", ".join("%s_%s" % (dates[g], g) for g in slates[-7:]))
out = {}
for lab, terms in (("team+big (live form)", ["chalk_team", "big"]), ("team+big+Q (candidate)", ["chalk_team", "big", "q"])):
    res = C.run(rows, terms, "B")
    for win, keep in (("all", lambda x: True), ("last 7", lambda x: x[0] in last7)):
        s = C.summary([x for x in res if keep(x)])
        out[(lab, win)] = s
        print("%-24s %-6s raw MAE %.2f -> %.2f gain %+.2f (2xSE %.2f) better %d/%d off10 %.1f%%->%.1f%% %s" % (
            lab, win, s["ours"], s["cand"], s["gain"], 2 * s["se"], s["better"], s["n"], 100 * s["off0"], 100 * s["off1"], "PASS" if s["pass"] else "fails"))
# the candidate against the live form, paired per slate (held out), last 7
a = {x[0]: x[2] for x in C.run(rows, ["chalk_team", "big", "q"], "B")}
b = {x[0]: x[2] for x in C.run(rows, ["chalk_team", "big"], "B")}
d = [b[g] - a[g] for g in slates[-7:] if g in a and g in b]
import math
print("candidate vs team+big, last 7 (held out, chalk MAE): %+.2f ± %.2f, better %d/%d" % (S.mean(d), S.stdev(d) / math.sqrt(len(d)), sum(x > 0 for x in d), len(d)))
tr = [r for r in rows if r["p"] >= C.DEPLOY_OWN]
c = C.ols([[r[t] for t in ("chalk_team", "big", "q")] for r in tr], [r["a"] - r["p"] for r in tr])
print("refit on all slates (raw, players 10%%+): c0 %+.2f, team %+.2f, big %+.2f, q %+.2f" % tuple(c))
qq = [r for r in tr if r["q"]]
print("Q rows at 10%+:", len(qq), "player-contests,", len({(r["g"], r["name"]) for r in qq}), "players,", len({r["g"] for r in qq}), "slates")
ok = out[("team+big+Q (candidate)", "all")]["pass"] and out[("team+big+Q (candidate)", "last 7")]["pass"]
since = slates[slates.index("157026"):] if "157026" in slates else []
print("graded slates under the live ownership version (own-2026-11-24, from 157026):", len(since), "of 7 (settling)")
ok = ok and len(since) >= 7
print("VERDICT:", "PASSES (ship)" if ok else "FAILS (do not ship)")
