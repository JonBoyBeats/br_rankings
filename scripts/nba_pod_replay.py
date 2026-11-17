"""Pod replay: ranking lists graded by team outcomes, through the night's real pods.

For each night and window, every real pod and every seat in it: that drafter is replaced by "me" drafting off a ranking
list (highest available at each of my picks, as Underdog's autodraft does). The other drafters keep their real picks;
when I've taken a player one of them drafted, that drafter takes the next available player by the window's ADP. Rounds
1-5 follow the list strictly; the round-6 pick is drawn evenly from the top 6 still available on the list, one seeded
draw per pod and seat shared by every list. My team is scored on the night's real box scores, a scratched player swapped
by Underdog's rule off the same list, and placed in the contest's real standings (the other teams' scores as they were).

Lists, per window: (a) my locked list, (b) the Tiers button's list (no manual moves), (c1-c5) my list with one button
tier's moves undone (that tier's players back at their button ranks, everyone else in my order around them), (d) ADP,
(e) ETR's PM projections, highest first. Each list continues past its last ranked player in ADP order.

Pick order is estimated: Underdog doesn't publish draft slots or pick order. Each team's picks, sorted by the ADP each was
taken at, are its rounds 1-6, and the pod's seats are the snake slots that fit those ADPs best (nba_swaps' fit).

Writes analysis/nba/report/pod_replay.md (results only) and pod_replay.json (season paired differences and the same since
each rule_dates.json date, for the Results dashboard). The Friday report (nba_money_friday.py) reruns it weekly.

  python3 scripts/nba_pod_replay.py [--mirror ../br-adp-mirror] [--since YYYY-MM-DD] [--dates D1,D2]
"""
import argparse, collections, datetime as dt, hashlib, itertools, json, math, os, random, re, statistics as st, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_money as M     # noqa: E402  nights, teams, windows, place_and_pay
import nba_swaps as S     # noqa: E402  snake pick numbers

REP = M.REP
OUT_MD = os.path.join(REP, "pod_replay.md")
OUT_JSON = os.path.join(REP, "pod_replay.json")
LISTS = ["a", "b", "c1", "c2", "c3", "c4", "c5", "d", "e", "f1", "f2", "f3", "f4", "f5"]
NAMES = {"a": "(a) my locked list", "b": "(b) the button's list", "d": "(d) ADP", "e": "(e) ETR (PM)",
         **{"c%d" % k: "(c%d) mine, T%d's moves undone" % (k, k) for k in range(1, 6)},
         **{"f%d" % k: "(f%d) mine (PM), T%d in ETR's order" % (k, k) for k in range(1, 6)}}
R6 = 6            # the round-6 pick: drawn from the top this many still available ...
R6_WEIGHTS = (38, 25, 14, 11, 6, 6)   # ... weighted to my real habit (the first replay's fidelity check, 2026-11-17)
MY_DRAWS = 200    # round-6 redraws at my real seats, for the top-1% spread
RULE_DATES = os.path.join(REP, "rule_dates.json")
RESAMPLES = 1000
num = M.num


# ---------------------------------------------------------------- the lists
def lists_for(rec, w):
    """{list: [player ids]} for the window, each finished in ADP order; and the ADP order itself."""
    out_now = {p for p, r in rec.items() if r.get("injury_" + w) == "Out"}
    pool = [p for p in rec if p not in out_now]
    adp = {p: num(rec[p].get("adp_" + w)) if num(rec[p].get("adp_" + w)) is not None else num(rec[p].get("adp_close")) for p in pool}
    by_adp = sorted(pool, key=lambda p: (adp[p] is None, adp[p] or 0, p))
    pset = set(pool)

    def finish(head):
        head = [p for p in head if p in pset]
        seen = set(head)
        return head + [p for p in by_adp if p not in seen]

    col = lambda k: {p: int(float(rec[p][k])) for p in pool if rec[p].get(k) not in (None, "")}
    rank = col(w + "_rank")
    if not rank:
        return None
    mine = sorted(rank, key=rank.get)
    L = {"a": finish(mine), "d": by_adp}
    built, tier = col(w + "_built"), col(w + "_c")
    if built and len(built) >= 0.8 * len(rank):
        L["b"] = finish(sorted(built, key=built.get))
        order_b = sorted(built, key=built.get)
        pos_b = {p: i for i, p in enumerate(order_b)}          # the button's position, 0-based (ranks can skip)
        for k in range(1, 6):
            back = {pos_b[p]: p for p in order_b if tier.get(p) == k}
            if not back:
                continue
            rest = iter([p for p in mine if p not in back.values()])
            out = []
            for i in range(len(mine) + len(back)):
                p = back.get(i) or next(rest, None)
                if p is not None:
                    out.append(p)
            out += list(rest)
            L["c%d" % k] = finish(out)
    if w == "pm":
        etr = {p: num(rec[p].get("etr_pm")) for p in pool}
        if sum(v is not None for v in etr.values()) >= 0.5 * len(rank):
            L["e"] = finish(sorted((p for p in pool if etr[p] is not None), key=lambda p: (-etr[p], adp[p] or 999)))
        mt = col(w + "_tier")                                   # my tiers at the lock
        if "e" in L and mt:
            for k in range(1, 6):                               # tier k's places in my list, filled in ETR's order
                members = [p for p in mine if mt.get(p) == k]
                if len(members) < 2:
                    continue
                it = iter(sorted(members, key=lambda p: (etr[p] is None, -(etr[p] or 0), rank[p])))
                L["f%d" % k] = finish([next(it) if mt.get(p) == k else p for p in mine])
    return L


