"""A2 test (a), 2026-11-20: steeper minutes at the top of the rotation, under the A2 rule (one change; adopted only if
it improves its lens on most slates with each slate held out of the fit, and no other lens gets noticeably worse).

The change: after the nightly's fit to 200 (battle-royale-research cbb_nightly.team_minutes), each team's projected
minutes m become m^(1+g), refit to the same team total (scaled, no one over 40), and points move with minutes
(points per minute held). g is chosen on the other slates (grid 0..0.60 by 0.02), applied to the held-out one.

Minutes lens (the measure): mean |actual - projected| minutes over the players not tagged Out, blowout teams (20+
margin) and news scratches (projected 15+, played 0) left out, as A1. Other lenses on the same slate: DraftKings
points MAE (everyone not Out), the shape (top-2 share of a team's projected points vs his last-5 shares, A1), the
Vegas slope (team sums on implied totals) and the salary gaps (2 sd, unexplained).

  python3 scripts/dk_minutes_steep_study.py [--fixed G]
"""
import csv, glob, math, os, statistics as S
from collections import defaultdict

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
GRID = [round(0.02 * i, 2) for i in range(31)]
num = lambda v: float(v) if v not in ("", None) else None


def slates():
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = list(csv.DictReader(open(f)))
        if rows and any(r.get("actual_dk") not in ("", None) for r in rows):
            out.append(rows)
    return out


def steepen(rows, g):
    """{dk_id: (minutes, points)} under exponent g, per team, the team total kept, 40 at most."""
    t = defaultdict(list)
    for r in rows:
        if r.get("status") != "Out" and num(r.get("min_proj")):
            t[r["team"]].append(r)
    out = {}
    for v in t.values():
        m0 = [num(r["min_proj"]) for r in v]
        tot = sum(m0)
        m = [x ** (1 + g) for x in m0]
        k = tot / sum(m) if sum(m) else 1.0
        m = [min(40.0, x * k) for x in m]
        for _ in range(20):                    # scale to the total, hold the 40 cap
            free = [i for i, x in enumerate(m) if x < 40 - 1e-9]
            gap = tot - sum(m)
            if abs(gap) < 1e-6 or not free:
                break
            s = sum(m[i] for i in free)
            m = [min(40.0, x * (1 + gap / s)) if i in free else x for i, x in enumerate(m)]
        for r, a, b in zip(v, m0, m):
            out[r["dk_id"]] = (b, (num(r.get("fp_dk")) or 0) * (b / a if a else 1))
    return out


def lenses(rows, g):
    st = steepen(rows, g)
    teams = defaultdict(list)
    for r in rows:
        teams[r["team"]].append(r)
    score = {t: sum(num(r.get("pts")) or 0 for r in rs) for t, rs in teams.items()}
    opp = {}
    for r in rows:
        two = (r.get("game") or "").split("@")
        if len(two) == 2:
            opp[r["team"]] = two[1] if r["team"] == two[0] else two[0]
    blow = {t for t in teams if t in opp and opp[t] in score and abs(score[t] - score[opp[t]]) >= 20}
    live = [r for r in rows if r["dk_id"] in st]
    act = lambda r: num(r.get("min")) or 0
    mm = [abs(act(r) - st[r["dk_id"]][0]) for r in live if r["team"] not in blow and not (num(r["min_proj"]) >= 15 and not act(r))]
    pm = [abs((num(r.get("actual_dk")) or 0) - st[r["dk_id"]][1]) for r in live]
    # shape: top-2 share of projected points, ours vs last-5 (A1's shape_rows)
    sh = []
    for t, rs in teams.items():
        lv = [r for r in rs if r["dk_id"] in st and num(r.get("dk_last5")) is not None and st[r["dk_id"]][1] > 0]
        if len(lv) >= 5:
            po, pr = sum(st[r["dk_id"]][1] for r in lv), sum(num(r["dk_last5"]) for r in lv)
            sh.append(sum(sorted((st[r["dk_id"]][1] / po for r in lv), reverse=True)[:2]) - sum(sorted((num(r["dk_last5"]) / pr for r in lv), reverse=True)[:2]))
    # Vegas slope
    vx, vy = [], []
    for t, rs in teams.items():
        r0 = next((r for r in rs if num(r.get("ou")) and num(r.get("spread")) is not None), None)
        if r0:
            vx.append(num(r0["ou"]) / 2 - num(r0["spread"]) / 2); vy.append(sum(st[r["dk_id"]][1] for r in rs if r["dk_id"] in st))
    slope = None
    if len(vx) >= 3:
        mx, my = S.mean(vx), S.mean(vy); sxx = sum((x - mx) ** 2 for x in vx)
        slope = sum((x - mx) * (y - my) for x, y in zip(vx, vy)) / sxx if sxx else None
    # salary gaps (2 sd), unexplained (A1's reasons)
    sal = [r for r in live if st[r["dk_id"]][1] > 0]
    unexp = gaps = 0
    if len(sal) >= 10:
        xs, ys = [num(r["salary"]) for r in sal], [st[r["dk_id"]][1] for r in sal]
        mx, my = S.mean(xs), S.mean(ys); b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); a = my - b * mx
        res = [y - (a + b * x) for x, y in zip(xs, ys)]; sd = S.pstdev(res)
        outT = {t for t, rs in teams.items() if any(r.get("status") == "Out" and (num(r.get("min_avg")) or 0) >= 20 for r in rs)}
        for r, e in zip(sal, res):
            if abs(e) >= 2 * sd:
                gaps += 1
                why = r.get("status") or r["team"] in outT or (num(r.get("min_avg")) is not None and abs(st[r["dk_id"]][0] - num(r["min_avg"])) >= 5) or r.get("missed") or r.get("src") != "box" or num(r.get("dk_last5")) is None
                unexp += not why
    return {"min_mae": S.mean(mm), "pts_mae": S.mean(pm), "shape_top2_vs_recent": S.mean(sh) if sh else None, "vegas_slope": slope, "gaps": gaps, "unexplained": unexp}


