"""Your real swaps, graded: what your Underdog app order chose, against your last saved board order and the swap board.

Your final round-6 shuffle happens in the Underdog app, which never reaches the board. But after lock the contest data
shows every pod's full roster, so each of your swaps (a pick with no draft ADP on your team; credited to the player it
replaced by scripts/nba_swaps.py) tells something about your app order: the incoming player was ranked above every
other player left undrafted in that pod whose game hadn't started at the swap (the swap time: the earliest tip among
that ruled-out player's swap targets that night, else his own tip).

  inferred order   per night, those "ranked above" constraints: how many, how many distinct incoming players, and how
                   complete they are (constraints against the players your saved order had ahead of the incoming one)
  against saved    your last board order saved in the tool before the swap: how often it would have picked the same
                   player, and the points of the real swap against the saved order's pick (did the app shuffle help?)
  graded           each real swap against the best available by ETR's final projection and against the swap board's
                   pick (ETR's final, near-ties within 2 points least drafted first): points per swap

Small sample: your swaps so far are about 100 over 9 nights; every number says so. Writes analysis/nba/report/my_swaps.md.

  python3 scripts/nba_my_swaps.py
"""
import collections, datetime as dt, glob, gzip, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_swaps as S           # noqa: E402
import nba_swap_board as W      # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NBA = os.path.join(HERE, "analysis", "nba")
OUT = os.path.join(NBA, "report", "my_swaps.md")
ME = "jonboybeats"
num = S.num


def main():
    days = sorted({os.path.basename(f)[:10] for f in glob.glob(os.path.join(NBA, "contests", "2026-*_*.csv.gz"))})
    nights, allrows = [], []
    for day in days:
        n = S.night(day)
        if not n or not n["credited"]:
            continue
        rows, tip, out = n["rows"], n["tip"], n["out"]
        mine = [c for c in n["credited"] if c["username"] == ME]
        my_swaps_all = sum(1 for t in n["all_teams"] if t["username"] == ME for i in range(1, 7) if t["p%d" % i] and not t["adp%d" % i])
        if not my_swaps_all:
            continue
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
        hist = W.tier_rows(day)
        drafted = {pid: num(r["drafted"]) or 0 for pid, r in hist.get("pm", {}).items()}
        snaps = W.orders(day)
        cons, incoming, same, helped, vs_best, vs_board, complete = [], set(), 0, [], [], [], []
        for c in mine:
            st = swap_time.get(c["out"])
            if st is None or c["swap"] not in rows or num(rows[c["swap"]]["actual"]) is None:
                continue
            elig = [p for p, r in rows.items() if p not in pods[c["draft_id"]] and p not in out and p not in sat
                    and r["team"] in tip and tip[r["team"]] >= st]
            if c["swap"] not in elig:
                elig.append(c["swap"])
            others = [p for p in elig if p != c["swap"]]
            cons += [(c["swap"], p) for p in others]
            incoming.add(c["swap"])
            fp = num(rows[c["swap"]]["actual"])
            withproj = [p for p in elig if (num(rows[p]["etr_last"]) or 0) > 0]
            if withproj:
                best = max(withproj, key=lambda p: num(rows[p]["etr_last"]))
                vs_best.append(fp - num(rows[best]["actual"]))
                board = W.tie_order(withproj, rows, drafted, "low")[0]
                vs_board.append(fp - num(rows[board]["actual"]))
            saved = [s for s in (snaps or []) if W.parse(s["at"]) <= st]
            if saved:
                rank = {p: i for i, p in enumerate(saved[-1]["order"])}
                pick = min((p for p in elig if p in rank), key=lambda p: rank[p], default=None)
                if pick:
                    same += pick == c["swap"]
                    helped.append(fp - num(rows[pick]["actual"]))
                    ahead = [p for p in elig if p in rank and c["swap"] in rank and rank[p] < rank[c["swap"]]]
                    complete.append(len(ahead))      # players your saved order had above the one the app chose
        nights.append({"day": day, "mine_all": my_swaps_all, "credited": len(mine), "cons": len(cons), "incoming": len(incoming),
                       "same": same, "with_saved": len(helped), "helped": helped, "vs_best": vs_best, "vs_board": vs_board,
                       "reorders": complete})
    md = ["# Your real swaps (from the contest rosters)", "",
          "Written by scripts/nba_my_swaps.py. Small sample: about 100 swaps over 9 nights so far; read every number as "
          "directional. Points: the real incoming player's score minus the other's (positive: your real swap was better).", "",
          "| Night | Your swaps | Credited | Inferred order: constraints (incoming players) | Saved order would have picked the same | App shuffle vs your saved order's pick | vs best by ETR final | vs the swap board's pick | Players your saved order had above the app's choice (avg) |",
          "|---|---|---|---|---|---|---|---|---|"]
    tot = collections.defaultdict(list)
    for x in nights:
        f = lambda v: "%+.1f (%d)" % (sum(v) / len(v), len(v)) if v else "-"
        md.append("| %s | %d | %d | %d (%d) | %s | %s | %s | %s | %s |" % (
            x["day"], x["mine_all"], x["credited"], x["cons"], x["incoming"],
            "%d of %d" % (x["same"], x["with_saved"]) if x["with_saved"] else "-", f(x["helped"]), f(x["vs_best"]), f(x["vs_board"]),
            "%.1f" % (sum(x["reorders"]) / len(x["reorders"])) if x["reorders"] else "-"))
        for k in ("helped", "vs_best", "vs_board", "reorders"):
            tot[k] += x[k]
        tot["same"].append(x["same"])
        tot["with_saved"].append(x["with_saved"])
        tot["mine_all"].append(x["mine_all"])
        tot["credited"].append(x["credited"])
    g = lambda v: "%+.1f per swap over %d swaps" % (sum(v) / len(v), len(v)) if v else "-"
    md += ["", "Season (small sample, %d nights): %d of your %d swaps credited to the player they replaced. Your saved order would "
           "have made the same swap %d of %d times; the app shuffle's real swaps against the saved order's picks: %s. Real swaps "
           "against the best by ETR's final: %s; against the swap board's pick: %s. On average your saved order had %.1f eligible "
           "players ranked above the one your app order chose." % (
               len(nights), sum(tot["credited"]), sum(tot["mine_all"]), sum(tot["same"]), sum(tot["with_saved"]), g(tot["helped"]),
               g(tot["vs_best"]), g(tot["vs_board"]), sum(tot["reorders"]) / len(tot["reorders"]) if tot["reorders"] else 0)]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
