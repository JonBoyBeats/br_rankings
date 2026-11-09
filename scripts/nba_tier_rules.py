"""NBA per-tier ranking rules: "I'm in tier 2, here's how to rank". Step 6, from tier_history.csv.

For each combined tier and window, every candidate order is graded against the Tiers button's current order (the rule
in NBA_TIER_RULE_STEPS, VALUE first and PRICEY last, a Questionable player two tiers back in PM): on the decision pairs
(ADP within 4 at the lock) inside the tier that the candidate orders differently, points per pair (the candidate's first
minus its second, a scratch scored through his swap), positive when the candidate beats the button. Beside it, each
order's own points per pair over every decision pair in the tier, to rank them.

Candidates (all listed before testing, 2026-11-09): ADP straight; projection straight (ours AM, ETR PM); ADP with
projection as tiebreak (within 2 picks); projection with ADP as tiebreak (within 3 points); the rule without the flags
(what VALUE first / PRICEY last adds); projection with Boom as tiebreak (within 3 points); X in place of the projection
for Q-tagged players; T5 by ADP with VALUE moved up; in T2-T4, a leverage tiebreak (within 2 projected points, the less
drafted first). Then the three ways to combine the ladders, graded on every decision pair across the board: no move (the
ADP tier, flags as tiebreaks), the one-tier cap (current), the full move to the projection tier.

Labels follow the evidence policy: a candidate's LEAN is eligible for adoption (listed before testing); a RULE needs its
check. Whether it is adopted is leans.json's call (picked from several candidates it is provisional and shadow-tested;
everything adopted is provisional until its money verdict).
Writes analysis/nba/report/tier_rules.md.

  python3 scripts/nba_tier_rules.py
"""
import collections, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_tier_grade as G      # noqa: E402
import nba_tier_history as T    # noqa: E402
import nba_q_lane as Q          # noqa: E402

REP = G.REP
OUT = os.path.join(REP, "tier_rules.md")
num = G.num
QR = re.compile(r"^q", re.I)


def items(rs, window, x=None, tier_of=None):
    out = []
    for r in rs:
        px = num(r["proj"])
        if x is not None and (r["date"], window, r["player_id"]) in x:
            px = x[(r["date"], window, r["player_id"])]
        t = tier_of(r) if tier_of else int(r["tier"])
        out.append({"r": r, "t": t, "adp": -G.adp(r), "proj": float(int(px + 0.5)) if px is not None else None, "projx": px,
                    "boom": num(r["boom"]), "drafted": -num(r["drafted"]) if num(r["drafted"]) is not None else None})
    return out


def ordered(its, steps, flags=True, by_tier=True):
    """Pid -> rank: by tier (if by_tier), then VALUE / none / PRICEY (if flags), then the steps."""
    out, rank = {}, 0
    tiers = sorted({i["t"] for i in its}) if by_tier else [None]
    for t in tiers:
        grp = [i for i in its if not by_tier or i["t"] == t]
        for f in (("VALUE", "", "PRICEY") if flags else (None,)):
            g = [i for i in grp if f is None or i["r"]["flag"] == f]
            for i in T.rule_sort(g, steps):
                rank += 1
                out[i["r"]["player_id"]] = rank
    return out


def candidates(tier, window):
    """[(name, function(its) -> {pid: rank})] for one tier group (tier: a set) and window."""
    rule = T.RULE_STEPS[window]
    cur = lambda its: ordered(its, rule[min(i["t"] for i in its)] if its else [], by_tier=True)
    out = [
        ("ADP straight", lambda its: ordered(its, [("adp", 0)], flags=False, by_tier=False)),
        ("Projection straight", lambda its: ordered(its, [("projx", 0)], flags=False, by_tier=False)),
        ("ADP, projection tiebreak (2 picks)", lambda its: ordered(its, [("adp", 2), ("projx", 0)], flags=False, by_tier=False)),
        ("Projection, ADP tiebreak (3 points)", lambda its: ordered(its, [("proj", 3), ("adp", 0)], flags=False, by_tier=False)),
        ("The rule without the flags", lambda its: rule_no_flags(its, rule)),
        ("Projection, Boom tiebreak (3 points)", lambda its: ordered(its, [("proj", 3), ("boom", 0)], flags=False, by_tier=False)),
    ]
    if tier == {5}:
        out.append(("T5 by ADP, VALUE moved up", lambda its: ordered(its, [("adp", 0)], flags=True, by_tier=False)))
    if tier & {2, 3, 4} and 5 not in tier and 1 not in tier:
        out.append(("Leverage tiebreak (2 points, less drafted first)", lambda its: leverage(its, rule)))
    return out


