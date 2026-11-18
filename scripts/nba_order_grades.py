"""NBA order grades: which order to lean toward inside each tier, graded on swap values (the operator's plan, 2026-11-18).
Grading only: the Tiers button is unchanged.

  Tiers (for grading), per night and window, from the window's ADP and projection (ETR's in the afternoon, ours in the
  morning; nba_tier_history.WINDOWS):
    ADP is the floor. T1 is the ADP ladder's natural top break (the button's first line, its biggest gap at ranks 2-5);
    T2 runs to ADP rank 15, T3 to 22, T4 to 30, T5 the rest among the union of the top 44 by ADP and the top 44 by the
    projection (4-drafter nights: 10 / 15 / 20, T5 to 30). The projection's rank sorted into the same bands gives his
    projection tier; two or more tiers above his ADP tier, he moves up one (the button's move). Never down. Players who
    logged 0 minutes (scratched: Underdog swaps them) are left out.
  Swap values: for each tier, the window's real lineups that drafted a player from it (drafted picks, not swaps); each
    tier player is swapped into that slot (the other five unchanged; a lineup already holding him is skipped for him) and
    the lineup re-ranked in its contest's real standings (others as they were). His top-1% and top-10% rates over those
    lineups are his swap values. Points are Underdog's (nba_pod_replay.ud_points).
  Orders, per tier, window and night: ADP; the projection rounded to whole points, ADP breaking ties; my locked list's
    order (players off it last, by ADP); in T5 also leverage (the button's rule: under 60% drafted first, by projection).
  Score (main): how fast swap value drops down the order: minus the least-squares slope of swap value on position in the
    tier, in rate points per place (top-10% or top-1%). A good order puts high values first (positive); near-equal tiers
    score near zero, big gaps count. Also the rank correlation (Spearman, position against value, sign flipped), for
    reference. Season = the mean over nights, last7 = the last 7 nights it ran; 80% ranges resample nights.
  Headline and stakes: from pod_replay.json (scripts/nba_pod_replay.py): my list against an ADP list, ETR's (PM) and
    our Proj's (AM), and where my real teams land among my list's replays; each tier's stakes is the pod replay's
    projection-order-minus-ADP-order pair for that tier (my own tier lines there).

Writes analysis/nba/report/order_grades.json (the Results page reads it) and order_grades.md. Runs nightly after the pod
replay (nba_daily.yml).

  python3 scripts/nba_order_grades.py [--mirror ../br-adp-mirror]
"""
import argparse, bisect, collections, csv, itertools, json, math, os, statistics as st, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_money as M            # noqa: E402  nights, teams, windows, drafted_by, boot_range
import nba_pod_replay as R       # noqa: E402  Underdog's points, the pod replay's file
import nba_tier_history as T     # noqa: E402  the ladder's lines, the window's columns

REP = M.REP
OUT_JSON = os.path.join(REP, "order_grades.json")
OUT_MD = os.path.join(REP, "order_grades.md")
BANDS = {6: (15, 22, 30, 44), 4: (10, 15, 20, 30)}     # T2, T3, T4 last ADP rank; the T5 union's depth
KEYS = ("top10", "top1")
num = M.num


def window_cols(rows, w):
    cols = T.WINDOWS[w]
    adp_col = next((c for c in cols["adp"] if any(num(r.get(c)) is not None for r in rows)), None)
    proj_col = next((c for c, _ in cols["proj"] if any(num(r.get(c)) is not None for r in rows)), None)
    return adp_col, proj_col


def bands_of(ranked, values, pod):
    """{player: tier} for an order (best first) with its values: T1 to the ladder's first line, then the fixed bands."""
    b2, b3, b4, _ = BANDS[pod]
    t1 = T.lines(values, T.LADDER[pod], T.MIN_TIER[pod])[0] if len(values) > 6 else 2
    out = {}
    for i, p in enumerate(ranked, 1):
        out[p] = 1 if i <= t1 else 2 if i <= b2 else 3 if i <= b3 else 4 if i <= b4 else 5
    return out


