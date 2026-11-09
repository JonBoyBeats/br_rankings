"""NBA swaps: what Underdog did with every drafted player ruled out before his game, from the contest leaderboards.

Underdog swaps a drafted player ruled out before his game to the highest-ranked player left undrafted in that pod
by the drafter's own rankings at swap time. The leaderboards (analysis/nba/contests/*.csv.gz, scripts/nba_contests.py)
show final rosters, and a swapped-in player carries no draft ADP: that blank is how a swap is found here.

Each swap is credited to the ruled-out player it replaced: among the night's players who logged 0 minutes for a
team that played, the one nearest in ADP to the team's missing slot. The slot is found by fitting the team's drafted
picks to a snake draft (its seat and which rounds are missing, least total ADP distance); the candidate's distance is
the nearest of his ADPs that day (AM, PM, ETR upload, close: a player's ADP at draft and at lock can sit in different
rounds). Each ruled-out player is credited at most once per pod (he was drafted by one team there) and never when he is on a
roster in that pod; the pod's matching with the least total distance is taken. A swap stays unattributed when no
candidate is within a round (pod picks) of its slot, or another matching within a pick (MARGIN) of the best gives its
team different players.

Prints, for every night with contests on file: teams and swaps; ruled-out players still on a final roster (not
swapped, so a real 0); when swaps happen (the swapped-in player's tip against the ruled-out player's); and for each
ruled-out player: how many swaps, where they landed, the swaps' points, his tier and tag at each lock
(tier_history.csv), and how many swaps landed on his own teammates. Writes analysis/nba/report/swaps.csv
(one row per ruled-out player and target).

  python3 scripts/nba_swaps.py
"""
import collections, csv, datetime as dt, glob, gzip, itertools, json, math, os, urllib.request

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NBA = os.path.join(HERE, "analysis", "nba")
TIPS = os.path.join(NBA, "contests", "tips.json")
OUT = os.path.join(NBA, "report", "swaps.csv")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=%s"
EXCLUDED = {    # nights left uncredited on purpose, and out of every swap-specific test (their scratches score the season's average swap)
    "2026-11-01": "Obi Toppin (ADP 23.1) and Jakob Poeltl (23.4) both sat, 0.3 picks apart: ADP can't tell which one a swap replaced",
}
MARGIN = 1.0      # a credit needs its matching to beat, by this many picks, every matching that gives the team other players
TEAM = {"SA": "SAS", "NY": "NYK", "GS": "GSW", "NO": "NOP", "UTAH": "UTA", "WSH": "WAS"}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def tips(day):
    """{team: tip time (UTC)} for the Pacific day, from ESPN's scoreboard (cached in tips.json)."""
    cache = json.load(open(TIPS)) if os.path.exists(TIPS) else {}
    if day not in cache:
        out = {}
        for d in (day, (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()):   # late tips are the next UTC day
            for e in json.load(urllib.request.urlopen(ESPN % d.replace("-", ""), timeout=30)).get("events", []):
                t = dt.datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
                if (t - dt.timedelta(hours=8)).date().isoformat() != day:
                    continue
                for c in e["competitions"][0]["competitors"]:
                    a = c["team"]["abbreviation"]
                    out[TEAM.get(a, a)] = t.isoformat()
        cache[day] = out
        json.dump(cache, open(TIPS, "w"), indent=1, sort_keys=True)
    return {k: dt.datetime.fromisoformat(v) for k, v in cache[day].items()}


def snake(r, k, pod):
    """Pick number of seat k (1..pod) in round r (1..6) of a snake draft."""
    return (r - 1) * pod + k if r % 2 else r * pod - k + 1


def slots(adps, nsw, pod):
    """The missing slots' pick numbers: the seat and missing rounds that fit the drafted ADPs (sorted) best."""
    best = None
    for k in range(1, pod + 1):
        for miss in itertools.combinations(range(1, 7), nsw):
            rounds = [r for r in range(1, 7) if r not in miss][:len(adps)]
            cost = sum(abs(a - snake(r, k, pod)) for a, r in zip(adps, rounds))
            if best is None or cost < best[0]:
                best = (cost, [snake(r, k, pod) for r in miss])
    return best[1]


def credit_pod(teams, pod, out):
    """{draft_id: [ruled-out players]} for one pod's teams with swaps [(draft_id, drafted ADPs, n swaps)]: each team's
    missing slots matched to the ruled-out players nearest in ADP, every player used once in the pod (he was drafted by
    one team) and only within a round (pod picks) of the slot. The matching with the least total distance is taken; a
    team is left out when it can't be matched in range, or when another matching within MARGIN picks of the best gives it
    different players."""
    dist = lambda o, x: min(abs(v - x) for v in out[o]["adps"])
    opts = []
    for did, adps, nsw in teams:
        sl = slots(adps, nsw, pod)
        near = sorted((o for o in out if all(dist(o, x) <= pod for x in sl)), key=lambda o: sum(dist(o, x) for x in sl))[:nsw + 3]
        o = [(sum(dist(c, x) for c, x in zip(perm, sl)), perm) for perm in itertools.permutations(near, nsw)]
        opts.append(o + [((pod + 1) * nsw, None)])            # unmatched costs more than any match in range
    def search(bound):
        """Every matching costing at most bound (None: find the cheapest), as (cost, [perm per team])."""
        found, lim = [], [bound]
        def go(i, used, cost, pick):
            if lim[0] is not None and cost > lim[0]:
                return
            if i == len(teams):
                if bound is None:
                    lim[0] = cost
                found.append((cost, list(pick)))
                return
            for c, perm in opts[i]:
                if perm is None or not used & set(perm):
                    go(i + 1, used | set(perm or ()), cost + c, pick + [perm])
        go(0, frozenset(), 0, [])
        return found
    best = min(search(None), key=lambda x: x[0])
    near_best = search(best[0] + MARGIN)
    return {did: best[1][i] for i, (did, _, _) in enumerate(teams)
            if best[1][i] is not None and all(set(m[i] or ()) == set(best[1][i]) for _, m in near_best)}


def night(day):
    path = glob.glob(os.path.join(NBA, "daily", "%s_*_main.csv" % day))
    if not path:
        return None
    rows = {r["player_id"]: r for r in csv.DictReader(open(path[0]))}
    hist = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(NBA, "report", "tier_history.csv"))):
        if r["date"] == day:
            hist[r["player_id"]][r["window"]] = r
    contests = sorted(glob.glob(os.path.join(NBA, "contests", "%s_*.csv.gz" % day)))
    teams = [t for f in contests for t in csv.DictReader(gzip.open(f, "rt"))]
    if not teams:
        return None
    pod = 4 if max((num(r["adp_close"]) or 0) for r in rows.values()) <= 28 else 6
    played = {r["team"] for r in rows.values() if num(r["min"])}
    last_adp = lambda r: next((num(r.get(c)) for c in ("adp_close", "adp_pm", "adp_etr", "adp_am") if num(r.get(c)) is not None), None)
    day_adps = lambda r: [num(r.get(c)) for c in ("adp_am", "adp_pm", "adp_etr", "adp_close") if num(r.get(c)) is not None]
    out = {p: dict(r, adp_out=last_adp(r), adps=day_adps(r)) for p, r in rows.items() if r["min"] == "0.0" and r["team"] in played and last_adp(r) is not None}
    tip = tips(day)
    swaps, unattributed, kept, credited = collections.defaultdict(list), 0, collections.Counter(), []
    pods = collections.defaultdict(list)
    for t in teams:
        pods[t["draft_id"]].append(t)
    for did, pts in pods.items():
        roster = {t["p%d" % i] for t in pts for i in range(1, 7) if t["p%d" % i] and num(t["adp%d" % i]) is not None}
        for p in roster & set(out):
            kept[p] += 1                           # a ruled-out player still on a final roster: not swapped
        need = {t["username"] + str(i): t for i, t in enumerate(pts) if any(t["p%d" % k] and num(t["adp%d" % k]) is None for k in range(1, 7))}
        if not need:
            continue
        if day in EXCLUDED:
            unattributed += sum(1 for t in need.values() for i in range(1, 7) if t["p%d" % i] and num(t["adp%d" % i]) is None)
            continue
        cands = {o: r for o, r in out.items() if o not in roster}
        got = credit_pod([(k, sorted(num(t["adp%d" % i]) for i in range(1, 7) if num(t["adp%d" % i]) is not None),
                           sum(1 for i in range(1, 7) if t["p%d" % i] and num(t["adp%d" % i]) is None)) for k, t in need.items()], pod, cands)
        for k, t in need.items():
            sw = [t["p%d" % i] for i in range(1, 7) if t["p%d" % i] and num(t["adp%d" % i]) is None]
            if k not in got:
                unattributed += len(sw)
                continue
            # which out player went to which swapped-in pick on a two-swap team is arbitrary: paired in ADP order
            for o, x in zip(sorted(got[k], key=lambda o: out[o]["adp_out"]), sw):
                swaps[o].append(x)
                credited.append({"out": o, "swap": x, "draft_id": t["draft_id"], "contest_id": t["contest_id"],
                                 "username": t["username"], "team": t})
    return {"day": day, "rows": rows, "hist": hist, "teams": len(teams), "credited": credited, "all_teams": teams, "pods": len({t["draft_id"] for t in teams}),
            "contests": len(contests), "swaps": swaps, "unattributed": unattributed, "kept": kept, "out": out, "tip": tip,
            "n_swaps": sum(1 for t in teams for i in range(1, 7) if t["p%d" % i] and not t["adp%d" % i])}


