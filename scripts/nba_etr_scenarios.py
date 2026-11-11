"""Every ETR scenario file you've uploaded, next to ETR's main file from the same moment: how ETR moves each teammate
when a player sits. For the study of the board's out bump (nbaLineupBump) against ETR's own.

The board keeps a day's scenarios ("Scottie OUT") only that day, so this reads them from the gist's history (every save
is a commit) and adds them to analysis/nba/daily/etr_scenarios.csv, which keeps every scenario seen so far: the nightly
clone reaches back only a week. A scenario is read from the first save holding it, against the main file in that save
(the main file for the same Pacific day; a scenario without one is skipped). One row per player on the scenario's
team(s), in the main file or the scenario:

  date, scenario, file, at          the scenario and its upload
  main_file, main_at                the main file it is read against
  team, name
  main_median, main_ceiling         ETR's main file (blank: not in it)
  scen_median, scen_ceiling         the scenario (blank: not in it, so he sits in it)
  out                               who the scenario sits: on the main file, not in the scenario (";" between)

  python3 scripts/nba_etr_scenarios.py --gist ../gist
"""
import argparse, csv, os, subprocess

from nba_daily import Gist, iso, pacific_day

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(HERE, "analysis", "nba", "daily", "etr_scenarios.csv")
COLS = ["date", "scenario", "file", "at", "main_file", "main_at", "team", "name", "main_median", "main_ceiling",
        "scen_median", "scen_ceiling", "out"]


def num(v):
    return "" if v is None else round(float(v), 2)


def rows_for(c, cur):
    teams = {e["team"] for e in c["entries"] if e.get("team")}
    main = {e["norm"]: e for e in cur["entries"] if e.get("team") in teams and not e.get("scenario")}
    scen = {e["norm"]: e for e in c["entries"]}
    out = ";".join(sorted(main[k]["name"] for k in main if k not in scen))
    rows = []
    for k in sorted(set(main) | set(scen)):
        m, s = main.get(k), scen.get(k)
        e = m or s
        rows.append({"date": pacific_day(iso(c["at"])), "scenario": c["label"], "file": c.get("file") or "", "at": c["at"],
                     "main_file": cur.get("file") or "", "main_at": cur["at"], "team": e.get("team") or "", "name": e["name"],
                     "main_median": num(m and m.get("median")), "main_ceiling": num(m and m.get("ceiling")),
                     "scen_median": num(s and s.get("median")), "scen_ceiling": num(s and s.get("ceiling")), "out": out})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gist", default=os.path.join(HERE, "..", "gist"))
    a = ap.parse_args()
    have = list(csv.DictReader(open(OUT))) if os.path.exists(OUT) else []
    seen = {(r["scenario"], r["at"]) for r in have}
    g, new = Gist(a.gist), []
    for _, sha in g.revs:
        try:
            raw = g.show(sha, "br_projections_nba.json")
        except (subprocess.CalledProcessError, ValueError):
            continue
        cur = raw.get("current") if isinstance(raw, dict) else None
        for c in ((raw.get("conditionals") or {}).values() if isinstance(raw, dict) else []):
            key = (c.get("label"), c.get("at"))
            if key in seen or not c.get("entries"):
                continue
            if not cur or not cur.get("entries") or pacific_day(iso(cur["at"])) != pacific_day(iso(c["at"])):
                continue
            seen.add(key)
            new += rows_for(c, cur)
    rows = sorted(have + new, key=lambda r: (r["date"], r["at"], r["scenario"], r["team"], r["name"]))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    n = len({(r["scenario"], r["at"]) for r in rows})
    print("%d scenarios on file (%d new rows), %s" % (n, len(new), ", ".join(sorted({r["date"] for r in rows})) or "none"))


if __name__ == "__main__":
    main()
