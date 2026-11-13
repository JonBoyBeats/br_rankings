"""Season tests on the contest side (asked 2026-11-13): results only, no rule changes. Writes
analysis/nba/report/money_season_tests.md.

Every night on file (nba_money.load: teams, draft windows, prices, swaps credited), each pick read at its team's draft
window in tier_history.csv (tier, flag, drafted%, Boom, built rank) and scored by what it scored (a ruled-out pick through
its swap: the team's slots). Multiple: a group's top-1% (top-10%) finishes over what the whole field in the same contest
and the same price quintile finishes (all teams in that stratum, so the field averages 1.0); counts beside it, and an 80%
range from resampling nights.

  1. T5 by drafted%     each T5 pick's drafted% at the lock (share of that window's pods modelled to take him), 10-point
                        bands: holders' multiples and the band's share of the field's T5 picks
  2. Upside in T5       within a band, players whose Boom% is above (below) what's usual for their projection (a season
                        line of Boom% on projection over every T5 player)
  3. Winners by tier    top-1% teams' points from each tier minus the field's, in the same contest and price quintile;
                        season (per top-1% team) and the median night
  4. Duds and smashes   a pick under 60% (over 150%) of that night's tier average (players who played, at that window):
                        top-1% teams carrying one in the tier against the field's rate in their stratum
  5. Boundaries         a T4 VALUE player against a T3 PRICEY one, and a T4 PRICEY player against a top-3 T5 one (the
                        button's first three in T5): pairs at one window with ADP within 4 in the same round (within 4
                        alone where same-round leaves under 100 teams a side); each side's multiple, and A against B
                        (nba_money.evaluate: same contest and price, the register's lift)

  python3 scripts/nba_money_season.py --mirror ../br-adp-mirror
"""
import argparse, collections, math, os, random, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_money as M      # noqa: E402

OUT = os.path.join(M.REP, "money_season_tests.md")
num = M.num
BANDS = [(k, k + 10) for k in range(0, 100, 10)]
GROUPS = [("under 20%", 0, 20), ("20-70%", 20, 70), ("70%+", 70, 101)]


def teams_of(N):
    """[(night, team)] with a draft window and a price bin."""
    return [(n, t) for n in N for ts in n["teams"].values() for t in ts if t["window"] and t["bin"] is not None]


def picks(n, t):
    """[(tier row or None, points scored)] for a team's six paid picks at its window."""
    rows = n["tiers"][t["window"]]
    return [(rows.get(pp), fp) for pp, _, fp in t["slots"]]


def rates(TT):
    """{(date, contest, bin): {x: the stratum's top-x% rate}} over every team with a window and bin."""
    by = collections.defaultdict(list)
    for n, t in TT:
        by[(n["date"], t["contest"]["contest_id"], t["bin"])].append(t)
    return {k: {x: sum(t["top"][x] for t in v) / len(v) for x in (1, 10)} for k, v in by.items()}