# ---------------------------------------------------------------- pods
def pod_plan(ts, pod):
    """Each team's picks in round order (cheapest ADP-at-draft first; None for an uncredited swap) and the pod's snake
    pick sequence [(round, team index)] from the best-fitting seat for each team."""
    plans, adps = [], []
    for t in ts:
        picks = sorted(zip(t["paid"], t["paid_pid"]), key=lambda x: x[0])
        plans.append([p for _, p in picks])
        adps.append([a for a, _ in picks])
    cost = [[sum(abs(a - S.snake(r, k, pod)) for r, a in enumerate(ad, 1)) for k in range(1, pod + 1)] for ad in adps]
    best = min(itertools.permutations(range(pod)), key=lambda perm: sum(cost[i][perm[i]] for i in range(pod)))
    team_at = {best[i]: i for i in range(pod)}               # slot (0-based) -> team index
    seq = [(r, team_at[k if r % 2 else pod - 1 - k]) for r in range(1, 7) for k in range(pod)]
    return plans, seq


def replay(plans, seq, s, L, by_adp, u, probe=None):
    """My six picks off list L at seat s, the pod's drafted set, and (probe) the top of L still available at my
    round-6 pick."""
    taken, mine, i_l, i_a, top = set(), [], 0, 0, None
    for r, i in seq:
        if i == s:
            while L[i_l] in taken:
                i_l += 1
            if r < 6:
                p = L[i_l]
            else:
                avail = [q for q in L[i_l:i_l + 60] if q not in taken]
                p = avail[min(u, len(avail) - 1)]
                if probe:
                    top = avail[:15]
            mine.append(p)
            taken.add(p)
        else:
            q = plans[i][r - 1]
            if q is None:
                continue
            if q in taken:
                while by_adp[i_a] in taken:
                    i_a += 1
                q = by_adp[i_a]
            taken.add(q)
    return mine, taken, top


def draw(*key):
    """The round-6 place (0-based) for a seeded key, weighted by R6_WEIGHTS."""
    x = int(hashlib.md5("|".join(map(str, key)).encode()).hexdigest(), 16) % sum(R6_WEIGHTS)
    for i, wt in enumerate(R6_WEIGHTS):
        if x < wt:
            return i
        x -= wt
    return 0


# ---------------------------------------------------------------- a night
def ud_points(n):
    """Each player's points as Underdog scored them: the box score, corrected where the leaderboards' team totals say otherwise."""
    pts = {p: num(r.get("actual")) for p, r in n["rec"].items()}
    teams = [t for c in n["contests"] for t in n["teams"][c["contest_id"]]]
    fixed = {}
    nbad = lambda: sum(1 for t in teams if abs(t["points"] - sum(pts.get(p) or 0 for p in t["picks"])) > 0.05)
    for _ in range(30):
        bad = collections.defaultdict(list)
        for t in teams:
            d = round(t["points"] - sum(pts.get(p) or 0 for p in t["picks"]), 1)
            if abs(d) > 0.05:
                for p in t["picks"]:
                    bad[p].append(d)
        if not bad:
            break
        before, done = nbad(), False
        for p, ds in sorted(bad.items(), key=lambda kv: -len(kv[1]))[:10]:
            corr, k = collections.Counter(ds).most_common(1)[0]
            if k < 2:
                continue
            old = pts.get(p)
            pts[p] = (old or 0) + corr
            if nbad() < before:
                fixed[p] = (fixed.get(p, (0, 0))[0] + corr, k)
                done = True
                break
            pts[p] = old
        if not done:
            break
    left = sum(1 for t in teams if abs(t["points"] - sum(pts.get(p) or 0 for p in t["picks"])) > 0.05)
    return pts, fixed, left, len(teams)


