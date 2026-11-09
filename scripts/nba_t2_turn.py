"""T2-1's backtest (pre-registered 2026-11-09 in hypotheses.json): does T2 behave differently past the 1/2 turn?

Inside T2 at each window's record (6-drafter; AM the primary sample, PM every slate), on decision pairs (ADP within 4,
a scratch scored through his swap):
  a. the window's projection straight (ours AM, ETR PM) against ADP straight, positive when the projection was right,
     split by where the pair sits: both at ADP 9.5 or earlier (the 1/2 turn), straddling 9.5, both after it (picks 10+)
  b. T2-1 (ADP to 9.5, then the projection; flag groups kept) against the button, positive when T2-1 was right, by
     window, with the AM secondary sample as context
Points per pair with the 80% range from resampling slates and the evidence label (under 40 pairs: not enough yet).
Writes analysis/nba/report/t2_turn.md.

  python3 scripts/nba_t2_turn.py
"""
import collections, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G      # noqa: E402
import nba_shadow as SH         # noqa: E402  T2-1's pairwise rule

REP = G.REP
OUT = os.path.join(REP, "t2_turn.md")
TURN = SH.TURN12
CUTS = [("AM primary", lambda r: r["window"] == "am" and r["sample"] == "primary"),
        ("AM secondary (context)", lambda r: r["window"] == "am" and r["sample"] == "secondary"),
        ("PM", lambda r: r["window"] == "pm")]


def main():
    H = G.load()
    t2 = collections.defaultdict(list)
    for r in H:
        if r["pod"] == "6" and r["tier"] == "2":
            t2[(r["date"], r["window"])].append(r)
    where = lambda a, b: "both at 9.5 or earlier" if G.adp(a) <= TURN and G.adp(b) <= TURN else \
        "both after 9.5 (picks 10+)" if G.adp(a) > TURN and G.adp(b) > TURN else "straddling 9.5"
    proj = {c: collections.defaultdict(lambda: (collections.defaultdict(list), collections.defaultdict(list))) for c, _ in CUTS}
    idea = {c: (collections.defaultdict(list), collections.defaultdict(list)) for c, _ in CUTS}
    for (d, w), rs in t2.items():
        cut = next((c for c, f in CUTS if f(rs[0])), None)
        if cut is None:
            continue
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                if abs(G.adp(a) - G.adp(b)) > G.DECISION or a["slot"] == b["slot"]:
                    continue
                pa, pb = G.num(a["proj"]), G.num(b["proj"])
                if pa is not None and pb is not None and pa != pb and G.adp(a) != G.adp(b):
                    pf = a if pa > pb else b
                    af = a if G.adp(a) < G.adp(b) else b
                    if pf is not af:
                        g = pf["slot"] - (b if pf is a else a)["slot"]
                        per, pl = proj[cut][where(a, b)]
                        per[d].append(g)
                        pl[a["player_id"]].append(g)
                        pl[b["player_id"]].append(g)
                p = SH.pairwise("turn12", a, b, {})
                if p is None or not a["built"] or not b["built"]:
                    continue
                bf = a if int(a["built"]) < int(b["built"]) else b
                if p is bf:
                    continue
                g = p["slot"] - bf["slot"]
                per, pl = idea[cut]
                per[d].append(g)
                pl[a["player_id"]].append(g)
                pl[b["player_id"]].append(g)
    md = ["# T2-1: T2 past the 1/2 turn", "",
          "Written by scripts/nba_t2_turn.py, as pre-registered in hypotheses.json (T2-1, 2026-11-09). 6-drafter; points per "
          "pair (80% range from resampling slates), pairs, evidence label.", "",
          "## a. The window's projection straight against ADP straight, inside T2 (positive: the projection was right)", "",
          "| Window | Both at 9.5 or earlier | Straddling 9.5 | Both after 9.5 (picks 10+) |", "|---|---|---|---|"]
    for c, _ in CUTS:
        md.append("| %s | %s |" % (c, " | ".join(G.fmt(G.verdict(*proj[c][k])) if proj[c][k][0] else "-"
                                              for k in ("both at 9.5 or earlier", "straddling 9.5", "both after 9.5 (picks 10+)"))))
    md += ["", "## b. T2-1 against the button, inside T2 (positive: T2-1 was right)", "", "| Window | T2-1 against the button |", "|---|---|"]
    for c, _ in CUTS:
        md.append("| %s | %s |" % (c, G.fmt(G.verdict(*idea[c])) if idea[c][0] else "-"))
    md += ["", "In sample only: T2-1's forward nights from 2026-11-10 decide it (shadow.md)."]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
