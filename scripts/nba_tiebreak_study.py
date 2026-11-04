"""The ownership-tiebreak study in analysis/nba/report/field_studies.md (section 2), as run.

Each night's flagship (its largest contest) and that night's daily record. A decision pair is two players with:
  - closing ADP (adp_close, raw ADP, not ranks) within 4 of each other
  - ETR medians (etr_median) within 2 points
  - drafted% (pods that drafted him / pods, in the flagship) at least 10 points apart, and both at least 2%
    (the floor drops the undrafted pile and late scratches, whom Underdog swaps off every team)
Every unordered pair that qualifies counts, so a player can be in several. Players need adp_close, etr_median and
actual in the record (opening night has no ETR). "Outscored" is actual points strictly higher. A breaker scored at
least the 90th percentile of the night's priced players in his round band (band = ceil(closing-ADP rank / pod size)).
Ranges: whole nights resampled 1,000 times, 80%.

  python3 scripts/nba_tiebreak_study.py [--since YYYY-MM-DD] [--through YYYY-MM-DD]
"""
import argparse, collections, itertools, math, os, random, sys

sys.path.insert(0, os.path.dirname(__file__))
import nba_contests as nc   # noqa: E402  the contest files, the daily record and drafted%, as the measures read them


def night_pairs(date):
    contests, teams = nc.load_night(date)
    c = max(contests, key=lambda c: int(c["entries"]))
    ts, pod = teams[c["contest_id"]], int(c["pod_size"])
    info = nc.players_on(date, c["slate"])
    path = os.path.join(nc.DAILY, "%s_%s.csv" % (date, c["slate"].replace("nba_", "")))
    etr = {r["player_id"]: float(r["etr_median"]) for r in nc.csv.DictReader(open(path)) if r["etr_median"]}
    rank, (d, _) = nc.day_ranks(info), nc.drafted(ts, pod)
    by_band = collections.defaultdict(list)
    for p, r in info.items():
        if r["adp"] is not None and r["fp"] is not None:
            by_band[math.ceil(rank[p] / pod)].append(r["fp"])
    p90 = {b: sorted(v)[int(0.9 * (len(v) - 1))] for b, v in by_band.items()}
    cut, on = math.ceil(len(ts) / 100), collections.defaultdict(list)
    for t in ts:
        for p in t["picks"]:
            on[p].append(t["place"] <= cut)
    ps = [p for p in info if info[p]["adp"] is not None and info[p]["fp"] is not None and p in etr]
    out = []
    for a, b in itertools.combinations(ps, 2):
        if abs(info[a]["adp"] - info[b]["adp"]) > 4 or abs(etr[a] - etr[b]) > 2:
            continue
        da, db = d.get(a, 0), d.get(b, 0)
        if abs(da - db) < 0.10 or min(da, db) < 0.02:
            continue
        lo, hi = (a, b) if da < db else (b, a)
        brk = lambda p: info[p]["fp"] >= p90[math.ceil(rank[p] / pod)]
        out.append({"date": date, "lo_wins": info[lo]["fp"] > info[hi]["fp"], "lo_brk": brk(lo), "hi_brk": brk(hi),
                    "lo_t1": sum(on[lo]), "lo_n": len(on[lo]), "hi_t1": sum(on[hi]), "hi_n": len(on[hi])})
    return out


def summary(ps):
    lt, ln, ht, hn = (sum(p[k] for p in ps) for k in ("lo_t1", "lo_n", "hi_t1", "hi_n"))
    return (sum(p["lo_wins"] for p in ps) / len(ps), sum(p["lo_brk"] for p in ps) / len(ps),
            sum(p["hi_brk"] for p in ps) / len(ps), lt / ln, ht / hn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-20")
    ap.add_argument("--through", default="2026-11-02")
    a = ap.parse_args()
    dates = sorted({c["date"] for c in nc.load_contests() if a.since <= c["date"] <= a.through})
    by = {d: night_pairs(d) for d in dates}
    pairs = [p for d in dates for p in by[d]]
    s, dd = summary(pairs), [d for d in dates if by[d]]
    random.seed(5)
    bs = [summary([p for d in random.choices(dd, k=len(dd)) for p in by[d]]) for _ in range(1000)]
    w, t = sorted(x[0] for x in bs), sorted(x[3] - x[4] for x in bs)
    print("%d pairs over %d nights (%s to %s)" % (len(pairs), len(dd), a.since, a.through))
    print("  lower-drafted outscored the higher: %.0f%% (80%%: %.0f-%.0f)" % (100 * s[0], 100 * w[100], 100 * w[900]))
    print("  breaker rate: lower-drafted %.0f%%, higher %.0f%%" % (100 * s[1], 100 * s[2]))
    print("  top-1%% rate of teams carrying: lower-drafted %.2f%%, higher %.2f%% (difference 80%%: %+.2f to %+.2f)" % (
        100 * s[3], 100 * s[4], 100 * t[100], 100 * t[900]))


if __name__ == "__main__":
    main()
