"""NBA swap lock grading: on nights you pressed the board's Swap button, each of your swaps against the swap the PM
list would have made (2026-11-13).

Underdog swaps a drafted player ruled out before his game to the highest-ranked player left undrafted in that pod by
your rankings at swap time. On the leaderboards a swapped-in pick carries no draft ADP (scripts/nba_swaps.py), so each
of your teams' swaps is a blank-ADP pick. For each one, in that pod:

  swap list   the first player on your swap lock (swap_rank in the daily record) who played, isn't on another roster in
              the pod, and whose game tipped no earlier than the ruled-out player's (Underdog skips a game that has
              started; the ruled-out player is the one scripts/nba_swaps.py credits the swap to): what the Swap button's
              list gives, checked against the player Underdog actually put in
  PM list     the same on your PM lock (pm_rank): what you'd have had without pressing it

Checked on the PM list itself (it should give Underdog's actual swap where the PM lock was the list on Underdog): 24 of
24 on 11-12, 6 of 6 on 11-11, 14 of 16 on 11-10.

Points: the two players' fantasy points. Contest: the team's place and payout with the PM list's player in place of
the one Underdog gave it (the rest of the contest as it finished). A team with two swaps takes each list's first two.
Season to date, nights with a swap lock only (meta.json "swap").

  python3 scripts/nba_swap_grade.py [--dry-run]   (--dry-run: every night with a PM lock and its tiers, the swap list
                                                 built as the button would have: the PM list, T5 down by ETR's final)
"""
import argparse, collections, csv, glob, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_contests as C   # noqa: E402
import nba_swaps as S      # noqa: E402  tip times

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(HERE, "analysis", "nba", "report", "swap_grade.csv")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def night_rows(dry=False):
    """[(date, {player_id: daily row}, swap order, PM order)] for nights with a swap lock (dry run: every night with a PM
    lock and its tiers, the swap order built from it: T1-T4 as locked, T5 down by ETR's final, the unprojected last)."""
    meta = json.load(open(os.path.join(DAILY, "meta.json")))
    out = []
    for path in sorted(glob.glob(os.path.join(DAILY, "*_main.csv"))):
        m = meta.get(os.path.basename(path)) or {}
        if not m.get("swap") and not dry:
            continue
        rows = {r["player_id"]: r for r in csv.DictReader(open(path))}
        if not rows:
            continue
        pm = sorted((p for p, r in rows.items() if num(r.get("pm_rank")) is not None), key=lambda p: num(rows[p]["pm_rank"]))
        if dry:
            starts = ((m.get("pm") or {}).get("tiers")) or []
            if len(starts) < 4:
                continue
            head = [p for p in pm if num(rows[p]["pm_rank"]) < starts[3]]
            tail = [p for p in pm if num(rows[p]["pm_rank"]) >= starts[3]]
            sw = head + sorted([p for p in tail if num(rows[p]["etr_last"]) is not None], key=lambda p: -num(rows[p]["etr_last"])) + \
                [p for p in tail if num(rows[p]["etr_last"]) is None]
        else:
            sw = sorted((p for p, r in rows.items() if num(r.get("swap_rank")) is not None), key=lambda p: num(rows[p]["swap_rank"]))
        if pm and sw:
            out.append((next(iter(rows.values()))["date"], rows, sw, pm))
    return out


def credited_outs():
    """{(date, swapped-in player): [ruled-out players' teams]} from scripts/nba_swaps.py's credits."""
    out = collections.defaultdict(list)
    path = os.path.join(HERE, "analysis", "nba", "report", "swaps.csv")
    if os.path.exists(path):
        for r in csv.DictReader(open(path)):
            out[(r["date"], r["swap_id"])].append(r["out_team"])
    return out


