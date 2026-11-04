"""NBA forward tests on the contests: the checks the contest side asked the morning report to keep (2026-11-04),
each night's numbers kept in analysis/nba/report/forward_tests.json so the running tallies don't re-read every
night's leaderboards. Printed as part of the Field section (scripts/nba_field.py).

Pre-registered before any of these nights were seen: slates FORWARD_FROM to FORWARD_TO (4 weeks), the flagship
contest each night, 4- and 6-drafter slates apart. Ranges come from resampling whole nights.

  1 Turns       2/3 turn: for each of the night's top 3 by closing ADP, his teams with the most-owned round 2-3 pair
                (ranks pod+1..3*pod) against his teams with any other such pair. 1/2 turn: the most-owned pair of
                ranks pod-1..pod+2 against teams with another pair there. Top-1% rate and points of each, and on
                the cases where the most-owned combo outscored the rest, the top-1% rate of each (the crowding
                check). A crowding penalty is real only if, on those cases, the most-owned combo's top-1% rate
                stays below the rest's with the 90% range of the difference below zero.
  2 Boom bump   the board's Boom with and without the peer-break bump (nbaPeerShift in index.html; pbr in the
                morning file) for players it moved 2+ points, against the rest: predicted against the rate of
                actual booms (a night 10+ over his bar, as the board defines Boom), on ETR's last number at lock.
  3 Ownership   the contest side's study as run (scripts/nba_tiebreak_study.py: closing ADP within 4, ETR
  tiebreak      medians within 2, drafted% 10+ points apart and both at least 2%). Graded on the top-1% rate of
                the teams carrying the lower- against the higher-drafted player; who outscored is context only
                (it swings 37-58% with the cut: about a coin flip). In sample both windows ran about +0.2
                percentage points for the lower one, range touching zero. Bar, set 2026-11-04 before the window:
                at its end, the lean holds if the 80% range of the difference is above zero (backed by the same
                direction in sample), goes against it if below, else not settled.
  4 Your teams  breakers a team (yours, the top 1%, the field); picks drafted in under half the pods, a team (yours,
                the field); and of your teams with a top-3 player and a round 2-3 pair, how many took his most-owned
                pair, a rarer one (within 2 projected points of it at half its share or less) or another.
  5 Q tags      players Questionable or Doubtful at Lock AM: played or sat, points over his ADP band's average
                (his closing price), and the top-1% rate of teams that drafted him before noon PT against after.
  6 Risers      waits on two weeks of the poller's hourly contest counts (from 2026-11-04).

A breaker scored at least the 90th percentile of the priced players in his ADP round band that night (the
contest side's definition, nba_contests.py).
"""
import json, math, os, random, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import nba_contests as C   # noqa: E402
import nba_report as R     # noqa: E402
import nba_tiebreak_study as TB   # noqa: E402  the ownership tiebreak, the contest side's definition as run

FORWARD_FROM, FORWARD_TO = "2026-11-05", "2026-12-02"
STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "nba", "report", "forward_tests.json")
QTAGS = ("Questionable", "Doubtful")


def ratio(a, b):
    return a / b if b else None


def boot(nights, fn, level=0.8):
    """`level` range of fn over nights resampled, or None with fewer than 3."""
    if len(nights) < 3:
        return None
    rnd = random.Random(7)
    vals = sorted(v for v in (fn([rnd.choice(nights) for _ in nights]) for _ in range(500)) if v is not None)
    tail = int(len(vals) * (1 - level) / 2)
    return (vals[tail], vals[len(vals) - 1 - tail]) if vals else None


