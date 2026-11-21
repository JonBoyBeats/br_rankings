"""Who sits? A chance-to-play for the players we project (2026-11-21, step B of the coordinator's follow-up to the
cheap-player study, scripts/dk_cheap_minutes_study.py: about 312 cheap DNPs at about 2.7 points each). Analysis only.

The model: a small logistic fit of played (real minutes > 0) on what we have before lock, fitted leave-one-slate-out so
every slate is scored by a model that never saw it:
  - log(1 + projected minutes) and depth (his rank on his team by projected minutes, players not Out)
  - season participation: his games played / his team's (the most any teammate has played), and the games missed (the
    team's less his, capped at 5), for every slate (gp, the mirror's slate file at lock)
  - the "missed k of n" tag: of his team's last 5 game dates (every teammate's last5 dates at lock), how many he
    missed, and whether he missed the last one; days since his last game (capped 21). The dates are on file from
    11-18 on: before that, these are 0 and a flag says unknown
  - Questionable; newcomer / thin sample (src not box, or under 3 games); teammates Out (projected 15+ minutes)
The current implied chance: 0 for Out, the gate's Questionable factor (gate.json) for Q, else 1.
The variant projection: chance x our projection (minutes if he plays x our rate), the Q discount replaced by it.

  python3 scripts/dk_dnp_study.py accuracy [--pdir DIR]   calibration, Brier, the Q factor, MAE / RMSE, A2 lenses;
                                                           with --pdir, writes each night's chances for the banks
  python3 scripts/dk_dnp_study.py score --dir DIR         the banks drawn by scripts/dk_dnp_study.js, on real results
"""
import argparse, csv, datetime as dt, glob, json, math, os, statistics as S, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_minutes_steep_study as M            # noqa: E402  (the A2 lenses)
from dk_cheap_minutes_study import NIGHTS, slates   # noqa: E402  (the graded slates; the nights with standings)

DK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "cbb", "dk")
MIRROR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "br-adp-mirror")
num = lambda v: float(v) if v not in ("", None) else None
QF = json.load(open(os.path.join(DK, "gate.json")))["questionable"]["factor"]
FEATS = ["const", "logmin", "depth", "part", "gmiss", "known", "miss5", "misslast", "days", "q", "thin", "touts"]
VARIANTS = ["cur", "dnp_cheap", "dnp_all"]


def lock_players(date, g):
    """The mirror's slate file just before lock (as scripts/dk_q_missed_study.py finds it)."""
    from nba_daily import Mirror, iso
    Mi = lock_players.M = getattr(lock_players, "M", None) or Mirror(MIRROR)
    day = iso(date + "T00:00:00Z")
    start = None
    for t, sha in reversed(Mi.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
        x = next((s for s in Mi.show(sha, "dk_cbb_morning.json").get("slates", []) if str(s["draft_group_id"]) == g), None)
        if x and start is None:
            start = iso(x["start"])
        if x and start and t < start:
            return x.get("players") or {}, date
    return {}, date


def features(rows):
    """[(row, x vector, played)] for every player not Out, his chance's inputs at lock (dk_sit.features: the one
    definition, shared with the nightly card's p_play since 2026-11-21)."""
    import dk_sit
    d, g = rows[0]["date"], rows[0]["draft_group"]
    P, _ = lock_players(d, g)
    players = [{"id": r["dk_id"], "team": r["team"], "status": r.get("status") or "", "min_proj": num(r.get("min_proj")), "min_avg": num(r.get("min_avg")),
                "gp": (P.get(r["dk_id"]) or {}).get("gp") or 0, "last5": (P.get(r["dk_id"]) or {}).get("last5") or [], "src": r.get("src")} for r in rows]
    F, by = dk_sit.features(players, d), {r["dk_id"]: r for r in rows}
    return [(by[i], x, 1 if (num(by[i].get("min")) or 0) > 0 else 0) for i, (x, _) in F.items()]


def fit(X, y, lam=1.0):
    """L2 logistic by Newton (the constant unpenalized)."""
    X, y = np.array(X), np.array(y, float)
    w = np.zeros(X.shape[1]); R = lam * np.eye(X.shape[1]); R[0, 0] = 0
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ w))
        H = X.T @ (X * (p * (1 - p))[:, None]) + R
        step = np.linalg.solve(H, X.T @ (y - p) - R @ w)
        w += step
        if np.abs(step).max() < 1e-8:
            break
    return w


