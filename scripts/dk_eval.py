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
  risers    analysis/cbb/dk/riser_eval.csv, nightly: does the cut's lean pick players who beat their projections? For
            each saved bank with a cut and real points, every player in RISER_MIN+ of the banked or the kept lineups:
            his share of each, the change (kept less banked), projection, actual, actual minus projection, projected
            ownership. Graded by the night (a night's players move together, so the night is the unit): risers (change
            +RISER_STEP+) against fallers (-RISER_STEP or more) on actual minus projection, and the rank correlation of
            the change with it; across nights, the nights risers beat fallers and the average gap. The owner's question
            (2026-11-17): are the players the cut raises the ones to be overweight on? 2026-11-16 (the old cut): no.
  pairs     analysis/cbb/dk/pair_eval.csv, nightly: the team tiles' platoon pairs (as they stood at lock) graded, both
            sets: EvanMiya's position bands and role (the tiles' pairs from 2026-11-18) and ESPN's G or F/C (the set they
            replaced, still computed beside them): each pair split (one over projection, one under), both over or both
            under, against the baseline of any two teammates both projected PAIR_BASE_MIN+ minutes on the same slates;
            for the owner at PAIR_REPORT_NIGHTS graded slates with both sets, to check the band cutoffs (2.33 / 3.67,
            role gap 1.0) against data.
  platoon   analysis/cbb/dk/platoon_eval.csv, nightly: the spot check of each platoon rule (Never together, from the
            tiles) used in a saved bank, from the bank's rule_log (the DK page records it each draw): the pair's result
            against projection (both over, both under, or split: the negative pairing held; a player who didn't play
            counts as under), how many of the draws' rule-free lineups it blocked, their projected points against those
            passing (positive: it blocked lineups projected higher), and on the real points the blocked lineups logged
            (up to 20 a draw) against the bank's lineups from the same draws. Flags, once a pair spans PLATOON_FLAG_DAYS:
            never binds (blocked none) and never held (never split).
  fills     analysis/cbb/dk/fill_eval.csv, nightly: would other parts of the bank have filled the contests better than
            the owner's picks? For each saved bank with graded standings in its entered contests, FILL_SETS random
            fills of the owner's own entry counts (each lineup in one contest only, as entered), drawn from the whole
            bank, the cut's kept and removed lineups, and each kept idea (group), every lineup paid alone against the
            contest's real field and payout table (the nightly grade's own lineup()): average dollars back and return
            on the fees, the share of lineups in the top 10%%, the best fill, and the share of fills beating the owner's
            entries in dollars. The night is the unit: across nights, how often the kept fills' average beat the entered.
  ideas     analysis/cbb/dk/idea_eval.csv, nightly: each saved bank's ideas (the tag each lineup was first drawn under),
            scored on the real points against each entered contest's real lines: banked, kept and entered counts,
            the kept share (kept / banked) and entered share (of the contest's entries), the top-10% and cash rates of
            the idea's banked lineups and of its entered ones, and where the entered set falls among RANDOM_SETS random
            sets of its size from the idea's own banked lineups. The readout groups ideas by kind (idea_kind: "2+ from
            a team", "game stack 3", "locks", ...) across nights, since a night's tags name its own teams.
  fieldcheck analysis/cbb/dk/field_eval.csv, nightly: the simulated field (the mirror's dk_cbb_field.json before lock)
            against each graded contest's real field, size-matched (both sampled to the smaller of the two, 1,000 at
            most, 20 draws): the share of entries holding a lineup another user also entered (the simulated field's
            lineups each count as their own user), distinct lineups per 1,000 entries, salary used (10th / 50th / 90th
            percentile, at the $50,000 cap, under $49,000), players by ownership band and the top one's ownership,
            lineups with 2+ to 5+ from one team, and (simulated) the average miss of its ownership against the real.
            Construction (construction(), against the contest's real ownership): players at or under 10% and at or
            above 40% per lineup, summed ownership, salary, the slate's games. Beside real and sim, the same for our
            bank, our cut (the saved build), our entered (the owner's standings entries) and each SHARP user's
            entries, with dup_field: the share of them some other real user also entered.
            field_metrics is the one definition; battle-royale-research scripts/dk_field_calibrate.py uses it.
            Every row: own_pct (the side's mean summed ownership as a percentile of the real field's) and night_tag
            (news / quiet, night_tag()). Also own_pos_eval.csv: the real field's top-10% / top-1% rates by own-sum
            percentile band; printed with duplication real vs simulated by night tag (tracking only, 2026-11-19).
  owncard   the ownership card, nightly (printed): ownership is the slate's main $15 contest's (BASE_CONTEST; else its
            biggest graded contest). Projected under 5% landed under 5%; OWN_DECIDE's 3 bands (settings are decided on
            these) and OWN_SHOW's 5 (read only): actual / projected, average miss, nights over; the other contests
            against the baseline; our projection's miss by baseline ownership; last night's leverage list (LEV_*); and
            last night's construction rows from field_eval.csv.
  scan      analysis/cbb/dk/scan_eval.csv, nightly (log only): each saved slate scan's stacks against the night's real field
            (the baseline contest): the share of real entries holding each stack that reached the top 10% / top 1%, the
            scan's top third against its bottom third, and team stacks by their tile verdict
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
# The Questionable discount (2026-11-18, the owner's call): a player tagged Questionable is projected at his projection
# x the measured factor, sum of actual / sum of projected over every graded Questionable player-night (Out excluded),
# once there are Q_MIN_N of them; written to gate.json, applied by dk_sim.js gatedProj (the page, the shadow sets) and
# battle-royale-research dk_cbb_field.py (the simulated field). 2026-11-16/17: 10 player-nights, 6 didn't play, the 4
# who did played 54 of 94 projected minutes; 29.5 of 151.6 points, 0.19.
Q_MIN_N = 5
OWN_BANDS = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 35), (35, 101)]
FIELD_EVAL = os.path.join(DK, "field_eval.csv")
FIELD_COLS = ["date", "draft_group", "contest_id", "contest", "side", "lineups", "matched_n", "dup_other", "distinct_per_1000",
              "sal_p10", "sal_p50", "sal_p90", "at_cap", "under_49k", "own_30", "own_20", "own_10", "own_5", "own_1", "top_own",
              "team2", "team3", "team4", "team5", "games", "low10", "high40", "own_sum", "sal_mean", "dup_field", "proj_mean", "own_proj", "punt1", "punt2", "own_pct", "night_tag", "own_mae", "params"]
# Ownership position and news nights (tracking, 2026-11-19, from the ETR show): own_pct, a side's mean summed ownership
# as a percentile of the real field's lineups' summed ownership; night_tag, "news" when a player projected NEWS_MIN+
# minutes in the morning run was Out (or Doubtful, which the projection outs) at lock and not in the morning, or was
# named out or doubtful by the news feed that day (its kind, or "doubtful" / "out" in its text), or was marked out on the page (the build's outs, saved from
# 2026-11-19), else "quiet". own_pos_eval.csv: the real field's top-10% and top-1% rates by
# own-sum percentile band of the real field.
NEWS_MIN = 20
NEWS_SAYS = r"\bdoubtful\b|\b(?:is|are|ruled|will be|listed as|remains?)\s+out\b|\bout\s+(?:tonight|for|vs\.?|versus|against|indefinitely)\b|\bwill not play\b|\bwon't play\b"
OWN_POS_EVAL = os.path.join(DK, "own_pos_eval.csv")
OWN_POS_COLS = ["date", "draft_group", "contest_id", "contest", "night_tag", "band", "entries", "top10", "top1"]
OWN_POS_BANDS = [(0, 10), (10, 25), (25, 50), (50, 75), (75, 100)]
# The construction rows beside real and sim (fieldcheck): our bank, our cut, our entered (the owner's standings entries)
# and each sharp user's. The owner's list, 2026-11-19.
SHARP = ["dbaggot3", "feartheturtle7"]
OWN_BANDS_FIELD = [(30, 101), (20, 30), (10, 20), (5, 10), (1, 5)]
IDEA_EVAL = os.path.join(DK, "idea_eval.csv")
IDEA_COLS = ["date", "draft_group", "idea", "kind", "contest_id", "contest", "banked", "kept", "entered", "kept_share", "entered_share",
             "banked_top10", "banked_cash", "entered_top10", "entered_cash", "pct_top10", "pct_cash", "version"]
PAIR_EVAL = os.path.join(DK, "pair_eval.csv")
PAIR_COLS = ["date", "draft_group", "set", "team", "starter", "bench", "pos", "corr", "games", "thin", "starter_beat", "bench_beat", "result"]
PAIR_BASE_MIN, PAIR_REPORT_NIGHTS = 12, 5
PLATOON_EVAL = os.path.join(DK, "platoon_eval.csv")
PLATOON_COLS = ["date", "draft_group", "pair", "starter_id", "bench_id", "starter_beat", "bench_beat", "result", "draws", "blocked", "of",
                "proj_gap", "real_blocked", "real_banked", "real_gap", "version"]
PLATOON_FLAG_DAYS = 14
FILL_EVAL = os.path.join(DK, "fill_eval.csv")
FILL_COLS = ["date", "draft_group", "subset", "lineups", "fills", "fees", "avg_dollars", "roi", "top10_rate", "best_fill",
             "beat_entered", "entered_dollars", "entered_top10_rate", "version"]
FILL_SETS = 1000
RISER_EVAL = os.path.join(DK, "riser_eval.csv")
RISER_COLS = ["date", "draft_group", "dk_id", "name", "team", "salary", "bank_share", "kept_share", "change", "proj", "actual", "beat",
              "own", "version"]
RISER_MIN, RISER_STEP = 0.03, 0.01
CUT_EVAL = os.path.join(DK, "cut_eval.csv")
CUT_COLS = ["date", "draft_group", "tag", "group", "lineups", "mean", "best", "contest_id", "contest", "top10", "cash", "wins",
            "protect", "phase"]
DECISION_SLATES = 30
CAP_DK = 50000
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


