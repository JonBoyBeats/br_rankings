"""Season tests on the tiers, all pairs by nights (results only; 2026-11-13). python3 scripts/nba_tier_season_tests.py <out.json> > analysis/nba/report/tier_season_tests.md body. Reads analysis/nba/report/tier_history.csv:
each night's tiers, flags, projection (AM ours at the lock, PM ETR at the lock), ADP, Boom and the button's order."""
import collections, csv, functools, math, random, sys

sys.path.insert(0, "scripts")
import nba_tier_history as TH

H = list(csv.DictReader(open("analysis/nba/report/tier_history.csv")))
num = TH.num
for r in H:
    r["adpv"], r["projv"], r["act"] = num(r["adp"]), num(r["proj"]), num(r["actual"])
    r["boomv"], r["tierv"], r["builtv"], r["podv"] = num(r["boom"]), int(r["tier"]), num(r["built"]), int(r["pod"])
    r["ok"] = r["played"] == "1" and r["act"] is not None            # ruled out after lock / no box: left out
NW = collections.defaultdict(list)
for r in H:
    NW[(r["date"], r["window"])].append(r)
CAP = {6: 36, 4: 24}


def adp_of(r):
    return min(r["adpv"], CAP[r["podv"]]) if r["adpv"] is not None else CAP[r["podv"]]


def keyed(r):
    v = r["projv"]
    return {"row": r, "adp": -adp_of(r), "proj": float(int(v + 0.5)) if v is not None else None, "projx": v, "boom": r["boomv"]}


def rank_by(rows, how):
    """{player_id: position} for an order; None marks a tie the order can't break (its pairs are left out)."""
    if how == "adp":
        return {r["player_id"]: adp_of(r) for r in rows}
    if how == "proj":
        return {r["player_id"]: -(r["projv"] if r["projv"] is not None else -1e9) for r in rows}
    raise ValueError


def positions(order):
    return {r["player_id"]: i for i, r in enumerate(order)}


def pair_rows(rows, key_a, key_b):
    """(points A's first minus A's second, A right?) for every pair the two orders put differently."""
    out = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            x, y = rows[i], rows[j]
            a, b = key_a[x["player_id"]], key_a[y["player_id"]]
            c, d = key_b[x["player_id"]], key_b[y["player_id"]]
            if a == b or c == d or (a < b) == (c < d):
                continue
            first, second = (x, y) if a < b else (y, x)
            if first["act"] == second["act"]:
                continue
            out.append(first["act"] - second["act"])
    return out


def summarize(by_night):
    """by_night: {night: [A's points per disagreeing pair]} (positive: A's first scored more)."""
    nights = [n for n, v in by_night.items() if v]
    won = sum(1 for n in nights if sum(x > 0 for x in by_night[n]) > sum(x < 0 for x in by_night[n]))
    lost = sum(1 for n in nights if sum(x > 0 for x in by_night[n]) < sum(x < 0 for x in by_night[n]))
    allp = [x for n in nights for x in by_night[n]]
    rnd, a_ahead, b_ahead = random.Random(11), 0, 0
    for _ in range(4000):
        s = [rnd.choice(nights) for _ in nights]
        diff = sum(sum(x > 0 for x in by_night[n]) - sum(x < 0 for x in by_night[n]) for n in s)
        a_ahead += diff > 0
        b_ahead += diff < 0
    return {"nights": len(nights), "won": won, "lost": lost, "even": len(nights) - won - lost, "pairs": len(allp),
            "right": sum(x > 0 for x in allp), "ppp": sum(allp) / len(allp) if allp else 0.0,
            "a_share": a_ahead / 4000, "b_share": b_ahead / 4000}


def line(label, a, b, s):
    if not s["nights"]:
        return "| %s | %s vs %s | no disagreeing pairs | | | |" % (label, a, b)
    return "| %s | %s vs %s | %d-%d-%d of %d | %.0f%% / %.0f%% | %+.2f | %d (%s right %d%%) |" % (
        label, a, b, s["won"], s["lost"], s["even"], s["nights"], 100 * s["a_share"], 100 * s["b_share"], s["ppp"],
        s["pairs"], a, round(100 * s["right"] / s["pairs"]))


