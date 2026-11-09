"""Q-1's backtest (pre-registered 2026-11-09 in hypotheses.json): the push decision for Questionable players, split.

For every player tagged Questionable at a window's record, the push decision is graded in cells: window (AM primary
sample, PM) x flag (VALUE / unflagged / PRICEY) x our calibrated chance he plays (under 50%, 50-70%, over 70%;
scripts/nba_q_lane.py's fit) x tier (T1-T2 / T3-T5, his combined tier). In each cell the slate's order is rebuilt three
ways, as the Tiers button orders (by tier, VALUE first and PRICEY last, then the tier's rule): no push, the cell's
Questionable players one tier back, two tiers back (to T5 at most). On 6-drafter decision pairs (ADP within 4, any
tiers) with one of the cell's players that a push orders differently from no push, points per pair (a scratch scored
through his swap), positive when the push was right; with the 80% range from resampling slates and the evidence label
(under 40 pairs: not enough yet). 72 cells: by chance alone about 40% of the cells with enough pairs would show a lean.

Then Q-1 itself against the button, in sample, from the shadow (shadow.json). Writes analysis/nba/report/q_split.md.

  python3 scripts/nba_q_split.py
"""
import collections, json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G      # noqa: E402
import nba_tier_history as T    # noqa: E402
import nba_tier_rules as R      # noqa: E402
import nba_q_lane as Q          # noqa: E402

REP = G.REP
OUT = os.path.join(REP, "q_split.md")
QR = re.compile(r"^q", re.I)
FLAGS = [("VALUE", "VALUE"), ("unflagged", ""), ("PRICEY", "PRICEY")]
BANDS = [("under 50%", 0, 0.5), ("50-70%", 0.5, 0.7), ("over 70%", 0.7, 1.01)]
TIERS = [("T1-T2", {1, 2}), ("T3-T5", {3, 4, 5})]


def order(rs, w, tier_of):
    """{player_id: rank}: the button's order with each player in tier_of(r)."""
    its = R.items(rs, w, tier_of=tier_of)
    out, rank = {}, 0
    for t in range(1, 6):
        for f in ("VALUE", "", "PRICEY"):
            for i in T.rule_sort([i for i in its if i["t"] == t and i["r"]["flag"] == f], T.RULE_STEPS[w][t]):
                rank += 1
                out[i["r"]["player_id"]] = rank
    return out


