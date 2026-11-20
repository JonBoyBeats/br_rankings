"""A2 candidate, 2026-11-20, this season's check: an Out player projected 15-20 minutes (2+ games) handed off like an
Out regular (battle-royale-research cbb_nightly: OUT_SHARE of his minutes by m x (40 - m), OUT_POS_OTHER outside his
position group), then the fit to 200 (fit_minutes), against the projection as it stood (the fit alone). Each graded
slate's teams with such an Out; graded on his teammates: minutes MAE and DraftKings points MAE (points move with
minutes). The threshold, 15, is what 2025-26's halves chose (scripts/cbb_outhand_study.py there).

  python3 scripts/dk_outhand_study.py --brr ../battle-royale-research
"""
import argparse, csv, glob, os, statistics as S, sys

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
num = lambda v: float(v) if v not in ("", None) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brr", required=True)
    ap.add_argument("--lo", type=float, default=15)
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import cbb_nightly as nt
    grp = lambda r: "G" if str(r.get("position") or "").startswith("G") else "B"
    allm, alld = [[], []], [[], []]
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = list(csv.DictReader(open(f)))
        if not rows or not any(r.get("actual_dk") for r in rows):
            continue
        for t in sorted({r["team"] for r in rows}):
            rs = [r for r in rows if r["team"] == t]
            sat = [r for r in rs if r["status"] == "Out" and num(r["min_proj"]) and a.lo <= num(r["min_proj"]) < nt.OUT_REG_MIN and num(r.get("min_avg"))]
            live = [r for r in rs if r["status"] != "Out" and num(r["min_proj"])]
            if not sat or len(live) < 5:
                continue
            m0 = [num(r["min_proj"]) for r in live]
            freed, groups = nt.OUT_SHARE * sum(num(r["min_proj"]) for r in sat), {grp(r) for r in sat}
            w = [m * max(1.0, 40 - m) * (1.0 if grp(r) in groups else nt.OUT_POS_OTHER) for r, m in zip(live, m0)]
            m1 = nt.fit_minutes([min(40.0, m + freed * wi / sum(w)) for m, wi in zip(m0, w)])
            act = lambda r: num(r.get("min")) or 0
            pts = lambda r, m, b: (num(r["fp_dk"]) or 0) * (m / b if b else 1)
            em = [[abs(act(r) - b) for r, b in zip(live, m0)], [abs(act(r) - m) for r, m in zip(live, m1)]]
            ed = [[abs((num(r["actual_dk"]) or 0) - pts(r, b, b)) for r, b in zip(live, m0)], [abs((num(r["actual_dk"]) or 0) - pts(r, m, b)) for r, m, b in zip(live, m1, m0)]]
            for k in (0, 1):
                allm[k] += em[k]; alld[k] += ed[k]
            print("%s %s without %s: teammates' minutes MAE %.3f -> %.3f, DK points %.3f -> %.3f; starters' minutes %s" % (
                rows[0]["date"], t, ", ".join("%s (%.1f)" % (r["name"], num(r["min_proj"])) for r in sat), S.mean(em[0]), S.mean(em[1]), S.mean(ed[0]), S.mean(ed[1]),
                ", ".join("%s %.0f->%.0f (played %.0f)" % (r["name"].split()[-1], b, m, act(r)) for r, b, m in zip(live, m0, m1) if b >= 25)))
    if allm[0]:
        print("All: teammates' minutes MAE %.3f -> %.3f, DK points %.3f -> %.3f (%d teammate-nights)" % (S.mean(allm[0]), S.mean(allm[1]), S.mean(alld[0]), S.mean(alld[1]), len(allm[0])))


if __name__ == "__main__":
    main()
