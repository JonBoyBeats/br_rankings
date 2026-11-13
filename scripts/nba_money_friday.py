"""The Friday report's contest results (asked 2026-11-13; first report 2026-11-20). Writes analysis/nba/report/money_friday.json,
which the rankings side's Friday report reads. Runs in its own Friday job (.github/workflows/nba_friday.yml) after the
nightly record, so the nightly money step doesn't grow. Results only: nothing here writes the register or the button.

Every test is read over every night on file, as multiples against the whole field in the same contest and price quintile
(top 1%, top 10%, cash; counts and an 80% range: nba_money.field_multiple), for the season and since its rule went in. Rule
dates come from analysis/nba/report/rule_dates.json (kept by the rankings side: {rule id: {"since", "windows": {am, pm},
"what"}}); each group names its rule (RULES), and "since" counts a team from the first night its window ran that rule. A
group with no rule shows the season only.

  t2-turns              the 1/2- and 2/3-turn lines of the draft card (nba_money.turn_teams, reach_kinds), each beside
                        its turn's own average (the turn's teams together), as the turn line's multiple over the turn's
  t2-elite-break        elites: the top of T1 at the window, cut at the biggest gap in the window's projection among T1's
                        top 3-4 (always 1-3). Elite teams: the team's first player by closing-ADP rank is an elite. Its
                        round-2 pick (second by rank) in T2: ETR-leaning when T2 ranked by the window's projection puts
                        him higher than T2 by ADP, ADP-leaning when lower, agree when level. PM is the test (the break is
                        on there), AM for reference; non-elite teams beside it as context
  t3t4-boundaries       a T4 VALUE player against a T3 PRICEY one, a T4 PRICEY one against the button's top three in T5,
                        by ADP tier and flag (the 2026-11-13 button moves PRICEY players out of their combined tier):
                        pairs at one window, ADP within 4 in the same round; each side's teams
  t5-drafted            teams holding a T5 player by the share of pods that drafted him (rosters, swaps credited back), in
                        two pools: ADP T5 (ADP tier 5, the same whatever the button does) and the button's own T5 (from
                        2026-11-13 the button moves 60%+ players below its cut, so there the 60% line reads off itself),
                        10-point bands and the 60% line, all nights and by pod size; on 4-drafter nights (T5 by
                        projection on the board, no line) a 40% line as well
  t5-operator-order     T5 pairs (ADP within 4, no tag) where your board's order and the projection's differ: teams
                        holding your first against teams holding the projection's first
  q-tags                Q picks (tagged at the snapshot the team drafted at) by tier and played/sat; fallen 6+ picks
                        past the pre-tag ADP; T1-T4 teammates of a Q player by whether he sat; crowd swaps (share of
                        pods 15+ points higher after swaps) against other swap targets within 6 projected points
  swap-button           your swaps against what your PM list would have swapped to: waits for the board's swap lock
  monthly               first Friday of the month (or --monthly): the top-1% edge by tier against its share of points,
                        and duds and smashes by tier (scripts/nba_money_season2.py); otherwise last month's is carried
  proposals             the weekly MONEY verdict proposals (nba_money.proposals, as money_proposals.json was on Mondays)

  python3 scripts/nba_money_friday.py --mirror ../br-adp-mirror [--monthly]
"""
import argparse, collections, datetime as dt, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_money as M      # noqa: E402

OUT = os.path.join(M.REP, "money_friday.json")
RULE_DATES = os.path.join(M.REP, "rule_dates.json")
num = M.num
CROWD, WITHIN = 15, 6


def units_of(N):
    """[(night, team)] with a draft window and price bin."""
    return [(n, t) for n in N for ts in n["teams"].values() for t in ts if t["window"] and t["bin"] is not None]


RD = {}            # rule_dates.json, loaded in main