def grade(dry=False):
    swaps, outs_of = [], credited_outs()
    for date, rows, sw, pm in night_rows(dry):
        try:
            tip = S.tips(date)
        except Exception:                              # no tip times: no game-started rule that night
            tip = {}
        played = {p for p, r in rows.items() if (num(r["min"]) or 0) > 0}
        pts = {p: num(r["actual"]) or 0.0 for p, r in rows.items()}
        contests, teams = C.load_night(date)
        for c in contests:
            ts = teams[c["contest_id"]]
            pods = collections.defaultdict(set)
            for t in ts:
                pods[t["draft_id"]].update(t["picks"])
            n = len(ts)
            pay = {}
            for t in ts:
                pay.setdefault(t["place"], t["payout"])
            for t in ts:
                if t["username"] != C.ME:
                    continue
                got = [p for p, a in zip(t["picks"], t["adps"]) if a is None]
                if not got:
                    continue
                taken = pods[t["draft_id"]] - set(got)          # his own swapped-in player was free when the swap ran
                t0 = min((tip[o] for g in got for o in outs_of.get((date, g), []) if o in tip), default=None)

                def first(order, k):
                    return [p for p in order if p in played and p not in taken and
                            (t0 is None or tip.get(rows[p]["team"], t0) >= t0)][:k]
                want_sw, want_pm = first(sw, len(got)), first(pm, len(got))
                if len(want_pm) < len(got):
                    continue
                alt = t["points"] - sum(pts.get(p, 0.0) for p in got) + sum(pts[p] for p in want_pm)
                place_alt = 1 + sum(1 for u in ts if u is not t and u["points"] > alt)
                top10 = math.ceil(n / 10)
                swaps.append({"date": date, "contest": c["contest_id"], "draft_id": t["draft_id"], "swaps": len(got),
                              "underdog": "+".join(rows[p]["name"] if p in rows else p[:8] for p in got),
                              "swap_list": "+".join(rows[p]["name"] for p in want_sw),
                              "pm_list": "+".join(rows[p]["name"] for p in want_pm),
                              "matched": sorted(got) == sorted(want_sw), "differs": sorted(want_sw) != sorted(want_pm),
                              "pts_swap": round(sum(pts.get(p, 0.0) for p in got), 1), "pts_pm": round(sum(pts[p] for p in want_pm), 1),
                              "place": t["place"], "place_pm": place_alt, "teams": n,
                              "payout": t["payout"], "payout_pm": pay.get(place_alt, 0.0),
                              "top10": t["place"] <= top10, "top10_pm": place_alt <= top10})
    return swaps


def season_line(swaps=None):
    """One line for the morning report's Q section."""
    swaps = grade() if swaps is None else swaps
    if not swaps:
        return "Swap button: no swap lock yet. Once you press it after your last draft, each swap is compared here with the one your PM list would have made."
    nights = len({s["date"] for s in swaps})
    d = [s for s in swaps if s["differs"]]
    line = "Swap button: %d of your swaps on %d night%s with a swap lock; the swap list and the PM list picked %s" % (
        len(swaps), nights, "" if nights == 1 else "s", "the same player every time" if not d else "different players on %d" % len(d))
    if d:
        gain = sum(s["pts_swap"] - s["pts_pm"] for s in d)
        places = sum(s["place_pm"] - s["place"] for s in d) / len(d)
        cash = sum(s["payout"] - s["payout_pm"] for s in d)
        flips = sum(1 for s in d if s["top10"] and not s["top10_pm"]) - sum(1 for s in d if s["top10_pm"] and not s["top10"])
        line += ", and on those the swap list's player scored %+.1f a swap (%+.1f in all), the teams finished %.0f places %s, " \
                "%+d top-10%% finish%s and %s$%.0f against the PM list" % (
                    gain / len(d), gain, abs(places), "higher" if places >= 0 else "lower", flips, "" if abs(flips) == 1 else "es",
                    "+" if cash >= 0 else "-", abs(cash))
    matched = sum(1 for s in swaps if s["matched"])
    return line + ". (Underdog's swap matched the swap list on %d of %d: under that, the list wasn't pushed in time or a game had started.)" % (
        matched, len(swaps))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="every night: the swap list built from the PM lock, T5 down by ETR's final")
    a = ap.parse_args()
    swaps = grade(a.dry_run)
    if not a.dry_run:
        cols = ["date", "contest", "draft_id", "swaps", "underdog", "swap_list", "pm_list", "matched", "differs", "pts_swap", "pts_pm",
                "place", "place_pm", "teams", "payout", "payout_pm", "top10", "top10_pm"]
        with open(OUT, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(swaps)
    print(season_line(swaps))


if __name__ == "__main__":
    main()
