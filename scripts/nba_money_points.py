"""Points checks on the contest side's money verdicts (2026-11-09), each on the money side's own definition
(scripts/nba_money.py DECISIONS), graded on the rankings side's decision pairs (same tier, ADP within 4; T5 drafted
players only; a scratch scored through his swap) with its evidence bar (nba_tier_grade.verdict).

  ownership   T5 and T2-T4: the less drafted of two within 2 projected points (the window's projection: ours AM, ETR PM),
              drafted% at least 10 apart and the less drafted at 2%+ (money's less_drafted()); points per pair, positive
              when the less drafted scored more. Every such pair, not only where your board moved.
  pricey t1   an unflagged elite over a PRICEY one in T1 (money's flag_vs_plain): positive when the unflagged scored more
  cap         the combined tier's order over the projection tier's where they differ (money's one-tier-cap): positive
              when the combined tier's first scored more
  round 6     AM: a round-6 pick (ADP past 5 rounds) whose teammate was tagged Q/D/GTD at Lock AM and played: his score
              over his ADP round band's average, against the other round-6 picks

Cuts: the policy cuts (6-drafter AM primary, 6-drafter PM) and every slate (both pods, both AM samples: money's sample).
Writes analysis/nba/report/money_points.md.

  python3 scripts/nba_money_points.py
"""
import collections, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G      # noqa: E402

REP = G.REP
OUT = os.path.join(REP, "money_points.md")
num = G.num
QT = re.compile(r"^(q|d|g)", re.I)
CUTS = [("6-drafter AM, primary", lambda r: r["pod"] == "6" and r["window"] == "am" and r["sample"] == "primary"),
        ("6-drafter PM", lambda r: r["pod"] == "6" and r["window"] == "pm"),
        ("every slate, AM (money's sample)", lambda r: r["window"] == "am"),
        ("every slate, PM (money's sample)", lambda r: r["window"] == "pm")]


def less_drafted(a, b, proj_within=2, min_gap=10):
    """Money's pick: the less drafted of two within proj_within projected points, drafted% min_gap apart, both 2%+."""
    pa, pb, da, db = num(a["proj"]), num(b["proj"]), num(a["drafted"]), num(b["drafted"])
    if None in (pa, pb, da, db) or abs(pa - pb) > proj_within or abs(da - db) < min_gap or min(da, db) < 2:
        return None
    return a if da < db else b


def graded(H, cut, tiers, pick, same_tier=True):
    """{slate: [points of pick's first minus the other]} and {player: [...]} over the decision pairs."""
    per, pl = collections.defaultdict(list), collections.defaultdict(list)
    by = collections.defaultdict(list)
    for r in H:
        if cut(r) and (tiers is None or int(r["tier"]) in tiers) and (r["tier"] != "5" or (num(r["adp"]) is not None and num(r["adp"]) < G.cap(r))):
            by[(r["date"], r["window"])].append(r)
    for (d, _), rs in by.items():
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                if abs(G.adp(a) - G.adp(b)) > G.DECISION or (same_tier and a["tier"] != b["tier"]):
                    continue
                p = pick(a, b)
                if p is None:
                    continue
                o = b if p is a else a
                g = p["slot"] - o["slot"]
                per[d].append(g)
                pl[a["player_id"]].append(g)
                pl[b["player_id"]].append(g)
    return per, pl


def pricey_t1(a, b):
    fa, fb = a["flag"], b["flag"]
    if {fa, fb} != {"PRICEY", ""}:
        return None
    return a if fa == "" else b


def cap_order(a, b):
    ta, tb, pa, pb = int(a["tier"]), int(b["tier"]), int(a["p_tier"] or 0), int(b["p_tier"] or 0)
    if not pa or not pb or ta == tb or pa == pb or (ta < tb) == (pa < pb):
        return None
    return a if ta < tb else b


def round6(H):
    """AM round-6 picks: score over the ADP round band, split by a teammate tagged at Lock AM who played / sat / none."""
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    by = collections.defaultdict(list)
    for r in H:
        if r["window"] == "am":
            by[r["date"]].append(r)
    for d, rs in by.items():
        pod = int(rs[0]["pod"])
        pr = sorted((r for r in rs if num(r["adp"]) is not None and num(r["adp"]) < G.cap(r)), key=G.adp)
        bands = collections.defaultdict(list)
        for i, r in enumerate(pr):
            bands[min(i // pod, 5)].append(r)
        r6 = bands.get(5, [])
        if not r6:
            continue
        m = sum(r["slot"] for r in r6) / len(r6)
        for r in r6:
            mates = [x for x in rs if x["team"] == r["team"] and x["player_id"] != r["player_id"] and QT.match(x["tag"] or "")]
            k = "teammate tagged, played" if any(x["played"] == "1" for x in mates) else \
                "teammate tagged, sat" if mates else "no tagged teammate"
            out[k][d].append(r["slot"] - m)
    return out


def main():
    H = G.load()
    md = ["# Points checks on the money verdicts (2026-11-09)", "",
          "Written by scripts/nba_money_points.py, each decision on the money side's own definition (scripts/nba_money.py), "
          "graded on decision pairs (same tier, ADP within 4; T5 drafted only; a scratch scored through his swap). Points per "
          "pair (80% range from resampling slates), pairs, evidence level. Money's verdicts are from money_report.md section 3b "
          "(after the price-split check).", ""]
    rows = [("1. T5 ownership tiebreak: the less drafted within 2 projected points", {5}, less_drafted, True),
            ("2. T2-T4 leverage: the less drafted within 2 projected points", {2, 3, 4}, less_drafted, True),
            ("3. T1: an unflagged elite over a PRICEY one", {1}, pricey_t1, True),
            ("4. The one-tier cap: the combined tier's first over the projection tier's", None, cap_order, False)]
    md += ["| Decision | " + " | ".join(c for c, _ in CUTS) + " |", "|---|" + "---|" * len(CUTS)]
    for name, tiers, pick, same in rows:
        cells = []
        for _, cut in CUTS:
            per, pl = graded(H, cut, tiers, pick, same)
            cells.append(G.fmt(G.verdict(per, pl)))
        md.append("| %s | %s |" % (name, " | ".join(cells)))
    md += ["", "Ownership by tier (every slate, both windows):", "", "| Tier | Points per pair |", "|---|---|"]
    for t in (2, 3, 4, 5):
        per, pl = graded(H, lambda r: True, {t}, less_drafted)
        md.append("| T%d | %s |" % (t, G.fmt(G.verdict(per, pl))))
    md += ["", "## 5. Round-6 picks with a teammate tagged at Lock AM (every AM slate)", "",
           "| Round-6 pick | Score over his ADP round band |", "|---|---|"]
    for k, per in sorted(round6(H).items()):
        md.append("| %s | %s |" % (k, G.fmt(G.verdict(per))))
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
