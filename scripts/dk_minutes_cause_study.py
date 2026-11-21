"""Where our minutes go wrong (2026-11-21, the operator's step C via the coordinator). Analysis only.

For every player who played (not tagged Out, projected minutes, real minutes > 0) on every slate with box scores, the
minutes error e = real - projected, split by cause:
  team out     his team had an Out regular (season average 15+ minutes): did the hand-off's projected boost (our
               minutes less the same team fit with the Outs put back in, as cbb_nightly's out_gain) get the size right?
               Correction: the boost scaled by k.
  blowout      by the final margin (20+, a diagnostic: not knowable before lock) and by the pre-game spread (the usable
               version; cbb_nightly already scales minutes by the spread, MIN_BY_SPREAD, so this is what's left).
               Correction: b x max(0, |spread| - 10) for starters (projected 25+) and for the bench (under 15), b fit.
  recent       his last-5 minutes (min_last5, the MPG column's data) against what we project: does weighting them in
               beat our form minutes (FORM 0.8 weights plus last season)? Correction: our minutes moved w of the way
               to his last-5 mean, the team refit to 200 (cbb_nightly.fit_minutes).
  overtime     the team's real minutes add up to 215+ (an overtime): noise, not knowable before lock. Fouls: the box
               scores we keep have no fouls column, so foul trouble is not measured.
Each correction's parameter is chosen on the other slates (held out by slate) and judged on the one left out. Every
cause's share of the squared minutes error, its bias, and how much of the error its held-out correction removes.

  analyse --brr DIR             the cause table, per slate then pooled
  lenses --brr DIR --cand C     the A2 lenses for a candidate (C: out / spread / recent), held out by slate, as the A2
                                studies report them (scripts/dk_minutes_steep_study.py: minutes, points, shape, Vegas,
                                salary gaps), points moving with minutes (points per minute held)
  score --dir DIR --cand C      the rule-free banks drawn by scripts/dk_minutes_cause_study.js (current vs the candidate,
                                same seeds), scored on real points as scripts/dk_cheap_minutes_study.py does
"""
import argparse, csv, json, math, os, statistics as S, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import dk_minutes_steep_study as M          # noqa: E402  (slates, the A2 lenses)

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
num = lambda v: float(v) if v not in ("", None) else None
OUT_AVG, OT_MIN, BLOW, SPREAD0 = 15.0, 215.0, 20.0, 10.0
GRID = {"out": [round(0.1 * i, 1) for i in range(31)], "spread": None, "recent": [round(0.05 * i, 2) for i in range(21)]}


def name_of(rows):
    return "%s_%s" % (rows[0]["date"], rows[0]["draft_group"])


def prep(rows, nt):
    """Per player who played: his error and the cause fields. Team-level: OT, final margin, the Out regulars and the
    projected boost (our minutes less the team fit with the Outs back in, at the steepen of the slate's date)."""
    teams = defaultdict(list)
    for r in rows:
        teams[r["team"]].append(r)
    score = {t: sum(num(r.get("pts")) or 0 for r in rs) for t, rs in teams.items()}
    tmin = {t: sum(num(r.get("min")) or 0 for r in rs) for t, rs in teams.items()}
    opp = {}
    for r in rows:
        two = (r.get("game") or "").split("@")
        if len(two) == 2:
            opp[r["team"]] = two[1] if r["team"] == two[0] else two[0]
    g = nt.STEEP if rows[0]["date"] >= "2026-11-20" else 0.0
    boost = {}
    for t, rs in teams.items():
        live = [r for r in rs if r.get("status") != "Out" and num(r.get("min_proj"))]
        outs = [r for r in rs if r.get("status") == "Out" and (num(r.get("min_avg")) or 0) >= OUT_AVG]
        if not outs or len(live) < 5:
            continue
        m0 = [num(r.get("min_raw")) or num(r["min_proj"]) for r in live]
        om = [num(r.get("min_raw")) or num(r.get("min_proj")) or num(r.get("min_avg")) for r in outs]
        base = nt.steepen(nt.fit_minutes(m0 + om), g)[:len(live)]
        for r, b in zip(live, base):
            boost[r["dk_id"]] = num(r["min_proj"]) - b
    out = []                     # every player not Out with projected minutes; the error is measured on those who played
    for r in rows:
        mp, ma = num(r.get("min_proj")), num(r.get("min")) or 0
        if r.get("status") == "Out" or not mp:
            continue
        t = r["team"]
        sp = num(r.get("spread"))
        out.append({"id": r["dk_id"], "team": t, "mp": mp, "ma": ma, "e": ma - mp, "played": ma > 0, "boost": boost.get(r["dk_id"]),
                    "ot": tmin.get(t, 0) >= OT_MIN, "margin": abs(score[t] - score[opp[t]]) if t in opp and opp[t] in score else None,
                    "spread": abs(sp) if sp is not None else None, "l5": num(r.get("min_last5")), "avg": num(r.get("min_avg"))})
    return out


