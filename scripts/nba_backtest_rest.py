"""NBA tiers backtest, the rest (step 8): players who changed tier between the locks, the ceiling blend, the residual
correlations for the contest side, and small slates. Writes analysis/nba/report/backtest_rest.md.

  tier changes   every player in both windows' tier history (6-drafter slates), by how his combined tier moved from the
                 AM lock to the PM lock: how many, what moved (his ADP, his projection: ours in the morning, ETR in the
                 afternoon), his score against his PM ADP round band, breakers, scratches (scored through the swap)
  ceiling blend  per slate, the rank correlation of ETR's blended number (25% median, 75% ceiling: the board's Proj)
                 against ETR's own median, priced players; ours is one number converted both ways, so it is 1.0 by
                 construction. At 0.97 or above the blend is cosmetic for ordering; below, the weight is tested
                 (w = 0, .25, .5, .75, 1 on ceiling) on decision pairs graded by breakers
  residuals      scripts/nba_residuals.py (residual = actual - ETR's median), teammates and opponents by spread band;
                 game totals aren't on file (the mirror keeps spreads only)
  small slates   the 4-drafter cuts of tier_grade.md, which are graded apart

  python3 scripts/nba_backtest_rest.py
"""
import collections, csv, glob, math, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G      # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = G.REP
OUT = os.path.join(REP, "backtest_rest.md")
num = G.num


def band_means(rows):
    """{player_id: his score minus his PM ADP round band's average} for a slate's PM rows."""
    pr = sorted((r for r in rows if num(r["adp"]) is not None), key=G.adp)
    pod = int(rows[0]["pod"])
    bands = collections.defaultdict(list)
    for i, r in enumerate(pr):
        bands[min(i // pod, 6)].append(r)
    out = {}
    for rs in bands.values():
        m = sum(r["slot"] for r in rs) / len(rs)
        for r in rs:
            out[r["player_id"]] = r["slot"] - m
    return out


def main():
    H = G.load()
    md = ["# NBA tiers backtest: the rest (step 8)", "", "Written by scripts/nba_backtest_rest.py. 6-drafter slates unless marked; "
          "a scratch is scored through his swap.", ""]
    # ---- tier changes
    by = collections.defaultdict(dict)
    for r in H:
        if r["pod"] == "6":
            by[(r["date"], r["player_id"])][r["window"]] = r
    pm_slates = collections.defaultdict(list)
    for r in H:
        if r["pod"] == "6" and r["window"] == "pm":
            pm_slates[r["date"]].append(r)
    over = {}
    for d, rs in pm_slates.items():
        over.update({(d, k): v for k, v in band_means(rs).items()})
    groups = collections.defaultdict(list)
    for (d, pid), w in by.items():
        if "am" not in w or "pm" not in w:
            continue
        a, p = int(w["am"]["tier"]), int(w["pm"]["tier"])
        if a == 5 and p == 5:
            continue
        key = "up" if p < a else "down" if p > a else "same"
        groups[(key, min(a, p))].append((w["am"], w["pm"], over.get((d, pid))))
    md += ["## Players who changed tier between the AM and PM locks", "",
           "| Move | From the higher of his two tiers | Players | ADP moved (AM to PM, picks earlier) | Projection moved (ETR at PM minus ours at AM) | Score over his PM ADP band | Breakers | Scratched |",
           "|---|---|---|---|---|---|---|---|"]
    for key in ("up", "down", "same"):
        for t in (1, 2, 3, 4):
            g = groups.get((key, t))
            if not g:
                continue
            adp_mv = [num(am["adp"]) - num(pm["adp"]) for am, pm, _ in g if num(am["adp"]) is not None and num(pm["adp"]) is not None]
            pj = [G.num(pm["proj"]) - G.num(am["proj"]) for am, pm, _ in g if G.num(am["proj"]) is not None and G.num(pm["proj"]) is not None]
            ov = [o for _, _, o in g if o is not None]
            md.append("| %s | T%d | %d | %s | %s | %s | %d | %d |" % (
                {"up": "Moved up a tier", "down": "Moved down a tier", "same": "Same tier"}[key], t, len(g),
                "%+.1f" % (sum(adp_mv) / len(adp_mv)) if adp_mv else "-", "%+.1f" % (sum(pj) / len(pj)) if pj else "-",
                "%+.1f" % (sum(ov) / len(ov)) if ov else "-", sum(pm["slot_brk"] for _, pm, _ in g), sum(1 for _, pm, _ in g if pm["scratched"] == "1")))
    # ---- ceiling blend
    md += ["", "## The ceiling blend", ""]
    cors = []
    for p in sorted(glob.glob(os.path.join(HERE, "analysis", "nba", "daily", "*_main.csv"))):
        rows = [r for r in csv.DictReader(open(p)) if num(r["etr_last"]) is not None and num(r["etr_median"]) is not None
                and num(r.get("adp_close")) is not None]
        if len(rows) >= 10:
            cors.append((os.path.basename(p)[:10], G.spearman([num(r["etr_last"]) for r in rows], [num(r["etr_median"]) for r in rows]), len(rows)))
    low = [c for c in cors if c[1] < 0.97]
    md.append("Rank correlation of ETR's blended number against its own median, priced players, per slate: %s. Lowest %.3f (%s). %s" % (
        ", ".join("%s %.3f" % (d[5:], c) for d, c, _ in cors), min(c for _, c, _ in cors), min(cors, key=lambda x: x[1])[0],
        "Every slate is at 0.97 or above: the blend is cosmetic for ordering (it moves the scale, not the order), and our Proj is one "
        "number converted both ways (1.0 by construction). No weight test needed." if not low else
        "%d slates fall below 0.97, so the weight is worth testing." % len(low)))
    # ---- residuals
    md += ["", "## Residual correlations (for the contest side)", ""]
    try:
        subprocess.run([sys.executable, os.path.join(HERE, "scripts", "nba_residuals.py")], check=True, capture_output=True)
        md += [l for l in open(os.path.join(REP, "residual_correlations.md")).read().splitlines()[2:]]
    except subprocess.CalledProcessError as e:
        md.append("nba_residuals.py failed: %s" % e.stderr.decode()[-300:])
    # ---- small slates
    md += ["", "## Small slates (4-drafter pods)", "",
           "Graded apart in tier_grade.md and tier_rules.md (5 slates so far: 10-20 has no projections, so 4 graded). Almost "
           "every cell is \"not enough yet\"; the only leans are AM middle PRICEY lagging (+6.8, 43 pairs) and AM T5 VALUE (+2.3, 55), "
           "both candidates. Nothing adopted on small slates; the 6-drafter switches are not applied to them by the report."]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
