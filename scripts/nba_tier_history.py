"""NBA tier history: the Tiers button rebuilt for every main slate at the AM and the PM lock, point in time.

For each slate in analysis/nba/daily/ and each window, from what was known at that lock (never closing values):

  AM   ADP at the AM board (adp_am), our Proj then (ours_am; before 2026-10-28 no board number was saved, so the
       mirror's morning file, ours_raw), his tag then (injury_am), our chance he plays then (play_am)
  PM   ADP at the PM board (adp_pm), ETR's upload as it stood then (etr_pm), his tag then (injury_pm), play_pm

the two ladders and the combined tier exactly as the board's Tiers button builds them (index.html, NBA_LADDER):
ladder A by ADP, ladder P by the projection, each with four lines at the biggest gap inside 2-5, 12-18, 19-25 and
27-33 (2-4, 8-12, 13-17, 18-22 on 4-drafter slates); a tier apart keeps the ADP tier with a VALUE / PRICEY flag,
two or more moves one tier toward P. Players tagged Q, D or GTD get a class: TRAP (P(play) x Proj lands in a lower
tier than ADP), SMASH (healthy a tier higher and P(play) 70%+), FAIR (healthy tier = ADP tier).

Writes analysis/nba/report/tier_history.csv, one row per slate, window and player, and prints the coverage.
Everything graded by tier reads from it.

  python3 scripts/nba_tier_history.py [--mirror ../br-adp-mirror]   (the mirror for Boom at each lock)
"""
import argparse, csv, functools, glob, json, math, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(HERE, "analysis", "nba", "report", "tier_history.csv")
MIN_TIER = {6: 4, 4: 3}     # T2-T4 on each ladder hold at least this many (2026-11-09)
MIN_T1 = 2                  # T1, the elite, at least 2
LADDER = {6: [(2, 5, 4), (12, 18, 15), (19, 25, 22), (27, 33, 30)], 4: [(2, 4, 3), (8, 12, 10), (13, 17, 15), (18, 22, 20)]}
SMASH_PLAY = 0.7
Q_TAG = re.compile(r"^(q|d|g)", re.I)
RULE_STEPS = {     # each tier's rule (index.html NBA_TIER_RULE_STEPS, nba_report.py TIER_RULES): (key, within), higher first
    # step 6's switches (2026-11-09): PM T2 and T4 ADP (2: ETR), provisional; PM T5 ADP; T5's ownership tiebreak paused
    # T5 both windows (2026-11-09, provisional; money RULE, the shadow decides): the less drafted within 2 projected points first
    "am": {1: [("adp", 2), ("boom", 0)], 2: [("adp", 0)], 3: [("proj", 3), ("adp", 0)],
           4: [("proj", 3), ("adp", 0)], 5: [("lev", 2), ("proj", 3), ("adp", 0)]},
    "pm": {1: [("projx", 0)], 2: [("adp", 2), ("projx", 0)], 3: [("proj", 0), ("adp", 0), ("boom", 0)],
           4: [("adp", 2), ("projx", 0)], 5: [("lev", 2), ("adp", 0)]},
}
PM_Q_PUSH = 2      # PM window: a Questionable player is ordered two tiers back (lean adopted 2026-11-09; "old" rules only)
# The 2026-11-13 redesign (index.html NBA_RULESET; the same rules, one update): "old" until the operator's check
RULESET = "new"            # switched 2026-11-13
R6 = {6: 30, 4: 20}            # T4's last pick: the start of round 6, or earlier at an ADP gap of T4_GAP+ just before it
T4_GAP, T4_MIN = 2, 4          # T4 short of T4_MIN borrows from the bottom of T3
T5_LINE, T5_GRAY = 60, (50, 70)
MIN_FLOOR = 20                 # T5: only players projected for 20+ minutes (T5 dud rates, 2026-11-13)
Q_FALL = 6                     # a Q player whose ADP fell this many picks since the tag (across slates: this many players passed him) goes below the cut
DEFAULT_RANKED = 44            # the board's ranked list (NBA_DEFAULT_RANKED): T5 ends there, the rest sorts by projection
CEIL = (1.045, 7.31)           # index.html NBA_CEIL: the board's Proj from a median, to read ETR's median back out
FIELD_MODEL = os.path.join(HERE, "analysis", "nba", "contests", "field_model.json")
MIRROR = None
COLS = ["date", "slate", "pod", "window", "sample", "board", "player_id", "name", "team", "adp", "proj", "proj_src", "a_tier", "p_tier",
        "tier", "flag", "tag", "q_class", "play", "exp_tier", "actual", "min", "played", "scratched", "breaker",
        "your_rank", "your_tier", "built", "boom", "drafted", "proj_min", "pre_tag_adp", "pre_tag_src", "pre_tag_passed"]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def lines(vals, spec, min_size, unconstrained=False):
    """The board's nbaLadderLines: per window, the rank k (a line ends a tier at k) with the biggest step
    vals[k-1] -> vals[k], among the ranks that leave T2-T4 at least min_size players and T1 at least MIN_T1 (the
    next-biggest gap when the biggest breaks that); ties go to the rank nearest the window's start. unconstrained: no minimum."""
    out, prev, n = [], 0, len(vals)
    for j, (lo, hi, start) in enumerate(spec):
        least = prev + (1 if unconstrained else MIN_T1 if j == 0 else min_size)
        most = n - 1 if unconstrained or j < len(spec) - 1 else n - min_size
        best, gap = None, -math.inf
        for k in range(max(lo, least), min(hi, most, n - 1) + 1):
            g = abs(vals[k - 1] - vals[k])
            if g > gap + 1e-9 or (abs(g - gap) <= 1e-9 and abs(k - start) < abs(best - start)):
                best, gap = k, g
        if best is None:
            best = min(max(least, start), n)
        out.append(best)
        prev = best
    return out