def night(n):
    rec, sw = n["rec"], n["swaps"] or {}
    actual, _, _, _ = ud_points(n)
    actual = {p: v or 0.0 for p, v in actual.items()}
    team_of = {p: r.get("team") for p, r in rec.items()}
    tip = sw.get("tip") or {}
    out = sw.get("out") or {}
    kept = sw.get("kept") or collections.Counter()
    swaps_of = sw.get("swaps") or {}
    scratched = {o for o in out if len(swaps_of.get(o, [])) >= kept.get(o, 0)}   # swapped at least as often as kept
    sat = {p for p, r in rec.items() if r.get("min") == "0.0"}
    when = collections.defaultdict(list)
    for x in sw.get("credited", []):
        tt = tip.get(team_of.get(x["swap"]))
        if tt:
            when[x["out"]].append(tt)
    swap_time = {o: min(when[o]) if when[o] else tip.get(team_of.get(o)) for o in scratched}

    def score(team, L, taken):
        pts, used, swaps = 0.0, set(team), 0
        for p in team:
            if p not in scratched:
                pts += actual.get(p, 0.0)
                continue
            stt = swap_time.get(p)
            tgt = next((q for q in L if q not in taken and q not in used and q not in sat and q not in scratched
                        and (stt is None or (tip.get(team_of.get(q)) and tip[team_of[q]] >= stt))), None)
            if tgt:
                used.add(tgt)
                pts += actual.get(tgt, 0.0)
                swaps += 1
        return pts, swaps

    res = collections.defaultdict(lambda: collections.defaultdict(float))   # (window, list) -> sums
    fins = collections.defaultdict(list)                                    # window -> (a)'s replayed finish percentiles
    mine_rows = []                                                          # my real seats: real vs (a) at the seat
    r6 = []                                                                 # my real round-6 pick's place among (a)'s top available
    my_t1 = {"seats": 0, "real": 0, "list": 0, "draws": [0] * MY_DRAWS}       # top-1% counts at my real seats
    lists = {w: lists_for(rec, w) for w in ("am", "pm")}
    for c in n["contests"]:
        pod, ts_all, nn = c["pod_size"], n["teams"][c["contest_id"]], len(n["teams"][c["contest_id"]])
        pods = collections.defaultdict(list)
        for t in ts_all:
            pods[t["draft_id"]].append(t)
        for did, ts in pods.items():
            if len(ts) != pod:
                continue
            w = collections.Counter(t["window"] for t in ts).most_common(1)[0][0]
            Lw = lists.get(w)
            if not Lw:
                continue
            plans, seq = pod_plan(ts, pod)
            for s, t in enumerate(ts):
                u = draw(n["date"], c["contest_id"], did, s)
                seen = {}
                for name, L in Lw.items():
                    if name != "a" and L == Lw["a"]:
                        got = seen["a"]
                    else:
                        team, taken, top = replay(plans, seq, s, L, Lw["d"], u, probe=(name == "a" and t["mine"]))
                        pts, nsw = score(team, L, taken)
                        place, pay = M.place_and_pay(c, t, pts)
                        got = (place / nn, place <= math.ceil(nn / 100), place <= math.ceil(nn / 10), pay, nsw, team, top)
                    seen[name] = got
                    fin, t1, t10, pay, nsw, team, top = got
                    a = res[(w, name)]
                    a["n"] += 1
                    a["top1"] += t1
                    a["top10"] += t10
                    a["fin"] += fin
                    a["cash"] += pay > 0
                    a["pay"] += pay
                    a["fee"] += c["fee"]
                    a["swaps"] += nsw
                    if name == "a":
                        fins[w].append(fin)
                        if t["mine"]:
                            real6 = plans[s][5]
                            mine_rows.append({"w": w, "fin": t["fin"], "t1": t["top"][1], "t10": t["top"][10], "pay": t["payout"],
                                              "fee": c["fee"], "rfin": fin, "rt1": t1, "rt10": t10, "rpay": pay})
                            r6.append({"w": w, "real": real6, "top": top, "drawn": team[5],
                                       "pos": (top.index(real6) + 1) if top and real6 in top else None})
                            my_t1["seats"] += 1
                            my_t1["real"] += t["top"][1]
                            my_t1["list"] += t1
                            for k in range(MY_DRAWS):
                                tm, tk, _ = replay(plans, seq, s, L, Lw["d"], draw(n["date"], c["contest_id"], did, s, k))
                                pl, _ = M.place_and_pay(c, t, score(tm, L, tk)[0])
                                my_t1["draws"][k] += pl <= math.ceil(nn / 100)
    for r in mine_rows:                                                     # where my real team lands among (a)'s replays
        f = fins.get(r["w"]) or [r["fin"]]
        r["beat"] = sum(1 for v in f if v > r["fin"]) / len(f)
    return {"date": n["date"], "res": {"%s|%s" % k: dict(v) for k, v in res.items()}, "mine": mine_rows, "r6": r6, "my_t1": my_t1,
            "lists": {w: sorted(L) for w, L in lists.items() if L}}


