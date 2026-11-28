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

check("the night record logs gp (games played at lock) and the scorecard splits by it",
      "gp" in cbb_daily.DK_COLS and any("games played at lock" in x for x in SC.lines()))
_doc = {"sources": {"gajewski": {"slates": [
    {"slate": "2026-11-27_157547", "status": "graded", "rows": 200,
     "rot_min": {"ours": 8.0, "source": 7.0, "ruler": 8.5, "n": 60}, "stars_pts": {"ours": 9.0, "source": 9.5, "ruler": 9.2, "n": 20},
     "rot_pts": {"ours": 7.5, "source": 7.4, "ruler": 7.9, "n": 60}, "spearman": {"ours": 0.31, "source": 0.39, "n": 120},
     "disagree": {"below $7k": {"n": 10, "source_closer": 0.6, "mae_ours_minus_source": 0.5}, "$7k+": {"n": 0}},
     "min_disagree": {"below $7k": {"n": 5, "source_closer": 3, "ours_closer": 2, "mae_ours_minus_source": 1.0}, "$7k+": {"n": 0}},
     "ppm": {"below $7k": {"n": 40, "mae_ours": 0.25, "mae_source": 0.27, "bias_ours": -0.05, "bias_source": -0.02}, "$7k+": {"n": 0}}},
    {"slate": "2026-11-28_157555", "status": "not final"}]},
    "rotowire": {"slates": [{"slate": "2026-11-27_157545", "status": "not final",
                 "coverage": {"ours_matched": 175, "lock_players": 305, "teams_covered": 19, "teams": 20, "teams_missing": ["STMRY"]}}]}}}
_sl = SC.source_lines(_doc)
check("the shadow source section: aggregates, the not-final slate, the blend trigger",
      any("Gajewski (shadow): 1 graded slate; not final yet: 2026-11-28_157555" in x for x in _sl)
      and any("-1.00" in x and "1 of 1" in x for x in _sl) and any("due at 10 graded slates (now 1)" in x for x in _sl)
      and any("the source closer on 3, ours on 2" in x for x in _sl) and any("ours MAE 0.250" in x for x in _sl) and any("hybrid" in x for x in _sl)
      and any("RotoWire (shadow): 0 graded slates" in x for x in _sl) and any("ours with a source row 175 of 305, teams 19 of 20" in x for x in _sl))
# source value vs ownership (pre-registered 2026-11-28): the nightly aggregates read into the sources section
_vo = SC.value_own_lines({"source_nights": 6, "first_read_at": 5, "decision_at": 10, "previous_terms": ["chalk_team", "big"], "status": "first read",
                          "test1": {"all": {"bins": [{"err_live": -2.0}, {"err_live": -1.0}, {"err_live": 0.0}, {"err_live": 1.0}, {"err_live": 3.0}],
                                            "q5_minus_q1": 5.0, "se": 1.0, "positive": 6, "n": 6}},
                          "test2": {"src_edge": {"n": 6, "gain": 0.5, "se": 0.2, "better": 5, "off10_gain": 0.01, "off10_se": 0.01,
                                                 "mae_prev": 11.0, "mae_cand": 10.5, "tag": "(no tag before 10 nights; read: PROVEN)"}}})
check("source value vs ownership: count, status, Test 1 quintiles, Test 2 read",
      "source nights with real ownership: 6" in _vo[0] and "first read" in _vo[0] and any("-2.0 / -1.0 / +0.0 / +1.0 / +3.0" in x and "positive on 6 of 6" in x for x in _vo)
      and any("11.00 → 10.50" in x and "no tag before 10" in x for x in _vo), _vo)
_vo2 = SC.value_own_lines({"source_nights": 6, "status": "first read", "test2": {},
                           "per_source": {"all": {"alone": {"us": {"value": {"mean": 0.5, "se": 0.05, "n": 6, "leads": 0}, "proj": None, "value_in_tier": {"mean": 0.4, "se": 0.05, "n": 6, "leads": 0}},
                                                            "gj": {"value": {"mean": 0.6, "se": 0.05, "n": 6, "leads": 0}, "proj": None, "value_in_tier": {"mean": 0.5, "se": 0.05, "n": 6, "leads": 0}}},
                                                  "paired": {"gj_vs_us": {"value": None, "proj": None, "value_in_tier": {"mean": 0.1, "se": 0.02, "n": 6, "leads": 5}, "players": 400}}}},
                           "variants": {"val_gj": {"n": 6, "gain": 0.3, "se": 0.1, "better": 5}, "val_us": {"n": 0, "note": "x"}},
                           "triangulation": {"G1": {"miss": -1.0, "se": 0.5, "nights": 6}, "G5": {"miss": 4.0, "se": 1.0, "nights": 6}}})
