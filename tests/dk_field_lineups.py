"""field_lineups.csv (scripts/dk_eval.py fieldlineups): the contest type and a standings Lineup cell as DraftKings ids.
python3 tests/dk_field_lineups.py"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_eval as E  # noqa: E402

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or not info else "  " + str(info)))
    ok += bool(cond)
    bad += not cond


check("contest type: a satellite under 100 is a qualifier", E.contest_type({"name": "CBB Satellite to X", "size": 40}) == "qualifier")
check("contest type: 10-30 entries is a qualifier", E.contest_type({"name": "CBB $3 Dime Time", "size": 20}) == "qualifier")
check("contest type: a mid-size contest is a main", E.contest_type({"name": "CBB $6K Pull Up Jumper", "size": 470}) == "main")
check("contest type: FLAGSHIP_MIN+ entries is a flagship", E.contest_type({"name": "CBB $20K And-One", "size": 5945}) == "flagship")
ids = {"A Guard": "1", "B Guard": "2", "C Fwd": "3", "D Util": "4"}
got = E.lineup_ids("G A Guard G B Guard F C Fwd UTIL D Util UTIL Nobody Known", ids)
check("lineup ids: slot order, ? for a name the record can't place", got == "1 2 3 4 ?", got)
check("lineup ids: an empty entry is ''", E.lineup_ids("", ids) == "")
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