def tiers_for(rec, w, pod):
    """{player: grading tier} for the window, and the inputs the orders read: adp, proj, my rank."""
    rows = list(rec.values())
    adp_col, proj_col = window_cols(rows, w)
    if not adp_col or not proj_col:
        return None
    adp = {p: num(r.get(adp_col)) for p, r in rec.items()}
    proj = {p: num(r.get(proj_col)) for p, r in rec.items()}
    sat = {p for p, r in rec.items() if r.get("min") == "0.0"}
    pa = sorted((p for p in rec if adp[p] is not None), key=lambda p: (adp[p], p))
    pp_ = sorted((p for p in rec if proj[p] is not None), key=lambda p: (-proj[p], adp[p] if adp[p] is not None else 999, p))
    depth = BANDS[pod][3]
    union = set(pa[:depth]) | set(pp_[:depth])
    at = bands_of(pa, [adp[p] for p in pa], pod)
    pt = bands_of(pp_, [max(proj[p], 0) for p in pp_], pod)
    tier = {}
    for p in union:
        if p in sat or adp[p] is None:
            continue
        a, q = at.get(p, 5), pt.get(p, 5)
        tier[p] = a - 1 if a - q >= 2 else a                  # up one tier at two or more apart; never down
    rank = {p: int(float(r[w + "_rank"])) for p, r in rec.items() if r.get(w + "_rank") not in (None, "")}
    return {"tier": tier, "adp": adp, "proj": proj, "rank": rank}


def orders(members, X, w, drafted):
    """{order: [players]} for a tier's members."""
    adp, proj, rank = X["adp"], X["proj"], X["rank"]
    a = lambda p: adp[p] if adp[p] is not None else 999
    rnd = lambda p: math.floor(proj[p] + 0.5) if proj[p] is not None else -1e9
    out = {"adp": sorted(members, key=lambda p: (a(p), p)),
           ("etr" if w == "pm" else "proj"): sorted(members, key=lambda p: (-rnd(p), a(p), p))}
    if any(p in rank for p in members):
        out["mine"] = sorted(members, key=lambda p: (0, rank[p]) if p in rank else (1, a(p)))
    return out


def lev_order(members, X, drafted):
    """T5's leverage order (the button's rule): under 60% drafted first, each group by projection."""
    proj, adp = X["proj"], X["adp"]
    k = lambda p: (-(proj[p] if proj[p] is not None else -1e9), adp[p] if adp[p] is not None else 999, p)
    return sorted([p for p in members if (drafted.get(p) or 0) < T.T5_LINE], key=k) + \
        sorted([p for p in members if (drafted.get(p) or 0) >= T.T5_LINE], key=k)


def slope_score(vals):
    """Minus the least-squares slope of value on position (1..m): positive when value falls down the order."""
    m = len(vals)
    if m < 2:
        return None
    xs = range(1, m + 1)
    mx, my = (m + 1) / 2, sum(vals) / m
    vx = sum((x - mx) ** 2 for x in xs)
    return -sum((x - mx) * (v - my) for x, v in zip(xs, vals)) / vx


def rank_corr(vals):
    """Minus Spearman's rho between position and value (ties averaged)."""
    m = len(vals)
    if m < 3:
        return None
    order = sorted(range(m), key=lambda i: vals[i])
    rk = [0.0] * m
    i = 0
    while i < m:
        j = i
        while j + 1 < m and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        for t in range(i, j + 1):
            rk[order[t]] = (i + j) / 2 + 1
        i = j + 1
    pos = list(range(1, m + 1))
    mp, mr = (m + 1) / 2, sum(rk) / m
    cov = sum((a - mp) * (b - mr) for a, b in zip(pos, rk))
    va, vb = sum((a - mp) ** 2 for a in pos), sum((b - mr) ** 2 for b in rk)
    return None if not va or not vb else -cov / math.sqrt(va * vb)


def swap_values(n, w, members, pts):
    """{player: {"top10", "top1", "n"}}: each member swapped into the slot of every window lineup that drafted a member."""
    mem = set(members)
    acc = {p: [0, 0, 0] for p in members}                   # top10 hits, top1 hits, lineups
    for c in n["contests"]:
        ts = n["teams"][c["contest_id"]]
        asc = c.get("points_asc") or sorted(t["points"] for t in ts)
        c["points_asc"] = asc
        nn = len(ts)
        c1, c10 = math.ceil(nn / 100), math.ceil(nn / 10)
        for t in ts:
            if t["window"] != w:
                continue
            held = set(t["picks"])
            for x, a in zip(t["picks"], t["adps"]):
                if a is None or x not in mem:                 # drafted picks only (a swapped-in pick has no ADP)
                    continue
                base = t["points"] - pts.get(x, 0.0)
                for y in members:
                    if y != x and y in held:
                        continue
                    v = base + pts.get(y, 0.0)
                    ahead = nn - bisect.bisect_right(asc, v) - (1 if t["points"] > v else 0)
                    place = ahead + 1
                    s = acc[y]
                    s[0] += place <= c10
                    s[1] += place <= c1
                    s[2] += 1
    return {p: {"top10": s[0] / s[2], "top1": s[1] / s[2], "n": s[2]} for p, s in acc.items() if s[2]}