def fixed(sl, names, g):
    """Each slate at one fixed g (e.g. the one 2025-26's halves both choose): every lens, before -> after."""
    fmt = lambda x: "-" if x is None else "%.3f" % x
    rs = [(n, lenses(rows, 0.0), lenses(rows, g)) for n, rows in zip(names, sl)]
    print("At g %.2f on every slate:" % g)
    for n, b, a in rs:
        print("  %s: minutes %s -> %s; points %s -> %s; shape %s -> %s; Vegas %s -> %s; gaps %d/%d -> %d/%d" % (
            n, fmt(b["min_mae"]), fmt(a["min_mae"]), fmt(b["pts_mae"]), fmt(a["pts_mae"]), fmt(b["shape_top2_vs_recent"]), fmt(a["shape_top2_vs_recent"]),
            fmt(b["vegas_slope"]), fmt(a["vegas_slope"]), b["unexplained"], b["gaps"], a["unexplained"], a["gaps"]))
    k = lambda key, f: sum(f(a[key], b[key]) for _, b, a in rs if a[key] is not None and b[key] is not None)
    print("  minutes better on %d of %d, points better on %d; |shape| larger on %d of %d; unexplained gaps %d -> %d of %d -> %d" % (
        k("min_mae", lambda x, y: x < y), len(rs), k("pts_mae", lambda x, y: x < y), k("shape_top2_vs_recent", lambda x, y: abs(x) > abs(y)),
        sum(1 for _, b, a in rs if a["shape_top2_vs_recent"] is not None), sum(b["unexplained"] for _, b, _ in rs), sum(a["unexplained"] for _, _, a in rs),
        sum(b["gaps"] for _, b, _ in rs), sum(a["gaps"] for _, _, a in rs)))


def main():
    sl = slates()
    import sys
    if "--fixed" in sys.argv:
        fixed(sl, ["%s_%s" % (r[0]["date"], r[0]["draft_group"]) for r in sl], float(sys.argv[sys.argv.index("--fixed") + 1]))
        return
    names = ["%s_%s" % (r[0]["date"], r[0]["draft_group"]) for r in sl]
    L = {(i, g): lenses(rows, g) for i, rows in enumerate(sl) for g in GRID}
    better, out = 0, []
    for i in range(len(sl)):
        tot = lambda g: sum(L[(j, g)]["min_mae"] for j in range(len(sl)) if j != i)
        g = min(GRID, key=tot)
        b, a = L[(i, 0.0)], L[(i, g)]
        better += a["min_mae"] < b["min_mae"] - 1e-9
        out.append((names[i], g, b, a))
    fmt = lambda x: "-" if x is None else "%.3f" % x
    print("Held out by slate (g chosen on the others): minutes MAE, points MAE, shape top-2 ours-recent, Vegas slope, salary gaps unexplained/all")
    for n, g, b, a in out:
        print("  %s g %.2f: minutes %s -> %s; points %s -> %s; shape %s -> %s; Vegas %s -> %s; gaps %d/%d -> %d/%d" % (
            n, g, fmt(b["min_mae"]), fmt(a["min_mae"]), fmt(b["pts_mae"]), fmt(a["pts_mae"]), fmt(b["shape_top2_vs_recent"]), fmt(a["shape_top2_vs_recent"]),
            fmt(b["vegas_slope"]), fmt(a["vegas_slope"]), b["unexplained"], b["gaps"], a["unexplained"], a["gaps"]))
    print("Minutes lens better on %d of %d held-out slates" % (better, len(sl)))
    print("Whole-sample curve (minutes MAE, points MAE summed over slates): " + "; ".join(
        "%.2f: %.3f / %.3f" % (g, S.mean(L[(i, g)]["min_mae"] for i in range(len(sl))), S.mean(L[(i, g)]["pts_mae"] for i in range(len(sl)))) for g in GRID))


if __name__ == "__main__":
    main()