# ---------------------------------------------------------------- one night
def night(date, teams, pod, rows, times, mirror):
    """This night's numbers for every test. teams: the flagship's; rows: the record's rows by player id."""
    n, cut = len(teams), math.ceil(len(teams) / 100)
    top = lambda t: t["place"] <= cut
    priced = {p: r for p, r in rows.items() if r["adp_close"] is not None}
    rank = {p: i + 1 for i, (_, p) in enumerate(sorted((r["adp_close"], p) for p, r in priced.items()))}
    proj = {p: r["etr_last"] for p, r in rows.items() if r["etr_last"] is not None}
    # breakers, as nba_contests.py: the 90th percentile of the priced players' points in his round band (closing ADP)
    by_band = defaultdict(list)
    for r in priced.values():
        if r["actual"] is not None:
            by_band[math.ceil(r["adp_close"] / pod)].append(r["actual"])
    p90 = {b: sorted(v)[int(0.9 * (len(v) - 1))] for b, v in by_band.items()}
    brk = {p for p, r in priced.items() if r["actual"] is not None and r["actual"] >= p90[math.ceil(r["adp_close"] / pod)]}
    pods = defaultdict(set)
    for t in teams:
        pods[t["draft_id"]].update(t["picks"])
    own = {p: 100 * sum(1 for s in pods.values() if p in s) / len(pods) for p in priced}
    out = {"pod": pod, "teams": n}

    # 1 turns
    def case(pop, rest):
        g = lambda ts: [len(ts), sum(1 for t in ts if top(t)), sum(t["points"] for t in ts)]
        return {"pop": g(pop), "rest": g(rest)}

    def pairs_in(t, lo, hi):
        mid = sorted(p for p in t["picks"] if lo <= rank.get(p, 0) <= hi)
        return {(a, b) for i, a in enumerate(mid) for b in mid[i + 1:]}
    t23, rarer23 = [], {}
    for anchor in [p for p, r in rank.items() if r <= 3]:
        ts = [t for t in teams if anchor in t["picks"]]
        held = {id(t): pairs_in(t, pod + 1, 3 * pod) for t in ts}
        cnt = defaultdict(int)
        for ps in held.values():
            for k in ps:
                cnt[k] += 1
        if not cnt:
            continue
        top_pair = max(cnt, key=cnt.get)
        pop = [t for t in ts if top_pair in held[id(t)]]
        rest = [t for t in ts if held[id(t)] and top_pair not in held[id(t)]]
        t23.append(dict(case(pop, rest), anchor=rows[anchor]["name"], combo=[rows[p]["name"] for p in top_pair]))
        pp = lambda k: sum(proj.get(p, 0) for p in k)
        rarer23[anchor] = (top_pair, {k for k, v in cnt.items() if k != top_pair and abs(pp(k) - pp(top_pair)) <= 2
                                      and v <= cnt[top_pair] / 2}, held)
    held12 = {id(t): pairs_in(t, pod - 1, pod + 2) for t in teams}
    cnt12 = defaultdict(int)
    for ps in held12.values():
        for k in ps:
            cnt12[k] += 1
    t12 = []
    if cnt12:
        top12 = max(cnt12, key=cnt12.get)
        t12.append(dict(case([t for t in teams if top12 in held12[id(t)]], [t for t in teams if held12[id(t)] and top12 not in held12[id(t)]]),
                        combo=[rows[p]["name"] for p in top12]))
    out["turns"] = {"2/3": t23, "1/2": t12}

    # 2 Boom peer bump
    out["boom"] = boom_check(date, rows, mirror)

    # 3 ownership tiebreak: the contest side's study, as run (scripts/nba_tiebreak_study.py), so the definition is theirs
    out["ties"] = TB.night_pairs(date)

    # 4 your teams
    mine = [t for t in teams if t["username"] == C.ME]
    best = [t for t in teams if top(t)]
    nb = lambda ts: [len(ts), sum(sum(1 for p in t["picks"] if p in brk) for t in ts)]
    low = lambda ts: [len(ts), sum(sum(1 for p in t["picks"] if p in own and own[p] < 50) for t in ts)]
    took = {"most-owned": 0, "rarer": 0, "other": 0}
    for t in mine:
        for anchor, (top_pair, rarer, held) in rarer23.items():
            if anchor in t["picks"]:
                hs = pairs_in(t, pod + 1, 3 * pod)
                if hs:
                    took["most-owned" if top_pair in hs else "rarer" if hs & rarer else "other"] += 1
    out["mine"] = {"breakers": {"mine": nb(mine), "top1": nb(best), "field": nb(teams)},
                   "low_drafted": {"mine": low(mine), "field": low(teams)}, "turn23": took}

    # 5 Q tags at Lock AM
    means = C.band_means(pod)
    q = []
    for p, r in priced.items():
        if r.get("injury_am") in QTAGS:
            ts = [t for t in teams if p in t["picks"]]
            early = [t for t in ts if id(t) in times and times[id(t)].astimezone(C.PT).hour < C.AM_UNTIL]
            late = [t for t in ts if id(t) in times and times[id(t)].astimezone(C.PT).hour >= C.AM_UNTIL]
            played = (r["min"] or 0) > 0
            q.append({"name": r["name"], "tag": r["injury_am"], "played": played,
                      "value": round(r["actual"] - means[math.ceil(r["adp_close"] / pod)], 1) if played and r["actual"] is not None else None,
                      "early": [len(early), sum(1 for t in early if top(t))], "late": [len(late), sum(1 for t in late if top(t))]})
    out["q"] = q
    return out


