"""The Monday lock review's ownership section (2026-11-23): our projected ownership (the field doc's own, what the DK
page shows) against real ownership on every graded contest, by the operator's contest-size bands, and two candidate
calibrations tested held out by slate. Analysis only: it changes nothing the pipeline or the page reads.

Bands (the operator, 2026-11-23): Large 300+ entries, Medium 30-299, Small under 30 (the under-10 contests noted).
Candidates:
  flat      own' = own^a, renormalized to the contest's projected total (800% less what's unlisted): a < 1 flattens.
            a fitted leave-one-slate-out on the held-out log error, log((real + 1) / (own' + 1))
  big       ours with only the big-game factor (below), f fitted on the other slates
  mix       own' = (1 - b) own + b x the contest's projected total spread evenly over its listed players: lifts the
            near-zero players a power can't (a player we project at 0 stays 0 under own^a), b fitted held out
  flat+big  the flattening, then the watchlist's confirmed pattern "coming off a big game" (last game's DK points 10+ over his
            season average, dk_eval.ownwatch's flag) x f, f fitted on the other slates (real/projected of the flagged
            against the rest), renormalized again
Lenses: mean |log error|, MAE in points, the band ratios real/projected (under 5, 5-20, 20+), and how many players
cross the page's thresholds (10%: the draw's "under X%"; 20%: chalk) between ours and the candidate.

  python3 scripts/dk_own_review.py --mirror ../br-adp-mirror
"""
import argparse, collections, csv, datetime as dt, math, os, random, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E          # noqa: E402

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
BANDS = [("Large", 300, 10 ** 9), ("Medium", 30, 300), ("Small", 0, 30)]
OWNB = [(0, 5), (5, 20), (20, 101)]


def entries(cid):
    f = os.path.join(DK, "standings", "contest-standings-%s.csv" % cid)
    if not os.path.exists(f):
        return None
    return sum(1 for r in csv.reader(open(f, encoding="utf-8-sig")) if len(r) > 1 and r[1].strip().isdigit())


def band(n):
    return next(b for b, lo, hi in BANDS if lo <= n < hi)