def corrected(P, cand, par):
    """{id: corrected minutes} for one slate's played players under a candidate and its parameter (refit to the team's
    projected total for 'recent', so a team still adds up to what it did)."""
    if cand == "out":
        return {p["id"]: p["mp"] + (par - 1) * p["boost"] if p["boost"] is not None else p["mp"] for p in P}
    if cand == "spread":
        bs, bb = par
        f = lambda p: (bs if p["mp"] >= 25 else bb if p["mp"] < 15 else 0.0) * max(0.0, (p["spread"] or 0) - SPREAD0)
        return {p["id"]: max(0.0, p["mp"] + f(p)) for p in P}
    if cand == "recent":
        by = defaultdict(list)
        for p in P:
            by[p["team"]].append(p)
        res = {}
        for ps in by.values():
            m = [p["mp"] + par * (p["l5"] - p["mp"]) if p["l5"] is not None else p["mp"] for p in ps]
            tot0, tot1 = sum(p["mp"] for p in ps), sum(m)
            k = tot0 / tot1 if tot1 else 1.0          # the team keeps its projected total
            for p, x in zip(ps, m):
                res[p["id"]] = min(40.0, x * k)
        return res
    raise ValueError(cand)


def sse(P, mins=None):
    return sum((p["ma"] - (mins[p["id"]] if mins else p["mp"])) ** 2 for p in P if p["played"])


def fit_spread(train):
    """Least squares b for starters and bench on max(0, |spread| - 10) against the error."""
    out = []
    for sel in (lambda p: p["mp"] >= 25, lambda p: p["mp"] < 15):
        xs = [(max(0.0, (p["spread"] or 0) - SPREAD0), p["e"]) for P in train for p in P if p["played"] and sel(p)]
        sxx = sum(x * x for x, _ in xs)
        out.append(sum(x * y for x, y in xs) / sxx if sxx else 0.0)
    return tuple(out)


def choose(cand, train):
    if cand == "spread":
        return fit_spread(train)
    return min(GRID[cand], key=lambda k: sum(sse(P, corrected(P, cand, k)) for P in train))


