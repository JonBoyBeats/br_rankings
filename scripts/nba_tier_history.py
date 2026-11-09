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

  python3 scripts/nba_tier_history.py
"""
import csv, glob, json, math, os, re

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(HERE, "analysis", "nba", "report", "tier_history.csv")
LADDER = {6: [(2, 5, 4), (12, 18, 15), (19, 25, 22), (27, 33, 30)], 4: [(2, 4, 3), (8, 12, 10), (13, 17, 15), (18, 22, 20)]}
SMASH_PLAY = 0.7
Q_TAG = re.compile(r"^(q|d|g)", re.I)
COLS = ["date", "slate", "pod", "window", "board", "player_id", "name", "team", "adp", "proj", "proj_src", "a_tier", "p_tier",
        "tier", "flag", "tag", "q_class", "play", "exp_tier", "actual", "min", "played", "scratched", "breaker",
        "your_rank", "your_tier", "built"]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def lines(vals, spec):
    """The board's nbaLadderLines: per window, the rank k (a line ends a tier at k) with the biggest step
    vals[k-1] -> vals[k]; ties go to the rank nearest the window's start."""
    out, prev = [], 1
    for lo, hi, start in spec:
        best, gap = None, -math.inf
        for k in range(max(lo, prev + 1), min(hi, len(vals) - 1) + 1):
            g = abs(vals[k - 1] - vals[k])
            if g > gap + 1e-9 or (abs(g - gap) <= 1e-9 and abs(k - start) < abs(best - start)):
                best, gap = k, g
        if best is None:
            best = max(prev + 1, min(start, len(vals)))
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
    la = lines([adp(r) for r in A], LADDER[pod])
    lp = lines([max(proj(r), 0) if proj(r) is not None else 0 for r in P], LADDER[pod])
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
        out.append({"date": date, "slate": slate, "pod": pod, "window": window, "board": (meta.get(window) or {}).get("from", ""),
                    "player_id": pid, "name": r["name"], "team": r["team"], "adp": num(r.get(adp_col)), "proj": proj(r),
                    "proj_src": src[1], "a_tier": a, "p_tier": p, "tier": c, "flag": "VALUE" if d > 0 else "PRICEY" if d < 0 else "",
                    "tag": tag, "q_class": q, "play": play if play is not None else "", "exp_tier": et,
                    "actual": "" if act is None else act, "min": "" if mins is None else mins,
                    "played": "" if mins is None else int(mins > 0), "scratched": "" if mins is None else int(mins == 0),
                    "breaker": "" if act is None else int(pid in brk),
                    "your_rank": r.get(w["rank"], ""), "your_tier": r.get(w["tier"], ""), "built": r.get(w["built"], "")})
    info = {"date": date, "window": window, "pod": pod, "adp_col": adp_col, "proj_src": src[1], "lines_a": la, "lines_p": lp,
            "n": len(out), "tags": sum(1 for x in out if Q_TAG.match(x["tag"])),
            "play": sum(1 for x in out if x["play"] != ""), "board": (meta.get(window) or {}).get("from", "")}
    return out, info


def main():
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
    print("| Slate | Window | Pod | Board | ADP | Projection | ADP lines | Proj lines | Tagged Q/D/GTD | With P(play) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for i in infos:
        if i.get("skip"):
            print("| %s | %s | - | - | - | - | %s | | | |" % (i["date"], i["window"].upper(), i["skip"]))
            continue
        print("| %s | %s | %d | %s | %s | %s | %s | %s | %d | %d |" % (
            i["date"], i["window"].upper(), i["pod"], i["board"] or "-", i["adp_col"], i["proj_src"],
            ", ".join(map(str, i["lines_a"])), ", ".join(map(str, i["lines_p"])), i["tags"], i["play"]))
    print("\n%d rows -> %s" % (len(rows_out), os.path.relpath(OUT, HERE)))


if __name__ == "__main__":
    main()