def rule_no_flags(its, rule):
    out, rank = {}, 0
    for t in sorted({i["t"] for i in its}):
        for i in T.rule_sort([i for i in its if i["t"] == t], rule[t]):
            rank += 1
            out[i["r"]["player_id"]] = rank
    return out


def leverage(its, rule):
    """The button's order, but within 2 projected points the less drafted first (both with a drafted%)."""
    out, rank = {}, 0
    for t in sorted({i["t"] for i in its}):
        for f in ("VALUE", "", "PRICEY"):
            steps = [("projx", 2), ("drafted", 0)] + rule[t]
            for i in T.rule_sort([i for i in its if i["t"] == t and i["r"]["flag"] == f], steps):
                rank += 1
                out[i["r"]["player_id"]] = rank
    return out


def grade_orders(rows, window, tier, x):
    """{candidate: ({slate: [gain vs button]}, {pid: [gain]}, [own points per pair over all pairs])}"""
    res = collections.defaultdict(lambda: (collections.defaultdict(list), collections.defaultdict(list), []))
    base_own = []
    by_slate = collections.defaultdict(list)
    for r in rows:
        if int(r["tier"]) in tier and r["built"]:
            by_slate[r["date"]].append(r)
    for d, rs in by_slate.items():
        base = {r["player_id"]: int(r["built"]) for r in rs}
        its = items(rs, window)
        orders = [(name, f(its)) for name, f in candidates(tier, window)]
        orders.append(("X for Q-tagged players", rule_no_flags_x(rs, window, x)))
        pairs = [(a, b) for i, a in enumerate(rs) for b in rs[i + 1:] if abs(G.adp(a) - G.adp(b)) <= G.DECISION and a["slot"] != b["slot"]]
        for a, b in pairs:
            first, second = (a, b) if base[a["player_id"]] < base[b["player_id"]] else (b, a)
            base_own.append(first["slot"] - second["slot"])
        for name, o in orders:
            for a, b in pairs:
                if a["player_id"] not in o or b["player_id"] not in o:
                    continue
                cf = o[a["player_id"]] < o[b["player_id"]]
                first, second = (a, b) if cf else (b, a)
                g = first["slot"] - second["slot"]
                res[name][2].append(g)
                if cf == (base[a["player_id"]] < base[b["player_id"]]):
                    continue
                res[name][0][d].append(g)
                res[name][1][a["player_id"]].append(g)
                res[name][1][b["player_id"]].append(g)
    return res, base_own


def rule_no_flags_x(rs, window, x):
    its = items(rs, window, x=x)
    out, rank = {}, 0
    for t in sorted({i["t"] for i in its}):
        for f in ("VALUE", "", "PRICEY"):
            for i in T.rule_sort([i for i in its if i["t"] == t and i["r"]["flag"] == f], T.RULE_STEPS[window][t]):
                rank += 1
                out[i["r"]["player_id"]] = rank
    return out


def ladder_versions(rows, window):
    """The three ways to combine the ladders, against the current one-tier cap, on every decision pair."""
    res = collections.defaultdict(lambda: (collections.defaultdict(list), collections.defaultdict(list)))
    by_slate = collections.defaultdict(list)
    for r in rows:
        if r["built"]:
            by_slate[r["date"]].append(r)
    push = lambda r, t: min(5, t + T.PM_Q_PUSH) if window == "pm" and QR.match(r["tag"] or "") else t
    versions = {"No move (ADP tier, flags as tiebreaks)": lambda r: push(r, int(r["a_tier"])),
                "Full move to the projection tier": lambda r: push(r, int(r["p_tier"]))}
    for d, rs in by_slate.items():
        base = {r["player_id"]: int(r["built"]) for r in rs}
        pairs = [(a, b) for i, a in enumerate(rs) for b in rs[i + 1:] if abs(G.adp(a) - G.adp(b)) <= G.DECISION and a["slot"] != b["slot"]]
        for name, tf in versions.items():
            its = items(rs, window, tier_of=tf)
            o, rank = {}, 0
            for t in sorted({i["t"] for i in its}):
                for f in ("VALUE", "", "PRICEY"):
                    for i in T.rule_sort([i for i in its if i["t"] == t and i["r"]["flag"] == f], T.RULE_STEPS[window][t]):
                        rank += 1
                        o[i["r"]["player_id"]] = rank
            for a, b in pairs:
                cf = o[a["player_id"]] < o[b["player_id"]]
                if cf == (base[a["player_id"]] < base[b["player_id"]]):
                    continue
                first, second = (a, b) if cf else (b, a)
                g = first["slot"] - second["slot"]
                res[name][0][d].append(g)
                res[name][1][a["player_id"]].append(g)
                res[name][1][b["player_id"]].append(g)
    return res


