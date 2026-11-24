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
  lab       the shadow lab (2026-11-24), run by ideas: the experiments registered in analysis/cbb/dk/lab.json graded on
            each saved bank's kept lineups (entered or not): real finish percentile per graded contest of 100+ entries,
            treatment against control on the same slate and contest, slate by slate; lab.json's results (the DK page's
            Lab scoreboard) and lab_eval.csv rewritten whole. Slates before registration are a look-back only.
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
  fieldusers analysis/cbb/dk/field_users.csv (capture only, 2026-11-24): each graded small contest's (the qualifier profile:
            10-30 entries, or a qualifier / satellite under 100) users: entries, distinct lineups, mean summed and per-player
            projected ownership, mean players under 5% projected. Nothing reads it yet. Nightly runs it.
  qualcheck the count of real qualifier fields in field_users.csv against QUAL_REFIT_AT (10): the DK page's qualifier field
            is an assumed chalk style until then (fill_profiles_2026-11-24.md, the refit plan)
  flagjoint analysis/cbb/dk/flagship_joint.csv, nightly: each saved build's flagships filled together (joint top-1%
            coverage, the DK page's flagship profile) against each alone, in-sim on fresh nights; a row per new build
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
from collections import Counter, defaultdict
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
IDEA_COLS = ["date", "draft_group", "idea", "kind", "contest_id", "contest", "banked", "shared", "kept", "entered", "kept_share", "entered_share",
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
# None (not chosen yet: the blend), "ours" (the gate back to its own rule), "dk" (DraftKings' average), "blend", or
# "blend6k" (the 2026-11-23 lock: ours alone under $6,000, the blend at $6,000+; analysis/cbb/dk/lock_review_2026-11-23.md:
# points MAE 5.630 -> 5.421, better on 10 of 11 slates; banks top 10% better on 7 of 9 nights, worse on 2).
CALIBRATION_BLEND = {"w": 0.5, "from": "2026-11-17", "version": "cal-1"}
PROJ_CHOICE = "blend6k"
# The week's lock (2026-11-23, approved by the operator): while set, the nightly refits are computed and written beside
# the live value (gate.json questionable.factor_refit; sit_model_refit.json), but the live values stay as pinned here
# until the next Friday review changes this line. None: the refits apply nightly, as before.
# questionable: the projection's Questionable factor; questionable_field: the simulated field's (2026-11-23, the owner's
# call before the lock: a Questionable player keeps his full projection and his Q tag, the owner rules him in or out
# on the news; the field fades him at 1.0, i.e. not at all, from the owner's call at 17:56Z: at 0.333 the field
# never drafted a Q player, 0% owned; Mark out rebuilds the field without him. A measured field factor from real
# standings may replace it after review).
LOCK = {"version": "lock-2026-11-23", "questionable": 1.0, "questionable_field": 1.0}
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
    for step in (fieldusers, flagjoint):        # contest profiles (2026-11-24): the qualifier fields and the flagships' record
        try:
            step(a)
        except Exception as e:      # noqa: BLE001 (a side record; the grading above stands)
            print("  %s: skipped (%s)" % (step.__name__, e))


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
    if today >= cb["from"] and PROJ_CHOICE == "blend6k":    # the lock's choice: the blend at $6,000+, ours alone below
        for b in bands:
            b.update(open=b["lo"] >= 6000, w=cb["w"] if b["lo"] >= 6000 else 1.0)
        doc.update(override="the owner's choice at the 2026-11-23 lock: the %d/%d blend at $6,000+, ours alone below" % (
            round(100 * cb["w"]), round(100 * (1 - cb["w"]))), version=LOCK["version"] if LOCK else "blend6k")
    if LOCK and LOCK.get("questionable") is not None:        # pinned for the week; the refit kept beside it
        quest.update(factor_refit=quest["factor"], factor=LOCK["questionable"], pinned=LOCK["version"])
        if LOCK.get("questionable_field") is not None:     # the field's own fade (dk_cbb_field.q_factor reads it first)
            quest["field_factor"] = LOCK["questionable_field"]
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
        if r.get("stackq"):          # the DK page's stack quick buttons (2026-11-24): one kind per shape
            parts.append("quick stack %s" % r["stackq"].get("shape"))
            continue
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
    if t.get("scan_set"):
        parts.append("scan floors")
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
        # every tag a lineup was drawn under (2026-11-20, shared credit): a lineup two ideas drew counts for both
        idea = [set(t) if isinstance(t, list) else {t} for t in b["tags"]]
        kept = set(b["final"]) if b.get("final") else set(range(len(b["pool"])))
        settings = b.get("tag_settings") or {}
        for cid, L in sorted(lines.items()):
            t10, cash = num(L["field_top10"]), num(L["field_cash"])
            ent = (b.get("portfolios") or {}).get(cid) or []
            for name in sorted(set().union(*idea)):
                mem = [k for k in range(len(b["pool"])) if name in idea[k]]
                ke, en = [k for k in mem if k in kept], [k for k in ent if name in idea[k]]
                rate = lambda ks, line: sum(score[k] >= line for k in ks) / len(ks) if ks and line is not None else ""
                row = {"date": b["day"], "draft_group": g, "idea": name, "kind": idea_kind(settings.get(name) or {}), "contest_id": cid,
                       "contest": L["contest"], "banked": len(mem), "shared": sum(1 for k in mem if len(idea[k]) > 1), "kept": len(ke), "entered": len(en),
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
        print("  ideas %s (%s): %d ideas, %d contests" % (g, b["day"], len(set().union(*idea)), len(lines)))
    if out:
        with open(IDEA_EVAL, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=IDEA_COLS)
            w.writeheader()
            w.writerows(out)
    try:            # the shadow lab (2026-11-24): its experiments on the same banks, paired against their controls
        lab(a)
    except Exception as e:      # noqa: BLE001 (a side record; the ideas grade above stands)
        print("  lab: skipped (%s)" % e)


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
    his real points against the scan's projection; printed by Read (core and leverage against fade and skip; lean core and
    lean leverage from 2026-11-20, derived for scans saved before: an even with a positive gain, by the scan's median)."""
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
        pmed = sc.get("pownMedian")
        def pread(row):                 # lean reads (2026-11-20) for scans saved before them: an even with a positive gain
            if row["read"] == "even" and row["g_t1"] > 0 and pmed is not None and row.get("fown") is not None:
                return "lean core" if row["fown"] >= pmed else "lean leverage"
            return row["read"]
        for i, row in enumerate(sc.get("players") or []):
            pid = str(row["id"])
            hit = [rk for rk, L in lines if any(x and x["dk_id"] == pid for x in L)]
            act = num((byid.get(pid) or {}).get("actual_dk"))
            out.append({"date": date, "draft_group": g, "contest_id": cid, "contest": cname, "stack": row["key"], "kind": "player", "n": "",
                        "rank": i + 1, "of": len(sc["players"]), "read": pread(row), "scan_g_t1": round(row["g_t1"], 5),
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
            for v, sub in [(v, [r for r in pls if r["read"] in v.split("+")]) for v in ("core", "leverage", "core+leverage", "lean core", "lean leverage", "lean core+lean leverage",
                                                                                     "even", "fade", "skip", "fade+skip")] if sub))
    return out


# --- A1, the morning projection audit (2026-11-20, the operator's three-lens plan; tracking, nothing moves a number) ---
# On every graded slate (analysis/cbb/dk/<date>_<group>.csv): minutes (rank agreement, top-5 match, the miss by
# rotation slot, the 15+ minute players who didn't play), shape (our share of each team's projected points against his
# share over his last 5, the top-2 and top-5 share), Vegas (each team's summed projection against its implied total),
# salary (projection on salary, the big gaps and their reasons) and ownership agreement (our points per $1K against
# the real ownership in the slate's baseline contest). Blowouts (|final margin| 20+) are out of the minutes headline.
PROJ_AUDIT = os.path.join(DK, "proj_audit.csv")
PROJ_AUDIT_COLS = ["date", "draft_group", "teams", "blowouts", "min_rank", "min_top5", "slot_miss", "news_miss", "shape_top2_ours", "shape_top2_recent",
                   "shape_top5_ours", "shape_top5_recent", "vegas_slope", "vegas_slope_actual", "vegas_r", "sal_gaps", "sal_unexplained", "own_rank", "own_n"]
BLOWOUT = 20


def spearman(x, y):
    """Rank correlation (average ranks for ties)."""
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    if len(x) < 3:
        return None
    a, b = rk(x), rk(y)
    ma, mb = S.mean(a), S.mean(b)
    num_ = sum((p - ma) * (q - mb) for p, q in zip(a, b)); den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num_ / den if den else None


def shape_rows(team_rows, proj, recent):
    """A team's top-2 and top-5 shares of its projected points: ours (by our projection) and recent (his last-5 average)."""
    rs = [r for r in team_rows if (proj(r) or 0) > 0 and recent(r) is not None]
    if len(rs) < 5:
        return None
    po, pr = sum(proj(r) for r in rs), sum(recent(r) for r in rs)
    if not po or not pr:
        return None
    o, c = sorted((proj(r) / po for r in rs), reverse=True), sorted((recent(r) / pr for r in rs), reverse=True)
    return sum(o[:2]), sum(c[:2]), sum(o[:5]), sum(c[:5])


def projaudit(a):
    """A1 (see above): proj_audit.csv rebuilt whole, a row per graded slate, and the lines printed."""
    own = defaultdict(dict)
    base = baselines()
    for r in read(os.path.join(DK, "own_eval.csv")):
        g = str(r["draft_group"])
        if g in base and r["contest_id"] == base[g][0]:
            own[g][r["dk_id"]] = num(r["own_actual"]) or 0.0
    out, lines, PX, PY, PA = [], [], [], [], []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = read(f)
        if not rows or not any(r.get("actual_dk") not in ("", None) for r in rows):
            continue
        date, g = rows[0]["date"], str(rows[0]["draft_group"])
        live = [r for r in rows if r.get("status") != "Out"]
        teams = defaultdict(list)
        for r in rows:
            teams[r["team"]].append(r)
        # the final margin from the box: each team's points summed
        score = {t: sum(num(r.get("pts")) or 0 for r in rs) for t, rs in teams.items()}
        opp = {}
        for r in rows:
            two = (r.get("game") or "").split("@")
            if len(two) == 2:
                opp[r["team"]] = two[1] if r["team"] == two[0] else two[0]
        blow = {t for t in teams if t in opp and opp[t] in score and abs(score[t] - score[opp[t]]) >= BLOWOUT}
        # 1. minutes
        ranks, top5, slot, news = [], [], defaultdict(list), []
        for t, rs in teams.items():
            act = {r["dk_id"]: num(r.get("min")) or 0 for r in rs}
            lv = [r for r in rs if r.get("status") != "Out"]
            for r in lv:
                if (num(r.get("min_proj")) or 0) >= 15 and not act[r["dk_id"]]:
                    news.append("%s %s (%.0f projected)" % (r["name"], t, num(r["min_proj"])))
            if t in blow:
                continue
            pl = [r for r in lv if act[r["dk_id"]] > 0]
            rho = spearman([num(r.get("min_proj")) or 0 for r in pl], [act[r["dk_id"]] for r in pl])
            if rho is not None:
                ranks.append(rho)
            byp = sorted(lv, key=lambda r: -(num(r.get("min_proj")) or 0))
            bya = sorted(rs, key=lambda r: -act[r["dk_id"]])
            top5.append(len({r["dk_id"] for r in byp[:5]} & {r["dk_id"] for r in bya[:5]}))
            for i, r in enumerate(byp[:8]):
                slot[i + 1].append(act[r["dk_id"]] - (num(r.get("min_proj")) or 0))
        # 2. shape (no results needed): ours vs his last-5 average, tonight's outs left out
        sh = [x for x in (shape_rows([r for r in rs if r.get("status") != "Out"], lambda r: num(r.get("fp_dk")), lambda r: num(r.get("dk_last5"))) for rs in teams.values()) if x]
        # 3. Vegas: each team's summed projection against its implied total
        vx, vy, va, vt = [], [], [], []
        for t, rs in teams.items():
            r0 = next((r for r in rs if num(r.get("ou")) and num(r.get("spread")) is not None), None)
            if r0:
                vx.append(num(r0["ou"]) / 2 - num(r0["spread"]) / 2); vy.append(sum(num(r.get("fp_dk")) or 0 for r in rs if r.get("status") != "Out")); vt.append(t)
                va.append(sum(num(r.get("actual_dk")) or 0 for r in rs))
        PX += vx; PY += vy; PA += va
        slope = r_ = slope_a = None
        vout = []
        if len(vx) >= 3:
            mx, my = S.mean(vx), S.mean(vy)
            sxx = sum((x - mx) ** 2 for x in vx); sxy = sum((x - mx) * (y - my) for x, y in zip(vx, vy)); syy = sum((y - my) ** 2 for y in vy)
            slope = sxy / sxx if sxx else None
            r_ = sxy / math.sqrt(sxx * syy) if sxx and syy else None
            ma = S.mean(va)      # the reference: the teams' real DK points on the same implied totals
            slope_a = sum((x - mx) * (y - ma) for x, y in zip(vx, va)) / sxx if sxx else None
            if slope is not None:
                vout = sorted(((y - (my + slope * (x - mx)), t, x, y) for x, y, t in zip(vx, vy, vt)), key=lambda z: -abs(z[0]))[:3]
        # 4. salary: projection on salary; the big gaps (2 sd) and their reasons
        sal = [r for r in live if (num(r.get("fp_dk")) or 0) > 0]
        gaps, unexplained = [], 0
        if len(sal) >= 10:
            xs, ys = [num(r["salary"]) for r in sal], [num(r["fp_dk"]) for r in sal]
            mx, my = S.mean(xs), S.mean(ys)
            b_ = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a_ = my - b_ * mx
            res = [y - (a_ + b_ * x) for x, y in zip(xs, ys)]; sd = S.pstdev(res)
            outT = {t for t, rs in teams.items() if any(r.get("status") == "Out" and (num(r.get("min_avg")) or 0) >= 20 for r in rs)}
            for r, e in zip(sal, res):
                if abs(e) >= 2 * sd:
                    why = []
                    if r.get("status"):
                        why.append("Q status")
                    if r["team"] in outT:
                        why.append("teammate out")
                    if num(r.get("min_avg")) is not None and abs((num(r.get("min_proj")) or 0) - num(r["min_avg"])) >= 5:
                        why.append("minutes change")
                    if r.get("missed"):
                        why.append("back from injury / missed")
                    if r.get("src") != "box" or num(r.get("dk_last5")) is None:
                        why.append("newcomer / few games")
                    unexplained += not why
                    gaps.append((e, r, why))
        # 5. ownership agreement: our points per $1K against the real ownership
        og = own.get(g, {})
        ox = [r for r in live if r["dk_id"] in og or og]
        orank = spearman([(num(r.get("fp_dk")) or 0) / max(1, num(r["salary"])) for r in ox], [og.get(r["dk_id"], 0.0) for r in ox]) if og else None
        row = {"date": date, "draft_group": g, "teams": len(teams), "blowouts": len(blow),
               "min_rank": round(S.mean(ranks), 3) if ranks else "", "min_top5": round(S.mean(top5), 2) if top5 else "",
               "slot_miss": " ".join("%d:%+.1f" % (k, S.mean(v)) for k, v in sorted(slot.items())), "news_miss": len(news),
               "shape_top2_ours": round(S.mean(x[0] for x in sh), 3) if sh else "", "shape_top2_recent": round(S.mean(x[1] for x in sh), 3) if sh else "",
               "shape_top5_ours": round(S.mean(x[2] for x in sh), 3) if sh else "", "shape_top5_recent": round(S.mean(x[3] for x in sh), 3) if sh else "",
               "vegas_slope": round(slope, 2) if slope is not None else "", "vegas_slope_actual": round(slope_a, 2) if slope_a is not None else "", "vegas_r": round(r_, 3) if r_ is not None else "",
               "sal_gaps": len(gaps), "sal_unexplained": unexplained, "own_rank": round(orank, 3) if orank is not None else "", "own_n": len(og)}
        out.append(row)
        lines.append("%s %s (%d teams, %d blowouts out): minutes rank %s, top-5 match %s of 5, by slot %s; shape top-2 ours %s vs recent %s, top-5 %s vs %s; Vegas slope %s (real DK points %s; r %s); "
                     "salary gaps %d (%d unexplained); points per $1K vs real ownership rank %s" % (
                         date, g, row["teams"], row["blowouts"], row["min_rank"], row["min_top5"], row["slot_miss"], row["shape_top2_ours"], row["shape_top2_recent"],
                         row["shape_top5_ours"], row["shape_top5_recent"], row["vegas_slope"], row["vegas_slope_actual"], row["vegas_r"], row["sal_gaps"], unexplained, row["own_rank"]))
        if vout:
            lines.append("    Vegas outliers (our team total against the line's): " + "; ".join("%s %+.0f (implied %.1f, ours %.0f)" % (t, e, x, y) for e, t, x, y in vout))
        if news:
            lines.append("    didn't play (projected 15+ minutes): " + "; ".join(news))
        if gaps:
            lines.append("    biggest salary gaps: " + "; ".join("%s %+.1f (%s)" % (r["name"], e, ", ".join(w) or "unexplained") for e, r, w in sorted(gaps, key=lambda x: -abs(x[0]))[:6]))
        if og:
            pairs_ = sorted(ox, key=lambda r: -abs(((num(r.get("fp_dk")) or 0) / max(1, num(r["salary"])) * 1000 - 4.5) * 10 - og.get(r["dk_id"], 0.0)))
            rv = sorted(ox, key=lambda r: -(num(r.get("fp_dk")) or 0) / max(1, num(r["salary"])))
            vr = {r["dk_id"]: i + 1 for i, r in enumerate(rv)}
            orr = {r["dk_id"]: i + 1 for i, r in enumerate(sorted(ox, key=lambda r: -og.get(r["dk_id"], 0.0)))}
            dis = sorted(ox, key=lambda r: -abs(vr[r["dk_id"]] - orr[r["dk_id"]]) if (vr[r["dk_id"]] <= 15 or orr[r["dk_id"]] <= 15) else 0)[:5]
            lines.append("    biggest value / ownership disagreements (value rank vs ownership rank): " + "; ".join(
                "%s #%d vs #%d (%.0f%%)" % (r["name"], vr[r["dk_id"]], orr[r["dk_id"]], og.get(r["dk_id"], 0.0)) for r in dis))
    if getattr(a, "mirror", None):           # pre-lock: the shape lens on the mirror's open slates
        mf = os.path.join(a.mirror, "dk_cbb_morning.json")
        for sl in (json.load(open(mf)).get("slates") or []) if os.path.exists(mf) else []:
            if sl.get("locked"):
                continue
            tm = defaultdict(list)
            for r in (sl.get("players") or {}).values():
                if r.get("status") != "Out":
                    tm[r["team"]].append(r)
            l5 = lambda r: (S.mean(r["dk_last5"]) if isinstance(r.get("dk_last5"), list) and r["dk_last5"] else num(r.get("dk_last5")))
            l5 = (lambda f: (lambda r: f(r) if not isinstance(r.get("dk_last5"), list) else (S.mean(x[2] if isinstance(x, list) else x for x in r["dk_last5"]) if r["dk_last5"] else None)))(l5)
            per = {t: shape_rows(rs, lambda r: num(r.get("fp_dk")), l5) for t, rs in tm.items()}
            per = {t: x for t, x in per.items() if x}
            if per:
                lines.append("Pre-lock shape %s (%d teams): top-2 ours %.3f vs recent %.3f; steepest against recent: %s" % (
                    sl["draft_group_id"], len(per), S.mean(x[0] for x in per.values()), S.mean(x[1] for x in per.values()),
                    ", ".join("%s %+.0f pts" % (t, 100 * (x[0] - x[1])) for t, x in sorted(per.items(), key=lambda kv: -abs(kv[1][0] - kv[1][1]))[:4])))
    if out:
        with open(PROJ_AUDIT, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=PROJ_AUDIT_COLS)
            w.writeheader()
            w.writerows(out)
    for l in lines:
        print(l)
    if out:
        m = lambda k: [num(r[k]) for r in out if r[k] not in ("", None)]
        mx, sxx = S.mean(PX), sum((x - S.mean(PX)) ** 2 for x in PX)
        pooled = sum((x - mx) * (y - S.mean(PY)) for x, y in zip(PX, PY)) / sxx
        pooled_a = sum((x - mx) * (y - S.mean(PA)) for x, y in zip(PX, PA)) / sxx
        print("All %d graded slates: minutes rank %.3f, top-5 match %.2f; shape top-2 ours %.3f vs recent %.3f (%s), top-5 %.3f vs %.3f; Vegas slope pooled over %d teams %.2f (real DK points %.2f); salary gaps %d, %d unexplained (%.0f%%); value vs ownership rank %.3f" % (
            len(out), S.mean(m("min_rank")), S.mean(m("min_top5")), S.mean(m("shape_top2_ours")), S.mean(m("shape_top2_recent")),
            "ours steeper" if S.mean(m("shape_top2_ours")) > S.mean(m("shape_top2_recent")) else "ours flatter", S.mean(m("shape_top5_ours")), S.mean(m("shape_top5_recent")),
            len(PX), pooled, pooled_a, sum(m("sal_gaps")), sum(m("sal_unexplained")), 100 * sum(m("sal_unexplained")) / max(1, sum(m("sal_gaps"))), S.mean(m("own_rank")) if m("own_rank") else float("nan")))


OWN_AUDIT = os.path.join(DK, "own_audit.csv")
OWN_AUDIT_COLS = ["date", "draft_group", "contest", "night_tag", "players", "teams", "team_rank", "team_miss", "team_top3", "top1_match", "order_rank",
                  "gap_ours", "gap_real", "top5_hit", "band_u5", "band_5_20", "band_20", "dup_real", "dup_sim"]


def own_team_shape(rs):
    """{team: (summed projected, summed real, [its players by our projection, top 4])} from own_rows rows."""
    t = defaultdict(list)
    for r in rs:
        t[r["team"]].append(r)
    return {k: (sum(r["own_proj"] for r in v), sum(r["own_act"] for r in v), sorted(v, key=lambda r: -r["own_proj"])[:4]) for k, v in t.items()}


def ownaudit(a):
    """B1, the morning ownership audit by shape (2026-11-20, BUILD; tracking): each graded slate's projected ownership
    against the real ownership of its baseline contest (own_rows: a player nobody drafted is 0%), by shape not exact %.
    Team: rank correlation of summed projected vs real, the mean miss of a team's sum, and real / projected for our 3
    most-owned teams. Within a team (teams with a player projected 5%+): how often our most-owned is the real most-owned,
    the rank agreement over our top 4, and the gap between our #1 and #2 (ours vs real, same two players). Slate: how
    many of our top 5 are the real top 5, and real / projected in the 3 decision bands. Duplication: real vs simulated
    share of entries holding a lineup another user entered (field_eval.csv, the slate's contests averaged), with the
    night tag. own_audit.csv rebuilt whole; the biggest team misses go in A3's log (misses)."""
    rows, base = own_rows()
    rows = [r for r in rows if r["own_proj"] is not None]
    fe = read(FIELD_EVAL)
    out = []
    for (d, g), rs in sorted(groupby_night(rows).items()):
        ts = own_team_shape(rs)
        tk = [k for k in ts if ts[k][0] > 0 or ts[k][1] > 0]
        trank = spearman([ts[k][0] for k in tk], [ts[k][1] for k in tk])
        top3 = sorted(tk, key=lambda k: -ts[k][0])[:3]
        m1, ordr, go, gr = [], [], [], []
        for k in tk:
            pl = ts[k][2]
            if len(pl) < 2 or pl[0]["own_proj"] < 5:
                continue
            allp = [r for r in rs if r["team"] == k]
            m1.append(max(allp, key=lambda r: r["own_act"])["dk_id"] == pl[0]["dk_id"])
            rho = spearman([r["own_proj"] for r in pl], [r["own_act"] for r in pl])
            if rho is not None:
                ordr.append(rho)
            go.append(pl[0]["own_proj"] - pl[1]["own_proj"]); gr.append(pl[0]["own_act"] - pl[1]["own_act"])
        p5 = {r["dk_id"] for r in sorted(rs, key=lambda r: -r["own_proj"])[:5]}
        a5 = {r["dk_id"] for r in sorted(rs, key=lambda r: -r["own_act"])[:5]}
        band = []
        for lo, hi in OWN_DECIDE:
            b = [r for r in rs if lo <= r["own_proj"] < hi]
            sp = sum(r["own_proj"] for r in b)
            band.append(round(sum(r["own_act"] for r in b) / sp, 2) if sp else "")
        sub = [r for r in fe if r["draft_group"] == g]
        dr = [num(r["dup_other"]) for r in sub if r["side"] == "real" and num(r["dup_other"]) is not None]
        ds = [num(r["dup_other"]) for r in sub if r["side"] == "sim" and num(r["dup_other"]) is not None]
        out.append({"date": d, "draft_group": g, "contest": base[g][1], "night_tag": next((r["night_tag"] for r in sub if r.get("night_tag")), ""),
                    "players": len(rs), "teams": len(tk), "team_rank": round(trank, 3) if trank is not None else "",
                    "team_miss": round(S.mean(abs(ts[k][1] - ts[k][0]) for k in tk), 1) if tk else "",
                    "team_top3": " ".join("%s:%.2f" % (k, ts[k][1] / ts[k][0]) for k in top3 if ts[k][0]),
                    "top1_match": "%d/%d" % (sum(m1), len(m1)), "order_rank": round(S.mean(ordr), 3) if ordr else "",
                    "gap_ours": round(S.mean(go), 1) if go else "", "gap_real": round(S.mean(gr), 1) if gr else "",
                    "top5_hit": len(p5 & a5), "band_u5": band[0], "band_5_20": band[1], "band_20": band[2],
                    "dup_real": round(S.mean(dr), 1) if dr else "", "dup_sim": round(S.mean(ds), 1) if ds else ""})
    if not out:
        print("Ownership audit: no graded night with a baseline contest yet")
        return
    with open(OWN_AUDIT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=OWN_AUDIT_COLS)
        w.writeheader()
        w.writerows(out)
    print("Ownership audit by shape (projected vs the baseline contest's real; a player nobody drafted counts 0%):")
    for r in out:
        print("  %s %s %s (%s): teams %s, rank %s, a team's sum off by %s pts, our top 3 teams real/proj %s; within a team: our most-owned the real one %s, "
              "order (top 4) %s, #1-#2 gap ours %s vs real %s; top-5 owned hit %s of 5; bands real/proj under 5 %s, 5-20 %s, 20+ %s; duplication real %s%% vs sim %s%%" % (
                  r["date"], r["draft_group"], r["contest"], r["night_tag"] or "untagged", r["teams"], r["team_rank"], r["team_miss"], r["team_top3"], r["top1_match"],
                  r["order_rank"], r["gap_ours"], r["gap_real"], r["top5_hit"], r["band_u5"], r["band_5_20"], r["band_20"], r["dup_real"], r["dup_sim"]))
    m = lambda k: [num(r[k]) for r in out if r[k] not in ("", None)]
    t1 = [tuple(map(int, r["top1_match"].split("/"))) for r in out]
    print("All %d slates: team rank %.3f, a team's sum off by %.1f pts; most-owned on a team right %d of %d; order %.3f; #1-#2 gap ours %.1f vs real %.1f; "
          "top-5 hit %.1f of 5; bands real/proj %s" % (len(out), S.mean(m("team_rank")), S.mean(m("team_miss")), sum(x[0] for x in t1), sum(x[1] for x in t1),
                                                       S.mean(m("order_rank")), S.mean(m("gap_ours")), S.mean(m("gap_real")), S.mean(m("top5_hit")),
                                                       ", ".join("%s %.2f" % (band_label(*b), S.mean(m(k))) for b, k in zip(OWN_DECIDE, ["band_u5", "band_5_20", "band_20"]) if m(k))))
    for l in own_pos_lines():
        if l.startswith("Duplication"):
            print(l)


OWN_WATCH = os.path.join(DK, "own_watch.json")
BLUE_BLOODS = {"DUKE", "UK", "KU", "UNC", "UCLA", "IU", "UCONN", "MSU", "ARIZ", "NOVA"}    # DK's team codes
# a pattern's status from its nights (B3): confirmed needs WATCH_CONFIRM player-nights on WATCH_NIGHTS nights, the
# same direction on WATCH_SAME of them and a ratio at least WATCH_SIZE away from 1; dead once measured on WATCH_NIGHTS
# nights with the direction under WATCH_DEAD or the ratio within 10%
WATCH_CONFIRM, WATCH_NIGHTS, WATCH_SAME, WATCH_SIZE, WATCH_DEAD = 30, 5, 0.75, 0.25, 0.6


def ownwatch(a):
    """B3, the ownership watchlist (2026-11-20, BUILD; hypotheses, not the improvement loop): for every graded
    player-night, log((real + 1) / (projected + 1)) in the baseline contest (own_rows), and per pattern the nightly
    gap between the players it flags and the rest of that night's players (so a night that ran hot everywhere counts
    zero). Patterns, from what's on file at lock: top-2 projected in the highest-total game; blue bloods (BLUE_BLOODS);
    coming off a big game (last game's DK points 10+ over his season average, from the mirror's file before lock);
    top-2 projected on the biggest favourite; the 5 highest salaries; round-number salaries ($X,000). Not measurable
    yet (no source on file): ranked teams, the national TV game, NBA prospects, salary drops, starter vs bench news
    beneficiary. Status: watching -> emerging -> confirmed / dead (WATCH_*). own_watch.json for the page, which shows
    confirmed patterns as a note and never moves a number; acting on one is a Friday-review decision."""
    rows, base = own_rows()
    rows = [r for r in rows if r["own_proj"] is not None]
    mirror = Mirror(a.mirror)
    bpath = os.path.join(DK, "watch_backfill.json")       # facts for slates graded before the records carried them
    backfill = json.load(open(bpath)) if os.path.exists(bpath) else {}
    nights = []
    for (d, g), rs in sorted(groupby_night(rows).items()):
        last, rec = {}, {}
        day = iso(d + "T00:00:00Z")
        vs = mirror.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))
        start = None
        for t, sha in reversed(vs):
            sl = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
            if sl and start is None:
                start = iso(sl["start"])
            if sl and start and t < start:
                last = {k: (p.get("last5") or [None])[-1] for k, p in (sl.get("players") or {}).items()}
                rec = sl.get("players") or {}
                break
        bf = backfill.get(g, {})
        fact = lambda k, f: (rec.get(k) or {}).get(f) if f in (rec.get(k) or {}) else (bf.get(k) or {}).get(f)
        ou = {}
        for r in rs:
            if num(r.get("ou")):
                ou[r["game"]] = num(r["ou"])
        hg = max(ou, key=ou.get) if ou else None
        fav = min((r for r in rs if num(r.get("spread")) is not None), key=lambda r: num(r["spread"]), default=None)
        top2 = lambda sub: {r["dk_id"] for r in sorted(sub, key=lambda r: -r["ours"])[:2]}
        flags = {
            "top-2 projected in the highest-total game": top2([r for r in rs if r["game"] == hg]),
            "blue bloods": {r["dk_id"] for r in rs if r["team"] in BLUE_BLOODS},
            "coming off a big game": {r["dk_id"] for r in rs if isinstance(last.get(r["dk_id"]), list) and r.get("dkavg") is not None and last[r["dk_id"]][2] >= r["dkavg"] + 10},
            "top-2 projected on the biggest favourite": top2([r for r in rs if fav and r["team"] == fav["team"]]),
            "the 5 highest salaries": {r["dk_id"] for r in sorted(rs, key=lambda r: -r["sal"])[:5]},
            "round-number salaries": {r["dk_id"] for r in rs if r["sal"] % 1000 == 0},
            "ranked teams (AP, else coaches)": {r["dk_id"] for r in rs if fact(r["dk_id"], "team_rank")},
            "the national TV games": {r["dk_id"] for r in rs if fact(r["dk_id"], "tv")},
            "salary down $300+ from his last slate": {r["dk_id"] for r in rs if fact(r["dk_id"], "sal_prev") and r["sal"] <= fact(r["dk_id"], "sal_prev") - 300},
        }
        seen = {k: any(fact(r["dk_id"], f) for r in rs) for k, f in (("ranked teams (AP, else coaches)", "team_rank"), ("the national TV games", "tv"),
                                                                     ("salary down $300+ from his last slate", "sal_prev"))}
        lr = {r["dk_id"]: math.log((r["own_act"] + 1) / (r["own_proj"] + 1)) for r in rs}
        nights.append({"date": d, "draft_group": g, "recency_on_file": bool(last), "on_file": seen, "flags": flags, "lr": lr,
                       "names": {r["dk_id"]: r["name"] for r in rs}, "proj": {r["dk_id"]: r["own_proj"] for r in rs}, "act": {r["dk_id"]: r["own_act"] for r in rs}})
    out = {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "rule": "confirmed: %d+ player-nights on %d+ nights, the same direction on %d%%+ of nights, real/projected %d%%+ off 1; dead: %d+ nights and the direction under %d%% or within 10%%" % (
        WATCH_CONFIRM, WATCH_NIGHTS, 100 * WATCH_SAME, 100 * WATCH_SIZE, WATCH_NIGHTS, 100 * WATCH_DEAD), "patterns": []}
    print("Ownership watchlist (real vs projected in the baseline contest; each night, the flagged players against the rest):")
    for name in nights[0]["flags"] if nights else []:
        per, n, ex = [], 0, []
        for nt in nights:
            if name == "coming off a big game" and not nt["recency_on_file"] or nt["on_file"].get(name) is False:
                continue
            f = nt["flags"][name]; rest = [v for k, v in nt["lr"].items() if k not in f]
            fl = [nt["lr"][k] for k in f if k in nt["lr"]]
            if fl and rest:
                per.append((nt["date"], S.mean(fl) - S.mean(rest))); n += len(fl)
                ex += ["%s %s %.0f/%.0f%%" % (nt["date"][5:], nt["names"][k], nt["act"][k], nt["proj"][k]) for k in f if k in nt["lr"]][:2]
        if not per:
            st, ratio, same = "watching", None, 0
        else:
            m = S.mean(x for _, x in per); ratio = math.exp(m); same = sum((x > 0) == (m > 0) for _, x in per) / len(per)
            if n >= WATCH_CONFIRM and len(per) >= WATCH_NIGHTS and same >= WATCH_SAME and abs(ratio - 1) >= WATCH_SIZE:
                st = "confirmed"
            elif len(per) >= WATCH_NIGHTS and (same < WATCH_DEAD or abs(ratio - 1) < 0.10):
                st = "dead"
            elif len(per) >= 3 and same >= 2 / 3 and abs(ratio - 1) >= 0.15:
                st = "emerging"
            else:
                st = "watching"
        out["patterns"].append({"pattern": name, "status": st, "player_nights": n, "nights": len(per), "ratio": round(ratio, 2) if ratio else None,
                                "same_direction": "%d of %d" % (round(same * len(per)), len(per)), "examples": ex[:6]})
        print("  %-42s %-9s %3d player-nights on %d nights; real/projected vs the rest x%s; same direction %d of %d nights%s" % (
            name, st, n, len(per), "%.2f" % ratio if ratio else "-", round(same * len(per)), len(per), ("; e.g. " + ", ".join(ex[:3])) if ex else ""))
    print("  not measured: NBA prospects (skipped for now), starter vs bench news beneficiary")
    with open(OWN_WATCH, "w") as fh:
        json.dump(out, fh, indent=1)


