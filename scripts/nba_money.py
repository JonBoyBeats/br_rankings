"""NBA money: does each decision make money (top finishes and dollars), not just points? The contest side of the process.

Everything is read off every team in every contest on file (analysis/nba/contests/, scripts/nba_contests.py), joined at
its draft window to the rankings side's point-in-time tiers (analysis/nba/report/tier_history.csv) and graded against a
price baseline. Writes analysis/nba/report/money_report.md and money_tiers.json (the morning report's per-tier block), and on Mondays
money_proposals.json (the weekly verdict proposals the rankings side's Monday section reads). It never writes decision_register.csv: MONEY verdicts go into the
register by hand, only when the user approves them. The 2:17am job runs it.

Definitions
  draft window  each team's draft time is the hourly ADP snapshot nearest the ADPs its picks were taken at
                (nba_contests.draft_times; kept in analysis/nba/contests/windows/<date>.json.gz); AM or PM by the nearer of
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
import argparse, bisect, collections, csv, datetime as dt, glob, gzip, json, math, os, random, re, statistics as st, sys
from zoneinfo import ZoneInfo

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
PT = ZoneInfo("America/Los_Angeles")
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
    path = os.path.join(WINDOWS, "%s.json.gz" % date)
    if os.path.exists(path):
        return json.load(gzip.open(path, "rt"))
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
        json.dump(out, gzip.open(path, "wt"), sort_keys=True)
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
        swap_out = collections.defaultdict(dict)          # team -> swapped-in pick -> the ruled-out player it replaced
        for x in (sw or {}).get("credited", []):
            credit[(x["contest_id"], x["draft_id"], x["username"])].add(x["out"])
            swap_out[(x["contest_id"], x["draft_id"], x["username"])][x["swap"]] = x["out"]
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
                so = swap_out.get(k, {})
                t["paid_pid"] = [p if a is not None else so.get(p) for p, a in zip(t["picks"], t["adps"])]
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
                # each slot: who was paid for, what it cost, what it scored (a swap scores through the swapped-in player)
                t["slots"] = [(pp, x, num((n["rec"].get(p) or {}).get("actual")) or 0.0) for pp, x, p in zip(t["paid_pid"], es, t["picks"])]
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
    for c in cases:
        d, cid, b, g, t = c[:5]
        by[(d, cid, b if bins == "case" else t[bins])][g].append(t)
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
                    cases += [(n["date"], t["contest"]["contest_id"], t["bin"], "A", t, {x}) for t in hx if id(t) not in iy]
                    cases += [(n["date"], t["contest"]["contest_id"], t["bin"], "B", t, {y}) for t in hy if id(t) not in ix]
    return cases


def hold_cases(nights, windows_, has, eligible=lambda n, t: True):
    cases = []
    for n in nights:
        for ts in n["teams"].values():
            for t in ts:
                if t["window"] in windows_ and t["bin"] is not None and eligible(n, t):
                    h = has(n, t)
                    cases.append((n["date"], t["contest"]["contest_id"], t["bin"], "A" if h else "B", t,
                                  set(h) if isinstance(h, (set, list, tuple)) else set()))
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
        return {p for p, a in zip(t["picks"], t["adps"]) if a is not None and a > last and teammate_tagged(n, "am", p, QRE, sat)}
    return has


def holds_where(cond):
    """The players a team holds that meet cond at its window (empty: it holds none)."""
    return lambda n, t: {p for p in t["holds"] if n["tiers"][t["window"]].get(p) and cond(n["tiers"][t["window"]][p])}


def q_class(cls, tiers):
    return holds_where(lambda r: r["q_class"] == cls and int(r["tier"]) in tiers)


def candidate_pick(window, tier, steps, flags):
    """A shadow candidate against the button (nba_shadow.py): where the candidate's order (the tier's rule steps unless
    given, with its own flag groups) and the button's built rank disagree on a pair, the candidate's first."""
    import nba_shadow as SH, nba_tier_rules as TR, nba_tier_history as T
    cache = {}
    def pick(a, b):
        k = a["date"]
        if "H" not in cache:
            cache["H"] = TR.G.load()
        if k not in cache:
            rs = [r for r in cache["H"] if r["date"] == k and r["window"] == window and r["tier"] == str(tier) and r["built"]]
            cache[k] = SH.alt_order(TR.items(rs, window), steps or T.RULE_STEPS[window][tier], flags)
        alt = cache[k]
        if a["player_id"] not in alt or b["player_id"] not in alt or not a["built"] or not b["built"]:
            return None
        nb, na = int(a["built"]) < int(b["built"]), alt[a["player_id"]] < alt[b["player_id"]]
        return None if nb == na else (a if na else b)
    return pick


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
    ("pm-t4-pricey-last-off", "PM T4: the candidate (PRICEY-last off, VALUE first kept) where it differs from the button",
     lambda N: pair_cases(N, ("pm",), {4}, candidate_pick("pm", 4, None, "value"))),
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
        return "none"
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


# ---------------------------------------------------------------- step 2: my results
def boot_range(nights, fn, level=0.8):
    if len(nights) < 3:
        return None
    rnd = random.Random(13)
    vals = sorted(v for v in (fn([rnd.choice(nights) for _ in nights]) for _ in range(RESAMPLES)) if v is not None)
    lo = int(len(vals) * (1 - level) / 2)
    return (vals[lo], vals[-1 - lo]) if vals else None


def scoreboard(N):
    mine = []                                             # (date, contest, team)
    for n in N:
        for c in n["contests"]:
            for t in n["teams"][c["contest_id"]]:
                if t["mine"]:
                    mine.append((n["date"], c, t))
    def tails(ts):
        return {x: sum(t["top"][x] for t in ts) / len(ts) / (x / 100) for x in (1, 5, 10, 20)} if ts else None
    def money(rows):
        fees = sum(c["fee"] for _, c, _ in rows)
        won = sum(t["payout"] for _, _, t in rows)
        return fees, won
    out = ["## 2. My results", "",
           "Tail ratio: my share of teams in the top X% over X (1.00 = the field's rate). Finish: average finish percentile (lower "
           "is better; 50 = the field). Ranges 80%, resampling nights. AM and PM by each team's draft window.", "",
           "| Contest | Drafters | Nights | Teams | Top 1% | Top 5% | Top 10% | Top 20% | Finish | AM top 10% (teams) | PM top 10% (teams) | Fees | Won | ROI |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    groups = collections.defaultdict(list)
    for d, c, t in mine:
        groups[(c["title"].strip(), c["pod_size"])].append((d, c, t))
    def line(name, pod, rows, ranges=False):
        ts = [t for _, _, t in rows]
        tl = tails(ts)
        am, pm = [t for t in ts if t["window"] == "am"], [t for t in ts if t["window"] == "pm"]
        fees, won = money(rows)
        ds = sorted({d for d, _, _ in rows})
        rng = ""
        if ranges:
            r = boot_range(ds, lambda dd: (lambda ts: tails(ts)[10] if ts else None)([t for d in dd for x, _, t in rows if x == d]))
            rng = " (%.2f-%.2f)" % r if r else ""
        return "| %s | %s | %d | %d | %.2f | %.2f | %.2f%s | %.2f | %.1f | %s (%d) | %s (%d) | $%.0f | $%.0f | %+.0f%% |" % (
            name, pod, len(ds), len(ts), tl[1], tl[5], tl[10], rng, tl[20], 100 * st.mean(t["fin"] for t in ts),
            "%.2f" % tails(am)[10] if am else "-", len(am), "%.2f" % tails(pm)[10] if pm else "-", len(pm), fees, won,
            100 * (won - fees) / fees if fees else 0)
    for (name, pod), rows in sorted(groups.items(), key=lambda kv: (-kv[0][1], -len(kv[1]))):
        out.append(line(name, pod, rows))
    for pod in (6, 4):
        rows = [x for x in mine if x[1]["pod_size"] == pod]
        if rows:
            out.append(line("**all %d-drafter**" % pod, pod, rows, True))
    out.append(line("**all**", "-", mine, True))
    # money concentration
    by_night = collections.defaultdict(lambda: [0.0, 0.0])
    for d, c, t in mine:
        by_night[d][0] += c["fee"]
        by_night[d][1] += t["payout"]
    fees, won = money(mine)
    best = max(by_night, key=lambda d: by_night[d][1] - by_night[d][0])
    bf, bw = by_night[best]
    ds = sorted(by_night)
    r = boot_range(ds, lambda dd: (sum(by_night[d][1] for d in dd) - sum(by_night[d][0] for d in dd)) / sum(by_night[d][0] for d in dd))
    out += ["", "Dollars: $%.0f in fees, $%.0f won, %+.0f%% ROI over %d nights (80%% range %+.0f%% to %+.0f%%, resampling nights). "
            "Without the best night (%s, $%.0f won on $%.0f) it is %+.0f%%: the money so far rests on one top finish, so the tail "
            "ratios above are the faster reader." % (fees, won, 100 * (won - fees) / fees, len(ds), 100 * r[0], 100 * r[1], best, bw, bf,
                                                    100 * ((won - bw) - (fees - bf)) / (fees - bf)), ""]
    # concentration and uniqueness, by night
    out += ["**Concentration and uniqueness**: per night, across all my teams. Top player: my most-used player and the share of my "
            "teams with him; top pair likewise; cores: a team's three earliest picks, how many of my teams share the most-used one. "
            "Uniqueness (flagship, from the contest measures): the median share of the field holding 4+ of a team's 6, and my "
            "teams with an exact duplicate in the field.", "",
            "| Night | My teams | Top player | Top pair | Biggest shared core | Field share with 4+ of 6 (median) | Teams with a duplicate |",
            "|---|---|---|---|---|---|---|"]
    names = {}
    for n in N:
        names.update({p: r["name"] for p, r in n["rec"].items()})
    for n in N:
        ts = [t for d, _, t in mine if d == n["date"]]
        if not ts:
            continue
        pc = collections.Counter(p for t in ts for p in set(t["holds"]))
        pr = collections.Counter(tuple(sorted(x)) for t in ts for x in __import__("itertools").combinations(sorted(set(t["picks"])), 2))
        cores = collections.Counter(tuple(sorted(p for p, a in sorted(zip(t["picks"], t["paid"]), key=lambda x: x[1])[:3])) for t in ts)
        u = None
        mp = os.path.join(NBA, "contests", "%s_measures.json" % n["date"])
        if os.path.exists(mp):
            for c in json.load(open(mp))["contests"]:
                if c.get("uniqueness"):
                    u = c["uniqueness"]
                    break
        (p1, k1), (pp, k2), (cc, k3) = pc.most_common(1)[0], pr.most_common(1)[0], cores.most_common(1)[0]
        out.append("| %s | %d | %s %.0f%% | %s %.0f%% | %d (%s) | %s | %s |" % (
            n["date"], len(ts), names.get(p1, p1), 100 * k1 / len(ts), " + ".join(names.get(x, x) for x in pp), 100 * k2 / len(ts),
            k3, " + ".join(names.get(x, x) for x in cc), "%.1f%%" % u["share4_median"] if u else "-",
            "%d of %d" % (u["teams_with_dupes"], u["teams"]) if u else "-"))
    return out + [""]


# ---------------------------------------------------------------- step 3f: my swaps, replayed for money
def place_and_pay(c, team, points):
    """The place and payout `team` would have had with `points`, against the contest's other real scores (ties ignored)."""
    if "points_asc" not in c:
        c["points_asc"] = sorted(c["points_sorted"])
    ahead = len(c["points_asc"]) - bisect.bisect_right(c["points_asc"], points) - (1 if team["points"] > points else 0)
    i = bisect.bisect_left(c["pay_places"], ahead + 1)
    return ahead + 1, c["pay_amounts"][i] if i < len(c["pay_amounts"]) else 0.0


