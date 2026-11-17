"""DraftKings CBB: grading the sim and the rule sets against real contests, and the projection gate.

The owner downloads each contest's full standings from DraftKings after it settles and drops it, as downloaded, in
analysis/cbb/dk/standings/ (contest-standings-<contest id>.csv; never edited). With last night's record
(analysis/cbb/dk/<date>_<draft group>.csv, scripts/cbb_daily.py) and the shadow portfolios saved before lock (the
mirror's dk_cbb_shadow.json, scripts/dk_shadow.js):

  nightly   per standings file not graded yet, rows in analysis/cbb/dk/eval.csv: each of the five frozen rule sets'
            shadow portfolio (and No extra rules' pool's top 20 by expected payout alone), the DK page's saved build
            (analysis/cbb/dk/builds: its hand-built 20 and auto-pick) and the owner's own entries (EntryName
            jonboyjackson), placed among the contest's real entries: share of lineups in the top 10%, share that
            cashed, dollars back on fees; and each one's percentile among RANDOM_SETS random sets of its size from its
            own pool, and the pool's average lineup against the field's average entry. Then the field's cut
            lines (winning score, top 10%, last paid place) against the sim's prediction (when the shadow was built
            for that contest), and each drafted player's projected ownership against his real %Drafted
            (analysis/cbb/dk/own_eval.csv).
  tiles     analysis/cbb/dk/tiles_eval.csv: each graded night's team tiles (as they stood before lock: quadrant,
            Quality, Leverage, the ranks) against what happened: did the team's top 5 by salary beat the points their
            salary implied at that night's rate? (Targets 2 and 3 come from the standings, in nightly:
            analysis/cbb/dk/team_eval.csv.)
  weights   Quality's weights fitted on the earlier 2/3 of the logged slates and tested on the later 1/3; written to
            analysis/cbb/dk/team_weights.json with use: true only if they beat equal weights there (the tiles read it)
  gate      analysis/cbb/dk/gate.json: by salary band, whether DraftKings' season average has beaten ours over the
            graded nights (lower mean error on everyone not tagged Out, a player who sat scoring 0, with at least
            GATE_NIGHTS nights and GATE_N player-nights, and the better of the two on GATE_SHARE of the nights). Where
            it has, the gate opens with w, the least-squares weight on ours in w x ours + (1 - w) x DK average; the DK
            page and the shadow portfolios then use that blend there (dk_sim.js gatedProj).
  cutcheck  analysis/cbb/dk/cut_eval.csv, nightly: each saved bank (analysis/cbb/dk/builds/dk_bank_*.json, the DK
            page's Save build) scored on the night's real DraftKings points, by rule tag: the lineups the cut removed,
            the ones it kept, and the ones entered: how many, their mean and best score, and against each entered
            contest's real lines once its standings are graded (eval.csv: winning score, top 10%, last paid place)
            the share that would have reached the top 10%, cashed, and won. Did the cut throw away winners? Rebuilt
            whole each run, so standings that come in later fill in.
  audit     the audit, projections and ownership first (the sim's grading waits for enough slates), last night and
            the season so far; short here and in the morning report, in full at the top of the readout:
            a. projections: ours against the actual DraftKings points by salary band (everyone not tagged Out, a player
               who sat scoring 0): average miss, bias (projection minus actual), rank correlation; DraftKings' season
               average and his last-5 average (dk_last5, recorded from 2026-11-17) as benchmarks on the same players
            b. ownership, from each night's biggest graded contest: projected against actual by projected-ownership
               band (bias, average miss, rank correlation); a player missing from the standings was drafted by no one
            c. ownership as the industry's view: each player's actual ownership against what our value implied (the
               night's players ranked by our points per $1,000, the k-th best value given the k-th highest actual
               ownership): where the field liked a player more than our value did, did he beat our projection, and
               where it liked him less, fall short? By size of the disagreement, then, for disagreements of
               AUDIT_DISAGREE+ points, where the field was right, by salary band, position and minutes change
               (projected minutes against his last 5)
  calnote   the calibration week's morning note (through 2026-11-23): bugs found, the audit's a / b / c in one line
            each, and the changes since the last graded slate with their reasons, from analysis/cbb/dk/versions.csv
            (every change, with the slate date it takes effect; the readout splits slates by it)
  calweek   for the owner's choice at the freeze: ours, DraftKings' average and the 50/50 blend over the calibration
            week's graded nights (CAL_WEEK), by salary band, and the nights each had the lowest average miss
  readout   the monthly readout, not nightly: each rule set against "No extra rules" slate by slate (slates won
            and the paired gap, on the top-10% rate first, then cash; dollars only as the long-run check), the
            owner's entries against the field's 10%, ownership by band, the sim's cut lines, the correlation check
            (real teammate and opponent correlation of misses, which the sim takes as 0, and the spread of game
            totals against the sim's), whether real scores land where the sim's draws put them, and where the
            30-slate decision stands: does any rule set, or the owner's entries, beat the field's top-10% rate?

  python3 scripts/dk_eval.py nightly --mirror ../br-adp-mirror
  python3 scripts/dk_eval.py gate
  python3 scripts/dk_eval.py tiles --mirror ../br-adp-mirror
  python3 scripts/dk_eval.py weights      (monthly, with the readout)
  python3 scripts/dk_eval.py cutcheck
  python3 scripts/dk_eval.py audit
  python3 scripts/dk_eval.py readout
"""
import argparse
import csv
import datetime as dt
import glob
import json
import math
import os
import random
import re
import statistics as S
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
from nba_daily import Mirror, iso  # noqa: E402

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
STANDINGS = os.path.join(DK, "standings")
EVAL, OWN_EVAL, GATE = os.path.join(DK, "eval.csv"), os.path.join(DK, "own_eval.csv"), os.path.join(DK, "gate.json")
USER = "jonboyjackson"
EVAL_COLS = ["date", "draft_group", "contest_id", "contest", "entries", "fee", "who", "lineups", "top10", "cash", "dollars_back",
             "fees", "pct_top10", "pct_cash", "pct_dollars", "pool_src", "pool_n", "pool_avg", "field_avg",
             "field_win", "field_top10", "field_cash", "sim_win", "sim_top10", "sim_cash", "rules", "phase", "version"]
RANDOM_SETS = 1000
TILES_EVAL = os.path.join(DK, "tiles_eval.csv")
TILE_COLS = ["date", "draft_group", "team", "verdict", "borderline", "quality", "leverage", "pts_rank", "value_rank", "conc_rank", "blowout_rank",
             "lev_rank", "ranked_against", "total", "value", "conc", "own_gap", "blowout", "blowout_games", "fragile",
             "top5_salary", "top5_actual", "top5_implied", "beat", "phase", "version"]
TEAM_EVAL = os.path.join(DK, "team_eval.csv")
TEAM_COLS = ["date", "draft_group", "contest_id", "team", "own_real", "pts_share", "beat_own", "top1_n", "top1_rate", "field_rate"]
WEIGHTS = os.path.join(DK, "team_weights.json")
QUALITY = ("pts", "value", "conc", "blowout")
FIT_MIN_SLATES = 10           # slates logged before the weights are fitted (earlier 2/3 to fit, later 1/3 to test)
QUADS = ("FOCUS", "CHALK", "LEVERAGE", "FADE")
RULE_NAMES = {"min": "Min N from a team / stack", "none": "Exclude team", "if": "1. if player then N+", "ifnot": "2. if NOT player then N+",
              "ifteam": "3. if N+ from team then M+ from opponent", "never": "4. never player with player"}
BUILDS = os.path.join(DK, "builds")       # the DK page's saved builds (Save build: its pool, the hand-built 20, the auto-pick)
OWN_COLS = ["date", "draft_group", "contest_id", "dk_id", "name", "salary", "own_proj", "own_actual"]
BANDS = [(6000, 99999), (4000, 5999), (0, 3999)]
GATE_NIGHTS, GATE_N, GATE_SHARE = 5, 100, 0.6
OWN_BANDS = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 35), (35, 101)]
CUT_EVAL = os.path.join(DK, "cut_eval.csv")
CUT_COLS = ["date", "draft_group", "tag", "group", "lineups", "mean", "best", "contest_id", "contest", "top10", "cash", "wins",
            "protect", "phase"]
