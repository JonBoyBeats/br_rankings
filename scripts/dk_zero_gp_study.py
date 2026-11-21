"""Zero-games players (2026-11-21, the coordinator's check before the 11-22 lock): a player with 0 games this season on a
team that has played 3+ gets last season's carried minutes in full (cbb_nightly.project: m = (played + MIN_FILL x mp) /
(gp + MIN_FILL) is mp at gp 0; a team game he sat counts for nothing), so 16-25 projected minutes for players who
haven't played. Analysis only.

The group: not Out, 0 games this season (the lock card's gp), his team's most games by any teammate 3+.
Variants (each replaces the Questionable factor for the group; everyone else as now):
  cur     our projection, Questionable x the gate's factor (as the page)
  zero_q  the group projected as if Questionable (x the gate's factor)
  zero_f  x the group's actual / projected on the OTHER slates (leave one slate out): the mean-correct factor
  zero_p  x his held-out chance to play (scripts/dk_sit.py's model fitted without the slate)

  accuracy --out DIR      points MAE / RMSE (the group, everyone), the A2 lenses; writes each night's factors for the banks
  score --dir DIR         the banks drawn by scripts/dk_zero_gp_study.js, on real results

  python3 scripts/dk_bank_noise_study.py extract --mirror ../br-adp-mirror --out DIR
  python3 scripts/dk_zero_gp_study.py accuracy --out DIR
  for n in ...; do node scripts/dk_zero_gp_study.js DIR/$n.json 2000 DIR/zf_$n.json DIR/zero_$n.json; done
  python3 scripts/dk_zero_gp_study.py score --dir DIR
"""
import argparse, json, math, os, statistics as S, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_minutes_steep_study as M            # noqa: E402  (the A2 lenses)
import dk_sit as K                            # noqa: E402  (the chance to play)
from dk_cheap_minutes_study import NIGHTS     # noqa: E402  (the nights with standings)
from dk_dnp_study import lock_players, QF, cur_p   # noqa: E402

num = K.num
VARIANTS = ["cur", "zero_q", "zero_f", "zero_p"]


def group(rows, P):
    """{id} of the slate's zero-games players (not Out, gp 0, team 3+ games), from the lock card."""
    tg = {}
    for r in rows:
        tg[r["team"]] = max(tg.get(r["team"], 0), (P.get(r["dk_id"]) or {}).get("gp") or 0)
    return {r["dk_id"] for r in rows if r.get("status") != "Out" and not ((P.get(r["dk_id"]) or {}).get("gp") or 0) and tg[r["team"]] >= 3}