def slate_for(mirror, cid):
    """(record rows, slate, start) for a contest: the record whose slate lists it in the mirror's DraftKings file as it
    stood around its night; (None, None, None) if none does."""
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
                return rows, s, iso(s["start"])
    return None, None, None


def night_points(rec, players):
    """Every drafted player's DraftKings points: the standings' FPTS, else the record's."""
    pts = {r["dk_id"]: num(r["actual_dk"]) for r in rec}
    for r in rec:
        if r["name"] in players and players[r["name"]][1] is not None:
            pts[r["dk_id"]] = players[r["name"]][1]
    return pts


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
        rec, slate, start = slate_for(mirror, cid)
        if not rec:
            print("  %s: no graded DraftKings slate lists contest %s yet" % (os.path.basename(path), cid))
            continue
        contest = next(c for c in slate["contests"] if str(c["id"]) == cid)
        pay, fee, n = pay_table(contest.get("payouts")), contest.get("entry_fee") or 0, len(entries)
        paid = max(pay) if pay else 0
        field = sorted((e["points"] for e in entries), reverse=True)
        top10 = math.ceil(0.1 * n)
        cut = {"win": field[0], "top10": field[top10 - 1], "cash": field[paid - 1] if paid and paid <= n else None}
        by_name = {r["name"]: r for r in rec}
        pts = night_points(rec, players)
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
        none_pool = ((sh or {}).get("rulesets", {}).get("none") or {}).get("pool")
        mine_pool = (banks or builds)[-1]["pool"] if builds else none_pool       # no saved build: "No extra rules"' pool
        pr = ((banks[-1].get("cut") or {}).get("protect") if banks else None)     # the cut's protect setting, priced by the readout
        protected = " protect%d" % pr if pr else ""
        used = sorted({r["type"] for r in ((saved[-1].get("rule_set") or []) if saved else [])})   # the night's rules
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
        # the Auto-fill benchmark: what Pick portfolios would have entered from the same final pool (Save build, 2026-11-18)
        for b in [b for b in banks if (b.get("auto_portfolios") or {}).get(cid)][-1:]:
            grade("auto_kept", [lineup(b["pool"][i]) for i in b["auto_portfolios"][cid]], b["pool"], "the bank's")
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


def tiles_at_lock(mirror, date, g):
    """A slate's team tiles as the mirror held them before its first game (its start from the mirror's DraftKings file
    around the night), or None."""
    day, start = iso(date + "T00:00:00Z"), None
    for t, sha in reversed(mirror.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
        s = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
        if s:
            start = iso(s["start"])
            break
    doc = at_lock(mirror, "dk_cbb_teams.json", start, g) if start else None
    return ((doc or {}).get("slates") or {}).get(g)


def pairs(a):
    """The tiles' platoon pairs graded, nightly (see the docstring): every pair in both sets, rebuilt whole each run."""
    mirror = Mirror(a.mirror)
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "????-??-??_*.csv"))):
        rec = read(f)
        if not rec or not any(num(r["actual_dk"]) is not None for r in rec):
            continue
        g, d = rec[0]["draft_group"], rec[0]["date"]
        T = tiles_at_lock(mirror, d, g)
        if not T:
            continue
        by = {r["dk_id"]: r for r in rec}
        beat = lambda i: (num(by[i]["actual_dk"]) or 0) - num(by[i]["fp_dk"]) if i in by and num(by[i]["fp_dk"]) is not None else None
        for t in T["teams"]:
            if "platoon_espn" in t:                          # both sets, from 2026-11-18
                sets = (("em", t.get("platoon") or []), ("espn", t.get("platoon_espn") or []))
            elif "EvanMiya" in (t.get("platoon_rule") or ""):
                sets = (("em", t.get("platoon") or []),)
            else:                                            # before EvanMiya's bands, the pairs were ESPN's G or F/C
                sets = (("espn", t.get("platoon") or []),)
            for name, ps in sets:
                for p in ps:
                    sb, bb = beat(str(p["starter"]["id"])), beat(str(p["bench"]["id"]))
                    if sb is None or bb is None:
                        continue
                    out.append({"date": d, "draft_group": g, "set": name, "team": t["team"], "starter": p["starter"]["name"], "bench": p["bench"]["name"],
                                "pos": p.get("pos") or "", "corr": p["corr"], "games": p["games"], "thin": int(bool(p.get("thin"))),
                                "starter_beat": round(sb, 2), "bench_beat": round(bb, 2),
                                "result": "split" if (sb > 0) != (bb > 0) else "both over" if sb > 0 else "both under"})
    if out:
        with open(PAIR_EVAL, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=PAIR_COLS)
            w.writeheader()
            w.writerows(out)
    for line in pair_lines():
        print("  " + line)