DECISION_SLATES = 30
PT = ZoneInfo("America/Los_Angeles")
VERSIONS = os.path.join(DK, "versions.csv")   # every change, with the slate date it takes effect (version_of)
# Calibration week: ours blended with DraftKings' average at w in every salary band, the gate's rule bypassed, from
# "from" (versions.csv cal-1), with no end date: it stays on until the owner chooses at the freeze which projection
# freezes (calweek reports ours, DraftKings' average and the blend over the week). PROJ_CHOICE records that choice:
# None (not chosen yet: the blend), "ours" (the gate back to its own rule), "dk" (DraftKings' average) or "blend".
CALIBRATION_BLEND = {"w": 0.5, "from": "2026-11-17", "version": "cal-1"}
PROJ_CHOICE = None
CAL_WEEK = ("2026-11-16", "2026-11-23")      # the calibration week's slates, for calweek
BLEND_W = 0.5            # the audit's blend: ours x BLEND_W + DraftKings' average x (1 - BLEND_W) (cal-1's)
AUDIT_DISAGREE = 5        # ownership points: a disagreement big enough to list where the field was right
DISAGREE_BINS = [(10, 999, "field liked more by 10+"), (5, 10, "more by 5-10"), (2, 5, "more by 2-5"), (-2, 2, "within 2"),
                 (-5, -2, "less by 2-5"), (-10, -5, "less by 5-10"), (-999, -10, "less by 10+")]
PROJ_BINS = [3, 6, 9, 12, 15, 20, 25, 30, 40, 999]   # our projection, upper edges: misses compared within a level
MIN_CHANGE = 4            # minutes: projected against his last 5, "up" / "down" past this
FREEZE_END = "2026-11-23"   # week 1, open for tweaks: slates through this date are warm-up, logged but not counted


def phase(date):
    return "warm-up" if str(date) <= FREEZE_END else "counted"


def counted(rows):
    """The readout's rows: the counted slates once there are any, else the warm-up ones (labelled as such)."""
    c = [r for r in rows if (r.get("phase") or phase(r["date"])) == "counted"]
    return (c, "counted") if c else ([r for r in rows if r not in c], "warm-up")
SIM_Z_SD = 1.266          # the spread of the sim's draws, in expected misses (cbb_form_study.py SIM_Z)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def read(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def standings(path):
    """(entries [{rank, name, points}], {player name: (%drafted, fpts)}) from a DraftKings standings CSV. Its player
    list has a row for each roster slot a player was drafted in, each with that slot's %Drafted (verified on the first
    files, 2026-11-16: Phillips G 53.44% + UTIL 11.01% = the 64.45% DraftKings shows)."""
    entries, players = [], {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("EntryId") and num(r.get("Points")) is not None:
                entries.append({"rank": int(num(r["Rank"])), "name": r.get("EntryName") or "", "points": num(r["Points"]),
                                "lineup": r.get("Lineup") or ""})
            if r.get("Player"):     # one row per roster slot he was drafted in (G, F, UTIL): his ownership is their sum
                nm, pct = r["Player"].strip(), num(str(r.get("%Drafted", "")).rstrip("%"))
                prev = players.get(nm, (None, None))[0]
                players[nm] = (pct if prev is None else prev + (pct or 0), num(r.get("FPTS")))
    return entries, players


def lineup_names(s):
    """The player names in a standings Lineup cell ("F Name G Name ... UTIL Name")."""
    parts = re.split(r"(?:^|\s)(G|F|UTIL)\s", " " + s.strip())
    return [x.strip() for x in parts[2::2] if x.strip()]


def at_lock(mirror, file, start, slate=None):
    """The mirror's file as it stood before the start; with slate, the latest version before it that has that draft
    group (an hourly run can leave a slate out, e.g. the shadow with no contest it could build for, on 2026-11-16)."""
    v = mirror.versions(file, start - dt.timedelta(days=2), start)
    for _, sha in reversed(v if slate else v[-1:]):
        d = mirror.show(sha, file)
        if not slate or str(slate) in ((d or {}).get("slates") or {}):
            return d
    return None


def placed(points, field_desc):
    """Place among the field's scores (sorted high to low): 1 + entries scoring more."""
    lo, hi = 0, len(field_desc)
    while lo < hi:
        mid = (lo + hi) // 2
        if field_desc[mid] > points:
            lo = mid + 1
        else:
            hi = mid
    return lo + 1


def pay_table(payouts):
    t = {}
    for a, b, v in payouts or []:
        for i in range(int(a), int(b) + 1):
            t[i] = v
    return t


def nightly(a):
    mirror = Mirror(a.mirror)
    done = {(r["contest_id"]) for r in read(EVAL)}
    out, own_out, team_out = [], [], []
    for path in sorted(glob.glob(os.path.join(STANDINGS, "*.csv"))):
        m = re.search(r"(\d{6,})", os.path.basename(path))
        if not m or m.group(1) in done:
            continue
        cid = m.group(1)
        entries, players = standings(path)
        if not entries:
            print("  %s: no entries read" % os.path.basename(path))
            continue
        # which slate: the record whose contests list this one (the mirror's DraftKings file as it stood at lock)
        rec, slate, start = None, None, None
        for f in sorted(glob.glob(os.path.join(DK, "????-??-??_*.csv"))):
            rows = read(f)
            if not rows:
                continue
            g = rows[0]["draft_group"]
            vs = mirror.versions("dk_cbb_morning.json", iso(rows[0]["date"] + "T00:00:00Z") - dt.timedelta(days=1),
                                 iso(rows[0]["date"] + "T00:00:00Z") + dt.timedelta(days=2))
            for t, sha in reversed(vs):
                doc = mirror.show(sha, "dk_cbb_morning.json")
                s = next((x for x in doc.get("slates", []) if str(x["draft_group_id"]) == g), None)
                if s and any(str(c["id"]) == cid for c in s.get("contests", [])):
                    rec, slate, start = rows, s, iso(s["start"])
                    break
            if rec:
                break
        if not rec:
            print("  %s: no graded DraftKings slate lists contest %s yet" % (os.path.basename(path), cid))
            continue
        contest = next(c for c in slate["contests"] if str(c["id"]) == cid)
        pay, fee, n = pay_table(contest.get("payouts")), contest.get("entry_fee") or 0, len(entries)
        paid = max(pay) if pay else 0
        field = sorted((e["points"] for e in entries), reverse=True)
        top10 = math.ceil(0.1 * n)
        cut = {"win": field[0], "top10": field[top10 - 1], "cash": field[paid - 1] if paid and paid <= n else None}
        # every drafted player's DraftKings points: the standings' FPTS, else the record's
        by_name = {r["name"]: r for r in rec}
        pts = {r["dk_id"]: num(r["actual_dk"]) for r in rec}
        for r in rec:
            if r["name"] in players and players[r["name"]][1] is not None:
                pts[r["dk_id"]] = players[r["name"]][1]
        shadow = at_lock(mirror, "dk_cbb_shadow.json", start, slate["draft_group_id"]) or {}
        sh = (shadow.get("slates") or {}).get(str(slate["draft_group_id"]))
        base = {"date": rec[0]["date"], "draft_group": slate["draft_group_id"], "contest_id": cid, "contest": contest["name"],
                "entries": n, "fee": fee, "field_win": cut["win"], "field_top10": cut["top10"], "field_cash": cut["cash"],
                "field_avg": round(S.mean(field), 2), "phase": phase(rec[0]["date"]), "version": (shadow or {}).get("version", "")}

        def lineup(ids):                 # (in the top 10%, cashed, dollars) for one lineup against the real entries
            p = placed(sum(pts.get(i) or 0 for i in ids), field)
            return (p <= top10, p <= paid, pay.get(p, 0), sum(pts.get(i) or 0 for i in ids))

        def grade(who, actual, pool, pool_src, extra=None):
            """A portfolio's row: its top-10% and cash rates and dollars, and where those land among RANDOM_SETS random
            sets of the same size from its own pool (percentile: share of random sets below it, ties half)."""
            k = len(actual)
            row = dict(base, who=who, lineups=k, top10=sum(a[0] for a in actual) / k, cash=sum(a[1] for a in actual) / k,
                       dollars_back=sum(a[2] for a in actual), fees=fee * k, pool_src=pool_src, sim_win="", sim_top10="", sim_cash="")
            if pool and len(pool) >= k:
                P = [lineup(ids) for ids in pool]
                rng = random.Random("%s-%s" % (cid, who))
                sets = [rng.sample(P, k) for _ in range(RANDOM_SETS)]
                for col, f in (("top10", lambda v: sum(a[0] for a in v) / k), ("cash", lambda v: sum(a[1] for a in v) / k),
                               ("dollars", lambda v: sum(a[2] for a in v))):
                    me = f(actual)
                    rs = [f(v) for v in sets]
                    row["pct_" + col] = round(100 * (sum(r < me for r in rs) + 0.5 * sum(r == me for r in rs)) / RANDOM_SETS, 1)
                row.update(pool_n=len(pool), pool_avg=round(S.mean(a[3] for a in P), 2))
            row.update(extra or {})
            out.append(row)

        saved = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(BUILDS, "*.json")))]
        saved = [b for b in saved if str(b.get("draft_group")) == str(slate["draft_group_id"])]
        builds = [b for b in saved if b.get("pool")]                  # Save build: a pool, hand-built and auto-pick
        banks = [b for b in builds if b.get("tags")]                  # the page's bank (Bank, cut and portfolios)
        mine_pool = (banks or builds)[-1]["pool"] if builds else none_pool
        pr = ((banks[-1].get("cut") or {}).get("protect") if banks else None)     # the cut's protect setting, priced by the readout
        protected = " protect%d" % pr if pr else ""
        used = sorted({r["type"] for r in ((saved[-1].get("rule_set") or []) if saved else [])})   # the night's rules
        none_pool = ((sh or {}).get("rulesets", {}).get("none") or {}).get("pool")
        if sh:
            same = str(sh["contest"]["id"]) == cid
            for key, rs in sh["rulesets"].items():
                L = rs.get("lineups") or []
                if L:
                    grade(key, [lineup(l["ids"]) for l in L], rs.get("pool"), "its own",
                          {"sim_win": rs["cut"]["win"], "sim_top10": rs["cut"]["top10"], "sim_cash": rs["cut"]["cash"]} if same else None)
            if sh.get("top20_alone"):
                grade("top20_alone", [lineup(l["ids"]) for l in sh["top20_alone"]["lineups"]], none_pool, "none's")
        for b in [b for b in builds if b.get("hand") or b.get("auto")][-1:]:   # the last builder save: hand-built and auto-pick
            for key in ("hand", "auto"):
                if b.get(key):
                    grade(key, [lineup(b["pool"][i]) for i in b[key]], b["pool"], "the build's")
        mine = [e for e in entries if e["name"].lower().startswith(USER)]
        if mine:
            grade("mine", [(e["rank"] <= top10, e["rank"] <= paid, pay.get(e["rank"], 0), e["points"]) for e in mine],
                  mine_pool, "the bank's" if banks else "the build's" if builds else "none's",
                  {"rules": (" ".join(used) if saved else "not saved") + protected})
        # each team against the real field: its actual share of the points against its real ownership share, and how
        # often 2+ of its players are in the top-1% lineups against how often the field played 2+ of them
        team_of = {r["name"]: r["team"] for r in rec}
        lineups = [(e["rank"], [team_of.get(nm) for nm in lineup_names(e.get("lineup") or "")]) for e in entries]
        lineups = [(rk, ts) for rk, ts in lineups if len(ts) == 8]
        top1 = [ts for rk, ts in lineups if rk <= max(1, math.ceil(0.01 * n))]
        all_pts = sum(num(r["actual_dk"]) or 0 for r in rec)
        for team in sorted({r["team"] for r in rec}):
            own_real = sum((players.get(r["name"]) or (None,))[0] or 0 for r in rec if r["team"] == team) / 800
            share = sum(num(r["actual_dk"]) or 0 for r in rec if r["team"] == team) / all_pts if all_pts else 0
            team_out.append({"date": rec[0]["date"], "draft_group": slate["draft_group_id"], "contest_id": cid, "team": team,
                             "own_real": round(own_real, 4), "pts_share": round(share, 4), "beat_own": int(share > own_real),
                             "top1_n": len(top1), "top1_rate": round(sum(ts.count(team) >= 2 for ts in top1) / len(top1), 4) if top1 else "",
                             "field_rate": round(sum(ts.count(team) >= 2 for _, ts in lineups) / len(lineups), 4) if lineups else ""})
        if not lineups:
            print("  %s: no lineups read from the standings' Lineup column; the top-1%% target is skipped" % os.path.basename(path))
        for name, (pct, _) in players.items():
            r = by_name.get(name)
            if r and pct is not None:
                own_out.append({"date": r["date"], "draft_group": r["draft_group"], "contest_id": cid, "dk_id": r["dk_id"], "name": name,
                                "salary": r["salary"], "own_proj": r["own"], "own_actual": pct})
        print("  graded %s (%s, %d entries): shadow %s, your entries %d" % (contest["name"], rec[0]["date"], n, "yes" if sh else "none saved", len(mine)))
    for path, cols, rows in ((EVAL, EVAL_COLS, out), (OWN_EVAL, OWN_COLS, own_out), (TEAM_EVAL, TEAM_COLS, team_out)):
        if rows:
            new = not os.path.exists(path)
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols)
                if new:
                    w.writeheader()
                w.writerows(rows)
    if not out:
        print("  DraftKings standings: nothing new to grade")