def tier_of(rank, ls):
    return 1 + sum(1 for k in ls if rank > k)


def pod_size(rows):
    """4 on the 24-pick small slates, else 6 (as the morning report)."""
    return 4 if max((num(r["adp_close"]) or num(r["adp_am"]) or 0) for r in rows) <= 28 else 6


WINDOWS = {
    "am": {"adp": ["adp_am"], "proj": [("ours_am", "ours"), ("ours_raw", "ours_raw")], "tag": "injury_am", "play": "play_am",
           "rank": "am_rank", "tier": "am_tier", "built": "am_built"},
    "pm": {"adp": ["adp_pm", "adp_close"], "proj": [("etr_pm", "etr"), ("etr_last", "etr_last")], "tag": "injury_pm",
           "play": "play_pm", "rank": "pm_rank", "tier": "pm_tier", "built": "pm_built"},
}


LEV_GAP = 10       # the T5 less-drafted tiebreak: drafted% at least this far apart (index.html NBA_LEV_GAP)


def lev_first(x, y, within):
    """The T5 tiebreak (key "lev"): within `within` projected points, drafted% LEV_GAP+ apart, ADP within 4, both 2%+:
    -1 if x (the less drafted) goes first, 1 if y, None where it doesn't apply. drafted is stored negative."""
    a, b, pa, pb = x.get("drafted"), y.get("drafted"), x.get("projx"), y.get("projx")
    if None in (a, b, pa, pb) or abs(pa - pb) > within or abs(a - b) < LEV_GAP or abs(x["adp"] - y["adp"]) > 4 or min(-a, -b) < 2:
        return None
    return -1 if a > b else 1


def lev_pass(order, within):
    """The rule's order with the T5 tiebreak: neighbours swapped while the lower one goes first by lev_first, until none
    moves (index.html nbaRuleSort). It ends: each swap puts a less-drafted player ahead of a more-drafted one."""
    out, moved = list(order), True
    while moved:
        moved = False
        for j in range(len(out) - 1):
            if lev_first(out[j], out[j + 1], within) == 1:
                out[j], out[j + 1] = out[j + 1], out[j]
                moved = True
    return out