def swap_money(N):
    """Each of my credited swaps against three alternatives: my last saved board order's pick (the app shuffle's cost),
    and the swap board's pick with near-ties least drafted first (leverage) or most drafted first (spread). The team's
    points move by the difference; its place and payout are re-read off the contest's real scores."""
    import nba_swap_board as W
    res = collections.defaultdict(lambda: collections.defaultdict(list))   # alternative -> date -> [(dpoints, dtop10, ddollars)]
    conc = collections.defaultdict(list)                                    # how -> share of a night's swaps on its top target
    for n in N:
        sw = n["swaps"]
        if not sw or not sw["credited"] or n["date"] in S.EXCLUDED:
            continue
        rows, tip, out = sw["rows"], sw["tip"], sw["out"]
        mine = [x for x in sw["credited"] if x["username"] == ME]
        if not mine:
            continue
        pods = collections.defaultdict(set)
        for t in sw["all_teams"]:
            for i in range(1, 7):
                if t["p%d" % i] and t["adp%d" % i]:
                    pods[t["draft_id"]].add(t["p%d" % i])
        targets = collections.defaultdict(list)
        for x in sw["credited"]:
            targets[x["out"]].append(x["swap"])
        swap_time = {}
        for o, ts in targets.items():
            tt = [tip[rows[s]["team"]] for s in ts if s in rows and rows[s]["team"] in tip]
            swap_time[o] = min(tt) if tt else tip.get(out[o]["team"])
        sat = {p for p, r in rows.items() if r["min"] == "0.0"}
        drafted = {pid: num(r["drafted"]) or 0 for pid, r in W.tier_rows(n["date"]).get("pm", {}).items()}
        snaps = W.orders(n["date"]) or []
        team_of = {(c["contest_id"], t["draft_id"], t["username"]): (c, t) for c in n["contests"] for t in n["teams"][c["contest_id"]]}
        alt_by_team = collections.defaultdict(lambda: collections.defaultdict(float))
        picks_how = collections.defaultdict(list)
        for x in mine:
            stime = swap_time.get(x["out"])
            if stime is None or x["swap"] not in rows or num(rows[x["swap"]]["actual"]) is None:
                continue
            elig = [p for p, r in rows.items() if p not in pods[x["draft_id"]] and p not in out and p not in sat
                    and r["team"] in tip and tip[r["team"]] >= stime]
            if x["swap"] not in elig:
                elig.append(x["swap"])
            fp = num(rows[x["swap"]]["actual"])
            withproj = [p for p in elig if (num(rows[p]["etr_last"]) or 0) > 0]
            alts = {}
            saved = [s for s in snaps if W.parse(s["at"]) <= stime]
            if saved:
                rank = {p: i for i, p in enumerate(saved[-1]["order"])}
                alts["saved"] = min((p for p in elig if p in rank), key=lambda p: rank[p], default=None)
            if withproj:
                alts["low"] = W.tie_order(withproj, rows, drafted, "low")[0]
                alts["high"] = W.tie_order(withproj, rows, drafted, "high")[0]
            k = (x["contest_id"], x["draft_id"], x["username"])
            for how, p in alts.items():
                if p is not None and num(rows[p]["actual"]) is not None:
                    alt_by_team[k][how] += num(rows[p]["actual"]) - fp
                    alt_by_team[k][how + "_n"] += 1
                    picks_how[how].append(p)
        for k, d in alt_by_team.items():
            if k not in team_of:
                continue
            c, t = team_of[k]
            for how in ("saved", "low", "high"):
                if d.get(how + "_n"):
                    place, pay = place_and_pay(c, t, t["points"] + d[how])
                    top10 = place <= math.ceil(len(c["points_sorted"]) / 10)
                    # real minus alternative: positive = what I really did beat the alternative
                    res[how][n["date"]].append((-d[how], int(t["top"][10]) - int(top10), t["payout"] - pay, int(d[how + "_n"])))
        for how in ("low", "high"):
            if picks_how[how]:
                conc[how].append(collections.Counter(picks_how[how]).most_common(1)[0][1] / len(picks_how[how]))
    out = ["### f. Swaps, replayed in money (my credited swaps)", "",
           "Each of my credited swaps against an alternative, the team's points moved by the difference and its place and payout "
           "re-read off the contest's real scores. Positive: what really happened beat the alternative. Small sample; directional. "
           "Nights left uncredited on purpose (%s) are out." % ", ".join(sorted(S.EXCLUDED)), "",
           "| My real swaps against | Nights | Swaps | Points a swap | Top-10% finishes | Dollars |", "|---|---|---|---|---|---|"]
    labels = {"saved": "my last saved board order's pick (is the app shuffle worth it?)",
              "low": "the swap board, near-ties least drafted first (leverage)", "high": "the swap board, near-ties most drafted first (spread)"}
    for how in ("saved", "low", "high"):
        v = [x for d in res[how].values() for x in d]
        if not v:
            continue
        nsw = sum(x[3] for x in v)
        out.append("| %s | %d | %d | %+.1f | %+d | %+.0f |" % (labels[how], len(res[how]), nsw, sum(x[0] for x in v) / nsw,
                                                             sum(x[1] for x in v), sum(x[2] for x in v)))
    lo = [x for d in res["low"].values() for x in d]
    hi = [x for d in res["high"].values() for x in d]
    if lo and hi:
        out += ["", "Leverage against spread: the leverage board's swaps would have made %+d top-10%% finishes and $%+.0f against "
                "the spread board's (real minus each, differenced). Leverage put %.0f%% of a night's replayed swaps on one player, "
                "spread %.0f%%." % (sum(x[1] for x in hi) - sum(x[1] for x in lo), sum(x[2] for x in hi) - sum(x[2] for x in lo),
                                    100 * st.mean(conc["low"]), 100 * st.mean(conc["high"]))]
    return out + [""], res