def accuracy(a):
    sl = [(d, g, rows) for d, g, rows in K.graded()]
    names = ["%s_%s" % (d, g) for d, g, _ in sl]
    G, F, noq = {}, {}, {}
    for (d, g, rows), n in zip(sl, names):
        P, _ = lock_players(d, g)
        G[n] = group(rows, P)
        pl = [{"id": r["dk_id"], "team": r["team"], "status": r.get("status") or "", "min_proj": num(r.get("min_proj")), "min_avg": num(r.get("min_avg")),
               "gp": (P.get(r["dk_id"]) or {}).get("gp") or 0, "last5": (P.get(r["dk_id"]) or {}).get("last5") or [], "src": r.get("src")} for r in rows]
        F[n] = K.features(pl, d)
        for r in rows:
            noq[(n, r["dk_id"])] = num(r.get("fp_dk")) or 0           # the card's projection before the Q factor
    rowsby = {n: rows for (_, _, rows), n in zip(sl, names)}
    act = {(n, r["dk_id"]): num(r.get("actual_dk")) or 0 for n in names for r in rowsby[n]}
    gsz = sum(len(G[n]) for n in names)
    print("Slates with box scores: %d; zero-games players (not Out, 0 games, team 3+): %d player-slates; played %d. A thin sample." % (
        len(sl), gsz, sum(1 for n in names for i in G[n] if (num(next(r for r in rowsby[n] if r["dk_id"] == i).get("min")) or 0) > 0)))
    # held-out factors
    fac, ph = {}, {}
    for n in names:
        o = [(n2, i) for n2 in names if n2 != n for i in G[n2]]
        fac[n] = sum(act[k] for k in o) / sum(noq[k] for k in o) if o and sum(noq[k] for k in o) else QF
        tr = [(x, int((num(next(r for r in rowsby[m] if r["dk_id"] == i).get("min")) or 0) > 0)) for m in names if m != n for i, (x, _) in F[m].items()]
        w = K.fit([x for x, _ in tr], [y for _, y in tr]); mod = {"w": w}
        for i in G[n]:
            if i in F[n]:
                ph[(n, i)] = K.predict(mod, F[n][i][0])
    print("Held-out zero_f factors by slate: " + ", ".join("%s %.3f" % (n, fac[n]) for n in names) + "  (the gate's Q factor %.3f)" % QF)
    proj = {}
    for n in names:
        for r in rowsby[n]:
            if r.get("status") == "Out":
                continue
            k = (n, r["dk_id"]); base = noq[k] * cur_p(r)
            if r["dk_id"] in G[n]:
                proj[k] = {"cur": base, "zero_q": noq[k] * QF, "zero_f": noq[k] * fac[n], "zero_p": noq[k] * ph.get(k, 1.0)}
            else:
                proj[k] = {v: base for v in VARIANTS}
    for title, keep in (("the zero-games group", lambda n, r: r["dk_id"] in G[n]), ("every player not Out", lambda n, r: True)):
        print("\n== Points, %s ==" % title)
        for v in VARIANTS:
            e = [act[(n, r["dk_id"])] - proj[(n, r["dk_id"])][v] for n in names for r in rowsby[n] if r.get("status") != "Out" and keep(n, r)]
            better = sum(1 for n in names if v != "cur" and [1 for r in rowsby[n] if r.get("status") != "Out" and keep(n, r)] and
                         S.mean(abs(act[(n, r["dk_id"])] - proj[(n, r["dk_id"])][v]) for r in rowsby[n] if r.get("status") != "Out" and keep(n, r)) <
                         S.mean(abs(act[(n, r["dk_id"])] - proj[(n, r["dk_id"])]["cur"]) for r in rowsby[n] if r.get("status") != "Out" and keep(n, r)) - 1e-9)
            print("  %-7s n %4d  MAE %.3f  RMSE %.3f  bias %+.3f%s" % (v, len(e), S.mean(abs(x) for x in e), math.sqrt(S.mean(x * x for x in e)), S.mean(e),
                                                                     "" if v == "cur" else "   slates better (MAE): %d of %d" % (better, sum(1 for n in names if [1 for r in rowsby[n] if keep(n, r)]))))
    print("\n== A2 lenses, every slate (points MAE all players; |shape| top-2 ours-recent; Vegas slope; 2 sd salary gaps unexplained). Minutes untouched ==")
    for v in VARIANTS[1:]:
        cnt = {"pts": 0, "shape": 0, "gaps": 0}; sums = {"b": [], "a": []}
        for n in names:
            rows = rowsby[n]; pts = {k[1]: x for k, x in proj.items() if k[0] == n}
            M.steepen = lambda rows_, gg, _p=pts, _r=rows, _v=v: {r["dk_id"]: (num(r["min_proj"]), _p[r["dk_id"]]["cur" if gg == 0 else _v])
                                                                  for r in _r if r.get("status") != "Out" and num(r.get("min_proj"))}
            b, a_ = M.lenses(rows, 0.0), M.lenses(rows, 1.0)
            cnt["pts"] += a_["pts_mae"] < b["pts_mae"] - 1e-9
            cnt["shape"] += abs(a_["shape_top2_vs_recent"] or 0) > abs(b["shape_top2_vs_recent"] or 0) + 1e-9
            cnt["gaps"] += a_["unexplained"] - b["unexplained"]
            sums["b"].append(b); sums["a"].append(a_)
        m = lambda side, k: S.mean(x[k] for x in sums[side] if x[k] is not None)
        print("  %-7s points MAE %.3f -> %.3f (better on %d of %d); |shape| %.3f -> %.3f (larger on %d); Vegas slope %.3f -> %.3f; unexplained gaps %+d in all" % (
            v, m("b", "pts_mae"), m("a", "pts_mae"), cnt["pts"], len(names), S.mean(abs(x["shape_top2_vs_recent"] or 0) for x in sums["b"]),
            S.mean(abs(x["shape_top2_vs_recent"] or 0) for x in sums["a"]), cnt["shape"], m("b", "vegas_slope"), m("a", "vegas_slope"), cnt["gaps"]))
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        for key, date, g, cid in NIGHTS:
            n = "%s_%s" % (date, g)
            if n not in G:
                continue
            f = {"zero_q": {i: QF for i in G[n]}, "zero_f": {i: fac[n] for i in G[n]}, "zero_p": {i: ph.get((n, i), 1.0) for i in G[n]}}
            json.dump(f, open(os.path.join(a.out, "zf_%s.json" % key), "w"))
        print("\nfactors written to %s" % a.out)


def score(a):
    """The DNP study's scorer (real top-10% / cash lines, the real field's percentile) on these banks and variants: it
    reads DIR/<night>.json and DIR/dnp_<night>.json, so the banks are copied under that name into DIR/_score."""
    import shutil
    import dk_dnp_study as D
    D.VARIANTS[:] = VARIANTS
    tmp = os.path.join(a.dir, "_score")
    os.makedirs(tmp, exist_ok=True)
    for key, *_ in NIGHTS:
        for src, dst in (("%s.json" % key, "%s.json" % key), ("zero_%s.json" % key, "dnp_%s.json" % key)):
            if os.path.exists(os.path.join(a.dir, src)):
                shutil.copy(os.path.join(a.dir, src), os.path.join(tmp, dst))
    D.score(argparse.Namespace(dir=tmp))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("accuracy"); x.add_argument("--out")
    y = sub.add_parser("score"); y.add_argument("--dir", required=True)
    a = ap.parse_args()
    {"accuracy": accuracy, "score": score}[a.cmd](a)
