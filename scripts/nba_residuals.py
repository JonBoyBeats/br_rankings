"""NBA residual correlations: when one player beats his projection, do his teammates and opponents too?

Residual = actual - ETR's median (the market's number), for every rotation player in every game on file
(analysis/nba/daily/*_box.csv, main slate or not). For pairs of players in the same game, the correlation of
their residuals, by relationship:

  teammates   star + star, star + role, role + role, and same position group (G, F, C)
  opponents   star + star across the game, and everyone across it
  by spread   each of the above by the game's spread: close (4.5 or less), mid (5-9.5), big (10+)

A star is one of his team's top two by ETR's median that night; everyone else is a role player. Each pair
counts once in each order, so the correlation is symmetric. The 80% range comes from resampling nights.
Game totals aren't on file yet (the mirror keeps spreads only), so there's no split by total.

For the contest work (stacking, correlation in a best-ball roster). Writes
analysis/nba/report/residual_correlations.md and prints it.

  python3 scripts/nba_residuals.py
"""
import csv, glob, os, random
from collections import defaultdict

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(HERE, "analysis", "nba", "report", "residual_correlations.md")
GROUP = {"PG": "G", "SG": "G", "G": "G", "SF": "F", "PF": "F", "F": "F", "C": "C"}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def players():
    """{date: [player]} with a residual: played, and ETR had a median for him."""
    out = {}
    for path in sorted(glob.glob(os.path.join(DAILY, "*_box.csv"))):
        rows = []
        for r in csv.DictReader(open(path)):
            act, med, mins = num(r["actual"]), num(r["etr_median"]), num(r["min"])
            if act is None or med is None or not mins:
                continue
            rows.append({"team": r["team"], "opp": r["opp"], "pos": GROUP.get((r["pos"] or "").split("-")[0], "?"),
                         "med": med, "res": act - med, "spread": num(r["spread"])})
        if rows:
            out[os.path.basename(path)[:10]] = rows
    return out


def band(spread):
    if spread is None:
        return None
    s = abs(spread)
    return "close (4.5 or less)" if s <= 4.5 else "mid (5-9.5)" if s < 10 else "big (10+)"


def pairs(nights):
    """{(relationship, spread band or 'all'): {date: [(res x, res y)]}}, each pair in both orders."""
    out = defaultdict(lambda: defaultdict(list))
    for date, rows in nights.items():
        top = {}
        for team in {r["team"] for r in rows}:
            mine = sorted((r for r in rows if r["team"] == team), key=lambda r: -r["med"])
            top.update({id(r): i < 2 for i, r in enumerate(mine)})
        for i, x in enumerate(rows):
            for y in rows[i + 1:]:
                if x["team"] == y["team"]:
                    kind = {2: "teammates: star + star", 1: "teammates: star + role", 0: "teammates: role + role"}[top[id(x)] + top[id(y)]]
                    kinds = [kind, "teammates: same position group"] if x["pos"] == y["pos"] != "?" else [kind]
                    kinds.append("teammates: all")
                elif x["opp"] == y["team"]:
                    kinds = ["opponents: all"] + (["opponents: star + star"] if top[id(x)] and top[id(y)] else [])
                else:
                    continue
                b = band(x["spread"] if x["spread"] is not None else (-y["spread"] if y["spread"] is not None else None))
                for k in kinds:
                    for cut in ("all", b):
                        if cut:
                            out[(k, cut)][date] += [(x["res"], y["res"]), (y["res"], x["res"])]
    return out


def corr(ps):
    n = len(ps)
    if n < 10:
        return None
    mx, my = sum(a for a, _ in ps) / n, sum(b for _, b in ps) / n
    sxy = sum((a - mx) * (b - my) for a, b in ps)
    sxx, syy = sum((a - mx) ** 2 for a, _ in ps), sum((b - my) ** 2 for _, b in ps)
    return sxy / (sxx * syy) ** 0.5 if sxx and syy else None


def main():
    nights = players()
    table = pairs(nights)
    order = ["teammates: star + star", "teammates: star + role", "teammates: role + role", "teammates: same position group",
             "teammates: all", "opponents: star + star", "opponents: all"]
    cuts = ["all", "close (4.5 or less)", "mid (5-9.5)", "big (10+)"]
    rnd = random.Random(7)
    out = ["# NBA residual correlations", "",
           "Residual = actual - ETR's median, every rotation player in every game, %d nights (%s to %s). "
           "Correlation of two players' residuals in the same game (pairs, each counted once); 80%% range from resampling nights. "
           "Close to 0: one player's big night says nothing about the other's. Written by scripts/nba_residuals.py." % (
               len(nights), min(nights), max(nights)), "",
           "| Relationship | " + " | ".join("Spread: " + c if c != "all" else "All games" for c in cuts) + " |",
           "|---" * (len(cuts) + 1) + "|"]
    for k in order:
        cells = []
        for c in cuts:
            per = table.get((k, c), {})
            ds = sorted(per)
            flat = [p for d in ds for p in per[d]]
            r = corr(flat)
            if r is None:
                cells.append("-")
                continue
            bs = sorted(v for v in (corr([p for d in (rnd.choice(ds) for _ in ds) for p in per[d]]) for _ in range(300)) if v is not None)
            cells.append("%+.2f (%+.2f to %+.2f), %d pairs" % (r, bs[len(bs) // 10], bs[len(bs) * 9 // 10], len(flat) // 2))
        out.append("| %s | %s |" % (k, " | ".join(cells)))
    out += ["", "No split by game total: totals aren't on file yet (the mirror keeps spreads only)."]
    open(OUT, "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
