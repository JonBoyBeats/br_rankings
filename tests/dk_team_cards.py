"""The team write-up's rules (scripts/dk_team_cards.py): python3 tests/dk_team_cards.py"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_team_cards as C  # noqa: E402

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or not info else "  " + str(info)))
    ok += bool(cond)
    bad += not cond


# DraftKings points from a box line, with the double-double bonus
check("dk_points: 20 pts 2/5 threes 10 reb 3 ast 1 stl 0 blk 2 to = 20 + 1 + 12.5 + 4.5 + 2 - 1 + 1.5",
      abs(C.dk_points({"PTS": "20", "3PT": "2-5", "REB": "10", "AST": "3", "STL": "1", "BLK": "0", "TO": "2"}) - 40.5) < 1e-9)
check("dk_points: triple-double adds 3 more", abs(C.dk_points({"PTS": "10", "REB": "10", "AST": "10"}) - (10 + 12.5 + 15 + 4.5)) < 1e-9)
# minutes
check("minutes safe: within 3 of season and last 3", C.minutes_note(30, 29, 31) == "minutes safe as projected")
check("projection above recent role, outs named", C.minutes_note(30, 24, 25, out_gain=6) == "projection above recent role (+6 from the outs)")
check("rising role: last 3 +3 over season", C.minutes_note(28, 24, 28) == "rising role")
check("shrinking role", C.minutes_note(22, 28, 24) == "shrinking role")
check("no note when nothing applies", C.minutes_note(25, 28, 29) is None)
# form against EvanMiya
check("bounce back under 0.85", C.form_note([10, 10, 10], [20, 20, 20], 0.7)[0] == "due to bounce back")
check("running hot over 1.15", C.form_note([20, 20, 20], [20, 20, 20], 0.8)[0] == "running hot, regression risk")
check("in line between", C.form_note([15, 15, 15], [20, 20, 20], 0.75)[0] == "in line")
check("no verdict under 3 games", C.form_note([15, 15], [20, 20], 0.75)[0] is None)
# shy away
check("shy away: volatile and low", C.shy_away([8, 18, 10, 22, 9]))
check("not shy: steady", not C.shy_away([14, 15, 16, 15]))
check("not shy: high minutes even if volatile", not C.shy_away([20, 34, 22, 36]))
# pool rule
check("pool: no 5x in last 5 and under 20 projected", C.pool_flag([10, 12, 9, 11, 8], 4000, 15))
check("pool: a 5x game keeps him", not C.pool_flag([10, 21, 9], 4000, 15))
check("pool: 20+ projected keeps him", not C.pool_flag([10, 12, 9], 4000, 22))
check("pool: under 3 games, no call", not C.pool_flag([10, 12], 4000, 15))
# shape and environment
lab, t5, t7, regs = C.shape({str(i): [m] * 4 for i, m in enumerate([34, 32, 30, 30, 28, 22, 16, 5, 3])}, 4)
check("shape: top 7 90%+ is tight", lab == "tight" and regs == 7)
check("environment: slate's lowest O/U by 5+ is a grind", C.environment(150, 150, 140.0, [140.0, 146.0, 150.0]) == "grind")
check("environment: fast teams, not lowest, pace-up", C.environment(60, 100, 150.0, [140.0, 150.0]) == "pace-up")
check("environment: middling", C.environment(200, 150, 150.0, [140.0, 150.0]) == "middling")
check("variant is deterministic", C.variant("Ace", ["a", "b", "c"]) == C.variant("Ace", ["a", "b", "c"]))
# the 4x count, hand-checked (Ace Buckner, $7,000, Clemson's 5 box scores to 11-17: 31.0, 38.0, 27.25, 33.5, 23.5;
# 4x = 28.0: 31.0, 38.0, 33.5 = 3; 5x = 35.0: 38.0 = 1; under 2x = 14.0: none)
bk = [31.0, 38.0, 27.25, 33.5, 23.5]
check("count_games: Buckner 4x = 3, 5x = 1, under 2x = 0",
      C.count_games(bk, 7000, 4) == 3 and C.count_games(bk, 7000, 5) == 1 and len(bk) - C.count_games(bk, 7000, 2) == 0)
check("count_games: exactly at the bar counts", C.count_games([28.0], 7000, 4) == 1)
# outs
check("new out: played this season", C.new_out(3) and not C.new_out(0))
# bottom line
L = lambda **k: dict({"name": "A B", "salary": 4500, "proj_min": 29, "gp": 5, "starts": 5, "mins": [30, 31, 29, 32, 30],
                      "ceil": 2, "season_mpg": 30.4, "dk_pm": 0.8}, **k)
check("core: 30+ projected, steady, every start", C.is_core(L(proj_min=33)))
check("core: not with a missed start", not C.is_core(L(proj_min=33, starts=4)))
check("core: not with swingy minutes", not C.is_core(L(proj_min=33, mins=[20, 36, 25, 38, 30])))
check("value: cheap, 25+ projected, 2+ ceilings", C.is_value(L()))
check("value: not over $5,000", not C.is_value(L(salary=5900)))
check("value: not with 1 ceiling", not C.is_value(L(ceil=1)))
# the moving group read
check("group: the starting job, best rate named", C.group_read(L(name="Dylan Faulkner", starts=4, mins=[33, 33, 30, 27, 20], dk_pm=1.09), "Dylan Faulkner")
      == "Faulkner has the starting job (4 of 5) and the team's best per-minute rate (1.09)")
check("group: steady bench minutes", C.group_read(L(name="Chase Thompson", starts=2, mins=[26, 30, 29, 31, 29], season_mpg=29.0), None)
      .startswith("Thompson's 29 minutes off the bench (2 of 5 starts) are as steady as a starter's (26-31)"))
check("group: starts but plays little, most nights = lowest 60%", C.group_read(L(name="David Fuchs", starts=4, mins=[18, 14, 12, 13, 21], season_mpg=15.6), None)
      == "Fuchs starts (4 of 5) but plays 12-14 most nights (median 14)")
# the Strong tier: 27+ projected, minutes CV <= 0.20, 4+ of the last 5 started or top-2 DK a game (Faulkner, Clemson)
fk = L(name="Dylan Faulkner", salary=6400, proj_min=27.3, starts=4, mins=[33, 33, 30, 27, 20], start_flags=[1, 1, 1, 1, 0], ceil=2, dk_pg=31.2)
check("strong: Faulkner (27.3 projected, CV 0.17, 4 of last 5 started)", C.is_strong(fk, []))
check("strong: top-2 DK a game stands in for the starts", C.is_strong(dict(fk, start_flags=[0, 0, 1, 0, 0]), ["Dylan Faulkner"]))
check("strong: not under 27 projected", not C.is_strong(dict(fk, proj_min=26.0), ["Dylan Faulkner"]))
check("strong: not with swingy minutes", not C.is_strong(dict(fk, mins=[36, 14, 33, 18, 30]), ["Dylan Faulkner"]))
check("strong: not without the starts or the top-2", not C.is_strong(dict(fk, start_flags=[0, 0, 1, 0, 0]), []))
# the rotation shares' context (the reference: team_stats on the banked slates' teams)
check("quantile: linear between order statistics", C.quantile([1, 2, 3, 4], 0.5) == 2.5 and C.quantile([5], 0.9) == 5)
check("pct_below: strictly under", C.pct_below([1, 2, 3, 4], 3) == 0.5)
ref = {"teams": {str(i): {"top5": v, "top7": v + 0.2, "top3dk": v - 0.2} for i, v in enumerate([0.50 + 0.005 * i for i in range(40)])}}
t, d = C.cuts(ref)
check("cuts: the reference's 67th / 33rd top-7 percentiles", abs(t - C.quantile([x["top7"] for x in ref["teams"].values()], 2 / 3)) < 1e-12 and d < t)
check("cuts: the fixed fallback without a reference", C.cuts(None) == (C.TIGHT_TOP7, C.DEEP_TOP7))
hi = C.context(0.69, "top5", ref, [0.69, 0.60, 0.55], ("tighter", "looser"))
check("context: above the median reads tighter, with tonight's rank", hi == " (tighter than nearly every team on our slates; the tightest of 3 tonight)", hi)
lo = C.context(0.52, "top5", ref, [0.69, 0.60, 0.52], ("tighter", "looser"))
check("context: below the median reads looser, in tenths", lo == " (looser than 9 of 10 teams on our slates; 3rd tightest of 3 tonight)", lo)
thin = C.context(0.6, "top5", {"teams": {"a": {"top5": 0.5}, "b": {"top5": 0.7}}}, [], ("tighter", "looser"))
check("context: a thin reference says so", "(thin: 2 teams)" in thin, thin)
st = C.team_stats([{"players": {"a": {"min": 30, "dk": 30}, "b": {"min": 10, "dk": 10}}}])
check("team_stats: shares from the box (2 players: top 5 = all; top 3 DK = all)", st["top5"] == 1.0 and st["top3dk"] == 1.0 and st["regs"] == 1)
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