# ---------------------------------------------------------------- step 4: the field
def ranks_of(n):
    priced = sorted((num(r["adp_close"]), p) for p, r in n["rec"].items() if num(r["adp_close"]) is not None)
    return {p: i + 1 for i, (_, p) in enumerate(priced)}


def drafted_by(t):
    """The players a team drafted: its picks taken with an ADP, plus the ruled-out players its swaps replaced."""
    swapped = {p for p, a in zip(t["picks"], t["adps"]) if a is None}
    return t["holds"] - swapped


def turn_teams(N):
    """[(night, team, info)] for teams at the 1/2 and 2/3 turns, read from rosters by closing-ADP rank.
    1/2 turn (6 drafters; scaled for 4): the team's two earliest players. Faller: the earliest is a top-(pod-2) player and
    the second comes by rank pod+2 (a player who fell to the turn, always taken). Otherwise a turn team when the earliest
    is rank pod-1..pod+2 and the second by rank 2 x pod: expected second rank pod+2 after rank pod-1 (picks 5 and 8),
    pod+1 after rank pod (6 and 7), else the next rank; a reach takes the first past rank pod, or the second 2+ ranks past
    its expected one. 2/3 turn: teams anchored by rank 1 or 2; their next two players against picks 2 x pod and 2 x pod + 1
    (anchor 1) or 2 x pod - 1 and 2 x pod + 2 (anchor 2); a faller there is a second player ranked 2 x pod - 3 or better."""
    out = []
    for n in N:
        rk = ranks_of(n)
        for c in n["contests"]:
            pod = c["pod_size"]
            for t in n["teams"][c["contest_id"]]:
                if t["bin"] is None or t["window"] is None:
                    continue
                rs = sorted((rk[p], p) for p in drafted_by(t) if p in rk)
                if len(rs) < 3:
                    continue
                (r1, p1), (r2, p2), (r3, p3) = rs[0], rs[1], rs[2]
                if r1 <= pod - 2 and r2 <= pod + 2 and r2 >= pod - 1:
                    out.append((n, t, {"turn": "1/2", "kind": "faller", "pair": (r1, r2), "picks": (p1, p2)}))
                elif pod - 1 <= r1 <= pod + 2 and r2 <= 2 * pod:
                    e2 = pod + 2 if r1 == pod - 1 else pod + 1 if r1 == pod else r1 + 1
                    reach = None
                    if r2 - e2 >= 2:
                        reach = (p2, list(range(e2, r2)))
                    elif r1 >= pod + 1:
                        reach = (p1, list(range(pod - 1, r1)))
                    out.append((n, t, {"turn": "1/2", "kind": "reach" if reach else "trust", "pair": (r1, r2), "picks": (p1, p2), "reach": reach}))
                if r1 in (1, 2):
                    e = (2 * pod, 2 * pod + 1) if r1 == 1 else (2 * pod - 1, 2 * pod + 2)
                    if r2 <= 2 * pod - 3:
                        out.append((n, t, {"turn": "2/3", "kind": "faller", "pair": (r2, r3), "anchor": r1, "picks": (p2, p3)}))
                    elif r3 <= 3 * pod:
                        reach = None
                        if r3 - e[1] >= 2:
                            reach = (p3, list(range(e[1], r3)))
                        elif r2 - e[0] >= 2:
                            reach = (p2, list(range(e[0], r2)))
                        out.append((n, t, {"turn": "2/3", "kind": "reach" if reach else "trust", "pair": (r2, r3), "anchor": r1,
                                           "picks": (p2, p3), "reach": reach}))
    return out


def reach_kinds(n, t, info, rk_inv):
    """Which way a reach went against the players it jumped (those ranked between the expected spot and the reach,
    not on the team): toward the higher projection, toward a VALUE flag, toward the less-drafted."""
    p, jumped_ranks = info["reach"]
    rows = n["tiers"][t["window"]]
    me = rows.get(p)
    jumped = [rows.get(rk_inv.get(r)) for r in jumped_ranks if rk_inv.get(r) not in t["holds"]]
    jumped = [j for j in jumped if j]
    if not me or not jumped:
        return set()
    kinds = set()
    if num(me["proj"]) is not None and all(num(j["proj"]) is not None and num(me["proj"]) > num(j["proj"]) for j in jumped):
        kinds.add("higher projection")
    if me["flag"] == "VALUE" and not any(j["flag"] == "VALUE" for j in jumped):
        kinds.add("VALUE flag")
    if num(me["drafted"]) is not None and all(num(j["drafted"]) is not None and num(me["drafted"]) < num(j["drafted"]) for j in jumped):
        kinds.add("less drafted")
    return kinds


def turns_section(N, dates, bins):
    tt = turn_teams(N)
    inv = {}
    for n in N:
        inv[n["date"]] = {r: p for p, r in ranks_of(n).items()}
    case = lambda n, t, g, i: (n["date"], t["contest"]["contest_id"], t[bins], g, t, set(i["picks"]))
    out = ["### Turns, from rosters by ADP rank (no pick order)", "",
           "Fallers (a top player who fell to the turn) are kept apart: always taken. For the pairs you control: does reaching "
           "(a player 2+ picks past ADP order) beat trusting ADP order? Lift against same-contest, same-price trusting teams. "
           "Definitions in turn_teams().", "", "| Turn | Test | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |", "|---|---|---|---|"]
    results = {}
    for turn in ("1/2", "2/3"):
        xs = [(n, t, i) for n, t, i in tt if i["turn"] == turn]
        trust = [case(n, t, "B", i) for n, t, i in xs if i["kind"] == "trust"]
        tests = [("a. reach vs trust", [case(n, t, "A", i) for n, t, i in xs if i["kind"] == "reach"] + trust),
                 ("fallers vs trust", [case(n, t, "A", i) for n, t, i in xs if i["kind"] == "faller"] + trust)]
        for kind in ("higher projection", "VALUE flag", "less drafted"):
            tests.append(("b. reach toward %s vs trust" % kind,
                          [case(n, t, "A", i) for n, t, i in xs if i["kind"] == "reach" and kind in reach_kinds(n, t, i, inv[n["date"]])] + trust))
        key = lambda t, i: (t["contest"]["pod_size"],) + (i["pair"] if turn == "1/2" else (i["anchor"],) + i["pair"])
        cells = collections.Counter(key(t, i) for n, t, i in xs if i["kind"] != "faller")
        for ck, k in sorted(cells.items(), key=lambda kv: (-kv[0][0], -kv[1]))[:16]:
            label = ("c. %d-drafter, ranks %d + %d" % ck) if turn == "1/2" else ("c. %d-drafter, anchor %d, ranks %d + %d" % ck)
            tests.append((label, [case(n, t, "A" if key(t, i) == ck else "B", i) for n, t, i in xs if i["kind"] != "faller"
                                  and t["contest"]["pod_size"] == ck[0]]))
        for name, cs in tests:
            ev = evaluate(cs, dates, bins)
            results[(turn, name)] = (ev, cs)
            out.append("| %s | %s | %s | %s |" % (turn, name, cell(ev["field"]["all"]), cell(ev["mine"]["all"])))
    return out + ["", "Rank pairs (c) are detail: most will be not enough yet. Each is against every other non-faller pair at "
                  "that turn.", ""], results


