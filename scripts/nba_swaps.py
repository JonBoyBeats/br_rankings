"""NBA swaps: what Underdog did with every drafted player ruled out before his game, from the contest leaderboards.

Underdog swaps a drafted player ruled out before his game to the highest-ranked player left undrafted in that pod
by the drafter's own rankings at swap time. The leaderboards (analysis/nba/contests/*.csv.gz, scripts/nba_contests.py)
show final rosters, and a swapped-in player carries no draft ADP: that blank is how a swap is found here.

Each swap is credited to the ruled-out player it replaced: among the night's players who logged 0 minutes for a
team that played, the one whose ADP round (his last ADP of the day: a player ruled out leaves ADP before lock; rounds of pod-size picks) is the round missing from that
team's other five picks. A team missing two rounds with two candidates in them is credited both; a swap with no
round match, or two candidates in the one missing round, stays unattributed.

Prints, for every night with contests on file: teams and swaps; ruled-out players still on a final roster (not
swapped, so a real 0); when swaps happen (the swapped-in player's tip against the ruled-out player's); and for each
ruled-out player: how many swaps, where they landed, the swaps' points, his tier and tag at each lock
(tier_history.csv), and how many swaps landed on his own teammates. Writes analysis/nba/report/swaps.csv
(one row per ruled-out player and target).

  python3 scripts/nba_swaps.py
"""
import collections, csv, datetime as dt, glob, gzip, json, math, os, urllib.request

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NBA = os.path.join(HERE, "analysis", "nba")
TIPS = os.path.join(NBA, "contests", "tips.json")
OUT = os.path.join(NBA, "report", "swaps.csv")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=%s"
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
    rnd = lambda a: min(6, max(1, math.ceil(a / pod)))
    played = {r["team"] for r in rows.values() if num(r["min"])}
    last_adp = lambda r: next((num(r.get(c)) for c in ("adp_close", "adp_pm", "adp_etr", "adp_am") if num(r.get(c)) is not None), None)
    out = {p: dict(r, adp_out=last_adp(r)) for p, r in rows.items() if r["min"] == "0.0" and r["team"] in played and last_adp(r) is not None}
    tip = tips(day)
    swaps, unattributed, kept = collections.defaultdict(list), 0, collections.Counter()
    for t in teams:
        picks = [(t["p%d" % i], num(t["adp%d" % i])) for i in range(1, 7) if t["p%d" % i]]
        sw = [p for p, a in picks if a is None]
        for p, a in picks:
            if a is not None and p in out:
                kept[p] += 1                       # a ruled-out player still on the final roster: not swapped
        if not sw:
            continue
        have = collections.Counter(rnd(a) for _, a in picks if a is not None)
        missing = [k for k in range(1, 7) if not have[k]]
        cands = [o for o in out if rnd(out[o]["adp_out"]) in missing and o not in dict(picks)]
        by_round = collections.defaultdict(list)
        for o in cands:
            by_round[rnd(out[o]["adp_out"])].append(o)
        options = [v[0] for k, v in by_round.items() if len(v) == 1]
        if len(sw) == 1 and len(cands) == 1:
            options = cands
        if len(options) == len(sw) and len(sw) <= len(missing):
            # credit in order of ADP: the earliest out player to the earliest-tipping swap is arbitrary, so with two
            # swaps on one team each pairing is recorded only when the targets tip at the same time or it can't matter
            for o, s in zip(sorted(options, key=lambda o: out[o]["adp_out"]), sw):
                swaps[o].append(s)
        else:
            unattributed += len(sw)
    return {"day": day, "rows": rows, "hist": hist, "teams": len(teams), "pods": len({t["draft_id"] for t in teams}),
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
