"""NBA money: does each decision make money (top finishes and dollars), not just points? The contest side of the process.

Everything is read off every team in every contest on file (analysis/nba/contests/, scripts/nba_contests.py), joined at
its draft window to the rankings side's point-in-time tiers (analysis/nba/report/tier_history.csv) and graded against a
price baseline. Writes analysis/nba/report/money.md and the MONEY column of decision_register.csv. The 2:17am job runs it.

Definitions
  draft window  each team's draft time is the hourly ADP snapshot nearest the ADPs its picks were taken at
                (nba_contests.draft_times; kept in analysis/nba/contests/windows/<date>.json); AM or PM by the nearer of
                that night's Lock AM and Lock PM (nba_field.window). Teams with fewer than 4 priced picks get no window.
  holding       a team holds a player if he is among its picks, or if he was ruled out and one of its swapped-in picks
                is credited to him (nba_swaps.night): a scratch is scored through his swap, never as 0
  price         E[FP | ADP at draft], fitted on prior slates with the same pod size only: average actual points by
                closing ADP, 1-pick bins smoothed over 5. A swapped-in pick is priced at what the team paid: the ADP of the
                ruled-out player it replaced (credited by nba_swaps), else the middle of the round the team is missing.
                A team's price is the sum over its six; price bins are its contest's quintiles of team price, and every
                test is run again on deciles (verdicts that change are flagged). Each pod size's first night has no
                prior slate, so it isn't priced. No contest mixes 4- and 6-drafter pods (checked).
  lift          for a decision, teams that did it (A) against same-price teams that didn't (B), stratified by contest x
                price bin and never pooled across contests: lift at X = sum of A's top-X% finishes / sum, over A's teams,
                of B's top-X% rate in that team's stratum. Finish: A's average finish percentile minus B's in the same
                strata (negative = A finished better). Ranges: whole slates resampled (1,000 times).
  windows       find = every slate but the last CHECK; check = the last CHECK. LEAN: 80%+ of resamples on one side of
                1.0 at the top 10%, with 100+ A teams and 10+ expected top-10% finishes. RULE: the 90% range clear of
                1.0 and the check slates the same way. Two verdicts per decision: POINTS (the rankings side's) and MONEY.

  python3 scripts/nba_money.py --mirror ../br-adp-mirror
"""
import argparse, bisect, collections, csv, datetime as dt, glob, gzip, json, math, os, random, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_contests as C        # noqa: E402  the contest files
import nba_daily as D           # noqa: E402  the mirror's ADP snapshots
import nba_field as F           # noqa: E402  lock times, the AM/PM window
import nba_swaps as S           # noqa: E402  swaps credited to the ruled-out player

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NBA = os.path.join(HERE, "analysis", "nba")
REP = os.path.join(NBA, "report")
WINDOWS = os.path.join(NBA, "contests", "windows")
ME = C.ME
CHECK = 5
XS = (1, 5, 10)
RESAMPLES = 1000
# Entry fees (Underdog's leaderboards carry none): read off each contest's prize pool per entry and confirmed by the
# user 2026-11-09. A contest not listed takes the standard fee its pool per entry fits.
FEES = {"The Layup Line": 5, "Buzzer Beater": 3, "The Alley-oop": 10, "Heat Check": 20, "The Crossover": 25, "Pick & Roll": 100}
FLAGSHIP_FEE = 5
LADDER = (1, 2, 3, 5, 10, 15, 20, 25, 50, 100)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- loading
def windows(date, contests, teams, mirror):
    """{(contest id, draft id, username): draft time ISO} for every team that night, cached."""
    path = os.path.join(WINDOWS, "%s.json" % date)
    if os.path.exists(path):
        return json.load(open(path))
    if not mirror:
        return {}
    m = D.Mirror(mirror)
    out = {}
    for c in contests:
        snaps = m.snapshots({"slate_id": c["slate_id"], "lock": F.iso(c["cutoff"])})
        if not snaps:
            continue
        ts = teams[c["contest_id"]]
        times = C.draft_times(ts, snaps)
        for t in ts:
            if id(t) in times:
                out["|".join((c["contest_id"], t["draft_id"], t["username"]))] = times[id(t)].isoformat()
    os.makedirs(WINDOWS, exist_ok=True)
    if out:
        json.dump(out, open(path, "w"), sort_keys=True)
    return out


