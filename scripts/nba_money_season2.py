"""Follow-ups to the season study (asked 2026-11-13), results only. Writes analysis/nba/report/money_season_followups.md.

Same matching as scripts/nba_money_season.py: every night on file, each pick read at its team's draft window in
tier_history.csv and scored through its swap; a multiple is a group's top-x% finishes (or cashes) over what the whole field
in the same contest and price quintile does, with an 80% range from resampling nights.

  ownership    a player's real share of the contest's teams, from the rosters. Draft: teams that drafted him (a swapped-in
               pick counts for the ruled-out player it replaced, where the swap is credited). After swaps: teams whose
               final lineup has him.
  1-2. T5 curve      teams holding a T5 player at each ownership band (0-5, 5-10, 10-20, 20-30, 30-50, 50+), once per band
  3. T5 width        pairs of T5 players at one window whose projections are within X points (X = 2-6) and whose ownership
                     differs: teams holding the less-owned and not the other (A) against teams holding the more-owned and
                     not the other (B), same contest and price quintile; a team counts once per pair it falls in
  4. Share of edge   per tier, its share of the top-1% teams' points edge over same-price teams, beside its share of the
                     field's average team points
  5. Cash line       per tier, teams carrying a dud (under 60% of that night's tier average among players who played) or a
                     smash (over 150%): cash, top-10% and top-1% multiples

  python3 scripts/nba_money_season2.py --mirror ../br-adp-mirror
"""
import argparse, collections, os, random, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_money as M            # noqa: E402
import nba_money_season as S     # noqa: E402

OUT = os.path.join(M.REP, "money_season_followups.md")
num = M.num
BANDS = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 101)]
WIDTHS = (2, 3, 4, 5, 6)
XS = ("cash", 10, 1)


def hit(t, x):
    return (t["payout"] > 0) if x == "cash" else t["top"][x]


def rates(TT):
    by = collections.defaultdict(list)
    for n, t in TT:
        by[(n["date"], t["contest"]["contest_id"], t["bin"])].append(t)
    return {k: {x: sum(hit(t, x) for t in v) / len(v) for x in XS} for k, v in by.items()}