def pair_lines():
    """Both platoon sets against each other and against any two rotation teammates, by how often a pair split."""
    rows = read(PAIR_EVAL)
    if not rows:
        return ["Platoon pair sets: none graded yet"]
    lines = []
    for name, label in (("em", "EvanMiya bands"), ("espn", "ESPN G or F/C")):
        rs = [r for r in rows if r["set"] == name]
        nights = len({(r["date"], r["draft_group"]) for r in rs})
        if rs:
            c = lambda res: sum(r["result"] == res for r in rs)
            lines.append("%s: %d pairs on %d graded slate%s; split %d (%.0f%%), both over %d, both under %d" % (
                label, len(rs), nights, "" if nights == 1 else "s", c("split"), 100 * c("split") / len(rs), c("both over"), c("both under")))
        else:
            lines.append("%s: none graded yet" % label)
    # the baseline: any two teammates both projected PAIR_BASE_MIN+ minutes, on the same graded slates
    slates = {(r["date"], r["draft_group"]) for r in rows}
    sp = tot = 0
    for f in sorted(glob.glob(os.path.join(DK, "????-??-??_*.csv"))):
        rec = read(f)
        if not rec or (rec[0]["date"], rec[0]["draft_group"]) not in slates:
            continue
        team = defaultdict(list)
        for r in rec:
            if num(r["min_proj"] or None) is not None and num(r["min_proj"]) >= PAIR_BASE_MIN and num(r["fp_dk"]) is not None and num(r["actual_dk"]) is not None:
                team[r["team"]].append(num(r["actual_dk"]) - num(r["fp_dk"]))
        for v in team.values():
            for i in range(len(v)):
                for j in range(i + 1, len(v)):
                    tot += 1; sp += (v[i] > 0) != (v[j] > 0)
    if tot:
        lines.append("Baseline, any two teammates projected %d+ minutes on those slates: %d pairs, split %.0f%%" % (PAIR_BASE_MIN, tot, 100 * sp / tot))
    n_em = len({(r["date"], r["draft_group"]) for r in rows if r["set"] == "em"})
    if n_em < PAIR_REPORT_NIGHTS:
        lines.append("(the comparison is for the owner at %d graded slates with both sets; %d so far)" % (PAIR_REPORT_NIGHTS, n_em))
    return lines


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
        T = tiles_at_lock(mirror, rec[0]["date"], g)
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
                        "phase": phase(rec[0]["date"]), "version": T.get("version", "")})
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
    qs = [r for r in rows if r["status"] == "Questionable"]
    qa, qp = sum(num(r["actual_dk"]) for r in qs), sum(num(r["fp_dk"]) for r in qs)
    quest = {"n": len(qs), "nights": len({r["date"] for r in qs}), "actual": round(qa, 2), "projected": round(qp, 2),
             "factor": round(qa / qp, 3) if len(qs) >= Q_MIN_N and qp else 1.0,
             "rule": "a Questionable player's projection x factor: actual / projected over the graded Questionable player-nights, "
                     "once there are %d" % Q_MIN_N}
    doc = {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "nights": len(nights), "bands": bands, "questionable": quest,
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
    print("Questionable: x%.2f (%d player-nights on %d nights: %.1f actual of %.1f projected)" % (quest["factor"], quest["n"], quest["nights"], qa, qp))
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
    """b and c's data: per slate, its baseline contest's actual ownership (baselines(): the main $15 contest, else the
    biggest graded one) on every audit player (0 if absent from the standings: nobody drafted him). {draft group: [row
    with own_act]}"""
    base = baselines()
    act = defaultdict(dict)
    for r in read(OWN_EVAL):
        if base.get(str(r["draft_group"]), (None,))[0] == r["contest_id"]:
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


def field_metrics(lineups, users, info, n, seed=3, draws=20):
    """A field's shape (fieldcheck): lineups, tuples of DK ids; users, each entry's user (None: each its own); info, DK id ->
    {salary, team}; n, the size both sides are sampled to for the size-dependent measures (duplication, distinct)."""
    rng = random.Random(seed)
    dup, dis = [], []
    for _ in range(draws if len(lineups) > n else 1):
        idx = rng.sample(range(len(lineups)), n) if len(lineups) > n else list(range(len(lineups)))
        who = defaultdict(set)
        for i in idx:
            who[lineups[i]].add(users[i] if users else i)
        dup.append(sum(1 for i in idx if len(who[lineups[i]]) > 1) / len(idx))
        dis.append(1000 * len(who) / len(idx))
    sal = sorted(sum(int(info[i]["salary"]) for i in L) for L in lineups)
    pct = lambda p: sal[min(len(sal) - 1, int(p * len(sal)))]
    cnt = defaultdict(int)
    for L in lineups:
        for i in L:
            cnt[i] += 1
    own = {i: 100 * c / len(lineups) for i, c in cnt.items()}
    team = lambda L, k: max(sum(1 for i in L if info[i]["team"] == t) for t in {info[i]["team"] for i in L}) >= k
    out = {"lineups": len(lineups), "matched_n": n, "dup_other": round(100 * S.mean(dup), 2), "distinct_per_1000": round(S.mean(dis)),
           "sal_p10": pct(0.1), "sal_p50": pct(0.5), "sal_p90": pct(0.9),
           "at_cap": round(100 * sum(x == CAP_DK for x in sal) / len(sal), 1), "under_49k": round(100 * sum(x < 49000 for x in sal) / len(sal), 1),
           "top_own": round(max(own.values()), 1), "team2": round(100 * sum(team(L, 2) for L in lineups) / len(lineups), 1),
           "team3": round(100 * sum(team(L, 3) for L in lineups) / len(lineups), 1),
           "team4": round(100 * sum(team(L, 4) for L in lineups) / len(lineups), 1),
           "team5": round(100 * sum(team(L, 5) for L in lineups) / len(lineups), 1)}
    for (lo, hi), col in zip(OWN_BANDS_FIELD, ("own_30", "own_20", "own_10", "own_5", "own_1")):
        out[col] = sum(1 for v in own.values() if lo <= v < hi)
    return out, own


PUNT_MIN = 15            # a punt: a player projected under this many minutes at lock (punt1 / punt2: lineups with 1+ / 2+)
COPIES_EVAL = os.path.join(DK, "copies_eval.csv")
SUPPLEMENT = os.path.join(DK, "contests_supplement.json")   # contests missing from the lobby files, from the owner's screenshots


def contest_info(slate, cid):
    """A contest's lobby record (entry fee, payouts) from the slate's lobby, else from SUPPLEMENT."""
    c = next((c for c in (slate or {}).get("contests") or [] if str(c.get("id")) == str(cid)), None)
    if c and c.get("payouts"):
        return c
    sup = (json.load(open(SUPPLEMENT)).get("contests") or {}) if os.path.exists(SUPPLEMENT) else {}
    return sup.get(str(cid)) or c
COPIES_COLS = ["date", "draft_group", "contest_id", "contest", "bucket", "entries", "share", "fees", "won", "roi"]
COPY_BUCKETS = [("unique", 0, 0), ("1-2", 1, 2), ("3-9", 3, 9), ("10+", 10, 10 ** 9)]


def copies_rows(path, contest, base):
    """A contest's real entries by copies (other USERS holding the same 8 players; the same user's re-entries aren't
    copies): each bucket's share of entries and its ROI, prizes split among entries tied on points (the payout
    table from the lobby)."""
    entries, _ = standings(path)
    pay = pay_table((contest or {}).get("payouts"))
    fee = num((contest or {}).get("entry_fee"))
    if not entries or not pay or not fee:
        return []
    users = defaultdict(set)
    key = [frozenset(lineup_names(e["lineup"])) for e in entries]
    for k, e in zip(key, entries):
        users[k].add((e["name"] or "").split(" (")[0].lower())
    order = sorted(range(len(entries)), key=lambda i: -entries[i]["points"])
    won, i = [0.0] * len(entries), 0
    while i < len(order):                   # a tie on points shares the prizes of the places it covers
        j = i
        while j + 1 < len(order) and entries[order[j + 1]]["points"] == entries[order[i]]["points"]:
            j += 1
        share = sum(pay.get(r, 0) for r in range(i + 1, j + 2)) / (j - i + 1)
        for k in order[i:j + 1]:
            won[k] = share
        i = j + 1
    out = []
    for name, lo, hi in COPY_BUCKETS:
        ix = [i for i, (k, e) in enumerate(zip(key, entries)) if lo <= len(users[k] - {(e["name"] or "").split(" (")[0].lower()}) <= hi]
        if ix:
            w = sum(won[i] for i in ix)
            out.append(dict(base, bucket=name, entries=len(ix), share=round(100 * len(ix) / len(entries), 1), fees=round(fee * len(ix), 2),
                            won=round(w, 2), roi=round(100 * (w - fee * len(ix)) / (fee * len(ix)), 1)))
    return out


def construction(lineups, ref, info, who=None, me=None, proj=None, pown=None, real_sums=None):
    """How a set of lineups is built against a contest's real ownership (ref: DK id -> % of its entries): players at or
    under 10% and at or above 40% per lineup, summed ownership and salary per lineup; with who (lineup -> the real
    field's users holding it), the share of the set's lineups some other real user (not me) also entered. With proj
    (DK id -> our projection at lock) and pown (DK id -> the simulated field's projected ownership): each lineup's
    projection and summed projected ownership, averaged (the bank check's two numbers, 2026-11-19)."""
    n = len(lineups)
    out = {"low10": round(sum(ref.get(i, 0) <= 10 for L in lineups for i in L) / n, 2),
           "high40": round(sum(ref.get(i, 0) >= 40 for L in lineups for i in L) / n, 2),
           "own_sum": round(sum(ref.get(i, 0) for L in lineups for i in L) / n),
           "sal_mean": round(sum(int(info[i]["salary"]) for L in lineups for i in L) / n), "dup_field": ""}
    if who is not None:
        out["dup_field"] = round(100 * sum(bool(who.get(L, set()) - {me}) for L in lineups) / n, 1)
    out["proj_mean"] = round(sum(proj.get(i, 0) for L in lineups for i in L) / n, 1) if proj else ""
    out["own_proj"] = round(sum(pown.get(i, 0) for L in lineups for i in L) / n) if pown else ""
    pu = [sum((num(info[i].get("min")) or 0) < PUNT_MIN for i in L) for L in lineups]
    out["punt1"], out["punt2"] = round(100 * sum(x >= 1 for x in pu) / n, 1), round(100 * sum(x >= 2 for x in pu) / n, 1)
    out["own_pct"] = ""
    if real_sums:                # real_sums: the real field's lineups' summed ownership, sorted
        import bisect
        out["own_pct"] = round(100 * bisect.bisect_left(real_sums, sum(ref.get(i, 0) for L in lineups for i in L) / n) / len(real_sums))
    return out


def night_tag(mirror, date, g, start, build):
    """"news" or "quiet" (see NEWS_MIN): the morning run's first version of the slate against the version at lock."""
    first = None
    for _, sha in mirror.versions("dk_cbb_morning.json", iso(date + "T00:00:00Z"), start):
        first = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g and x.get("players")), None)
        if first:               # the first version with the slate's rows (a slate can be listed before its rows fill)
            break
    last = None
    for _, sha in reversed(mirror.versions("dk_cbb_morning.json", iso(date + "T00:00:00Z"), start)):
        last = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
        if last:
            break
    if not first or not last:
        return ""
    big = {k for k, r in first["players"].items() if (num(r.get("min")) or 0) >= NEWS_MIN and r.get("status") != "Out"}
    late = {k for k in big if (last["players"].get(k) or {}).get("status") == "Out" or (last["players"].get(k) or {}).get("doubtful")}
    marked = big & {str(k) for k in ((build or {}).get("outs") or {})}
    # the news feed that day (every version up to lock: the file keeps only recent items): an item about him filed out
    # or doubtful, or a status item (any kind but plain "news") saying so in its text (11-18's Stokes "is doubtful
    # tonight" was filed questionable, before the doubtful kind existed); a bare "out" in commentary doesn't count
    said = set()
    for _, sha in mirror.versions("cbb_news.json", iso(date + "T00:00:00Z"), start):
        for x in (mirror.show(sha, "cbb_news.json") or {}).get("items") or []:
            if str(x.get("at", ""))[:10] >= date and (x.get("kind") in ("out", "doubtful") or x.get("kind") != "news" and re.search(NEWS_SAYS, x.get("text") or "", re.I)):
                said |= big & {str(i) for i in x.get("players") or []}
    return "news" if late or marked or said else "quiet"


def own_pos_rows(path, byname, ref, base):
    """The real field's entries by own-sum percentile band (of the real field): each band's top-10% and top-1% rates."""
    entries, _ = standings(path)
    n = len(entries)
    t10, t1 = math.ceil(0.1 * n), max(1, math.ceil(0.01 * n))
    xs = []
    for e in entries:
        ids = [byname.get(nm) for nm in lineup_names(e.get("lineup") or "")]
        if len(ids) == 8 and all(ids):
            xs.append((sum(ref.get(i, 0) for i in ids), e["rank"]))
    if not xs:
        return []
    order = sorted(range(len(xs)), key=lambda k: xs[k][0])
    pct = [0] * len(xs)
    for j, k in enumerate(order):
        pct[k] = 100 * j / len(xs)
    out = []
    for lo, hi in OWN_POS_BANDS:
        ix = [k for k in range(len(xs)) if lo <= pct[k] < hi]
        if ix:
            out.append(dict(base, band="%d-%d" % (lo, hi), entries=len(ix), top10=round(sum(xs[k][1] <= t10 for k in ix) / len(ix), 4),
                            top1=round(sum(xs[k][1] <= t1 for k in ix) / len(ix), 4)))
    return out


def own_pos_lines():
    """Printed by fieldcheck: the real fields' top-10% / top-1% rates by own-sum band, and duplication real vs sim by night tag."""
    rs, out = read(OWN_POS_EVAL), []
    if rs:
        f = lambda sub, k: sum(num(r[k]) * int(r["entries"]) for r in sub) / max(1, sum(int(r["entries"]) for r in sub))
        out.append("Ownership position, %d contest-nights (real fields; own-sum percentile of the real field: top 10%% / top 1%%): " % len({(r["date"], r["contest_id"]) for r in rs}) +
                   "; ".join("%s %.1f%% / %.2f%%" % (b, 100 * f([r for r in rs if r["band"] == b], "top10"), 100 * f([r for r in rs if r["band"] == b], "top1"))
                             for b in ["%d-%d" % x for x in OWN_POS_BANDS] if any(r["band"] == b for r in rs)))
    fe = [r for r in read(FIELD_EVAL) if r.get("night_tag")]
    for tag in ("news", "quiet"):
        sub = [r for r in fe if r["night_tag"] == tag]
        real = [num(r["dup_other"]) for r in sub if r["side"] == "real" and num(r["dup_other"]) is not None]
        sim = [num(r["dup_other"]) for r in sub if r["side"] == "sim" and num(r["dup_other"]) is not None]
        if real and sim:
            out.append("Duplication on %s nights (%d contest-nights, %d nights): real %.1f%%, simulated %.1f%% of entries holding a lineup another user entered" % (
                tag, len(real), len({r["date"] for r in sub}), S.mean(real), S.mean(sim)))
    return out


