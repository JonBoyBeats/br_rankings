"""NBA shadow orders: every switch that replaced a rule, and every forward-tested candidate, graded nightly against the
Tiers button on the same decision pairs.

From tier_history.csv (the button's order is its `built` rank), for each slate:

  PM T2   the switch ADP (2: ETR) against the rule it replaced, ADP (1: ETR)            provisional (best of 8 in step 6)
  PM T4   the switch ADP (2: ETR) against the rule it replaced, ETR (ties ADP, Boom)    provisional (best of 8 in step 6)
  PM T5   the switch ADP against the rule it replaced, ETR (2: less drafted): the paused ownership tiebreak
  PM T4   candidate: PRICEY-last off (VALUE first kept) against the button
  AM T4   candidate: the leverage tiebreak (within 2 projected points, less drafted first) against the button
  T5      candidates from the contest side (2026-11-09; money RULE for the ownership tiebreak): the tier's rule, VALUE first,
          then the less drafted first within 2 projected points (money's definition: drafted% 10+ apart, both 2%+), in
          each window against the current rule (AM: the button's order; PM: ADP, VALUE first)
  T2-T4   candidate: the same leverage tiebreak on money's definition, each window (money LEAN for)
  all     the one-tier cap (kept; money leans against): the projection tier's order where it and the combined tier's
          disagree, against the button

A pairwise candidate (a function of a decision pair) takes the button's order except where it applies; for those its
pick is graded against the button's.

Each alternative keeps the button's tiers and VALUE-first / PRICEY-last groups (except where it changes them); a PM
Questionable player, ordered two tiers back by the button, is left out of his tier's comparison. On the decision pairs
(ADP within 4) the two order differently, points per pair (a scratch scored through his swap): for a switch, positive
when the switch beat the old rule; for a candidate, positive when the candidate beat the button. Shown for the season
(in sample for the switches) and for the forward nights (from 2026-11-10), with the evidence level.
Writes analysis/nba/report/shadow.md and shadow.csv (one row per slate and comparison).

  python3 scripts/nba_shadow.py
"""
import collections, csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G      # noqa: E402
import nba_tier_history as T    # noqa: E402
import nba_tier_rules as R      # noqa: E402
import nba_money_points as MP   # noqa: E402  money's definitions

REP = G.REP
FORWARD = "2026-11-10"
QR = re.compile(r"^q", re.I)
COMPARE = [
    # (name, window, tier, kind, steps or a function of the items, flags)
    ("PM T2: ADP (2: ETR) vs the old ADP (1: ETR)", "pm", 2, "switch", [("adp", 1), ("projx", 0)], "both"),
    ("PM T4: ADP (2: ETR) vs the old ETR rule", "pm", 4, "switch", [("proj", 0), ("adp", 0), ("boom", 0)], "both"),
    ("PM T5: ADP vs the old ETR (2: less drafted), the paused ownership tiebreak", "pm", 5, "switch",
     [("projx", 2), ("drafted", 10), ("projx", 0)], "both"),
    ("PM T4 candidate: PRICEY-last off (VALUE first kept)", "pm", 4, "candidate", None, "value"),
    ("AM T4 candidate: the leverage tiebreak", "am", 4, "candidate", [("projx", 2), ("drafted", 0), ("proj", 3), ("adp", 0)], "both"),
    ("AM T5 candidate: the button's order, VALUE first, then the less drafted within 2 projected points", "am", 5, "candidate", "lev", "both"),
    ("PM T5 candidate: ADP, VALUE first, then the less drafted within 2 projected points", "pm", 5, "candidate", "lev", "both"),
    ("AM T2-T4 candidate: the less drafted within 2 projected points", "am", (2, 3, 4), "candidate", "lev", "both"),
    ("PM T2-T4 candidate: the less drafted within 2 projected points", "pm", (2, 3, 4), "candidate", "lev", "both"),
    ("All tiers, kept: the one-tier cap against the projection tier's order where they disagree", "am+pm", None, "cap", "cap", "both"),
]


