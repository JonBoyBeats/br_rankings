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
    # step 6's switches (2026-11-09): AM T4 leverage, PM T2 and T4 ADP (2: ETR), PM T5 ADP; T5's ownership tiebreak paused
    "am": {1: [("adp", 2), ("boom", 0)], 2: [("adp", 0)], 3: [("proj", 3), ("adp", 0)],
           4: [("projx", 2), ("drafted", 0), ("proj", 3), ("adp", 0)], 5: [("proj", 3), ("adp", 0)]},
    "pm": {1: [("projx", 0)], 2: [("adp", 2), ("projx", 0)], 3: [("proj", 0), ("adp", 0), ("boom", 0)],
           4: [("adp", 2), ("projx", 0)], 5: [("adp", 0)]},
}
PM_Q_PUSH = 2      # PM window: a Questionable player is ordered two tiers back (lean adopted 2026-11-09)
FIELD_MODEL = os.path.join(HERE, "analysis", "nba", "contests", "field_model.json")
MIRROR = None
COLS = ["date", "slate", "pod", "window", "sample", "board", "player_id", "name", "team", "adp", "proj", "proj_src", "a_tier", "p_tier",
        "tier", "flag", "tag", "q_class", "play", "exp_tier", "actual", "min", "played", "scratched", "breaker",
        "your_rank", "your_tier", "built", "boom", "drafted"]


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


def rule_sort(items, steps):
    """The rule's order (nba_report.py rule_order): each step's key, higher first, unless within its margin."""
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
                    "sample": "primary" if window == "pm" or (src[1] == "ours" and (meta.get("am") or {}).get("from") == "Lock AM") else "secondary",
                    "board": (meta.get(window) or {}).get("from", ""),
                    "player_id": pid, "name": r["name"], "team": r["team"], "adp": num(r.get(adp_col)), "proj": proj(r),
                    "proj_src": src[1], "a_tier": a, "p_tier": p, "tier": c, "flag": "VALUE" if d > 0 else "PRICEY" if d < 0 else "",
                    "tag": tag, "q_class": q, "play": play if play is not None else "", "exp_tier": et,
                    "actual": "" if act is None else act, "min": "" if mins is None else mins,
                    "played": "" if mins is None else int(mins > 0), "scratched": "" if mins is None else int(mins == 0),
                    "breaker": "" if act is None else int(pid in brk),
                    "your_rank": r.get(w["rank"], ""), "your_tier": r.get(w["tier"], ""), "built": "",
                    "boom": round(boom[pid], 3) if pid in boom else "", "drafted": round(drafted[pid], 1) if pid in drafted else ""})
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
