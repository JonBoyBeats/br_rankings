"""B3 backfill (2026-11-20): the watchlist's new facts for slates graded before the nightly carried them on each DK
record (battle-royale-research cbb_nightly, from 2026-11-20): team_rank (ESPN's AP rank on that day's scoreboard,
else the coaches' poll as ESPN lists it now: the polls of 2026-11-16 cover 11-16 to 11-19), tv (a national network
carrying the game: cbb_nightly.NATIONAL_TV on a broadcast ESPN marks national) and sal_prev (his salary on the most
recent banked DraftKings slate before, battle-royale-research data/dk/cbb/*.csv). Writes analysis/cbb/dk/
watch_backfill.json {draft group: {dk id: {team_rank, tv, sal_prev}}}; ownwatch uses a record's own fields first.

  python3 scripts/dk_watch_backfill.py --mirror ../br-adp-mirror --brr ../battle-royale-research
"""
import argparse, csv, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dk_vegas_study import at_lock          # noqa: E402  the mirror's slate file before lock
from nba_daily import Mirror                # noqa: E402

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True)
    ap.add_argument("--brr", required=True)
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import cbb_nightly as n
    from datetime import date
    m, coaches, out = Mirror(a.mirror), n.coaches_poll(), {}
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = list(csv.DictReader(open(f)))
        if not rows:
            continue
        d, g = rows[0]["date"], str(rows[0]["draft_group"])
        sl = at_lock(m, d, g) or {}
        et = {k: p.get("espn_team") for k, p in (sl.get("players") or {}).items()}
        games = n.espn_games([date.fromisoformat(d)])
        prev = n.prev_salaries(d)
        out[g] = {}
        for r in rows:
            t = et.get(r["dk_id"])
            gm = games.get(str(t), {}) if t else {}
            out[g][r["dk_id"]] = {"team_rank": gm.get("rank") or (coaches.get(str(t)) if t else None), "tv": gm.get("tv"), "sal_prev": prev.get((r["name"], r["team"]))}
        v = out[g].values()
        print("%s %s: %d players, ranked %d, national TV %d, previous salary %d" % (d, g, len(v), sum(1 for x in v if x["team_rank"]), sum(1 for x in v if x["tv"]), sum(1 for x in v if x["sal_prev"])))
    json.dump(out, open(os.path.join(DK, "watch_backfill.json"), "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