def rule_sort(items, steps):
    """The rule's order (nba_report.py rule_order): each step's key, higher first, unless within its margin. The T5
    tiebreak ("lev") is applied after the rule's order (lev_pass)."""
    lev = next((s for s in steps if s[0] == "lev"), None)
    if lev:
        return lev_pass(rule_sort(items, [s for s in steps if s[0] != "lev"]), lev[1])

    def cmp(x, y):
        for key, within in steps + [("projx", 0), ("adp", 0)]:
            a, b = x.get(key), y.get(key)
            if a is None or b is None or a == b or abs(a - b) <= within:
                continue
            if key == "drafted" and (abs(x["adp"] - y["adp"]) > 4 or min(-a, -b) < 2):
                continue
            return -1 if a > b else 1
        return 0
    return sorted(items, key=functools.cmp_to_key(cmp))


def booms(rows, adp_col, proj_col):
    """{player_id: the board's Boom %} at this lock (scripts/nba_boom_ties.py), or {} without --mirror."""
    if not MIRROR:
        return {}
    import nba_boom_ties as B
    mo = B.morning_at(MIRROR, rows[0]["date"])
    items = []
    for r in rows:
        m, a, v = mo.get(B.norm(r["name"])), num(r.get(adp_col)), num(r.get(proj_col))
        if a is None or v is None or not m or m.get("ppm") is None:
            continue
        items.append({"adp": a, "x": B.median_of_proj(v), "m": m, "r": r})
    if len(items) < 13:
        return {}
    bars = B.bars(items)
    return {it["r"]["player_id"]: B.chance(B.BOOM, it["x"], bars[id(it)], it["m"]) for it in items}


