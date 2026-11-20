"""A2 test (d), 2026-11-20: players with no recent games (no last 5 on file: newcomers, back from absence) projected
above the salary line. The change: such a player's points move k of the way from our projection to the slate's
salary line (fp_dk on salary, least squares over the players not Out, as A1), k chosen on the other slates (grid 0..1
by 0.05), judged on the held-out one. Minutes unchanged (the rate is what moves).

Measured among the flagged players who played (minutes > 0; DNPs, mostly Questionable players who sat, counted apart so
the test is about how much they score when they play): points MAE and bias. Also every player's points MAE, their
minutes (projected vs real, when they played) and the salary lens (2 sd gaps, unexplained as A1).

  python3 scripts/dk_newcomer_study.py
"""
import csv, glob, os, statistics as S
from collections import defaultdict

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
GRID = [round(0.05 * i, 2) for i in range(21)]
num = lambda v: float(v) if v not in ("", None) else None


def slates():
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = list(csv.DictReader(open(f)))
        if rows and any(r.get("actual_dk") not in ("", None) for r in rows):
            out.append(rows)
    return out


def prep(rows):
    live = [r for r in rows if r.get("status") != "Out" and (num(r.get("fp_dk")) or 0) > 0]
    xs, ys = [num(r["salary"]) for r in live], [num(r["fp_dk"]) for r in live]
    mx, my = S.mean(xs), S.mean(ys); b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a = my - b * mx
    for r in live:
        r["_line"] = a + b * num(r["salary"])
        r["_flag"] = num(r.get("dk_last5")) is None and num(r["fp_dk"]) > r["_line"]
    return live


def lens(live, k):
    fp = {r["dk_id"]: num(r["fp_dk"]) - (k * (num(r["fp_dk"]) - r["_line"]) if r["_flag"] else 0) for r in live}
    act = lambda r: num(r.get("actual_dk")) or 0
    fl = [r for r in live if r["_flag"]]
    played = [r for r in fl if (num(r.get("min")) or 0) > 0]
    res = [fp[r["dk_id"]] - r["_line"] for r in live]; sd = S.pstdev(res)
    outT = {r["team"] for r in live if False}
    gaps = [r for r, e in zip(live, res) if abs(e) >= 2 * sd]
    return {"flag": len(fl), "played": len(played), "dnp": len(fl) - len(played),
            "mae_played": S.mean(abs(act(r) - fp[r["dk_id"]]) for r in played) if played else None,
            "bias_played": S.mean(act(r) - fp[r["dk_id"]] for r in played) if played else None,
            "mae_all": S.mean(abs(act(r) - fp[r["dk_id"]]) for r in live),
            "min_played": S.mean((num(r.get("min")) or 0) - (num(r.get("min_proj")) or 0) for r in played) if played else None,
            "gaps": len(gaps), "gaps_flag": sum(1 for r in gaps if r["_flag"])}


def main():
    sl = [prep(r) for r in slates()]
    names = ["%s_%s" % (r[0]["date"], r[0]["draft_group"]) for r in sl]
    L = {(i, k): lens(s, k) for i, s in enumerate(sl) for k in GRID}
    f = lambda x, d=2: "-" if x is None else ("%." + str(d) + "f") % x
    better = worse_all = 0
    print("Held out by slate (k chosen on the others, on the flagged players who played):")
    for i in range(len(sl)):
        k = min(GRID, key=lambda x: sum(L[(j, x)]["mae_played"] * L[(j, x)]["played"] for j in range(len(sl)) if j != i and L[(j, x)]["played"]))
        b, a = L[(i, 0.0)], L[(i, k)]
        if b["played"]:
            better += a["mae_played"] < b["mae_played"] - 1e-9
        worse_all += a["mae_all"] > b["mae_all"] + 1e-9
        print("  %s k %.2f: flagged %d (played %d, DNP %d); their points MAE %s -> %s, bias %s -> %s, minutes real-proj %s; all players %s -> %s; 2 sd gaps %d (%d flagged) -> %d (%d)" % (
            names[i], k, b["flag"], b["played"], b["dnp"], f(b["mae_played"]), f(a["mae_played"]), f(b["bias_played"]), f(a["bias_played"]), f(b["min_played"], 1),
            f(b["mae_all"], 3), f(a["mae_all"], 3), b["gaps"], b["gaps_flag"], a["gaps"], a["gaps_flag"]))
    print("Their points MAE better on %d of %d held-out slates with a flagged player who played; all-player MAE worse on %d" % (
        better, sum(1 for i in range(len(sl)) if L[(i, 0.0)]["played"]), worse_all))
    tot = lambda k, key: sum(L[(i, k)][key] * L[(i, k)]["played"] for i in range(len(sl)) if L[(i, k)]["played"]) / sum(L[(i, k)]["played"] for i in range(len(sl)))
    print("Pooled (flagged who played): " + "; ".join("k %.2f MAE %.2f bias %+.2f" % (k, tot(k, "mae_played"), tot(k, "bias_played")) for k in GRID[::2]))


if __name__ == "__main__":
    main()
