"""College basketball daily record: one CSV per slate, our projection against what happened.

For every CBB slate that locked, each player our projection covered on its teams:

  at lock   adp_close: his last ADP before lock (blank: not priced); fp: our projection as
            it stood at lock (the mirror's cbb_morning.json, battle-royale-research
            scripts/cbb_nightly.py); fp_base: the same without EvanMiya; ud: Underdog's
            projection; src: what it was built from (box: a college season behind him,
            miya / miya+ud: a newcomer started from EvanMiya, ud / ud+box: from Underdog);
            min_proj and ppm_proj: the minutes and points per minute it multiplied;
            miya_ppm, bpr_rank: EvanMiya's part; spread, ou: his game's line
  actual    min, pts, reb, ast, stl, blk, tov from ESPN's box score and actual in Underdog
            points (the NBA's scoring: points 1, rebounds 1.2, assists 1.5, steals and
            blocks 3, turnovers -1); 0 for a player whose team played without him

  python3 scripts/cbb_daily.py record --mirror ../br-adp-mirror [--since 2026-11-03] [--rebuild]
  python3 scripts/cbb_daily.py report [--since 2026-11-03] [--date 2026-11-03]

report grades last night and every slate on file: mean error and bias of ours, ours
without EvanMiya and Underdog's on the players who played, overall, drafted only and by
src; where ours missed (minutes, and points per minute in the minutes played); and last
night's misses of MISS_PTS+. EvanMiya's November trial is decided on it; the college
morning report (.claude/skills/cbb-morning-report) reads it.
"""
import argparse
import csv
import datetime as dt
import glob
import json
import os
import statistics as S
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from nba_daily import ET, Mirror, UTC, at_pt, fetch_json, iso, pacific_day  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "daily")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"
MISS_PTS = 8                # a miss worth writing up: ours off by this many points
SCORING = {"PTS": 1, "REB": 1.2, "AST": 1.5, "STL": 3, "BLK": 3, "TO": -1}
COLS = ["date", "slate", "player_id", "name", "team", "adp_close", "src", "fp", "fp_base", "ud", "min_proj", "ppm_proj",
        "miya_ppm", "bpr_rank", "missed", "spread", "ou", "min", "pts", "reb", "ast", "stl", "blk", "tov", "actual"]


def slates(mirror, since, until):
    """Every CBB slate that locked in [since, until]."""
    found = {}
    for _, sha in mirror.versions("cbb_latest.json", since - dt.timedelta(days=2), until):
        for s in mirror.show(sha, "cbb_latest.json").get("slates", []):
            lock = iso(s["cutoff"])
            if since <= lock <= until:
                found[s["slate_id"]] = {"slate_id": s["slate_id"], "label": s["label"], "lock": lock}
    return sorted(found.values(), key=lambda s: s["lock"])


def at_lock(mirror, file, slate):
    """The file as it stood at lock, or None."""
    v = mirror.versions(file, slate["lock"] - dt.timedelta(days=2), slate["lock"])
    return mirror.show(v[-1][1], file) if v else None


def box(event):
    """{espn athlete id: {min, pts, ...}} for a final game, plus the team ids that played; None if not final."""
    s = fetch_json(f"{ESPN}/summary?event={event}")
    comp = (s.get("header") or {}).get("competitions", [{}])[0]
    if not ((comp.get("status") or {}).get("type") or {}).get("completed"):
        return None
    out, teams = {}, set()
    for team in (s.get("boxscore") or {}).get("players", []):
        teams.add(str(team["team"]["id"]))
        st = team["statistics"][0]
        for a in st["athletes"]:
            v = dict(zip(st["names"], a.get("stats") or []))
            if a.get("didNotPlay") or not v:
                continue
            try:
                row = {"min": float(v["MIN"]), "pts": float(v["PTS"]), "reb": float(v["REB"]), "ast": float(v["AST"]),
                       "stl": float(v["STL"]), "blk": float(v["BLK"]), "tov": float(v["TO"])}
            except (KeyError, ValueError):
                continue
            row["actual"] = round(sum(row[k] * w for k, w in zip(("pts", "reb", "ast", "stl", "blk", "tov"), SCORING.values())), 1)
            out[str(a["athlete"]["id"])] = row
    return out, teams


def events_by_opp(day):
    """{opponent's ESPN abbreviation: event id} for a day, for rows made before the projection carried its event."""
    out = {}
    for d in (day, day + dt.timedelta(days=1)):
        for e in fetch_json(f"{ESPN}/scoreboard?dates={d:%Y%m%d}&groups=50&limit=500").get("events", []):
            for c in e["competitions"][0]["competitors"]:
                out.setdefault(c["team"].get("abbreviation"), e["id"])
    return out


