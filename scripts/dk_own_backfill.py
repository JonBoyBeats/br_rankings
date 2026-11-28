"""Rebuild analysis/cbb/dk/own_eval.csv with every projected player graded (2026-11-28, a grading fix).

Before the fix own_eval logged only the players a contest's standings listed (somebody drafted them), so a player we
projected at X% whom nobody drafted never counted as a miss (small contests: projected sums of 465-543 against 800),
and real ownership came from the Player section's %Drafted, which lists some two-slot players once (see
dk_eval.standings_rows). This rewrites every logged contest: with its standings file on hand, from the file (lineup
counts) through dk_eval.own_log_rows; without one (a contest logged only from the sync repo's late-swap standings),
its old rows kept and every other night-record player added at 0. Rerunnable; it rewrites the file whole.

  python3 scripts/dk_own_backfill.py
"""
import csv, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_eval as E   # noqa: E402


def main():
    old = E.read(E.OWN_EVAL)
    by_c = defaultdict(list)
    for r in old:
        by_c[r["contest_id"]].append(r)
    recs = {}
    for f in os.listdir(E.DK):
        if f.endswith(".csv") and f[:4] == "2026" and "_" in f and f.count("_") == 1:
            rec = E.read(os.path.join(E.DK, f))
            if rec:
                recs[str(rec[0]["draft_group"])] = rec
    out, n_file, n_kept = [], 0, 0
    for cid, rows in sorted(by_c.items(), key=lambda kv: (kv[1][0]["date"], kv[0])):
        g = str(rows[0]["draft_group"])
        rec = recs.get(g)
        n = rows[0].get("entries")
        path = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if rec and os.path.exists(path):
            entries, players = E.standings(path)
            out += E.own_log_rows(rec, cid, players, n or len(entries))
            n_file += 1
        else:
            have = {r["dk_id"] for r in rows}
            out += rows
            if rec:
                out += [dict(x, own_actual=0.0) for x in E.own_log_rows(rec, cid, {}, n) if x["dk_id"] not in have]
            n_kept += 1
    with open(E.OWN_EVAL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=E.OWN_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    print("own_eval.csv: %d rows (was %d), %d contests rebuilt from their standings, %d kept from the sync repo's rows with zeros added"
          % (len(out), len(old), n_file, n_kept))


if __name__ == "__main__":
    main()