check("source value vs ownership amendment: per source, paired within tier, variants, triangulation groups",
      any("GJ value 0.60" in x and "US value 0.50" in x for x in _vo2) and any("GJ − US on common players (400" in x and "GJ leads on 5 of 6" in x for x in _vo2)
      and any("+ val_gj gain +0.30" in x for x in _vo2) and any("G5 +4.0" in x for x in _vo2), _vo2)
check("source value vs ownership amendment: labels pending reads as such", any("pending labels" in x for x in SC.value_own_lines({"source_nights": 1, "status": "context", "test2": {}, "triangulation": "pending labels"})))
check("source value vs ownership: nothing yet reads as context with no tests", SC.value_own_lines({"source_nights": 0, "status": "context", "test2": {}})[0].endswith("context."))
# fill arm on a main-only night (2026-11-28): small fees, no flagship; the gap also reads as % of the night's fees
import tempfile  # noqa: E402
with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date", "draft_group", "subset", "fees", "avg_dollars", "entered_dollars", "beat_entered"])
    w.writeheader()
    w.writerow({"date": "2026-12-01", "draft_group": "999001", "subset": "bank", "fees": "20.0", "avg_dollars": "15.0",
                "entered_dollars": "18.0", "beat_entered": "0.3"})
    w.writerow({"date": "2026-12-02", "draft_group": "999002", "subset": "bank", "fees": "0", "avg_dollars": "0",
                "entered_dollars": "0", "beat_entered": "0.5"})
_fe, SC.E.FILL_EVAL = SC.E.FILL_EVAL, f.name
fa = SC.fill_arm()
SC.E.FILL_EVAL = _fe
os.unlink(f.name)
check("fill arm: gap as % of fees on a main-only night, none (no division) on a zero-fee night",
      abs(fa["999001"]["fee"] - 15.0) < 1e-9 and fa["999002"]["fee"] is None and abs(fa["999001"]["dollars"] - 3.0) < 1e-9, fa)
cell = SC.window_cells("fill", [{"arms": {"fill": fa["999001"]}}, {"arms": {"fill": fa["999002"]}}])[0]
check("fill cell reads with the % of fees", "% of fees" in cell and "+15 (1)" in cell, cell)

# fill proposal 1 (2026-11-28): entered minus fill_prev per contest type; the main review trigger; the 11-27 gate
_ev = [dict(date="2026-11-29", draft_group="999101", contest_id="1", contest="CBB $15 Pull Up Jumper", entries="300", who="mine", dollars_back="30", fees="30"),
       dict(date="2026-11-29", draft_group="999101", contest_id="1", contest="CBB $15 Pull Up Jumper", entries="300", who="fill_prev", dollars_back="10", fees="30"),
       dict(date="2026-11-29", draft_group="999101", contest_id="2", contest="CBB $1 And-One", entries="2000", who="mine", dollars_back="5", fees="20"),
       dict(date="2026-11-29", draft_group="999101", contest_id="2", contest="CBB $1 And-One", entries="2000", who="fill_prev", dollars_back="8", fees="20"),
       dict(date="2026-11-20", draft_group="999100", contest_id="3", contest="CBB $1 And-One", entries="2000", who="fill_prev", dollars_back="8", fees="20")]
_ev += [dict(date="2026-11-29", draft_group="999101", contest_id="4", contest="CBB $10 King of the Bracket Qualifier", entries="20", who="mine", dollars_back="0", fees="10"),
        dict(date="2026-11-29", draft_group="999101", contest_id="4", contest="CBB $10 King of the Bracket Qualifier", entries="20", who="fill_prev", dollars_back="0", fees="10")]
_fl = SC.fill_type_lines(_ev, gate=None, standings_in=False)
check("fill by type: the qualifier tier (QUAL_CHALK 0.35 vs 0.8) with its 10-field review", any("qualifier (PROVISIONAL)" in x and "review at 10 qualifier fields (now 1)" in x for x in _fl), _fl)
check("fill by type: flagship +20 ahead 1, main -3 ahead 0 with the 10-slate review count; gate pending without standings",
      any("flagship (PROVEN): +20.00 (1), ahead 1" in x for x in _fl) and any("main (PROVISIONAL): -3.00 (1), ahead 0" in x and "(now 1)" in x for x in _fl)
      and any("pending (11-27's flagship standings" in x for x in _fl), _fl)