def analyse(a):
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import cbb_nightly as nt
    sl = M.slates(); names = [name_of(r) for r in sl]
    PA = [prep(rows, nt) for rows in sl]                       # every player not Out (the corrections run on these)
    Ps = [[p for p in P if p["played"]] for P in PA]           # the error is measured on those who played
    print("Slates with box scores: %d (%s); players who played: %d. A thin sample: nine slates over five dates." % (
        len(sl), ", ".join(names), sum(len(P) for P in Ps)))
    groups = [("team had an Out regular", lambda p: p["boost"] is not None, True),
              ("  of them, boosted 2+ min", lambda p: p["boost"] is not None and p["boost"] >= 2, True),
              ("final margin 20+ (diagnostic)", lambda p: (p["margin"] or 0) >= BLOW, False),
              ("pre-game spread 10+", lambda p: (p["spread"] or 0) >= SPREAD0, True),
              ("  starters (proj 25+), spread 10+", lambda p: (p["spread"] or 0) >= SPREAD0 and p["mp"] >= 25, True),
              ("  bench (proj <15), spread 10+", lambda p: (p["spread"] or 0) >= SPREAD0 and p["mp"] < 15, True),
              ("last-5 off his projection by 4+", lambda p: p["l5"] is not None and abs(p["l5"] - p["mp"]) >= 4, True),
              ("overtime game", lambda p: p["ot"], False)]
    tot = sum(sse(P) for P in Ps); n = sum(len(P) for P in Ps)
    print("\nPer slate: n played, minutes MAE, bias, and the share of the slate's squared error in each group (out / spread 10+ / last-5 off 4+ / overtime / final 20+)")
    for nm, P in zip(names, Ps):
        t = sse(P); sh = lambda f: 100 * sum(p["e"] ** 2 for p in P if f(p)) / t
        print("  %-18s n %3d MAE %.2f bias %+.2f | out %4.1f%% spread %4.1f%% recent %4.1f%% OT %4.1f%% blowout %4.1f%%" % (
            nm, len(P), S.mean(abs(p["e"]) for p in P), S.mean(p["e"] for p in P), sh(groups[0][1]), sh(groups[3][1]), sh(groups[6][1]), sh(groups[7][1]), sh(groups[2][1])))
    print("\nPooled: minutes MAE %.2f, RMSE %.2f, bias (real - ours) %+.2f over %d players who played." % (
        S.mean(abs(p["e"]) for P in Ps for p in P), math.sqrt(tot / n), S.mean(p["e"] for P in Ps for p in P), n))
    print("\n%-36s %6s %7s %8s %7s %s" % ("group", "n", "share n", "share SE", "bias", "knowable before lock"))
    for lab, f, known in groups:
        g = [p for P in Ps for p in P if f(p)]
        if g:
            print("%-36s %6d %6.1f%% %7.1f%% %+7.2f %s" % (lab, len(g), 100 * len(g) / n, 100 * sum(p["e"] ** 2 for p in g) / tot, S.mean(p["e"] for p in g), "yes" if known else "no"))
    # the hand-off's size: real error against the projected boost
    xb = [(p["boost"], p["e"]) for P in Ps for p in P if p["boost"] is not None]
    if xb:
        hi = [e for b, e in xb if b >= 2]; lo = [e for b, e in xb if b < 2]
        print("\nTeam out: %d teammate-games; projected boost mean %.2f min; their error (real - ours) %+.2f where boosted 2+ (n %d), %+.2f where boosted less (n %d)." % (
            len(xb), S.mean(b for b, _ in xb), S.mean(hi) if hi else 0, len(hi), S.mean(lo) if lo else 0, len(lo)))
    # each correction held out by slate
    print("\nHeld-out corrections (parameter chosen on the other slates; squared error removed, share of the whole):")
    best = None
    for cand in ("out", "spread", "recent"):
        before = after = 0.0; wins = 0; pars = []; rows_ = []
        cors = []
        for i, P in enumerate(Ps):
            par = choose(cand, [Q for j, Q in enumerate(PA) if j != i]); pars.append(par)
            c = corrected(PA[i], cand, par); cors.append(c)
            b, x = sse(P), sse(P, c)
            before += b; after += x; wins += x < b - 1e-9
            rows_.append((names[i], par, math.sqrt(b / len(P)), math.sqrt(x / len(P)), S.mean(abs(p["e"]) for p in P),
                          S.mean(abs(p["ma"] - c[p["id"]]) for p in P)))
        print("  %-7s removes %.2f%% of the squared error (MAE %.3f -> %.3f); better on %d of %d slates; parameters %s" % (
            cand, 100 * (before - after) / tot, S.mean(abs(p["e"]) for P in Ps for p in P),
            S.mean(abs(p["ma"] - c[p["id"]]) for P, c in zip(Ps, cors) for p in P),
            wins, len(Ps), "; ".join(fmtpar(x) for x in pars)))
        for nm, par, rb, ra, mb, ma in rows_:
            print("      %-18s par %-14s RMSE %.3f -> %.3f   MAE %.3f -> %.3f" % (nm, fmtpar(par), rb, ra, mb, ma))
        gain = (before - after) / tot
        if best is None or gain > best[1]:
            best = (cand, gain)
    ot = sum(p["e"] ** 2 for P in Ps for p in P if p["ot"])
    print("\nOvertime: %.1f%% of the squared error, not knowable before lock. Fouls: not in our box scores, not measured." % (100 * ot / tot))
    print("Largest held-out gain: %s (%.2f%% of the squared error)." % (best[0], 100 * best[1]))


def fmtpar(x):
    return "%.2f/%.2f" % x if isinstance(x, tuple) else "%.2f" % x


