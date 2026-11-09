"""NBA swap board backtest (step 7): how good the swaps were, and what the order of your rankings' tail does to them.

A swap goes to the drafter's highest-ranked player left undrafted in that pod whose game hasn't started at the swap
(analysis/nba/report/swaps.csv; nba_swaps.py credits each swap to the player it replaced). The swap time is taken as the
earliest tip among that ruled-out player's swap targets that night (step 3c: a swap only lands on a game not yet
started), else his own tip.

  efficiency    every credited swap against the best undrafted option in its pod by ETR's final projection at the swap
                (eligible: undrafted in the pod, game not started, ETR has him above 0 and he wasn't ruled out): the
                points left on the table, by the ruled-out player's tier, for the field and for your teams (by the window
                you drafted them)
  tie orders    your swapped teams replayed under three orders of the undrafted tail, each the projection order (ETR's
                final) with near-ties (within 2 points) reordered: projection only, ownership lowest first (your habit),
                ownership highest first. For each: the swaps' points, the share of your swapped teams that land on the
                single most-hit target, your exposure to each target (drafted plus swapped, over your teams) and the
                field's drafted% of the targets
  your order    from the orders your board saved to the gist (analysis/nba/daily/<date>_<slate>_orders.json.gz, every
                change, stamped): the order in force at each swap, what it picked, and its points against the
                projection-only order's pick; and how many swaps came after your last change that night
  live moves    how many times you changed your board after the slate locked, and how far

Writes analysis/nba/report/swap_board.md.

  python3 scripts/nba_swap_board.py
"""
import collections, csv, datetime as dt, glob, gzip, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_swaps as S       # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NBA = os.path.join(HERE, "analysis", "nba")
OUT = os.path.join(NBA, "report", "swap_board.md")
ME = "jonboybeats"
AM_UNTIL = 12
num = S.num
TIE = 2.0


def parse(t):
    return dt.datetime.fromisoformat(t.replace("Z", "+00:00"))


def my_draft_times(day):
    out = {}
    p = os.path.join(NBA, "contests", "%s_measures.json" % day)
    if os.path.exists(p):
        for c in json.load(open(p)).get("contests", []):
            for t in c.get("my_teams") or []:
                if t.get("drafted_at"):
                    out[t["draft_id"]] = parse(t["drafted_at"])
    return out


def tier_rows(day):
    out = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(NBA, "report", "tier_history.csv"))):
        if r["date"] == day:
            out[r["window"]][r["player_id"]] = r
    return out


def orders(day):
    p = glob.glob(os.path.join(NBA, "daily", "%s_*_orders.json.gz" % day))
    return json.load(gzip.open(p[0], "rt")) if p else None


def tie_order(pool, rows, drafted, how):
    """The undrafted pool in ETR's final order, near-ties (within TIE points of the group's top) reordered by how."""
    base = sorted(pool, key=lambda p: -(num(rows[p]["etr_last"]) or 0))
    out, i = [], 0
    while i < len(base):
        j, top = i, num(rows[base[i]]["etr_last"]) or 0
        while j + 1 < len(base) and top - (num(rows[base[j + 1]]["etr_last"]) or 0) <= TIE:
            j += 1
        grp = base[i:j + 1]
        if how == "low":
            grp = sorted(grp, key=lambda p: drafted.get(p, 0))
        elif how == "high":
            grp = sorted(grp, key=lambda p: -drafted.get(p, 0))
        out += grp
        i = j + 1
    return out