MISSES = os.path.join(DK, "misses.csv")
MISSES_COLS = ["date", "draft_group", "lens", "subject", "team", "miss", "detail", "tags", "driver"]


def gap_driver(r, gap):
    """What drives a salary gap (the coordinator, 2026-11-20): our projection against his last 5 (fp_dk - dk_last5)
    split into minutes ((min_proj - min_last5) x his recent points a minute), EvanMiya (fp_dk - fp_base_dk) and rate
    (the rest: our points a minute against his recent beyond EvanMiya). When our number sits within half the gap of
    his last 5, the price is what's off the line: "price (DK avg)". No last 5: "no recent games"."""
    fp, l5, m5, mp = num(r.get("fp_dk")), num(r.get("dk_last5")), num(r.get("min_last5")), num(r.get("min_proj"))
    if fp is None or l5 is None or not m5:
        return "no recent games", {}
    d = fp - l5
    parts = {"minutes": ((mp or 0) - m5) * l5 / m5, "EvanMiya": fp - (num(r.get("fp_base_dk")) if num(r.get("fp_base_dk")) is not None else fp)}
    parts["rate"] = d - parts["minutes"] - parts["EvanMiya"]
    if abs(d) < 0.5 * abs(gap):
        return "price (DK avg)", parts
    return max(parts, key=lambda k: abs(parts[k]) if (parts[k] > 0) == (d > 0) else -1), parts