HEAD = ("| test | A vs B | nights A won-lost-even | resamples A ahead / B ahead | points per pair (A's first minus "
        "A's second) | disagreeing pairs |\n|---|---|---|---|---|---|")


def tier_rows(night, t):
    return [r for r in NW[night] if r["tierv"] == t and r["ok"]]


def compare(window, tiers, order_a, order_b):
    """order_*: function(rows of one night's tier, night) -> {player_id: sort key}."""
    by = collections.defaultdict(list)
    for night in NW:
        if night[1] != window:
            continue
        for t in tiers:
            rows = tier_rows(night, t)
            if len(rows) >= 2:
                by[night] += pair_rows(rows, order_a(rows, night), order_b(rows, night))
    return summarize(by)


ADP = lambda rows, night: rank_by(rows, "adp")
PROJ = lambda rows, night: rank_by(rows, "proj")


def elites(night):
    t1 = sorted([r for r in NW[night] if r["tierv"] == 1 and r["projv"] is not None], key=lambda r: -r["projv"])
    if len(t1) <= 1:
        return 1
    top = [r["projv"] for r in t1[:4]]
    gaps = [top[i] - top[i + 1] for i in range(min(3, len(top) - 1))]
    return 1 + gaps.index(max(gaps))


def elite_break(rows, night):
    pod = NW[night][0]["podv"]
    x = (13 if pod == 6 else 9) - elites(night)
    head = sorted([r for r in rows if adp_of(r) < x], key=adp_of)
    tail = sorted([r for r in rows if adp_of(r) >= x], key=lambda r: -(r["projv"] if r["projv"] is not None else -1e9))
    return positions(head + tail)


SHARED = {"am": [("proj", 3), ("adp", 0)], "pm": [("proj", 0), ("adp", 0), ("boom", 0)]}


def shared(rows, night):
    out = []
    for f in ("VALUE", "", "PRICEY"):
        out += [k["row"] for k in TH.rule_sort([keyed(r) for r in rows if r["flag"] == f], SHARED[night[1]])]
    return positions(out)


def boundary(window, side_a, side_b):
    """Every player in side_a against every player in side_b, on nights both exist: A = side_a goes first."""
    by = collections.defaultdict(list)
    for night in NW:
        if night[1] != window:
            continue
        A, B = side_a(night), side_b(night)
        by[night] += [a["act"] - b["act"] for a in A for b in B if a["act"] != b["act"]]
    return summarize(by)


def t4_value(night):
    return [r for r in tier_rows(night, 4) if r["flag"] == "VALUE"]


def t3_pricey(night):
    return [r for r in tier_rows(night, 3) if r["flag"] == "PRICEY"]


def t4_pricey(night):
    return [r for r in tier_rows(night, 4) if r["flag"] == "PRICEY"]


def t5_top3(night):
    t5 = sorted([r for r in NW[night] if r["tierv"] == 5 and r["builtv"] is not None], key=lambda r: r["builtv"])[:3]
    return [r for r in t5 if r["ok"]]


def line5(night):
    """Today's T4/T5 line on the ADP ladder and the alternative (a 2+ pick gap in 28-33 / 18-23, else the start of
    round 6), and the players whose combined tier changes."""
    rows = NW[night]
    pod = rows[0]["podv"]
    A = sorted(rows, key=lambda r: (adp_of(r), -(r["projv"] if r["projv"] is not None else -1e9)))
    va = [adp_of(r) for r in A]
    la = TH.lines(va, TH.LADDER[pod], TH.MIN_TIER[pod])
    lo, hi, start = (28, 33, 30) if pod == 6 else (18, 23, 20)
    best, gap = None, -1
    for k in range(lo, min(hi, len(va) - 1) + 1):
        g = va[k] - va[k - 1]
        if g > gap + 1e-9 or (abs(g - gap) <= 1e-9 and abs(k - start) < abs(best - start)):
            best, gap = k, g
    alt = best if best is not None and gap >= 2 else start
    la2 = la[:3] + [alt]
    check = sum(1 for i, r in enumerate(A) if TH.tier_of(i + 1, la) != int(r["a_tier"]))
    changed = []
    for i, r in enumerate(A):
        a1, a2, p = TH.tier_of(i + 1, la), TH.tier_of(i + 1, la2), int(r["p_tier"])
        c1 = a1 - (1 if a1 - p > 0 else -1) if abs(a1 - p) >= 2 else a1
        c2 = a2 - (1 if a2 - p > 0 else -1) if abs(a2 - p) >= 2 else a2
        if c1 != c2:
            changed.append((r["name"], adp_of(r), c1, c2))
    return la[3], alt, gap, changed, check


