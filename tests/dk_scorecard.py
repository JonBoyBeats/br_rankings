"""The scorecard and the arm versions (scripts/dk_scorecard.py, scripts/dk_arms.py): python3 tests/dk_scorecard.py

arm_versions.json: every listed versions.csv row exists, each arm's versions run in date order, and the mid-day switch
(the ownership correction from 157026 on 2026-11-24) lands on the right slate. Made-up rows: the paired three-way MAE
(each column on the rows that logged it, live minus it on those rows), a PREVIOUS column equal to live counts as not
logged, the ruler backfill, the chalk band for ownership; made-up slates: the settling count and the same-night-pair
check (MISSING named), and the night record's new columns."""
import csv, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import cbb_daily  # noqa: E402
import dk_arms as A  # noqa: E402
import dk_scorecard as SC  # noqa: E402

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    print(("PASS " if cond else "FAIL ") + name + ("" if cond or not info else "  " + str(info)))
    ok += bool(cond)
    bad += not cond


# 1. arm_versions.json against versions.csv
arms = A.load()
vrows = list(csv.DictReader(open(os.path.join(SC.E.DK, "versions.csv"), newline="", encoding="utf-8")))
keys = {"%s | %s | %s" % (r["date"], r["component"], r["change"][:40]) for r in vrows}
missing = [x for h in arms.values() for v in h for x in v["rows"] if x not in keys]
check("every arm version's versions.csv rows exist", not missing, missing[:3])
check("the arms are the six tags", tuple(arms) == A.ARMS)
check("each arm's versions in date order, unique tags",
      all([v["from"] for v in h] == sorted(v["from"] for v in h) for h in arms.values())
      and len({v["tag"] for h in arms.values() for v in h}) == sum(len(h) for h in arms.values()))
check("ownership: the lock's field on 157024, the correction from 157026",
      A.version("ownership", "2026-11-24", "157024", arms)[0]["tag"] == "own-2026-11-23"
      and A.version("ownership", "2026-11-24", "157026", arms)[0]["tag"] == "own-2026-11-24"
      and A.version("ownership", "2026-11-25", "157293", arms)[1]["tag"] == "own-2026-11-23")
t = A.tags("2026-11-25", "157295", arms)
check("tags for a night record row", t["ver_projection"] == "proj-2026-11-25" and set(t) == {"ver_" + a for a in A.ARMS}, t)
check("before the first version: none", A.version("cut", "2026-11-01", "1", arms) == (None, None))

# 2. the paired three-way
rows = [{"a": 10, "l": 12, "p": 11, "r": None}, {"a": 20, "l": 15, "p": 15.0, "r": 22}, {"a": 30, "l": 30, "p": None, "r": 27}]
x = SC.three_way(rows, lambda r: r["a"], lambda r: r["l"], lambda r: r["p"], lambda r: r["r"])
check("live MAE on every row", abs(x["live"] - (2 + 5 + 0) / 3) < 1e-9 and x["n"] == 3, x)
check("previous on its rows, live minus it on the same rows", abs(x["prev"] - (1 + 5) / 2) < 1e-9 and abs(x["d_prev"] - ((2 + 5) / 2 - 3)) < 1e-9, x)
check("ruler on its rows", abs(x["ruler"] - (2 + 3) / 2) < 1e-9 and abs(x["d_ruler"] - ((5 + 0) / 2 - 2.5)) < 1e-9, x)
check("previous equal to live: not logged", not SC.logged([{"min_old": "20", "min_proj": "20"}], "min_old", "min_proj")
      and SC.logged([{"min_old": "20", "min_proj": "21"}], "min_old", "min_proj"))
check("ruler backfill: the live column on 157021, n/a on 156660 without a ruler column",
      SC.ruler_col([{"ruler_min": ""}], "157021", "ruler_min", "min_proj")({"min_proj": "31"}) == 31.0
      and SC.ruler_col([{"ruler_min": ""}], "156660", "ruler_min", "min_proj")({"min_proj": "31"}) is None
      and SC.ruler_col([{"ruler_min": "29"}], "157300", "ruler_min", "min_proj")({"ruler_min": "29"}) == 29.0)