def build(rows, date, slate, window, meta):
    w = WINDOWS[window]
    pod = pod_size(rows)
    cap = 24 if pod == 4 else 36
    adp_col = next((c for c in w["adp"] if any(num(r.get(c)) is not None for r in rows)), None)
    src = next(((c, name) for c, name in w["proj"] if any(num(r.get(c)) is not None for r in rows)), (None, ""))
    if adp_col is None or src[0] is None:
        return [], {"date": date, "window": window, "skip": "no ADP" if adp_col is None else "no projection"}
    adp = lambda r: min(num(r.get(adp_col)), cap) if num(r.get(adp_col)) is not None else cap
    proj = lambda r: num(r.get(src[0]))
    pool = [r for r in rows if num(r.get(adp_col)) is not None or proj(r) is not None]
    A = sorted(pool, key=lambda r: (adp(r), -(proj(r) if proj(r) is not None else -1e9)))
    P = sorted(pool, key=lambda r: (-(proj(r) if proj(r) is not None else -1e9), adp(r)))
    va, vp = [adp(r) for r in A], [max(proj(r), 0) if proj(r) is not None else 0 for r in P]
    la, lp = lines(va, LADDER[pod], MIN_TIER[pod]), lines(vp, LADDER[pod], MIN_TIER[pod])
    if RULESET == "new":
        la = la[:3] + [t4_line(va, pod, la[2])]
    moved = sum(a != b for a, b in zip(la + lp, lines(va, LADDER[pod], 0, True) + lines(vp, LADDER[pod], 0, True)))
    at = {r["player_id"]: tier_of(i + 1, la) for i, r in enumerate(A)}
    pt = {r["player_id"]: tier_of(i + 1, lp) for i, r in enumerate(P)}
    pvals = [(r["player_id"], proj(r)) for r in P if proj(r) is not None]
    # breakers: 90th percentile (nearest rank) of FP in his ADP round band, by the window's ADP
    graded = sorted([r for r in pool if num(r["actual"]) is not None], key=adp)
    bands = {}
    for i, r in enumerate(graded):
        bands.setdefault(min(i // pod, 6), []).append(r)
    brk = set()
    for rs in bands.values():
        a = sorted(num(r["actual"]) for r in rs)
        cut = a[math.ceil(0.9 * len(a)) - 1]
        brk |= {r["player_id"] for r in rs if num(r["actual"]) >= cut}
    boom = booms(rows, adp_col, src[0])
    curve = json.load(open(FIELD_MODEL))["drafted"].get(str(pod), []) if os.path.exists(FIELD_MODEL) else []
    priced = sorted((r for r in pool if num(r.get(adp_col)) is not None), key=adp)
    drafted = {r["player_id"]: (curve[i] if i < len(curve) else 0.0) for i, r in enumerate(priced)} if curve else {}
    out = []
    for r in pool:
        pid, a, p = r["player_id"], at[r["player_id"]], pt[r["player_id"]]
        d = a - p
        c = a - (1 if d > 0 else -1) if abs(d) >= 2 else a
        if RULESET == "new":
            if a == 5:
                c = 5                                    # round 6 is never in T4
            if c == 4 and d < 0:
                c = 5                                    # T4 PRICEY drops into T5
        tag, play, q, et = r.get(w["tag"]) or "", num(r.get(w["play"])), "", ""
        if Q_TAG.match(tag):
            v = proj(r)
            if play is not None and v is not None:
                e = play * v
                et = tier_of(1 + sum(1 for q2, x in pvals if x > e and q2 != pid), lp)
                q = "TRAP" if et > a else "SMASH" if p < a and play >= SMASH_PLAY else "FAIR" if p == a else ""
            else:
                q = "FAIR" if p == a else ""
        mins, act = num(r["min"]), num(r["actual"])
        out.append({"date": date, "slate": slate, "pod": pod, "window": window,
                    "sample": "primary" if window == "pm" or (src[1] == "ours" and ((meta.get("am") or {}).get("from") or "").startswith("Lock AM")) else "secondary",
                    "board": (meta.get(window) or {}).get("from", ""),
                    "player_id": pid, "name": r["name"], "team": r["team"], "adp": num(r.get(adp_col)), "proj": proj(r),
                    "proj_src": src[1], "a_tier": a, "p_tier": p, "tier": c, "flag": "VALUE" if d > 0 else "PRICEY" if d < 0 else "",
                    "tag": tag, "q_class": q, "play": play if play is not None else "", "exp_tier": et,
                    "actual": "" if act is None else act, "min": "" if mins is None else mins,
                    "played": "" if mins is None else int(mins > 0), "scratched": "" if mins is None else int(mins == 0),
                    "breaker": "" if act is None else int(pid in brk),
                    "your_rank": r.get(w["rank"], ""), "your_tier": r.get(w["tier"], ""), "built": "",
                    "boom": round(boom[pid], 3) if pid in boom else "", "drafted": round(drafted[pid], 1) if pid in drafted else ""})
    pmin = proj_minutes(rows, window)                     # stored nightly: the minutes the board's floor reads
    for x in out:
        x["proj_min"] = round(pmin[x["player_id"]], 1) if pmin.get(x["player_id"]) is not None else ""
    if RULESET == "new":
        new_order(out, pool, rows, adp, window, pod, date, slate, meta, boom, drafted)
        info = {"date": date, "window": window, "pod": pod, "adp_col": adp_col, "proj_src": src[1], "lines_a": la, "lines_p": lp,
                "n": len(out), "moved": moved, "tags": sum(1 for x in out if Q_TAG.match(x["tag"])),
                "play": sum(1 for x in out if x["play"] != ""), "board": (meta.get(window) or {}).get("from", "")}
        return out, info
    # the button's order: tier, then VALUE / no flag / PRICEY, each in the tier's rule for the window
    keyed = []
    for x in out:
        v = x["proj"]
        keyed.append({"row": x, "adp": -adp(next(r for r in pool if r["player_id"] == x["player_id"])),
                      "proj": float(int(v + 0.5)) if v is not None else None, "projx": v,
                      "boom": boom.get(x["player_id"]), "drafted": -drafted[x["player_id"]] if x["player_id"] in drafted else None,
                      "order_tier": min(5, x["tier"] + PM_Q_PUSH) if window == "pm" and re.match(r"^q", x["tag"], re.I) else x["tier"]})
    rank = 0
    for t in range(1, 6):
        for f in ("VALUE", "", "PRICEY"):
            for k in rule_sort([k for k in keyed if k["order_tier"] == t and k["row"]["flag"] == f], RULE_STEPS[window][t]):
                rank += 1
                k["row"]["built"] = rank
    info = {"date": date, "window": window, "pod": pod, "adp_col": adp_col, "proj_src": src[1], "lines_a": la, "lines_p": lp,
            "n": len(out), "moved": moved, "tags": sum(1 for x in out if Q_TAG.match(x["tag"])),
            "play": sum(1 for x in out if x["play"] != ""), "board": (meta.get(window) or {}).get("from", "")}
    return out, info


def t4_line(vals, pod, prev):
    """T4's last rank (index.html nbaT4Line): the start of round 6, or earlier at an ADP gap of T4_GAP+ in the three ranks before."""
    r6, best, gap = R6[pod], None, -math.inf
    for k in range(max(prev + 1, r6 - 3), min(r6 - 1, len(vals) - 1) + 1):
        g = vals[k] - vals[k - 1]
        if g > gap + 1e-9 or (abs(g - gap) <= 1e-9 and best is not None and abs(k - r6) < abs(best - r6)):
            best, gap = k, g
    return best if best is not None and gap >= T4_GAP else min(r6, len(vals))


def elites(projs):
    v = sorted(projs, reverse=True)[:4]
    if len(v) < 2:
        return 1
    gaps = [v[i] - v[i + 1] for i in range(min(3, len(v) - 1))]
    return 1 + gaps.index(max(gaps))


def t5_band(d):
    d = d or 0
    return 0 if d < T5_GRAY[0] else 1 if d < T5_LINE else 2 if d < T5_GRAY[1] else 3


_TAGS = {}


def q_tag_adp(date, slate, window, meta):
    """{player_id: (his ADP before the tag, source, players passed)} for every player Questionable at the window's lock (the
    mirror): "pre-tag" the last snapshot before the tag on this slate; tagged from the slate's first snapshot, "previous
    slate" his ADP in the newest snapshot of the last earlier main slate (up to 4 back) where he was untagged (the poller's
    pre_tag_src), with the players behind him there who are ahead of him at the window (the poller's pre_tag_passed: the
    fall across slates, since two slates' ADPs don't compare); else "first tagged", his ADP in the first snapshot that had
    him tagged (the board's device sighting). Players passed is None except across slates."""
    key = (date, window)
    if key in _TAGS or not MIRROR:
        return _TAGS.get(key, {})
    import datetime as dt
    import nba_daily as daily
    mirror = daily.Mirror(MIRROR)
    lock = dt.datetime.fromisoformat(meta["lock"])
    s = next((x for x in mirror.main_slates(lock - dt.timedelta(hours=1), lock + dt.timedelta(hours=1)) if x["label"] == slate), None)
    until = lock
    w = meta.get(window) or {}
    if w.get("at"):
        until = min(lock, dt.datetime.fromisoformat(w["at"].replace("Z", "+00:00")))
    snaps = [(t, {p["player_id"]: p for p in players}) for t, players in (mirror.snapshots(s) if s else []) if t <= until]
    out = {}
    if snaps:
        for pid, p in snaps[-1][1].items():
            if (p.get("injury") or "")[:1].lower() != "q":
                continue
            first = p.get("adp")
            for t, tab in reversed(snaps[:-1]):
                q = tab.get(pid)
                if q is None:
                    continue
                if (q.get("injury") or "")[:1].lower() != "q":
                    out[pid] = (q.get("adp"), "pre-tag", None)    # the poller's pre_tag_adp: the last snapshot before the tag
                    break
                first = q.get("adp")
            else:
                now = {k: v.get("adp") for k, v in snaps[-1][1].items() if v.get("adp") is not None}
                out[pid] = earlier_untagged(mirror, s, pid, now) or (first, "first tagged", None)
    _TAGS[key] = out
    return out


def earlier_untagged(mirror, slate, pid, now, look=4):
    """(ADP, "previous slate", players passed) from the newest snapshot of the last earlier main slates where he was priced
    and untagged, else None. Players passed: those behind him on that snapshot who are ahead of him in `now` ({player_id:
    ADP} at the window), among players priced on both (build_mirror.passed)."""
    import datetime as dt
    for s in reversed(mirror.main_slates(slate["lock"] - dt.timedelta(days=10), slate["lock"] - dt.timedelta(hours=1))[-look:]):
        for t, players in reversed(mirror.snapshots(s)):
            p = next((p for p in players if p["player_id"] == pid), None)
            if p is not None and (p.get("injury") or "")[:1].lower() != "q":
                then = {q["player_id"]: q.get("adp") for q in players if q.get("adp") is not None}
                k = None
                if pid in then and pid in now:
                    k = sum(1 for q in then if q != pid and q in now and then[q] > then[pid] and now[q] < now[pid])
                return p.get("adp"), "previous slate", k
    return None


def proj_minutes(rows, window):
    """{player_id: the minutes the board's floor reads}: box-score minutes (usual_min) in the morning; ETR-implied in the
    afternoon (index.html nbaStatRows: ETR's median over his usual points a minute, scaled so the typical 20+ minute
    player stays at his box-score level)."""
    usual = {r["player_id"]: num(r.get("usual_min")) for r in rows}
    if window == "am":
        return usual
    implied = {}
    for r in rows:
        v, ppm, u = num(r.get("etr_pm")), num(r.get("fp_pm")), usual[r["player_id"]]
        if v is not None and ppm and ppm > 0 and u is not None:
            implied[r["player_id"]] = ((v - 0.75 * CEIL[1]) / (0.25 + 0.75 * CEIL[0])) / ppm
    ratios = sorted(implied[k] / usual[k] for k in implied if usual[k] and usual[k] >= 20)
    ratio = ratios[len(ratios) // 2] if ratios else None
    return {k: (implied[k] / ratio if k in implied and ratio else usual[k]) for k in usual}


def new_order(out, pool, rows, adp, window, pod, date, slate, meta, boom, drafted):
    """The button's order under the 2026-11-13 rules (index.html nbaBuildLaddersNew): sets each row's tier and built rank."""
    by = {r["player_id"]: r for r in pool}
    seen = q_tag_adp(date, slate, window, meta)
    pmin = proj_minutes(rows, window)
    qteams = {x["team"] for x in out if re.match(r"^q", x["tag"], re.I)}
    for x in out:
        x["_qlast"] = x["_qtop"] = False
        if re.match(r"^q", x["tag"], re.I):
            a0, src, k = seen.get(x["player_id"]) or (None, "", None)
            x["pre_tag_adp"], x["pre_tag_src"] = ("", "") if a0 is None else (a0, src)
            x["pre_tag_passed"] = "" if k is None else k
            # across slates the fall is the players who passed him; on this slate, the raw pick difference
            fall = k if k is not None else (x["adp"] - a0 if a0 is not None and x["adp"] is not None else None)
            if fall is not None and fall >= Q_FALL:
                x["_qlast"] = True
            elif x["tier"] == 1:
                x["tier"], x["_qtop"] = 2, True
    t1_proj = [x["proj"] for x in out if x["a_tier"] == 1 and x["proj"] is not None]
    brk = (9 if pod == 4 else 13) - elites(t1_proj)

    def k(x):
        v = x["proj"]
        return {"row": x, "adp": -adp(by[x["player_id"]]), "rawadp": adp(by[x["player_id"]]),
                "proj": float(int(v + 0.5)) if v is not None else None, "projx": v, "boom": boom.get(x["player_id"]),
                "qmate": 1 if not x["tag"] and x["team"] in qteams else 0,
                "min": pmin.get(x["player_id"]), "dr": drafted.get(x["player_id"], 0.0) or 0.0}
    K = [k(x) for x in out]
    am = window == "am"
    T1 = [("adp", 2), ("qmate", 0), ("boom", 0)] if am else [("projx", 0), ("qmate", 0)]
    MID = [("adp", 0), ("qmate", 0)] if am else [("proj", 0), ("qmate", 0), ("adp", 0), ("boom", 0)]
    tier = lambda t: [z for z in K if not z["row"]["_qlast"] and z["row"]["tier"] == t]
    groups = lambda lst: [z for f in ("VALUE", "", "PRICEY") for z in rule_sort([y for y in lst if y["row"]["flag"] == f], MID)]
    t1 = rule_sort([z for z in tier(1)], T1)
    qtop = rule_sort([z for z in tier(2) if z["row"]["_qtop"]], T1)
    rest2 = [z for z in tier(2) if not z["row"]["_qtop"]]
    if am:
        t2 = rule_sort(rest2, [("adp", 0), ("qmate", 0)])
    else:
        t2 = rule_sort([z for z in rest2 if z["rawadp"] < brk], [("adp", 2), ("qmate", 0), ("projx", 0)]) + \
            rule_sort([z for z in rest2 if z["rawadp"] >= brk], [("projx", 0), ("qmate", 0)])
    t3, t4, borrowed = groups(tier(3)), groups(tier(4)), []
    while len(t4) + len(borrowed) < T4_MIN and len(t3) > 1:
        b = t3.pop()
        b["row"]["tier"] = 4
        borrowed.insert(0, b)
    t4 = borrowed + t4
    floor = lambda z: z["min"] is None or z["min"] >= MIN_FLOOR
    by_proj = lambda z: (-(z["projx"] if z["projx"] is not None else -1e9), z["rawadp"])
    # 4-drafter nights: no drafted% line (until a Friday shows one); the dropped T4 PRICEY players right after T5's top 3,
    # exempt from the line (index.html nbaBuildLaddersNew)
    band = (lambda z: 0) if pod == 4 else (lambda z: t5_band(z["dr"]))
    drop = lambda z: z["row"]["a_tier"] <= 4 and z["row"]["flag"] == "PRICEY"     # a T4 PRICEY player dropped into T5
    eligible = sorted([z for z in tier(5) if floor(z) and band(z) <= 1 and not drop(z)], key=lambda z: (band(z),) + by_proj(z))
    eligible = eligible[:3] + sorted([z for z in tier(5) if floor(z) and drop(z)], key=by_proj) + eligible[3:]
    head = t1 + qtop + t2 + t3 + t4
    t5 = eligible[:max(0, DEFAULT_RANKED - len(head))]
    in5 = {id(z) for z in t5}
    below = sorted([z for z in tier(5) if id(z) not in in5] + [z for z in K if z["row"]["_qlast"]], key=by_proj)
    for z in below:
        z["row"]["tier"] = 6                                  # below the cut: out of T5, sorted by projection
    for i, z in enumerate(head + t5 + below):
        z["row"]["built"] = i + 1
    for x in out:
        x.pop("_qlast", None)
        x.pop("_qtop", None)


def main():
    global MIRROR
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", help="a full clone of br-adp-mirror, for Boom at each lock")
    MIRROR = ap.parse_args().mirror
    meta = json.load(open(os.path.join(DAILY, "meta.json")))
    rows_out, infos = [], []
    for path in sorted(glob.glob(os.path.join(DAILY, "*_main.csv"))):
        name = os.path.basename(path)
        rows = list(csv.DictReader(open(path)))
        if not rows:
            continue
        for window in ("am", "pm"):
            got, info = build(rows, name[:10], rows[0]["slate"], window, meta.get(name, {}))
            rows_out += got
            infos.append(info)
    with open(OUT, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=COLS)
        wr.writeheader()
        wr.writerows(rows_out)
    print("| Slate | Window | Pod | Board | ADP | Projection | ADP lines | Proj lines | Lines moved by the minimum | Tagged Q/D/GTD | With P(play) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for i in infos:
        if i.get("skip"):
            print("| %s | %s | - | - | - | - | %s | | | |" % (i["date"], i["window"].upper(), i["skip"]))
            continue
        print("| %s | %s | %d | %s | %s | %s | %s | %s | %d | %d | %d |" % (
            i["date"], i["window"].upper(), i["pod"], i["board"] or "-", i["adp_col"], i["proj_src"],
            ", ".join(map(str, i["lines_a"])), ", ".join(map(str, i["lines_p"])), i["moved"], i["tags"], i["play"]))
    done = [i for i in infos if not i.get("skip")]
    print("\nThe minimum moved %d of %d lines (%d of %d slate-windows had at least one moved)" % (
        sum(i["moved"] for i in done), 8 * len(done), sum(1 for i in done if i["moved"]), len(done)))
    print("\n%d rows -> %s" % (len(rows_out), os.path.relpath(OUT, HERE)))


if __name__ == "__main__":
    main()