def since_of(rule):
    """{"am": date, "pm": date}: the first night the rule was live in each window (rule_dates.json), or None."""
    r = RD.get(rule) if rule else None
    if not isinstance(r, dict) or not r.get("since"):
        return None
    w = r.get("windows") or {}
    return {"am": w.get("am") or r["since"], "pm": w.get("pm") or r["since"]}


def read(groups, R, rule):
    """{group: {"rule", "since_dates", "season": multiples, "since": multiples or None}}; groups: {name: [(date, team)]};
    rule: the rule_dates.json id behind the group (a function of its name, or one id for all). "since" counts a team from
    the first night its window ran the rule."""
    out = {}
    for k, us in groups.items():
        us = list({id(t): (d, t) for d, t in us}.values())
        rid = rule(k) if callable(rule) else rule
        sd = since_of(rid)
        out[k] = {"rule": rid, "since_dates": sd, "season": M.field_multiple(us, R),
                  "since": M.field_multiple([(d, t) for d, t in us if d >= sd[t["window"]]], R) if sd else None}
    return out


# ---------------------------------------------------------------- T2
def t2_turns(N, R, rule):
    rk_inv = {n["date"]: {r: p for p, r in M.ranks_of(n).items()} for n in N}
    g = collections.defaultdict(list)
    for n, t, i in M.turn_teams(N):
        d = n["date"]
        g["%s turn: all" % i["turn"]].append((d, t))
        if i["kind"] == "reach" and i["turn"] == "2/3":
            toward = "higher projection" in M.reach_kinds(n, t, i, rk_inv[d])
            g["2/3 turn: reach %s projection" % ("toward" if toward else "not toward")].append((d, t))
        else:
            g["%s turn: %s" % (i["turn"], {"trust": "trust ADP"}.get(i["kind"], i["kind"]))].append((d, t))
    out = read(g, R, rule)
    for k, v in out.items():
        base = out["%s: all" % k.split(":")[0]]
        for span in ("season", "since"):
            if v[span] and base[span]:
                v[span]["vs_turn"] = {x: (round(v[span][x][0] / base[span][x][0], 2) if v[span][x][0] and base[span][x][0] else None)
                                      for x in ("top1", "top10", "cash")}
    return out


def elites(rows):
    """The window's elites: T1's top 3-4 by projection, cut at the biggest gap (1-3 players)."""
    t1 = sorted(((num(r["proj"]), p) for p, r in rows.items() if r["tier"] == "1" and num(r["proj"]) is not None), reverse=True)
    if len(t1) < 2:
        return {p for _, p in t1}
    top = t1[:4]
    gaps = [top[i][0] - top[i + 1][0] for i in range(min(3, len(top) - 1))]
    k = 1 + gaps.index(max(gaps))
    return {p for _, p in top[:k]}


def t2_elite(N, R, rule):
    g = collections.defaultdict(list)
    for n in N:
        rk = M.ranks_of(n)
        el = {w: elites(n["tiers"][w]) for w in ("am", "pm")}
        t2rank = {}
        for w in ("am", "pm"):
            t2 = [(p, r) for p, r in n["tiers"][w].items() if r["tier"] == "2" and num(r["proj"]) is not None and num(r["adp"]) is not None]
            by_proj = {p: i for i, (p, _) in enumerate(sorted(t2, key=lambda x: -num(x[1]["proj"])))}
            by_adp = {p: i for i, (p, _) in enumerate(sorted(t2, key=lambda x: num(x[1]["adp"])))}
            t2rank[w] = (by_proj, by_adp)
        for ts in n["teams"].values():
            for t in ts:
                w = t["window"]
                if not w or t["bin"] is None:
                    continue
                rs = sorted((rk[p], p) for p in M.drafted_by(t) if p in rk)
                if len(rs) < 2:
                    continue
                first, second = rs[0][1], rs[1][1]
                by_proj, by_adp = t2rank[w]
                if second not in by_proj:
                    continue
                lean = "ETR-leaning" if by_proj[second] < by_adp[second] else "ADP-leaning" if by_proj[second] > by_adp[second] else "agree"
                who = "elite" if first in el[w] else "non-elite"
                g["%s %s teams: round-2 T2 pick %s" % (w.upper(), who, lean)].append((n["date"], t))
    return read(g, R, rule)