def main():
    H = G.load()
    cal = [dict(p=float(r["play"]), y=int(r["played"]), tagged=bool(Q.QT.match(r["tag"] or ""))) for r in H if r["play"] != "" and r["played"] != ""]
    a, b, c = Q.fit(cal)
    pcal = lambda p: 1 / (1 + math.exp(-(a + b * Q.logit(min(max(p, 0.005), 0.995)) + c)))
    slates = collections.defaultdict(list)
    for r in H:
        if r["pod"] == "6" and (r["window"] == "pm" or r["sample"] == "primary") and (r["tier"] != "5" or (G.num(r["adp"]) is not None and G.num(r["adp"]) < G.cap(r))):
            slates[(r["date"], r["window"])].append(r)
    res = {}
    for (d, w), rs in slates.items():
        qs = [r for r in rs if QR.match(r["tag"] or "") and r["play"] != ""]
        if not qs:
            continue
        base = order(rs, w, lambda r: int(r["tier"]))
        sel = []        # (key, the Questionable players it pushes): each full cell, and each dimension alone
        for fl, fv in FLAGS:
            for bl, lo, hi in BANDS:
                for tl, ts in TIERS:
                    sel.append(((w, fl, bl, tl), {r["player_id"] for r in qs if r["flag"] == fv and lo <= pcal(float(r["play"])) < hi and int(r["tier"]) in ts}))
        sel += [((w, "flag", fl), {r["player_id"] for r in qs if r["flag"] == fv}) for fl, fv in FLAGS]
        sel += [((w, "chance", bl), {r["player_id"] for r in qs if lo <= pcal(float(r["play"])) < hi}) for bl, lo, hi in BANDS]
        sel += [((w, "tier", tl), {r["player_id"] for r in qs if int(r["tier"]) in ts}) for tl, ts in TIERS]
        for key, cell in sel:
                    if not cell:
                        continue
                    for v, k in (("one", 1), ("two", 2)):
                        alt = order(rs, w, lambda r, k=k: min(5, int(r["tier"]) + k) if r["player_id"] in cell else int(r["tier"]))
                        per, pl = res.setdefault(key + (v,), (collections.defaultdict(list), collections.defaultdict(list)))
                        for i, x in enumerate(rs):
                            for y in rs[i + 1:]:
                                if x["player_id"] not in cell and y["player_id"] not in cell:
                                    continue
                                if abs(G.adp(x) - G.adp(y)) > G.DECISION or x["slot"] == y["slot"]:
                                    continue
                                nb, na = base[x["player_id"]] < base[y["player_id"]], alt[x["player_id"]] < alt[y["player_id"]]
                                if nb == na:
                                    continue
                                f_, s_ = (x, y) if na else (y, x)
                                g = f_["slot"] - s_["slot"]
                                per[d].append(g)
                                for pid in (x["player_id"], y["player_id"]):
                                    if pid in cell:
                                        pl[pid].append(g)
    md = ["# Q-1: the Questionable push, split by flag, chance to play and tier", "",
          "Written by scripts/nba_q_split.py, as pre-registered in hypotheses.json (Q-1, 2026-11-09). Points per pair on "
          "decision pairs where the push orders a cell's Questionable players differently from no push; positive: the push "
          "was right. AM: the primary sample (Lock AM on our Proj); PM: every 6-drafter slate. Players: distinct Questionable "
          "players in the cell. 72 cells: about 40% of the cells with enough pairs would lean by chance alone.", ""]
    leans = 0
    for w in ("am", "pm"):
        md += ["## %s" % w.upper(), "", "| Flag | Chance to play | Tier | Players | Back one vs no push | Back two vs no push |", "|---|---|---|---|---|---|"]
        for fl, _ in FLAGS:
            for bl, _, _ in BANDS:
                for tl, _ in TIERS:
                    one, two = res.get((w, fl, bl, tl, "one")), res.get((w, fl, bl, tl, "two"))
                    if not one and not two:
                        continue
                    n = len(set(one[1] if one else ()) | set(two[1] if two else ()))
                    cells = []
                    for x in (one, two):
                        v = G.verdict(x[0], x[1]) if x else (0, None, None, None, "-")
                        leans += v[4].startswith(("LEAN", "RULE"))
                        cells.append(G.fmt(v) if v[0] else "-")
                    md.append("| %s | %s | %s | %d | %s | %s |" % (fl, bl, tl, n, cells[0], cells[1]))
        md += ["", "By one dimension at a time (%s):" % w.upper(), "", "| Split | Group | Players | Back one vs no push | Back two vs no push |", "|---|---|---|---|---|"]
        for dim, groups in (("flag", [x[0] for x in FLAGS]), ("chance", [x[0] for x in BANDS]), ("tier", [x[0] for x in TIERS])):
            for g_ in groups:
                one, two = res.get((w, dim, g_, "one")), res.get((w, dim, g_, "two"))
                if not one and not two:
                    continue
                n = len(set(one[1] if one else ()) | set(two[1] if two else ()))
                md.append("| %s | %s | %d | %s | %s |" % (dim, g_, n, *(G.fmt(G.verdict(x[0], x[1])) if x else "-" for x in (one, two))))
        md.append("")
    sh = {c["id"]: c for c in json.load(open(os.path.join(REP, "shadow.json")))} if os.path.exists(os.path.join(REP, "shadow.json")) else {}
    q1 = sh.get("Q-1")
    md += ["%d cells show a lean or rule." % leans, "",
           "**Q-1 against the button, in sample** (both windows, 6-drafter, Questionable players included): %s. Forward nights "
           "from %s decide it." % (q1["season"]["text"] if q1 else "not in the shadow yet", q1["forward_from"] if q1 else "2026-11-10")]
    open(OUT, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
