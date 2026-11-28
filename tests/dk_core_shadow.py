"""The green-core shadow (scripts/dk_core_shadow.py; scripts/dk_scorecard.py core_shadow_lines):
python3 tests/dk_core_shadow.py

Hand-made builds and log rows: the top-5 core and green-core sets, the pre-registration / counted split, the
ahead-on-both count against the 7-of-10 decision, the per-lineup-picked dollars, and the no-saved-build note."""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_core_shadow as CS  # noqa: E402
import dk_scorecard as SC  # noqa: E402

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or not info else "  " + str(info)))
    ok += bool(cond)
    bad += not cond


# 1. cores: 7 cores, one lineup each (players 1..24 by salary 24000 down); board values rank core i at 7 - i
sal = {str(i): 25000 - 1000 * i for i in range(1, 40)}
pool = [[str(3 * i + 1), str(3 * i + 2), str(3 * i + 3), "30", "31", "32", "33", "34"] for i in range(7)]
B = {"pool": pool, "final": list(range(7)), "cut_state": {"board": {"values": [[7 - i] for i in range(7)]}}}
green = {"4", "5", "16", "17", "19", "20"}         # cores 1 (4,5,6), 5 (16,17,18) and 6 (19,20,21) hold 2+ greens
s = CS.core_sets(B, sal, green)
check("top 5 cores: the 5 best board values", s["top5cores"] == [0, 1, 2, 3, 4], s["top5cores"])
check("green cores: 2+ greens, best first", s["green_top5"] == [1, 5, 6], s["green_top5"])
check("no board values: None", CS.core_sets({"pool": pool, "final": list(range(7)), "cut_state": {}}, sal, green) is None)


# 2. the scorecard section: two pre-registration slates, three counted
def row(date, g, cid, v, pct, dollars, n=2, picked=2, phase="counted"):
    return {"date": date, "draft_group": g, "contest_id": cid, "contest": "CBB $100 And-One", "size": "500", "fee": "1", "n": str(n),
            "variant": v, "set_size": "", "finish_pct": str(pct), "dollars": str(dollars), "fees": str(picked), "phase": phase,
            "lineups": "|".join(["1 2 3 4 5 6 7 8"] * picked)}
rows = []
for d, g, pg in (("2026-11-25", "1", "pre-registration"), ("2026-11-26", "2", "pre-registration")):
    rows += [row(d, g, "c" + g, "base", 50, 0, phase=pg), row(d, g, "c" + g, "green_top5", 60, 2, phase=pg),
             row(d, g, "c" + g, "top5cores", 40, 0, phase=pg), row(d, g, "c" + g, "entered", 50, 0, phase=pg)]
# counted: slate A green ahead on both; slate B green ahead on pct only; slate C green filled 1 of 2 and ahead per lineup
rows += [row("2026-11-28", "10", "a", "base", 50, 1), row("2026-11-28", "10", "a", "green_top5", 55, 3), row("2026-11-28", "10", "a", "entered", 50, 1)]
rows += [row("2026-11-29", "11", "b", "base", 50, 4), row("2026-11-29", "11", "b", "green_top5", 70, 2), row("2026-11-29", "11", "b", "entered", 50, 4)]
rows += [row("2026-11-30", "12", "c", "base", 50, 2), row("2026-11-30", "12", "c", "green_top5", 52, 2, picked=1), row("2026-11-30", "12", "c", "entered", 50, 2)]
evals = [{"who": "mine", "date": "2026-11-29", "draft_group": "99", "contest": "CBB $100 And-One", "entries": "500"}]
L = SC.core_shadow_lines(rows, evals)
txt = "\n".join(L)
counted = L[L.index(next(x for x in L if x.startswith("### Counted"))):L.index(next(x for x in L if x.startswith("### Pre-registration")))]
gline = next(x for x in counted if x.startswith("| Top-5 green cores"))
check("counted: 3 main slates, pre-registration 2", "### Counted (from 2026-11-28_10): 3 main slates" in txt and "### Pre-registration: 2 main slates" in txt, txt)
check("ahead on both: slates A and C (C per lineup picked: $2 on 1 lineup vs $1 a lineup)", "| 2 of 3 (need 7 of 10) |" in gline, gline)
check("finish pct vs the page: mean of +5, +20, +2", "+9.00 ± " in gline, gline)
check("entries filled: 5 of 6 for the variant, 6 of 6 for the page", "| 5 of 6 / 6 of 6 |" in gline, gline)
check("a main night with no saved build is named", "2026-11-29_99 — no saved build, press Save build" in txt, txt[-300:])
check("no rows: no section", SC.core_shadow_lines([], []) == [])
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
