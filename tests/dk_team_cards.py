"""The team write-up's rules (scripts/dk_team_cards.py): python3 tests/dk_team_cards.py"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_team_cards as C  # noqa: E402

ok = bad = 0


def check(name, cond):
    global ok, bad
    print(("PASS " if cond else "FAIL ") + name)
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
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
