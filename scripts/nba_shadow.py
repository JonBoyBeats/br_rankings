"""NBA shadow orders: every switch that replaced a rule, and every forward-tested candidate, graded nightly against the
Tiers button on the same decision pairs.

From tier_history.csv (the button's order is its `built` rank), for each slate:

  PM T2   the switch ADP (2: ETR) against the rule it replaced, ADP (1: ETR)            provisional (best of 8 in step 6)
  PM T4   the switch ADP (2: ETR) against the rule it replaced, ETR (ties ADP, Boom)    provisional (best of 8 in step 6)
  PM T5   the switch ADP against the rule it replaced, ETR (2: less drafted): the paused ownership tiebreak
  PM T4   candidate: PRICEY-last off (VALUE first kept) against the button
  AM T4   candidate: the leverage tiebreak (within 2 projected points, less drafted first) against the button
  T5      the switch (2026-11-09, provisional; money RULE for the ownership tiebreak): the tier's rule, VALUE first, then
          the less drafted first within 2 projected points (money's definition: drafted% 10+ apart, both 2%+), in each
          window against the rule it amended (AM: Proj (3: ADP); PM: ADP). The AM points cost on the primary sample (-3.7
          per pair on money's definition, check pending) is a known price for a money RULE, not a reason to drop it: the
          switch is dropped only if it loses to the old rule over its 14 forward nights
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
import collections, csv, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G      # noqa: E402
import nba_tier_history as T    # noqa: E402
import nba_tier_rules as R      # noqa: E402
import nba_money_points as MP   # noqa: E402  money's definitions

REP = G.REP
FORWARD = "2026-11-10"
HYP = os.path.join(REP, "hypotheses.json")
MAX_TESTING = 3            # ideas under test per tier at once
QR = re.compile(r"^q", re.I)
QT = re.compile(r"^(q|d|g)", re.I)
# The switches in force that are still provisional, and the kept cap: each against the rule it replaced (positive = the
# switch won). drop_if: "no win" (dropped unless it beats the old rule over 14 forward nights) or "loss" (dropped only if it
# loses there: the T5 tiebreak, whose points cost is a known price for a money RULE).
SWITCHES = [
    {"id": "pm-t2-adp-etr2", "name": "PM T2: ADP (2: ETR) vs the old ADP (1: ETR)", "window": "pm", "tiers": (2,), "kind": "switch",
     "steps": [("adp", 1), ("projx", 0)], "flags": "both", "drop_if": "no win"},
    {"id": "pm-t4-adp-etr2", "name": "PM T4: ADP (2: ETR) vs the old ETR rule", "window": "pm", "tiers": (4,), "kind": "switch",
     "steps": [("proj", 0), ("adp", 0), ("boom", 0)], "flags": "both", "drop_if": "no win"},
    {"id": "pm-t5-vs-old-etr", "name": "PM T5: the button (ADP, then the less drafted within 2 pts) vs the old ETR (2: less drafted)",
     "window": "pm", "tiers": (5,), "kind": "switch", "steps": [("projx", 2), ("drafted", 10), ("projx", 0)], "flags": "both", "drop_if": None},
    {"id": "t5-less-drafted-am", "name": "AM T5: the less drafted within 2 pts vs the old Proj (3: ADP)", "window": "am", "tiers": (5,),
     "kind": "switch", "steps": [("proj", 3), ("adp", 0)], "flags": "both", "drop_if": "loss"},
    {"id": "t5-less-drafted-pm", "name": "PM T5: the less drafted within 2 pts vs the old ADP", "window": "pm", "tiers": (5,),
     "kind": "switch", "steps": [("adp", 0)], "flags": "both", "drop_if": "loss"},
    {"id": "one-tier-cap", "name": "All tiers, kept: the one-tier cap against the projection tier's order where they disagree",
     "window": "am+pm", "tiers": None, "kind": "cap", "pairwise": "cap", "flags": "both", "drop_if": None},
]


def tier_ideas():
    """The ideas under test from hypotheses.json "tiers" (each written with its test before any grading), at most
    MAX_TESTING per tier."""
    reg = json.load(open(HYP)).get("tiers", {}) if os.path.exists(HYP) else {}
    testing = [dict(h, id=k) for k, h in reg.items() if h.get("status") == "testing"]
    per = collections.Counter(t for h in testing for t in h["tiers"])
    over = [t for t, n in per.items() if n > MAX_TESTING]
    if over:
        sys.exit("hypotheses.json: more than %d ideas under test in T%s" % (MAX_TESTING, ", T".join(map(str, sorted(over)))))
    out = []
    for h in testing:
        t = h["test"]
        out.append({"id": h["id"], "name": "%s: %s" % (h["id"], h["idea"]), "window": h["window"], "tiers": tuple(h["tiers"]),
                    "kind": "candidate", "steps": [tuple(x) for x in t["steps"]] if t.get("steps") else None,
                    "pairwise": t.get("pairwise"), "flags": t.get("flags", "both"), "forward": h.get("forward_from", FORWARD),
                    "drop_if": "no win"})
    return out


def pairwise(how, a, b, ctx):
    """A pairwise candidate's first of the pair, or None where it takes the button's order."""
    if how == "lev":                       # money's ownership tiebreak: the less drafted within 2 projected points
        return MP.less_drafted(a, b) if a["flag"] == b["flag"] and a["tier"] == b["tier"] else None
    if how == "beneficiary_r6":            # a round-6 pick whose teammate is tagged Q/D/GTD at this window's record
        last = 5 * int(a["pod"])
        ben = lambda r: G.num(r["adp"]) is not None and G.num(r["adp"]) > last and r["team"] in ctx["tagged"]
        return a if ben(a) and not ben(b) else b if ben(b) and not ben(a) else None
    c = MP.cap_order(a, b)                 # cap: the combined tier's first; the projection tier's is the other
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
    tagged = collections.defaultdict(set)
    for r in H:
        if QT.match(r["tag"] or ""):
            tagged[(r["date"], r["window"])].add(r["team"])
    rows_out, res = [], {}
    for c in SWITCHES + tier_ideas():
        window, tier, kind, steps, flags = c["window"], c["tiers"], c["kind"], c.get("steps"), c["flags"]
        fwd_from = c.get("forward", FORWARD)
        per_all, per_fwd, pl_all, pl_fwd = (collections.defaultdict(list) for _ in range(4))
        by_slate = collections.defaultdict(list)
        tiers = {str(t) for t in tier} if tier else {"1", "2", "3", "4", "5"}
        for r in H:
            if r["pod"] == "6" and r["window"] in window.split("+") and r["tier"] in tiers and r["built"] and \
                    not (r["window"] == "pm" and QR.match(r["tag"] or "")) and (r["tier"] != "5" or (G.num(r["adp"]) is not None and G.num(r["adp"]) < G.cap(r))):
                by_slate[(r["date"], r["window"])].append(r)
        for (d, w), rs in sorted(by_slate.items()):
            base = {r["player_id"]: int(r["built"]) for r in rs}
            ctx = {"tagged": tagged[(d, w)]}
            o = None
            if not c.get("pairwise"):
                o = {}
                for t in {r["tier"] for r in rs}:       # the alternative's order inside each tier
                    o.update(alt_order(R.items([r for r in rs if r["tier"] == t], w), steps if steps else T.RULE_STEPS[w][int(t)], flags))
            gains = []
            for i, a in enumerate(rs):
                for b in rs[i + 1:]:
                    if abs(G.adp(a) - G.adp(b)) > G.DECISION or a["slot"] == b["slot"] or (tier is not None and a["tier"] != b["tier"]):
                        continue
                    nb = base[a["player_id"]] < base[b["player_id"]]
                    if o is None:
                        p = pairwise(c["pairwise"], a, b, ctx)
                        if p is None or (p is a) == nb:
                            continue
                        no = p is a
                    else:
                        no = o[a["player_id"]] < o[b["player_id"]]
                    if nb == no:
                        continue
                    # switch: positive = the button (new) beat the old rule; candidate: positive = the candidate beat the button;
                    # cap (kept): positive = the button (the cap) beat the projection tier's order
                    first_new = (a, b) if nb else (b, a)
                    g = first_new[0]["slot"] - first_new[1]["slot"]
                    if kind == "candidate":
                        g = -g
                    gains.append(g)
                    for per, pl in ((per_all, pl_all),) + (((per_fwd, pl_fwd),) if d >= fwd_from else ()):
                        per[d].append(g)
                        pl[a["player_id"]].append(g)
                        pl[b["player_id"]].append(g)
            rows_out.append({"date": d, "comparison": c["name"], "kind": kind, "pairs": len(gains), "gain": round(sum(gains), 1)})
        res[c["name"]] = (kind, G.verdict(per_all, pl_all), G.verdict(per_fwd, pl_fwd), len(per_fwd), c, fwd_from)
    v2d = lambda v: {"n": v[0], "mean": v[1], "lo": v[2], "hi": v[3], "label": v[4], "text": G.fmt(v) if v[0] else "none yet"}
    json.dump([{"id": c["id"], "name": name, "kind": kind, "tiers": list(c["tiers"]) if c["tiers"] else [1, 2, 3, 4, 5],
                "window": c["window"], "drop_if": c.get("drop_if"), "forward_from": fwd, "forward_nights": n_fwd,
                "season": v2d(v_all), "forward": v2d(v_fwd)}
               for name, (kind, v_all, v_fwd, n_fwd, c, fwd) in res.items()], open(os.path.join(REP, "shadow.json"), "w"), indent=1)
    out = ["# NBA shadow orders", "", "Written nightly by scripts/nba_shadow.py. Points per pair on the decision pairs the two "
           "orders disagree on (80%% range from resampling slates). Switch: positive = the switch beat the rule it replaced. "
           "Candidate: positive = the candidate beat the button. Kept (the cap): positive = the cap beat the projection tier's order. Forward nights start %s; a provisional switch is dropped if it "
           "doesn't beat the old rule there over 14 nights, a candidate needs a lean there to be considered." % FORWARD, "",
           "| Comparison | Kind | Season | Forward nights | Forward |", "|---|---|---|---|---|"]
    for name, (kind, v_all, v_fwd, n_fwd, c, fwd) in res.items():
        out.append("| %s | %s | %s | %d | %s |" % (name, kind, G.fmt(v_all), n_fwd, G.fmt(v_fwd) if v_fwd[0] else "none yet"))
    open(os.path.join(REP, "shadow.md"), "w").write("\n".join(out) + "\n")
    with open(os.path.join(REP, "shadow.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "comparison", "kind", "pairs", "gain"])
        w.writeheader()
        w.writerows(rows_out)
    print("\n".join(out))


if __name__ == "__main__":
    main()