_fl2 = SC.fill_type_lines(_ev, gate={"status": "fails", "note": "+20 vs 2xSE 30"}, standings_in=True)
check("fill gate: a failed 11-27 gate says revert", any("FAILS – revert the flagship tier (+20 vs 2xSE 30)" in x for x in _fl2), _fl2)
# the bank (batch item 2, 2026-11-28): the line reads n/a with the 10-build review count before any graded build
_bl = SC.bank_lines([])
check("bank line: live bank minus the Draw-the-9 replay, PROVISIONAL with the 10-build review", any("live bank − Draw-the-9 replay" in x and "review at 10 builds" in x for x in _bl), _bl)
# batch item 5 (2026-11-28): the late-swap arm is off the scorecard; the over-trust gauge reads ours vs the field
check("scorecard: no late-swap arm row", "late swap" not in SC.ARM_OF and not any(l.startswith("| late swap") for l in SC.lines(sl, fake, today="2026-12-03")))
_ot = SC.over_trust_lines([{"slate": "2026-12-01_1", "ours": -8.0, "field": -1.0, "d": -7.0, "n": 20},
                           {"slate": "2026-12-02_2", "ours": -6.0, "field": -2.0, "d": -4.0, "n": 10}])
check("over-trust gauge: ours, field and ours minus field, rolling and last night",
      any("ours -7.0 ± 1.0 (2), field -1.5 ± 0.5 (2), ours − field -5.5 ± 1.5 (2)" in x for x in _ot) and any("last night (2026-12-02_2, 10 entries): ours -6.0, field -2.0" in x for x in _ot), _ot)
# source triangulation (shadow, 2026-11-28): per-group counts, recipe MAEs, closest source, the decision trigger; labels carry no numbers
_rec = lambda pts: {"pts": pts, "min": 5.0, "ppm": 0.25, "n": 10, "n_ppm": 8}
_tri = {"bank_sigma": {"lt5": 0.56}, "labels": [{"date": "2026-11-27", "dg": "1", "dk_id": "9", "name": "A", "group": "G2", "minutes_outlier": "RW", "ppm_outlier": ""}],
        "slates": [{"slate": "2026-11-27_1", "status": "graded", "counts": {"G1": 3, "G2": 10},
                    "groups": {"G2": {"n": 10, "recipes": {"US": _rec(7.5), "COMBO": _rec(7.0)}, "closest": {"minutes": {"n": 10, "closest": {"RW": 6, "US": 4},
                               "outlier_closest": 5, "outlier_n": 8}}, "noise": {"rel_miss_us": 0.5, "n": 9}},
                               "_combo_vs_us": {"us": 9.0, "combo": 8.5, "gain": 0.5, "n": 13}}},
                   {"slate": "2026-11-28_2", "status": "not final", "counts": {"G1": 9}}]}
_tl = SC.triangulation_lines(_tri)
check("triangulation: counts, recipe table, closest, COMBO gain, 10-slate trigger",
      any("2 slates, 1 graded" in x for x in _tl) and any("2026-11-27_1 G1 3 G2 10" in x for x in _tl) and any("| G2 minutes split, ppm agree | 10 | 7.50 (1)" in x for x in _tl)
      and any("closest RW 6, US 4 of 10; the outlier was right 5 of 8" in x for x in _tl) and any("+0.50 (1), ahead on 1 of 1" in x for x in _tl)
      and any("due at 10 graded source slates (now 1)" in x for x in _tl), _tl)
_old = SC.TRI_LABELS
SC.TRI_LABELS = tempfile.mktemp(suffix=".csv")
SC.write_tri_labels(_tri)
_lab = list(csv.DictReader(open(SC.TRI_LABELS)))
SC.TRI_LABELS = _old
check("triangulation labels: the seven number-free columns", _lab and list(_lab[0]) == ["date", "dg", "dk_id", "name", "group", "minutes_outlier", "ppm_outlier"])
# the source blend (2026-11-28): counted only where the build says it was loaded; the 7-slate review
_bd = {"slates": [{"slate": "2026-11-28_1", "status": "graded", "all": {"n": 30, "mae_us": 8.0, "mae_blend": 7.5, "bias_us": 2.0, "bias_blend": 1.0},
                   "by_group": {"G1": {"n": 9, "mae_us": 7.0, "mae_blend": 6.9, "bias_us": 1.0, "bias_blend": 1.0}}},
                  {"slate": "2026-11-29_2", "status": "graded", "all": {"n": 30, "mae_us": 8.0, "mae_blend": 9.0, "bias_us": 2.0, "bias_blend": 1.0}},
                  {"slate": "2026-11-30_3", "status": "not final"}]}
_bdl = SC.blend_lines(_bd, {"2026-11-28_1": True, "2026-11-29_2": False})
check("source blend: counts loaded nights only, flags the rest, 7-slate review",
      any("1 counted slate" in x for x in _bdl) and any("+0.50 (1); blend ahead on 1 of 1" in x for x in _bdl) and any("G1 +0.10 (1)" in x for x in _bdl)
      and any("2026-11-29_2 sources not loaded" in x for x in _bdl) and any("2026-11-30_3 no saved build (sources not loaded)" in x for x in _bdl)
      and any("review at 7 counted slates (now 1)" in x for x in _bdl), _bdl)
print("\n%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