def boom_check(date, rows, mirror):
    """[(Boom with the bump, without it, boomed)] for every player with a bump and a Boom, on ETR's last number;
    None if there's no mirror or the morning file had no pbr that day."""
    if not mirror:
        return None
    import nba_boom_ties as B
    mo = B.morning_at(mirror, date)
    if not any("pbr" in m for m in mo.values()):
        return None
    items = []
    for r in rows.values():
        m = mo.get(B.norm(r["name"]))
        if r["adp_close"] is None or r["etr_last"] is None or r["actual"] is None or not (r["min"] or 0) > 0 or not m or m.get("ppm") is None:
            continue
        items.append({"adp": r["adp_close"], "x": B.median_of_proj(r["etr_last"]), "m": m, "r": r})
    if len(items) < 13:
        return None
    bars = B.bars(items)
    out = []
    for it in items:
        b0 = B.chance(B.BOOM, it["x"], bars[id(it)], it["m"])
        pbr = it["m"].get("pbr")
        shift = 0.0
        if pbr and pbr[1] >= 8:
            rate = (pbr[0] + 0.089 * 10) / (pbr[1] + 10)
            shift = 1.52 * (rate - 0.089)
        b1 = 1 / (1 + math.exp(-(math.log(b0 / (1 - b0)) + shift)))
        out.append([round(b1, 4), round(b0, 4), it["r"]["actual"] >= bars[id(it)] + 10])
    return out


# ---------------------------------------------------------------- saving and the running lines
def load_store():
    return json.load(open(STORE)) if os.path.exists(STORE) else {}


def record(date, numbers):
    store = load_store()
    store[date] = numbers
    json.dump(store, open(STORE, "w"), indent=1, sort_keys=True)