MISS_TAGS = ["late news / scratch", "teammate out", "minutes role change", "newcomer / few games", "blowout", "stale DK avg",
             "salary-value spot", "chalk concentration", "Q status", "unexplained"]


def misses(a):
    """A3, the biggest-misses log (2026-11-20, BUILD): each graded slate's largest misses on each lens, every one with
    its automatic reason tags (MISS_TAGS; none fits: "unexplained"). misses.csv is rebuilt whole from the graded slate
    files and own_eval.csv. Lenses: minutes (real minus projected, top 5), shape (a team's top-2 share of its points,
    ours minus real, top 3 teams), Vegas (a team's real DK points minus our summed projection, top 3, the line's
    implied total beside), salary (every 2 sd gap off the slate's salary line, as A1; the miss is his real minus
    projected points) and ownership (real minus projected, against the slate's baseline contest, top 5).
    --friday: counts by tag for the week of the latest night (Monday on) and for all nights."""
    orows, base = own_rows()
    own = defaultdict(dict)                 # the baseline contest's ownership; a player nobody drafted is 0%
    for r in orows:
        if r["own_proj"] is not None:
            own[str(r["draft_group"])][r["dk_id"]] = (r["own_proj"], r["own_act"])
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = read(f)
        if not rows or not any(r.get("actual_dk") not in ("", None) for r in rows):
            continue
        date, g = rows[0]["date"], str(rows[0]["draft_group"])
        teams = defaultdict(list)
        for r in rows:
            teams[r["team"]].append(r)
        mins = lambda r: num(r.get("min")) or 0
        score = {t: sum(num(r.get("pts")) or 0 for r in rs) for t, rs in teams.items()}
        opp = {}
        for r in rows:
            two = (r.get("game") or "").split("@")
            if len(two) == 2:
                opp[r["team"]] = two[1] if r["team"] == two[0] else two[0]
        blow = {t for t in teams if t in opp and opp[t] in score and abs(score[t] - score[opp[t]]) >= BLOWOUT}
        live = [r for r in rows if r.get("status") != "Out"]
        scratch = {r["dk_id"] for r in live if (num(r.get("min_proj")) or 0) >= 15 and not mins(r)}
        outT = {t for t, rs in teams.items() if any((r.get("status") == "Out" and (num(r.get("min_avg")) or 0) >= 20) or r["dk_id"] in scratch for r in rs)}
        val = sorted([r for r in live if (num(r.get("fp_dk")) or 0) > 0], key=lambda r: -(num(r["fp_dk"]) / max(1, num(r["salary"]))))
        vrank = {r["dk_id"]: i + 1 for i, r in enumerate(val)}
        og = own.get(g, {})
        top_own = {k for k, _ in sorted(og.items(), key=lambda kv: -kv[1][1])[:5]}

        def tags(r, market=False):
            t = []
            if r["dk_id"] in scratch:
                t.append("late news / scratch")
            if r["team"] in outT and r["dk_id"] not in scratch:
                t.append("teammate out")
            ma = num(r.get("min_avg"))
            if ma is not None and (abs((num(r.get("min_proj")) or 0) - ma) >= 5 or abs((num(r.get("min_last5")) or ma) - ma) >= 5):   # pre-game evidence only
                t.append("minutes role change")
            if r.get("src") != "box" or num(r.get("dk_last5")) is None or r.get("missed"):
                t.append("newcomer / few games")
            if r["team"] in blow:
                t.append("blowout")
            if num(r.get("dk_avg")) is not None and num(r.get("dk_last5")) is not None and abs(num(r["dk_avg"]) - num(r["dk_last5"])) >= 5:
                t.append("stale DK avg")
            if market and vrank.get(r["dk_id"], 999) <= 15:
                t.append("salary-value spot")
            if market and (r["dk_id"] in top_own or (og.get(r["dk_id"], (0, 0))[1] >= 30)):
                t.append("chalk concentration")
            if r.get("status") == "Questionable":
                t.append("Q status")
            return t or ["unexplained"]

        def team_tags(t):
            x = []
            if any(r["dk_id"] in scratch for r in teams[t]):
                x.append("late news / scratch")
            if any(r.get("status") == "Out" and (num(r.get("min_avg")) or 0) >= 20 for r in teams[t]):
                x.append("teammate out")
            if t in blow:
                x.append("blowout")
            if any(r.get("status") == "Questionable" for r in teams[t]):
                x.append("Q status")
            return x or ["unexplained"]

        def add(lens, subject, team, miss, detail, tg, driver=""):
            out.append({"date": date, "draft_group": g, "lens": lens, "subject": subject, "team": team, "miss": round(miss, 2), "detail": detail, "tags": "; ".join(tg), "driver": driver})
        # minutes
        mm = [r for r in live if (num(r.get("min_proj")) or 0) >= 10 or mins(r) >= 10]
        for r in sorted(mm, key=lambda r: -abs(mins(r) - (num(r.get("min_proj")) or 0)))[:5]:
            add("minutes", r["name"], r["team"], mins(r) - (num(r.get("min_proj")) or 0), "%.0f projected, %.0f played" % (num(r.get("min_proj")) or 0, mins(r)), tags(r))
        # shape: top-2 share of the team's points, ours vs real
        sh = []
        for t, rs in teams.items():
            lv = [r for r in rs if r.get("status") != "Out" and (num(r.get("fp_dk")) or 0) > 0]
            po, pa = sum(num(r["fp_dk"]) for r in lv), sum(num(r.get("actual_dk")) or 0 for r in rs)
            if len(lv) >= 5 and po > 0 and pa > 0:
                o2 = sum(sorted((num(r["fp_dk"]) / po for r in lv), reverse=True)[:2])
                a2 = sum(sorted(((num(r.get("actual_dk")) or 0) / pa for r in rs), reverse=True)[:2])
                sh.append((o2 - a2, t, o2, a2))
        for e, t, o2, a2 in sorted(sh, key=lambda x: -abs(x[0]))[:3]:
            add("shape", t, t, 100 * e, "top-2 share ours %.0f%% vs real %.0f%%" % (100 * o2, 100 * a2), team_tags(t))
        # Vegas: the team's real DK points against our summed projection
        vg = []
        for t, rs in teams.items():
            r0 = next((r for r in rs if num(r.get("ou")) and num(r.get("spread")) is not None), None)
            if r0:
                ours = sum(num(r.get("fp_dk")) or 0 for r in rs if r.get("status") != "Out"); real = sum(num(r.get("actual_dk")) or 0 for r in rs)
                vg.append((real - ours, t, num(r0["ou"]) / 2 - num(r0["spread"]) / 2, ours, real))
        for e, t, imp, ours, real in sorted(vg, key=lambda x: -abs(x[0]))[:3]:
            add("Vegas", t, t, e, "implied %.1f, ours %.0f, real %.0f" % (imp, ours, real), team_tags(t))
        # salary: the 2 sd gaps off the salary line (as A1)
        if len(val) >= 10:
            xs, ys = [num(r["salary"]) for r in val], [num(r["fp_dk"]) for r in val]
            mx, my = S.mean(xs), S.mean(ys)
            b_ = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a_ = my - b_ * mx
            res = [y - (a_ + b_ * x) for x, y in zip(xs, ys)]; sd = S.pstdev(res)
            for r, e in sorted(zip(val, res), key=lambda z: -abs(z[1])):
                if abs(e) >= 2 * sd:
                    dv, parts = gap_driver(r, e)
                    add("salary", r["name"], r["team"], (num(r.get("actual_dk")) or 0) - num(r["fp_dk"]),
                        "projection %+.1f off the salary line; %.1f projected, %.1f real; $%s; vs last 5 %s" % (
                            e, num(r["fp_dk"]), num(r.get("actual_dk")) or 0, r["salary"], ", ".join("%s %+.1f" % kv for kv in parts.items()) or "-"),
                        tags(r, market=True), "%s (%s)" % (dv, "above" if e > 0 else "below"))
        # ownership
        byid = {r["dk_id"]: r for r in rows}
        for k, (pj, ac) in sorted(((k, v) for k, v in og.items() if k in byid), key=lambda kv: -abs(kv[1][1] - kv[1][0]))[:5]:
            r = byid[k]
            add("ownership", r["name"], r["team"], ac - pj, "%.0f%% projected, %.0f%% real (%s)" % (pj, ac, base[g][1]), tags(r, market=True))
        # ownership by team (B1): a team's summed ownership, real minus projected, top 3
        if og:
            tsum = defaultdict(lambda: [0.0, 0.0])
            for k, (pj, ac) in og.items():
                if k in byid:
                    tsum[byid[k]["team"]][0] += pj; tsum[byid[k]["team"]][1] += ac
            for t, (pj, ac) in sorted(tsum.items(), key=lambda kv: -abs(kv[1][1] - kv[1][0]))[:3]:
                add("own team", t, t, ac - pj, "summed %.0f%% projected, %.0f%% real" % (pj, ac), team_tags(t))
    if out:
        with open(MISSES, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=MISSES_COLS)
            w.writeheader()
            w.writerows(out)
    if not out:
        print("No graded slates.")
        return
    last = max(r["date"] for r in out)
    if getattr(a, "friday", False):
        d = dt.date.fromisoformat(last); mon = (d - dt.timedelta(days=d.weekday())).isoformat()
        for label, rs in (("week of %s" % mon, [r for r in out if r["date"] >= mon]), ("all %d nights" % len({r["date"] for r in out}), out)):
            c, by = Counter(), defaultdict(Counter)
            for r in rs:
                for t in r["tags"].split("; "):
                    c[t] += 1; by[t][r["lens"]] += 1
            print("Misses by tag, %s (%d misses on %d slates; a miss can carry several tags):" % (label, len(rs), len({(r["date"], r["draft_group"]) for r in rs})))
            for t, n in c.most_common():
                print("  %-22s %3d   %s" % (t, n, ", ".join("%s %d" % kv for kv in by[t].most_common())))
            sg = [r for r in rs if r["lens"] == "salary"]
            if sg:                      # what drives the salary gaps: does our rate run hot on stars?
                star = lambda r: "$8K+" if int(re.search(r"\$(\d+)", r["detail"]).group(1)) >= 8000 else "under $8K"
                dc = Counter((r["driver"], star(r)) for r in sg)
                print("  salary gaps by driver (%d; real minus projected beside): " % len(sg) + "; ".join(
                    "%s %s %d (%+.1f)" % (d, b, n, S.mean(x["miss"] for x in sg if x["driver"] == d and star(x) == b)) for (d, b), n in dc.most_common()))
        return
    for r in [r for r in out if r["date"] == last]:
        print("%s %s %-9s %-24s %+7.1f  %s  [%s]%s" % (r["date"], r["draft_group"], r["lens"], r["subject"], r["miss"], r["detail"], r["tags"], "  driver: " + r["driver"] if r["driver"] else ""))