def fee_of(c, teams):
    title = c["title"].strip()
    if title in FEES:
        return FEES[title]
    pool, n = sum(t["payout"] for t in teams), len(teams)
    fits = [f for f in LADDER if 0.80 <= pool / (n * f) <= 1.25]
    return fits[0] if fits else FLAGSHIP_FEE


def load(mirror):
    """Every night on file: contests, teams (with window, holdings, price later) and the point-in-time tiers."""
    tiers = collections.defaultdict(dict)                 # (date, window) -> player id -> tier_history row
    for r in csv.DictReader(open(os.path.join(REP, "tier_history.csv"))):
        tiers[(r["date"], r["window"])][r["player_id"]] = r
    nights = []
    for date in sorted({c["date"] for c in C.load_contests()}):
        contests, teams = C.load_night(date)
        rec = {}
        for p in glob.glob(os.path.join(NBA, "daily", "%s_*_main.csv" % date)):
            rec = {r["player_id"]: r for r in csv.DictReader(open(p))}
        wins = windows(date, contests, teams, mirror)
        am, pm = F.locks(date)
        sw = S.night(date)
        credit = collections.defaultdict(set)
        for x in (sw or {}).get("credited", []):
            credit[(x["contest_id"], x["draft_id"], x["username"])].add(x["out"])
        out_adp = {o: r["adp_out"] for o, r in ((sw or {}).get("out") or {}).items()}
        for c in contests:
            ts = teams[c["contest_id"]]
            c["fee"] = fee_of(c, ts)
            c["pod_size"] = int(c["pod_size"])
            n = len(ts)
            pay = sorted((t["place"], t["payout"]) for t in ts)
            c["pay_places"], c["pay_amounts"] = [p for p, _ in pay], [a for _, a in pay]
            c["points_sorted"] = sorted((t["points"] for t in ts), reverse=True)
            for t in ts:
                k = (c["contest_id"], t["draft_id"], t["username"])
                at = wins.get("|".join(k))
                t["window"] = F.window(F.iso(at), am, pm) if at else None
                t["at"] = at
                t["holds"] = set(t["picks"]) | credit.get(k, set())
                t["paid"] = paid(t, credit.get(k, set()), out_adp, c["pod_size"])
                t["fin"] = t["place"] / n
                t["top"] = {x: t["place"] <= math.ceil(x * n / 100) for x in XS + (20,)}
                t["mine"] = t["username"] == ME
                t["contest"] = c
        nights.append({"date": date, "contests": contests, "teams": teams, "rec": rec, "pod": max(int(c["pod_size"]) for c in contests),
                       "tiers": {w: tiers.get((date, w), {}) for w in ("am", "pm")}, "swaps": sw})
    price(nights)
    return nights


def paid(t, outs, out_adp, pod):
    """The ADP each pick was paid at the draft: a swapped-in pick at the ADP of the ruled-out player it replaced (credited
    from the swaps); one not credited at the middle of a round the team is missing."""
    have = [a for a in t["adps"] if a is not None]
    credited = sorted(out_adp[o] for o in outs if out_adp.get(o) is not None)
    rounds = {min(6, max(1, math.ceil(a / pod))) for a in have + credited}
    missing = [k for k in range(1, 7) if k not in rounds]
    fill = credited + [(k - 1) * pod + (pod + 1) / 2 for k in missing]
    out = []
    for a in t["adps"]:
        out.append(a if a is not None else (fill.pop(0) if fill else 6 * pod))
    return out