def night(n, drafted_by_w):
    rec = n["rec"]
    if not rec or not n["contests"]:
        return None
    pts, _, _, _ = R.ud_points(n)
    pts = {p: v or 0.0 for p, v in pts.items()}
    pod = 4 if n["pod"] == 4 else 6
    out = {}
    for w in ("am", "pm"):
        X = tiers_for(rec, w, pod)
        if not X or not any(t["window"] == w for ts in n["teams"].values() for t in ts):
            continue
        drafted = drafted_by_w.get((n["date"], w), {})
        for k in range(1, 6):
            members = [p for p, t in X["tier"].items() if t == k]
            if len(members) < 2:
                continue
            sv = swap_values(n, w, members, pts)
            members = [p for p in members if p in sv]
            if len(members) < 2:
                continue
            ords = orders(members, X, w, drafted)
            if k == 5:
                ords["lev"] = lev_order(members, X, drafted)
            cell = {"members": len(members), "lineups": max(v["n"] for v in sv.values()), "orders": {}}
            for o, lst in ords.items():
                cell["orders"][o] = {"slope": {q: slope_score([100 * sv[p][q] for p in lst]) for q in KEYS},
                                     "rc": {q: rank_corr([sv[p][q] for p in lst]) for q in KEYS},
                                     "players": [rec[p]["name"] for p in lst]}
            cell["values"] = {rec[p]["name"]: {q: round(100 * sv[p][q], 2) for q in KEYS} for p in members}
            out.setdefault(w, {})[str(k)] = cell
    return {"date": n["date"], "w": out} if out else None


# ---------------------------------------------------------------- summaries
def summarize(vals_by_night, last=7):
    """{"season", "last7"}: each {v, lo, hi, nights}; vals_by_night [(date, value)] (None dropped)."""
    vs = sorted((d, v) for d, v in vals_by_night if v is not None)

    def blk(sub):
        if not sub:
            return {"v": None, "lo": None, "hi": None, "nights": 0}
        xs = [v for _, v in sub]
        rng = M.boot_range(xs, lambda s: sum(s) / len(s))
        r3 = lambda x: None if x is None else round(x, 3)
        return {"v": r3(sum(xs) / len(xs)), "lo": r3(rng[0]) if rng else None, "hi": r3(rng[1]) if rng else None, "nights": len(xs)}
    return {"season": blk(vs), "last7": blk(vs[-last:])}


def split_of(vals_by_night, last=7):
    """{"season", "last7"}: nights the first came out ahead (won), behind (lost), level (even); [(date, diff)]."""
    vs = sorted((d, v) for d, v in vals_by_night if v is not None)
    cnt = lambda sub: {"won": sum(1 for _, v in sub if v > 1e-9), "lost": sum(1 for _, v in sub if v < -1e-9),
                       "even": sum(1 for _, v in sub if abs(v) <= 1e-9)}
    return {"season": cnt(vs), "last7": cnt(vs[-last:])}


def pooled(cells, x, y=None, key="top10"):
    """Seat-weighted pooled rate (or x minus y) over pod-replay by_night cells, in points, with nights resampled."""
    def fn(cs):
        tot = sum(c[x]["seats"] for c in cs)
        if not tot:
            return None
        return 100 * sum(c[x]["seats"] * (c[x][key] - (c[y][key] if y else 0)) for c in cs) / tot
    cs = [c for c in cells if c.get(x) and (not y or c.get(y))]

    def blk(sub):
        v = fn(sub) if sub else None
        rng = M.boot_range(sub, fn) if v is not None else None
        r3 = lambda z: None if z is None else round(z, 3)
        return {"v": r3(v), "lo": r3(rng[0]) if rng else None, "hi": r3(rng[1]) if rng else None, "nights": len(sub)}
    return {"season": blk(cs), "last7": blk(cs[-7:])}