def lenses(a):
    """The A2 lenses for one candidate, its parameter chosen on the other slates (held out by slate)."""
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import cbb_nightly as nt
    sl = M.slates(); names = [name_of(r) for r in sl]
    Ps = [prep(rows, nt) for rows in sl]
    orig = M.steepen
    fmt = lambda x: "-" if x is None else "%.3f" % x
    res = []
    for i, rows in enumerate(sl):
        par = choose(a.cand, [Q for j, Q in enumerate(Ps) if j != i])
        mins = corrected(Ps[i], a.cand, par)

        def st(rows_, g, _m=mins):
            out = {}
            for r in rows_:
                mp = num(r.get("min_proj"))
                if r.get("status") == "Out" or not mp:
                    continue
                m = _m.get(r["dk_id"], mp) if g else mp
                out[r["dk_id"]] = (m, (num(r.get("fp_dk")) or 0) * (m / mp))
            return out
        M.steepen = st
        b, x = M.lenses(rows, 0.0), M.lenses(rows, 1.0)
        res.append((names[i], par, b, x))
    M.steepen = orig
    print("Candidate %s, held out by slate: minutes MAE (A1's: no 20+ blowouts or news scratches), points MAE, shape top-2 ours-recent, Vegas slope, salary gaps unexplained/all" % a.cand)
    print("The correction runs on every player not Out (before lock no one knows who sits); it is fit on the errors of those who played.")
    for n, par, b, x in res:
        print("  %-18s par %-10s minutes %s -> %s; points %s -> %s; shape %s -> %s; Vegas %s -> %s; gaps %d/%d -> %d/%d" % (
            n, fmtpar(par), fmt(b["min_mae"]), fmt(x["min_mae"]), fmt(b["pts_mae"]), fmt(x["pts_mae"]), fmt(b["shape_top2_vs_recent"]), fmt(x["shape_top2_vs_recent"]),
            fmt(b["vegas_slope"]), fmt(x["vegas_slope"]), b["unexplained"], b["gaps"], x["unexplained"], x["gaps"]))
    k = lambda key, f: sum(1 for _, _, b, x in res if b[key] is not None and x[key] is not None and f(x[key], b[key]))
    m = lambda side, key: S.mean(r[side][key] for r in [{"b": b, "x": x} for _, _, b, x in res] if r[side][key] is not None)
    print("  pooled (mean of slates): minutes %.3f -> %.3f (better on %d of %d); points %.3f -> %.3f (better on %d); |shape| %.3f -> %.3f (larger on %d); Vegas %.3f -> %.3f; unexplained gaps %d -> %d" % (
        m("b", "min_mae"), m("x", "min_mae"), k("min_mae", lambda x, y: x < y - 1e-9), len(res), m("b", "pts_mae"), m("x", "pts_mae"), k("pts_mae", lambda x, y: x < y - 1e-9),
        S.mean(abs(b["shape_top2_vs_recent"] or 0) for _, _, b, _ in res), S.mean(abs(x["shape_top2_vs_recent"] or 0) for _, _, _, x in res),
        k("shape_top2_vs_recent", lambda x, y: abs(x) > abs(y) + 1e-9), m("b", "vegas_slope"), m("x", "vegas_slope"),
        sum(b["unexplained"] for _, _, b, _ in res), sum(x["unexplained"] for _, _, _, x in res)))
    # the parameter on every slate, for the banks (the .js applies it on the lock-time slates)
    print("  parameter on all slates: %s" % fmtpar(choose(a.cand, Ps)))


def score(a):
    import dk_eval as E
    import dk_cheap_minutes_study as C
    res = {}
    for key, date, g, cid in C.NIGHTS:
        f = os.path.join(a.dir, "mincause_%s.json" % key)
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
        for v, L in B["banks"].items():
            sc = [sum(act.get(x, 0) for x in ids) for ids in L]
            res[key][v] = {"n": len(L), "t10": S.mean(x >= t10 for x in sc), "cash": S.mean(x >= cash for x in sc), "pctl": S.mean(pctl(x) for x in sc),
                           "own": S.mean(sum(own.get(x, 0) for x in i) for i in L), "moved": B.get("moved", {}).get(v)}
    vs = list(next(iter(res.values())).keys())
    print("Rule-free banks at bank noise 0.35, the same seeds, current minutes vs the candidate (%s), scored on real points (%d nights with standings: thin)." % (a.cand, len(res)))
    for key, r in res.items():
        for v in vs:
            x = r[v]
            print("  %-11s %-8s n %5d own %4.0f%% top10 %5.1f%% cash %5.1f%% pctl %5.1f%%%s" % (key, v, x["n"], x["own"], 100 * x["t10"], 100 * x["cash"], 100 * x["pctl"],
                                                                              "" if x["moved"] is None else "  (players moved 1+ min: %d)" % x["moved"]))
    print("Pooled (mean of nights), nights better than current:")
    for v in vs:
        m = lambda k: S.mean(res[n][v][k] for n in res)
        w = lambda k: sum(res[n][v][k] > res[n]["cur"][k] + 1e-9 for n in res)
        print("  %-8s top10 %.1f%% cash %.1f%% pctl %.1f%%   better: top10 %d, cash %d, pctl %d of %d" % (v, 100 * m("t10"), 100 * m("cash"), 100 * m("pctl"), w("t10"), w("cash"), w("pctl"), len(res)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("analyse"); x.add_argument("--brr", required=True)
    y = sub.add_parser("lenses"); y.add_argument("--brr", required=True); y.add_argument("--cand", required=True, choices=["out", "spread", "recent"])
    z = sub.add_parser("score"); z.add_argument("--dir", required=True); z.add_argument("--cand", required=True)
    a = ap.parse_args()
    {"analyse": analyse, "lenses": lenses, "score": score}[a.cmd](a)