def main():
    days = sorted({os.path.basename(f)[:10] for f in glob.glob(os.path.join(NBA, "contests", "2026-*_*.csv.gz"))})
    eff = collections.defaultdict(list)            # key -> [points left]
    tie = {h: collections.defaultdict(list) for h in ("proj", "low", "high")}
    tie_targets = {h: collections.Counter() for h in tie}
    tie_nights = {h: [] for h in tie}
    mine_order, after_last, live = [], [], []
    for day in days:
        n = S.night(day)
        if not n or not n["credited"]:
            continue
        rows, tip, out = n["rows"], n["tip"], n["out"]
        hist = tier_rows(day)
        pods = collections.defaultdict(set)
        for t in n["all_teams"]:
            for i in range(1, 7):
                if t["p%d" % i] and t["adp%d" % i]:
                    pods[t["draft_id"]].add(t["p%d" % i])
        targets = collections.defaultdict(list)
        for c in n["credited"]:
            targets[c["out"]].append(c["swap"])
        swap_time = {}
        for o, ts in targets.items():
            tt = [tip[rows[s]["team"]] for s in ts if s in rows and rows[s]["team"] in tip]
            swap_time[o] = min(tt) if tt else tip.get(out[o]["team"])
        sat = {p for p, r in rows.items() if r["min"] == "0.0"}
        drafted_pct = {pid: num(r["drafted"]) or 0 for pid, r in hist.get("pm", {}).items()}
        my_times = my_draft_times(day)
        snaps = orders(day)
        my_teams = collections.defaultdict(list)
        lock = None
        for c in n["credited"]:
            st = swap_time.get(c["out"])
            if st is None or c["swap"] not in rows or num(rows[c["swap"]]["actual"]) is None:
                continue
            elig = [p for p, r in rows.items() if p not in pods[c["draft_id"]] and p not in out and p not in sat
                    and r["team"] in tip and tip[r["team"]] >= st and (num(r["etr_last"]) or 0) > 0]
            if not elig:
                continue
            best = max(elig, key=lambda p: num(rows[p]["etr_last"]))
            left = num(rows[best]["actual"]) - num(rows[c["swap"]]["actual"])
            h = hist.get("pm", {}).get(c["out"]) or hist.get("am", {}).get(c["out"]) or {}
            tier = "T" + (h.get("tier") or "?")
            eff[("all", tier)].append(left)
            eff[("all", "all")].append(left)
            if c["username"] == ME:
                w = my_times.get(c["draft_id"])
                win = "AM" if w and (w - dt.timedelta(hours=8)).hour < AM_UNTIL else "PM" if w else "?"
                eff[("mine", win)].append(left)
                eff[("mine", "all")].append(left)
                my_teams[c["draft_id"]].append((c, elig, st))
        # ---- tie orders and your own order, on your swapped teams
        my_all = [t for t in n["all_teams"] if t["username"] == ME]
        if not my_teams:
            continue
        for h in tie:
            got = collections.Counter()
            for did, lst in my_teams.items():
                for c, elig, st in lst:
                    order = tie_order(elig, rows, drafted_pct, h)
                    pick = order[0]
                    tie[h][day].append(num(rows[pick]["actual"]))
                    got[pick] += 1
            tie_targets[h].update(got)
            tot = sum(got.values())
            top = got.most_common(1)[0] if got else (None, 0)
            mine_drafted = collections.Counter(t["p%d" % i] for t in my_all for i in range(1, 7) if t["p%d" % i] and t["adp%d" % i])
            tie_nights[h].append({"day": day, "swaps": tot, "top_share": top[1] / tot if tot else 0, "top": rows[top[0]]["name"] if top[0] else "-",
                                  "top_exposure": (mine_drafted[top[0]] + top[1]) / len(my_all) if top[0] else 0,
                                  "top_field": drafted_pct.get(top[0], 0)})
        if snaps:
            lock_t = None
            for x in snaps:
                pass
            for did, lst in my_teams.items():
                for c, elig, st in lst:
                    live_order = [s for s in snaps if parse(s["at"]) <= st]
                    if not live_order:
                        continue
                    o = live_order[-1]["order"]
                    rank = {p: i for i, p in enumerate(o)}
                    pick = min((p for p in elig if p in rank), key=lambda p: rank[p], default=None)
                    proj_pick = tie_order(elig, rows, drafted_pct, "proj")[0]
                    board_pick = tie_order(elig, rows, drafted_pct, "low")[0]
                    if pick:
                        mine_order.append((day, num(rows[pick]["actual"]) - num(rows[proj_pick]["actual"]), pick == c["swap"],
                                           num(rows[pick]["actual"]) - num(rows[board_pick]["actual"])))
                    after_last.append(parse(snaps[-1]["at"]) <= st)
    # ---- live moves: saves of your board after the slate locked, and how much they moved
    meta = json.load(open(os.path.join(NBA, "daily", "meta.json")))
    for name, m in sorted(meta.items()):
        snaps = orders(name[:10])
        if not snaps:
            continue
        lock = parse(m["lock"])
        after = [x for x in snaps if parse(x["at"]) > lock]
        before = [x for x in snaps if parse(x["at"]) <= lock]
        moved = 0
        if after and before:
            a0 = {p: i for i, p in enumerate(before[-1]["order"])}
            moved = sum(1 for i, p in enumerate(after[-1]["order"][:80]) if abs(a0.get(p, i) - i) >= 1)
        live.append((name[:10], len(snaps), len(after), moved))
    # ---- write
    md = ["# NBA swap board backtest (step 7)", "", "Written by scripts/nba_swap_board.py. Credited swaps only (swaps.csv).", "",
          "## a. Swap efficiency: points left on the table against the best undrafted option by ETR's final projection", "",
          "| Swaps | Group | Swaps | Points left per swap | Share where the swap was already the best option or better |", "|---|---|---|---|---|"]
    for k in sorted(eff):
        v = eff[k]
        md.append("| %s | %s | %d | %+.1f | %.0f%% |" % ("Field and you" if k[0] == "all" else "Your teams", k[1], len(v), sum(v) / len(v),
                                                        100 * sum(1 for x in v if x <= 0) / len(v)))
    md += ["", "## b. Your swapped teams under three orders of near-ties (within %.0f points on ETR's final)" % TIE, "",
           "| Order | Your swaps | Their points | Nights | Share on the night's most-hit target (avg) | That target's exposure (drafted + swapped, avg) | His field drafted% (avg) |",
           "|---|---|---|---|---|---|---|"]
    names = {"proj": "Projection only", "low": "Ownership lowest first (your habit)", "high": "Ownership highest first"}
    for h in tie:
        v = [x for d in tie[h] for x in tie[h][d]]
        nn = tie_nights[h]
        if not v:
            continue
        md.append("| %s | %d | %.1f | %d | %.0f%% | %.0f%% | %.0f%% |" % (
            names[h], len(v), sum(v) / len(v), len(nn), 100 * sum(x["top_share"] for x in nn) / len(nn),
            100 * sum(x["top_exposure"] for x in nn) / len(nn), sum(x["top_field"] for x in nn) / len(nn)))
    md += ["", "## Your own swaps", "", "Graded from your real swaps in the contest rosters (your Underdog app order, which the board "
           "never sees): analysis/nba/report/my_swaps.md. The replay of your saved order that used to stand here is superseded.",
           "", "Reading section a: points left on the table are the best option's score minus the swap's, so positive means the swap "
           "fell short. The field left %+.1f a swap; yours left %+.1f (AM %+.1f, PM %+.1f)." % tuple(
               sum(eff[k]) / len(eff[k]) if eff[k] else 0 for k in (("all", "all"), ("mine", "all"), ("mine", "AM"), ("mine", "PM")))]
    md += ["", "## Your live moves: board saves after the slate locked", "", "| Slate | Saves that day | After lock | Top-80 ranks moved by them |", "|---|---|---|---|"]
    md += ["| %s | %d | %d | %d |" % x for x in live]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