# ---------------------------------------------------------------- T3/T4
def boundaries(N, R, rule):
    by_date = {n["date"]: n for n in N}
    top3 = {}
    for n in N:
        for w in ("am", "pm"):
            t5 = sorted((int(r["built"]), p) for p, r in n["tiers"][w].items() if r["tier"] == "5" and r["built"])
            top3[(n["date"], w)] = {p for _, p in t5[:3]}
    # by ADP tier and flag: the 2026-11-13 button moves PRICEY players out of their combined tier (rebuilt into every night)
    tests = [("T4 VALUE (A) vs T3 PRICEY (B)", lambda r: r["a_tier"] == "4" and r["flag"] == "VALUE", lambda r: r["a_tier"] == "3" and r["flag"] == "PRICEY"),
             ("T4 PRICEY (A) vs a top-3 T5 (B)", lambda r: r["a_tier"] == "4" and r["flag"] == "PRICEY",
              lambda r: r["tier"] == "5" and r["player_id"] in top3[(r["date"], r["window"])])]
    out = {}
    for name, fa, fb in tests:
        def pick(a, b, fa=fa, fb=fb):
            pod = by_date[a["date"]]["pod"]
            if math.ceil(num(a["adp"]) / pod) != math.ceil(num(b["adp"]) / pod):
                return None
            return a if fa(a) and fb(b) else b if fa(b) and fb(a) else None
        cs = M.pair_cases(N, ("am", "pm"), None, pick, same_tier=False)
        g = {name + ": A": [(c[0], c[4]) for c in cs if c[3] == "A"], name + ": B": [(c[0], c[4]) for c in cs if c[3] == "B"]}
        out.update(read(g, R, rule))
        out[name + ": A"]["slates"] = len({c[0] for c in cs if c[3] == "A"})
    return out


# ---------------------------------------------------------------- T5
POOLS = (("ADP T5", M.T5_POOL),                                   # ADP tier 5: the same pool whatever the button does
         ("button T5", lambda r: r.get("tier") == "5"))              # the button's own T5 (from 11-13: 60%+ already out)