def cur_p(r):
    return 0.0 if r.get("status") == "Out" else QF if r.get("status") == "Questionable" else 1.0


def accuracy(a):
    sl = slates()
    F = {n: features(rows) for n, rows in sl}
    print("Slates with box scores: %d (%s): a thin sample. The 'missed k of n' dates are on file for %d of them." % (
        len(sl), ", ".join(n for n, _ in sl), sum(1 for n in F if any(x[1][FEATS.index("known")] for x in F[n]))))
    # leave-one-slate-out chances
    ph = {}
    for n, _ in sl:
        tr = [x for m in F if m != n for x in F[m]]
        w = fit([x[1] for x in tr], [x[2] for x in tr])
        for r, xv, y in F[n]:
            ph[(n, r["dk_id"])] = float(1 / (1 + math.exp(-np.dot(w, xv))))
    wall = fit([x[1] for n in F for x in F[n]], [x[2] for n in F for x in F[n]])
    print("Coefficients, all slates (for reading only; the scores below are held out): " + ", ".join("%s %+.2f" % (f, c) for f, c in zip(FEATS, wall)))
    allx = [(n, r, y) for n in F for r, _, y in F[n]]
    groups = [("every player not Out", lambda r: True), ("cheap (under $5,000)", lambda r: num(r["salary"]) < 5000),
              ("in the draw's pool (projected 15+ minutes)", lambda r: (num(r.get("min_proj")) or 0) >= 15),
              ("cheap and in the pool", lambda r: num(r["salary"]) < 5000 and (num(r.get("min_proj")) or 0) >= 15)]
    for title, keep in groups:
        xs = [(n, r, y) for n, r, y in allx if keep(r)]
        if not xs:
            continue
        bm = S.mean((ph[(n, r["dk_id"])] - y) ** 2 for n, r, y in xs)
        bc = S.mean((cur_p(r) - y) ** 2 for n, r, y in xs)
        base = S.mean(y for _, _, y in xs)
        print("\n== %s: n %d, played %.1f%% ==" % (title, len(xs), 100 * base))
        print("  Brier: held-out model %.4f vs current (Q x%.3f, else 1) %.4f vs a flat %.3f %.4f" % (bm, QF, bc, base, S.mean((base - y) ** 2 for _, _, y in xs)))
        wins = sum(1 for m in F if [1 for n, r, y in xs if n == m] and
                   S.mean((ph[(n, r["dk_id"])] - y) ** 2 for n, r, y in xs if n == m) < S.mean((cur_p(r) - y) ** 2 for n, r, y in xs if n == m))
        print("  slates where the model's Brier beats the current: %d of %d" % (wins, len({n for n, _, _ in xs})))
        print("  calibration (held out):  bin        n   mean p   played")
        for lo, hi in ((0, .3), (.3, .5), (.5, .7), (.7, .8), (.8, .9), (.9, .95), (.95, 1.01)):
            b = [(ph[(n, r["dk_id"])], y) for n, r, y in xs if lo <= ph[(n, r["dk_id"])] < hi]
            if b:
                print("                         %.2f-%.2f %4d   %.3f    %.3f" % (lo, min(hi, 1), len(b), S.mean(p for p, _ in b), S.mean(y for _, y in b)))
    # the Q factor on this data
    q = [(n, r) for n, r, y in allx if r.get("status") == "Questionable"]
    if q:
        pl = [r for n, r in q if (num(r.get("min")) or 0) > 0]
        act, pr = sum(num(r.get("actual_dk")) or 0 for _, r in q), sum(num(r.get("fp_dk")) or 0 for _, r in q)
        print("\n== Questionable: %d player-nights over %d slates; played %d (%.0f%%); actual / projected over all of them %.3f (the gate's factor %.3f); "
              "when they played, actual / projected %.3f; the model's mean chance for them %.3f ==" % (
                  len(q), len({n for n, _ in q}), len(pl), 100 * len(pl) / len(q), act / pr if pr else 0, QF,
                  (sum(num(r.get("actual_dk")) or 0 for r in pl) / sum(num(r.get("fp_dk")) or 0 for r in pl)) if pl else 0, S.mean(ph[(n, r["dk_id"])] for n, r in q)))
    # projections: current (Q x factor) vs chance x our projection, cheap only and all
    print("\n== Points: current (our projection, Q x the factor) vs chance x our projection (the Q factor replaced), per slate ==")
    print("  MAE favours the median (a sure 0 or his full projection), RMSE the mean; the optimizer wants the mean, so both are shown")
    proj = {}
    for n, rows in sl:
        for r in rows:
            if r.get("status") == "Out":
                continue
            fp = num(r.get("fp_dk")) or 0; p = ph.get((n, r["dk_id"]), 1.0); cheap = num(r["salary"]) < 5000
            proj[(n, r["dk_id"])] = {"cur": fp * cur_p(r), "dnp_all": fp * p, "dnp_cheap": fp * p if cheap else fp * cur_p(r)}
    for title, keep in groups[:2]:
        print("  -- %s --" % title)
        tot = {v: [] for v in VARIANTS}
        for n, rows in sl:
            xs = [r for r in rows if r.get("status") != "Out" and keep(r)]
            act = [num(r.get("actual_dk")) or 0 for r in xs]
            line = []
            for v in VARIANTS:
                pr = [proj[(n, r["dk_id"])][v] for r in xs]
                e = [x - y for x, y in zip(act, pr)]; tot[v] += e
                line.append("%s MAE %.2f RMSE %.2f" % (v, S.mean(abs(x) for x in e), math.sqrt(S.mean(x * x for x in e))))
            print("    %-18s n %3d  %s" % (n, len(xs), " | ".join(line)))
        for v in VARIANTS:
            e = tot[v]
            wm = sum(1 for n, rows in sl if v != "cur" and S.mean(abs((num(r.get("actual_dk")) or 0) - proj[(n, r["dk_id"])][v]) for r in rows if r.get("status") != "Out" and keep(r))
                     < S.mean(abs((num(r.get("actual_dk")) or 0) - proj[(n, r["dk_id"])]["cur"]) for r in rows if r.get("status") != "Out" and keep(r)) - 1e-9)
            wr = sum(1 for n, rows in sl if v != "cur" and math.sqrt(S.mean(((num(r.get("actual_dk")) or 0) - proj[(n, r["dk_id"])][v]) ** 2 for r in rows if r.get("status") != "Out" and keep(r)))
                     < math.sqrt(S.mean(((num(r.get("actual_dk")) or 0) - proj[(n, r["dk_id"])]["cur"]) ** 2 for r in rows if r.get("status") != "Out" and keep(r))) - 1e-9)
            print("    pooled %-10s MAE %.3f  RMSE %.3f  bias (actual-proj) %+.3f%s" % (v, S.mean(abs(x) for x in e), math.sqrt(S.mean(x * x for x in e)), S.mean(e),
                                                                             "" if v == "cur" else "   slates better: MAE %d, RMSE %d of %d" % (wm, wr, len(sl))))
    # A2 lenses, the steep study's, with points: current vs the variant (minutes untouched)
    print("\n== A2 lenses, every slate (points MAE all players; |shape| top-2 ours-recent; Vegas slope; 2 sd salary gaps unexplained). Minutes untouched ==")
    for v in VARIANTS[1:]:
        cnt = {"pts": 0, "shape": 0, "gaps": 0}; sums = {"b": [], "a": []}
        for n, rows in sl:
            pts = {k[1]: x for k, x in proj.items() if k[0] == n}
            M.steepen = lambda rows_, gg, _p=pts, _r=rows, _v=v: {r["dk_id"]: (num(r["min_proj"]), _p[r["dk_id"]]["cur" if gg == 0 else _v])
                                                                  for r in _r if r.get("status") != "Out" and num(r.get("min_proj"))}
            b, a_ = M.lenses(rows, 0.0), M.lenses(rows, 1.0)
            cnt["pts"] += a_["pts_mae"] < b["pts_mae"] - 1e-9
            cnt["shape"] += abs(a_["shape_top2_vs_recent"] or 0) > abs(b["shape_top2_vs_recent"] or 0) + 1e-9
            cnt["gaps"] += a_["unexplained"] - b["unexplained"]
            sums["b"].append(b); sums["a"].append(a_)
        m = lambda side, k: S.mean(x[k] for x in sums[side] if x[k] is not None)
        print("  %-10s points MAE %.3f -> %.3f (better on %d of %d); |shape| %.3f -> %.3f (larger on %d); Vegas slope %.3f -> %.3f; unexplained gaps %+d in all" % (
            v, m("b", "pts_mae"), m("a", "pts_mae"), cnt["pts"], len(sl), S.mean(abs(x["shape_top2_vs_recent"] or 0) for x in sums["b"]),
            S.mean(abs(x["shape_top2_vs_recent"] or 0) for x in sums["a"]), cnt["shape"], m("b", "vegas_slope"), m("a", "vegas_slope"), cnt["gaps"]))
    # cheap DNPs the draw's pool would even see (the page leaves out players projected under 15 minutes)
    dn = [(n, r) for n, r, y in allx if not y and num(r["salary"]) < 5000]
    print("\nCheap DNPs: %d; projected 15+ minutes (in the draw's pool) %d; Q among those %d" % (
        len(dn), sum(1 for _, r in dn if (num(r.get("min_proj")) or 0) >= 15), sum(1 for _, r in dn if (num(r.get("min_proj")) or 0) >= 15 and r.get("status") == "Questionable")))
    if a.pdir:
        os.makedirs(a.pdir, exist_ok=True)
        for key, date, g, cid in NIGHTS:
            n = "%s_%s" % (date, g)
            json.dump({k[1]: x for k, x in ph.items() if k[0] == n}, open(os.path.join(a.pdir, "p_%s.json" % key), "w"))
        print("chances written to %s for %d nights" % (a.pdir, len(NIGHTS)))