SWAP_GRADES = os.path.join(DK, "swap_grades.csv")
SWAP_COLS = ["date", "draft_group", "exported", "contest", "accepted", "step", "out_id", "out_name", "in_id", "in_name", "ev_before", "ev_after",
             "out_actual", "in_actual", "gain_actual"]


def swaps(a):
    """Late swap graded (2026-11-23, the owner: with late swap the entered lineups are no longer the build's): a swap log
    from the DK page's Swap step (Save swap log: each export's proposals per entry, accepted or not, no entry IDs), each
    proposed swap scored on the night's box scores: DraftKings points of the player in less the player out, beside the
    expected payout the tool gave it. Accepted swaps are the decisions made; the rest are the tool's advice not taken.
    Appends to swap_grades.csv (a log's rows replace any earlier ones for its slate and export time)."""
    if a.group:       # the sync repo's merged log (2026-11-24: the DK page writes it; no file to send)
        import urllib.request
        url = "https://raw.githubusercontent.com/%s/main/cbb/%s/swaplog.json" % (a.sync_repo, a.group)
        d = json.loads(urllib.request.urlopen(url, timeout=30).read().decode("utf-8"))
    else:
        d = json.load(open(a.log))
    if d.get("kind") != "dk-swap-log":
        sys.exit("not a DK swap log")
    dg, day = str(d["slate"]), d.get("day")
    rec = {r["dk_id"]: r for r in records() if str(r.get("draft_group")) == dg}
    if not rec:
        sys.exit("no graded box scores for draft group %s yet (run the nightly grading first)" % dg)
    act = lambda i: num((rec.get(i) or {}).get("actual_dk"))
    nm = lambda i: (rec.get(i) or {}).get("name") or i
    rows = []
    for ex in d["log"]:
        for e in ex["entries"]:
            prev = (e.get("cur") or {}).get("ev")
            for k, st in enumerate(e.get("steps") or []):
                o, i = act(st["out"]), act(st["in"])
                rows.append({"date": day, "draft_group": dg, "exported": ex["exported"], "contest": e.get("contest"), "accepted": int(bool(e.get("accepted"))),
                             "step": k + 1, "out_id": st["out"], "out_name": nm(st["out"]), "in_id": st["in"], "in_name": nm(st["in"]),
                             "ev_before": prev, "ev_after": st.get("ev"), "out_actual": o, "in_actual": i,
                             "gain_actual": None if o is None or i is None else round(i - o, 2)})
                prev = st.get("ev")
    old = []
    if os.path.exists(SWAP_GRADES):
        keep = {(r["draft_group"], r["exported"]) for r in rows}
        old = [r for r in csv.DictReader(open(SWAP_GRADES)) if (r["draft_group"], r["exported"]) not in keep]
    with open(SWAP_GRADES, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SWAP_COLS); w.writeheader(); w.writerows(old + rows)
    for lab, sel in (("accepted", 1), ("not taken", 0)):
        v = [r for r in rows if r["accepted"] == sel and r["gain_actual"] is not None]
        if v:
            ev = [r["ev_after"] - r["ev_before"] for r in v if r["ev_after"] is not None and r["ev_before"] is not None]
            print("%-10s %3d swaps: the player in outscored the player out on %d (%.0f%%), %+.1f DK points a swap; expected payout %+.2f a swap" % (
                lab, len(v), sum(1 for r in v if r["gain_actual"] > 0), 100.0 * sum(1 for r in v if r["gain_actual"] > 0) / len(v),
                sum(r["gain_actual"] for r in v) / len(v), sum(ev) / len(ev) if ev else 0))
        else:
            print("%-10s no graded swaps" % lab)
    print("%d rows to %s" % (len(rows), SWAP_GRADES))