def build(mirror, slate):
    latest, morning = at_lock(mirror, "cbb_latest.json", slate), at_lock(mirror, "cbb_morning.json", slate)
    if not latest or not morning:
        return None
    s = next((x for x in latest["slates"] if x["slate_id"] == slate["slate_id"]), None)
    if not s:
        return None
    adp = {p["player_id"]: p["adp"] for p in s["players"]}
    teams = {p["team"] for p in s["players"]}
    rows = {pid: r for pid, r in morning["players"].items() if r.get("team") in teams}
    day = slate["lock"].astimezone(ET).date()
    need_scoreboard = any(not r.get("event") for r in rows.values())
    by_opp = events_by_opp(day) if need_scoreboard else {}
    boxes = {}
    out = []
    for pid, r in sorted(rows.items(), key=lambda x: -(x[1].get("fp") or 0)):
        ev = r.get("event") or by_opp.get(r.get("opp"))
        if not ev:
            continue
        if ev not in boxes:
            boxes[ev] = box(ev)
        if boxes[ev] is None:
            return None                     # a game not final yet: build the slate next run
        played, _ = boxes[ev]
        a = played.get(str(r.get("espn"))) if r.get("espn") else None
        if not a and not r.get("espn"):
            continue                        # not matched to ESPN: his night can't be read
        a = a or {"min": 0, "pts": 0, "reb": 0, "ast": 0, "stl": 0, "blk": 0, "tov": 0, "actual": 0}
        out.append({"date": pacific_day(slate["lock"]), "slate": slate["label"], "player_id": pid, "name": r.get("name"),
                    "team": r.get("team"), "adp_close": adp.get(pid, ""), "src": r.get("src"), "fp": r.get("fp"),
                    "fp_base": r.get("fp_base", r.get("fp") if r.get("miya_ppm") is None else ""), "ud": r.get("ud") or "",
                    "min_proj": r.get("min", ""), "ppm_proj": r.get("ppm", ""), "miya_ppm": r.get("miya_ppm", ""),
                    "bpr_rank": r.get("bpr_rank", ""), "missed": r.get("missed", ""), "spread": r.get("spread", ""), "ou": r.get("ou", ""), **a})
    return out


def record(a):
    now = dt.datetime.now(UTC)
    since = at_pt(a.since, 0) if a.since else at_pt(pacific_day(now - dt.timedelta(days=3)), 0)
    os.makedirs(OUT, exist_ok=True)
    mirror = Mirror(a.mirror)
    for slate in slates(mirror, since, now - dt.timedelta(hours=3)):
        path = os.path.join(OUT, "%s_%s.csv" % (pacific_day(slate["lock"]), slate["label"].replace("cbb_", "")))
        if os.path.exists(path) and not a.rebuild:
            continue
        rows = build(mirror, slate)
        if not rows:
            print("  %s: not ready (no projection at lock, or a game not final)" % slate["label"])
            continue
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
        print("  wrote %s: %d players, %d played" % (os.path.basename(path), len(rows), sum(1 for r in rows if r["min"])))


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def base(r):
    """Ours without EvanMiya: fp_base, or for a newcomer EvanMiya started, Underdog's number (what we used before)."""
    if num(r["fp_base"]) is not None:
        return num(r["fp_base"])
    return num(r["ud"]) if r["src"] in ("miya", "miya+ud") else None