def policy(label):
    if label.startswith("RULE"):
        return "RULE"
    if "check pending" in label or label.startswith("LEAN"):
        return "eligible (listed before testing)" + ("; RULE numbers, check pending" if "check pending" in label else "")
    return ""


def main():
    H = G.load()
    x = Q.x_values(H)
    cuts = [("6", "am", "primary", "6-drafter AM, primary (7 nights)"), ("6", "pm", None, "6-drafter PM (14 nights)"),
            ("6", "am", "secondary", "6-drafter AM, secondary (context only)"),
            ("4", "am", None, "4-drafter AM (small slates)"), ("4", "pm", None, "4-drafter PM (small slates)")]
    groups = [("T1", {1}), ("T2", {2}), ("T3/T4 (middle)", {3, 4}), ("T3", {3}), ("T4", {4}), ("T5 (drafted)", {5})]
    out = ["# NBA per-tier ranking rules (step 6)", "",
           "Written by scripts/nba_tier_rules.py. Each candidate against the Tiers button's current order inside the tier: "
           "points per pair on the decision pairs they order differently (positive: the candidate beat the button), with the "
           "80% range from resampling slates, pairs, and the evidence level; then the candidate's own points per pair over "
           "every decision pair in the tier (the button's own is in the header). A scratch is scored through his swap. "
           "Every candidate was listed before testing, so a LEAN is eligible for adoption; what is adopted, provisional or in the "
           "shadow is in leans.json, and everything adopted is provisional until its money verdict (decision_register.csv).", ""]
    for pod, window, sample, title in cuts:
        rows = [r for r in H if r["pod"] == pod and r["window"] == window and (sample is None or r["sample"] == sample)
                and (r["tier"] != "5" or (num(r["adp"]) is not None and num(r["adp"]) < G.cap(r)))]
        out += ["## " + title, ""]
        for gname, tier in groups:
            res, base_own = grade_orders(rows, window, tier, x)
            if not base_own:
                continue
            out += ["### %s (the button's own: %+.2f per pair over %d decision pairs)" % (gname, sum(base_own) / len(base_own), len(base_own)), "",
                    "| Candidate | Against the button | Own points per pair | Policy |", "|---|---|---|---|"]
            for name in [n for n, _ in candidates(tier, window)] + ["X for Q-tagged players"]:
                per, pl, own = res[name]
                v = G.verdict(per, pl)
                if sample == "secondary":
                    pol = "context"
                elif window == "am" and sample == "primary" and v[4].startswith("RULE"):
                    pol = "RULE"
                else:
                    pol = policy(v[4]) if v[4].startswith(("LEAN", "RULE")) and v[1] is not None and v[1] > 0 else ""
                out.append("| %s | %s | %s | %s |" % (name, G.fmt(v) if v[0] else "same order", "%+.2f" % (sum(own) / len(own)) if own else "-", pol))
            out.append("")
        lv = ladder_versions(rows, window)
        out += ["### Combining the ladders (every decision pair, against the one-tier cap)", "", "| Version | Against the one-tier cap | Policy |", "|---|---|---|"]
        for name, (per, pl) in lv.items():
            v = G.verdict(per, pl)
            pol = "context" if sample == "secondary" else policy(v[4]) if v[4].startswith(("LEAN", "RULE")) and v[1] > 0 else ""
            out.append("| %s | %s | %s |" % (name, G.fmt(v), pol))
        out.append("")
    open(OUT, "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