def real_field(path, byname):
    """A standings file's entries as (lineups, users): each lineup's names matched to DK ids (byname: name -> id, only
    names that are unique on the slate); entries with an unmatched name are left out."""
    entries, _ = standings(path)
    L, U = [], []
    for x in entries:
        ids = [byname.get(nm) for nm in lineup_names(x.get("lineup") or "")]
        if len(ids) == 8 and all(ids):
            L.append(tuple(sorted(ids)))
            U.append((x["name"] or "").split(" (")[0].lower())
    return L, U, len(entries)


def fieldcheck(a):
    """The nightly field check (see the docstring): rows in field_eval.csv for every graded contest, rebuilt whole."""
    mirror, ev, out, copies, pos = Mirror(a.mirror), read(EVAL), [], [], []
    graded = {}
    for r in ev:
        graded.setdefault((r["date"], str(r["draft_group"])), {})[r["contest_id"]] = r["contest"]
    for (date, g), contests in sorted(graded.items()):
        slate = None
        for _, sha in reversed(mirror.versions("dk_cbb_morning.json", iso(date + "T00:00:00Z") - dt.timedelta(days=1),
                                               iso(date + "T00:00:00Z") + dt.timedelta(days=2))):
            slate = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
            if slate:
                break
        fd = at_lock(mirror, "dk_cbb_field.json", iso(slate["start"]), g) if slate else None
        F = ((fd or {}).get("slates") or {}).get(g) or {}
        if not slate or not F.get("field"):
            print("  field check %s (%s): no %s" % (g, date, "slate rows" if not slate else "simulated field saved before lock"))
            continue
        info = slate["players"]
        names = defaultdict(list)
        for k, r in info.items():
            names[r["name"]].append(k)
        byname = {nm: v[0] for nm, v in names.items() if len(v) == 1}
        sim = [tuple(sorted(L)) for L in F["field"]]
        games = len({r.get("game") for r in info.values()})
        # our projection at lock (through the gate, as the page shows it) and the simulated field's ownership
        pj = {k: num(r.get("fp_gate")) if num(r.get("fp_gate")) is not None else (num(r.get("fp_dk")) or 0) for k, r in info.items()}
        pown = F.get("own") or {}
        bf = os.path.join(BUILDS, "dk_bank_%s_%s.json" % (date, g))
        B = json.load(open(bf)) if os.path.exists(bf) else {}
        bank = [tuple(sorted(str(i) for i in L)) for L in B.get("pool") or []]
        cut = [bank[i] for i in B.get("final") or []]
        tag = night_tag(mirror, date, g, iso(slate["start"]), B)
        for cid, cname in sorted(contests.items()):
            path = os.path.join(STANDINGS, "contest-standings-%s.csv" % cid)
            if not os.path.exists(path):
                continue
            L, U, total = real_field(path, byname)
            copies += copies_rows(path, contest_info(slate, cid),
                                  {"date": date, "draft_group": g, "contest_id": cid, "contest": cname})
            n = min(len(L), len(sim), 1000)
            rm, rown = field_metrics(L, U, info, n)
            sm, sown = field_metrics(sim, None, info, n)
            sm["own_mae"] = round(S.mean(abs(sown.get(k, 0) - rown.get(k, 0)) for k in set(rown) | set(sown)), 2)
            base = {"date": date, "draft_group": g, "contest_id": cid, "contest": cname, "games": games, "night_tag": tag}
            rs_ = sorted(sum(rown.get(i, 0) for i in x) for x in L)
            pos += own_pos_rows(path, byname, rown, {"date": date, "draft_group": g, "contest_id": cid, "contest": cname, "night_tag": tag})
            out.append(dict(base, side="real", own_mae="", params="", **rm, **construction(L, rown, info, proj=pj, pown=pown, real_sums=rs_)))
            out.append(dict(base, side="sim", params=json.dumps(F.get("params")), **sm, **construction(sim, rown, info, proj=pj, pown=pown, real_sums=rs_)))
            who = defaultdict(set)
            for x, u in zip(L, U):
                who[x].add(u)
            sides = [("bank", bank, USER), ("cut", cut, USER), ("entered", [x for x, u in zip(L, U) if u == USER], USER)]
            sides += [("user:" + u, [x for x, v in zip(L, U) if v == u], u) for u in SHARP]
            for side, xs, me in sides:
                if xs:
                    m, _ = field_metrics(xs, None, info, len(xs))
                    out.append(dict(base, side=side, own_mae="", params="", **dict(m, dup_other=""),
                                    **construction(xs, rown, info, who, me, proj=pj, pown=pown, real_sums=rs_)))
        print("  field check %s (%s): %d contests" % (g, date, len(contests)))
    if out:
        with open(FIELD_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELD_COLS)
            w.writeheader()
            w.writerows(out)
    if copies:
        with open(COPIES_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COPIES_COLS)
            w.writeheader()
            w.writerows(copies)
    if pos:
        with open(OWN_POS_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=OWN_POS_COLS)
            w.writeheader()
            w.writerows(pos)
    for line in own_pos_lines():
        print(line)


def idea_kind(t):
    """An idea's kind, from its saved settings (the bank's tag_settings), without the night's teams and players: the
    rules' templates ("2+ from a team", "if/then", ...) and the settings off their defaults."""
    parts = []
    for r in t.get("conds") or []:
        if r.get("base"):           # baseline rules (every draw on the slate) aren't part of an idea; recorded, not kinded
            continue
        ty = r.get("type")
        parts.append("platoon never-together" if r.get("src") == "platoon" else
                     "stack with opponent" if str(r.get("label", "")).startswith("Stack ") else
                     "%d+ from a team" % r.get("n", 1) if ty == "min" else "exclude a team" if ty == "none" and len(r.get("ids") or []) > 1 else
                     "exclude a player" if ty == "none" else "if/then (%s)" % ty)
    if t.get("stackN"):
        parts.append("game stack %d%s" % (t["stackN"], " both teams" if t.get("stackBoth") else ""))
    if t.get("maxOwn") is not None:
        parts.append("ownership cap")
    if t.get("lowN"):
        parts.append("%d low-owned" % t["lowN"])
    if t.get("levW"):
        parts.append("leverage weight")
    if t.get("lock"):
        parts.append("locks")
    if t.get("excl"):
        parts.append("excludes")
    return " + ".join(sorted(set(parts))) or "no rules"