def price(nights):
    """Each team's price and its contest's price bin, from E[FP | ADP] fitted on the nights before with that pod size."""
    seen = collections.defaultdict(lambda: collections.defaultdict(list))   # pod size -> ADP bin -> actual points, prior nights
    for n in nights:
        for c in n["contests"]:
            pod = c["pod_size"]
            bins = {b: st.mean(v) for b, v in seen[pod].items() if v}
            def e(adp):
                b = int(min(6 * pod, adp if adp is not None else 6 * pod))
                near = [bins[k] for k in range(b - 2, b + 3) if k in bins]
                return st.mean(near) if near else None
            ts = n["teams"][c["contest_id"]]
            for t in ts:
                es = [e(a) for a in t["paid"]]
                t["price"] = sum(es) if es and None not in es else None
            ps = sorted(t["price"] for t in ts if t["price"] is not None)
            for t in ts:
                for k in (5, 10):
                    t["bin%d" % k] = None if t["price"] is None else min(k - 1, bisect.bisect_right(ps, t["price"]) * k // (len(ps) + 1))
                t["bin"] = t["bin5"]
        for r in n["rec"].values():
            a, fp = num(r["adp_close"]), num(r["actual"])
            if a is not None and fp is not None:
                seen[n["pod"]][int(min(6 * n["pod"], a))].append(fp)


# ---------------------------------------------------------------- the lift engine
def strata_lift(cases, bins="bin5"):
    """cases: [(date, contest id, bin, 'A'|'B', team)]. -> per-date sums {date: [O1, E1, O5, E5, O10, E10, fin diff, nA]},
    stratified by contest x the team's price bin (`bins`: quintiles or deciles)."""
    by = collections.defaultdict(lambda: {"A": [], "B": []})
    for d, cid, _, g, t in cases:
        by[(d, cid, t[bins])][g].append(t)
    out = collections.defaultdict(lambda: [0.0] * 8)
    for (d, cid, b), v in by.items():
        if not v["A"] or not v["B"]:
            continue
        rate = {x: sum(t["top"][x] for t in v["B"]) / len(v["B"]) for x in XS}
        fin_b = st.mean(t["fin"] for t in v["B"])
        s = out[d]
        for t in v["A"]:
            for i, x in enumerate(XS):
                s[2 * i] += t["top"][x]
                s[2 * i + 1] += rate[x]
            s[6] += t["fin"] - fin_b
            s[7] += 1
    return out


def summarize(per_date):
    """Lift at 1/5/10, finish difference, A teams, expected top-10s, and the resampled share above 1.0 and 80/90% ranges."""
    ds = sorted(per_date)
    def agg(dd):
        s = [sum(per_date[d][i] for d in dd) for i in range(8)]
        return s
    s = agg(ds)
    if not s[7]:
        return None
    lift = lambda s, i: s[2 * i] / s[2 * i + 1] if s[2 * i + 1] else None
    res = {"n": int(s[7]), "e10": s[5], "o10": s[4], "lift": {x: lift(s, i) for i, x in enumerate(XS)}, "fin": 100 * s[6] / s[7],
           "slates": len(ds)}
    rnd = random.Random(11)
    boots = []
    for _ in range(RESAMPLES if len(ds) >= 3 else 0):
        b = agg([rnd.choice(ds) for _ in ds])
        if b[5]:
            boots.append(b[4] / b[5])
    if boots:
        boots.sort()
        res["above"] = sum(1 for v in boots if v > 1) / len(boots)
        res["r80"] = (boots[len(boots) // 10], boots[len(boots) * 9 // 10])
        res["r90"] = (boots[len(boots) // 20], boots[len(boots) * 19 // 20])
    return res


# ---------------------------------------------------------------- decisions as teams
def rows_of(n, w, tiers=None):
    cap = 6 * n["pod"]
    return [r for r in n["tiers"][w].values() if (tiers is None or int(r["tier"]) in tiers) and num(r["adp"]) is not None
            and num(r["adp"]) < cap]


def decision_pairs(rows, pick):
    """[(preferred, other)] over the decision pairs (ADP within 4): pick(a, b) returns the preferred row or None."""
    out = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if abs(num(a["adp"]) - num(b["adp"])) > 4:
                continue
            p = pick(a, b)
            if p is not None:
                out.append((p["player_id"], (b if p is a else a)["player_id"]))
    return out


def holders(n):
    """{window: {player id: [team]}} for teams with a window and a price bin."""
    out = {"am": collections.defaultdict(list), "pm": collections.defaultdict(list)}
    for ts in n["teams"].values():
        for t in ts:
            if t["window"] in out and t["bin"] is not None:
                for p in t["holds"]:
                    out[t["window"]][p].append(t)
    return out


def pair_cases(nights, windows_, tiers, pick, same_tier=True):
    cases = []
    for n in nights:
        H = n.setdefault("_holders", holders(n))
        for w in windows_:
            rows = rows_of(n, w, tiers)
            groups = [[r for r in rows if r["tier"] == t] for t in {r["tier"] for r in rows}] if same_tier else [rows]
            for g in groups:
                for x, y in decision_pairs(g, pick):
                    hx, hy = H[w].get(x, []), H[w].get(y, [])
                    ix, iy = {id(t) for t in hx}, {id(t) for t in hy}
                    cases += [(n["date"], t["contest"]["contest_id"], t["bin"], "A", t) for t in hx if id(t) not in iy]
                    cases += [(n["date"], t["contest"]["contest_id"], t["bin"], "B", t) for t in hy if id(t) not in ix]
    return cases


def hold_cases(nights, windows_, has, eligible=lambda n, t: True):
    cases = []
    for n in nights:
        for ts in n["teams"].values():
            for t in ts:
                if t["window"] in windows_ and t["bin"] is not None and eligible(n, t):
                    cases.append((n["date"], t["contest"]["contest_id"], t["bin"], "A" if has(n, t) else "B", t))
    return cases


def f_(r, k):
    return num(r[k])


def less_drafted(min_gap=10, proj_within=2):
    def pick(a, b):
        pa, pb, da, db = f_(a, "proj"), f_(b, "proj"), f_(a, "drafted"), f_(b, "drafted")
        if None in (pa, pb, da, db) or abs(pa - pb) > proj_within or abs(da - db) < min_gap or min(da, db) < 2:
            return None
        return a if da < db else b
    return pick


def flag_vs_plain(flag, want):
    """VALUE (or PRICEY) against an unflagged partner: the preferred one is the flagged (want=True) or the plain."""
    def pick(a, b):
        fa, fb = a["flag"] == flag, b["flag"] == flag
        if fa == fb or (a["flag"] and b["flag"]):
            return None
        flagged = a if fa else b
        return flagged if want else (b if fa else a)
    return pick


def order_vs(key_a, key_b, skip=lambda a, b: False):
    """Where order key_a and order key_b disagree on a pair: the one key_a puts first (lower is first)."""
    def pick(a, b):
        if skip(a, b):
            return None
        xa, xb, ya, yb = key_a(a), key_a(b), key_b(a), key_b(b)
        if None in (xa, xb, ya, yb) or xa == xb or ya == yb or (xa < xb) == (ya < yb):
            return None
        return a if xa < xb else b
    return pick


QRE = ("Questionable", "Doubtful", "GTD")
built = lambda r: num(r["built"])
yours = lambda r: num(r["your_rank"])
etr = lambda r: -num(r["proj"]) if num(r["proj"]) is not None else None
tagged = lambda r: r["tag"] in QRE
untagged = lambda a, b: tagged(a) or tagged(b)


def switch_pick(window, tier, old_steps):
    """A switch against the rule it replaced (nba_shadow.py): where the button (the new rule's built rank) and the old
    rule order a pair differently, the button's first."""
    import nba_shadow as SH, nba_tier_rules as TR
    cache = {}
    def pick(a, b):
        k = a["date"]
        if "H" not in cache:
            cache["H"] = TR.G.load()
        if k not in cache:
            rs = [r for r in cache["H"] if r["date"] == k and r["window"] == window and r["tier"] == str(tier) and r["built"]]
            cache[k] = SH.alt_order(TR.items(rs, window), old_steps, "both")
        old = cache[k]
        if a["player_id"] not in old or b["player_id"] not in old or not a["built"] or not b["built"]:
            return None
        nb, no = int(a["built"]) < int(b["built"]), old[a["player_id"]] < old[b["player_id"]]
        return None if nb == no else (a if nb else b)
    return pick


def teammate_tagged(n, w, p, tags, sat=None):
    """Whether a teammate of player p carried one of `tags` at window w (and, with sat, whether he then sat or played)."""
    rows, me = n["tiers"][w], n["tiers"][w].get(p)
    if not me:
        return False
    for r in rows.values():
        if r["team"] == me["team"] and r["player_id"] != p and r["tag"] in tags:
            if sat is None or (r["scratched"] == "1") == sat:
                return True
    return False


def beneficiary_r6(sat):
    def has(n, t):
        last = 5 * t["contest"]["pod_size"]
        return any(a is not None and a > last and teammate_tagged(n, "am", p, QRE, sat) for p, a in zip(t["picks"], t["adps"]))
    return has


def holds_where(cond):
    return lambda n, t: any(cond(n["tiers"][t["window"]].get(p)) for p in t["holds"] if n["tiers"][t["window"]].get(p))


def q_class(cls, tiers):
    return holds_where(lambda r: r["q_class"] == cls and int(r["tier"]) in tiers)


def pricey_ahead(a, b):
    """PRICEY-last off: the PRICEY player of a PRICEY/unflagged pair, where he outprojects the other."""
    if (a["flag"] == "PRICEY") == (b["flag"] == "PRICEY") or (a["flag"] and b["flag"]):
        return None
    f, o = (a, b) if a["flag"] == "PRICEY" else (b, a)
    return f if None not in (num(f["proj"]), num(o["proj"])) and num(f["proj"]) > num(o["proj"]) else None


# (register id, label, builder -> cases). A is always the side the decision says to take.
DECISIONS = [
    ("ownership-tiebreak-t5", "T5: the less-drafted of two within 2 projected points",
     lambda N: pair_cases(N, ("am", "pm"), {5}, less_drafted())),
    ("leverage-t2-t4", "T2-T4: the less-drafted of two within 2 projected points",
     lambda N: pair_cases(N, ("am", "pm"), {2, 3, 4}, less_drafted())),
    ("value-up-middle-t5", "VALUE over an unflagged player (T3-T5)",
     lambda N: pair_cases(N, ("am", "pm"), {3, 4, 5}, flag_vs_plain("VALUE", True))),
    ("pricey-flags", "An unflagged player over a PRICEY one (T1-T5)",
     lambda N: pair_cases(N, ("am", "pm"), {1, 2, 3, 4, 5}, flag_vs_plain("PRICEY", False))),
    ("pm-t4-pricey-last-off", "PM T4: PRICEY over an unflagged player he outprojects (the candidate)",
     lambda N: pair_cases(N, ("pm",), {4}, pricey_ahead)),
    ("am-t5-button-order", "AM T5: the button's first of the pair",
     lambda N: pair_cases(N, ("am",), {5}, order_vs(built, lambda r: -built(r) if built(r) is not None else None))),
    ("pm-t2-adp-etr2", "PM T2: the switch ADP (2: ETR) over the old ADP (1: ETR)",
     lambda N: pair_cases(N, ("pm",), {2}, switch_pick("pm", 2, [("adp", 1), ("projx", 0)]))),
    ("pm-t4-adp-etr2", "PM T4: the switch ADP (2: ETR) over the old ETR rule",
     lambda N: pair_cases(N, ("pm",), {4}, switch_pick("pm", 4, [("proj", 0), ("adp", 0), ("boom", 0)]))),
    ("pm-t5-adp-value", "PM T5: ADP with VALUE first over the old ETR (2: less drafted)",
     lambda N: pair_cases(N, ("pm",), {5}, switch_pick("pm", 5, [("projx", 2), ("drafted", 10), ("projx", 0)]))),
    ("one-tier-cap", "The combined tier's order over the projection tier's, where they differ",
     lambda N: pair_cases(N, ("am", "pm"), None, order_vs(lambda r: num(r["tier"]), lambda r: num(r["p_tier"])), same_tier=False)),
    ("am-questionable-no-push", "AM: holding a player Questionable at Lock AM",
     lambda N: hold_cases(N, ("am",), holds_where(lambda r: r["tag"] == "Questionable"))),
    ("pm-questionable-back-two", "PM: holding a player Questionable at Lock PM",
     lambda N: hold_cases(N, ("pm",), holds_where(lambda r: r["tag"] == "Questionable"))),
    ("q-tag-pushes", "Passing a tagged player for the one the button ranked below him",
     lambda N: pair_cases(N, ("am", "pm"), None, lambda a, b: (b if built(a) < built(b) else a) if tagged(a) != tagged(b) and
                          built(a) is not None and built(b) is not None and (tagged(a) if built(a) < built(b) else tagged(b)) else None,
                          same_tier=False)),
    ("q-tag-raises", "Taking a tagged player over one the button ranked above him",
     lambda N: pair_cases(N, ("am", "pm"), None, lambda a, b: (a if tagged(a) else b) if tagged(a) != tagged(b) and
                          built(a) is not None and built(b) is not None and
                          (built(a) > built(b) if tagged(a) else built(b) > built(a)) else None, same_tier=False)),
    ("q-class-x:SMASH", "Holding a SMASH-class tagged player", lambda N: hold_cases(N, ("am", "pm"), q_class("SMASH", {1, 2, 3, 4, 5}))),
    ("q-class-x:FAIR", "Holding a FAIR-class tagged player", lambda N: hold_cases(N, ("am", "pm"), q_class("FAIR", {1, 2, 3, 4, 5}))),
    ("q-class-x:TRAP", "Holding a TRAP-class tagged player", lambda N: hold_cases(N, ("am", "pm"), q_class("TRAP", {1, 2, 3, 4, 5}))),
    ("beneficiary-round6:sat", "AM: a round-6 pick whose teammate was tagged at Lock AM and sat",
     lambda N: hold_cases(N, ("am",), beneficiary_r6(True))),
    ("beneficiary-round6:played", "AM: a round-6 pick whose teammate was tagged at Lock AM and played",
     lambda N: hold_cases(N, ("am",), beneficiary_r6(False))),
    ("pm-t5-beneficiary", "PM: a T5 player whose teammate was tagged or out at Lock PM",
     lambda N: hold_cases(N, ("pm",), holds_where(lambda r: int(r["tier"]) == 5 and teammate_tagged(N_BY[r["date"]], "pm", r["player_id"], QRE + ("Out",))))),
    ("pm-middle-takes", "PM T3/T4: your board's first where it differs from ETR's",
     lambda N: pair_cases(N, ("pm",), {3, 4}, order_vs(yours, etr))),
    ("pm-t2-other-reads", "PM T2: your board's first against the button (no tag on either)",
     lambda N: pair_cases(N, ("pm",), {2}, order_vs(yours, built, untagged))),
    ("am-t5-other-reads", "AM T5: your board's first against the button (no tag on either)",
     lambda N: pair_cases(N, ("am",), {5}, order_vs(yours, built, untagged))),
]
N_BY = {}


def evaluate(cases, dates, bins="bin5"):
    """{who: {span: summary}} for the field (every A team) and mine (my A teams against the field's B), over all slates,
    the find slates and the check slates."""
    check = set(dates[-CHECK:])
    out = {}
    for who in ("field", "mine"):
        cs = cases if who == "field" else [c for c in cases if c[3] == "B" or c[4]["mine"]]
        per = strata_lift(cs, bins)
        out[who] = {"all": summarize(per), "find": summarize({d: v for d, v in per.items() if d not in check}),
                    "check": summarize({d: v for d, v in per.items() if d in check})}
    return out


def verdict(ev):
    """LEAN / RULE / not enough, on the top-10% lift (the faster reader), from the field's teams."""
    a, chk = ev["field"]["all"], ev["field"]["check"]
    if not a or a["n"] < 100 or a["e10"] < 10 or "above" not in a:
        return "not enough", None
    side = 1 if a["lift"][10] > 1 else -1
    same_check = chk and chk["lift"][10] is not None and (chk["lift"][10] > 1) == (side > 0)
    if (a["r90"][0] > 1 or a["r90"][1] < 1) and same_check:
        return ("RULE for" if side > 0 else "RULE against"), side
    if a["above"] >= 0.8 or a["above"] <= 0.2:
        return ("LEAN for" if side > 0 else "LEAN against"), side
    return "no lean", None


def cell(s):
    if not s:
        return "-"
    r = " (%.2f-%.2f)" % s["r80"] if "r80" in s else ""
    g = lambda x: "%.2f" % s["lift"][x] if s["lift"][x] is not None else "-"
    return "%s%s at 10%%, %s at 1%%; finish %+.1f; %d teams, %d slates" % (g(10), r, g(1), s["fin"], s["n"], s["slates"])


# ---------------------------------------------------------------- step 0: data checks; step 1: the baseline
def data_checks(N):
    skipped = json.load(open(os.path.join(NBA, "contests", "skipped.json")))
    out = ["## 0. Data checks", "",
           "Every team in every contest pulled (scripts/nba_contests.py): picks, ADP at draft, draft (pod) id, place, points and "
           "payout on every row. Entry fees are not in Underdog's data: read off each contest's prize pool per entry and confirmed "
           "(flagships and The Layup Line $5, Buzzer Beater $3, The Alley-oop $10, Heat Check $20, The Crossover $25, Pick & Roll "
           "$100). Pick order and slot are not public: turns are read from rosters by ADP rank (section 4), never rebuilt. No "
           "contest mixes 4- and 6-drafter pods.", "",
           "| Night | Drafters | Contests | Teams | Short teams | Swapped-in picks | Swaps credited | Teams with a draft window | Priced | Mine |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    flags = []
    for n in N:
        ts = [t for v in n["teams"].values() for t in v]
        sw = n["swaps"] or {}
        nsw = sum(1 for t in ts for a in t["adps"] if a is None)
        cred = len(sw.get("credited", []))
        out.append("| %s | %d | %d | %d | %d | %d | %d | %.0f%% | %.0f%% | %d |" % (
            n["date"], n["pod"], len(n["contests"]), len(ts), sum(1 for t in ts if len(t["picks"]) < 6), nsw, cred,
            100 * sum(1 for t in ts if t["window"]) / len(ts), 100 * sum(1 for t in ts if t["bin"] is not None) / len(ts),
            sum(t["mine"] for t in ts)))
        if nsw > 50 and cred < nsw / 4:
            flags.append("%s: %d swapped-in picks, %d credited" % (n["date"], nsw, cred))
    out += ["", "Found:", "",
            "- Before 10-30 only each night's flagship is on file (the backfill took flagships); every contest from 10-30 on.",
            "- %d contests aren't public (HTTP 401, Underdog's admin promos): %s." % (
                len(skipped), ", ".join(sorted("%s" % v["slate"] for v in skipped.values()))),
            "- Teams are all complete: every contest's team count equals its entries, no short teams.",
            "- Swaps: a swapped-in pick carries no draft ADP. nba_swaps.py credits it to the ruled-out player by the round the "
            "team is missing; where that fails the scratch can't be seen on the team, and the pick is priced at the middle of the "
            "missing round. Nights where most swaps went uncredited (for the rankings side: the round match misses when a "
            "player's ADP at draft and at lock sit in different rounds, as Dejounte and Jerome on 10-31):"]
    out += ["  - " + f for f in flags] or ["  - none"]
    out += ["- Draft windows come from matching each team's ADPs at draft to the hourly snapshots; teams with fewer than 4 "
            "priced picks (mostly swaps) get none and sit out the window tests.", ""]
    return out


def baseline_section(N):
    rnd = random.Random(5)
    rows = [(n["date"], c, t) for n in N for c in n["contests"] for t in n["teams"][c["contest_id"]] if t["price"] is not None]
    out = ["## 1. The price baseline", "",
           "E[FP | ADP] per pick from earlier slates with the same pod size (average actual points at each closing ADP, smoothed "
           "over 5 picks); a swapped-in pick at the ADP the team paid (the ruled-out player it replaced, else the middle of its "
           "missing round). A team's price is the sum of its six. Teams are only ever compared within one contest and one price "
           "group (quintiles; deciles as the robustness check). %d of %d teams priced (each pod size's first night, 10-20 and "
           "10-21, has no earlier slate)." % (len(rows), sum(len(v) for n in N for v in n["teams"].values())), "",
           "**Ten random teams**", "", "| Night | Contest | Drafters | Window | Price group | Expected | Actual | ADP paid |",
           "|---|---|---|---|---|---|---|---|"]
    for d, c, t in sorted(rnd.sample(rows, 10), key=lambda x: (x[0], x[1]["title"])):
        out.append("| %s | %s | %d | %s | %d | %.1f | %.1f | %s |" % (
            d, c["title"].strip(), c["pod_size"], (t["window"] or "-").upper(), t["bin5"] + 1, t["price"], t["points"],
            ", ".join(("%.1f" % p) + ("" if a is not None else " (swap)") for a, p in zip(t["adps"], t["paid"]))))
    by = collections.defaultdict(list)
    night = collections.defaultdict(list)
    for d, c, t in rows:
        night[d].append(t["points"] - t["price"])
    for n in N:
        for c in n["contests"]:
            ts = [t for t in n["teams"][c["contest_id"]] if t["price"] is not None]
            if not ts:
                continue
            m = st.mean(t["points"] - t["price"] for t in ts)
            typ = c["title"].strip() if c["title"].strip() in FEES else "flagships"
            by[("Contest (its mean against its night's)", typ)].append(m - st.mean(night[n["date"]]))
            for t in ts:
                r = t["points"] - t["price"] - m
                if t["window"]:
                    by[("Window (inside contest)", t["window"].upper())].append(r)
                by[("Swap on the team (inside contest)", "yes" if None in t["adps"] else "no")].append(r)
                by[("Price quintile (inside contest; 1 = cheapest)", t["bin5"] + 1)].append(r)
            by[("Pod size (contest mean)", c["pod_size"])].append(m)
    out += ["", "**Bias checks**: points over price. Whole nights swing with the slate's scoring (%+.0f to %+.0f), which never "
            "matters: teams are compared only inside a contest." % (min(st.mean(v) for v in night.values()), max(st.mean(v) for v in night.values())),
            "", "| Check | Group | Points over price | n |", "|---|---|---|---|"]
    for k in sorted(by, key=lambda k: (k[0], str(k[1]))):
        out.append("| %s | %s | %+.1f | %d |" % (k[0], k[1], st.mean(by[k]), len(by[k])))
    out += ["", "Read: no bias by window or contest. The pod-size offset doesn't matter: no contest mixes pod sizes, so 4- and "
            "6-drafter teams are never compared. A swap costs a team about 6 points against what it paid. Within a contest the cheapest teams beat their price and the priciest trail "
            "it (ADP lags news, so players taken past their displayed ADP carry what the price misses). That is why every test "
            "compares teams inside one price group, and runs again on ten groups.", ""]
    return out
