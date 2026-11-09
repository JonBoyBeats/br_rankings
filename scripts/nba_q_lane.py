"""NBA Q lane: our miss probability calibrated, the swap value S, the swap-adjusted projection X, the Q classes on it,
the AM push-back rule tested, beneficiaries, and the implied cost of a scratch by tier.

Everything is on the scale of actual points: projections are the board's median (nbaMedianOf of its Proj, which is 75%
ceiling and runs 6-9 points high; the median lands within 0-2 points of what players score), and swaps are what the
swapped-in players scored (analysis/nba/report/swaps.csv).

  calibration   our chance he plays (tier_history play, from nba_sit.json at the lock) against whether he played,
                by window, tag and tier, with ranges from resampling slates; then a refit (logistic on the logit of our
                number, plus a tagged term) that gives the calibrated P(play) used below
  S             at each lock: the best expected score (calibrated P(play) x median) among players the field leaves
                undrafted in about half of pods or more (projected drafted% under 50 at that lock): what a swap is worth.
                Directional: it uses projections in place of each drafter's own order, and no teammate boost
  X             P(play) x median + (1 - P(play)) x S, for every player tagged Q, D or GTD at the lock; its tier is where X
                falls on that lock's projection ladder. SMASH: X's tier higher than his ADP tier; FAIR: the same; TRAP: lower
  push rule     in the AM window, for tagged players: the button's order against pushing him back one tier, two tiers,
                or ranking him on X, graded on decision pairs that involve him (a scratch scored through his swap)
  beneficiaries undrafted or T5 players with a teammate tagged at the lock: in round 6 at the AM lock, against their ADP
                band, split by whether the teammate sat; and how often they were a swap target
  scratch cost  each tier's average score against the average swap for players ruled out from that tier, split by whether
                his teammates were priced up (every teammate projected for 20+ already inside ADP 30 at the PM lock) or not

Writes analysis/nba/report/q_lane.md and prints it.

  python3 scripts/nba_q_lane.py
"""
import collections, csv, glob, math, os, random, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nba_boom_ties as B          # noqa: E402  the board's median of its Proj
import nba_tier_grade as G         # noqa: E402  slots scored with the swap rule, the evidence bar
import nba_tier_history as T       # noqa: E402  the rule order
import nba_swaps as SW             # noqa: E402  nights excluded from swap tests

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = os.path.join(HERE, "analysis", "nba", "report")
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
OUT = os.path.join(REP, "q_lane.md")
QT = re.compile(r"^(q|d|g)", re.I)
num = G.num


def tag_type(t):
    t = (t or "").lower()
    return "Doubtful" if t.startswith("d") else "Questionable" if t.startswith("q") else "GTD" if t.startswith("g") else \
        "Out" if t.startswith("o") else "Probable" if t.startswith("p") else "none"


def logit(p):
    p = min(max(p, 0.005), 0.995)
    return math.log(p / (1 - p))


def fit(rows):
    """Logistic refit: played ~ a + b * logit(our P(play)) + c * tagged (IRLS)."""
    X = [(1.0, logit(r["p"]), 1.0 if r["tagged"] else 0.0) for r in rows]
    y = [r["y"] for r in rows]
    w = [0.0, 1.0, 0.0]
    for _ in range(50):
        g, h = [0.0] * 3, [[0.0] * 3 for _ in range(3)]
        for x, t in zip(X, y):
            z = sum(a * b for a, b in zip(w, x))
            p = 1 / (1 + math.exp(-z))
            for i in range(3):
                g[i] += (t - p) * x[i]
                for j in range(3):
                    h[i][j] += p * (1 - p) * x[i] * x[j]
        for i in range(3):
            h[i][i] += 1e-6
        step = solve(h, g)
        w = [a + b for a, b in zip(w, step)]
        if max(abs(s) for s in step) < 1e-8:
            break
    return w


def solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[c][c]:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] if M[i][i] else 0 for i in range(n)]


