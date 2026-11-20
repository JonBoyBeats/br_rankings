"""A2 test (c), 2026-11-20: the Vegas slope. Our team totals move with the line less than real DraftKings points do
(A1: pooled 2.32 vs 2.47 a point of implied total). The projection's only line term on points is battle-royale-
research cbb_nightly.implied_factor: points per minute x (1 + PPM_PER_IMPLIED x x), x = his team's implied total
(o/u / 2 - spread / 2) minus its points per game last season (cbb/team_strength_2025-26.json), capped at REL_CAP
either way. The change tested: PPM_PER_IMPLIED x lam, i.e. each player's points x (1 + lam p x) / (1 + p x), his
minutes unchanged. lam is chosen on the other slates (grid 0.5..3.0), judged on the held-out one.

Lens (the measure): the mean |real - projected| of a team's summed DraftKings points (players not tagged Out), with
the pooled slope beside it. Also the player points MAE. The team's espn id comes from the mirror's slate file as it
stood before lock.

  python3 scripts/dk_vegas_study.py --mirror ../br-adp-mirror --brr ../battle-royale-research
"""
import argparse, csv, datetime as dt, glob, json, os, statistics as S, sys

sys.path.insert(0, os.path.dirname(__file__))
from nba_daily import Mirror, iso  # noqa: E402

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
P, CAP = 0.01231, 15
GRID = [round(0.25 * i, 2) for i in range(2, 13)]
num = lambda v: float(v) if v not in ("", None) else None


def at_lock(m, d, g):
    day = iso(d + "T00:00:00Z")
    start = None
    for t, sha in reversed(m.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))):
        sl = next((s for s in m.show(sha, "dk_cbb_morning.json").get("slates", []) if str(s["draft_group_id"]) == g), None)
        if sl and start is None:
            start = iso(sl["start"])
        if sl and start and t < start:
            return sl
    return None


def load(m, usual):
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = list(csv.DictReader(open(f)))
        if not rows or not any(r.get("actual_dk") not in ("", None) for r in rows):
            continue
        sl = at_lock(m, rows[0]["date"], rows[0]["draft_group"]) or {}
        et = {k: (p.get("espn_team")) for k, p in (sl.get("players") or {}).items()}
        for r in rows:
            u = usual.get(str(et.get(r["dk_id"])))
            ou, sp = num(r.get("ou")), num(r.get("spread"))
            r["_x"] = max(-CAP, min(CAP, ou / 2 - sp / 2 - u)) if (u is not None and ou and sp is not None) else None
            r["_imp"] = ou / 2 - sp / 2 if ou and sp is not None else None
        out.append(rows)
    return out


def lens(rows, lam):
    teams = {}
    pm = []
    for r in rows:
        if r.get("status") == "Out" or num(r.get("fp_dk")) is None:
            continue
        x = r["_x"]
        f = (1 + lam * P * x) / (1 + P * x) if x is not None else 1.0
        fp = num(r["fp_dk"]) * f
        a = num(r.get("actual_dk")) or 0
        pm.append(abs(a - fp))
        t = teams.setdefault(r["team"], [0.0, 0.0, r["_imp"]])
        t[0] += fp
        t[1] += a
    tm = [abs(v[1] - v[0]) for v in teams.values()]
    return S.mean(tm), S.mean(pm), [(v[2], v[0], v[1]) for v in teams.values() if v[2] is not None]


def slope(pts, k):
    xs = [p[0] for p in pts]; ys = [p[k] for p in pts]
    mx, my = S.mean(xs), S.mean(ys); sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True)
    ap.add_argument("--brr", required=True)
    a = ap.parse_args()
    usual = json.load(open(os.path.join(a.brr, "cbb", "team_strength_2025-26.json")))["points"]
    sl = load(Mirror(a.mirror), usual)
    names = ["%s_%s" % (r[0]["date"], r[0]["draft_group"]) for r in sl]
    cover = [sum(r["_x"] is not None for r in rows if r.get("status") != "Out") / max(1, sum(r.get("status") != "Out" for r in rows)) for rows in sl]
    L = {(i, l): lens(rows, l) for i, rows in enumerate(sl) for l in GRID}
    better_t = better_p = 0
    print("Held out by slate (lam chosen on the others): team-sum MAE, player points MAE")
    for i in range(len(sl)):
        l = min(GRID, key=lambda x: sum(L[(j, x)][0] for j in range(len(sl)) if j != i))
        b, t = L[(i, 1.0)], L[(i, l)]
        better_t += t[0] < b[0] - 1e-9; better_p += t[1] < b[1] - 1e-9
        print("  %s (line term on %.0f%% of players) lam %.2f: team %.2f -> %.2f; players %.3f -> %.3f" % (names[i], 100 * cover[i], l, b[0], t[0], b[1], t[1]))
    print("Team-sum MAE better on %d of %d held out; player points MAE better on %d" % (better_t, len(sl), better_p))
    for l in GRID:
        pts = [p for i in range(len(sl)) for p in L[(i, l)][2]]
        print("  lam %.2f: team MAE %.2f, players %.3f, pooled slope ours %.2f vs real %.2f (%d teams)" % (
            l, S.mean(L[(i, l)][0] for i in range(len(sl))), S.mean(L[(i, l)][1] for i in range(len(sl))), slope(pts, 1), slope(pts, 2), len(pts)))


if __name__ == "__main__":
    main()