def big_game_flags(mirror):
    """{draft group: {dk_id}} flagged 'coming off a big game' at lock (dk_eval.ownwatch's rule and data)."""
    rows, _ = E.own_rows()
    M, out = E.Mirror(mirror), {}
    for (d, g), rs in E.groupby_night([r for r in rows if r["own_proj"] is not None]).items():
        day = E.iso(d + "T00:00:00Z"); start = None; last = {}
        for t, sha in reversed(M.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
            sl = next((x for x in M.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
            if sl and start is None:
                start = E.iso(sl["start"])
            if sl and start and t < start:
                last = {k: (p.get("last5") or [None])[-1] for k, p in (sl.get("players") or {}).items()}
                break
        out[g] = {r["dk_id"] for r in rs if isinstance(last.get(r["dk_id"]), list) and r.get("dkavg") is not None and last[r["dk_id"]][2] >= r["dkavg"] + 10}
    return out


def load():
    con = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(DK, "own_eval.csv"))):
        p, a = E.num(r["own_proj"]), E.num(r["own_actual"])
        if p is None or a is None:
            continue
        con[(r["date"], str(r["draft_group"]), r["contest_id"])].append({"id": r["dk_id"], "name": r["name"], "p": p, "a": a})
    out = []
    for (d, g, c), rs in sorted(con.items()):
        n = entries(c)
        if n:
            out.append({"date": d, "g": g, "cid": c, "n": n, "band": band(n), "rows": rs})
    return out


def calib(rs, a, big=None, f=1.0, mix=0.0):
    """own' for a contest's rows: ^a renormalized to the projected total (or, with mix, shrunk that far toward an even
    spread), then the flagged x f renormalized."""
    tot = sum(r["p"] for r in rs)
    q = [r["p"] ** a if r["p"] > 0 else 0.0 for r in rs]
    s = sum(q) or 1.0
    q = [x * tot / s for x in q]
    if mix:
        q = [(1 - mix) * x + mix * tot / len(rs) for x in q]
    if big and f != 1.0:
        q = [x * (f if r["id"] in big else 1.0) for x, r in zip(q, rs)]
        s = sum(q) or 1.0
        q = [x * tot / s for x in q]
    return q


def lens(cons, a=1.0, big=None, f=1.0, mix=0.0):
    le, ae, bands = [], [], {b: [0.0, 0.0] for b in OWNB}
    for c in cons:
        q = calib(c["rows"], a, (big or {}).get(c["g"]), f, mix)
        for r, x in zip(c["rows"], q):
            le.append(abs(math.log((r["a"] + 1) / (x + 1)))); ae.append(abs(r["a"] - x))
            for lo, hi in OWNB:
                if lo <= r["p"] < hi:       # banded by OUR projection, as the audit
                    bands[(lo, hi)][0] += r["a"]; bands[(lo, hi)][1] += x
    return {"log": S.mean(le) if le else None, "mae": S.mean(ae) if ae else None,
            "bands": [round(v[0] / v[1], 2) if v[1] else None for v in bands.values()], "n": len(le)}


def fit_a(cons, big=None, f=1.0):
    grid = [x / 100 for x in range(50, 121, 2)]
    return min(grid, key=lambda a: lens(cons, a, big, f)["log"])


def fit_f(cons, a, big):
    """The flagged players' real / candidate against the rest's, pooled over contests (log ratio of means)."""
    fl, rest = [], []
    for c in cons:
        q = calib(c["rows"], a); b = big.get(c["g"]) or set()
        for r, x in zip(c["rows"], q):
            (fl if r["id"] in b else rest).append(math.log((r["a"] + 1) / (x + 1)))
    return math.exp(S.mean(fl) - S.mean(rest)) if fl and rest else 1.0


def crossings(cons, a, big=None, f=1.0, mix=0.0):
    """Players whose ownership crosses 10% or 20% between ours and the candidate, per contest (mean)."""
    out = []
    for c in cons:
        q = calib(c["rows"], a, (big or {}).get(c["g"]), f, mix)
        out.append(sum(1 for r, x in zip(c["rows"], q) if (r["p"] < 10) != (x < 10) or (r["p"] < 20) != (x < 20)))
    return S.mean(out) if out else 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror")); a_ = ap.parse_args()
    cons = load()
    slates = sorted({c["g"] for c in cons}, key=lambda g: min(c["date"] for c in cons if c["g"] == g))
    big = big_game_flags(a_.mirror)
    print("Contests: %d on %d slates. By band: %s" % (len(cons), len(slates), "; ".join(
        "%s %d contests on %d slates (%s entries)" % (b, sum(c["band"] == b for c in cons), len({c["g"] for c in cons if c["band"] == b}),
                                                     ", ".join(str(c["n"]) for c in cons if c["band"] == b) if b == "Small" else "%d-%d" % (
                                                         min([c["n"] for c in cons if c["band"] == b] or [0]), max([c["n"] for c in cons if c["band"] == b] or [0])))
        for b, _, _ in BANDS)))
    print("\n== Real vs ours by band (all contests; real/projected in our <5 / 5-20 / 20+ bands; |log error|; MAE points) ==")
    for b, _, _ in BANDS:
        cb = [c for c in cons if c["band"] == b]
        if cb:
            L = lens(cb)
            print("  %-6s n %4d players  bands %s  |log| %.3f  MAE %.2f" % (b, L["n"], L["bands"], L["log"], L["mae"]))
    u10 = [c for c in cons if c["n"] < 10]
    if u10:
        L = lens(u10); print("  (under 10 entries: %d contests, n %d, bands %s, |log| %.3f)" % (len(u10), L["n"], L["bands"], L["log"]))
    print("\n== Per slate (all its contests): ours vs real ==")
    for g in slates:
        cs = [c for c in cons if c["g"] == g]; L = lens(cs)
        print("  %s %s  %d contests (%s)  bands %s  |log| %.3f  MAE %.2f" % (cs[0]["date"], g, len(cs), "/".join(sorted({c["band"][0] for c in cs})), L["bands"], L["log"], L["mae"]))
    # leave one slate out: a (flat) and a + f (flat+big)
    print("\n== Candidates held out by slate (fit on the other slates, scored on the slate) ==")
    rows = []
    for g in slates:
        tr, te = [c for c in cons if c["g"] != g], [c for c in cons if c["g"] == g]
        a = fit_a(tr); f = fit_f(tr, a, big)
        b0, b1, b2 = lens(te), lens(te, a), lens(te, a, big, f)
        rows.append((g, te[0]["date"], a, f, b0, b1, b2))
        print("  %s %s  a %.2f  f %.2f  |log| ours %.3f -> flat %.3f -> flat+big %.3f   bands ours %s flat %s" % (
            te[0]["date"], g, a, f, b0["log"], b1["log"], b2["log"], b0["bands"], b1["bands"]))
    # the big-game factor alone, and the mix toward even, held out the same way
    for g in slates:
        tr, te = [c for c in cons if c["g"] != g], [c for c in cons if c["g"] == g]
        f1 = fit_f(tr, 1.0, big); mb = min([x / 100 for x in range(0, 31, 2)], key=lambda m: lens(tr, 1.0, mix=m)["log"])
        r = next(x for x in rows if x[0] == g)
        rows[rows.index(r)] = r + (lens(te, 1.0, big, f1), lens(te, 1.0, mix=mb), f1, mb, lens(te, 1.0, big, f1, mb))
    print("  big alone: f by slate %s; mix: b by slate %s" % (", ".join("%.2f" % r[9] for r in rows), ", ".join("%.2f" % r[10] for r in rows)))
    for r in rows:
        print("  %s %s  held out: |log| ours %.3f, mix %.3f, mix+big %.3f; MAE ours %.2f, mix %.2f, mix+big %.2f; bands mix %s" % (
            r[1], r[0], r[4]["log"], r[8]["log"], r[11]["log"], r[4]["mae"], r[8]["mae"], r[11]["mae"], r[8]["bands"]))
    for k, nm in ((5, "flat"), (6, "flat+big"), (7, "big"), (8, "mix"), (11, "mix+big")):
        better = sum(1 for r in rows if r[k]["log"] < r[4]["log"] - 1e-9); mbet = sum(1 for r in rows if r[k]["mae"] < r[4]["mae"] - 1e-9)
        bb = [S.mean(r[k]["bands"][j] for r in rows) for j in range(3)]
        print("  %-8s held-out |log| %.3f vs ours %.3f, better on %d of %d slates; MAE %.2f vs %.2f (better on %d); bands %s vs ours %s" % (
            nm, S.mean(r[k]["log"] for r in rows), S.mean(r[4]["log"] for r in rows), better, len(rows), S.mean(r[k]["mae"] for r in rows), S.mean(r[4]["mae"] for r in rows), mbet,
            [round(x, 2) for x in bb], [round(S.mean(r[4]["bands"][j] for r in rows), 2) for j in range(3)]))
    aall = fit_a(cons); fall = fit_f(cons, aall, big)
    print("  fitted on every slate: a %.2f, big-game f %.2f; pooled bands ours %s -> flat %s -> flat+big %s" % (
        aall, fall, lens(cons)["bands"], lens(cons, aall)["bands"], lens(cons, aall, big, fall)["bands"]))
    # by band: a fitted per band, and its spread over slate bootstraps (does one exponent fit all?)
    print("\n== One exponent or per band? (a fitted per band on every slate; 200 bootstrap resamples of slates) ==")
    rnd = random.Random(20261123)
    for b, _, _ in BANDS:
        cb = [c for c in cons if c["band"] == b]
        gs = sorted({c["g"] for c in cb})
        if len(gs) < 3:
            print("  %-6s %d contests on %d slates: too thin to fit (fit with the neighbouring band)" % (b, len(cb), len(gs))); continue
        boots = []
        for _ in range(200):
            pick = [rnd.choice(gs) for _ in gs]
            boots.append(fit_a([c for g in pick for c in cb if c["g"] == g]))
        boots.sort()
        print("  %-6s %d contests on %d slates: a %.2f (bootstrap 90%%: %.2f-%.2f); held-out |log| at it %.3f vs ours %.3f" % (
            b, len(cb), len(gs), fit_a(cb), boots[10], boots[189], lens(cb, fit_a(cb))["log"], lens(cb)["log"]))
    f1all = fit_f(cons, 1.0, big)
    mball = min([x / 100 for x in range(0, 31, 2)], key=lambda m: lens(cons, 1.0, mix=m)["log"])
    print("\n== The mix by band (b fitted per band; 200 slate bootstraps) and what it moves ==")
    for b, _, _ in BANDS:
        cb = [c for c in cons if c["band"] == b]; gs = sorted({c["g"] for c in cb})
        fitb = lambda cc: min([x / 100 for x in range(0, 31, 2)], key=lambda m: lens(cc, 1.0, mix=m)["log"])
        if len(gs) < 3:
            L0, L1 = lens(cb), lens(cb, 1.0, mix=mball)
            print("  %-6s %d contests on %d slates: too thin to fit; at the pooled b %.2f |log| %.3f -> %.3f, MAE %.2f -> %.2f, bands %s -> %s" % (
                b, len(cb), len(gs), mball, L0["log"], L1["log"], L0["mae"], L1["mae"], L0["bands"], L1["bands"])); continue
        boots = sorted(fitb([c for g in [rnd.choice(gs) for _ in gs] for c in cb if c["g"] == g]) for _ in range(200))
        L0, L1 = lens(cb), lens(cb, 1.0, mix=fitb(cb))
        print("  %-6s b %.2f (bootstrap 90%%: %.2f-%.2f); |log| %.3f -> %.3f, MAE %.2f -> %.2f, bands %s -> %s" % (
            b, fitb(cb), boots[10], boots[189], L0["log"], L1["log"], L0["mae"], L1["mae"], L0["bands"], L1["bands"]))
    print("  mix b %.2f on every slate moves %.1f players a contest across 10%% / 20%%" % (mball, crossings(cons, 1.0, mix=mball)))
    print("\n== What it would move on the page (players crossing 10%% or 20%% a contest, mean): flat %.1f, flat+big %.1f, big alone (f %.2f) %.1f ==" % (
        crossings(cons, aall), crossings(cons, aall, big, fall), f1all, crossings(cons, 1.0, big, f1all)))
    for b, _, _ in BANDS:          # the big-game factor by band
        cb = [c for c in cons if c["band"] == b]
        if len({c["g"] for c in cb}) >= 3:
            print("  big-game f in %s: %.2f; |log| ours %.3f -> big %.3f" % (b, fit_f(cb, 1.0, big), lens(cb)["log"], lens(cb, 1.0, big, fit_f(cb, 1.0, big))["log"]))
    nb = sum(len(v) for v in big.values())
    print("Big-game flags on file: %d player-slates on %d slates" % (nb, sum(1 for v in big.values() if v)))


if __name__ == "__main__":
    main()
