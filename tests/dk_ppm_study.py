"""Checks for scripts/dk_ppm_study.py: DraftKings scoring, the miss split, the opponent factor, the double-double chance."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import dk_ppm_study as M

ok = fail = 0


def check(name, cond, info=""):
    global ok, fail
    if cond:
        ok += 1
        print("PASS", name)
    else:
        fail += 1
        print("FAIL", name, info)


s = {"pts": 20, "tpm": 2, "reb": 8, "ast": 4, "stl": 1, "blk": 1, "to": 2}
check("DraftKings scoring: 20 + 1 + 10 + 6 + 2 + 2 - 1 = 40", abs(M.dkpts(s) - 40.0) < 1e-9, M.dkpts(s))
x = {"games": [(30.0, dict(s), 25.0)], "band_rate": {c: 0.2 for c in M.CATS}, "miya": None, "carry": None,
     "opp_al": {c: 10.0 for c in M.CATS}, "opp_ex": {c: 10.0 for c in M.CATS}, "L": {c: 5.0 for c in M.CATS}}
r = M.ppm_rates(x, {"base": {"pm": 0.0001}})
check("clean base with no prior is his own rate", abs(r["pts"] - 20 / 30) < 1e-4, r["pts"])
check("an opponent that allows exactly what its opponents produce is a factor 1", abs(M.opp_factor(x, M.OPP_CATS, 3, 1.0) - 1) < 1e-9)
x2 = dict(x, opp_al={c: 15.0 for c in M.CATS})
check("an opponent that allows more is a factor over 1", M.opp_factor(x2, ("pts",), 3, 1.0) > 1)
table = [(0.02, 0.0084), (0.05, 0.0763), (1.01, 0.6429)]
check("no minutes, no double-double", M.dd_chance({"pts": 1, "reb": 1, "ast": 1}, 0, table) == 0.0)
sp, used = M.decompose()
check("the miss split sums to 1 in each band", all(abs(v["minutes"] + v["per_minute"] - 1) < 1e-9 for v in sp.values()) and used > 0)
print("%d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