def score(a):
    import dk_eval as E
    res = {}
    for key, date, g, cid in NIGHTS:
        f = os.path.join(a.dir, "dnp_%s.json" % key)
        if not os.path.exists(f):
            continue
        N = json.load(open(os.path.join(a.dir, key + ".json"))); B = json.load(open(f))
        P = {r["dk_id"]: r for r in csv.DictReader(open(os.path.join(DK, "%s_%s.csv" % (date, g))))}
        act = {k: float(r["actual_dk"] or 0) for k, r in P.items()}
        own = N["field"]["own"]
        ents, _ = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
        pts = sorted([e["points"] for e in ents], reverse=True)
        t10, cash = pts[math.ceil(0.1 * len(pts)) - 1], pts[min(max(E.pay_table(N["contest"]["payouts"])), len(pts)) - 1]
        asc = sorted(pts)
        pctl = lambda x: sum(1 for p in asc if p < x) / len(asc)
        res[key] = {}
        for v in VARIANTS:
            L = B["banks"][v]; sc = [sum(act.get(x, 0) for x in ids) for ids in L]
            dnp = [sum(1 for x in ids if x in P and not float(P[x]["min"] or 0)) for ids in L]
            res[key][v] = {"n": len(L), "t10": S.mean(x >= t10 for x in sc), "cash": S.mean(x >= cash for x in sc), "pctl": S.mean(pctl(x) for x in sc),
                           "own": S.mean(sum(own.get(x, 0) for x in i) for i in L), "dnp": S.mean(dnp)}
    print("Rule-free banks at bank noise 0.35, the same seeds under each projection, scored on real points (%d nights with standings: thin)." % len(res))
    print("%-11s %-10s %5s %5s %7s %6s %6s %5s" % ("night", "variant", "n", "own", "top10%", "cash%", "pctl", "DNPs"))
    for key, r in res.items():
        for v in VARIANTS:
            x = r[v]
            print("%-11s %-10s %5d %4.0f%% %6.1f%% %5.1f%% %5.1f%% %5.2f" % (key, v, x["n"], x["own"], 100 * x["t10"], 100 * x["cash"], 100 * x["pctl"], x["dnp"]))
    print("\nPooled (mean of the nights) and nights better than current:")
    for v in VARIANTS:
        m = lambda k: S.mean(res[n][v][k] for n in res)
        w = lambda k: sum(res[n][v][k] > res[n]["cur"][k] + 1e-9 for n in res)
        print("  %-10s top10 %.1f%% cash %.1f%% pctl %.1f%% DNPs a lineup %.2f   better: top10 %d, cash %d, pctl %d of %d" % (
            v, 100 * m("t10"), 100 * m("cash"), 100 * m("pctl"), m("dnp"), w("t10"), w("cash"), w("pctl"), len(res)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("accuracy"); x.add_argument("--pdir")
    y = sub.add_parser("score"); y.add_argument("--dir", required=True)
    a = ap.parse_args()
    {"accuracy": accuracy, "score": score}[a.cmd](a)