# ---------------------------------------------------------------- summaries
def pooled(nights, w, name, key):
    """Pooled rate of `key` over the nights' seats (fin: mean finish percentile)."""
    n = sum(x["res"].get("%s|%s" % (ww, name), {}).get("n", 0) for x in nights for ww in W(w))
    if not n:
        return None
    return sum(x["res"].get("%s|%s" % (ww, name), {}).get(key, 0) for x in nights for ww in W(w)) / n


def W(w):
    return ("am", "pm") if w == "both" else (w,)


def paired(nights, w, x, y, key, since=None):
    """(x) minus (y), pooled over the night-windows where both lists ran (same pods and seats), from `since` ({am, pm}
    dates) when given; the 80% range resamples nights."""
    cells = [[(n, ww) for ww in W(w) if n["res"].get("%s|%s" % (ww, x)) and n["res"].get("%s|%s" % (ww, y))
              and (not since or n["date"] >= since[ww])] for n in nights]
    cells = [c for c in cells if c]

    def fn(ns):
        flat = [cw for c in ns for cw in c]
        tot = sum(n["res"]["%s|%s" % (ww, x)]["n"] for n, ww in flat)
        if not tot:
            return None
        return sum(n["res"]["%s|%s" % (ww, x)][key] - n["res"]["%s|%s" % (ww, y)][key] for n, ww in flat) / tot
    v = fn(cells) if cells else None
    rng = M.boot_range(cells, fn) if v is not None else None
    return {"nights": len(cells), "diff": v, "lo": rng[0] if rng else None, "hi": rng[1] if rng else None}


def pp(v, scale=100, spec="%+.2f"):
    return "-" if v is None else spec % (v * scale)