FIELD_USERS = os.path.join(DK, "field_users.csv")
FIELD_USERS_COLS = ["date", "draft_group", "contest_id", "contest", "size", "user", "entries", "lineups",
                    "own_sum", "own_avg", "sub5"]
SUB5 = 5.0          # a player under this projected ownership (%) counts as leverage


def small_contest(c):
    """The qualifier profile's contests (2026-11-24, the contest profiles): 10-30 entries, or a qualifier / satellite
    (ticket prizes) under 100 entries."""
    size = int(num((c or {}).get("size")) or 0)
    return 10 <= size <= 30 or (size < 100 and bool(re.search(r"qualifier|satellite", (c or {}).get("name") or "", re.I)))


def fieldusers(a):
    """Capture only (2026-11-24, the operator; nothing reads it yet): from each graded small contest's standings
    (small_contest: the qualifiers), one row per user: entries, distinct lineups, the mean summed projected ownership
    of their lineups (own_sum, chalk-follow) and per player (own_avg), and the mean count of players projected under
    SUB5% (sub5, leverage). Projected ownership is the night record's own (the pipeline's, before lock). The owner's own
    entries (USER) are left out. Rebuilt whole."""
    mirror, out = Mirror(a.mirror), []
    for path in sorted(glob.glob(os.path.join(STANDINGS, "contest-standings-*.csv"))):
        cid = re.search(r"(\d+)\.csv$", path).group(1)
        entries, _ = standings(path)
        if not entries or len(entries) > 100:
            continue
        rows, slate, _ = slate_for(mirror, cid)
        c = next((x for x in (slate or {}).get("contests") or [] if str(x.get("id")) == cid), None)
        if not rows or not c or not small_contest(c):
            continue
        own = {}
        for r in rows:
            v = num(r.get("own"))
            if v is not None:
                own.setdefault(r["name"], v)
        users = defaultdict(list)
        for e in entries:
            users[re.sub(r"\s*\(\d+/\d+\)$", "", e["name"]).strip()].append(lineup_names(e["lineup"]))
        for u, lus in sorted(users.items()):
            if u.lower() == USER:          # the field only: the owner's own entries are graded elsewhere
                continue
            sums = [sum(own.get(nm, 0.0) for nm in L) for L in lus if L]
            subs = [sum(1 for nm in L if nm in own and own[nm] < SUB5) for L in lus if L]
            n = max(1, len(sums))
            out.append({"date": rows[0]["date"], "draft_group": rows[0]["draft_group"], "contest_id": cid, "contest": c.get("name"),
                        "size": c.get("size"), "user": u, "entries": len(lus), "lineups": len({tuple(sorted(L)) for L in lus if L}),
                        "own_sum": round(sum(sums) / n, 1), "own_avg": round(sum(sums) / n / 8, 2), "sub5": round(sum(subs) / n, 2)})
    with open(FIELD_USERS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELD_USERS_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print("%d user rows from %d small contests to %s" % (len(out), len({r["contest_id"] for r in out}), FIELD_USERS))
    qualcheck(a)


QUAL_REFIT_AT = 10      # real qualifier fields captured before the DK page's assumed chalk field (QUAL_CHALK) is refit


def qualcheck(a=None):
    """How many real qualifier fields field_users.csv holds (contests named qualifier / satellite): the DK page's
    qualifier field is an assumed chalk style (QUAL_CHALK 0.8) until QUAL_REFIT_AT of them are in; then refit it
    (fill_profiles_2026-11-24.md, the refit plan)."""
    rows = read(FIELD_USERS)
    q = sorted({r["contest_id"] for r in rows if re.search(r"qualifier|satellite", r.get("contest") or "", re.I)})
    users = sum(1 for r in rows if r["contest_id"] in q)
    print("  qualifier fields captured: %d of %d for the chalk-field refit (%d user rows)%s"
          % (len(q), QUAL_REFIT_AT, users, "; REFIT DUE: fill_profiles_2026-11-24.md has the plan" if len(q) >= QUAL_REFIT_AT else ""))


def flagjoint(a):
    """The flagships filled together (the DK page's flagship profile, joint top-1% coverage) against each alone, for
    every saved build not yet logged: a row each in analysis/cbb/dk/flagship_joint.csv (scripts/dk_flagship_compare.py;
    in-sim, scored on fresh nights). Run by nightly, so it accrues."""
    import dk_flagship_compare as fcmp
    fcmp.run(Mirror(a.mirror))


# The shadow lab (2026-11-24, the operator): pre-registered experiments graded on real results, no entries needed.
# analysis/cbb/dk/lab.json holds the registry (fixed before the first counted slate) and the results this rewrites;
# lab_eval.csv the per-slate, per-contest rows. Run by ideas (nightly) and on its own (lab).
LAB = os.path.join(DK, "lab.json")
LAB_EVAL = os.path.join(DK, "lab_eval.csv")
LAB_COLS = ["date", "draft_group", "experiment", "arm", "counted", "contest_id", "contest", "entries", "t_n", "c_n", "t_pct", "c_pct", "diff",
            "t_top10", "c_top10", "top10_diff"]
LAB_MIN_ENTRIES = 100
STACK_RE = re.compile(r"STACK (\S+@\S+) (\d\+\d)")
DRAW9_RE = re.compile(r"^(.*) (L[\d.]+ U\d+)$")
GROUP_RE = re.compile(r"(^|: )at least \d+ of ", re.I)


def lab_arms(b, team):
    """{(experiment, arm): (treatment indices, control indices)} among the bank's kept lineups. arm is "" for a and b,
    the cell ("L0.1 U1") for c."""
    tags = [set(t) if isinstance(t, list) else {t} for t in b["tags"]]
    kept = sorted(set(b["final"])) if b.get("final") else list(range(len(b["pool"])))
    st = b.get("tag_settings") or {}
    out = {}
    # a: STACK vs the plain game-group tags of the same games
    games = {m.group(1) for k in kept for t in tags[k] for m in [STACK_RE.search(t)] if m}
    if games:
        teams_of = {g: set(g.split("@")) for g in games}

        def game_group(tag):
            for r in (st.get(tag) or {}).get("conds") or []:
                ids = r.get("ids") or []
                ts = {team.get(str(i)) for i in ids}
                if r.get("type") == "min" and (r.get("n") or 0) >= 2 and not r.get("stackq") and ids and any(ts <= teams_of[g] for g in games):
                    return True
            return False
        T = [k for k in kept if any(STACK_RE.search(t) for t in tags[k])]
        C = [k for k in kept if not any(STACK_RE.search(t) for t in tags[k]) and any(game_group(t) for t in tags[k])]
        out[("a", "")] = (T, C)
    # b: SCANFLOOR vs group rules
    T = [k for k in kept if any("SCANFLOOR" in t for t in tags[k])]
    if T:
        grp = lambda tag: any(GROUP_RE.search(r.get("label") or "") for r in (st.get(tag) or {}).get("conds") or [] if r.get("type") == "min")
        C = [k for k in kept if not any("SCANFLOOR" in t for t in tags[k]) and any(grp(t) for t in tags[k])]
        out[("b", "")] = (T, C)
    # d: GREENS game groups (the DK page's Set greens) vs the operator's own group rules ("at least N of", in a tag with
    # no GREENS / STACK / SCANFLOOR)
    T = [k for k in kept if any("GREENS " in t for t in tags[k])]
    if T:
        plain = lambda tag: not ("GREENS " in tag or STACK_RE.search(tag) or "SCANFLOOR" in tag)
        hand = lambda tag: plain(tag) and any(GROUP_RE.search(r.get("label") or "") and not r.get("greens") for r in (st.get(tag) or {}).get("conds") or [] if r.get("type") == "min")
        C = [k for k in kept if not any("GREENS " in t for t in tags[k]) and any(hand(t) for t in tags[k])]
        out[("d", "")] = (T, C)
    # c: each Draw the 9 cell vs the same idea's L0 U0
    cells = defaultdict(lambda: defaultdict(set))         # cell -> idea -> kept indices
    for k in kept:
        for t in tags[k]:
            m = DRAW9_RE.match(t)
            if m:
                cells[m.group(2)][m.group(1)].add(k)
    base = cells.get("L0 U0") or {}
    for cell, by in cells.items():
        if cell == "L0 U0":
            continue
        ideas = [i for i in by if i in base]
        if ideas:
            out[("c", cell)] = (sorted(set().union(*(by[i] for i in ideas))), sorted(set().union(*(base[i] for i in ideas))))
    return out


def lab_summary(nights, planned, bar):
    """The scoreboard numbers for a list of slate differences (oldest first): verdict on the first `planned`."""
    d = [n["diff"] for n in nights]
    first = d[:planned]
    mean = S.mean(first) if first else None
    se = S.stdev(first) / math.sqrt(len(first)) if len(first) >= 2 else None
    ahead = sum(x > 0 for x in first)
    res = {"nights": len(d), "counted_for_verdict": len(first), "planned": planned, "diff": round(mean, 2) if mean is not None else None,
           "noise": round(se, 2) if se is not None else None, "ahead": ahead, "behind": sum(x < 0 for x in first),
           "top10_diff": round(S.mean(n["top10_diff"] for n in nights[:planned]), 4) if nights else None, "verdict": "running"}
    if len(first) >= planned:
        ok = ahead >= bar["ahead_nights"] and se is not None and mean > bar["pooled_over_noise"] * se
        res["verdict"] = "pass" if ok else "fail"
    return res


def lab(a=None):
    """Grade the registered experiments (lab.json) on every saved bank with real results; rewrite lab.json's results
    and lab_eval.csv. Slates before an experiment's registration are a look-back, shown but not counted."""
    reg = json.load(open(LAB))
    banks = {}
    for f in sorted(glob.glob(os.path.join(BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if b.get("pool") and b.get("tags") and (g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or "")):
            banks[g] = b
    contests = defaultdict(dict)
    for r in read(EVAL):
        contests[str(r["draft_group"])][r["contest_id"]] = r["contest"]
    rows, nights = [], defaultdict(list)          # (experiment, arm) -> [{date, draft_group, counted, diff, top10_diff, ...}]
    for g, b in sorted(banks.items(), key=lambda kv: (kv[1].get("day") or "", kv[0])):
        rec = read(os.path.join(DK, "%s_%s.csv" % (b["day"], g)))
        if not rec:
            continue
        team = {r["dk_id"]: r["team"] for r in rec}
        arms = {k: v for k, v in lab_arms(b, team).items() if v[0] and v[1]}
        if not arms:
            continue
        per = defaultdict(list)
        for cid, cname in sorted(contests.get(g, {}).items()):
            path = os.path.join(STANDINGS, "contest-standings-%s.csv" % cid)
            if not os.path.exists(path):
                continue
            entries, players = standings(path)
            n = len(entries)
            if n < LAB_MIN_ENTRIES:
                continue
            pts = night_points(rec, players)
            field = sorted((e["points"] for e in entries), reverse=True)
            top10 = math.ceil(0.1 * n)
            score = {}

            def fin(k):
                if k not in score:
                    p = placed(sum(pts.get(str(i)) or 0 for i in b["pool"][k]), field)
                    score[k] = (100.0 * (n - (p - 1)) / n, p <= top10)
                return score[k]
            for (ex, arm), (T, C) in arms.items():
                tp, cp = [fin(k)[0] for k in T], [fin(k)[0] for k in C]
                tt, ct = sum(fin(k)[1] for k in T) / len(T), sum(fin(k)[1] for k in C) / len(C)
                row = {"date": b["day"], "draft_group": g, "experiment": ex, "arm": arm, "contest_id": cid, "contest": cname, "entries": n,
                       "t_n": len(T), "c_n": len(C), "t_pct": round(S.mean(tp), 3), "c_pct": round(S.mean(cp), 3),
                       "diff": round(S.mean(tp) - S.mean(cp), 3), "t_top10": round(tt, 4), "c_top10": round(ct, 4), "top10_diff": round(tt - ct, 4)}
                per[(ex, arm)].append(row)
        regd = {e["id"]: e for e in reg["experiments"]}
        for key, rs in per.items():
            counted = b["day"] >= regd[key[0]]["registered"]
            for r in rs:
                r["counted"] = int(counted)
            rows.extend(rs)
            nights[key].append({"date": b["day"], "draft_group": g, "counted": counted, "contests": len(rs), "t_n": rs[0]["t_n"], "c_n": rs[0]["c_n"],
                                "diff": round(S.mean(r["diff"] for r in rs), 2), "top10_diff": round(S.mean(r["top10_diff"] for r in rs), 4),
                                "t_pct": round(S.mean(r["t_pct"] for r in rs), 2), "c_pct": round(S.mean(r["c_pct"] for r in rs), 2)})
    for e in reg["experiments"]:
        keys = sorted(k for k in nights if k[0] == e["id"])
        arms = {}
        for k in keys or ([(e["id"], "")] if e["id"] != "c" else []):
            ns = nights.get(k, [])
            cnt = [x for x in ns if x["counted"]]
            arms[k[1] or "all"] = dict(lab_summary(cnt, e["planned_nights"], e["pass"]), slates=cnt, lookback=[x for x in ns if not x["counted"]])
        e["results"] = {"arms": arms}
    reg["updated_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LAB, "w") as f:
        json.dump(reg, f, indent=2)
        f.write("\n")
    with open(LAB_EVAL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LAB_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for e in reg["experiments"]:
        for arm, r in e["results"]["arms"].items():
            print("  lab %s%s: %d of %d slates, diff %s ± %s, ahead %d / behind %d, %s; look-back %d slate%s" % (
                e["id"], "" if arm == "all" else " " + arm, r["nights"], r["planned"], r["diff"], r["noise"], r["ahead"], r["behind"], r["verdict"],
                len(r["lookback"]), "" if len(r["lookback"]) == 1 else "s"))


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
    pa_ = sub.add_parser("projaudit")
    pa_.add_argument("--mirror", help="the mirror checkout: the shape lens on today's open slates too")
    sub.add_parser("ownaudit")
    sw = sub.add_parser("swaps"); sw.add_argument("--log", help="a saved swap log file"); sw.add_argument("--group", help="a draft group: its log from the sync repo")
    sw.add_argument("--sync-repo", default="JonBoyBeats/dk-sync")
    ow = sub.add_parser("ownwatch")
    ow.add_argument("--mirror", required=True)
    ms = sub.add_parser("misses")
    ms.add_argument("--friday", action="store_true", help="counts by tag: the latest night's week, and all nights")
    sub.add_parser("risers")
    sub.add_parser("platoon")
    pr = sub.add_parser("pairs")
    pr.add_argument("--mirror", required=True)
    fl = sub.add_parser("fills")
    fl.add_argument("--mirror", required=True)
    fc = sub.add_parser("fieldcheck")
    fc.add_argument("--mirror", required=True)
    fu = sub.add_parser("fieldusers")
    fu.add_argument("--mirror", required=True)
    sub.add_parser("qualcheck")
    sub.add_parser("lab")
    fj = sub.add_parser("flagjoint")
    fj.add_argument("--mirror", required=True)
    r = sub.add_parser("readout")
    r.add_argument("--sim-z", dest="sim_z", help="a dk_cbb_field.json, for the sim's draw shape (default: none)")
    a = ap.parse_args()
    os.makedirs(STANDINGS, exist_ok=True)
    return {"nightly": nightly, "gate": gate, "tiles": tiles, "weights": weights, "readout": readout, "cutcheck": cutcheck, "audit": audit, "calnote": calnote, "calweek": calweek, "ideas": ideas, "risers": risers, "fills": fills, "platoon": platoon, "pairs": pairs, "fieldcheck": fieldcheck, "owncard": owncard, "scan": scan_grade, "projaudit": projaudit, "misses": misses, "ownaudit": ownaudit, "ownwatch": ownwatch, "swaps": swaps, "fieldusers": fieldusers, "qualcheck": qualcheck, "flagjoint": flagjoint, "lab": lab}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
