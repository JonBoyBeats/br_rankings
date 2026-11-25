"""Tests for the banded A1 proxy lenses (dk_eval.py projaudit, proj_audit.csv): python3 tests/dk_proj_audit_bands.py"""
import csv, glob, os, sys
sys.argv = [sys.argv[0]]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_eval as E

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    if cond:
        ok += 1; print("PASS " + name)
    else:
        bad += 1; print("FAIL " + name + " " + str(info))


cols = ["%s_%s" % (b, f) for b, _, _ in E.PROJ_BANDS for f in E.PROJ_BAND_FIELDS]
check("proj_audit.csv columns: the banded fields for ROTATION and STARS", all(c in E.PROJ_AUDIT_COLS for c in cols) and E.PROJ_BANDS == [("rot", 10.0, 25.0), ("stars", 25.0, float("inf"))])
# pooled: slate means of the rank lenses, gap counts summed, the share on the band's players
rows = [{"rot_n": "10", "rot_own_rank": "0.5", "rot_sal_gaps": "1", "rot_sal_unexplained": "1", "rot_sal_abs": "3", "rot_min_rank": "0.4", "rot_top5_hit": "0.8",
         "stars_n": "4", "stars_own_rank": "", "stars_sal_gaps": "0", "stars_sal_unexplained": "0", "stars_sal_abs": "5", "stars_min_rank": "", "stars_top5_hit": "1",
         "own_rank": "0.8", "sal_gaps": "2", "sal_unexplained": "1", "min_rank": "0.7", "min_top5": "4"},
        {"rot_n": "30", "rot_own_rank": "0.7", "rot_sal_gaps": "3", "rot_sal_unexplained": "0", "rot_sal_abs": "5", "rot_min_rank": "0.6", "rot_top5_hit": "0.6",
         "stars_n": "6", "stars_own_rank": "0.9", "stars_sal_gaps": "2", "stars_sal_unexplained": "1", "stars_sal_abs": "3", "stars_min_rank": "0.5", "stars_top5_hit": "0.5",
         "own_rank": "0.9", "sal_gaps": "5", "sal_unexplained": "2", "min_rank": "0.9", "min_top5": "3"}]
p = E.proj_band_pooled(rows)
check("pooled rotation: own rank mean +0.60 over 2 slates, gaps 4 of 40 (10%; 1 unexplained), |gap| 4.0, minutes +0.50, top-5 hit 0.70",
      p[0].startswith("ROTATION 10-25: own rank +0.60 (+0.50 to +0.70, 2 slates); salary gaps 4 of 40 (10%; 1 unexplained), mean |gap| 4.0; minutes rank +0.50 (+0.40 to +0.60, 2 slates); top-5 hit 0.70"), p[0])
check("pooled stars: a slate without the lens is left out of its mean", p[1].startswith("STARS 25+: own rank +0.90 (+0.90 to +0.90, 1 slates); salary gaps 2 of 10 (20%; 1 unexplained)"), p[1])
check("secondary all-player line", p[2].startswith("secondary, all players: own rank +0.85") and "salary gaps 7 (3 unexplained)" in p[2] and "top-5 match 3.50 of 5" in p[2], p[2])
check("label prefix", E.proj_band_pooled(rows, "week")[0].startswith("week, ROTATION 10-25"))
t = E.proj_band_text(rows[0])
check("per-slate text: both bands, a missing lens as a dash", "ROTATION 10-25 10 players: own rank +0.50" in t and "STARS 25+ 4 players: own rank –" in t, t)
# the backfill: every graded slate has the band columns, and the band's player count matches its slate file
pa = list(csv.DictReader(open(E.PROJ_AUDIT)))
graded = [f for f in sorted(glob.glob(os.path.join(E.DK, "20??-??-??_*.csv"))) if any(r.get("actual_dk") not in ("", None) for r in csv.DictReader(open(f)))]
check("proj_audit.csv: a row per graded slate, every band column present", len(pa) == len(graded) and all(all(c in r for c in cols) for r in pa), (len(pa), len(graded)))
cnt_ok = True
for f in graded:
    rs = list(csv.DictReader(open(f)))
    g = str(rs[0]["draft_group"]); r0 = next(r for r in pa if str(r["draft_group"]) == g)
    n = sum(1 for r in rs if r.get("status") != "Out" and 10 <= (E.num(r.get("fp_dk")) or 0) < 25)
    cnt_ok &= int(r0["rot_n"]) == n
check("rot_n = the slate's live players projected 10-25", cnt_ok)
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