def build(nights):
    md, js = [], {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "nights": [n["date"] for n in nights], "season": {}, "paired": {}, "by_night": []}
    keys = (("top1", "top-1%"), ("top10", "top-10%"), ("fin", "mean finish percentile"))
    # season table
    season = {}
    for w in ("am", "pm", "both"):
        for name in LISTS:
            n = sum(x["res"].get("%s|%s" % (ww, name), {}).get("n", 0) for x in nights for ww in W(w))
            if not n:
                continue
            ns = sum(1 for x in nights if any(x["res"].get("%s|%s" % (ww, name)) for ww in W(w)))
            fee = sum(x["res"].get("%s|%s" % (ww, name), {}).get("fee", 0) for x in nights for ww in W(w))
            pay = sum(x["res"].get("%s|%s" % (ww, name), {}).get("pay", 0) for x in nights for ww in W(w))
            season[(w, name)] = {"nights": ns, "seats": int(n), **{k: pooled(nights, w, name, k) for k in ("top1", "top10", "fin", "cash")},
                                 "roi": pay / fee - 1 if fee else None}
    js["season"] = {}
    for (w, name), v in season.items():
        js["season"].setdefault(w, {})[name] = {"nights": v["nights"], "seats": v["seats"],
                                                **{k: None if v[k] is None else round(100 * v[k], 3) for k in ("top1", "top10", "fin", "cash", "roi")}}
    # paired
    pairs = [("a", y) for y in LISTS[1:]]
    P = {}
    for w in ("am", "pm", "both"):
        for x, y in pairs:
            for k, _ in keys:
                r = paired(nights, w, x, y, k)
                if r["nights"]:
                    P[(w, x, y, k)] = r
    # for the Results dashboard: (a) minus each list, in percentage points (finish: percentile points, lower is better)
    js["paired_note"] = ("(a) my locked list minus each list, same pods and seats; diff/lo/hi in percentage points (fin: mean finish "
                         "percentile, negative = mine finished higher); lo-hi is the 80% range from resampling nights")
    js["labels"] = NAMES
    # since each rule's date: one block per distinct date, naming the rules that share it
    rd = json.load(open(RULE_DATES)) if os.path.exists(RULE_DATES) else {}
    groups = collections.defaultdict(list)
    for rid, v in rd.items():
        if not rid.startswith("_") and isinstance(v, dict) and re.match(r"\d{4}-\d\d-\d\d$", v.get("since") or ""):
            wd = v.get("windows") if isinstance(v.get("windows"), dict) else {}
            groups[(wd.get("am") or v["since"], wd.get("pm") or v["since"])].append(rid)
    SR = []
    for (am, pm), rids in sorted(groups.items()):
        blk = {"since": {"am": am, "pm": pm}, "rules": sorted(rids), "paired": {}}
        for w in ("am", "pm", "both"):
            for x, y in pairs:
                for k, _ in keys:
                    r = paired(nights, w, x, y, k, since={"am": am, "pm": pm})
                    if r["nights"]:
                        blk["paired"].setdefault(w, {}).setdefault(y, {})[k] = {
                            "nights": r["nights"], **{f: None if r[f] is None else round(100 * r[f], 3) for f in ("diff", "lo", "hi")}}
        SR.append(blk)
    js["since_rules"] = SR
    # top 1% at my real seats: real against (a), with the spreads
    T = [x["my_t1"] for x in nights if x["my_t1"]["seats"]]
    MT = None
    if T:
        dr = sorted(sum(t["draws"][k] for t in T) for k in range(MY_DRAWS))
        q = lambda v, f: v[int(f * (len(v) - 1))]
        lst, real, seats = sum(t["list"] for t in T), sum(t["real"] for t in T), sum(t["seats"] for t in T)
        gap = M.boot_range(T, lambda ns: sum(t["real"] - t["list"] for t in ns))
        lr = M.boot_range(T, lambda ns: sum(t["list"] for t in ns))
        mean_draws = st.mean(dr)
        MT = {"nights": len(T), "seats": seats, "real": real, "list": lst, "draws_median": q(dr, 0.5), "draws_lo": q(dr, 0.1),
              "draws_hi": q(dr, 0.9), "draws_mean": round(mean_draws, 1), "gap_lo": gap[0] if gap else None, "gap_hi": gap[1] if gap else None,
              "nights_lo": lr[0] if lr else None, "nights_hi": lr[1] if lr else None, "poisson": poisson_range(mean_draws)}
    js["my_seats_top1"] = MT
    js["paired"] = {}
    for (w, x, y, k), v in P.items():
        js["paired"].setdefault(w, {}).setdefault(y, {})[k] = {
            "nights": v["nights"], **{f: None if v[f] is None else round(100 * v[f], 3) for f in ("diff", "lo", "hi")}}
    # fidelity: my real round-6 pick's place among (a)'s top available
    r6 = [r for x in nights for r in x["r6"]]
    pos = collections.Counter(r["pos"] if r["pos"] is not None and r["pos"] <= R6 else ("7-15" if r["pos"] else "not in top 15") for r in r6)
    # actual vs (a)
    mine = [r for x in nights for r in x["mine"]]
    beat = [r["beat"] for r in mine]

    # ---- markdown
    def row_season(w):
        out = ["| List | Nights | Seats | Top 1% | Top 10% | Mean finish pct | Cash | ROI |", "|---|---|---|---|---|---|---|---|"]
        for name in LISTS:
            s_ = season.get((w, name))
            if s_:
                out.append("| %s | %d | %d | %.2f%% | %.1f%% | %.1f | %.0f%% | %+.0f%% |" % (
                    NAMES[name], s_["nights"], s_["seats"], 100 * s_["top1"], 100 * s_["top10"], 100 * s_["fin"], 100 * s_["cash"], 100 * s_["roi"]))
        return out

    def row_paired(w):
        out = ["| (a) minus | Nights | Top 1% (pts) | 80% range | Top 10% (pts) | 80% range | Mean finish pct (lower is better) | 80% range |",
               "|---|---|---|---|---|---|---|---|"]
        for x, y in pairs:
            if (w, x, y, "top1") not in P:
                continue
            cells = []
            for k, _ in keys:
                r = P[(w, x, y, k)]
                cells += [pp(r["diff"]), "%s to %s" % (pp(r["lo"]), pp(r["hi"])) if r["lo"] is not None else "-"]
            out.append("| %s | %d | %s |" % (NAMES[y], P[(w, x, y, "top1")]["nights"], " | ".join(cells)))
        return out

    head = summary(season, P, pos, r6, mine, beat, MT)
    md += ["# Pod replay: my NBA rankings graded by team outcomes", "",
           "Results only. Generated %s from %d nights (%s to %s)." % (js["generated"][:16].replace("T", " "), len(nights), nights[0]["date"], nights[-1]["date"]), ""]
    md += ["## Plain English", ""] + head + [""]
    md += ["## How it was run", "",
           "- Every real pod in every main-slate contest, every seat, each window's pods (the lock nearest the draft time, as the money "
           "engine sorts them). That seat's drafter becomes me, drafting off a list: the highest available at each of my picks.",
           "- The other drafters keep their real picks; when I've taken one of theirs, they take the next available by the window's ADP "
           "(their later picks stay as they were unless taken too).",
           "- **Pick order is estimated.** Underdog doesn't publish draft slots. Each team's picks, sorted by the ADP each was taken at, are its "
           "rounds 1-6; the pod's seats are the snake slots that fit those ADPs best (the swap crediting's fit).",
           "- Rounds 1-5 follow the list strictly. Round 6: drawn from the top %d still available on the list, weighted %s to match my real "
           "round-6 habit, one seeded draw per pod and seat, the same for every list." % (R6, "/".join(map(str, R6_WEIGHTS))),
           "- Scored on the night's box scores as Underdog scored them: a player's box score is corrected where the leaderboards' team totals disagree (stat corrections, 1-4.5 points, one or two players most nights; every night's teams then reconcile to within 3). A scratched player (0 minutes for a team that played, swapped at least as often as he was left on a real roster: a DNP kept on rosters scores 0) is swapped to the "
           "highest player on the same list left undrafted in the replayed pod whose game hadn't started at the swap (the earliest real "
           "swap target's tip, else his own team's tip).",
           "- Placed in the contest's real standings: my seat's real score is replaced, everyone else's stays as it was (the pod-mates "
           "who lost a player to me aren't re-scored). Ties ignored. Top X%: place <= ceil(X% of entries). Cash: any payout. ROI: payout over fees.",
           "- (c) undoes one tier's manual moves: that tier's players (by the button's tier) go back to their button positions and "
           "everyone else keeps my order around them. A list identical to (a) reuses (a)'s results.",
           "- (b) and (c) need the button's list at the lock: on file from 2026-11-09 (PM) and 2026-11-10 (AM). (e) is ETR's PM "
           "projections, highest first (ETR's own rank isn't kept). 11/15 had no locks on file and is out.",
           "- (f) is my PM list with one of my tiers (my tier lines at the PM lock, on file from 10/23) in ETR's order: that tier's "
           "places in my list, filled by its players highest ETR projection first. (a) minus (f) below zero: ETR's order beat mine there.", ""]
    for w, lab in (("both", "Both windows"), ("am", "AM"), ("pm", "PM")):
        md += ["## Season: %s" % lab, ""] + row_season(w) + ["", "Paired: (a) minus each list, same pods and seats, nights resampled for the 80% ranges.", ""] + row_paired(w) + [""]
    if MT:
        md += ["## Top 1% at my seats: luck or list", "",
               "My locked list (a) replayed at my real seats and pods only (%d teams, %d nights), against my real teams." % (MT["seats"], MT["nights"]), "",
               "| | Top-1% finishes |", "|---|---|",
               "| My real teams | %d |" % MT["real"],
               "| (a) at the same seats, the replay's draw | %d |" % MT["list"],
               "| (a), %d round-6 redraws: median (10%%-90%%) | %d (%d-%d) |" % (MY_DRAWS, MT["draws_median"], MT["draws_lo"], MT["draws_hi"]),
               "| (a), nights resampled: 80%% range | %s |" % ("%d-%d" % (MT["nights_lo"], MT["nights_hi"]) if MT["nights_lo"] is not None else "-"),
               "| (a), Poisson spread around its redraw mean (%.1f): 80%% range | %d-%d |" % (MT["draws_mean"], MT["poisson"][0], MT["poisson"][1]),
               "| Real minus (a), nights resampled: 80%% range | %+d (%s) |" % (MT["real"] - MT["list"], "%+d to %+d" % (MT["gap_lo"], MT["gap_hi"]) if MT["gap_lo"] is not None else "-"),
               "", "The redraws show how much the round-6 pick alone moves the count; the nights and Poisson ranges show how far a count "
               "this size swings by luck. Real and (a) share the same nights' box scores, so the real-minus-(a) range is the gap from "
               "drafting off something other than the locked list (earlier boards, round-6 choices).", ""]
    if SR:
        md += ["## Since the rules went in", "",
               "(a) minus each list, both windows, top-10% points (80% range), from each rule date's first night per window (AM and PM "
               "apart in pod_replay.json). Season is above.", ""]
        for blk in SR:
            md += ["### Since %s (AM) / %s (PM): %s" % (blk["since"]["am"], blk["since"]["pm"], ", ".join(blk["rules"])), "",
                   "| (a) minus | Window | Nights | Top 10% (pts) | 80% range | Top 1% (pts) | Mean finish pct |", "|---|---|---|---|---|---|---|"]
            for w in ("both",):                                  # per window: pod_replay.json
                for y, v in (blk["paired"].get(w) or {}).items():
                    t10 = v["top10"]
                    md.append("| %s | %s | %d | %+.2f | %s | %+.2f | %+.2f |" % (
                        NAMES[y], w.upper(), t10["nights"], t10["diff"], "%+.2f to %+.2f" % (t10["lo"], t10["hi"]) if t10["lo"] is not None else "-",
                        v["top1"]["diff"], v["fin"]["diff"]))
            md += [""]
    # fidelity
    md += ["## Round 6 fidelity", "",
           "My real round-6 pick (each of my real teams' sixth by ADP-at-draft), placed among (a)'s top still available at that seat's "
           "round-6 pick in the replay. The replay's draw puts %s at places 1-%d (from the first replay's even-draw check)." % (
               "/".join("%d%%" % x for x in R6_WEIGHTS), R6), "",
           "| Window | Teams | " + " | ".join("#%d" % k for k in range(1, R6 + 1)) + " | 7-15 | not in top 15 |", "|---" * (R6 + 4) + "|"]
    for w in ("both", "am", "pm"):
        sub = [r for r in r6 if w == "both" or r["w"] == w]
        if not sub:
            continue
        c_ = collections.Counter(r["pos"] if r["pos"] is not None and r["pos"] <= R6 else ("7-15" if r["pos"] else "none") for r in sub)
        md.append("| %s | %d | %s | %.0f%% | %.0f%% |" % (w.upper(), len(sub), " | ".join("%.0f%%" % (100 * c_[k] / len(sub)) for k in range(1, R6 + 1)),
                                                        100 * c_["7-15"] / len(sub), 100 * c_["none"] / len(sub)))
    md += ["", "By night (both windows): the share of my real round-6 picks that were (a)'s #1 available, #1-3, #1-6.", "",
           "| Night | Teams | #1 | #1-3 | #1-6 |", "|---|---|---|---|---|"]
    for x in nights:
        sub = x["r6"]
        if sub:
            f = lambda lim: 100 * sum(1 for r in sub if r["pos"] and r["pos"] <= lim) / len(sub)
            md.append("| %s | %d | %.0f%% | %.0f%% | %.0f%% |" % (x["date"], len(sub), f(1), f(3), f(R6)))
    md += [""]
    # actual vs (a)
    md += ["## My real teams against (a)", "",
           "My real teams beside (a) replayed at the same seats, and where they land in (a)'s replayed distribution (all seats, same night "
           "and window).", "",
           "| Window | Teams | Real top 1% | (a) top 1% | Real top 10% | (a) top 10% | Real mean finish | (a) mean finish | Real beat this share of (a)'s replays |",
           "|---|---|---|---|---|---|---|---|---|"]
    for w in ("both", "am", "pm"):
        sub = [r for r in mine if w == "both" or r["w"] == w]
        if not sub:
            continue
        bs = [r["beat"] for r in sub]
        md.append("| %s | %d | %.2f%% | %.2f%% | %.1f%% | %.1f%% | %.1f | %.1f | %.0f%% |" % (
            w.upper(), len(sub), 100 * st.mean(r["t1"] for r in sub), 100 * st.mean(r["rt1"] for r in sub),
            100 * st.mean(r["t10"] for r in sub), 100 * st.mean(r["rt10"] for r in sub),
            100 * st.mean(r["fin"] for r in sub), 100 * st.mean(r["rfin"] for r in sub), 100 * st.mean(bs) if bs else 0))
    md += [""]
    # by night
    md += ["## By night", "", "Top 10% / mean finish percentile for each list; seats are every seat in that window's pods.", "",
           "| Night | Window | Seats | " + " | ".join(NAMES[k].split(" ")[0] for k in LISTS) + " |", "|---" * (len(LISTS) + 3) + "|"]
    for x in nights:
        for w in ("am", "pm"):
            a = x["res"].get("%s|a" % w)
            if not a:
                continue
            cells = []
            for name in LISTS:
                r = x["res"].get("%s|%s" % (w, name))
                cells.append("-" if not r else "%.1f%% / %.0f" % (100 * r["top10"] / r["n"], 100 * r["fin"] / r["n"]))
            md.append("| %s | %s | %d | %s |" % (x["date"], w.upper(), a["n"], " | ".join(cells)))
            js["by_night"].append({"date": x["date"], "window": w, **{name: {k: x["res"]["%s|%s" % (w, name)][k] / x["res"]["%s|%s" % (w, name)]["n"]
                                                                          for k in ("top1", "top10", "fin", "cash")} | {"seats": int(x["res"]["%s|%s" % (w, name)]["n"])}
                                                                   for name in LISTS if x["res"].get("%s|%s" % (w, name))}})
    md += [""]
    js["r6_fidelity"] = {str(k): v for k, v in sorted(pos.items(), key=lambda kv: str(kv[0]))}
    return md, js