def tiles(a):
    """Each graded night's team tiles (the mirror's dk_cbb_teams.json as it stood before the first game) against what
    happened: the team's top 5 by salary, their actual DraftKings points against what their salary implied at that
    night's rate (every team's top 5: actual points per $1,000 of salary). One row per team in tiles_eval.csv."""
    mirror = Mirror(a.mirror)
    done = {(r["date"], r["draft_group"]) for r in read(TILES_EVAL)}
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "????-??-??_*.csv"))):
        rec = read(f)
        if not rec or (rec[0]["date"], rec[0]["draft_group"]) in done:
            continue
        g = rec[0]["draft_group"]
        day = iso(rec[0]["date"] + "T00:00:00Z")
        start = None
        for t, sha in reversed(mirror.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
            s = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
            if s:
                start = iso(s["start"])
                break
        doc = at_lock(mirror, "dk_cbb_teams.json", start, g) if start else None
        T = ((doc or {}).get("slates") or {}).get(g)
        if not T:
            print("  tiles %s: none saved before lock" % g)
            continue
        top5 = {}
        for t in T["teams"]:
            v = sorted([r for r in rec if r["team"] == t["team"] and r["status"] != "Out"], key=lambda r: -num(r["salary"]))[:5]
            top5[t["team"]] = (sum(num(r["salary"]) for r in v), sum(num(r["actual_dk"]) or 0 for r in v))
        sal, pts = sum(x[0] for x in top5.values()), sum(x[1] for x in top5.values())
        rate = pts / sal if sal else 0
        for t in T["teams"]:
            s5, a5 = top5[t["team"]]
            rk = t.get("ranks") or {}
            out.append({"date": rec[0]["date"], "draft_group": g, "team": t["team"], "verdict": t["verdict"], "total": t["total"],
                        "borderline": int(bool(t.get("borderline"))),
                        "quality": t.get("quality", ""), "leverage": t.get("leverage", ""), "pts_rank": rk.get("pts", ""),
                        "value_rank": rk.get("value", ""), "conc_rank": rk.get("conc", ""), "blowout_rank": rk.get("blowout", ""),
                        "lev_rank": rk.get("lev", ""), "ranked_against": T["slate"].get("ranked_against", ""),
                        "value": round(t["value"], 3), "conc": round(t["conc"], 3) if t["conc"] is not None else "",
                        "own_gap": round(t["own_gap"], 3), "blowout": t["blowout"] if t["blowout"] is not None else "",
                        "blowout_games": t["blowout_games"], "fragile": int(bool(t["fragile"])), "top5_salary": s5,
                        "top5_actual": round(a5, 2), "top5_implied": round(s5 * rate, 2), "beat": int(a5 > s5 * rate),
                        "phase": phase(rec[0]["date"]), "version": (doc or {}).get("version", "")})
        print("  tiles %s (%s): %d teams graded" % (g, rec[0]["date"], len(T["teams"])))
    if out:
        new = not os.path.exists(TILES_EVAL)
        with open(TILES_EVAL, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=TILE_COLS)
            if new:
                w.writeheader()
            w.writerows(out)


def corr(a, b):
    if len(a) < 3 or not S.pstdev(a) or not S.pstdev(b):
        return 0.0
    ma, mb = S.mean(a), S.mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (len(a) * S.pstdev(a) * S.pstdev(b))


def fit_weights():
    """Quality's weights fitted on the earlier 2/3 of the logged slates (least squares of the top 5's actual - implied
    points on the four ranks, negative weights set to 0, the rest scaled to sum to 1), and checked on the later 1/3:
    the correlation of quality with that margin, fitted weights against equal. None before FIT_MIN_SLATES slates."""
    tl = [r for r in read(TILES_EVAL) if r.get("pts_rank") not in ("", None)]
    slates = sorted({(r["date"], r["draft_group"]) for r in tl})
    if len(slates) < FIT_MIN_SLATES:
        return {"slates": len(slates), "use": False, "note": "fitted from %d slates on" % FIT_MIN_SLATES}
    cut = slates[(2 * len(slates)) // 3 - 1]
    train = [r for r in tl if (r["date"], r["draft_group"]) <= cut]
    test = [r for r in tl if (r["date"], r["draft_group"]) > cut]
    X = [[1.0] + [num(r[k + "_rank"]) for k in QUALITY] for r in train]
    y = [num(r["top5_actual"]) - num(r["top5_implied"]) for r in train]
    n = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) for j in range(n)] for i in range(n)]
    v = [sum(x[i] * yi for x, yi in zip(X, y)) for i in range(n)]
    for i in range(n):                        # Gaussian elimination
        for j in range(i + 1, n):
            f = A[j][i] / A[i][i] if A[i][i] else 0
            A[j] = [aj - f * ai for aj, ai in zip(A[j], A[i])]
            v[j] -= f * v[i]
    beta = [0.0] * n
    for i in reversed(range(n)):
        beta[i] = (v[i] - sum(A[i][j] * beta[j] for j in range(i + 1, n))) / A[i][i] if A[i][i] else 0.0
    raw = [max(0.0, b) for b in beta[1:]]
    w = {k: (b / sum(raw) if sum(raw) else 0.25) for k, b in zip(QUALITY, raw)}
    eq = {k: 0.25 for k in QUALITY}
    q = lambda r, ws: sum(ws[k] * num(r[k + "_rank"]) for k in QUALITY)
    m = [num(r["top5_actual"]) - num(r["top5_implied"]) for r in test]
    cf, ce = corr([q(r, w) for r in test], m), corr([q(r, eq) for r in test], m)
    return {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "slates": len(slates),
            "train_slates": len([s for s in slates if s <= cut]), "test_slates": len([s for s in slates if s > cut]),
            "weights": {k: round(x, 3) for k, x in w.items()}, "equal": eq, "test_corr_fitted": round(cf, 3), "test_corr_equal": round(ce, 3),
            "use": cf > ce}