def multiple(units, R):
    """units: [(night, team)] (a team once). -> {teams, o1, e1, m1, o10, e10, m10, r10 (80% range)}."""
    per = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for n, t in units:
        r = R[(n["date"], t["contest"]["contest_id"], t["bin"])]
        p = per[n["date"]]
        p[0] += t["top"][1]; p[1] += r[1]; p[2] += t["top"][10]; p[3] += r[10]
    s = [sum(p[i] for p in per.values()) for i in range(4)]
    out = {"teams": len(units), "o1": int(s[0]), "e1": s[1], "m1": s[0] / s[1] if s[1] else None,
           "o10": int(s[2]), "e10": s[3], "m10": s[2] / s[3] if s[3] else None}
    ds, rnd, boots = sorted(per), random.Random(11), []
    for _ in range(1000 if len(ds) >= 3 else 0):
        b = [per[rnd.choice(ds)] for _ in ds]
        e = sum(x[3] for x in b)
        if e:
            boots.append(sum(x[2] for x in b) / e)
    boots.sort()
    out["r10"] = (boots[len(boots) // 10], boots[len(boots) * 9 // 10]) if boots else None
    return out


def mcell(m):
    if not m["teams"] or m["m10"] is None:
        return "- | - | 0"
    r = " (%.2f-%.2f)" % m["r10"] if m["r10"] else ""
    return "%.2f (%d of %.1f) | %.2f%s (%d of %.1f) | %d" % (m["m1"], m["o1"], m["e1"], m["m10"], r, m["o10"], m["e10"], m["teams"])


MHEAD = "top-1% multiple (finishes of expected) | top-10% multiple (80% range) (finishes of expected) | teams"


def band_of(d):
    return next("%d-%d%%" % (a, b) for a, b in BANDS if a <= d < b) if d < 100 else "90-100%"


def test1(TT, R):
    units = collections.defaultdict(set)
    picks_in = collections.Counter()
    n_picks = 0
    for i, (n, t) in enumerate(TT):
        for row, _ in picks(n, t):
            if not row or row["tier"] != "5":
                continue
            d = num(row["drafted"])
            n_picks += 1
            b = band_of(d) if d is not None else "no drafted%"
            picks_in[b] += 1
            units[b].add(i)
            if d is not None:
                units[next(g for g, a, z in GROUPS if a <= d < z)].add(i)
    res = {}
    L = ["| Drafted% at lock | share of the field's T5 picks | " + MHEAD + " |", "|---|---|---|---|---|"]
    for b in ["%d-%d%%" % ab for ab in BANDS] + ["no drafted%"]:
        m = multiple([TT[i] for i in units[b]], R)
        res[b] = m
        L.append("| %s | %.1f%% (%d) | %s |" % (b, 100 * picks_in[b] / n_picks, picks_in[b], mcell(m)))
    L.append("| | | | | |")
    for g, a, z in GROUPS:
        m = multiple([TT[i] for i in units[g]], R)
        res[g] = m
        k = sum(picks_in[band_of(x)] for x in range(a, min(z, 100), 10))
        L.append("| **%s** | %.1f%% (%d) | %s |" % (g, 100 * k / n_picks, k, mcell(m)))
    return L, res


def test2(TT, R, N):
    xs, ys = [], []
    for n in N:
        for w in ("am", "pm"):
            for r in n["tiers"][w].values():
                if r["tier"] == "5" and num(r["boom"]) is not None and num(r["proj"]) is not None:
                    xs.append(num(r["proj"])); ys.append(num(r["boom"]))
    mx, my = st.mean(xs), st.mean(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    resid = lambda r: num(r["boom"]) - (my + slope * (num(r["proj"]) - mx))
    units = collections.defaultdict(set)
    for i, (n, t) in enumerate(TT):
        for row, _ in picks(n, t):
            if not row or row["tier"] != "5" or num(row["drafted"]) is None or num(row["boom"]) is None or num(row["proj"]) is None:
                continue
            side = "higher" if resid(row) > 0 else "lower"
            d = num(row["drafted"])
            units[(next(g for g, a, z in GROUPS if a <= d < z), side)].add(i)
            units[(band_of(d), side)].add(i)
    res = {}
    L = ["Usual Boom%% for a projection: %.3f + %.4f x (projection - %.1f), from %d T5 player-windows." % (my, slope, mx, len(xs)), "",
         "| Drafted% band | Boom vs usual | " + MHEAD + " |", "|---|---|---|---|---|"]
    for b in [g for g, _, _ in GROUPS] + ["%d-%d%%" % ab for ab in BANDS]:
        for side in ("higher", "lower"):
            if not units[(b, side)]:
                continue
            m = multiple([TT[i] for i in units[(b, side)]], R)
            res[(b, side)] = m
            L.append("| %s | %s | %s |" % ("**%s**" % b if b in [g for g, _, _ in GROUPS] else b, side, mcell(m)))
    return L, res


def test3(TT):
    """Per tier: top-1% teams' points from the tier minus the stratum's average (same contest and price bin), and the same
    against the whole contest."""
    pts = lambda n, t: {k: sum(fp for row, fp in picks(n, t) if (row["tier"] if row else "none") == k) for k in ("1", "2", "3", "4", "5", "none")}
    strat, cont = collections.defaultdict(list), collections.defaultdict(list)
    P = {}
    for i, (n, t) in enumerate(TT):
        P[i] = pts(n, t)
        strat[(n["date"], t["contest"]["contest_id"], t["bin"])].append(i)
        cont[(n["date"], t["contest"]["contest_id"])].append(i)
    mean_of = lambda ids: {k: st.fmean(P[j][k] for j in ids) for k in P[ids[0]]}
    sm = {k: mean_of(v) for k, v in strat.items()}
    cm = {k: mean_of(v) for k, v in cont.items()}
    gap = collections.defaultdict(list)          # (tier, basis) -> [(date, gap)]
    for i, (n, t) in enumerate(TT):
        if not t["top"][1]:
            continue
        s, c = sm[(n["date"], t["contest"]["contest_id"], t["bin"])], cm[(n["date"], t["contest"]["contest_id"])]
        for k in P[i]:
            gap[(k, "price")].append((n["date"], P[i][k] - s[k]))
            gap[(k, "contest")].append((n["date"], P[i][k] - c[k]))
    L = ["| Tier | top-1% minus same-price field, season | median night | top-1% minus whole contest, season | median night |",
         "|---|---|---|---|---|"]
    res = {}
    for k in ("1", "2", "3", "4", "5", "none"):
        row = []
        for basis in ("price", "contest"):
            g = gap[(k, basis)]
            byn = collections.defaultdict(list)
            for d, x in g:
                byn[d].append(x)
            row += [st.fmean(x for _, x in g), st.median(st.fmean(v) for v in byn.values())]
        res[k] = row
        L.append("| %s | %+.1f | %+.1f | %+.1f | %+.1f |" % (("T" + k) if k != "none" else "no tier row", *row))
    tot = [sum(res[k][j] for k in res) for j in range(4)]
    L.append("| **all six picks** | %+.1f | (%+.1f) | %+.1f | (%+.1f) |" % tuple(tot))
    n1 = len(gap[("1", "price")])
    L += ["", "%d top-1%% teams. Medians don't add up across tiers; the season columns do (every pick has a tier row or "
          "falls in \"no tier row\")." % n1]
    return L, res


def test4(TT, R):
    avg = {}
    for n in {id(n): n for n, _ in TT}.values():
        for w in ("am", "pm"):
            by = collections.defaultdict(list)
            for r in n["tiers"][w].values():
                if r["played"] == "1" and num(r["actual"]) is not None:
                    by[r["tier"]].append(num(r["actual"]))
            for k, v in by.items():
                avg[(n["date"], w, k)] = st.fmean(v)
    carry = {}
    for i, (n, t) in enumerate(TT):
        c = set()
        for row, fp in picks(n, t):
            if not row:
                continue
            a = avg.get((n["date"], t["window"], row["tier"]))
            if a:
                if fp < 0.6 * a:
                    c.add(("dud", row["tier"]))
                if fp > 1.5 * a:
                    c.add(("smash", row["tier"]))
        carry[i] = c
    strat = collections.defaultdict(list)
    for i, (n, t) in enumerate(TT):
        strat[(n["date"], t["contest"]["contest_id"], t["bin"])].append(i)
    rate = {k: {x: sum(x in carry[i] for i in v) / len(v) for x in [(a, b) for a in ("dud", "smash") for b in "12345"]} for k, v in strat.items()}
    L = ["| | Tier | top-1% teams carrying one | field's share (same contest and price) | ratio |", "|---|---|---|---|---|"]
    res = {}
    top = [(i, n, t) for i, (n, t) in enumerate(TT) if t["top"][1]]
    for kind in ("dud", "smash"):
        for k in "12345":
            x = (kind, k)
            o = sum(x in carry[i] for i, _, _ in top)
            e = sum(rate[(n["date"], t["contest"]["contest_id"], t["bin"])][x] for _, n, t in top)
            res[x] = (o, e, len(top))
            L.append("| %s | T%s | %.1f%% (%d of %d) | %.1f%% | %.2f |" % (
                "dud (under 60%)" if kind == "dud" else "smash (over 150%)", k, 100 * o / len(top), o, len(top), 100 * e / len(top),
                o / e if e else float("nan")))
    return L, res


def test5(N, TT, R, dates):
    def pick_pair(want_a, want_b):
        def pick(a, b):
            if want_a(a) and want_b(b):
                return a
            if want_a(b) and want_b(a):
                return b
            return None
        return pick
    tests = [("T4 VALUE (A) vs T3 PRICEY (B)", lambda r: r["tier"] == "4" and r["flag"] == "VALUE",
              lambda r: r["tier"] == "3" and r["flag"] == "PRICEY"),
             ("T4 PRICEY (A) vs a top-3 T5 (B)", lambda r: r["tier"] == "4" and r["flag"] == "PRICEY", "top3")]
    L = ["| Test | pairs | side | " + MHEAD + " |", "|---|---|---|---|---|---|"]
    res = {}
    for name, fa, fb in tests:
        for n in N:
            for w in ("am", "pm"):
                t5 = sorted((int(r["built"]), p) for p, r in n["tiers"][w].items() if r["tier"] == "5" and r["built"])
                n.setdefault("_top3", {})[w] = {p for _, p in t5[:3]}
        want_b = fb if fb != "top3" else (lambda r: r["tier"] == "5" and r["player_id"] in N_BY[r["date"]]["_top3"][r["window"]])
        for label, same_round in (("same round", True), ("ADP within 4", False)):
            def pick(a, b, sr=same_round):
                if sr:
                    pod = N_BY[a["date"]]["pod"]
                    if math.ceil(num(a["adp"]) / pod) != math.ceil(num(b["adp"]) / pod):
                        return None
                return pick_pair(fa, want_b)(a, b)
            cs = M.pair_cases(N, ("am", "pm"), None, pick, same_tier=False)
            A = {(c[0], id(c[4])): c[4] for c in cs if c[3] == "A"}
            B = {(c[0], id(c[4])): c[4] for c in cs if c[3] == "B"}
            if same_round and min(len(A), len(B)) < 100:
                continue
            ev = M.evaluate(cs, dates)["field"]["all"]
            ma = multiple([(N_BY[d], t) for (d, _), t in A.items()], R)
            mb = multiple([(N_BY[d], t) for (d, _), t in B.items()], R)
            res[name] = (label, ma, mb, ev)
            L.append("| %s | %s | A | %s |" % (name, label, mcell(ma)))
            L.append("| | | B | %s |" % mcell(mb))
            L.append("| | | A against B | %s |" % (M.cell(ev) if ev else "none"))
            break
    return L, res


N_BY = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(M.HERE, "..", "br-adp-mirror"))
    ap.add_argument("--json", help="also dump the numbers here")
    a = ap.parse_args()
    M.MIRROR_PATH = a.mirror
    N = [n for n in M.load(a.mirror) if n["tiers"]["am"] or n["tiers"]["pm"]]
    for n in N:
        N_BY[n["date"]] = n
        for w in ("am", "pm"):
            for r in n["tiers"][w].values():
                r["window"] = w
    dates = [n["date"] for n in N]
    TT = teams_of(N)
    R = rates(TT)
    l1, r1 = test1(TT, R)
    l2, r2 = test2(TT, R, N)
    l3, r3 = test3(TT)
    l4, r4 = test4(TT, R)
    l5, r5 = test5(N, TT, R, dates)
    body = (["## 1. T5 by how often drafted", ""] + l1 + ["", "## 2. Upside in T5 (Boom% against the usual for his projection)", ""] + l2 +
            ["", "## 3. Where winners are made: points by tier", ""] + l3 + ["", "## 4. Dud and smash tolerance", ""] + l4 +
            ["", "## 5. Boundaries", ""] + l5)
    head = ["# Season tests: T5 and the tier boundaries in contest results", "",
            "Written by scripts/nba_money_season.py (definitions in its docstring), %s to %s: %d nights, %d teams with a draft window "
            "and price. Multiples are against the same contest and price quintile (the field averages 1.0). Results only: no "
            "rule changes." % (dates[0], dates[-1], len(N), len(TT)), "", "## Summary", "",
            "(written by hand from the tables below when the file is published)", ""]
    open(OUT, "w").write("\n".join(head + body) + "\n")
    if not a.json:
        print("\n".join(head + body))
        return
    import json
    json.dump({"t1": {k: v for k, v in r1.items()}, "t2": {"%s|%s" % k: v for k, v in r2.items()}, "t3": r3,
               "t4": {"%s|%s" % k: v for k, v in r4.items()}, "t5": {k: [v[0], v[1], v[2], {"lift10": v[3]["lift"][10], "r80": v[3].get("r80"), "n": v[3]["n"]} if v[3] else None] for k, v in r5.items()}},
              open(a.json, "w"), indent=1, default=str)
    print("\n".join(head + body))


if __name__ == "__main__":
    main()