def poisson_range(lam, lo=0.1, hi=0.9):
    """The 10%-90% range of a Poisson count with mean lam."""
    out, cdf, k, pk = [], 0.0, 0, math.exp(-lam)
    while len(out) < 2 and k < 10 * lam + 50:
        cdf += pk
        if not out and cdf >= lo:
            out.append(k)
        if len(out) == 1 and cdf >= hi:
            out.append(k)
        k += 1
        pk *= lam / k
    return out


def summary(season, P, pos, r6, mine, beat, MT=None):
    """The plain-English lines on top, from the numbers below them."""
    out = []
    a = season.get(("both", "a"))
    if a:
        out.append("- **My locked list, replayed through every real seat** (%d nights, %d seats): top 1%% %.2f%%, top 10%% %.1f%%, mean finish "
                   "percentile %.1f (an average team: 1%%, 10%%, 50)." % (a["nights"], a["seats"], 100 * a["top1"], 100 * a["top10"], 100 * a["fin"]))
    for y, what in (("b", "the button's list"), ("d", "ADP"), ("e", "ETR's order (PM)")):
        w = "both"
        r1, r10, rf = P.get((w, "a", y, "top1")), P.get((w, "a", y, "top10")), P.get((w, "a", y, "fin"))
        if r10 and r10["diff"] is not None:
            out.append("- **Against %s** (%d nights%s): my list %s top-10%% (80%% range %s to %s), %s top-1%%, mean finish %s." % (
                what, r10["nights"], ", PM" if y == "e" else "", pp(r10["diff"], spec="%+.2f pts"),
                pp(r10["lo"]), pp(r10["hi"]), pp(r1["diff"], spec="%+.2f pts"), pp(rf["diff"], spec="%+.1f")))
    tiers = [(k, P.get(("both", "a", "c%d" % k, "top10"))) for k in range(1, 6)]
    tiers = [(k, r) for k, r in tiers if r and r["diff"] is not None]
    if tiers:
        out.append("- **My manual moves, tier by tier** (top-10% points my moves added, 80% range): " + "; ".join(
            "T%d %s (%s to %s)" % (k, pp(r["diff"]), pp(r["lo"]), pp(r["hi"])) for k, r in tiers) + ".")
    ft = [(k, P.get(("pm", "a", "f%d" % k, "top10"))) for k in range(1, 6)]
    ft = [(k, r) for k, r in ft if r and r["diff"] is not None]
    if ft:
        out.append("- **ETR by tier (PM):** my list minus my list with one tier in ETR's order, top-10% points (80% range; below zero, "
                   "ETR's order beat mine in that tier): " + "; ".join("T%d %s (%s to %s)" % (k, pp(r["diff"]), pp(r["lo"]), pp(r["hi"])) for k, r in ft) + ".")
    if MT:
        out.append("- **Top 1%% at my seats:** my real teams %d, my locked list at the same seats %d (round-6 redraws %d-%d, a count this "
                   "size swings %d-%d by luck); real minus list %+d, nights resampled %s." % (
                       MT["real"], MT["list"], MT["draws_lo"], MT["draws_hi"], MT["poisson"][0], MT["poisson"][1], MT["real"] - MT["list"],
                       "%+d to %+d" % (MT["gap_lo"], MT["gap_hi"]) if MT["gap_lo"] is not None else "-"))
    if r6:
        top1 = sum(1 for r in r6 if r["pos"] == 1) / len(r6)
        in6 = sum(1 for r in r6 if r["pos"] and r["pos"] <= R6) / len(r6)
        out.append("- **Round 6 fidelity:** %.0f%% of my real round-6 picks were (a)'s #1 still available, %.0f%% were in its top %d "
                   "(the replay's weighted draw: %d%% and 100%%)." % (100 * top1, 100 * in6, R6, R6_WEIGHTS[0]))
    if mine:
        out.append("- **My real teams** (%d): top 10%% %.1f%% against %.1f%% for (a) replayed at the same seats; they beat %.0f%% of "
                   "(a)'s replayed teams on average (50%% = in line with the list)." % (
                       len(mine), 100 * st.mean(r["t10"] for r in mine), 100 * st.mean(r["rt10"] for r in mine), 100 * st.mean(beat) if beat else 0))
    return out


def run(N, want=None, since=None):
    """Replay the nights, write pod_replay.md and pod_replay.json, and return the json (the Friday report embeds it)."""
    t0, out = time.time(), []
    for n in N:
        if (want and n["date"] not in want) or (since and n["date"] < since):
            continue
        t1 = time.time()
        r = night(n)
        if r["res"]:
            out.append(r)
        print("pod replay %s: %s seats, %.0fs" % (n["date"], int(sum(v["n"] for k, v in r["res"].items() if k.endswith("|a"))), time.time() - t1), flush=True)
    md, js = build(out)
    open(OUT_MD, "w").write("\n".join(md) + "\n")
    json.dump(js, open(OUT_JSON, "w"), separators=(",", ":"))
    print("wrote %s and %s in %.0fs" % (OUT_MD, OUT_JSON, time.time() - t0))
    return js


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror")
    ap.add_argument("--since")
    ap.add_argument("--dates")
    a = ap.parse_args()
    run(M.load(a.mirror), set(a.dates.split(",")) if a.dates else None, a.since)


if __name__ == "__main__":
    main()