if __name__ == "__main__":
    nights = sorted({n[0] for n in NW})
    pods = collections.Counter(NW[(d, "am")][0]["podv"] if (d, "am") in NW else NW[(d, "pm")][0]["podv"] for d in nights)
    print("# Season tests on the tiers (all pairs, by nights)\n")
    print("%d nights (%s to %s; %d six-drafter, %d four-drafter). Morning projection: ours at the AM lock as it stood "
          "(before 10-28 the morning file); afternoon: ETR's upload at the PM lock. Tiers: the button rebuilt at each lock "
          "(tier_history.csv). Players who didn't play are left out. Every pair in the tier, only those the two orders "
          "put differently; a night goes to the order with more of its pairs right.\n" % (
              len(nights), nights[0], nights[-1], pods[6], pods[4]))
    R = {}
    for w, proj_name in (("am", "ours"), ("pm", "ETR")):
        R[("t1", w)] = (proj_name, compare(w, [1], PROJ, ADP))
        R[("t2", w)] = (proj_name, compare(w, [2], PROJ, ADP))
        R[("t2e", w)] = (proj_name, compare(w, [2], elite_break, ADP))
        R[("t3", w)] = (proj_name, compare(w, [3], shared, ADP))
        R[("t4", w)] = (proj_name, compare(w, [4], shared, ADP))
        R[("4a", w)] = (proj_name, boundary(w, t4_value, t3_pricey))
        R[("4b", w)] = (proj_name, boundary(w, t5_top3, t4_pricey))
    json_out = {"%s:%s" % k: v[1] for k, v in R.items()}
    import json
    json.dump(json_out, open(sys.argv[1], "w"), indent=1)
    print(HEAD)
    for w, wl in (("am", "morning"), ("pm", "afternoon")):
        p = R[("t1", w)][0]
        print(line("1. T1, " + wl, p, "ADP", R[("t1", w)][1]))
        print(line("2. T2, " + wl, p, "ADP", R[("t2", w)][1]))
        print(line("2. T2 elite break, " + wl, "ADP to pick X, then " + p, "ADP", R[("t2e", w)][1]))
        print(line("3. T3, " + wl, "shared sort", "ADP", R[("t3", w)][1]))
        print(line("3. T4, " + wl, "shared sort", "ADP", R[("t4", w)][1]))
        print(line("4a. T4 VALUE vs T3 PRICEY, " + wl, "T4 VALUE first", "T3 PRICEY first", R[("4a", w)][1]))
        print(line("4b. T5 top 3 vs T4 PRICEY, " + wl, "T5 top 3 first", "T4 PRICEY first", R[("4b", w)][1]))
    print("\n## 5. The T4/T5 line\n")
    diff, ex, tot, bad = 0, [], 0, 0
    for night in sorted(NW):
        now, alt, gap, changed, check = line5(night)
        tot += 1
        bad += check
        if now != alt:
            diff += 1
            ex.append((night, now, alt, gap, changed))
    print("Line differs on %d of %d night-windows (rebuild check: %d players off the stored ADP tier)." % (diff, tot, bad))
    for night, now, alt, gap, changed in ex:
        print("- %s %s: today's line after pick %d, the new one after %d (%s); tier changes: %s" % (
            night[0], night[1], now, alt, "gap %.1f" % gap if gap >= 2 else "no 2-pick gap, start of round 6",
            "; ".join("%s (ADP %.1f) T%d->T%d" % c for c in changed) or "none"))