def main():
    days = sorted({os.path.basename(f)[:10] for f in glob.glob(os.path.join(NBA, "contests", "2026-*_*.csv.gz"))})
    recs, timing = [], collections.Counter()
    for day in days:
        n = night(day)
        if not n:
            continue
        rows, tip = n["rows"], n["tip"]
        if day in EXCLUDED:
            print("\n## %s: EXCLUDED from swap credit and swap-specific tests: %s" % (day, EXCLUDED[day]))
        print("\n## %s: %d contests, %d pods, %d teams, %d swapped-in picks (%d not credited to one player)" % (
            day, n["contests"], n["pods"], n["teams"], n["n_swaps"], n["unattributed"]))
        for o, targets in sorted(n["swaps"].items(), key=lambda x: -len(x[1])):
            r, h = n["out"][o], n["hist"].get(o, {})
            fps = [num(rows[s]["actual"]) for s in targets if s in rows and num(rows[s]["actual"]) is not None]
            mates = sum(1 for s in targets if s in rows and rows[s]["team"] == r["team"])
            top = collections.Counter(targets).most_common(4)
            for s in targets:
                if s in rows and r["team"] in tip and rows[s]["team"] in tip:
                    d = (tip[rows[s]["team"]] - tip[r["team"]]).total_seconds()
                    timing["earlier" if d < 0 else "same" if d == 0 else "later"] += 1
            tier = lambda w: (h.get(w) or {}).get("tier", "-")
            print("- %s (%s, ADP %s; tier AM %s / PM %s; tag AM %s / PM %s / lock %s): %d swaps, kept on %d rosters; "
                  "swap FP mean %.1f (%.1f to %.1f); %d on teammates; to %s" % (
                      r["name"], r["team"], r["adp_out"], tier("am"), tier("pm"), r["injury_am"] or "-", r.get("injury_pm") or "-",
                      r["injury"] or "-", len(targets), n["kept"][o], sum(fps) / len(fps) if fps else 0, min(fps or [0]),
                      max(fps or [0]), mates, ", ".join("%s %d (%.1f)" % (rows[s]["name"], c, num(rows[s]["actual"]) or 0)
                                                        for s, c in top if s in rows)))
            for s, c in collections.Counter(targets).items():
                if s in rows:
                    recs.append({"date": day, "out_id": o, "out": r["name"], "out_team": r["team"], "out_adp": r["adp_out"],
                                 "out_tier_am": tier("am"), "out_tier_pm": tier("pm"), "tag_am": r["injury_am"],
                                 "tag_pm": r.get("injury_pm", ""), "tag_lock": r["injury"], "swap_id": s, "swap": rows[s]["name"],
                                 "swap_team": rows[s]["team"], "teammate": int(rows[s]["team"] == r["team"]),
                                 "swap_adp": rows[s]["adp_close"], "swap_fp": rows[s]["actual"], "teams": c,
                                 "swap_tip_vs_out": "" if r["team"] not in tip or rows[s]["team"] not in tip else
                                 int((tip[rows[s]["team"]] - tip[r["team"]]).total_seconds() // 60)})
        zeros = [(rows[o]["name"], c) for o, c in n["kept"].most_common() if c]
        print("  Ruled out but still on a final roster (scored 0): %s" % (", ".join("%s %d" % z for z in zeros) or "none"))
    print("\nSwap timing, credited swaps: the swapped-in player's game tipped earlier than the ruled-out player's %d, "
          "at the same time %d, later %d" % (timing["earlier"], timing["same"], timing["later"]))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader()
        w.writerows(recs)
    print("%d rows -> %s" % (len(recs), os.path.relpath(OUT, HERE)))


if __name__ == "__main__":
    main()