# 3. ownership: the chalk band per column, the ruler joined from the record
own = [{"draft_group": "157300", "dk_id": "1", "p": 30.0, "raw": 25.0, "a": 40.0},
       {"draft_group": "157300", "dk_id": "2", "p": 5.0, "raw": 16.0, "a": 6.0},
       {"draft_group": "157300", "dk_id": "3", "p": 2.0, "raw": 2.0, "a": 1.0}]
rec = [{"dk_id": "1", "own_ruler": "35"}, {"dk_id": "2", "own_ruler": "4"}, {"dk_id": "3", "own_ruler": ""}]
o = SC.ownership_arm("157300", rec, own)
check("ownership live: band by max(actual, live)", o["n"] == 1 and o["live"] == 10.0 and o["live_off"] == 1.0, o)
check("ownership previous: band by max(actual, live, raw), live minus raw on it",
      abs(o["prev"] - (15 + 10) / 2) < 1e-9 and abs(o["d_prev"] - ((10 + 1) / 2 - 12.5)) < 1e-9 and o["prev_off"] == 1.0, o)
check("ownership ruler: from the record's own_ruler", o["ruler"] == 5.0 and o["d_ruler"] == 5.0, o)

# 4. settling and the same-night-pair check on made-up slates (a change on 2026-12-01)
fake = {"projection": [{"tag": "p-old", "from": "2026-11-16", "rows": []}, {"tag": "p-new", "from": "2026-12-01", "rows": []}],
        "ownership": [{"tag": "o", "from": "2026-11-16", "rows": []}], "field": [{"tag": "f", "from": "2026-11-16", "rows": []}],
        "cut": [{"tag": "c", "from": "2026-11-16", "rows": []}], "fill": [{"tag": "fi", "from": "2026-11-16", "rows": []}],
        "late_swap": [{"tag": "s", "from": "2026-11-16", "rows": []}]}
arm = lambda prev: {"live": 7.0, "prev": prev, "ruler": 7.5, "d_prev": None if prev is None else 7.0 - prev, "d_ruler": -0.5, "n": 40}
sl = [{"slate": "2026-11-%02d_1" % d, "date": "2026-11-%02d" % d, "group": "1", "arms": {"minutes": arm(None)}} for d in (28, 29, 30)]
sl += [{"slate": "2026-12-01_1", "date": "2026-12-01", "group": "1", "arms": {"minutes": arm(6.5)}},
       {"slate": "2026-12-02_1", "date": "2026-12-02", "group": "1", "arms": {"minutes": arm(None)}}]
ls = SC.lines(sl, fake, today="2026-12-03")
row = next(l for l in ls if l.startswith("| minutes |") and "last 5" in l)
check("settling: 2 of 7 under the new version", "p-new (2026-12-01)" in row and "settling 2 of 7" in row, row)
chk = next(l for l in ls if l.startswith("- minutes:"))
check("pair check names the slate without PREVIOUS", "1 of 2" in chk and "MISSING on 2026-12-02_1" in chk, chk)
check("pair check: an arm never changed has nothing to pair", not any(l.startswith("- field:") for l in ls))
real = SC.lines(SC.collect(), arms, today="2026-11-25")
check("pair check: a changed arm with no PREVIOUS column says so",
      any(l.startswith("- field:") and "no PREVIOUS column" in l for l in real), [l for l in real if l.startswith("- field")])
check("paired diff with SE and slate count", "+0.50 (1)" in row and "-0.50 ± 0.00 (5)" in row, row)
check("results read over 20+ nights only", any("20+ nights only" in l for l in ls))

# 5. the night record carries the ruler and the version tags
check("night record columns", all(c in cbb_daily.DK_COLS for c in ("ruler_min", "ruler_fp", "ruler_fp_gate", "own_ruler", "ver_projection", "ver_late_swap")))

print("\n%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