def tiers_of_team(n, t):
    rows = n["tiers"][t["window"]] if t["window"] else {}
    return [rows[p] for p in drafted_by(t) if p in rows]


GROUP = {"PG": "G", "SG": "G", "G": "G", "SF": "F", "PF": "F", "F": "F", "C": "C"}


def stars(n, w):
    """Each team's top two by projection at the window."""
    key = ("_stars", w)
    if key not in n:
        by = collections.defaultdict(list)
        for p, r in n["tiers"][w].items():
            if num(r["proj"]) is not None:
                by[r["team"]].append((num(r["proj"]), p))
        n[key] = {p for v in by.values() for _, p in sorted(v, reverse=True)[:2]}
    return n[key]


def opp_stars(n, t):
    """The team's stars on opposite sides of one game (empty if none)."""
    s = stars(n, t["window"])
    mine = [p for p in drafted_by(t) if p in s and p in n["rec"]]
    return {p for a in mine for b in mine if a != b and n["rec"][a]["opp"] == n["rec"][b]["team"] for p in (a, b)}


def same_pos(n, t, big=None):
    """Teammates in the same position group on the team (big: only in games with a spread of 5+, or under 5)."""
    ps = [(p, n["rec"][p]) for p in drafted_by(t) if p in n["rec"]]
    out = set()
    for i, (pa, a) in enumerate(ps):
        for pb, b in ps[i + 1:]:
            if a["team"] == b["team"] and GROUP.get((a["pos"] or "").split("-")[0]) == GROUP.get((b["pos"] or "").split("-")[0]):
                if big is None or ((abs(num(a["spread"]) or 0)) >= 5) == big:
                    out |= {pa, pb}
    return out