def t5_drafted(N, R, rule):
    g = collections.defaultdict(list)
    for n in N:
        for cid, ts in n["teams"].items():
            sh = M.pod_shares(n, cid)
            pod = ts[0]["contest"]["pod_size"] if ts else None
            for t in ts:
                w = t["window"]
                if not w or t["bin"] is None:
                    continue
                for pool, inside in POOLS:
                    bands = set()
                    for p in M.drafted_by(t):
                        if not inside(n["tiers"][w].get(p) or {}):
                            continue
                        s = sh.get(p, 0)
                        b = min(90, int(s // 10) * 10)
                        bands |= {"%d-%d%%" % (b, b + 10), "under 60%" if s < M.UNDER else "60%+"}
                        if pod == 4:                 # the board runs 4-drafter T5 by projection, no line: a 40% line tested too
                            bands.add("under 40%" if s < 40 else "40%+")
                    for b in bands:
                        if b not in ("under 40%", "40%+"):
                            g["%s, all nights: %s" % (pool, b)].append((n["date"], t))
                        g["%s, %d-drafter nights: %s" % (pool, pod, b)].append((n["date"], t))
    def order(k):
        span, b = k.rsplit(": ", 1)
        line = b in ("under 40%", "40%+", "under 60%", "60%+")
        return (span, line, b if line else "", int(b.split("-")[0]) if not line else 0)
    return dict(sorted(read(g, R, rule).items(), key=lambda kv: order(kv[0])))


def t5_operator(N, R, rule):
    proj_first = lambda r: -num(r["proj"]) if num(r["proj"]) is not None else None
    cs = M.pair_cases(N, ("am", "pm"), {5}, M.order_vs(M.yours, proj_first, M.untagged))
    g = {"your first": [(c[0], c[4]) for c in cs if c[3] == "A"], "the projection's first": [(c[0], c[4]) for c in cs if c[3] == "B"]}
    out = read(g, R, rule)
    out["your first"]["slates"] = len({c[0] for c in cs})
    return out


# ---------------------------------------------------------------- Q tags
def q_tags(N, R, rule):
    g = M.q_groups(N)
    for n in N:
        tg = M.tags_of(n) or {}
        pre = tg.get("pre", {})
        for ts in n["teams"].values():
            for t in ts:
                if not t["window"] or t["bin"] is None:
                    continue
                q = M.q_at_draft(n, t)
                if not q:
                    continue
                held = M.drafted_by(t)
                for p in held:
                    if p in q and pre.get(p) is not None and q[p][0] is not None:
                        fall = q[p][0] - pre[p]
                        g["fell 6+ picks past the pre-tag ADP" if fall >= 6 else "fell under 6 picks (or rose)"].append((n["date"], t))
                qteams = collections.defaultdict(list)
                for p, (_, _, team) in q.items():
                    qteams[team].append(p)
                rows = n["tiers"][t["window"]]
                for p in held:
                    r = rows.get(p)
                    if r and r["a_tier"] in ("1", "2", "3", "4"):
                        for x in qteams.get(r["team"], []):
                            if x != p:
                                g["T%s teammate of a Q player who %s" % (r["a_tier"], "sat" if M.sat(n, x) else "played")].append((n["date"], t))
    # swaps: crowd targets against other targets within WITHIN projected points
    for n in N:
        for cid, ts in n["teams"].items():
            pods = collections.defaultdict(list)
            for t in ts:
                pods[t["draft_id"]].append(t)
            after = collections.Counter(p for ps in pods.values() for p in set().union(*(set(t["picks"]) for t in ps)))
            draft = M.pod_shares(n, cid)
            swapped = collections.defaultdict(list)
            for t in ts:
                for p, x in zip(t["picks"], t["adps"]):
                    if x is None and t["window"] and t["bin"] is not None:
                        swapped[p].append(t)
            crowd = {p for p in swapped if 100 * after[p] / len(pods) - draft.get(p, 0) >= CROWD}
            proj = lambda p: num((n["tiers"]["pm"].get(p) or n["tiers"]["am"].get(p) or {}).get("proj"))
            for c in crowd:
                for o in set(swapped) - crowd:
                    if proj(c) is not None and proj(o) is not None and abs(proj(c) - proj(o)) <= WITHIN:
                        g["crowd swap"] += [(n["date"], t) for t in swapped[c]]
                        g["off-crowd swap"] += [(n["date"], t) for t in swapped[o]]
    return read(g, R, rule)


# ---------------------------------------------------------------- monthly
def monthly(N):
    import nba_money_season as S, nba_money_season2 as S2
    TT = S.teams_of(N)
    R2 = S2.rates(TT)
    _, edge = S2.test4(TT)
    _, dud = S2.test5(TT, R2, N)
    js = lambda m: {"teams": m["teams"], **{("top%s" % x if x != "cash" else "cash"): list(m[x]) for x in (1, 10, "cash")},
                    "range80_top10": list(m["r10"]) if m["r10"] else None}
    return {"edge_by_tier": {("T" + k if k != "none" else "no tier row"): {"edge": round(v[0], 1), "edge_share": round(v[1], 3),
                                                                           "field_points": round(v[2], 1), "points_share": round(v[3], 3)}
                             for k, v in edge.items()},
            "duds_smashes": {"%s T%s" % k: js(v) for k, v in dud.items()}}


# each test's groups and the rule_dates.json rule behind them (None: no rule, season only)
RULES = {
    "t2-turns": None,
    "t2-elite-break": "t2-pm-elite-break",
    "t3t4-boundaries": lambda g: "t3-pricey-over-t4-value" if g.startswith("T4 VALUE") else "t4-pricey-to-t5",
    "t5-drafted": "t5-drafted-60",
    "t5-operator-order": "t5-drafted-60",
    "q-tags": lambda g: ("q-adp-fall" if g.startswith("fell") else "q-teammate-tiebreak" if "teammate" in g
                         else "swap-button" if "swap" in g else "q-t1-to-t2" if g.startswith("T1") else "q-keeps-tier"),
}
TESTS = (("t2-turns", "The 1/2- and 2/3-turn lines, each against its turn's average", t2_turns),
         ("t2-elite-break", "Elite teams' round-2 T2 pick: ETR-leaning, ADP-leaning or agree (PM is the test)", t2_elite),
         ("t3t4-boundaries", "T4 VALUE vs T3 PRICEY; T4 PRICEY vs T5's top three (same round; ADP tier and flag)", boundaries),
         ("t5-drafted", "Teams holding a T5 player (ADP T5 and the button's T5), by the share of pods that drafted him", t5_drafted),
         ("t5-operator-order", "T5: your order against the projection's, where they differ", t5_operator),
         ("q-tags", "Q picks, their fall, their teammates, and crowd swaps", q_tags))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(M.HERE, "..", "br-adp-mirror"))
    ap.add_argument("--monthly", action="store_true", help="run the monthly tests even if it isn't the first Friday")
    a = ap.parse_args()
    M.MIRROR_PATH = a.mirror
    N = [n for n in M.load(a.mirror) if n["tiers"]["am"] or n["tiers"]["pm"]]
    for n in N:
        for w in ("am", "pm"):
            for r in n["tiers"][w].values():
                r["window"] = w
    R = M.field_rates(N)
    RD.update(json.load(open(RULE_DATES)) if os.path.exists(RULE_DATES) else {})
    prev = json.load(open(OUT)) if os.path.exists(OUT) else {}
    tests = {}
    for k, label, f in TESTS:
        tests[k] = {"label": label, "groups": f(N, R, RULES[k])}
    tests["swap-button"] = {"label": "Your swaps against what your PM list would have swapped to", "rule": "swap-button",
                            "since_dates": since_of("swap-button"), "status": "waiting for the board's swap lock (none saved yet)",
                            "groups": {}}
    today = dt.datetime.now(M.PT).date()
    if a.monthly or today.day <= 7 or "monthly" not in prev:
        mon = dict(monthly(N), generated=today.isoformat())
    else:
        mon = prev["monthly"]
    tj_path = os.path.join(M.REP, "money_tiers.json")
    tj = json.load(open(tj_path))
    old = prev.get("proposals") or (json.load(open(os.path.join(M.REP, "money_proposals.json")))
                                    if os.path.exists(os.path.join(M.REP, "money_proposals.json")) else None)
    out = {"generated": today.isoformat(), "nights": [n["date"] for n in N],
           "notes": "Multiples against the whole field in the same contest and price quintile: [multiple, finishes, expected] for "
                    "top 1%, top 10% and cash, the top-10% 80% range from resampling nights, and team counts; 'since' covers "
                    "nights on or after the test's rule date (rule_dates.json), 'season' every night on file. Definitions: "
                    "scripts/nba_money_friday.py.",
           "tests": tests, "monthly": mon, "proposals": M.proposals(tj, old)}
    json.dump(out, open(OUT, "w"), indent=1)
    print("money_friday.json: %d tests, %d nights, monthly %s, %d proposals" % (len(tests), len(N), mon.get("generated"),
                                                                                 len(out["proposals"]["proposals"])))


if __name__ == "__main__":
    main()