def ideas(a):
    """The nightly idea tracking (see the docstring), rebuilt whole each run like the cut check."""
    banks = {}
    for f in sorted(glob.glob(os.path.join(BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or ""):
            banks[g] = b
    ev, out, rng = read(EVAL), [], random.Random(11)
    for g, b in sorted(banks.items(), key=lambda kv: kv[1].get("day") or ""):
        rec = read(os.path.join(DK, "%s_%s.csv" % (b["day"], g)))
        pts = {r["dk_id"]: num(r["actual_dk"]) for r in rec}
        lines = {r["contest_id"]: r for r in ev if str(r["draft_group"]) == g and r["contest_id"] in (b.get("portfolios") or {}) and r["who"] == "mine"}
        if not rec or not lines:
            print("  ideas %s (%s): %s" % (g, b["day"], "no real points yet" if not rec else "no graded standings yet"))
            continue
        score = [sum(pts.get(str(i)) or 0 for i in L) for L in b["pool"]]
        idea = [t[0] for t in b["tags"]]
        kept = set(b["final"]) if b.get("final") else set(range(len(b["pool"])))
        settings = b.get("tag_settings") or {}
        for cid, L in sorted(lines.items()):
            t10, cash = num(L["field_top10"]), num(L["field_cash"])
            ent = (b.get("portfolios") or {}).get(cid) or []
            for name in sorted(set(idea)):
                mem = [k for k in range(len(b["pool"])) if idea[k] == name]
                ke, en = [k for k in mem if k in kept], [k for k in ent if idea[k] == name]
                rate = lambda ks, line: sum(score[k] >= line for k in ks) / len(ks) if ks and line is not None else ""
                row = {"date": b["day"], "draft_group": g, "idea": name, "kind": idea_kind(settings.get(name) or {}), "contest_id": cid,
                       "contest": L["contest"], "banked": len(mem), "kept": len(ke), "entered": len(en),
                       "kept_share": round(len(ke) / len(mem), 4), "entered_share": round(len(en) / len(ent), 4) if ent else "",
                       "banked_top10": rate(mem, t10), "banked_cash": rate(mem, cash), "entered_top10": rate(en, t10), "entered_cash": rate(en, cash),
                       "pct_top10": "", "pct_cash": "", "version": version_of(b["day"])}
                if en and len(mem) > len(en):     # the entered set among random sets of its size from the idea's banked lineups
                    for col, line in (("pct_top10", t10), ("pct_cash", cash)):
                        if line is None:
                            continue
                        me = sum(score[k] >= line for k in en)
                        rs = [sum(score[k] >= line for k in rng.sample(mem, len(en))) for _ in range(RANDOM_SETS)]
                        row[col] = round(100 * (sum(r < me for r in rs) + 0.5 * sum(r == me for r in rs)) / RANDOM_SETS, 1)
                out.append(row)
        print("  ideas %s (%s): %d ideas, %d contests" % (g, b["day"], len(set(idea)), len(lines)))
    if out:
        with open(IDEA_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=IDEA_COLS)
            w.writeheader()
            w.writerows(out)


def print_ideas():
    """The readout's ideas section: by kind across nights."""
    rows = read(IDEA_EVAL)
    print("\nIdeas by kind, across nights (idea_eval.csv; each night's ideas grouped by kind; rates against the real lines):")
    if not rows:
        print("   none graded yet")
        return
    print("   %-44s %6s %7s %7s %8s %9s %9s %10s %10s" % ("kind", "nights", "banked", "kept %", "entered", "bank t10", "ent t10", "ent cash", "pct t10"))
    by = defaultdict(list)
    for r in rows:
        by[r["kind"]].append(r)
    for k, v in sorted(by.items(), key=lambda kv: -sum(num(r["banked"]) for r in kv[1])):
        seen = {(r["draft_group"], r["idea"]) : r for r in v}.values()          # banked / kept once a night, not per contest
        banked, kept = sum(num(r["banked"]) for r in seen), sum(num(r["kept"]) for r in seen)
        en = [r for r in v if num(r["entered"])]
        wavg = lambda col, rs: sum(num(r[col]) * num(r["entered"]) for r in rs) / sum(num(r["entered"]) for r in rs) if rs else None
        bt = S.mean(num(r["banked_top10"]) for r in v if r["banked_top10"] not in ("", None)) if any(r["banked_top10"] not in ("", None) for r in v) else None
        pc = [num(r["pct_top10"]) for r in v if r["pct_top10"] not in ("", None)]
        print("   %-44s %6d %7d %6.0f%% %8d %8s %9s %10s %10s" % (k[:44], len({r["draft_group"] for r in v}), banked, 100 * kept / banked if banked else 0,
              sum(num(r["entered"]) for r in v), "%.1f%%" % (100 * bt) if bt is not None else "-",
              "%.1f%%" % (100 * wavg("entered_top10", en)) if en else "-", "%.1f%%" % (100 * wavg("entered_cash", en)) if en else "-",
              "%.0f" % S.mean(pc) if pc else "-"))
    print("   bank t10: the idea's banked lineups reaching the top 10% (is the idea good?); ent t10 / cash: its entered ones; pct t10:"
          " the entered set among random sets of its size from the idea's own bank (50 = the cut and pick chose no better than chance).")


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
    if getattr(a, "mirror", None):           # the match warning: players whose game found no ESPN match
        try:
            doc = json.load(open(os.path.join(a.mirror, "dk_cbb_morning.json")))
        except (OSError, ValueError):
            doc = {"slates": []}
        for sl in doc.get("slates", []):
            un = [r for r in sl["players"].values() if not r.get("event")]
            if un:
                print("MATCH WARNING, slate %s (%s): %d players unmatched (games %s): on DraftKings' average, no minutes, line or "
                      "fragility; their results can't be graded either" % (sl["draft_group_id"], sl.get("day"), len(un),
                                                                           ", ".join(sorted({r.get("game") or r.get("team") for r in un}))))
            else:
                print("Games matched, slate %s (%s): all %d players" % (sl["draft_group_id"], sl.get("day"), len(sl["players"])))
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
    for line in riser_lines() + fill_lines() + auto_lines() + platoon_lines() + pair_lines():
        print(line)
    fe = [r for r in read(FIELD_EVAL) if r["date"] == last]
    if fe:
        big = max(fe, key=lambda r: num(r["lineups"]) if r["side"] == "real" else 0)
        real = next(r for r in fe if r["contest_id"] == big["contest_id"] and r["side"] == "real")
        sim = next(r for r in fe if r["contest_id"] == big["contest_id"] and r["side"] == "sim")
        print("Field check, %s (size-matched at %s), real / sim: dup with another user %s%% / %s%%; distinct per 1,000 %s / %s; salary"
              " p10-p50-p90 %s-%s-%s / %s-%s-%s; at the cap %s%% / %s%%; under $49,000 %s%% / %s%%; players 30%%+ owned %s / %s; top owned"
              " %s%% / %s%%; 3+ from one team %s%% / %s%%; sim ownership miss %s" % (
                  big["contest"], real["matched_n"], real["dup_other"], sim["dup_other"], real["distinct_per_1000"], sim["distinct_per_1000"],
                  real["sal_p10"], real["sal_p50"], real["sal_p90"], sim["sal_p10"], sim["sal_p50"], sim["sal_p90"],
                  real["at_cap"], sim["at_cap"], real["under_49k"], sim["under_49k"], real["own_30"], sim["own_30"],
                  real["top_own"], sim["top_own"], real["team3"], sim["team3"], sim["own_mae"]))
        # duplication drift: the simulated field's rate (the night's contests averaged) outside the range of the real ones
        rd = [num(r["dup_other"]) for r in fe if r["side"] == "real"]
        sd = S.mean(num(r["dup_other"]) for r in fe if r["side"] == "sim")
        try:
            pr = json.loads(sim["params"] or "null") or {}
        except ValueError:
            pr = {}
        built = ("%d build styles" % len(pr["styles"])) if pr.get("styles") else "the original single style" if pr else "unknown settings"
        print(("DUPLICATION DRIFT: the simulated field (%s) %.1f%% against the real contests' %.1f-%.1f%% (field calibration, "
               "battle-royale-research dk_field_calibrate.py; the 11-22 refit)" if not min(rd) <= sd <= max(rd) else
               "Duplication in line: the simulated field (%s) %.1f%%, the real contests %.1f-%.1f%%") % (built, sd, min(rd), max(rd)))
    else:
        print("Field check: no graded field yet")
    print("Changes: " + ("; ".join("%s %s: %s (why: %s)" % (r["version"], r["component"], r["change"], r["reason"]) for r in changes) if changes else "none"))


def readout(a):
    print_audit(full=True)
    print_ideas()
    print()
    for line in riser_lines() + fill_lines() + auto_lines() + platoon_lines() + pair_lines():
        print(line)
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


def platoon(a):
    """The nightly platoon spot check (see the docstring), rebuilt whole each run."""
    banks = {}
    for f in sorted(glob.glob(os.path.join(BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or ""):
            banks[g] = b
    out = []
    for g, b in sorted(banks.items(), key=lambda kv: kv[1].get("day") or ""):
        log = b.get("rule_log") or []
        if not log:
            continue
        rec = {r["dk_id"]: r for r in read(os.path.join(DK, "%s_%s.csv" % (b["day"], g)))}
        if not any(num(r["actual_dk"]) is not None for r in rec.values()):
            print("  platoon %s (%s): no real points recorded yet" % (g, b["day"]))
            continue
        act = lambda i: num(rec[i]["actual_dk"]) or 0 if i in rec else 0
        score = lambda ids: sum(act(str(i)) for i in ids)
        by = {}
        for e in log:
            by.setdefault(tuple(e["ids"]), []).append(e)
        for (s_id, b_id), es in sorted(by.items()):
            beat = lambda i: (num(rec[i]["actual_dk"]) or 0) - num(rec[i]["fp_dk"]) if i in rec and num(rec[i]["fp_dk"]) is not None else None
            sb, bb = beat(str(s_id)), beat(str(b_id))
            res = "" if sb is None or bb is None else "both over" if sb > 0 and bb > 0 else "split" if (sb > 0) != (bb > 0) else "both under"
            blocked, of = sum(e["blocked"] for e in es), sum(e["of"] for e in es)
            gaps = [(e["gap"], e["blocked"]) for e in es if e.get("gap") is not None and e["blocked"]]
            sample = [x.split(",") for e in es for x in (e.get("sample") or [])]
            tags = {e["tag"] for e in es}
            banked = [score(L) for L, t in zip(b["pool"], b["tags"]) if t[0] in tags]
            rb = S.mean(score(L) for L in sample) if sample else None
            rk = S.mean(banked) if banked else None
            out.append({"date": b["day"], "draft_group": g, "pair": "%s / %s" % ((rec.get(str(s_id)) or {}).get("name", s_id), (rec.get(str(b_id)) or {}).get("name", b_id)),
                        "starter_id": s_id, "bench_id": b_id, "starter_beat": round(sb, 2) if sb is not None else "", "bench_beat": round(bb, 2) if bb is not None else "",
                        "result": res, "draws": len(es), "blocked": blocked, "of": of,
                        "proj_gap": round(sum(x * n for x, n in gaps) / sum(n for _, n in gaps), 2) if gaps else "",
                        "real_blocked": round(rb, 2) if rb is not None else "", "real_banked": round(rk, 2) if rk is not None else "",
                        "real_gap": round(rb - rk, 2) if rb is not None and rk is not None else "", "version": version_of(b["day"])})
    if out:
        with open(PLATOON_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=PLATOON_COLS)
            w.writeheader()
            w.writerows(out)
    for line in platoon_lines():
        print("  " + line)


def platoon_lines():
    """The platoon spot check: last night's rules, and the flags once a pair spans PLATOON_FLAG_DAYS."""
    rows = read(PLATOON_EVAL)
    if not rows:
        return ["Platoon rules: none graded yet (a bank saved with its rule log, and its night's points)"]
    last = max(r["date"] for r in rows)
    f = lambda x: "%+.1f" % num(x) if x not in ("", None) else "-"
    lines = ["Platoon rules, %s: " % last + "; ".join("%s %s (%s / %s vs projection), blocked %s of %s, projected %s, real %s" % (
        r["pair"], r["result"] or "-", f(r["starter_beat"]), f(r["bench_beat"]), r["blocked"], r["of"], f(r["proj_gap"]), f(r["real_gap"]))
        for r in rows if r["date"] == last)]
    by = {}
    for r in rows:
        by.setdefault((r["starter_id"], r["bench_id"]), []).append(r)
    flags = []
    for k, rs in by.items():
        days = (dt.date.fromisoformat(max(r["date"] for r in rs)) - dt.date.fromisoformat(min(r["date"] for r in rs))).days
        if days >= PLATOON_FLAG_DAYS:
            if not sum(int(r["blocked"]) for r in rs):
                flags.append("%s never binds (%d nights)" % (rs[-1]["pair"], len(rs)))
            if not any(r["result"] == "split" for r in rs):
                flags.append("%s never held: no split in %d nights" % (rs[-1]["pair"], len(rs)))
    lines.append("Platoon flags (pairs over %d+ days): %s" % (PLATOON_FLAG_DAYS, "; ".join(flags) if flags else "none"))
    return lines


def fills(a):
    """The nightly random-fill grade (see the docstring), rebuilt whole each run."""
    mirror = Mirror(a.mirror)
    banks = {}
    for f in sorted(glob.glob(os.path.join(BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or ""):
            banks[g] = b
    out, rng = [], random.Random(13)
    for g, b in sorted(banks.items(), key=lambda kv: kv[1].get("day") or ""):
        pf = {c: ks for c, ks in (b.get("portfolios") or {}).items() if ks}
        files = {c: os.path.join(STANDINGS, "contest-standings-%s.csv" % c) for c in pf}
        if not pf or not all(os.path.exists(p) for p in files.values()):
            print("  fills %s (%s): %s" % (g, b["day"], "no portfolios saved" if not pf else "standings missing for " +
                                          ", ".join(c for c, p in files.items() if not os.path.exists(p))))
            continue
        pool, kept = b["pool"], set(b.get("final") or range(len(b["pool"])))
        pay, fee = {}, {}
        for cid in pf:
            entries, players = standings(files[cid])
            rec, slate, _ = slate_for(mirror, cid)
            if not rec:
                break
            contest = next(c for c in slate["contests"] if str(c["id"]) == cid)
            table, n = pay_table(contest.get("payouts")), len(entries)
            field = sorted((e["points"] for e in entries), reverse=True)
            top10, pts = field[math.ceil(0.1 * n) - 1], night_points(rec, players)
            pay[cid] = [(table.get(placed(v, field), 0), v >= top10) for v in (sum(pts.get(str(i)) or 0 for i in L) for L in pool)]
            fee[cid] = contest.get("entry_fee") or 0
        if len(pay) < len(pf):
            print("  fills %s (%s): a contest's slate isn't in the mirror's history" % (g, b["day"]))
            continue
        fees = sum(fee[c] * len(ks) for c, ks in pf.items())
        n_ent = sum(len(ks) for ks in pf.values())
        e_dol = sum(pay[c][k][0] for c, ks in pf.items() for k in ks)
        e_t10 = sum(pay[c][k][1] for c, ks in pf.items() for k in ks) / n_ent
        grp = lambda k: (b.get("groups") or {}).get(b["tags"][k][0], b["tags"][k][0])
        subsets = [("bank", list(range(len(pool)))), ("kept", sorted(kept)), ("cut", [k for k in range(len(pool)) if k not in kept])]
        subsets += [("kept: " + gname, [k for k in sorted(kept) if grp(k) == gname]) for gname in sorted({grp(k) for k in kept})]
        for name, idx in subsets:
            if len(idx) < n_ent:
                continue
            dol, t10 = [], []
            for _ in range(FILL_SETS):
                pick = rng.sample(idx, n_ent)
                i, d, t = 0, 0.0, 0
                for c, ks in pf.items():
                    for k in pick[i:i + len(ks)]:
                        d += pay[c][k][0]; t += pay[c][k][1]
                    i += len(ks)
                dol.append(d); t10.append(t / n_ent)
            out.append({"date": b["day"], "draft_group": g, "subset": name, "lineups": len(idx), "fills": FILL_SETS, "fees": round(fees, 2),
                        "avg_dollars": round(S.mean(dol), 2), "roi": round(S.mean(dol) / fees, 4) if fees else "",
                        "top10_rate": round(S.mean(t10), 4), "best_fill": round(max(dol), 2),
                        "beat_entered": round(sum(d > e_dol for d in dol) / FILL_SETS, 4), "entered_dollars": round(e_dol, 2),
                        "entered_top10_rate": round(e_t10, 4), "version": version_of(b["day"])})
        print("  fills %s (%s): %d entries in %d contests, %d subsets" % (g, b["day"], n_ent, len(pf), len(subsets)))
    if out:
        with open(FILL_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FILL_COLS)
            w.writeheader()
            w.writerows(out)
    for line in fill_lines():
        print("  " + line)


def fill_lines():
    """The random-fill grade in two lines: last night, and across the graded nights."""
    rows = read(FILL_EVAL)
    if not rows:
        return ["Random fills: no night with a saved bank and its standings graded yet"]
    nights = sorted({(r["date"], r["draft_group"]) for r in rows})
    by = lambda d, g, sub: next((r for r in rows if (r["date"], r["draft_group"]) == (d, g) and r["subset"] == sub), None)
    d, g = nights[-1]
    e, k, bk, c = by(d, g, "kept"), by(d, g, "kept"), by(d, g, "bank"), by(d, g, "cut")
    ideas = sorted((r for r in rows if (r["date"], r["draft_group"]) == (d, g) and r["subset"].startswith("kept: ")),
                   key=lambda r: -num(r["avg_dollars"]))
    pc = lambda x: "%.0f%%" % (100 * num(x))
    line1 = ("Random fills, %s (your entry counts, %s fills each): yours $%.2f back on $%.2f (%s), top 10%% %s; average fill: bank $%.2f, "
             "kept $%.2f (beats yours %s), cut $%.2f; ideas (kept): %s" % (
                 d, k["fills"], num(k["entered_dollars"]), num(k["fees"]), pc(num(k["entered_dollars"]) / num(k["fees"]) if num(k["fees"]) else 0),
                 pc(k["entered_top10_rate"]), num(bk["avg_dollars"]), num(k["avg_dollars"]), pc(k["beat_entered"]), num(c["avg_dollars"]) if c else 0,
                 ", ".join("%s $%.2f" % (r["subset"][6:], num(r["avg_dollars"])) for r in ideas)))
    won = [num(by(dd, gg, "kept")["avg_dollars"]) > num(by(dd, gg, "kept")["entered_dollars"]) for dd, gg in nights if by(dd, gg, "kept")]
    line2 = "Random fills, %d graded night%s: the kept lineups' average fill beat your entries on %d%s" % (
        len(won), "" if len(won) == 1 else "s", sum(won), " (too few nights to say)" if len(won) < 10 else "")
    return [line1, line2]


def auto_lines():
    """Your entries against the Auto-fill benchmark (auto_kept), last night and across the nights that have both."""
    ev = read(EVAL)
    nights = {}
    for r in ev:
        if r["who"] in ("mine", "auto_kept"):
            d = nights.setdefault((r["date"], r["draft_group"]), {})
            x = d.setdefault(r["who"], [0.0, 0.0, 0])
            x[0] += num(r["dollars_back"]) or 0; x[1] += num(r["fees"]) or 0; x[2] += int(r["lineups"])
    both = sorted(k for k, v in nights.items() if "mine" in v and "auto_kept" in v)
    if not both:
        return ["Auto-fill benchmark: none graded yet (Save build records it once there's a cut and entry counts)"]
    m, au = nights[both[-1]]["mine"], nights[both[-1]]["auto_kept"]
    won = sum(nights[k]["auto_kept"][0] > nights[k]["mine"][0] for k in both)
    return ["Auto-fill benchmark, %s: yours $%.2f back on $%.2f, Auto-fill from the same final pool $%.2f on $%.2f; across %d night%s "
            "Auto-fill beat yours on %d%s" % (both[-1][0], m[0], m[1], au[0], au[1], len(both), "" if len(both) == 1 else "s", won,
                                             " (too few nights to say)" if len(both) < 10 else "")]


def risers(a):
    """The nightly riser / faller grade (see the docstring), rebuilt whole each run like the cut check."""
    banks = {}
    for f in sorted(glob.glob(os.path.join(BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or ""):
            banks[g] = b
    out = []
    for g, b in sorted(banks.items(), key=lambda kv: kv[1].get("day") or ""):
        if not b.get("final"):
            print("  risers %s (%s): no cut saved with the bank" % (g, b["day"]))
            continue
        rec = {r["dk_id"]: r for r in read(os.path.join(DK, "%s_%s.csv" % (b["day"], g)))}
        if not any(num(r["actual_dk"]) is not None for r in rec.values()):
            print("  risers %s (%s): no real points recorded yet" % (g, b["day"]))
            continue
        pool, kept = b["pool"], b["final"]

        def share(idx):
            c = {}
            for k in idx:
                for i in pool[k]:
                    c[str(i)] = c.get(str(i), 0) + 1
            return {i: v / len(idx) for i, v in c.items()}
        bk, kp = share(range(len(pool))), share(kept)
        for i in sorted(set(bk) | set(kp)):
            r = rec.get(i)
            if not r or max(bk.get(i, 0), kp.get(i, 0)) < RISER_MIN or num(r["actual_dk"]) is None or num(r["fp_dk"]) is None:
                continue
            out.append({"date": b["day"], "draft_group": g, "dk_id": i, "name": r["name"], "team": r["team"], "salary": r["salary"],
                        "bank_share": round(bk.get(i, 0), 4), "kept_share": round(kp.get(i, 0), 4), "change": round(kp.get(i, 0) - bk.get(i, 0), 4),
                        "proj": r["fp_dk"], "actual": r["actual_dk"], "beat": round(num(r["actual_dk"]) - num(r["fp_dk"]), 2),
                        "own": r["own"], "version": version_of(b["day"])})
    if out:
        with open(RISER_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=RISER_COLS)
            w.writeheader()
            w.writerows(out)
    for line in riser_lines():
        print("  " + line)


def riser_nights():
    """Per graded night: (date, players, risers n, their mean beat, fallers n, their mean beat, rank corr of change with beat)."""
    by = {}
    for r in read(RISER_EVAL):
        by.setdefault((r["date"], r["draft_group"]), []).append(r)
    out = []
    for (d, g), rs in sorted(by.items()):
        up = [num(r["beat"]) for r in rs if num(r["change"]) >= RISER_STEP]
        dn = [num(r["beat"]) for r in rs if num(r["change"]) <= -RISER_STEP]
        out.append((d, len(rs), len(up), S.mean(up) if up else None, len(dn), S.mean(dn) if dn else None,
                    spearman([num(r["change"]) for r in rs], [num(r["beat"]) for r in rs])))
    return out


def riser_lines():
    """The riser / faller grade in two lines: last night, and across the graded nights (the night as the unit)."""
    nights = riser_nights()
    if not nights:
        return ["Risers vs fallers: no night with a saved cut graded yet"]
    d, n, nu, mu, nd, md, rho = nights[-1]
    f = lambda x: "%+.1f" % x if x is not None else "-"
    both = [x for x in nights if x[3] is not None and x[5] is not None]
    gaps = [x[3] - x[5] for x in both]
    rhos = [x[6] for x in nights if x[6] is not None]
    return ["Risers vs fallers, %s (%d players in %d%%+ of the bank or the kept): %d risers %s against projection, %d fallers %s; "
            "rank correlation of the cut's change with actual minus projection %s" % (d, n, round(100 * RISER_MIN), nu, f(mu), nd, f(md),
                                                                                   "%+.2f" % rho if rho is not None else "-"),
            "Risers vs fallers, %d graded night%s: risers beat fallers on %d; average gap %s points, average rank correlation %s%s" % (
                len(nights), "" if len(nights) == 1 else "s", sum(g > 0 for g in gaps), f(S.mean(gaps)) if gaps else "-",
                "%+.2f" % S.mean(rhos) if rhos else "-", " (too few nights to say)" if len(nights) < 10 else "")]

# The ownership card (owncard): ownership is the main $15 contest's (the owner's baseline, 2026-11-19: BASE_CONTEST in
# its name, else the slate's biggest graded contest). Settings are decided on OWN_DECIDE's 3 bands; OWN_SHOW's 5 are read only.
BASE_CONTEST = "Pull Up Jumper"
OWN_DECIDE = [(0, 5), (5, 20), (20, 101)]
OWN_SHOW = [(0, 5), (5, 10), (10, 20), (20, 35), (35, 101)]
LEV_LOW, LEV_BEAT, LEV_HIGH, LEV_MISS = 5, 8, 25, 5     # the leverage list: under 5% owned beating projection by 8+, 25%+ missing by 5+


def baselines():
    """{draft group: (contest id, contest name, date)}: each slate's ownership baseline."""
    best = {}
    for r in read(EVAL):
        g, base = str(r["draft_group"]), BASE_CONTEST in r["contest"] and "(Early)" not in r["contest"]
        key = (base, num(r.get("entries")) or 0)
        if g not in best or key > best[g][0]:
            best[g] = (key, r["contest_id"], r["contest"], r["date"])
    return {g: v[1:] for g, v in best.items()}


def own_rows():
    """Every audit player-night with own_act: his ownership in the slate's baseline contest (0 if nobody drafted him),
    and own_by: {contest id: his ownership} for each of the slate's graded contests."""
    by = defaultdict(lambda: defaultdict(dict))
    for r in read(OWN_EVAL):
        by[str(r["draft_group"])][r["contest_id"]][r["dk_id"]] = num(r["own_actual"]) or 0.0
    out, base = [], baselines()
    for r in audit_rows():
        g = str(r["draft_group"])
        if g in base and base[g][0] in by[g]:
            out.append(dict(r, own_act=by[g][base[g][0]].get(r["dk_id"], 0.0), own_by={c: v.get(r["dk_id"], 0.0) for c, v in by[g].items()}))
    return out, base


def band_label(lo, hi):
    return "under %d" % hi if not lo else "%d+" % lo if hi > 100 else "%d-%d" % (lo, hi)


def band_line(rows, bands, proj, act, label):
    """One row a band: n, projected and actual means, actual / projected, average miss, and the nights it ran over
    (actual above projected) out of the nights it was measured."""
    out = []
    for lo, hi in bands:
        rs = [r for r in rows if lo <= proj(r) < hi]
        if not rs:
            continue
        night = defaultdict(list)
        for r in rs:
            night[r["date"]].append(act(r) - proj(r))
        sp, sa = sum(proj(r) for r in rs), sum(act(r) for r in rs)
        out.append("  %-8s n %3d  %s %5.1f  actual %5.1f  actual/%s %s  miss %4.1f  over on %d of %d nights" % (
            band_label(lo, hi), len(rs), label, sp / len(rs), sa / len(rs), label,
            "%.2f" % (sa / sp) if sp else "  - ", S.mean(abs(act(r) - proj(r)) for r in rs),
            sum(S.mean(v) > 0 for v in night.values()), len(night)))
    return out


def owncard(a):
    """The short ownership card: calibration against the baseline contest, the other contests against it, projection
    misses by ownership, last night's leverage list and construction."""
    rows, base = own_rows()
    rows = [r for r in rows if r["own_proj"] is not None]
    if not rows:
        print("Ownership card: no graded night with a baseline contest yet")
        return
    last = max(r["date"] for r in rows)
    print("Ownership card (baseline: %s)" % "; ".join("%s %s" % (d, c) for g, (_, c, d) in sorted(base.items(), key=lambda x: x[1][2])))
    u5 = [r for r in rows if r["own_proj"] < 5]
    per = defaultdict(list)
    for r in u5:
        per[r["date"]].append(r["own_act"] < 5)
    cross = sorted([r for r in u5 if r["own_act"] >= 10], key=lambda r: -r["own_act"])
    print("Projected under 5%% landed under 5%%: %.0f%% of %d (%s)%s" % (
        100 * S.mean(x for v in per.values() for x in v), len(u5), ", ".join("%s %.0f%%" % (d[5:], 100 * S.mean(v)) for d, v in sorted(per.items())),
        "; landed 10%+: " + ", ".join("%s %s %.1f" % (r["date"][5:], r["name"], r["own_act"]) for r in cross) if cross else ""))
    print("Ownership, the 3 bands settings are decided on (by our projection):")
    print("\n".join(band_line(rows, OWN_DECIDE, lambda r: r["own_proj"], lambda r: r["own_act"], "proj")))
    print("Ownership, 5 bands (read only):")
    print("\n".join(band_line(rows, OWN_SHOW, lambda r: r["own_proj"], lambda r: r["own_act"], "proj")))
    names = {r["contest_id"]: r["contest"] for r in read(EVAL)}
    kinds = defaultdict(list)                       # contest kind -> [(date, MAE vs baseline, {band: mean diff})]
    for (d, g), rs in groupby_night(rows).items():
        for cid in rs[0]["own_by"]:
            if cid == base[g][0]:
                continue
            diff = {b: [r["own_by"][cid] - r["own_act"] for r in rs if b[0] <= r["own_act"] < b[1]] for b in OWN_DECIDE}
            kinds[contest_kind(names.get(cid, cid))].append((d, S.mean(abs(r["own_by"][cid] - r["own_act"]) for r in rs), diff))
    print("Other contests against the baseline (their ownership minus its, by its band):")
    for k, v in sorted(kinds.items()):
        cells = []
        for b in OWN_DECIDE:
            ds = [S.mean(x[2][b]) for x in v if x[2][b]]
            cells.append("%s %+.1f (higher on %d of %d)" % (band_label(*b), S.mean(ds), sum(x > 0 for x in ds), len(ds)) if ds else "-")
        print("  %-16s %d contest-night%s, miss %.1f; %s" % (k, len(v), "" if len(v) == 1 else "s", S.mean(x[1] for x in v), "; ".join(cells)))
    print("Projection (actual minus ours, fp_dk as the audit) by baseline ownership:")
    print("\n".join(proj_band_lines(rows)))
    print("Leverage, %s:" % last)
    for line in leverage_lines([r for r in rows if r["date"] == last]):
        print("  " + line)
    fe = [r for r in read(FIELD_EVAL) if r["date"] == last and BASE_CONTEST in r["contest"] and "(Early)" not in r["contest"]]
    if fe:
        print("Construction, %s %s (%s games): side, 3+ from a team, <=10%% / >=40%% owned a lineup, summed ownership, salary, shared with another user, "
              "projection and projected ownership, with a player projected under %d minutes (1+ / 2+)" % (last, fe[0]["contest"], fe[0]["games"], PUNT_MIN))
        for r in fe:
            print("  %-20s %5s  %5s%%  %4s / %-4s  %4s%%  %s  %s  %s pts %s%%  %s%% / %s%%" % (
                r["side"], r["lineups"], r["team3"], r["low10"], r["high40"], r["own_sum"], r["sal_mean"], r["dup_field"] or r["dup_other"],
                r.get("proj_mean", ""), r.get("own_proj", ""), r.get("punt1", ""), r.get("punt2", "")))
    cp = read(COPIES_EVAL)
    if cp:
        agg = defaultdict(lambda: [0, 0.0, 0.0])
        for r in cp:
            a = agg[r["bucket"]]
            a[0] += int(r["entries"]); a[1] += num(r["fees"]); a[2] += num(r["won"])
        tot = sum(a[0] for a in agg.values())
        print("Copies (other users holding the same 8 players), %d contests, ties split: " % len({r["contest_id"] for r in cp}) + "; ".join(
            "%s %.0f%% of entries, ROI %+.0f%%" % (b, 100 * agg[b][0] / tot, 100 * (agg[b][2] - agg[b][1]) / agg[b][1]) for b, _, _ in COPY_BUCKETS if agg[b][1]))


def groupby_night(rows):
    out = defaultdict(list)
    for r in rows:
        out[(r["date"], str(r["draft_group"]))].append(r)
    return out


def contest_kind(name):
    for k in ("Pull Up Jumper", "And-One", "Quarter Jukebox", "Dime Time", "Big Five", "High Five"):
        if k in name:
            return k + (" (small)" if k == "And-One" and "$100 " in name else "")
    return name


def proj_band_lines(rows):
    """Our projection's miss by baseline ownership band (3 bands): n, bias (actual minus ours), average miss, nights over."""
    out = []
    for lo, hi in OWN_DECIDE:
        rs = [r for r in rows if lo <= r["own_act"] < hi]
        if not rs:
            continue
        night = defaultdict(list)
        for r in rs:
            night[r["date"]].append(r["act"] - r["ours"])
        out.append("  %-8s n %3d  bias %+5.1f  miss %4.1f  actual above ours on %d of %d nights" % (
            band_label(lo, hi), len(rs), S.mean(r["act"] - r["ours"] for r in rs),
            S.mean(abs(r["act"] - r["ours"]) for r in rs), sum(S.mean(v) > 0 for v in night.values()), len(night)))
    return out


def leverage_lines(rows):
    """Under LEV_LOW% owned beating our projection by LEV_BEAT+, and LEV_HIGH%+ missing it by LEV_MISS+: minutes and
    points per minute, and teammates projected 10+ minutes who sat (not tagged Out)."""
    sat = defaultdict(list)
    for r in rows:
        if (num(r.get("min_proj")) or 0) >= 10 and not num(r.get("min")):
            sat[r["team"]].append("%s%s" % (r["name"], " (%s)" % r["status"] if r.get("status") else ""))
    def line(r):
        mp, m = num(r.get("min_proj")) or 0, num(r.get("min")) or 0
        ppm = num(r.get("ppm_proj"))
        others = [x for x in sat[r["team"]] if not x.startswith(r["name"])]
        return "%s %s $%d, %.1f%% owned: %.1f on %.1f; minutes %.0f -> %.0f, points a minute %s -> %s%s" % (
            r["name"], r["team"], r["sal"], r["own_act"], r["act"], r["ours"], mp, m, "%.2f" % ppm if ppm else "-",
            "%.2f" % (r["act"] / m) if m else "-", "; sat: " + ", ".join(others) if others else "")
    low = sorted([r for r in rows if r["own_act"] < LEV_LOW and r["act"] - r["ours"] >= LEV_BEAT], key=lambda r: r["ours"] - r["act"])
    high = sorted([r for r in rows if r["own_act"] >= LEV_HIGH and r["ours"] - r["act"] >= LEV_MISS], key=lambda r: r["act"] - r["ours"])
    return (["Under %d%% owned, beat ours by %d+:%s" % (LEV_LOW, LEV_BEAT, "" if low else " none")] + ["  " + line(r) for r in low] +
            ["%d%%+ owned, missed ours by %d+:%s" % (LEV_HIGH, LEV_MISS, "" if high else " none")] + ["  " + line(r) for r in high])


SCAN_EVAL = os.path.join(DK, "scan_eval.csv")
SCAN_COLS = ["date", "draft_group", "contest_id", "contest", "stack", "kind", "n", "rank", "of", "read", "scan_g_t1", "scan_field", "tile_verdict",
             "real_entries", "real_top10", "real_top1", "proj", "actual"]


def scan_grade(a):
    """The slate scan graded, nightly (log only): each stack a saved build's scan ranked, against the real field of the
    night's baseline contest (the main $15, else the biggest graded): the share of real entries holding the stack that
    reached the real top 10% and top 1%; beside each team's tile verdict (tiles_eval.csv) for its team stacks. Prints
    whether the scan's top third of stacks reached the top 10% / top 1% more often than its bottom third, and the same
    by tile verdict. Player rows (the player scan, 2026-11-19): the same rates for real entries holding the player, and
    his real points against the scan's projection; printed by Read (core and leverage against fade and skip)."""
    base, verdict, out = baselines(), {}, []
    for r in read(os.path.join(DK, "tiles_eval.csv")):
        verdict[(str(r["draft_group"]), r["team"])] = r["verdict"]
    for f in sorted(glob.glob(os.path.join(BUILDS, "*.json"))):
        B = json.load(open(f))
        sc, g = B.get("scan"), str(B.get("draft_group"))
        if not sc or g not in base:
            continue
        cid, cname, date = base[g]
        path = os.path.join(STANDINGS, "contest-standings-%s.csv" % cid)
        slate = os.path.join(DK, "%s_%s.csv" % (date, g))
        if not os.path.exists(path) or not os.path.exists(slate):
            continue
        info = {r["name"]: r for r in read(slate)}
        entries, _ = standings(path)
        n = len(entries)
        t10, t1 = math.ceil(0.1 * n), max(1, math.ceil(0.01 * n))
        lines = [(e["rank"], [info.get(x) for x in lineup_names(e["lineup"])]) for e in entries]
        for row in sc.get("rows") or []:
            def holds(L):
                L = [x for x in L if x]
                if row["kind"] == "team":
                    return sum(x["team"] == row["team"] for x in L) >= row["n"]
                two = row["game"].split("@")
                ing = [x for x in L if x["game"] == row["game"]]
                return len(ing) >= row["n"] and all(any(x["team"] == t for x in ing) for t in two)
            hit = [rk for rk, L in lines if holds(L)]
            out.append({"date": date, "draft_group": g, "contest_id": cid, "contest": cname, "stack": row["key"], "kind": row["kind"], "n": row["n"],
                        "rank": row["rank"], "of": len(sc["rows"]), "read": row["read"], "scan_g_t1": round(row["g_t1"], 5), "scan_field": round(row["field"], 4),
                        "tile_verdict": verdict.get((g, row["team"]), "") if row["kind"] == "team" else "",
                        "real_entries": len(hit), "real_top10": round(sum(rk <= t10 for rk in hit) / len(hit), 4) if hit else "",
                        "real_top1": round(sum(rk <= t1 for rk in hit) / len(hit), 4) if hit else ""})
        byid = {r["dk_id"]: r for r in info.values()}
        for i, row in enumerate(sc.get("players") or []):
            pid = str(row["id"])
            hit = [rk for rk, L in lines if any(x and x["dk_id"] == pid for x in L)]
            act = num((byid.get(pid) or {}).get("actual_dk"))
            out.append({"date": date, "draft_group": g, "contest_id": cid, "contest": cname, "stack": row["key"], "kind": "player", "n": "",
                        "rank": i + 1, "of": len(sc["players"]), "read": row["read"], "scan_g_t1": round(row["g_t1"], 5),
                        "scan_field": round(row["fown"] / 100, 4) if row.get("fown") is not None else "", "tile_verdict": "",
                        "real_entries": len(hit), "real_top10": round(sum(rk <= t10 for rk in hit) / len(hit), 4) if hit else "",
                        "real_top1": round(sum(rk <= t1 for rk in hit) / len(hit), 4) if hit else "",
                        "proj": round(row["proj"], 2) if row.get("proj") is not None else "", "actual": act if act is not None else ""})
    if out:
        with open(SCAN_EVAL, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=SCAN_COLS)
            w.writeheader()
            w.writerows(out)
    for line in scan_lines():
        print(line)


def scan_lines():
    allr = [r for r in read(SCAN_EVAL) if r["real_entries"] and int(r["real_entries"]) >= 5]
    rs, pls = [r for r in allr if r["kind"] != "player"], [r for r in allr if r["kind"] == "player"]
    if not allr:
        return ["Slate scan: no graded scan yet (a build saved with a scan, and its standings)"]
    def rate(sub, k):
        e = sum(int(r["real_entries"]) for r in sub)
        return sum(num(r[k]) * int(r["real_entries"]) for r in sub) / e if e else None
    top = [r for r in rs if int(r["rank"]) <= int(r["of"]) / 3]
    bot = [r for r in rs if int(r["rank"]) > 2 * int(r["of"]) / 3]
    f = lambda x: "%.1f%%" % (100 * x) if x is not None else "-"
    out = [] if not rs else ["Slate scan, %d night%s: real entries holding the scan's top third of stacks reached the top 10%% %s / top 1%% %s; its bottom third %s / %s" % (
        len({r["date"] for r in rs}), "" if len({r["date"] for r in rs}) == 1 else "s", f(rate(top, "real_top10")), f(rate(top, "real_top1")), f(rate(bot, "real_top10")), f(rate(bot, "real_top1")))]
    tv = [r for r in rs if r["tile_verdict"] and r["kind"] == "team" and r["n"] == "3"]
    if tv:
        out.append("  team 3+ stacks by tile verdict: " + "; ".join("%s %s / %s (%d)" % (v, f(rate([r for r in tv if r["tile_verdict"] == v], "real_top10")),
                   f(rate([r for r in tv if r["tile_verdict"] == v], "real_top1")), len([r for r in tv if r["tile_verdict"] == v]))
                   for v in ("FOCUS", "CHALK", "LEVERAGE", "FADE") if any(r["tile_verdict"] == v for r in tv)))
    if pls:                     # the player scan: entries holding each Read's players, and the players' real less projected points
        def pts(sub):
            d = [num(r["actual"]) - num(r["proj"]) for r in sub if r.get("actual") not in ("", None) and r.get("proj") not in ("", None)]
            return "%+.1f" % (sum(d) / len(d)) if d else "-"
        out.append("  players by Read (top 10% / top 1% of real entries holding them; real less projected points; players): " + "; ".join(
            "%s %s / %s, %s (%d)" % (v, f(rate(sub, "real_top10")), f(rate(sub, "real_top1")), pts(sub), len(sub))
            for v, sub in [(v, [r for r in pls if r["read"] in v.split("+")]) for v in ("core", "leverage", "core+leverage", "even", "fade", "skip", "fade+skip")] if sub))
    return out


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
    cn = sub.add_parser("calnote")
    cn.add_argument("--mirror", help="the mirror checkout, for the match warning on its DraftKings slates")
    sub.add_parser("calweek")
    sub.add_parser("ideas")
    sub.add_parser("owncard")
    sub.add_parser("scan")
    sub.add_parser("risers")
    sub.add_parser("platoon")
    pr = sub.add_parser("pairs")
    pr.add_argument("--mirror", required=True)
    fl = sub.add_parser("fills")
    fl.add_argument("--mirror", required=True)
    fc = sub.add_parser("fieldcheck")
    fc.add_argument("--mirror", required=True)
    r = sub.add_parser("readout")
    r.add_argument("--sim-z", dest="sim_z", help="a dk_cbb_field.json, for the sim's draw shape (default: none)")
    a = ap.parse_args()
    os.makedirs(STANDINGS, exist_ok=True)
    return {"nightly": nightly, "gate": gate, "tiles": tiles, "weights": weights, "readout": readout, "cutcheck": cutcheck, "audit": audit, "calnote": calnote, "calweek": calweek, "ideas": ideas, "risers": risers, "fills": fills, "platoon": platoon, "pairs": pairs, "fieldcheck": fieldcheck, "owncard": owncard, "scan": scan_grade}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