def build(nights, pr):
    js = {"generated": M.dt.datetime.now(M.PT).isoformat(timespec="minutes"), "nights": [x["date"] for x in nights],
          "defs": {
              "tiers": "ADP is the floor: T1 to the ADP ladder's natural top break, T2 to ADP rank 15, T3 to 22, T4 to 30, T5 the rest "
                       "among the top 44 by ADP or by projection (4-drafter nights 10/15/20/30); the projection moves a player up one "
                       "tier when it puts him two or more tiers higher, never down; scratched players left out.",
              "score": "How fast swap value drops down the order: minus the slope of each player's swap value (the window's real "
                       "lineups that drafted a tier player, with him swapped into that slot, re-ranked in the real standings) on his "
                       "place in the order. Positive: the order puts the better swaps first; near zero: the tier was close to even.",
              "units": "rate points per place in the order (top-10% or top-1% rate of the swapped lineups, in percentage points)",
              "headline": "Whole lists through the real pods (pod replay): my locked list, ADP's order, ETR's (PM) or our Proj's (AM); "
                          "rates in points, vs_mine is that list minus mine; my_percentile: the median share of my list's replayed "
                          "teams my real teams beat, 0-100.",
              "orders": "adp: ADP; etr / proj: the projection rounded to whole points, ADP breaking ties; mine: my locked list's "
                        "order; lev (T5): under 60% drafted first, by projection.",
              "split": "won / lost / even: nights the first list or order came out ahead of the second, behind it, level (headline "
                       "vs_mine: that list against mine; tier diffs: the first order's score against the second's).",
              "stakes": "The pod replay's read for the tier: my list with my tier in the projection's order minus the same in ADP's "
                        "order (my own tier lines), top-10% and top-1% points."},
          "headline": {}, "tiers": {}}
    # ---- tiers
    for w in ("am", "pm"):
        po = "etr" if w == "pm" else "proj"
        for k in map(str, range(1, 6)):
            cells = [(x["date"], x["w"][w][k]) for x in nights if w in x["w"] and k in x["w"][w]]
            if not cells:
                continue
            names = sorted({o for _, c in cells for o in c["orders"]}, key=lambda o: ["adp", po, "mine", "lev"].index(o))
            blk = {"members": "%s players a night (median), %s lineups re-ranked a player" % (
                       int(st.median(c["members"] for _, c in cells)), int(st.median(c["lineups"] for _, c in cells))),
                   "orders": {}, "diffs": {}}
            for o in names:
                blk["orders"][o] = {q: summarize([(d, c["orders"][o]["slope"][q]) for d, c in cells if o in c["orders"]]) for q in KEYS}
                blk["orders"][o]["rank_corr"] = {q: summarize([(d, c["orders"][o]["rc"][q]) for d, c in cells if o in c["orders"]]) for q in KEYS}
            for a, b in itertools.combinations(names, 2):
                blk["diffs"]["%s-%s" % (a, b)] = {}
                for q in KEYS:
                    dv = [(d, c["orders"][a]["slope"][q] - c["orders"][b]["slope"][q]) for d, c in cells
                          if a in c["orders"] and b in c["orders"] and c["orders"][a]["slope"][q] is not None and c["orders"][b]["slope"][q] is not None]
                    blk["diffs"]["%s-%s" % (a, b)][q] = dict(summarize(dv), split=split_of(dv))
            # stakes: the pod replay's projection-order minus ADP-order pair for the tier (my tier lines)
            x_, y_ = ("f" if w == "pm" else "p") + k, "d" + k
            bn = sorted((c for c in pr.get("by_night", []) if c["window"] == w), key=lambda c: c["date"])
            blk["stakes"] = {q: pooled(bn, x_, y_, q) for q in KEYS}
            js["tiers"].setdefault(w, {})[k] = blk
    # ---- headline
    for w in ("am", "pm"):
        po, pl = ("etr", "e") if w == "pm" else ("proj", "pj")
        bn = sorted((c for c in pr.get("by_night", []) if c["window"] == w), key=lambda c: c["date"])
        if not bn:
            continue
        h = {"lists": {}, "vs_mine": {}}
        for name, key in (("mine", "a"), ("adp", "d"), (po, pl)):
            if any(c.get(key) for c in bn):
                h["lists"][name] = {q: pooled(bn, key, None, q) for q in KEYS}
                if name != "mine":
                    h["vs_mine"][name] = {q: dict(pooled(bn, key, "a", q), split=split_of(
                        [(c["date"], c[key][q] - c["a"][q]) for c in bn if c.get(key) and c.get("a")])) for q in KEYS}
        beats = sorted((d, v[w]) for d, v in (pr.get("my_beat") or {}).items() if v.get(w))
        h["my_percentile"] = summarize([(d, 100 * st.median(b)) for d, b in beats])
        js["headline"][w] = h
    js["by_night"] = [{"date": x["date"], "tiers": {w: {k: {"members": c["members"], "lineups": c["lineups"],
                                                            "orders": {o: {"slope": {q: None if v["slope"][q] is None else round(v["slope"][q], 3) for q in KEYS},
                                                                           "players": v["players"]} for o, v in c["orders"].items()},
                                                            "values": c["values"]} for k, c in ws.items()} for w, ws in x["w"].items()}}
                      for x in nights]
    return js


