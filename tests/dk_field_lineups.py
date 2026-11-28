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


import dk_contest_type as T  # noqa: E402

# the DK page's profile (dk.html profileAuto), the one definition (scripts/dk_contest_type.py)
cases = [("CBB $6K Pull Up Jumper [$2K to 1st]", 470, "flagship", "flagship"), ("CBB $1K Pull Up Jumper [$200 to 1st]", 78, "flagship", "flagship"),
         ("CBB $1.25K And-One", 1486, "main", "main"), ("CBB $100 And-One", 118, "main", "main"),
         ("CBB $250 Quarter Jukebox [Just $0.25!]", 1189, "main", "main"), ("CBB $50 Dime Time [Just $0.10!]", 594, "lab", "main"),
         ("CBB Satellite to CBB 12-12 $222 Slam Jam Special", 13, "qualifier", "qualifier"), ("CBB $5 Qualifier", 400, "qualifier", "qualifier"),
         ("CBB $500 High Five [Single Entry]", 118, "flagship", "flagship"), ("CBB $250 High Five [Single Entry]", 59, "qualifier", "qualifier"),
         ("CBB $100 Buzzer Beater", 39, "qualifier", "qualifier"), ("CBB $3 Late Add", 900, "main", "main")]
for nm, n, prof, typ in cases:
    check("page profile: %s (%d) is %s, type %s" % (nm, n, prof, typ), T.profile(nm, n) == prof and T.contest_type(nm, n) == typ,
          (T.profile(nm, n), T.contest_type(nm, n)))
check("dk_eval.contest_type reads the contest dict through the one definition",
      E.contest_type({"name": "CBB $1.25K And-One", "size": 1486}) == "main" and E.contest_type({"name": "CBB $6K Pull Up Jumper", "size": 470}) == "flagship")
ids = {"A Guard": "1", "B Guard": "2", "C Fwd": "3", "D Util": "4"}
got = E.lineup_ids("G A Guard G B Guard F C Fwd UTIL D Util UTIL Nobody Known", ids)
check("lineup ids: slot order, ? for a name the record can't place", got == "1 2 3 4 ?", got)
check("lineup ids: an empty entry is ''", E.lineup_ids("", ids) == "")
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