def multiple(units, R):
    """units: [(night, team)], each team once. -> {x: (multiple, observed, expected)}, teams, 80% range at the top 10%."""
    per = collections.defaultdict(lambda: collections.defaultdict(float))
    for n, t in units:
        r = R[(n["date"], t["contest"]["contest_id"], t["bin"])]
        p = per[n["date"]]
        for x in XS:
            p[("o", x)] += hit(t, x)
            p[("e", x)] += r[x]
    out = {"teams": len(units)}
    for x in XS:
        o, e = sum(p[("o", x)] for p in per.values()), sum(p[("e", x)] for p in per.values())
        out[x] = (o / e if e else None, int(o), e)
    ds, rnd, boots = sorted(per), random.Random(11), []
    for _ in range(1000 if len(ds) >= 3 else 0):
        b = [per[rnd.choice(ds)] for _ in ds]
        e = sum(p[("e", 10)] for p in b)
        if e:
            boots.append(sum(p[("o", 10)] for p in b) / e)
    boots.sort()
    out["r10"] = (boots[len(boots) // 10], boots[len(boots) * 9 // 10]) if boots else None
    return out


def m3(m):
    if not m["teams"] or m[10][0] is None:
        return "- | - | - | 0"
    f = lambda x: "%.2f (%d of %.1f)" % m[x] if m[x][0] is not None else "-"
    r = " (%.2f-%.2f)" % m["r10"] if m["r10"] else ""
    return "%s | %s | %s%s | %d" % (f(1), f("cash"), f(10).replace(" (", "%s (" % r, 1), "", m["teams"])


HEAD3 = "top 1% (finishes of expected) | cash (of expected) | top 10% (80% range) (of expected) | teams"


def ownership(N):
    """{(date, contest id): ({player: draft share}, {player: after-swap share})}."""
    out = {}
    for n in N:
        for cid, ts in n["teams"].items():
            d, a = collections.Counter(), collections.Counter()
            for t in ts:
                d.update(M.drafted_by(t))
                a.update(set(t["picks"]))
            out[(n["date"], cid)] = ({p: 100 * k / len(ts) for p, k in d.items()}, {p: 100 * k / len(ts) for p, k in a.items()})
    return out


def band(o):
    return next("%d-%d%%" % (a, b) if b <= 100 else "%d%%+" % a for a, b in BANDS if a <= o < b)


def t5_players(n, t, which):
    """The team's T5 players at its window: drafted (with swaps credited back) or in the final lineup."""
    rows = n["tiers"][t["window"]]
    ps = M.drafted_by(t) if which == "draft" else set(t["picks"])
    return [p for p in ps if rows.get(p) and rows[p]["tier"] == "5"]


def test2(TT, R, OWN):
    L = []
    res = {}
    for which, k in (("draft", 0), ("after swaps", 1)):
        units, picks = collections.defaultdict(set), collections.Counter()
        for i, (n, t) in enumerate(TT):
            own = OWN[(n["date"], t["contest"]["contest_id"])][k]
            for p in t5_players(n, t, "draft" if k == 0 else "final"):
                b = band(own.get(p, 0))
                units[b].add(i)
                picks[b] += 1
        tot = sum(picks.values())
        L += ["**%s ownership**" % which.capitalize(), "", "| T5 ownership | share of the field's T5 picks | " + HEAD3 + " |",
              "|---|---|---|---|---|---|"]
        for a, b in BANDS:
            lab = band(a)
            m = multiple([TT[i] for i in units[lab]], R)
            res[(which, lab)] = m
            L.append("| %s | %.1f%% (%d) | %s |" % (lab, 100 * picks[lab] / tot, picks[lab], m3(m)))
        L.append("")
    return L, res


def weighted_lift(TT, wA, wB):
    """Stratified (contest x price quintile) lift of A-weighted teams against B-weighted teams, per x, with the top-10%
    80% range from resampling nights: like nba_money.strata_lift with a team counted once per pair it falls in."""
    by = collections.defaultdict(list)
    for i, (n, t) in enumerate(TT):
        if wA.get(i) or wB.get(i):
            by[(n["date"], t["contest"]["contest_id"], t["bin"])].append(i)
    per = collections.defaultdict(lambda: collections.defaultdict(float))
    for (d, _, _), ids in by.items():
        sb = sum(wB.get(i, 0) for i in ids)
        sa = sum(wA.get(i, 0) for i in ids)
        if not sb or not sa:
            continue
        p = per[d]
        for x in XS:
            rb = sum(wB.get(i, 0) * hit(TT[i][1], x) for i in ids) / sb
            p[("o", x)] += sum(wA.get(i, 0) * hit(TT[i][1], x) for i in ids)
            p[("e", x)] += sa * rb
        p["nA"] += sa
        p["nB"] += sb
    out = {x: (lambda o, e: (o / e if e else None))(sum(p[("o", x)] for p in per.values()), sum(p[("e", x)] for p in per.values())) for x in XS}
    out["nA"], out["nB"], out["slates"] = sum(p["nA"] for p in per.values()), sum(p["nB"] for p in per.values()), len(per)
    ds, rnd, boots = sorted(per), random.Random(11), []
    for _ in range(1000 if len(ds) >= 3 else 0):
        b = [per[rnd.choice(ds)] for _ in ds]
        e = sum(p[("e", 10)] for p in b)
        if e:
            boots.append(sum(p[("o", 10)] for p in b) / e)
    boots.sort()
    out["r10"] = (boots[len(boots) // 10], boots[len(boots) * 9 // 10]) if boots else None
    out["above"] = sum(v > 1 for v in boots) / len(boots) if boots else None
    return out


def test3(TT, OWN, N):
    L = ["| Within (projected points) | ownership | less-owned's holders against the more-owned's: top 1% | cash | top 10% (80% range; share of resamples above 1) | team-pairs A / B | slates |",
         "|---|---|---|---|---|---|---|"]
    res = {}
    # per (date, window): T5 rows with a projection
    t5 = {}
    for n in N:
        for w in ("am", "pm"):
            t5[(n["date"], w)] = [(p, num(r["proj"])) for p, r in n["tiers"][w].items() if r["tier"] == "5" and num(r["proj"]) is not None]
    for which, k in (("draft", 0), ("after swaps", 1)):
        for X in WIDTHS:
            wA, wB = {}, {}
            partners = {}
            for i, (n, t) in enumerate(TT):
                key = (n["date"], t["contest"]["contest_id"], t["window"])
                own = OWN[(n["date"], t["contest"]["contest_id"])][k]
                if key not in partners:
                    rows = t5[(n["date"], t["window"])]
                    less, more = collections.defaultdict(set), collections.defaultdict(set)
                    for ia, (a, pa) in enumerate(rows):
                        for b, pb in rows[ia + 1:]:
                            if abs(pa - pb) > X:
                                continue
                            oa, ob = own.get(a, 0), own.get(b, 0)
                            if oa == ob:
                                continue
                            lo, hi = (a, b) if oa < ob else (b, a)
                            less[lo].add(hi)        # lo is the less-owned of the pair (lo, hi)
                            more[hi].add(lo)
                    partners[key] = (less, more)
                less, more = partners[key]
                H = set(t5_players(n, t, "draft" if k == 0 else "final"))
                a = sum(len(less[p] - H) for p in H)
                b = sum(len(more[p] - H) for p in H)
                if a:
                    wA[i] = a
                if b:
                    wB[i] = b
            r = weighted_lift(TT, wA, wB)
            res[(which, X)] = r
            f = lambda v: "%.2f" % v if v is not None else "-"
            L.append("| %d | %s | %s | %s | %s (%.2f-%.2f; %.0f%%) | %d / %d | %d |" % (
                X, which, f(r[1]), f(r["cash"]), f(r[10]), r["r10"][0], r["r10"][1], 100 * r["above"], r["nA"], r["nB"], r["slates"]))
    return L, res


def test4(TT):
    P = {i: {k: sum(fp for row, fp in S.picks(n, t) if (row["tier"] if row else "none") == k) for k in ("1", "2", "3", "4", "5", "none")}
         for i, (n, t) in enumerate(TT)}
    strat = collections.defaultdict(list)
    for i, (n, t) in enumerate(TT):
        strat[(n["date"], t["contest"]["contest_id"], t["bin"])].append(i)
    sm = {k: {tier: st.fmean(P[j][tier] for j in v) for tier in P[v[0]]} for k, v in strat.items()}
    gap = collections.defaultdict(float)
    n1 = 0
    for i, (n, t) in enumerate(TT):
        if t["top"][1]:
            n1 += 1
            s = sm[(n["date"], t["contest"]["contest_id"], t["bin"])]
            for tier in P[i]:
                gap[tier] += P[i][tier] - s[tier]
    field = {tier: st.fmean(P[i][tier] for i in P) for tier in P[0]}
    tg, tf = sum(gap.values()) / n1, sum(field.values())
    L = ["| Tier | top-1% edge over same-price teams | share of the edge | field's average points | share of the field's points | edge share over points share |",
         "|---|---|---|---|---|---|"]
    res = {}
    for tier in ("1", "2", "3", "4", "5", "none"):
        g = gap[tier] / n1
        res[tier] = (g, g / tg, field[tier], field[tier] / tf)
        L.append("| %s | %+.1f | %.0f%% | %.1f | %.0f%% | %.2f |" % ("T" + tier if tier != "none" else "no tier row", g, 100 * g / tg,
                                                               field[tier], 100 * field[tier] / tf, (g / tg) / (field[tier] / tf) if field[tier] else 0))
    L.append("| **all** | %+.1f | 100%% | %.1f | 100%% | |" % (tg, tf))
    return L, res


def test5(TT, R, N):
    avg = {}
    for n in N:
        for w in ("am", "pm"):
            by = collections.defaultdict(list)
            for r in n["tiers"][w].values():
                if r["played"] == "1" and num(r["actual"]) is not None:
                    by[r["tier"]].append(num(r["actual"]))
            for k, v in by.items():
                avg[(n["date"], w, k)] = st.fmean(v)
    units = collections.defaultdict(list)
    for n, t in TT:
        c = set()
        for row, fp in S.picks(n, t):
            a = avg.get((n["date"], t["window"], row["tier"])) if row else None
            if a:
                if fp < 0.6 * a:
                    c.add(("dud", row["tier"]))
                if fp > 1.5 * a:
                    c.add(("smash", row["tier"]))
        for x in c:
            units[x].append((n, t))
    L = ["| | Tier | " + HEAD3 + " |", "|---|---|---|---|---|---|"]
    res = {}
    for kind in ("dud", "smash"):
        for k in "12345":
            m = multiple(units[(kind, k)], R)
            res[(kind, k)] = m
            L.append("| %s | T%s | %s |" % ("dud (under 60%)" if kind == "dud" else "smash (over 150%)", k, m3(m)))
    return L, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(M.HERE, "..", "br-adp-mirror"))
    a = ap.parse_args()
    M.MIRROR_PATH = a.mirror
    N = [n for n in M.load(a.mirror) if n["tiers"]["am"] or n["tiers"]["pm"]]
    dates = [n["date"] for n in N]
    TT = S.teams_of(N)
    R = rates(TT)
    OWN = ownership(N)
    l2, _ = test2(TT, R, OWN)
    l3, _ = test3(TT, OWN, N)
    l4, _ = test4(TT)
    l5, _ = test5(TT, R, N)
    head = ["# Season follow-ups: real ownership in T5, the tiebreak's width, the edge by tier, duds at the cash line", "",
            "Written by scripts/nba_money_season2.py (definitions in its docstring), %s to %s: %d nights, %d teams with a draft "
            "window and price. Multiples are against the same contest and price quintile (the field averages 1.0). Results "
            "only: no rule changes." % (dates[0], dates[-1], len(N), len(TT)), "", "## Summary", "",
            "(written by hand from the tables below when the file is published)", ""]
    body = (["## 1-2. T5 by real ownership", ""] + l2 + ["## 3. T5: how wide the less-owned tiebreak can go", ""] + l3 +
            ["", "## 4. Share of the edge by tier", ""] + l4 + ["", "## 5. Duds and smashes at the cash line", ""] + l5)
    open(OUT, "w").write("\n".join(head + body) + "\n")
    print("\n".join(head + body))


if __name__ == "__main__":
    main()