def resample_rate(per, rnd):
    ds = sorted(per)
    bs = []
    for _ in range(1000):
        s = [v for d in (rnd.choice(ds) for _ in ds) for v in per[d]]
        if s:
            bs.append(sum(s) / len(s))
    bs.sort()
    return bs[len(bs) // 10], bs[len(bs) * 9 // 10]


def x_values(H):
    """{(date, window, player_id): X on the board's Proj scale} for every player tagged Q, D or GTD at a lock with our
    chance on file: the calibrated chance x median + (1 - it) x S, as in main()."""
    for r in H:
        r.setdefault("med", B.median_of_proj(num(r["proj"])) if num(r["proj"]) is not None else None)
    cal = [dict(p=float(r["play"]), y=int(r["played"]), tagged=bool(QT.match(r["tag"] or ""))) for r in H
           if r["play"] != "" and r["played"] != ""]
    a, b, c = fit(cal)
    pcal = lambda p, tagged: 1 / (1 + math.exp(-(a + b * logit(p) + (c if tagged else 0))))
    S = {}
    for r in H:
        if r["med"] is None or tag_type(r["tag"]) == "Out" or (num(r["drafted"]) is not None and num(r["drafted"]) >= 50):
            continue
        p = pcal(float(r["play"]), bool(QT.match(r["tag"] or ""))) if r["play"] != "" else (0.6 if QT.match(r["tag"] or "") else 0.97)
        k = (r["date"], r["window"])
        S[k] = max(S.get(k, 0), p * r["med"])
    out = {}
    for r in H:
        k = (r["date"], r["window"])
        if QT.match(r["tag"] or "") and r["med"] is not None and r["play"] != "" and k in S:
            p = pcal(float(r["play"]), True)
            x = p * r["med"] + (1 - p) * S[k]
            out[(r["date"], r["window"], r["player_id"])] = x * (0.25 + 0.75 * B.CEIL[0]) + 0.75 * B.CEIL[1]
    return out


def main():
    H = G.load()
    rnd = random.Random(11)
    daily = {}
    for p in glob.glob(os.path.join(DAILY, "*_main.csv")):
        for r in csv.DictReader(open(p)):
            daily[(r["date"], r["player_id"])] = r
    for r in H:
        r["med"] = B.median_of_proj(num(r["proj"])) if num(r["proj"]) is not None else None
        r["tt"] = tag_type(r["tag"])
    out = ["# NBA Q lane", "", "Written by scripts/nba_q_lane.py. Projections are medians (expected actual points); a scratch is "
           "scored through his swap. Slates since 2026-10-27 (when our miss chances start).", ""]

    # ---- a. calibration
    cal = [r for r in H if r["play"] != "" and r["played"] != ""]
    for r in cal:
        r["p"], r["y"], r["tagged"] = float(r["play"]), int(r["played"]), bool(QT.match(r["tag"] or ""))
    out += ["## a. Our chance he plays, against what happened", "",
            "| Window | Tag | Tier | Players | Predicted | Played | 80% range |", "|---|---|---|---|---|---|---|"]
    for w in ("am", "pm"):
        for tt in ("Questionable", "Doubtful", "GTD", "Probable", "none"):
            for tname, tiers in (("T1-T2", "12"), ("T3-T4", "34"), ("T5", "5"), ("all", "12345")):
                rs = [r for r in cal if r["window"] == w and r["tt"] == tt and r["tier"] in tiers]
                if len(rs) < (3 if tt != "none" else 20) or (tname != "all" and tt == "none" and False):
                    continue
                per = collections.defaultdict(list)
                for r in rs:
                    per[r["date"]].append(r["y"])
                lo, hi = resample_rate(per, rnd)
                out.append("| %s | %s | %s | %d | %.0f%% | %.0f%% | %.0f%% to %.0f%% |" % (
                    w.upper(), tt, tname, len(rs), 100 * sum(r["p"] for r in rs) / len(rs), 100 * sum(r["y"] for r in rs) / len(rs),
                    100 * lo, 100 * hi))
    a, b, c = fit(cal)
    pcal = lambda p, tagged: 1 / (1 + math.exp(-(a + b * logit(p) + (c if tagged else 0))))
    out += ["", "Refit on %d player-locks (both windows): played ~ %.2f + %.2f x logit(our chance) %+.2f if tagged Q/D/GTD. "
            "So our 70%% for a tagged player reads %.0f%%, our 50%% reads %.0f%%, an untagged 95%% reads %.0f%%." % (
                len(cal), a, b, c, 100 * pcal(0.7, True), 100 * pcal(0.5, True), 100 * pcal(0.95, False)), "",
            "| Predicted (calibrated) | Players | Played |", "|---|---|---|"]
    for r in cal:
        r["pc"] = pcal(r["p"], r["tagged"])
    for lo_, hi_ in ((0, .3), (.3, .5), (.5, .7), (.7, .9), (.9, 1.01)):
        rs = [r for r in cal if r["tagged"] and lo_ <= r["pc"] < hi_]
        if rs:
            out.append("| tagged, %.0f-%.0f%% | %d | %.0f%% (predicted %.0f%%) |" % (
                100 * lo_, min(100, 100 * hi_), len(rs), 100 * sum(r["y"] for r in rs) / len(rs), 100 * sum(r["pc"] for r in rs) / len(rs)))

    # ---- b. S at each lock
    locks = collections.defaultdict(list)
    for r in H:
        locks[(r["date"], r["window"])].append(r)
    S = {}
    for k, rs in locks.items():
        best = None
        for r in rs:
            if r["med"] is None or r["tt"] == "Out":
                continue
            dr = num(r["drafted"])
            if dr is not None and dr >= 50:
                continue
            p = pcal(float(r["play"]), bool(QT.match(r["tag"] or ""))) if r["play"] != "" else (0.6 if QT.match(r["tag"] or "") else 0.97)
            v = p * r["med"]
            if best is None or v > best[0]:
                best = (v, r["name"])
        S[k] = best
    swaps = collections.defaultdict(lambda: [0, 0.0])
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        swaps[r["date"]][0] += int(r["teams"])
        swaps[r["date"]][1] += int(r["teams"]) * float(r["swap_fp"])
    out += ["", "## b. The swap value S at each lock (best expected score among players under 50% drafted)", "",
            "Excluded from swap tests (no credited swaps, so no actual average): " + "; ".join("%s (%s)" % kv for kv in sorted(SW.EXCLUDED.items())) + ".", "",
            "| Slate | S at AM | S at PM | The PM player | Swaps' actual average (credited) |", "|---|---|---|---|---|"]
    diffs = []
    for d in sorted({k[0] for k in S}):
        am, pm = S.get((d, "am")), S.get((d, "pm"))
        act = swaps[d][1] / swaps[d][0] if swaps[d][0] else None
        if pm and act is not None:
            diffs.append(act - pm[0])
        out.append("| %s | %s | %s | %s | %s |" % (d, "%.1f" % am[0] if am else "-", "%.1f" % pm[0] if pm else "-",
                                                  pm[1] if pm else "-", "%.1f (%d)" % (act, swaps[d][0]) if act is not None else "-"))
    if diffs:
        out += ["", "Swaps scored %+.1f against S at the PM lock on average (%d slates): S is %s." % (
            sum(diffs) / len(diffs), len(diffs), "about right" if abs(sum(diffs) / len(diffs)) < 3 else
            "low (the swaps landed on better players than the best projected undrafted one)" if sum(diffs) > 0 else "high")]

    # ---- c. X and its classes
    lines = {}
    for k, rs in locks.items():
        meds = sorted((r["med"] for r in rs if r["med"] is not None), reverse=True)
        cnt = collections.Counter(int(r["p_tier"]) for r in rs)
        cuts, run = [], 0
        for t in range(1, 5):
            run += cnt[t]
            cuts.append(run)
        lines[k] = (meds, cuts)
    tagged = [r for r in H if QT.match(r["tag"] or "") and r["med"] is not None and r["play"] != "" and S.get((r["date"], r["window"]))]
    for r in tagged:
        meds, cuts = lines[(r["date"], r["window"])]
        p = pcal(float(r["play"]), True)
        r["pc"] = p
        r["X"] = p * r["med"] + (1 - p) * S[(r["date"], r["window"])][0]
        rank = 1 + sum(1 for m in meds if m > r["X"])
        r["x_tier"] = T.tier_of(rank, cuts)
        a_t = int(r["a_tier"])
        r["xclass"] = "SMASH" if r["x_tier"] < a_t else "FAIR" if r["x_tier"] == a_t else "TRAP"
    out += ["", "## c-d. Q classes on X (swap-adjusted), by window and tier", "",
            "| Window | Tier | Class | Players | Played | Slot score (him or his swap) | Breakers | Healthy tier higher / same / lower than ADP |",
            "|---|---|---|---|---|---|---|---|"]
    for w in ("am", "pm"):
        for tname, tiers in (("T1-T2", "12"), ("T3-T4", "34"), ("T5", "5")):
            for cl in ("SMASH", "FAIR", "TRAP"):
                rs = [r for r in tagged if r["window"] == w and r["tier"] in tiers and r["xclass"] == cl]
                if not rs:
                    continue
                hh = collections.Counter("higher" if int(r["p_tier"]) < int(r["a_tier"]) else "same" if r["p_tier"] == r["a_tier"] else "lower" for r in rs)
                out.append("| %s | %s | %s | %d | %.0f%% | %.1f | %d | %d / %d / %d |" % (
                    w.upper(), tname, cl, len(rs), 100 * sum(int(r["played"]) for r in rs) / len(rs),
                    sum(r["slot"] for r in rs) / len(rs), sum(r["slot_brk"] for r in rs), hh["higher"], hh["same"], hh["lower"]))

    # ---- d. the AM push rule
    out += ["", "## d. Pushing a tagged player back: the button's order against each variant", "",
            "Decision pairs (ADP within 4) that include a tagged player and that the variant orders differently from the "
            "button. Positive: the variant's order was right more, in points per pair.", "",
            "| Window | Tag | Back one tier | Back two tiers | Rank on X |", "|---|---|---|---|---|"]
    for w in ("am", "pm"):
        for tt in ("Questionable", "Doubtful", "all tagged"):
            res = {v: (collections.defaultdict(list), collections.defaultdict(list)) for v in ("one", "two", "x")}
            for (d, ww), rs in locks.items():
                if ww != w:
                    continue
                tg = {r["player_id"]: r for r in rs if r.get("X") is not None and (tt == "all tagged" or r["tt"] == tt)}
                if not tg:
                    continue
                base = {r["player_id"]: int(r["built"]) for r in rs if r["built"]}
                for v in res:
                    def key(r, v=v):
                        t = int(r["tier"])
                        if r["player_id"] in tg:
                            t = min(5, t + 1) if v == "one" else min(5, t + 2) if v == "two" else r["x_tier"]
                        return t
                    tiers = {r["player_id"]: key(r) for r in rs if r["built"]}
                    order = {}
                    rank = 0
                    for t in range(1, 6):
                        items = []
                        for r in rs:
                            if r["player_id"] not in tiers or tiers[r["player_id"]] != t:
                                continue
                            px = num(r["proj"])
                            if r["player_id"] in tg and v == "x":
                                px = r["X"] * (0.25 + 0.75 * B.CEIL[0]) + 0.75 * B.CEIL[1]
                            items.append({"r": r, "adp": -G.adp(r), "proj": float(int(px + 0.5)) if px is not None else None,
                                          "projx": px, "boom": num(r["boom"]), "drafted": -num(r["drafted"]) if num(r["drafted"]) is not None else None})
                        for it in T.rule_sort(items, T.RULE_STEPS[w][t]):
                            rank += 1
                            order[it["r"]["player_id"]] = rank
                    pool = [r for r in rs if r["player_id"] in order and r["player_id"] in base]
                    for i in range(len(pool)):
                        for j in range(i + 1, len(pool)):
                            x, y = pool[i], pool[j]
                            if x["player_id"] not in tg and y["player_id"] not in tg:
                                continue
                            if abs(G.adp(x) - G.adp(y)) > G.DECISION or x["slot"] == y["slot"]:
                                continue
                            vb, vv = base[x["player_id"]] < base[y["player_id"]], order[x["player_id"]] < order[y["player_id"]]
                            if vb == vv:
                                continue
                            a_, b_ = (x, y) if vv else (y, x)
                            g = a_["slot"] - b_["slot"]
                            res[v][0][d].append(g)
                            for pid in tg:
                                if pid in (x["player_id"], y["player_id"]):
                                    res[v][1][pid].append(g)
            out.append("| %s | %s | %s |" % (w.upper(), tt, " | ".join(G.fmt(G.verdict(res[v][0], res[v][1])) for v in ("one", "two", "x"))))

    # ---- e. beneficiaries
    out += ["", "## e. Beneficiaries: undrafted or T5 players with a teammate tagged at the AM lock", ""]
    bands = {}
    for (d, w), rs in locks.items():
        if w != "am":
            continue
        pod = int(rs[0]["pod"])
        pr = sorted((r for r in rs if num(r["adp"]) is not None and r["played"] != ""), key=G.adp)
        for i, r in enumerate(pr):
            bands.setdefault((d, min(i // pod, 6)), []).append(r["slot"])
        for i, r in enumerate(pr):
            r["band"] = min(i // pod, 6)
    swap_hits = collections.Counter()
    for r in csv.DictReader(open(os.path.join(REP, "swaps.csv"))):
        swap_hits[(r["date"], r["swap_id"])] += int(r["teams"])
    rows = []
    for (d, w), rs in locks.items():
        if w != "am" or rs[0]["pod"] != "6":
            continue
        tagged_by_team = collections.defaultdict(list)
        for r in rs:
            if QT.match(r["tag"] or ""):
                tagged_by_team[r["team"]].append(r)
        for r in rs:
            mates = [m for m in tagged_by_team.get(r["team"], []) if m["player_id"] != r["player_id"]]
            if not mates or not (r["tier"] == "5" or num(r["adp"]) is None) or r["played"] == "":
                continue
            sat = any(m["played"] == "0" for m in mates)
            band_mean = None
            if r.get("band") is not None and bands.get((d, r["band"])):
                bm = bands[(d, r["band"])]
                band_mean = sum(bm) / len(bm)
            rows.append({"d": d, "r": r, "sat": sat, "r6": r.get("band") == 5, "over": r["slot"] - band_mean if band_mean is not None else None,
                         "hit": swap_hits[(d, r["player_id"])]})
    out += ["| Group | Players | Teammate sat | Score over his ADP band | Swap target (any credited swaps) |", "|---|---|---|---|---|"]
    for name, sel in (("Round 6 at the AM lock, teammate sat", lambda x: x["r6"] and x["sat"]),
                      ("Round 6 at the AM lock, teammate played", lambda x: x["r6"] and not x["sat"]),
                      ("All (T5 or undrafted), teammate sat", lambda x: x["sat"]),
                      ("All (T5 or undrafted), teammate played", lambda x: not x["sat"])):
        rs = [x for x in rows if sel(x)]
        ov = [x["over"] for x in rs if x["over"] is not None]
        out.append("| %s | %d | %d | %s | %d (%d swaps) |" % (name, len(rs), sum(1 for x in rs if x["sat"]),
                                                            "%+.1f (%d with a band)" % (sum(ov) / len(ov), len(ov)) if ov else "-",
                                                            sum(1 for x in rs if x["hit"]), sum(x["hit"] for x in rs)))

    # ---- scratch cost by tier
    out += ["", "## Implied cost of a scratch, by tier", "",
            "Each tier's average score (players who played, at the PM lock; T5 drafted only) against the average swap for "
            "players ruled out from that tier (credited swaps, weighted by teams). Priced up: at the PM lock every teammate "
            "projected for 20+ was already drafted inside ADP 30, so no cheap beneficiary was left for a swap; cheap: one was. "
            "Excluded from swap tests: " + "; ".join("%s (%s)" % kv for kv in sorted(SW.EXCLUDED.items())) + ".", "",
            "Swaps in money (contest side, money_report.md \"Swaps by the ruled-out player's tier\", 2026-11-09, on the swap "
            "credits before the 11-09 re-credit): teams with a T1-T2 scratch reached the top 10% at 0.42 times the rate of "
            "same-price teams with no swap (finish 13.4 percentile points worse; 6,262 teams, 5 slates); T3-T5 scratches 0.79 "
            "(finish +4.2; 12,522 teams, 10 slates). The swap doesn't make the slot whole in money, least of all at the top. "
            "No rule change yet.", "",
            "| Tier (PM lock; AM if off the PM board) | Tier average | Out players (the real sample) | Swaps | Swap average (range by player) | Cost | Priced-up teammates: swaps, average | Cheap teammates: swaps, average |",
            "|---|---|---|---|---|---|---|---|"]
    tavg = {}
    for t in "12345":
        rs = [r for r in H if r["window"] == "pm" and r["pod"] == "6" and r["tier"] == t and r["played"] == "1" and num(r["adp"]) is not None]
        tavg[t] = sum(num(r["actual"]) for r in rs) / len(rs) if rs else None
    sw_rows = list(csv.DictReader(open(os.path.join(REP, "swaps.csv"))))
    pm_rows = collections.defaultdict(list)          # (date, team) -> his teammates at the PM lock
    for r in H:
        if r["window"] == "pm":
            pm_rows[(r["date"], r["team"])].append(r)

    def priced_up(d, out_id):
        """Every teammate projected for 20+ (median) at the PM lock was already drafted inside ADP 30: no cheap beneficiary."""
        team = daily.get((d, out_id), {}).get("team")
        mates = [m for m in pm_rows.get((d, team), []) if m["player_id"] != out_id and m["med"] is not None and m["med"] >= 20]
        return bool(mates) and all(num(m["adp"]) is not None and num(m["adp"]) < 30 for m in mates)
    per_out = collections.defaultdict(lambda: [0, 0.0])
    for r in sw_rows:
        t = r["out_tier_pm"] if r["out_tier_pm"] not in ("", "-") else r["out_tier_am"]
        k = (t, r["date"], r["out_id"])
        per_out[k][0] += int(r["teams"])
        per_out[k][1] += int(r["teams"]) * float(r["swap_fp"])
    for t in "12345":
        ks = [k for k in per_out if k[0] == t]
        if not ks:
            continue
        n = sum(per_out[k][0] for k in ks)
        avg = sum(per_out[k][1] for k in ks) / n
        avgs = [per_out[k][1] / per_out[k][0] for k in ks]
        up = [k for k in ks if priced_up(k[1], k[2])]
        cheap = [k for k in ks if k not in up]
        part = lambda kk: "%d, %.1f" % (sum(per_out[k][0] for k in kk), sum(per_out[k][1] for k in kk) / sum(per_out[k][0] for k in kk)) if kk else "-"
        out.append("| T%s | %s | %d%s | %d | %.1f (%.1f to %.1f) | %s | %s | %s |" % (
            t, "%.1f" % tavg[t] if tavg[t] else "-", len(ks), " (anecdote: under 5 players)" if len(ks) < 5 else "", n, avg, min(avgs), max(avgs),
            "%+.1f" % (avg - tavg[t]) if tavg[t] else "-", part(up), part(cheap)))
    open(OUT, "w").write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