def report(a):
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, "*.csv"))):
        if not a.since or os.path.basename(f) >= a.since:
            rows += list(csv.DictReader(open(f)))
    nights = sorted({r["date"] for r in rows})
    if not nights:
        print("CBB record: nothing on file yet")
        return
    last = a.date or nights[-1]
    night = [r for r in rows if r["date"] == last]
    print("CBB record: %d player-nights, %d slate days (%s); last night %s" % (len(rows), len(nights), ", ".join(nights), last))

    def grade(label, rs):
        rs = [dict(r, base=base(r)) for r in rs if num(r["min"]) and num(r["fp"]) is not None and num(r["ud"]) is not None]
        rs = [r for r in rs if r["base"] is not None]
        if not rs:
            print("  %-34s none yet" % label)
            return
        parts = []
        for k, name in (("fp", "ours"), ("base", "ours w/o Miya"), ("ud", "Underdog")):
            err = [num(r[k]) - num(r["actual"]) for r in rs]
            parts.append("%s %.2f (%+.2f)" % (name, S.mean(abs(e) for e in err), S.mean(err)))
        print("  %-34s n=%-4d mean error (bias): %s" % (label, len(rs), " | ".join(parts)))

    def split(label, rs):
        """Where ours missed: minutes, and points per minute in the minutes he played."""
        rs = [r for r in rs if num(r["min"]) and num(r["min_proj"]) and num(r["ppm_proj"])]
        if not rs:
            return
        dm = [num(r["min_proj"]) - num(r["min"]) for r in rs]
        dp = [num(r["ppm_proj"]) - num(r["actual"]) / num(r["min"]) for r in rs]
        print("  %-34s n=%-4d minutes off %.1f (bias %+.1f) | points/minute off %.2f (bias %+.2f), weighted by minutes %.2f" % (
            label, len(rs), S.mean(map(abs, dm)), S.mean(dm), S.mean(map(abs, dp)), S.mean(dp),
            sum(abs(d) * num(r["min"]) for d, r in zip(dp, rs)) / sum(num(r["min"]) for r in rs)))

    for title, rs in (("LAST NIGHT (%s)" % last, night), ("SEASON (%d nights)" % len(nights), rows)):
        print("\n%s. Players who played, where ours and Underdog's both had a number (without EvanMiya: Underdog's"
              " for a newcomer it started):" % title)
        grade("everyone", rs)
        grade("drafted (an ADP at lock)", [r for r in rs if r["adp_close"]])
        by = defaultdict(list)
        for r in rs:
            by[r["src"]].append(r)
        for k in sorted(by):
            grade("built from: " + k, by[k])
        print("  Where ours missed, players who played:")
        split("everyone", rs)
        split("drafted", [r for r in rs if r["adp_close"]])
        split("newcomers (EvanMiya / Underdog)", [r for r in rs if str(r["src"]).startswith(("miya", "ud"))])

    # standing watches (2026-11-03 report): minutes by EvanMiya's rank on his team, players built from last
    # season (the board's green chip is ranks 1-3); and players back from a missed season (MISSED_SEASON)
    for title, rs in (("LAST NIGHT", night), ("SEASON", rows)):
        box = [r for r in rs if r["src"] == "box" and num(r["min_proj"]) and num(r["min"]) is not None and not r.get("missed")]
        line = []
        for lo, hi in ((1, 3), (4, 7), (8, 99)):
            v = [num(r["min"]) - num(r["min_proj"]) for r in box if r["bpr_rank"] and lo <= int(r["bpr_rank"]) <= hi]
            if v:
                line.append("ranks %d-%s n=%d %+.1f" % (lo, hi if hi < 99 else "+", len(v), S.mean(v)))
        miss = [r for r in rs if r.get("missed") and num(r["min_proj"]) and num(r["min"]) is not None]
        print("\nWatch, %s: minutes actual - projected by EvanMiya team rank (built from last season, DNPs as 0): %s" % (
            title.lower(), "; ".join(line) or "none"))
        if miss:
            print("  back from a missed season: n=%d, minutes %+.1f (actual %.1f vs %.1f projected)" % (
                len(miss), S.mean(num(r["min"]) - num(r["min_proj"]) for r in miss),
                S.mean(num(r["min"]) for r in miss), S.mean(num(r["min_proj"]) for r in miss)))

    big = sorted((r for r in night if num(r["fp"]) is not None and num(r["min"]) and (r["adp_close"] or num(r["fp"]) >= 15)
                  and abs(num(r["fp"]) - num(r["actual"])) >= MISS_PTS), key=lambda r: -abs(num(r["fp"]) - num(r["actual"])))
    print("\nLast night's misses of %d+ (drafted, or projected 15+), biggest first:" % MISS_PTS)
    for r in big:
        print("  %-24s %-5s ADP %-5s ours %5.1f%s UD %-5s actual %5.1f | min %4.1f vs %4.1f proj | pts/min %.2f vs %.2f | spread %s | %s" % (
            r["name"], r["team"], r["adp_close"] or "-", num(r["fp"]),
            " (w/o Miya %.1f)" % num(r["fp_base"]) if num(r["fp_base"]) is not None and num(r["fp_base"]) != num(r["fp"]) else "",
            r["ud"] or "-", num(r["actual"]), num(r["min"]), num(r["min_proj"]) or 0,
            num(r["actual"]) / num(r["min"]), num(r["ppm_proj"]) or 0, r["spread"] or "-", r["src"]))
    dnp = [r for r in night if not num(r["min"]) and r["adp_close"]]
    if dnp:
        print("Drafted and didn't play last night: " + ", ".join("%s %s" % (r["name"], r["team"]) for r in dnp))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--mirror", required=True)
    r.add_argument("--since", help="YYYY-MM-DD, Pacific; default three days back")
    r.add_argument("--rebuild", action="store_true")
    p = sub.add_parser("report")
    p.add_argument("--since", help="YYYY-MM-DD: only slates from this day")
    p.add_argument("--date", help="YYYY-MM-DD: the night to show as last night (default the newest on file)")
    a = ap.parse_args()
    return record(a) if a.cmd == "record" else report(a)


if __name__ == "__main__":
    sys.exit(main())