def pairwise(how, a, b):
    """A pairwise candidate's first of the pair, or None where it takes the button's order."""
    if how == "lev":
        return MP.less_drafted(a, b) if a["flag"] == b["flag"] and a["tier"] == b["tier"] else None
    c = MP.cap_order(a, b)                 # the combined tier's first; the projection tier's is the other
    return None if c is None else (b if c is a else a)


def alt_order(its, steps, flags):
    groups = ("VALUE", "", "PRICEY") if flags == "both" else ("VALUE", None)
    out, rank = {}, 0
    for f in groups:
        g = [i for i in its if (i["r"]["flag"] == f) if f is not None] if f is not None else \
            [i for i in its if i["r"]["flag"] != "VALUE"]
        for i in T.rule_sort(g, steps):
            rank += 1
            out[i["r"]["player_id"]] = rank
    return out


def main():
    H = G.load()
    rows_out, res = [], {}
    for name, window, tier, kind, steps, flags in COMPARE:
        per_all, per_fwd, pl_all, pl_fwd = (collections.defaultdict(list) for _ in range(4))
        by_slate = collections.defaultdict(list)
        tiers = {str(t) for t in (tier if isinstance(tier, tuple) else (tier,))} if tier else {"1", "2", "3", "4", "5"}
        for r in H:
            if r["pod"] == "6" and r["window"] in window.split("+") and r["tier"] in tiers and r["built"] and \
                    not (r["window"] == "pm" and QR.match(r["tag"] or "")) and (r["tier"] != "5" or (G.num(r["adp"]) is not None and G.num(r["adp"]) < G.cap(r))):
                by_slate[(r["date"], r["window"])].append(r)
        for (d, w), rs in sorted(by_slate.items()):
            base = {r["player_id"]: int(r["built"]) for r in rs}
            o = None if isinstance(steps, str) else alt_order(R.items(rs, w), steps if steps else T.RULE_STEPS[w][tier], flags)
            gains = []
            for i, a in enumerate(rs):
                for b in rs[i + 1:]:
                    if abs(G.adp(a) - G.adp(b)) > G.DECISION or a["slot"] == b["slot"] or (tier is not None and a["tier"] != b["tier"]):
                        continue
                    nb = base[a["player_id"]] < base[b["player_id"]]
                    if o is None:
                        p = pairwise(steps, a, b)
                        if p is None or (p is a) == nb:
                            continue
                        no = p is a
                    else:
                        no = o[a["player_id"]] < o[b["player_id"]]
                    if nb == no:
                        continue
                    # switch: positive = the button (new) beat the old rule; candidate: positive = the candidate beat the button
                    first_new = (a, b) if nb else (b, a)
                    g = first_new[0]["slot"] - first_new[1]["slot"]
                    if kind == "candidate":
                        g = -g                 # cap (kept): positive = the button (the cap) beat the projection tier's order
                    gains.append(g)
                    for per, pl in ((per_all, pl_all),) + (((per_fwd, pl_fwd),) if d >= FORWARD else ()):
                        per[d].append(g)
                        pl[a["player_id"]].append(g)
                        pl[b["player_id"]].append(g)
            rows_out.append({"date": d, "comparison": name, "kind": kind, "pairs": len(gains), "gain": round(sum(gains), 1)})
        res[name] = (kind, G.verdict(per_all, pl_all), G.verdict(per_fwd, pl_fwd), len(per_fwd))
    out = ["# NBA shadow orders", "", "Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two "
           "orders disagree on (80%% range from resampling slates). Switch: positive = the switch beat the rule it replaced. "
           "Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start %s; a provisional switch is dropped if it "
           "doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered." % FORWARD, "",
           "| Comparison | Kind | Season | Forward nights | Forward |", "|---|---|---|---|---|"]
    for name, (kind, v_all, v_fwd, n_fwd) in res.items():
        out.append("| %s | %s | %s | %d | %s |" % (name, kind, G.fmt(v_all), n_fwd, G.fmt(v_fwd) if v_fwd[0] else "none yet"))
    open(os.path.join(REP, "shadow.md"), "w").write("\n".join(out) + "\n")
    with open(os.path.join(REP, "shadow.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "comparison", "kind", "pairs", "gain"])
        w.writeheader()
        w.writerows(rows_out)
    print("\n".join(out))


if __name__ == "__main__":
    main()