def weights(a):
    """Fit, and write analysis/cbb/dk/team_weights.json: the tiles use the fitted weights only when use is true."""
    w = fit_weights()
    if "weights" in w:
        with open(WEIGHTS, "w") as f:
            json.dump(w, f, indent=1)
            f.write("\n")
    print(weights_line(w))


def weights_line(w):
    if "weights" not in w:
        return "   Quality weights: equal (%d graded slates; %s)" % (w["slates"], w["note"])
    return ("   Quality weights fitted on %d slates, tested on the next %d: fitted %s (correlation with the top 5's beat %.2f) against equal"
            " (%.2f): %s" % (w["train_slates"], w["test_slates"], ", ".join("%s %.2f" % kv for kv in w["weights"].items()),
                             w["test_corr_fitted"], w["test_corr_equal"], "the fitted weights are in use" if w["use"] else "equal weights stay"))


def records():
    return [r for f in sorted(glob.glob(os.path.join(DK, "????-??-??_*.csv"))) for r in read(f)]


def band_name(b):
    return "$%s+" % format(b["lo"], ",") if b["hi"] > 9999 else "$%s-%s" % (format(b["lo"], ","), format(b["hi"], ","))


def gate(a):
    rows = [r for r in records() if r["status"] != "Out" and num(r["fp_dk"]) is not None and num(r["actual_dk"]) is not None]
    nights = sorted({r["date"] for r in rows})
    bands = []
    for lo, hi in BANDS:
        v = [r for r in rows if lo <= num(r["salary"]) <= hi and num(r["dk_avg"])]
        b = {"lo": lo, "hi": hi, "n": len(v), "nights": len({r["date"] for r in v}), "open": False, "w": 1.0}
        if v:
            b["mae_ours"] = round(S.mean(abs(num(r["fp_dk"]) - num(r["actual_dk"])) for r in v), 3)
            b["mae_avg"] = round(S.mean(abs(num(r["dk_avg"]) - num(r["actual_dk"])) for r in v), 3)
            won = 0
            for d in {r["date"] for r in v}:
                vd = [r for r in v if r["date"] == d]
                won += S.mean(abs(num(r["dk_avg"]) - num(r["actual_dk"])) for r in vd) < S.mean(abs(num(r["fp_dk"]) - num(r["actual_dk"])) for r in vd)
            b["nights_avg_won"] = won
            if b["nights"] >= GATE_NIGHTS and b["n"] >= GATE_N and b["mae_avg"] < b["mae_ours"] and won >= GATE_SHARE * b["nights"]:
                # least squares on actual - avg = w x (ours - avg)
                x = [num(r["fp_dk"]) - num(r["dk_avg"]) for r in v]
                y = [num(r["actual_dk"]) - num(r["dk_avg"]) for r in v]
                sxx = sum(xi * xi for xi in x)
                b.update(open=True, w=round(max(0.0, min(1.0, sum(xi * yi for xi, yi in zip(x, y)) / sxx if sxx else 1.0)), 3))
        bands.append(b)
    doc = {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "nights": len(nights), "bands": bands,
           "rule": "open where DraftKings' average beat ours: %d+ nights, %d+ player-nights, lower mean error, better on %d%%+ of nights"
                   % (GATE_NIGHTS, GATE_N, 100 * GATE_SHARE)}
    cb, today = CALIBRATION_BLEND, dt.datetime.now(PT).date().isoformat()
    if today >= cb["from"] and PROJ_CHOICE in (None, "blend", "dk"):    # every band at w, whatever the rule says
        w = 0.0 if PROJ_CHOICE == "dk" else cb["w"]
        for b in bands:
            b.update(open=True, w=w)
        doc.update(override=("calibration blend, ours %d%% / DraftKings' average %d%% in every band, until the owner's choice at the freeze"
                             if PROJ_CHOICE is None else "the owner's choice at the freeze: %s in every band" % (
                                 "DraftKings' average" if PROJ_CHOICE == "dk" else "the %d/%d blend" % (round(100 * w), round(100 * (1 - w)))))
                   % ((round(100 * w), round(100 * (1 - w))) if PROJ_CHOICE is None else ()), version=cb["version"])
    with open(GATE, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print("Projection gate (%d graded nights): %s" % (len(nights), "; ".join(
        "%s %s (n=%d, ours %s vs DK avg %s)" % (band_name(b), "OPEN w=%.2f" % b["w"] if b["open"] else "closed",
                                                b["n"], b.get("mae_ours", "-"), b.get("mae_avg", "-")) for b in bands)))


def ranks(v):
    """Ranks, ties averaged (for rank correlation)."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    return corr(ranks(a), ranks(b)) if len(a) >= 3 else None


def sal_band(salary):
    return next(b for b in BANDS if b[0] <= salary <= b[1])


def audit_rows():
    """Every recorded DK player-night that counts for the audit: not tagged Out, with his actual points (0 if he sat)."""
    out = []
    for r in records():
        act, ours = num(r["actual_dk"]), num(r["fp_dk"])
        if r.get("status") == "Out" or act is None or ours is None or num(r["salary"]) is None:
            continue
        out.append(dict(r, act=act, ours=ours, sal=num(r["salary"]), dkavg=num(r.get("dk_avg")), last5=num(r.get("dk_last5")),
                        own_proj=num(r.get("own"))))
    return out


def fmt_stats(v, act):
    """(n, average miss, bias, rank correlation) for projections v against actuals act."""
    if not v:
        return None
    d = [x - y for x, y in zip(v, act)]
    return len(v), S.mean(abs(x) for x in d), S.mean(d), spearman(v, act)


def proj_audit(rows):
    """a: by salary band (and all), ours against DK's average (players with one) and against last-5 (players with one)."""
    out = []
    for b in BANDS + [(0, 99999)]:
        rs = [r for r in rows if b[0] <= r["sal"] <= b[1]]
        withavg = [r for r in rs if r["dkavg"] is not None]
        with5 = [r for r in rs if r["last5"] is not None]
        out.append({"band": "all" if b == (0, 99999) else band_name({"lo": b[0], "hi": b[1]}),
                    "ours": fmt_stats([r["ours"] for r in withavg], [r["act"] for r in withavg]),
                    "dkavg": fmt_stats([r["dkavg"] for r in withavg], [r["act"] for r in withavg]),
                    "blend": fmt_stats([BLEND_W * r["ours"] + (1 - BLEND_W) * r["dkavg"] for r in withavg], [r["act"] for r in withavg]),
                    "ours5": fmt_stats([r["ours"] for r in with5], [r["act"] for r in with5]),
                    "last5": fmt_stats([r["last5"] for r in with5], [r["act"] for r in with5])})
    return out


def own_nights(rows):
    """b and c's data: per slate, its biggest graded contest's actual ownership on every audit player (0 if absent from
    the standings: nobody drafted him). {draft group: [row with own_act]}"""
    ev, oe = read(EVAL), read(OWN_EVAL)
    size = {}
    for r in ev:
        if num(r.get("entries")) and (r["draft_group"] not in size or num(r["entries"]) > size[r["draft_group"]][1]):
            size[r["draft_group"]] = (r["contest_id"], num(r["entries"]))
    act = defaultdict(dict)
    for r in oe:
        if size.get(str(r["draft_group"]), (None,))[0] == r["contest_id"]:
            act[str(r["draft_group"])][r["dk_id"]] = num(r["own_actual"])
    nights = defaultdict(list)
    for r in rows:
        g = str(r["draft_group"])
        if g in act:
            nights[g].append(dict(r, own_act=act[g].get(r["dk_id"], 0.0) or 0.0))
    return nights


def own_audit(nights):
    """b: projected against actual ownership, by projected-ownership band (and all)."""
    rows = [r for v in nights.values() for r in v if r["own_proj"] is not None]
    out = []
    for lo, hi in OWN_BANDS + [(0, 101)]:
        rs = [r for r in rows if lo <= r["own_proj"] < hi]
        st = fmt_stats([r["own_proj"] for r in rs], [r["own_act"] for r in rs])
        out.append({"band": "all" if (lo, hi) == (0, 101) else "%d-%d%%" % (lo, hi) if hi < 101 else "%d%%+" % lo, "stats": st})
    return out


def industry(nights):
    """c: each player's disagreement (actual ownership minus what our value implied) and his outcome against ours. beat is
    his miss (actual - ours) less the season's median miss for players projected like him (PROJ_BINS), so the field
    isn't credited with how misses run at a projection level: outcomes can't go below 0 and run skewed, so low
    projections beat theirs more often, and the field's disagreements lean toward some projection levels."""
    out = []
    pbin = lambda x: next(i for i, e in enumerate(PROJ_BINS) if x < e)
    misses = defaultdict(list)
    for rs in nights.values():
        for r in rs:
            misses[pbin(r["ours"])].append(r["act"] - r["ours"])
    med = {k: (sorted(v)[(len(v) - 1) // 2] + sorted(v)[len(v) // 2]) / 2 for k, v in misses.items()}
    for g, rs in nights.items():
        by_value = sorted(rs, key=lambda r: -(r["ours"] / (r["sal"] / 1000)))
        owns = sorted((r["own_act"] for r in rs), reverse=True)
        for r, implied in zip(by_value, owns):
            mp, m5 = num(r.get("min_proj")), num(r.get("min_last5"))
            chg = "unknown" if mp is None or m5 is None else "up %d+" % MIN_CHANGE if mp - m5 >= MIN_CHANGE else \
                  "down %d+" % MIN_CHANGE if m5 - mp >= MIN_CHANGE else "within %d" % MIN_CHANGE
            out.append(dict(r, implied=implied, d=r["own_act"] - implied, beat=r["act"] - r["ours"] - med[pbin(r["ours"])], min_change=chg))
    return out


def field_right(rs):
    """The share of players where the field's disagreement pointed the right way (liked more: beat ours; less: fell short)."""
    v = [(r["beat"] > 0) == (r["d"] > 0) for r in rs if r["beat"] != 0]
    return (sum(v) / len(v), len(v)) if v else (None, 0)


def keeps_right(rs):
    """(text, flagged): the field's right share with its slate consistency (slates where it was right on more than half
    / slates measured), flagged only when it's right well beyond chance (2.5 standard errors over 50%, 20+ players) AND
    on 2/3+ of 5+ slates: the slate is the unit that replicates, not the player."""
    fr, n = field_right(rs)
    by = defaultdict(list)
    for r in rs:
        by[r["draft_group"]].append(r)
    nights = [field_right(v)[0] for v in by.values()]
    nights = [x for x in nights if x is not None]
    won = sum(x > 0.5 for x in nights)
    flag = (fr is not None and n >= 20 and (fr - 0.5) / (0.25 / n) ** 0.5 >= 2.5 and len(nights) >= 5 and won >= 2 * len(nights) / 3)
    return ("%s of %d, right on %d of %d slates" % ("%.0f%%" % (100 * fr) if fr is not None else "-", n, won, len(nights)), flag)


def print_audit(full):
    rows = audit_rows()
    if not rows:
        print("  audit: no recorded DK slates yet")
        return
    last = max(r["date"] for r in rows)
    print("Audit, projections and ownership first (%d DK slates recorded, %d player-nights; last night %s)" % (
        len({r["draft_group"] for r in rows}), len(rows), last))
    f = lambda st: "-" if not st else "%4.1f %+5.1f %s" % (st[1], st[2], "%.2f" % st[3] if st[3] is not None else "  - ")
    for name, rs in (("last night", [r for r in rows if r["date"] == last]), ("season", rows)):
        a = proj_audit(rs)
        if full:
            print("\n  a. Projections, %s (average miss, bias = projection minus actual, rank correlation; DK points):" % name)
            proj_table(a)
        else:
            al = a[-1]
            print("  a. Projections, %s: ours %s, DK average %s, 50/50 blend %s%s (miss, bias, rank corr; %d players)" % (
                name, f(al["ours"]), f(al["dkavg"]), f(al["blend"]), "" if not al["last5"] else "; on the %d with a last-5: ours %s, last-5 %s" % (
                    al["ours5"][0], f(al["ours5"]), f(al["last5"])), al["ours"][0] if al["ours"] else 0))
    nights = own_nights(rows)
    if not nights:
        print("  b, c. Ownership: no graded standings yet")
        return
    lastg = {str(r["draft_group"]) for r in rows if r["date"] == last}
    for name, ns in (("last night", {g: v for g, v in nights.items() if g in lastg}), ("season", nights)):
        if not ns:
            continue
        b = own_audit(ns)
        if full:
            print("\n  b. Ownership, %s (%d slates' biggest graded contest; projected against actual, ownership points):" % (name, len(ns)))
            print("     %-10s %5s  %-17s" % ("projected", "n", "miss bias rank"))
            for x in b:
                if x["stats"]:
                    print("     %-10s %5d  %s" % (x["band"], x["stats"][0], f(x["stats"])))
        else:
            al = b[-1]["stats"]
            print("  b. Ownership, %s: miss %.1f, bias %+.1f, rank corr %s (%d players, %d slates)" % (
                name, al[1], al[2], "%.2f" % al[3] if al[3] is not None else "-", al[0], len(ns)))
    ind = industry(nights)
    big = [r for r in ind if abs(r["d"]) >= AUDIT_DISAGREE]
    fr, n = field_right(big)
    more = [r for r in big if r["d"] > 0]
    less = [r for r in big if r["d"] < 0]
    if not full:
        print("  c. The field against our value, season: disagreed by %d+ points on %d players; the field was right on %s "
              "(liked more: %d, beat ours by %+.1f against the usual miss at his projection; liked less: %d, %+.1f)%s" % (
                  AUDIT_DISAGREE, len(big), keeps_right(big)[0], len(more),
                  S.mean(r["beat"] for r in more) if more else 0, len(less), S.mean(r["beat"] for r in less) if less else 0,
                  "; FIELD KEEPS BEING RIGHT: see the readout for where" if keeps_right(big)[1] else ""))
        return
    print("\n  c. Ownership as the industry's view, season (actual ownership minus what our value implied, and the player against our projection):")
    print("     (beat ours: his miss against the season's median miss for players projected like him, so how misses run at a level doesn't count)")
    print("     %-26s %5s  %12s  %10s  %11s" % ("the field", "n", "vs median", "beat ours", "field right"))
    for lo, hi, label in DISAGREE_BINS:
        rs = [r for r in ind if lo <= r["d"] < hi]
        if not rs:
            continue
        fr2, _ = field_right(rs) if label != "within 2" else (None, 0)
        print("     %-26s %5d  %+12.1f  %9.0f%%  %11s" % (label, len(rs), S.mean(r["beat"] for r in rs),
              100 * sum(r["beat"] > 0 for r in rs) / len(rs), "%.0f%%" % (100 * fr2) if fr2 is not None else ""))
    print("     Where they disagreed by %d+ points, the field right by:" % AUDIT_DISAGREE)
    for key, name in (("band", "salary band"), ("position", "position"), ("min_change", "minutes (projected against his last 5)")):
        groups = defaultdict(list)
        for r in big:
            k = band_name({"lo": sal_band(r["sal"])[0], "hi": sal_band(r["sal"])[1]}) if key == "band" else r.get(key) or "?"
            groups[k].append(r)
        print("       %s: %s" % (name, "; ".join("%s %s%s" % (k, keeps_right(v)[0], " (FIELD KEEPS BEING RIGHT)" if keeps_right(v)[1] else "")
              for k, v in sorted(groups.items()))))
    print("     'field right': liked more and he beat our projection, or liked less and he fell short. FIELD KEEPS BEING RIGHT only when it's")
    print("     right well beyond chance (2.5 standard errors over 50%, 20+ players) and on 2/3+ of 5+ slates; anything short of that is directional.")


def versions():
    return read(VERSIONS)


def version_of(date):
    """The version in effect on a slate's date: the latest versions.csv label dated on or before it."""
    v = [r for r in versions() if r["date"] <= str(date)]
    return v[-1]["version"] if v else "-"


def proj_table(a):
    f = lambda st: "-" if not st else "%4.1f %+5.1f %s" % (st[1], st[2], "%.2f" % st[3] if st[3] is not None else "  - ")
    print("     %-14s %5s  %-17s %-17s %-17s | %5s  %-17s %-17s" % ("salary band", "n", "ours", "DK average", "50/50 blend", "n", "ours", "last-5"))
    for b in a:
        n = b["ours"][0] if b["ours"] else 0
        n5 = b["ours5"][0] if b["ours5"] else 0
        print("     %-14s %5d  %-17s %-17s %-17s | %5d  %-17s %-17s" % (b["band"], n, f(b["ours"]), f(b["dkavg"]), f(b["blend"]), n5, f(b["ours5"]), f(b["last5"])))


def calweek(a):
    """For the owner's choice at the freeze: ours, DraftKings' average and the 50/50 blend (and last-5) over the
    calibration week's graded nights, by salary band, and on how many nights each had the lowest average miss."""
    rows = [r for r in audit_rows() if CAL_WEEK[0] <= r["date"] <= CAL_WEEK[1]]
    nights = sorted({r["date"] for r in rows})
    print("Calibration week %s to %s: %d graded nights, %d player-nights. Which projection freezes is the owner's call; until"
          " then the blend stays on (dk_eval.py PROJ_CHOICE: %s)." % (CAL_WEEK[0], CAL_WEEK[1], len(nights), len(rows), PROJ_CHOICE or "not chosen"))
    if not rows:
        return
    print("  Average miss, bias (projection minus actual), rank correlation, DK points:")
    proj_table(proj_audit(rows))
    won = defaultdict(int)
    for d in nights:
        al = proj_audit([r for r in rows if r["date"] == d])[-1]
        best = min(("ours", "DK average", "50/50 blend"), key=lambda k: al[{"ours": "ours", "DK average": "dkavg", "50/50 blend": "blend"}[k]][1])
        won[best] += 1
    print("  Lowest average miss, night by night: " + ", ".join("%s %d of %d" % (k, won[k], len(nights)) for k in ("ours", "DK average", "50/50 blend")))


def cut_line(g):
    """The calibration note's cut line for one slate: kept against cut, average score and each entered contest's top-10%
    rate, from cut_eval.csv; and whether 'kept averages more but reaches the top 10% less' held (the contests' mean rate)."""
    rows = [r for r in read(CUT_EVAL) if str(r["draft_group"]) == str(g) and r["tag"] == "all"]
    k = {r["contest"]: r for r in rows if r["group"] == "kept"}
    c = {r["contest"]: r for r in rows if r["group"] == "cut"}
    if not k or not c:
        return None, None
    km, cm = num(next(iter(k.values()))["mean"]), num(next(iter(c.values()))["mean"])
    both = [n for n in k if n in c and k[n]["top10"] not in ("", None)]
    if not both:
        return "kept averaged %.1f, cut %.1f (no graded standings yet)" % (km, cm), None
    kt, ct = S.mean(num(k[n]["top10"]) for n in both), S.mean(num(c[n]["top10"]) for n in both)
    held = km > cm and kt < ct
    return ("kept averaged %.1f, cut %.1f; top 10%%, kept / cut: %s" % (km, cm, ", ".join(
        "%s %.1f%% / %.1f%%" % (re.sub(r"^CBB \$[\d.,K]+ ", "", n).split(" [")[0], 100 * num(k[n]["top10"]), 100 * num(c[n]["top10"])) for n in sorted(both)))), held


def audit(a):
    print_audit(full=False)


def calnote(a):
    """The calibration week's morning note: bugs found, the audit's a / b / c in one line each, and the changes made
    since the last graded slate with their reasons (versions.csv)."""
    import contextlib
    import io
    rows = audit_rows()
    last = max((r["date"] for r in rows), default="")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_audit(full=False)
    lines = buf.getvalue().splitlines()
    pick = lambda pre: next((l.strip() for l in lines if l.strip().startswith(pre)), pre + " -")
    new = [r for r in versions() if r["date"] > last]
    bugs = [r for r in new if r["reason"].startswith("Bug")]
    changes = [r for r in new if not r["reason"].startswith("Bug")]
    print("Calibration note, %s (last graded slate %s; version now %s)" % (dt.datetime.now(PT).date().isoformat(), last or "-",
                                                                           versions()[-1]["version"] if versions() else "-"))
    print("Bugs found: " + ("; ".join("%s (%s)" % (r["change"], r["reason"][5:].strip()) for r in bugs) if bugs else "none"))
    print(pick("a. Projections, last night"))
    print(pick("b. Ownership, last night"))
    print(pick("c. "))
    cuts = sorted({(r["date"], r["draft_group"]) for r in read(CUT_EVAL)})
    line, _ = cut_line(cuts[-1][1]) if cuts else (None, None)
    held = [cut_line(g)[1] for _, g in cuts]
    held = [h for h in held if h is not None]
    print("Cut check, last night: %s. 'Kept averages more but reaches the top 10%% less' held on %d of %d graded nights." % (
        line or "no saved bank scored yet", sum(held), len(held)))
    print("Changes: " + ("; ".join("%s %s: %s (why: %s)" % (r["version"], r["component"], r["change"], r["reason"]) for r in changes) if changes else "none"))


def readout(a):
    print_audit(full=True)
    print()
    ev, kind = counted(read(EVAL))
    print("DraftKings CBB readout, %s" % dt.date.today().isoformat())
    slates = sorted({r["draft_group"] for r in ev})
    print("\n1. Rule sets and your entries against the field (%d %s slates; the decision waits for %d counted, from the freeze after %s)" % (
        len(slates), kind, DECISION_SLATES, FREEZE_END))
    if kind == "warm-up" and ev:
        print("   WARM-UP: these slates ran before the freeze, on code still being tweaked (versions: %s); they don't count." %
              ", ".join(sorted({r.get("version") or "?" for r in ev})))
    if not ev:
        print("   nothing graded yet: the standings files start it")
    else:
        # one value per slate and who: lineups-weighted across that slate's graded contests
        per = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0.0]))
        for r in ev:
            t = per[r["draft_group"]][r["who"]]
            n = num(r["lineups"])
            t[0] += num(r["top10"]) * n; t[1] += num(r["cash"]) * n; t[2] += n; t[3] += num(r["dollars_back"]); t[4] += num(r["fees"])
        who_all = sorted({w for s in per.values() for w in s}, key=lambda w: (w == "mine", w != "none", w))
        print("   %-8s %7s %8s %8s %12s %22s %22s" % ("", "slates", "top 10%", "cash", "$ back/fees", "top10 vs none: won, gap", "cash vs none: won, gap"))
        for w in who_all:
            sl = [s for s in per if w in per[s]]
            t10 = [per[s][w][0] / per[s][w][2] for s in sl]
            ca = [per[s][w][1] / per[s][w][2] for s in sl]
            back, fees = sum(per[s][w][3] for s in sl), sum(per[s][w][4] for s in sl)
            pair = ""
            pair_c = ""
            if w != "none":
                both = [s for s in sl if "none" in per[s]]
                g10 = [per[s][w][0] / per[s][w][2] - per[s]["none"][0] / per[s]["none"][2] for s in both]
                gc = [per[s][w][1] / per[s][w][2] - per[s]["none"][1] / per[s]["none"][2] for s in both]
                if both:
                    pair = "%d of %d, %+.1f pts" % (sum(g > 0 for g in g10), sum(g != 0 for g in g10), 100 * S.mean(g10))
                    pair_c = "%d of %d, %+.1f pts" % (sum(g > 0 for g in gc), sum(g != 0 for g in gc), 100 * S.mean(gc))
            print("   %-8s %7d %7.1f%% %7.1f%% %12s %22s %22s" % (w, len(sl), 100 * S.mean(t10), 100 * S.mean(ca),
                  "%.2f / %.2f" % (back, fees), pair, pair_c))
        print("   The field's top-10% rate is 10% by definition; its cash rate is the contest's paid places over entries."
              " 'won': slates where the rule set's rate beat No extra rules' (ties left out), 'gap': the mean of the per-slate differences.")
        # by version (versions.csv): each slate under the changes in effect on its date
        byv = defaultdict(lambda: defaultdict(list))
        for r in ev:
            byv[version_of(r["date"])][r["who"]].append(r)
        print("\n   By version (versions.csv; a slate counts under the version in effect on its date):")
        for v in sorted(byv):
            parts = []
            for w in ("mine", "none"):
                x = byv[v].get(w) or []
                if x:
                    n = sum(num(r["lineups"]) for r in x)
                    parts.append("%s top 10%% %.1f%%, cash %.1f%%" % (w, 100 * sum(num(r["top10"]) * num(r["lineups"]) for r in x) / n,
                                                                    100 * sum(num(r["cash"]) * num(r["lineups"]) for r in x) / n))
            print("   %-8s %d slates: %s" % (v, len({r["draft_group"] for w in byv[v] for r in byv[v][w]}), "; ".join(parts) or "-"))
        # against random sets of the same size from the portfolio's own pool: no skill in the pick is ~50
        print("\n   Against %d random sets of the same size from each portfolio's own pool (percentile: 50 = no better than"
              " chance; slates beating the random median on the top-10%% rate):" % RANDOM_SETS)
        print("   %-12s %7s %9s %9s %9s %16s %22s" % ("", "slates", "top 10%", "cash", "dollars", "beat median", "pool avg vs field avg"))
        for w in sorted({r["who"] for r in ev}, key=lambda w: (w == "mine", w not in ("none", "top20_alone"), w)):
            v = [r for r in ev if r["who"] == w and r.get("pct_top10") not in ("", None)]
            if not v:
                continue
            sl = sorted({r["draft_group"] for r in v})
            def per_slate(col):     # a slate's percentile: the mean over its graded contests
                return [S.mean(num(r[col]) for r in v if r["draft_group"] == g) for g in sl]
            t10 = per_slate("pct_top10")
            gap = S.mean(num(r["pool_avg"]) - num(r["field_avg"]) for r in v if num(r.get("pool_avg")) is not None)
            print("   %-12s %7d %9.0f %9.0f %9.0f %16s %+21.1f" % (w, len(sl), S.mean(t10), S.mean(per_slate("pct_cash")),
                  S.mean(per_slate("pct_dollars")), "%d of %d" % (sum(x > 50 for x in t10), len(sl)), gap))
        print("   none: the 20-pick on No extra rules' pool; top20_alone: that pool's top 20 by expected payout alone; hand / auto:"
              " the DK page's hand-built 20 and its auto-pick, from the same saved pool; mine: your entries, against the saved"
              " build's pool (else No extra rules').")
        for x, y in (("none", "top20_alone"), ("hand", "auto")):
            both = sorted({r["draft_group"] for r in ev if r["who"] == x} & {r["draft_group"] for r in ev if r["who"] == y})
            if both:
                d = [S.mean(num(r["top10"]) for r in ev if r["who"] == x and r["draft_group"] == g)
                     - S.mean(num(r["top10"]) for r in ev if r["who"] == y and r["draft_group"] == g) for g in both]
                print("   %s against %s, top-10%% rate slate by slate: %d of %d slates won, mean gap %+.1f pts" % (
                    x, y, sum(g > 0 for g in d), sum(g != 0 for g in d), 100 * S.mean(d)))
        if kind == "counted" and len(slates) >= DECISION_SLATES:
            beat = [w for w in who_all if S.mean(per[s][w][0] / per[s][w][2] for s in per if w in per[s]) > 0.10]
            print("   DECISION (%d slates): beating the field's 10%% top-10 rate: %s" % (len(slates), ", ".join(beat) or "none: cut back"))
        cuts = list({r["contest_id"]: r for r in ev if r["sim_top10"] not in ("", None)}.values())   # once a contest
        if cuts:
            for k in ("win", "top10", "cash"):
                d = [num(r["field_" + k]) - num(r["sim_" + k]) for r in cuts if num(r["field_" + k]) is not None and num(r["sim_" + k]) is not None]
                if d:
                    print("   cut line %-6s real - sim: %+.1f points on average (%d contests the shadow was built for)" % (k, S.mean(d), len(d)))

    # nights each rule template was used (the owner's saved rules with his entries): his results on those nights
    mine = [r for r in ev if r["who"] == "mine" and r.get("rules") not in (None, "", "not saved")]
    if mine:
        print("\n   Your entries on nights each rule template was used (directional only: few nights, and the nights differ):")
        uses = [(name, lambda r, k=k: k in r["rules"].split()) for k, name in RULE_NAMES.items()]
        uses.append(("the cut's Protect % a tag", lambda r: any(t.startswith("protect") for t in r["rules"].split())))
        for name, used_on in uses:
            on = [r for r in mine if used_on(r)]
            off = [r for r in mine if not used_on(r)]
            if on:
                print("   %-42s used %d nights: top 10%% %4.1f%%, cash %4.1f%% | not used %d: top 10%% %s, cash %s" % (
                    name, len({r["draft_group"] for r in on}), 100 * S.mean(num(r["top10"]) for r in on), 100 * S.mean(num(r["cash"]) for r in on),
                    len({r["draft_group"] for r in off}), "%4.1f%%" % (100 * S.mean(num(r["top10"]) for r in off)) if off else "-",
                    "%4.1f%%" % (100 * S.mean(num(r["cash"]) for r in off)) if off else "-"))

    tl, _ = counted(read(TILES_EVAL))
    te = read(TEAM_EVAL)
    quad = {(r["date"], r["draft_group"], r["team"]): r["verdict"] for r in tl}
    print("\n1b. Team tiles by quadrant (%d team-nights, %d nights). The three targets:" % (len(tl), len({(r["date"], r["draft_group"]) for r in tl})))
    print("   1 the top 5 by salary beat their salary-implied points; 2 the team's actual points share beat its real ownership"
          " (standings); 3 2+ of its players in the contest's top-1% lineups, against the field's rate of playing 2+ of them")
    for v in QUADS:
        x = [r for r in tl if r["verdict"] == v]
        y = [r for r in te if quad.get((r["date"], str(r["draft_group"]), r["team"])) == v]
        z = [r for r in y if r["top1_rate"] not in ("", None) and r["field_rate"] not in ("", None)]
        if not x and not y:
            continue
        print("   %-8s n=%-4d 1: %s | 2: %s | 3: %s" % (v, len(x),
              "%3.0f%%" % (100 * S.mean(int(r["beat"]) for r in x)) if x else "-",
              "%3.0f%% (n=%d)" % (100 * S.mean(int(r["beat_own"]) for r in y), len(y)) if y else "-",
              ("top 1%% %.0f%% vs field %.0f%%, ahead in %d of %d" % (100 * S.mean(num(r["top1_rate"]) for r in z), 100 * S.mean(num(r["field_rate"]) for r in z),
               sum(num(r["top1_rate"]) > num(r["field_rate"]) for r in z), len(z))) if z else "-"))
    if tl:
        print("   Ranked against: %s." % ", ".join(sorted({r["ranked_against"] for r in tl if r.get("ranked_against")})))
    print(weights_line(fit_weights()))

    print("\n2. Projected ownership against real %Drafted: the audit's b, at the top")

    rec = [r for r in records() if r["status"] != "Out" and num(r["fp_dk"]) and num(r["miss_dk"])]
    print("\n3. The sim's players against reality (%d player-nights, %d nights)" % (len(rec), len({r["date"] for r in rec})))
    played = [r for r in rec if num(r["min"])]
    z = [(num(r["actual_dk"]) - num(r["fp_dk"])) / num(r["miss_dk"]) for r in played]
    if z:
        try:
            zs = json.load(open(a.sim_z))["z"] if a.sim_z else None
        except Exception:
            zs = None
        if zs:
            dec = [0] * 10
            for x in z:
                dec[min(9, int(10 * sum(q <= x for q in zs) / len(zs)))] += 1
            print("   where real scores fell in the sim's range, by tenth (10% each if the sim's spread is right): " +
                  " ".join("%.0f" % (100 * d / len(z)) for d in dec))
        print("   misses in expected misses: sd %.2f (the sim draws %.2f)" % (S.pstdev(z), SIM_Z_SD))
    # correlation of misses within a game, and the spread of game totals
    by_game = defaultdict(list)
    for r in rec:
        by_game[(r["date"], r.get("game"))].append(r)
    tm, op = [], []
    for v in by_game.values():
        v = [r for r in v if num(r["min"]) and num(r["fp_dk"]) >= 10]
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                zi = (num(v[i]["actual_dk"]) - num(v[i]["fp_dk"])) / num(v[i]["miss_dk"])
                zj = (num(v[j]["actual_dk"]) - num(v[j]["fp_dk"])) / num(v[j]["miss_dk"])
                (tm if v[i]["team"] == v[j]["team"] else op).append((zi, zj))

    def corr(p):
        if len(p) < 30:
            return None
        p = p + [(b, a2) for a2, b in p]
        xs, ys = zip(*p)
        mx, my, sx, sy = S.mean(xs), S.mean(ys), S.pstdev(xs), S.pstdev(ys)
        return sum((x - mx) * (y - my) for x, y in p) / (len(p) * sx * sy) if sx and sy else None
    ct, co = corr(tm), corr(op)
    print("   correlation of misses, players projected 10+: teammates %s (%d pairs), opponents %s (%d pairs); the sim takes both"
          " as 0 (2025-26: -0.007, -0.004)" % ("%.3f" % ct if ct is not None else "-", len(tm), "%.3f" % co if co is not None else "-", len(op)))
    # the pivot and bring-back rules lean on this: when a team's #1 (its highest projection) busts (a miss of 1+
    # expected misses under), how his teammates and the opponents projected 10+ did, against nights he didn't
    bust, fine = {"mates": [], "opp": []}, {"mates": [], "opp": []}
    nights = defaultdict(list)
    for r in rec:
        nights[(r["date"], r["draft_group"])].append(r)
    for v in nights.values():
        for team in {r["team"] for r in v}:
            mine_ = [r for r in v if r["team"] == team]
            one = max(mine_, key=lambda r: num(r["fp_dk"]))
            if not num(one["min"]) and not num(one["actual_dk"]):
                continue                            # he sat: that's news, not a bust
            z1 = (num(one["actual_dk"]) - num(one["fp_dk"])) / num(one["miss_dk"])
            side = bust if z1 <= -1 else fine
            for r in v:
                if r is one or num(r["fp_dk"]) < 10 or r.get("game") != one.get("game"):
                    continue
                z = (num(r["actual_dk"]) - num(r["fp_dk"])) / num(r["miss_dk"])
                (side["mates"] if r["team"] == team else side["opp"]).append(z)
    for k, name in (("mates", "teammates"), ("opp", "opponents")):
        if bust[k] and fine[k]:
            print("   a team's #1 busting: his %s' misses %+.2f (n=%d) against %+.2f when he didn't (n=%d), in expected misses;"
                  " the sim draws them the same either way" % (name, S.mean(bust[k]), len(bust[k]), S.mean(fine[k]), len(fine[k])))
        else:
            print("   a team's #1 busting: his %s: not enough nights yet (%d player-nights beside a bust, %d beside none)" % (
                name, len(bust[k]), len(fine[k])))
    real, sim = [], []
    for v in by_game.values():
        if len(v) >= 10:
            real.append(sum(num(r["actual_dk"]) for r in v) - sum(num(r["fp_dk"]) for r in v))
            sim.append(math.sqrt(sum((SIM_Z_SD * num(r["miss_dk"])) ** 2 for r in v)))
    if len(real) >= 5:
        print("   game totals (every projected player in the game): real misses spread %.1f against the sim's %.1f (n=%d games);"
              " real wider means missing in-game correlation" % (S.pstdev(real), S.mean(sim), len(real)))

    try:
        gt = json.load(open(GATE))
        print("\n4. Projection gate (%d graded nights): %s" % (gt["nights"], "; ".join(
            "%s %s" % (band_name(b), "OPEN w=%.2f" % b["w"] if b["open"] else "closed") for b in gt["bands"])))
    except Exception:
        print("\n4. Projection gate: no gate file yet")


def cutcheck(a):
    """The nightly cut check (see the docstring): one row per saved bank, rule tag ("all" for the whole bank), group
    (cut / kept / entered) and, once standings are graded, entered contest."""
    banks = {}
    for f in sorted(glob.glob(os.path.join(BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or ""):
            banks[g] = b
    ev = read(EVAL)
    out = []
    for g, b in sorted(banks.items(), key=lambda kv: kv[1].get("day") or ""):
        rec = read(os.path.join(DK, "%s_%s.csv" % (b["day"], g)))
        pts = {r["dk_id"]: num(r["actual_dk"]) for r in rec}
        if not rec or not any(v is not None for v in pts.values()):
            print("  cut check %s (%s): no real points recorded yet" % (g, b["day"]))
            continue
        pool = b["pool"]
        score = [sum(pts.get(str(i)) or 0 for i in L) for L in pool]
        entered = sorted({k for ks in (b.get("portfolios") or {}).values() for k in ks})
        kept = set(b["final"]) if b.get("final") else set(range(len(pool)))
        groups = {"cut": [k for k in range(len(pool)) if k not in kept], "kept": sorted(kept), "entered": entered}
        lines = {r["contest_id"]: r for r in ev if str(r["draft_group"]) == g and r["contest_id"] in (b.get("portfolios") or {})}
        tags = ["all"] + sorted({t for ts in b["tags"] for t in ts})
        protect = (b.get("cut") or {}).get("protect") or ""
        for tag in tags:
            member = (lambda k: True) if tag == "all" else (lambda k, t=tag: t in b["tags"][k])
            for grp, ks in groups.items():
                ks = [k for k in ks if member(k)]
                if not ks:
                    continue
                v = [score[k] for k in ks]
                row = {"date": b["day"], "draft_group": g, "tag": tag, "group": grp, "lineups": len(ks), "mean": round(S.mean(v), 2),
                       "best": round(max(v), 2), "protect": protect, "phase": phase(b["day"])}
                if not lines:
                    out.append(dict(row, contest_id="", contest="", top10="", cash="", wins=""))
                for cid, L in sorted(lines.items()):
                    t10, cash, win = num(L["field_top10"]), num(L["field_cash"]), num(L["field_win"])
                    out.append(dict(row, contest_id=cid, contest=L["contest"],
                                    top10=round(sum(x >= t10 for x in v) / len(v), 4) if t10 is not None else "",
                                    cash=round(sum(x >= cash for x in v) / len(v), 4) if cash is not None else "",
                                    wins=sum(x >= win for x in v) if win is not None else ""))
        # the night in brief: each tag's kept against cut, and whether the cut held anything better than what was entered
        best_in = max((score[k] for k in entered), default=None)
        print("  cut check %s (%s): %d banked, %d kept, %d entered%s; best entered %s, best kept %.1f, best cut %.1f%s" % (
            g, b["day"], len(pool), len(kept), len(entered), ", protect %s%%" % protect if protect else "",
            "%.1f" % best_in if best_in is not None else "-", max(score[k] for k in kept),
            max((score[k] for k in groups["cut"]), default=0), "" if lines else " (no graded standings yet: points only)"))
        for tag in tags[1:]:
            ks = [k for k in range(len(pool)) if tag in b["tags"][k]]
            kk = [score[k] for k in ks if k in kept]
            cc = [score[k] for k in ks if k not in kept]
            print("    %-70s kept %4d mean %5.1f best %5.1f | cut %4d mean %5.1f best %5.1f" % (
                tag[:70], len(kk), S.mean(kk) if kk else 0, max(kk, default=0), len(cc), S.mean(cc) if cc else 0, max(cc, default=0)))
    if out:
        with open(CUT_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CUT_COLS)
            w.writeheader()
            w.writerows(out)
        print("  cut_eval.csv: %d rows" % len(out))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nightly")
    n.add_argument("--mirror", required=True)
    sub.add_parser("gate")
    sub.add_parser("weights")
    t = sub.add_parser("tiles")
    t.add_argument("--mirror", required=True)
    sub.add_parser("cutcheck")
    sub.add_parser("audit")
    sub.add_parser("calnote")
    sub.add_parser("calweek")
    r = sub.add_parser("readout")
    r.add_argument("--sim-z", dest="sim_z", help="a dk_cbb_field.json, for the sim's draw shape (default: none)")
    a = ap.parse_args()
    os.makedirs(STANDINGS, exist_ok=True)
    return {"nightly": nightly, "gate": gate, "tiles": tiles, "weights": weights, "readout": readout, "cutcheck": cutcheck, "audit": audit, "calnote": calnote, "calweek": calweek}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
