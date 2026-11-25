"""Tests for scripts/dk_proj_grade.py (the projection grade by band): python3 tests/dk_proj_grade.py"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_proj_grade as G

ok = bad = 0


def check(name, cond, info=""):
    global ok, bad
    if cond:
        ok += 1; print("PASS " + name)
    else:
        bad += 1; print("FAIL " + name + " " + str(info))


def row(fp, act, mp=None, m=None, own=0.0, sal=5000, did="1", name="x", own_raw=None):
    r = {"fp_dk": str(fp), "actual_dk": "" if act is None else str(act), "min_proj": "" if mp is None else str(mp), "min": "" if m is None else str(m),
         "own": str(own), "salary": str(sal), "dk_id": did, "name": name, "team": "T"}
    if own_raw is not None:
        r["own_raw"] = str(own_raw)
    return r


# graded: projected > 0 and a real score
rs = [row(0, 5), row(12, None), row(12, 20), row(30, 10)]
check("graded keeps projected > 0 with a score", [r["fp_dk"] for r in G.graded(rs)] == ["12", "30"])
# stats by hand: errors +8 and -20; MAE 14, bias -6, off by 10+ 1 of 2; minutes |30-25| = 5 (the second has none)
st = G.stats([row(12, 20, 25, 30), row(30, 10)])
check("stats: MAE, bias (actual - ours), off 10+, minutes MAE", st["n"] == 2 and st["mae"] == 14 and st["bias"] == -6 and st["off"] == 0.5 and st["min_mae"] == 5, st)
check("off by 10+ counts exactly 10", G.stats([row(10, 20)])["off"] == 1.0 and G.stats([row(10, 19.9)])["off"] == 0.0)
# band edges: 10 is ROTATION, 25 is STARS, 9.99 is under 10
g = [row(9.99, 9), row(10, 10), row(24.9, 25), row(25, 25), row(40, 40)]
check("band edges: rotation [10, 25), stars [25, inf)", [r["fp_dk"] for r in G.band(g, *G.ROTATION)] == ["10", "24.9"] and [r["fp_dk"] for r in G.band(g, *G.STARS)] == ["25", "40"]
      and [r["fp_dk"] for r in G.band(g, 0, G.LOW)] == ["9.99"])
# headline per slate and pooled
sl = [("2026-01-01_1", [row(12, 22), row(30, 30), row(5, 5)]), ("2026-01-02_2", [row(15, 5), row(26, 36)])]
h = G.headline(sl)
rot, stars, low, allp = h["pooled"]
check("headline pooled: rotation (+10, -10), stars (0, +10), under 10 one", rot["n"] == 2 and rot["mae"] == 10 and rot["bias"] == 0 and stars["n"] == 2 and stars["bias"] == 5 and low["n"] == 1 and allp["n"] == 5)
check("headline per slate", h["per"][0][1]["bias"] == 10 and h["per"][1][1]["bias"] == -10 and h["per"][1][3] is None)
# ownership crossover: own_raw wins over own; the 5-15% band's per-slate bias
sl2 = [("a", [row(12, 16, own=20, own_raw=10), row(12, 12, own=3)]), ("b", [row(12, 10, own=7)])]
c = G.crossover(sl2)
mid = dict(c["pooled"])["5-15%"]
check("crossover reads own_raw where present", c["src"] == "own_raw" and mid["n"] == 2 and dict(c["pooled"])["15%+"] is None)
check("5-15% band per-slate bias: +4 and -2, one positive", [round(st["bias"], 6) for _, st in c["mid_per"]] == [4, -2] and c["mid_pos"] == 1 and c["mid_mean"] == 1)
# base tags: BASE in the tag or the idea name; Draw the 9 cells only L0 U0; not "baseline"
doc = {"tags": [["x L0 U0"], ["x L0.1 U0"], ["baseline idea"], ["mine"], ["y"]], "groups": {"x L0 U0": "BASE", "x L0.1 U0": "BASE", "y": "my base"}}
check("base tags: L0 U0 of a BASE idea, a tag in an idea named base; not baseline, not other cells", G.base_tags(doc) == {"x L0 U0", "y"}, G.base_tags(doc))
# fine bands cover every projection once
fs = G.FINE
check("fine bands tile [0, inf)", fs[0][0] == 0 and all(fs[i][1] == fs[i + 1][0] for i in range(len(fs) - 1)) and fs[-1][1] == math.inf)
# missed ceilings: 5x salary in thousands, with the real data (12+ slates, 147+ hits; each hit at 5x)
ce = G.ceilings(G.slates())
hits = [h for x in ce for h in x[2]]
check("missed ceilings: every hit is 5x salary", hits and all(h[3] >= 5 * h[2] / 1000 for h in hits))
print("%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