def md_of(js):
    f = lambda b: "-" if b["v"] is None else "%+.2f%s" % (b["v"], " (%+.2f to %+.2f)" % (b["lo"], b["hi"]) if b["lo"] is not None else "")
    out = ["# Order grades: which order to lean toward in each tier", "", "Results only; grading, not the button. Generated %s, %d nights." % (
        js["generated"], len(js["nights"])), "", "- **Tiers:** " + js["defs"]["tiers"], "- **Score:** " + js["defs"]["score"] +
        " Units: " + js["defs"]["units"] + ".", "- **Orders:** " + js["defs"]["orders"], ""]
    for w in ("pm", "am"):
        if w not in js["tiers"]:
            continue
        out += ["## %s" % ("Afternoon" if w == "pm" else "Morning"), "",
                "| Tier | Players | Order | Top 10%: season (80% range) | nights | last 7 | Top 1%: season | last 7 |", "|---|---|---|---|---|---|---|---|"]
        for k, blk in sorted(js["tiers"][w].items()):
            for o, v in blk["orders"].items():
                out.append("| T%s | %s | %s | %s | %d | %s | %s | %s |" % (k, blk["members"].split(" ")[0], o, f(v["top10"]["season"]), v["top10"]["season"]["nights"],
                                                                     f(v["top10"]["last7"]), f(v["top1"]["season"]), f(v["top1"]["last7"])))
            for dk, v in blk["diffs"].items():
                out.append("| T%s | | %s | %s | %d | %s | %s | %s |" % (k, dk.replace("-", " minus "), f(v["top10"]["season"]), v["top10"]["season"]["nights"],
                                                                       f(v["top10"]["last7"]), f(v["top1"]["season"]), f(v["top1"]["last7"])))
        out.append("")
    for w, h in js["headline"].items():
        out += ["## Headline, %s (pod replay)" % w.upper(), ""] + ["- %s: top 10%% %s, top 1%% %s" % (k, f(v["top10"]["season"]), f(v["top1"]["season"]))
                                                                for k, v in h["lists"].items()]
        out += ["- %s minus mine: top 10%% %s, top 1%% %s" % (k, f(v["top10"]["season"]), f(v["top1"]["season"])) for k, v in h["vs_mine"].items()]
        out += ["- My real teams' median percentile among my list's replays: %s" % f(h["my_percentile"]["season"]), ""]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror")
    a = ap.parse_args()
    t0 = time.time()
    N = M.load(a.mirror)
    drafted = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(REP, "tier_history.csv"))):
        if r.get("drafted") not in (None, ""):
            drafted[(r["date"], r["window"])][r["player_id"]] = float(r["drafted"])
    nights = []
    for n in N:
        t1 = time.time()
        x = night(n, drafted)
        if x:
            nights.append(x)
        print("order grades %s: %.0fs" % (n["date"], time.time() - t1), flush=True)
    pr = json.load(open(R.OUT_JSON)) if os.path.exists(R.OUT_JSON) else {}
    js = build(nights, pr)
    json.dump(js, open(OUT_JSON, "w"), separators=(",", ":"))
    open(OUT_MD, "w").write("\n".join(md_of(js)) + "\n")
    print("wrote %s and %s in %.0fs" % (OUT_JSON, OUT_MD, time.time() - t0))


if __name__ == "__main__":
    main()