def lines(date, pod):
    """The forward tests, last night and running over the pre-registered window, for slates with this pod size."""
    store = load_store()
    ds = sorted(d for d, v in store.items() if FORWARD_FROM <= d <= min(date, FORWARD_TO) and v["pod"] == pod)
    last = store.get(date) if date in ds else None
    out = ["### 10. Forward tests (pre-registered 2026-11-04; slates %s to %s, %d-drafter)" % (FORWARD_FROM, FORWARD_TO, pod), ""]
    if not ds:
        return out + ["No forward nights yet (the window starts %s)." % FORWARD_FROM, ""]
    out.append("%d nights in so far. Ranges: 80%%, resampling nights; the turns' crowding bar uses 90%%." % len(ds))
    out.append("")

    # 1 turns
    out += ["**Turns: the most-owned combo against the rest**", "",
            "| Turn | Cases | Top 1%: most-owned / rest | Points: most-owned - rest | Cases it outscored | On those: top 1% most-owned / rest | Crowding penalty? |",
            "|---|---|---|---|---|---|---|"]
    for k in ("2/3", "1/2"):
        cases = lambda xs: [(d, c) for d in xs for c in store[d]["turns"][k]]
        def rate(cs, side):
            return ratio(sum(c[side][1] for _, c in cs), sum(c[side][0] for _, c in cs))
        def pts(cs):
            return [c["pop"][2] / c["pop"][0] - c["rest"][2] / c["rest"][0] for _, c in cs if c["pop"][0] and c["rest"][0]]
        outscored = lambda cs: [(d, c) for d, c in cs if c["pop"][0] and c["rest"][0] and c["pop"][2] / c["pop"][0] > c["rest"][2] / c["rest"][0]]
        cs = cases(ds)
        if not cs:
            continue
        diff = lambda xs: (lambda o: None if not o or rate(o, "pop") is None or rate(o, "rest") is None else rate(o, "pop") - rate(o, "rest"))(outscored(cases(xs)))
        g = boot(ds, diff, 0.9)
        o = outscored(cs)
        verdict = ("verdict when the window ends" if date < FORWARD_TO else "yes" if g and g[1] < 0 else "no")
        out.append("| %s | %d | %s / %s | %+.1f | %d | %s / %s | %s%s |" % (
            k, len(cs), pct(rate(cs, "pop")), pct(rate(cs, "rest")), sum(pts(cs)) / len(pts(cs)) if pts(cs) else 0, len(o),
            pct(rate(o, "pop")) if o else "-", pct(rate(o, "rest")) if o else "-", verdict,
            " (90%% range of the difference: %+.2f to %+.2f percentage points)" % (100 * g[0], 100 * g[1]) if g else ""))
    if last:
        out.append("")
        out.append("Last night: " + "; ".join("%s turn, %s: %s (%d teams, %d top 1%%, %.1f pts) vs the rest (%d, %d, %.1f)" % (
            k, " + ".join(([c["anchor"]] if "anchor" in c else []) + c["combo"]), "most-owned", c["pop"][0], c["pop"][1],
            c["pop"][2] / max(1, c["pop"][0]), c["rest"][0], c["rest"][1], c["rest"][2] / max(1, c["rest"][0]))
            for k in ("1/2", "2/3") for c in last["turns"][k]) + ".")
    out.append("")

    # 2 Boom bump
    rowsb = [(d, x) for d in ds for x in (store[d]["boom"] or [])]
    out.append("**Boom peer bump: calibration**")
    out.append("")
    if not rowsb:
        out += ["No nights with pbr in the morning file yet.", ""]
    else:
        moved = [x for _, x in rowsb if abs(x[0] - x[1]) >= 0.02]
        rest = [x for _, x in rowsb if abs(x[0] - x[1]) < 0.02]
        line = lambda xs: "%d players: Boom %.0f%% with the bump (%.0f%% without), %.0f%% boomed" % (
            len(xs), 100 * sum(x[0] for x in xs) / len(xs), 100 * sum(x[1] for x in xs) / len(xs), 100 * sum(x[2] for x in xs) / len(xs)) if xs else "none"
        brier = lambda xs, i: sum((x[i] - x[2]) ** 2 for x in xs) / len(xs) if xs else None
        out += ["- Moved 2+ points: %s; Brier %s with the bump, %s without (lower is better)." % (
            line(moved), R.fmt(brier(moved, 0), "%.4f"), R.fmt(brier(moved, 1), "%.4f")),
                "- The rest: %s." % line(rest), ""]

    # 3 ownership tiebreak, graded on the top-1% rate of the teams carrying each (the points half isn't a finding)
    ts = [x for d in ds for x in store[d]["ties"]]
    out.append("**Ownership tiebreak: the lower- against the higher-drafted player in tied pairs**")
    out.append("")
    if not ts:
        out += ["No tied pairs yet.", ""]
    else:
        def dif(dd):
            xs = [x for d in dd for x in store[d]["ties"]]
            lt, ln, ht, hn = (sum(x[k] for x in xs) for k in ("lo_t1", "lo_n", "hi_t1", "hi_n"))
            return lt / ln - ht / hn if ln and hn else None
        lt, ln, ht, hn = (sum(x[k] for x in ts) for k in ("lo_t1", "lo_n", "hi_t1", "hi_n"))
        g80, g90 = boot(ds, dif), boot(ds, dif, 0.9)
        verdict = ("verdict when the window ends" if date < FORWARD_TO else
                   "the lean holds" if g80 and g80[0] > 0 else "against the lean" if g80 and g80[1] < 0 else "not settled")
        out += ["%d pairs: teams carrying the lower-drafted player finished top 1%% %s, the higher %s (80%% range of the difference "
                "%s); %s. Points, context only: the lower one outscored %.0f%%, breakers %.0f%% vs %.0f%%." % (
                    len(ts), pct(ratio(lt, ln)), pct(ratio(ht, hn)),
                    "%+.2f to %+.2f percentage points" % (100 * g80[0], 100 * g80[1]) if g80 else "from 3 nights", verdict,
                    100 * sum(x["lo_wins"] for x in ts) / len(ts), 100 * sum(x["lo_brk"] for x in ts) / len(ts),
                    100 * sum(x["hi_brk"] for x in ts) / len(ts)), ""]

    # 4 your teams
    agg = lambda path: [sum(store[d]["mine"][path[0]][path[1]][i] for d in ds) for i in (0, 1)]
    per = lambda a: "%.2f" % (a[1] / a[0]) if a[0] else "-"
    tk = {k: sum(store[d]["mine"]["turn23"][k] for d in ds) for k in ("most-owned", "rarer", "other")}
    lastm = last["mine"] if last else None
    out += ["**Your teams**", "",
            "| | Last night | Running |", "|---|---|---|",
            "| Breakers a team: yours | %s | %s |" % (per(lastm["breakers"]["mine"]) if lastm else "-", per(agg(("breakers", "mine")))),
            "| Breakers a team: top 1%% | %s | %s |" % (per(lastm["breakers"]["top1"]) if lastm else "-", per(agg(("breakers", "top1")))),
            "| Breakers a team: field | %s | %s |" % (per(lastm["breakers"]["field"]) if lastm else "-", per(agg(("breakers", "field")))),
            "| Picks under 50%% drafted a team: yours | %s | %s |" % (per(lastm["low_drafted"]["mine"]) if lastm else "-", per(agg(("low_drafted", "mine")))),
            "| Picks under 50%% drafted a team: field | %s | %s |" % (per(lastm["low_drafted"]["field"]) if lastm else "-", per(agg(("low_drafted", "field")))),
            "| 2/3 turn: most-owned / rarer / other pair | %s | %d / %d / %d |" % (
                " / ".join(str(lastm["turn23"][k]) for k in ("most-owned", "rarer", "other")) if lastm else "-", tk["most-owned"], tk["rarer"], tk["other"]),
            ""]

    # 5 Q tags
    qs = [(d, x) for d in ds for x in store[d]["q"]]
    out.append("**Questionable or Doubtful at Lock AM**")
    out.append("")
    if not qs:
        out += ["None yet.", ""]
    else:
        pl = [x for _, x in qs if x["played"]]
        e = [sum(x["early"][i] for _, x in qs) for i in (0, 1)]
        l = [sum(x["late"][i] for _, x in qs) for i in (0, 1)]
        out += ["%d tagged: %d played (%s over their closing price on average), %d sat. Teams that drafted them before noon PT finished "
                "top 1%% %s (%d teams), after noon %s (%d). Underdog swaps a ruled-out player, so the sat ones barely show in the "
                "leaderboards." % (len(qs), len(pl), R.fmt(sum(x["value"] for x in pl if x["value"] is not None) / len(pl) if pl else None, "%+.1f"),
                                   len(qs) - len(pl), pct(ratio(e[1], e[0])), e[0], pct(ratio(l[1], l[0])), l[0])]
        if last and last["q"]:
            out.append("Last night: " + "; ".join("%s (%s) %s%s" % (x["name"], x["tag"], "played" if x["played"] else "sat",
                                                                     ", %+.1f" % x["value"] if x["value"] is not None else "") for x in last["q"]) + ".")
        out.append("")

    out += ["**Risers**: waits on two weeks of the poller's hourly contest counts (logged from 2026-11-04).", ""]
    return out


def pct(v):
    return "-" if v is None else "%.2f%%" % (100 * v)