def field_section(N, dates, bins):
    out = ["## 4. The field", ""]
    res = {}
    # drafted% by tier, flag and Q class: each flagged player against an unflagged partner (same tier, ADP within 4)
    out += ["### Drafted% by tier, flag and Q class", "",
            "Each flagged (or tagged) player against unflagged, untagged partners in his tier within 4 ADP picks, at the window "
            "the teams drafted in: the share of that window's pods that took each (all contests). Negative: the field drafted the "
            "flagged one less.", "", "| Window | Tier | Flag | Pairs | Flagged drafted% | Partner drafted% | Difference |", "|---|---|---|---|---|---|---|"]
    agg = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for n in N:
        for w in ("am", "pm"):
            pods, inpod = set(), collections.defaultdict(set)
            for ts in n["teams"].values():
                for t in ts:
                    if t["window"] == w:
                        pods.add(t["draft_id"])
                        for p in drafted_by(t):
                            inpod[p].add(t["draft_id"])
            if not pods:
                continue
            dr = {p: len(v) / len(pods) for p, v in inpod.items()}
            rows = rows_of(n, w)
            for i, a in enumerate(rows):
                for b in rows[i + 1:]:
                    if a["tier"] != b["tier"] or abs(num(a["adp"]) - num(b["adp"])) > 4:
                        continue
                    for x, y in ((a, b), (b, a)):
                        lab = x["flag"] or (x["q_class"] and "Q " + x["q_class"])
                        if lab and not y["flag"] and not y["q_class"]:
                            tg = "T1-T2" if int(x["tier"]) <= 2 else "T3-T4" if int(x["tier"]) <= 4 else "T5"
                            g = agg[(w.upper(), tg, lab)]
                            g[0] += 1
                            g[1] += dr.get(x["player_id"], 0)
                            g[2] += dr.get(y["player_id"], 0)
    for k in sorted(agg):
        c, fx, fy = agg[k]
        out.append("| %s | %s | %s | %d | %.0f%% | %.0f%% | %+.0f |" % (k + (c, 100 * fx / c, 100 * fy / c, 100 * (fx - fy) / c)))
    # T5 below 100: low-drafted T5 breakers
    low = collections.Counter()
    tot = collections.Counter()
    for n in N:
        f = max(n["contests"], key=lambda c: int(c["entries"]))
        d, _ = C.drafted(n["teams"][f["contest_id"]], f["pod_size"])
        for p, r in n["tiers"]["pm"].items():
            if r["tier"] == "5" and r["breaker"] == "1":
                tot[r["flag"] or "unflagged"] += 1
                if d.get(p, 0) < 0.5:
                    low[r["flag"] or "unflagged"] += 1
    out += ["", "T5 breakers (PM tiers) drafted in under half the flagship's pods: %s (of all T5 breakers: %s)." % (
        ", ".join("%s %d" % kv for kv in sorted(low.items())), ", ".join("%s %d" % kv for kv in sorted(tot.items()))), ""]
    # stacks
    out += ["### Stacks (residual_correlations.md): teams holding the structure against same-price teams without", "",
            "| Structure | Lift at 10% (80% range), at 1%; finish; teams, slates | Mine |", "|---|---|---|"]
    for name, has in (("Opposing stars (their team's top 2 by projection, same game)", opp_stars),
                      ("Same-position teammates", lambda n, t: same_pos(n, t)),
                      ("Same-position teammates, spread 5+", lambda n, t: same_pos(n, t, True))):
        cs = hold_cases(N, ("am", "pm"), has)
        ev = evaluate(cs, dates, bins)
        res[("stack", name)] = (ev, cs)
        out.append("| %s | %s | %s |" % (name, cell(ev["field"]["all"]), cell(ev["mine"]["all"])))
    # top-finish makeup
    out += ["", "### What top-1% teams held (a description, not a rule)", "",
            "Per team, at its draft window's tiers: picks by combined tier, VALUE and PRICEY picks, tagged picks by Q class, breakers.", "",
            "| | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | FAIR | TRAP | SMASH | Breakers |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    acc = {"Top 1%": collections.Counter(), "Field": collections.Counter()}
    cnt = collections.Counter()
    for n in N:
        for ts in n["teams"].values():
            for t in ts:
                if not t["window"]:
                    continue
                rs = tiers_of_team(n, t)
                for g in (["Top 1%"] if t["top"][1] else []) + ["Field"]:
                    cnt[g] += 1
                    for r in rs:
                        acc[g]["T" + r["tier"]] += 1
                        acc[g][r["flag"]] += 1
                        acc[g][r["q_class"]] += 1
                        acc[g]["brk"] += r["breaker"] == "1"
    for g in ("Top 1%", "Field"):
        a = acc[g]
        out.append("| %s | %s |" % (g, " | ".join("%.2f" % (a[k] / cnt[g]) for k in ("T1", "T2", "T3", "T4", "T5", "VALUE", "PRICEY", "FAIR", "TRAP", "SMASH", "brk"))))
    # swap luck
    def swapped(n, t):
        return {p for p, a in zip(t["paid_pid"], t["adps"]) if a is None and p} or any(a is None for a in t["adps"])
    ev = evaluate(hold_cases([n for n in N if n["date"] not in S.EXCLUDED], ("am", "pm"), swapped), dates, bins)
    res[("swaps", "any")] = ev
    out += ["", "### Swaps in the field", "", "Teams with a swap against same-price teams without (each priced at what it paid): %s." % cell(ev["field"]["all"]), ""]
    # high-volume users
    per_user = collections.defaultdict(lambda: collections.Counter())
    nights_user = collections.defaultdict(set)
    for n in N:
        for ts in n["teams"].values():
            for t in ts:
                per_user[t["username"]]["teams"] += 1
                nights_user[t["username"]].add(n["date"])
    vol = [u for u, c in per_user.items() if c["teams"] >= 100 and len(nights_user[u]) >= 8 and u != ME]
    def profile(users):
        a, k = collections.Counter(), 0
        for n in N:
            for ts in n["teams"].values():
                for t in ts:
                    if t["username"] in users and t["window"]:
                        k += 1
                        for r in tiers_of_team(n, t):
                            a["T" + r["tier"]] += 1
                            a[r["flag"]] += 1
                            a["tagged"] += bool(r["tag"])
                            a["drafted"] += num(r["drafted"]) or 0
                            a["picks"] += 1
                        a["dupe"] += 0
        return a, k
    out += ["### High-volume users (100+ teams on 8+ nights; studied, never ranked)", "",
            "%d users. Per team, against the field and me:" % len(vol), "",
            "| | Teams | T1 | T2 | T3 | T4 | T5 | VALUE | PRICEY | Tagged | Average drafted% of picks |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for lab, users in (("High-volume", set(vol)), ("Me", {ME}), ("Everyone", set(per_user))):
        a, k = profile(users)
        if k:
            out.append("| %s | %d | %s | %.0f%% |" % (lab, k, " | ".join("%.2f" % (a[x] / k) for x in ("T1", "T2", "T3", "T4", "T5", "VALUE", "PRICEY", "tagged")),
                                                     a["drafted"] / a["picks"] if a["picks"] else 0))
    return out + [""], res


# ---------------------------------------------------------------- step 3: the register in money
SPLITS = [   # detail rows under a register row: (register id, label, builder)
    ("ownership-tiebreak-t5", "AM only", lambda N: pair_cases(N, ("am",), {5}, less_drafted())),
    ("ownership-tiebreak-t5", "PM only", lambda N: pair_cases(N, ("pm",), {5}, less_drafted())),
    ("value-up-middle-t5", "T3", lambda N: pair_cases(N, ("am", "pm"), {3}, flag_vs_plain("VALUE", True))),
    ("value-up-middle-t5", "T4", lambda N: pair_cases(N, ("am", "pm"), {4}, flag_vs_plain("VALUE", True))),
    ("value-up-middle-t5", "T5", lambda N: pair_cases(N, ("am", "pm"), {5}, flag_vs_plain("VALUE", True))),
] + [("pricey-flags", "T%d" % k, (lambda k: lambda N: pair_cases(N, ("am", "pm"), {k}, flag_vs_plain("PRICEY", False)))(k)) for k in range(1, 6)]


def register_section(N, dates):
    """Every register decision (and its detail splits) on quintiles and deciles; the verdict on quintiles, flagged where
    deciles disagree."""
    for n in N:
        N_BY[n["date"]] = n
    rows = []
    for rid, label, b in DECISIONS:
        rows.append((rid, label, b, False))
        rows += [(r, "  %s" % l, bb, True) for r, l, bb in SPLITS if r == rid]
    out = ["## 3. The register in money", "",
           "A = teams that did what the decision says, against same-contest, same-price teams that did the other (pairs) or "
           "didn't (holdings). Field: every team; mine: my A teams against the field's B. Lift at the top 10%% with its 80%% range "
           "(resampling slates), at the top 1%%, and finish (A's average finish percentile minus B's: negative is better). "
           "Find = slates before the last %d, check = the last %d." % (CHECK, CHECK), "",
           "| Decision | Field, all slates | Find | Check | Mine | Money (quintiles) | Deciles |", "|---|---|---|---|---|---|---|"]
    ref = evaluate(hold_cases(N, ("am", "pm"), lambda n, t: t["mine"]), dates)["field"]["all"]
    out.insert(len(out) - 2, "Reference for the Mine column: all my teams against same-price field teams run %s. Mine reads "
               "against that, not against 1.00." % cell(ref))
    out.insert(len(out) - 2, "")
    res = {}
    for rid, label, b, split in rows:
        cs = b(N)
        ev5, ev10 = evaluate(cs, dates, "bin5"), evaluate(cs, dates, "bin10")
        v5, v10 = verdict(ev5)[0], verdict(ev10)[0]
        res[(rid, label.strip())] = (ev5, v5, v10, split, cs)
        out.append("| %s%s | %s | %s | %s | %s | %s | %s |" % (
            "" if split else "**%s** " % rid, label, cell(ev5["field"]["all"]), cell(ev5["field"]["find"]), cell(ev5["field"]["check"]),
            cell(ev5["mine"]["all"]), v5, v10 + (" **(changes)**" if v10 != v5 else "")))
    return out + [""], res


# ---------------------------------------------------------------- step 5: two verdicts per decision
def sign_points(v):
    v = (v or "").lower()
    if "against" in v or "costs" in v:
        return -1
    if "lean" in v or "rule" in v:
        return 1
    return 0


def combine(points, money):
    p, m = sign_points(points), (1 if money.endswith("for") else -1 if money.endswith("against") else 0)
    strong = money.startswith("RULE")
    if p > 0 and m > 0:
        return "keep: points and money agree"
    if p > 0 and m < 0:
        return "rethink: money RULE against it" if strong else "keep on points; money leans against (watch)"
    if p > 0:
        return "keep on points; money not settled"
    if p < 0 and m > 0:
        return "keep: the leverage pays (money RULE)" if strong else "watch: money leans for the leverage, not yet its bar"
    if p < 0 and m < 0:
        return "drop: both negative"
    if p < 0:
        return "drop on points unless money clears its bar"
    if m:
        return "candidate: hand to the rankings side with its points cost" if strong else "watch: money leans %s" % ("for" if m > 0 else "against")
    return "not enough on either side yet"


def verdict_section(reg, swaps, survived):
    register = list(csv.DictReader(open(os.path.join(REP, "decision_register.csv"))))
    pts = {r["id"]: r["points_verdict"] for r in register}
    main = {k[0]: v for k, v in reg.items() if not v[3]}
    cells = len(reg)
    leans = sum(1 for v in reg.values() if v[1].startswith(("LEAN", "RULE")))
    rules = sum(1 for v in reg.values() if v[1].startswith("RULE"))
    flips = [k for k, v in reg.items() if v[1] != v[2]]
    out = ["## 5. Draft verdicts (not yet written to decision_register.csv)", "",
           "MONEY rests on the top-10%% lift (the faster reader); the top-1%% lift and finish are beside it in section 3 as the "
           "long-run and steadier checks. %d cells tested; %d show a lean or rule and %d a rule. By chance alone about %d would "
           "show a lean (40%% of cells: 80%%+ of resamples one side happens 40%% of the time with nothing there) and about %d a rule "
           "(90%% range clear of 1.0 and the check slates agreeing, about 5%%). So a lone lean is weak; a rule, or a lean that agrees "
           "with the points verdict, counts." % (cells, leans, rules, round(0.4 * cells), max(1, round(0.05 * cells))),
           "A lean or rule counts only if it survives the price-split check (section 3b); MONEY below is the verdict that survives.",
           "", "| Decision | Status | POINTS | MONEY before the check | MONEY (survives the check) | Top-10% lift (80% range), all slates | Recommendation |",
           "|---|---|---|---|---|---|---|"]
    for r in register:
        rid = r["id"]
        if rid in ("swap-shuffle", "swap-ownership-order", "live-moves"):
            continue
        subs = [(k, v) for k, v in main.items() if k == rid or k.startswith(rid + ":")]
        for k, (ev5, v5, v10, _, _) in subs:
            a = ev5["field"]["all"]
            lift = ("%.2f (%.2f-%.2f)" % ((a["lift"][10],) + a["r80"]) if a and "r80" in a and a["lift"][10] else "-")
            after = survived.get(k, v5)
            out.append("| %s | %s | %s | %s%s | %s | %s | %s |" % (k, r["status"], pts[rid], v5, " (deciles: %s)" % v10 if v10 != v5 else "",
                                                               after, lift, combine(pts[rid], after)))
    out.append("| live-moves | %s | %s | not enough (saves after lock on 3 nights) | not enough | - | not enough on either side yet |" % (
        next(r["status"] for r in register if r["id"] == "live-moves"), pts["live-moves"]))
    for rid in ("swap-shuffle", "swap-ownership-order"):
        out.append("| %s | %s | %s | not enough (about 100 swaps; section 3f has the dollars) | not enough | - | not enough on either side yet |" % (
            rid, next(r["status"] for r in register if r["id"] == rid), pts[rid]))
    if flips:
        out += ["", "Verdicts that change on ten price groups: " + "; ".join("%s%s (%s on five, %s on ten)" % (
            k[0], " " + k[1] if reg[k][3] else "", reg[k][1], reg[k][2]) for k in flips) + "."]
    return out + [""]


def report(N, mirror):
    dates = [n["date"] for n in N]
    out = ["# NBA money report (draft)", "",
           "Written by scripts/nba_money.py (definitions in its docstring), %s. Slates %s to %s: %d nights, %d contests, %d teams. "
           "The contest side's read of whether decisions make money; POINTS verdicts are the rankings side's "
           "(decision_register.csv)." % (dt.date.today().isoformat(), dates[0], dates[-1], len(N), sum(len(n["contests"]) for n in N),
                                         sum(len(v) for n in N for v in n["teams"].values())), ""]
    out += data_checks(N) + baseline_section(N) + scoreboard(N)
    reg_out, reg = register_section(N, dates)
    sw_out, sw = swap_money(N)
    turn_out, turns = turns_section(N, dates, "bin5")
    field_out, field = field_section(N, dates, "bin5")
    chk_out, survived, checked = check_section(reg, turns, field, dates)
    out += reg_out + chk_out + sw_out
    r6_out, _ = round6_section(N, dates)
    out += r6_out
    out += field_out[:2] + turn_out + field_out[2:] + swap_split_section(N, dates)
    out += verdict_section(reg, sw, survived)
    return out, {"reg": reg, "turns": turns, "field": field, "checked": checked, "survived": survived}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", help="a clone of br-adp-mirror (draft windows for nights not cached yet)")
    ap.add_argument("--proposals", action="store_true", help="write money_proposals.json even if it isn't Monday")
    a = ap.parse_args()
    N = load(a.mirror)
    out, parts = report(N, a.mirror)
    open(os.path.join(REP, "money_report.md"), "w").write("\n".join(out) + "\n")
    tj = tiers_json(N, parts)
    json.dump(tj, open(os.path.join(REP, "money_tiers.json"), "w"), indent=1)
    if a.proposals or dt.datetime.now(PT).weekday() == 0:             # Mondays (Pacific): the weekly verdict proposals
        json.dump(proposals(tj), open(os.path.join(REP, "money_proposals.json"), "w"), indent=1)
    print("\n".join(out))



# ---------------------------------------------------------------- the price-split check (2026-11-09)
def price_check(cases, dates):
    """Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other
    picks. (a) the A-B gap in points over price, split into the decision pick(s) and the other picks; (b) the lift again,
    matched on the price of the other picks (contest x quintile of that price among the test's teams); (c) the decision
    pick's own points, A's minus B's, in the same strata."""
    rows = []
    for c in cases:
        d, cid, b, g, t, dec = c[:6]
        if t["price"] is None:
            continue
        ds = [x for x in t["slots"] if x[0] in dec]
        rows.append([c, t["points"] - t["price"], sum(fp - e for _, e, fp in ds), sum(fp for _, _, fp in ds),
                     t["price"] - sum(e for _, e, _ in ds), len(ds)])
    # a holding test's B teams have no decision pick: their "other picks" are put on the A teams' footing by taking off
    # the average price of A's decision picks in the same contest
    holding = not any(r[5] for r in rows if r[0][3] == "B")
    if holding:
        dec_price = collections.defaultdict(list)
        for r in rows:
            if r[0][3] == "A" and r[5]:
                dec_price[(r[0][0], r[0][1])].append(r[0][4]["price"] - r[4])
        for r in rows:
            if r[0][3] == "B":
                r[4] -= st.mean(dec_price[(r[0][0], r[0][1])]) if dec_price[(r[0][0], r[0][1])] else 0
    by = collections.defaultdict(lambda: {"A": [], "B": []})
    for r in rows:
        by[(r[0][0], r[0][1], r[0][4]["bin5"])][r[0][3]].append(r)
    gap = [0.0, 0.0, 0.0]
    nA = 0
    for v in by.values():
        if not v["A"] or not v["B"]:
            continue
        mb = [st.mean(r[i] for r in v["B"]) for i in (1, 2, 3)]
        for r in v["A"]:
            for k, i in enumerate((1, 2, 3)):
                gap[k] += r[i] - mb[k]
            nA += 1
    if not nA:
        return None
    gt, gd, gfp = (x / nA for x in gap)
    # (b) matched on the other picks' price
    q = {}
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r[0][0], r[0][1])].append(r[4])
    for k, v in groups.items():
        q[k] = sorted(v)
    re_cases = []
    for r in rows:
        c = r[0]
        v = q[(c[0], c[1])]
        bin_ = min(4, bisect.bisect_right(v, r[4]) * 5 // (len(v) + 1))
        re_cases.append((c[0], c[1], bin_, c[3], c[4]))
    ev = evaluate(re_cases, dates, "case")
    return {"gap": gt, "dec": gd, "oth": gt - gd, "own": None if holding else gfp, "has_dec": any(r[5] for r in rows), "ev": ev,
            "verdict": verdict(ev)[0], "holding": holding}


def check_section(reg, turns, field, dates):
    out = ["## 3b. The price-split check", "",
           "Teams are matched on total price, so a team that took the cheaper player at the decision spent more on its other "
           "picks, and cheaper teams beat their price (section 1). For every lean or rule, and the draft-card candidates: the A-B "
           "gap in points over price, split into the decision pick(s) and the other picks; the decision pick's own points (A's "
           "minus B's); and the top-10% lift again, matched on the other picks' price (contest x quintile). A money verdict "
           "counts only if it survives the re-match. A leverage win should show as rank gained with equal or slightly lower own "
           "points, not as better other picks. Holding tests (a Q player, a beneficiary, a stack): the teams without the holding "
           "have no decision pick, so their other picks' price is taken as their price less the average price of the holders' "
           "decision picks in that contest, and own points don't apply. Shares are shown when the gap is half a point or more.", "",
           "| Decision | Verdict before | Gap, points over price (A-B) | From the decision pick | From the other picks | Decision pick's own points (A-B) | Lift matched on the other picks' price | Verdict that survives |",
           "|---|---|---|---|---|---|---|---|"]
    items = [((k[0] + (" " + k[1] if v[3] else "")), v[1], v[4]) for k, v in reg.items() if v[1].startswith(("LEAN", "RULE"))]
    for k, (ev, cs) in turns.items():
        if k[1] in ("a. reach vs trust", "fallers vs trust", "b. reach toward higher projection vs trust"):
            items.append(("turn %s: %s" % k, verdict(ev)[0], cs))
    for k, (ev, cs) in field.items():
        if k[0] == "stack":
            items.append(("stack: " + k[1], verdict(ev)[0], cs))
    survived, checked = {}, {}
    for name, before, cs in items:
        r = price_check(cs, dates)
        if not r:
            continue
        survived[name] = r["verdict"]
        checked[name] = r
        share = lambda x: "%+.1f (%.0f%%)" % (x, 100 * x / r["gap"]) if abs(r["gap"]) >= 0.5 else "%+.1f" % x
        a = r["ev"]["field"]["all"]
        out.append("| %s | %s | %+.1f | %s | %s | %s | %s | %s |" % (
            name, before, r["gap"], share(r["dec"]) if r["has_dec"] else "-", share(r["oth"]) if r["has_dec"] else "-",
            "%+.1f" % r["own"] if r["own"] is not None else "- (holding)", cell(a), r["verdict"]))
    return out + [""], survived, checked


def round6_section(N, dates):
    """The knowable round-6 rule: AM teams with a round-6 pick whose teammate was tagged (Questionable, Doubtful, GTD) at
    Lock AM, whether he then played or sat, against same-price AM teams without one; split by how high the tagged teammate
    was being drafted (his Lock AM ADP round; his best if several). Then the price-split check on each."""
    def has(lo, hi):
        def f(n, t):
            last = 5 * t["contest"]["pod_size"]
            rows = n["tiers"]["am"]
            out = set()
            for p, a in zip(t["paid_pid"], t["paid"]):
                me = rows.get(p) if p else None
                if not me or a is None or a <= last:
                    continue
                mates = [num(r["adp"]) for r in rows.values() if r["team"] == me["team"] and r["player_id"] != p and r["tag"] in QRE]
                mates = [x if x is not None else 6 * t["contest"]["pod_size"] for x in mates]
                if mates:
                    rd = min(6, max(1, math.ceil(min(mates) / t["contest"]["pod_size"])))
                    if lo <= rd <= hi:
                        out.add(p)
            return out
        return f
    out = ["### The knowable round-6 rule", "",
           "AM teams with a round-6 pick whose teammate was tagged at Lock AM (played or sat: not known at the draft), against "
           "same-price AM teams without one, by the round the tagged teammate was being drafted in. Then the price-split check: "
           "the round-6 pick's own points over price against the other picks, and the lift re-matched on the other picks' price.", "",
           "| Tagged teammate drafted in | Lift at 10% (80% range), at 1%; finish; teams, slates | Gap over price (A-B) | From the round-6 pick | From the other picks | Lift matched on the other picks' price | Verdict that survives |",
           "|---|---|---|---|---|---|---|"]
    res = {}
    for label, lo, hi in (("any round", 1, 6), ("rounds 1-2", 1, 2), ("rounds 3-4", 3, 4), ("rounds 5-6 or undrafted", 5, 6)):
        cs = hold_cases(N, ("am",), has(lo, hi))
        ev = evaluate(cs, dates)
        r = price_check(cs, dates)
        res[label] = (ev, r)
        if not r:
            out.append("| %s | %s | - | - | - | - | %s |" % (label, cell(ev["field"]["all"]), verdict(ev)[0]))
            continue
        share = lambda x: "%+.1f (%.0f%%)" % (x, 100 * x / r["gap"]) if abs(r["gap"]) >= 0.5 else "%+.1f" % x
        out.append("| %s | %s | %+.1f | %s | %s | %s | %s |" % (label, cell(ev["field"]["all"]), r["gap"], share(r["dec"]), share(r["oth"]),
                                                             cell(r["ev"]["field"]["all"]), r["verdict"]))
    return out + [""], res


def swap_split_section(N, dates):
    """Teams with a swap against same-price teams without, by the ruled-out player's tier at the team's window."""
    def has(group, window=None):
        def f(n, t):
            if window and t["window"] != window:
                return False
            outs = [p for p, a in zip(t["paid_pid"], t["adps"]) if a is None]
            if not outs:
                return False
            if group == "not credited":
                return any(p is None for p in outs)
            tiers = [n["tiers"][t["window"]].get(p) for p in outs if p]
            ok = [r for r in tiers if r and (int(r["tier"]) <= 2) == (group == "T1-T2")]
            return {r["player_id"] for r in ok}
        return f
    out = ["### Swaps by the ruled-out player's tier (at the team's draft window)", "",
           "Teams with such a swap against same-price teams with no swap. A swapped team is priced at what it paid. Nights "
           "nba_swaps.py leaves uncredited on purpose are out of every swap test (%s)." % ", ".join(sorted(S.EXCLUDED)), "",
           "| Ruled-out player | Window | Lift at 10% (80% range), at 1%; finish; teams, slates |", "|---|---|---|"]
    for group in ("T1-T2", "T3-T5", "not credited"):
        for w in (None, "am", "pm"):
            f = has(group, w)
            cs = [c for c in hold_cases([n for n in N if n["date"] not in S.EXCLUDED], ("am", "pm"), f)
                  if c[3] == "A" or not any(a is None for a in c[4]["adps"])]
            out.append("| %s | %s | %s |" % (group, w.upper() if w else "both", cell(evaluate(cs, dates)["field"]["all"])))
    return out + [""]


# ---------------------------------------------------------------- the morning report's per-tier block
def tier_keys(spec):
    """The register's tier column as tiers: "5", "3,4,5", "1-5"; "all", "turn" and "undrafted" are their own blocks."""
    spec = (spec or "").strip()
    if spec in ("all", "turn", "undrafted"):
        return [spec]
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += [str(k) for k in range(int(a), int(b) + 1)]
        elif part.strip():
            out.append(part.strip())
    return out


def mine_where(cs):
    """My teams where the decision applied (A), season to date: teams, top-10% rate over the field's 10%, top 1%, finish."""
    ts = list({id(c[4]): c[4] for c in cs if c[3] == "A" and c[4]["mine"]}.values())     # each team once
    if not ts:
        return None
    return {"teams": len(ts), "top10_ratio": round(sum(t["top"][10] for t in ts) / len(ts) / 0.10, 2),
            "top1_ratio": round(sum(t["top"][1] for t in ts) / len(ts) / 0.01, 2), "finish_pct": round(100 * st.mean(t["fin"] for t in ts), 1)}


def lift_of(ev, checked=None):
    a = (checked["ev"] if checked else ev)["field"]["all"]
    if not a or a["lift"][10] is None:
        return None
    return {"lift10": round(a["lift"][10], 2), "range80": [round(x, 2) for x in a["r80"]] if "r80" in a else None,
            "teams": a["n"], "slates": a["slates"], "after_price_check": bool(checked)}


def tiers_json(N, parts):
    """analysis/nba/report/money_tiers.json, for the morning report's tier sections (scripts/nba_money.py writes it nightly):
    per tier, last night's exposure (mine against the field's, at each team's draft window), the field's drafted% of the
    tier's VALUE, PRICEY and tagged players, and season to date the register's decisions for the tier: the approved MONEY
    verdict, the current top-10% lift (after the price-split check where it ran) and my finish where the decision applied."""
    reg, turns, field, checked = parts["reg"], parts["turns"], parts["field"], parts["checked"]
    n = N[-1]
    names = {p: r["name"] for p, r in n["rec"].items()}
    out = {"generated": dt.date.today().isoformat(), "night": n["date"], "pod": n["pod"], "slates": [x["date"] for x in N],
           "notes": "Exposure: share of teams holding the player (mine: my teams in that window; field: every team in it). "
                    "Drafted%: share of that window's pods that drafted him. lift10: top-10% lift against same-contest, "
                    "same-price teams (money_report.md). verdict: the MONEY column of decision_register.csv as approved; "
                    "current: this run's read (after the price-split check where it ran). mine: my teams where the decision "
                    "applied, season to date (top-10% and top-1% rates over the field's).",
           "tiers": {}}
    blocks = collections.defaultdict(lambda: {"exposure": {}, "drafted": {}, "decisions": []})
    # last night: exposure and drafted%
    for w in ("am", "pm"):
        ts = [t for v in n["teams"].values() for t in v if t["window"] == w]
        mine = [t for t in ts if t["mine"]]
        if not ts:
            continue
        pods = collections.defaultdict(set)
        held = collections.Counter()
        held_mine = collections.Counter()
        for t in ts:
            for p in drafted_by(t):
                pods[p].add(t["draft_id"])
                held[p] += 1
                held_mine[p] += t["mine"]
        npods = len({t["draft_id"] for t in ts})
        rows = n["tiers"][w]
        for k in ("1", "2", "3", "4", "5"):
            tier_rows = [r for r in rows.values() if r["tier"] == k]
            if not tier_rows:
                continue
            per_team = lambda group: sum(1 for t in group for p in drafted_by(t) if rows.get(p, {}).get("tier") == k) / len(group) if group else None
            players = sorted(({"name": r["name"], "adp": num(r["adp"]), "flag": r["flag"] or None, "tag": r["tag"] or None,
                               "q_class": r["q_class"] or None, "mine": round(held_mine[r["player_id"]] / len(mine), 3) if mine else None,
                               "field": round(held[r["player_id"]] / len(ts), 3), "drafted": round(len(pods[r["player_id"]]) / npods, 3)}
                              for r in tier_rows if held[r["player_id"]] or held_mine[r["player_id"]]),
                             key=lambda x: (x["adp"] is None, x["adp"]))
            blocks[k]["exposure"][w] = {"my_teams": len(mine), "field_teams": len(ts),
                                        "picks_per_team": {"mine": round(per_team(mine), 2) if mine else None, "field": round(per_team(ts), 2)},
                                        "players": players}
            blocks[k]["drafted"][w] = {lab: [{"name": x["name"], "drafted": x["drafted"], "mine": x["mine"]} for x in players
                                              if (x["flag"] == lab if lab != "Q" else bool(x["tag"]))] for lab in ("VALUE", "PRICEY", "Q")}
    # season to date: the register's decisions
    register = list(csv.DictReader(open(os.path.join(REP, "decision_register.csv"))))
    main_rows = {k[0]: v for k, v in reg.items() if not v[3]}
    def sources(rid):
        """[(label, ev, cases, checked result)] for a register id."""
        if rid == "pricey-flags:T1":
            v = reg.get(("pricey-flags", "T1"))
            return [("", v[0], v[4], checked.get("pricey-flags T1"))] if v else []
        cards = {"card-turn23-reach-higher-proj": [("2/3", "b. reach toward higher projection vs trust")],
                 "card-turn12-reach": [("1/2", "a. reach vs trust")],
                 "card-fallers": [("1/2", "fallers vs trust"), ("2/3", "fallers vs trust")]}
        if rid in cards:
            return [("%s turn" % k[0] if len(cards[rid]) > 1 else "", turns[k][0], turns[k][1], checked.get("turn %s: %s" % k)) for k in cards[rid] if k in turns]
        stacks = {"card-same-position-teammates": "Same-position teammates", "card-opposing-stars": "Opposing stars (their team's top 2 by projection, same game)"}
        if rid in stacks:
            k = ("stack", stacks[rid])
            return [("", field[k][0], field[k][1], checked.get("stack: " + stacks[rid]))] if k in field else []
        return [(k.split(":", 1)[1] if ":" in k else "", v[0], v[4], checked.get(k)) for k, v in main_rows.items() if k == rid or k.startswith(rid + ":")]
    for r in register:
        keys = tier_keys(r["tier"]) if r["window"] != "live" else ["live"]
        for label, ev, cs, chk in sources(r["id"]) or [("", None, None, None)]:
            item = {"id": r["id"] + (":" + label if label else ""), "decision": r["decision"], "window": r["window"], "status": r["status"],
                    "points": r["points_verdict"], "verdict": r["money_verdict"],
                    "current": (chk["verdict"] if chk else verdict(ev)[0]) if ev else None,
                    "lift": lift_of(ev, chk) if ev else None, "mine": mine_where(cs) if cs else None}
            lift = item["lift"]
            item["line"] = "%s: %s%s%s%s" % (item["id"], r["money_verdict"].split(" (")[0],
                                            "; this run: %s" % item["current"] if item["current"] else "",
                                            "; top-10%% lift %.2f%s" % (lift["lift10"], " (%.2f-%.2f)" % tuple(lift["range80"]) if lift["range80"] else "") if lift else "",
                                          "; my teams there %.2fx at the top 10%% (%d teams)" % (item["mine"]["top10_ratio"], item["mine"]["teams"]) if item["mine"] else "")
            for k in keys:
                blocks[k]["decisions"].append(item)
    out["tiers"] = {k: blocks[k] for k in ("1", "2", "3", "4", "5", "all", "turn", "live", "undrafted") if k in blocks}
    return out


# ---------------------------------------------------------------- Monday: the weekly verdict proposals
VERDICTS = ("RULE for", "RULE against", "LEAN for", "LEAN against", "no lean", "not enough", "pending")


def register_verdict(text, label):
    """The verdict the register's MONEY text gives a row, or one of its splits ("played: RULE for; sat: no lean";
    "no lean for FAIR ... not enough SMASH"; "RULE for at both turns")."""
    text = text or ""
    if label:
        m = re.search(re.escape(label) + r": (%s)" % "|".join(VERDICTS), text)
        if m:
            return m.group(1)
        m = re.search(r"(%s)(?: for)? %s\b" % ("|".join(VERDICTS), re.escape(label)), text)
        if m:
            return m.group(1)
    m = re.search("|".join(VERDICTS), text)
    return m.group(0) if m else None


def proposals(tj):
    """Each register row (or split) whose verdict this run reads differently: register id, current MONEY verdict, the
    proposed verdict, the read, the reason. A row the register holds back until it has N slates ("re-read at N") isn't
    proposed before then. Proposals only: the register changes when the user approves."""
    seen, out = set(), []
    for block in tj["tiers"].values():
        for x in block["decisions"]:
            if x["id"] in seen or not x["current"]:
                continue
            seen.add(x["id"])
            label = x["id"].split(":", 1)[1] if ":" in x["id"] else ""
            label = label.replace(" turn", "") if x["id"].startswith("card-fallers") else label
            have = register_verdict(x["verdict"], label)
            if have == x["current"] or (have == "pending" and x["current"] in ("no lean", "not enough")):
                continue
            hold = re.search(r"re-read at (\d+)", x["verdict"] or "")
            if hold and x["lift"] and x["lift"]["slates"] < int(hold.group(1)):
                continue
            lift = x["lift"]
            strength = lambda v: 2 if v and v.startswith("RULE") else 1 if v and v.startswith("LEAN") else 0
            side = lambda v: 1 if v and v.endswith("for") else -1 if v and v.endswith("against") else 0
            if side(have) and side(x["current"]) and side(have) != side(x["current"]):
                why = "the read has turned to the other side"
            elif strength(x["current"]) > strength(have):
                why = "the read has strengthened"
            else:
                why = "the read has weakened"
            reason = "%s: the register says %s, this run reads %s" % (why, have or "nothing", x["current"])
            if lift:
                reason += " (top-10%% lift %.2f%s on %d slates, %d teams%s)" % (
                    lift["lift10"], ", 80%% range %.2f-%.2f" % tuple(lift["range80"]) if lift["range80"] else "", lift["slates"], lift["teams"],
                    ", after the price-split check" if lift["after_price_check"] else "")
            out.append({"id": x["id"], "current_money": x["verdict"], "proposed": x["current"], "read": {"lift": lift, "mine": x["mine"]},
                        "reason": reason})
    return {"generated": tj["generated"], "night": tj["night"], "slates": len(tj["slates"]),
            "notes": "Weekly MONEY verdict proposals (scripts/nba_money.py, Mondays). Nothing here is in decision_register.csv "
                     "until the user approves it. Reads: money_report.md sections 3, 3b and 5. A change to the rankings side's "
                     "inputs (tier_history.csv: a rebuilt button) can move a read without the contests changing; check the "
                     "register's points side when that happens.",
            "proposals": out}


if __name__ == "__main__":
    main()
