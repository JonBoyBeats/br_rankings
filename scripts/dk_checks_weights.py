"""The checks weighting study (the operator, 2026-11-24; analysis only, nothing on the page changes).

The game view's checks count 7 pass/fail boxes as equals (dk.html checksMap): 1 OBPR, 2 MPG, 3 DK per minute,
4 5x rate, 5 under-2x rate (both on the last 5 games), 6 bank / field, 7 scan read. This asks whether a weighted
score of the same boxes, each a continuous 0-1 score (the player's percentile in the slate's rotation pool),
picks tonight's 5x players better than the equal count, and better than our own projection.

Data, all known at lock:
  lock-time rows   BRR data/dk/cbb/<date>_<dg>_proj.json (obpr, bpr_rank, min_avg, gp, dk_avg, min, salary, fp)
  season game logs ESPN's athlete gamelog (the endpoint cbb_nightly.form() reads), games before tonight's tip only
  results          analysis/cbb/dk/<date>_<dg>.csv (actual_dk), the graded slates
Target: actual DK points >= 5 x salary in thousands (secondary: points per $1k).
Pool: the slate's rotation players (season mpg >= 15 and 3+ games, the checks' own pool), not tagged Out at lock.

Variants (operator's preferences):
  boxes 4-5   rate = w x last-5 rate + (1 - w) x season rate, w in 0 / .25 / .5 / .75 / 1
  minutes     season mpg | season mpg with recent games weighted up (0.8 per game back) | tonight's projection
  price       boxes 1-3 percentile slate-wide | within salary bands (<5k, 5-7k, 7k+) | blends .75/.25, .5/.5
Model: L2 logistic on the 5 scores (no negative weights: a negative one is dropped and the fit redone),
leave-one-slate-out; the variant is chosen inside the training slates (inner leave-one-out), so the held-out
slate never picks its own variant. Compared on each held-out slate with (a) the page's equal count at its
cutoffs (the same last-5 games, reconstructed from the logs where the lock file had none) and (c) our
projection's value (fp / salary) and our P(5x) (normal around fp with sd = 1.25 x the expected miss).

Usage: python3 scripts/dk_checks_weights.py --brr ../battle-royale-research --logs <gamelogs.json> [--fetch]
"""
import argparse
import csv
import glob
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DK = os.path.join(ROOT, "analysis", "cbb", "dk")
CK = {"rotMpg": 15, "rotGp": 3, "obprTop": 30, "obprTeam": 2, "mpgPct": 70, "mpgAbs": 28, "ppmPct": 60, "x5Pct": 60, "x2Pct": 40}
BANDS = (5000, 7000)
BLEND_W = (0.0, 0.25, 0.5, 0.75, 1.0)
MINUTES = ("season", "recent", "proj")
PRICE = ("slate", "band", "mix75", "mix50")
FORM = 0.8
L2 = 1.0
GUARD_MIN = 20
NAMES = ["OBPR", "MPG", "DK/min", "5x rate", "under-2x"]


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ckq(a, p):                                   # the page's percentile cut (nearest rank)
    v = sorted(x for x in a if x is not None)
    if not v:
        return None
    return v[max(0, min(len(v) - 1, math.ceil(p / 100 * len(v)) - 1))]


def pct(vals):
    """Each value's percentile in the list (mid-rank / n, 0..1); None stays None (scored 0.5)."""
    ok = [(v, i) for i, v in enumerate(vals) if v is not None]
    out = [0.5] * len(vals)
    if not ok:
        return out
    srt = sorted(v for v, _ in ok)
    n = len(srt)
    for v, i in ok:
        lo = np.searchsorted(srt, v, "left")
        hi = np.searchsorted(srt, v, "right")
        out[i] = (lo + hi) / 2 / n
    return out


def band(sal):
    return 0 if sal < BANDS[0] else 1 if sal < BANDS[1] else 2


def load(brr, logs):
    slates = []
    for f in sorted(glob.glob(os.path.join(DK, "2026-11-*_1*.csv"))):
        tag = os.path.basename(f)[:-4]
        pj = os.path.join(brr, "data", "dk", "cbb", tag + "_proj.json")
        if not os.path.exists(pj):
            continue
        P = json.load(open(pj))
        rows = []
        for r in csv.DictReader(open(f)):
            p = P.get(r["dk_id"])
            if not p or (p.get("min_avg") or 0) < CK["rotMpg"] or (p.get("gp") or 0) < CK["rotGp"] or p.get("status") == "Out":
                continue
            act = num(r["actual_dk"])
            if act is None:
                continue
            sal = p["salary"] / 1000
            tip = str(p.get("game_start") or r["date"])[:10]
            g = logs.get(r["espn"]) or {}
            games = [(d, m, x) for d, m, x in zip(g.get("dates", []), g.get("mins", []), g.get("dks", [])) if d < tip]
            if len(games) < 1 and p.get("last5"):
                games = [(d, m, x) for d, m, x in p["last5"]]
            last5 = games[-5:]
            rows.append({"slate": tag, "name": p["name"], "team": p["team"], "dk_id": r["dk_id"], "sal": p["salary"],
                         "fp": p.get("fp"), "miss": num(r.get("miss_dk")) or p.get("miss_dk") or 8.0, "min_proj": p.get("min"),
                         "min_avg": p.get("min_avg"), "gp": p.get("gp"), "dk_avg": p.get("dk_avg"), "obpr": p.get("obpr"),
                         "bpr_rank": p.get("bpr_rank"), "games": games, "last5": last5, "status": p.get("status"),
                         "y": 1 if act >= 5 * sal else 0, "ppk": act / sal, "act": act})
        if len(rows) >= 15 and sum(x["y"] for x in rows) >= 2:
            slates.append((tag, rows))
    return slates


def rate(g, sal, x):
    if not g:
        return None
    return sum(1 for q in g if (q[2] >= x * sal if x > 0 else q[2] < -x * sal)) / len(g)


def recent_mpg(r):
    g = r["games"]
    if not g:
        return r["min_avg"]
    w = [FORM ** (len(g) - 1 - j) for j in range(len(g))]
    return sum(a * q[1] for a, q in zip(w, g)) / sum(w)


def features(rows, w, minutes, price):
    """The five continuous box scores (0-1) for one slate's pool under one variant."""
    sal = [r["sal"] / 1000 for r in rows]
    obpr = [r["obpr"] for r in rows]
    mpg = [r["min_avg"] if minutes == "season" else recent_mpg(r) if minutes == "recent" else r["min_proj"] for r in rows]
    ppm = [r["dk_avg"] / r["min_avg"] if r["min_avg"] and r["dk_avg"] is not None else None for r in rows]
    x5 = []
    x2 = []
    for r, s in zip(rows, sal):
        a5, b5 = rate(r["last5"], s, 5), rate(r["games"], s, 5)
        a2, b2 = rate(r["last5"], s, -2), rate(r["games"], s, -2)
        x5.append(None if a5 is None else w * a5 + (1 - w) * b5)
        x2.append(None if a2 is None else w * a2 + (1 - w) * b2)

    def priced(vals):
        s = pct(vals)
        if price == "slate":
            return s
        bands = [band(r["sal"]) for r in rows]
        bp = [0.5] * len(rows)
        for b in (0, 1, 2):
            ix = [i for i in range(len(rows)) if bands[i] == b]
            for i, v in zip(ix, pct([vals[i] for i in ix])):
                bp[i] = v
        a = {"band": 0.0, "mix75": 0.75, "mix50": 0.5}[price]
        return [a * x + (1 - a) * y for x, y in zip(s, bp)]

    f1 = priced(obpr)
    # the page's "top-2 on his team" route into box 1 kept as a floor on the score
    f1 = [max(v, 0.7) if (r["bpr_rank"] or 99) <= CK["obprTeam"] else v for v, r in zip(f1, rows)]
    f2, f3 = priced(mpg), priced(ppm)
    f4 = pct(x5)
    f5 = [1 - v for v in pct(x2)]
    return np.array([f1, f2, f3, f4, f5]).T


def equal_count(rows):
    """The page's checks, boxes 1-5 pass/fail at its cutoffs (the same pool and last-5 games)."""
    o = CK
    three = [r for r in rows if len(r["last5"]) >= 3]
    ppm = lambda r: r["dk_avg"] / r["min_avg"] if r["min_avg"] and r["dk_avg"] is not None else None
    cut = {"obpr": ckq([r["obpr"] for r in rows], 100 - o["obprTop"]), "mpg": ckq([r["min_avg"] for r in rows], o["mpgPct"]),
           "ppm": ckq([ppm(r) for r in rows], o["ppmPct"]),
           "x5": ckq([rate(r["last5"], r["sal"] / 1000, 5) for r in three], o["x5Pct"]),
           "x2": ckq([rate(r["last5"], r["sal"] / 1000, -2) for r in three], o["x2Pct"])}
    out = []
    for r in rows:
        s = r["sal"] / 1000
        n3 = len(r["last5"]) >= 3
        x5, x2, p = rate(r["last5"], s, 5), rate(r["last5"], s, -2), ppm(r)
        b = [r["obpr"] is not None and ((cut["obpr"] is not None and r["obpr"] >= cut["obpr"]) or (r["bpr_rank"] or 99) <= o["obprTeam"]),
             r["min_avg"] is not None and ((cut["mpg"] is not None and r["min_avg"] >= cut["mpg"]) or r["min_avg"] >= o["mpgAbs"]),
             p is not None and cut["ppm"] is not None and p >= cut["ppm"],
             n3 and x5 is not None and cut["x5"] is not None and x5 >= cut["x5"] and x5 > 0,
             n3 and x2 is not None and cut["x2"] is not None and x2 <= cut["x2"]]
        out.append(sum(b))
    return np.array(out, float)


def fit(X, y):
    """L2 logistic with no negative weights: a weight below 0 is dropped and the fit redone."""
    keep = list(range(X.shape[1]))
    while True:
        Z = np.column_stack([np.ones(len(X)), X[:, keep]])

        def nll(b):
            t = Z @ b
            return np.sum(np.logaddexp(0, t) - y * t) + L2 * np.sum(b[1:] ** 2)

        def grad(b):
            p = 1 / (1 + np.exp(-(Z @ b)))
            g = Z.T @ (p - y)
            g[1:] += 2 * L2 * b[1:]
            return g

        b = minimize(nll, np.zeros(Z.shape[1]), jac=grad, method="L-BFGS-B").x
        neg = [k for k, v in zip(keep, b[1:]) if v < 0]
        if not neg:
            w = np.zeros(X.shape[1])
            w[keep] = b[1:]
            return b[0], w
        keep = [k for k in keep if k not in neg]
        if not keep:
            return b[0], np.zeros(X.shape[1])


def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y)
    if y.sum() == 0 or y.sum() == len(y):
        return None
    r = np.argsort(np.argsort(s + 1e-9 * np.random.default_rng(0).random(len(s))))
    from scipy.stats import rankdata
    rk = rankdata(s)
    n1 = y.sum()
    return (rk[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1))


def topk(s, y, k):
    o = np.argsort(-np.asarray(s, float), kind="stable")[:k]
    return int(np.asarray(y)[o].sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brr", default=os.path.join(os.path.dirname(ROOT), "battle-royale-research"))
    ap.add_argument("--logs", required=True, help="gamelogs.json: {espn id: {dates, mins, dks}} (--fetch writes it)")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--out", default=os.path.join(DK, "checks_weights_2026-11-24"))
    ap.add_argument("--price", default=",".join(PRICE), help="price treatments to allow (the operator: price counts a little)")
    a = ap.parse_args()
    if a.fetch:
        sys.path.insert(0, os.path.join(a.brr, "scripts"))
        import cbb_nightly as c
        from concurrent.futures import ThreadPoolExecutor
        ids = sorted({r["espn"] for f in glob.glob(os.path.join(DK, "2026-11-*_1*.csv")) for r in csv.DictReader(open(f)) if r["espn"]})

        def go(i):
            f = c.form(i)
            return i, ({"dates": f["dates"], "dks": f["dks"], "mins": f["mins"]} if f else None)
        with ThreadPoolExecutor(8) as ex:
            json.dump(dict(ex.map(go, ids)), open(a.logs, "w"))
    logs = json.load(open(a.logs))
    slates = load(a.brr, logs)
    os.makedirs(a.out, exist_ok=True)
    tags = [t for t, _ in slates]
    variants = [(w, m, p) for w in BLEND_W for m in MINUTES for p in a.price.split(",")]
    feats = {v: {t: features(rows, *v) for t, rows in slates} for v in variants}
    Y = {t: np.array([r["y"] for r in rows]) for t, rows in slates}

    def cv_auc(v, train):                       # inner leave-one-out mean AUC over the training slates
        A = []
        for h in train:
            tr = [t for t in train if t != h]
            b0, w = fit(np.vstack([feats[v][t] for t in tr]), np.concatenate([Y[t] for t in tr]))
            x = auc(feats[v][h] @ w, Y[h])
            if x is not None:
                A.append(x)
        return float(np.mean(A)) if A else 0.0

    # every variant's plain leave-one-slate-out AUC (for the tables), then the honest nested run
    var_rows = []
    for v in variants:
        A = []
        for h in tags:
            tr = [t for t in tags if t != h]
            b0, w = fit(np.vstack([feats[v][t] for t in tr]), np.concatenate([Y[t] for t in tr]))
            A.append(auc(feats[v][h] @ w, Y[h]))
        A = [x for x in A if x is not None]
        var_rows.append({"w_last5": v[0], "minutes": v[1], "price": v[2], "auc": round(float(np.mean(A)), 4)})
    with open(os.path.join(a.out, "variants.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(var_rows[0]), lineterminator="\r\n")
        wr.writeheader()
        wr.writerows(var_rows)

    per = []
    picks = []
    for h, rows in slates:
        tr = [t for t in tags if t != h]
        best = max(variants, key=lambda v: cv_auc(v, tr))
        picks.append(best)
        b0, w = fit(np.vstack([feats[best][t] for t in tr]), np.concatenate([Y[t] for t in tr]))
        y = Y[h]
        sb = feats[best][h] @ w
        sa = equal_count(rows) + 1e-3 * np.array([r["fp"] or 0 for r in rows]) / 100     # ties in the count broken by projection
        val = np.array([(r["fp"] or 0) / (r["sal"] / 1000) for r in rows])
        p5 = np.array([1 - norm.cdf((5 * r["sal"] / 1000 - (r["fp"] or 0)) / (1.25 * r["miss"])) for r in rows])
        ppk = np.array([r["ppk"] for r in rows])
        row = {"slate": h, "n": len(rows), "hits": int(y.sum()), "variant": "%s/%s/%s" % best}
        for k, s in (("a", sa), ("b", sb), ("value", val), ("p5x", p5)):
            row["auc_" + k] = auc(s, y)
            row["top10_" + k] = topk(s, y, 10)
            row["top20_" + k] = topk(s, y, 20)
            row["rho_" + k] = float(spearmanr(s, ppk).statistic)
        row["weights"] = [round(float(x), 3) for x in w]
        per.append(row)
    with open(os.path.join(a.out, "per_slate.csv"), "w", newline="") as fh:
        keys = [k for k in per[0] if k != "weights"]
        wr = csv.DictWriter(fh, fieldnames=keys, lineterminator="\r\n", extrasaction="ignore")
        wr.writeheader()
        wr.writerows(per)

    # the final fit: the variant most often picked, fitted on every slate; rescaled so a perfect player scores 7
    from collections import Counter
    final = Counter(picks).most_common(1)[0][0]
    b0, w = fit(np.vstack([feats[final][t] for t in tags]), np.concatenate([Y[t] for t in tags]))
    w7 = 7 * w / w.sum() if w.sum() > 0 else w
    # the green threshold, held out. A green should mean about as many players as today's green (4+ of 5 boxes), so
    # on each slate the cut is the training slates' score at today's green share, then scored on the held-out slate.
    # The guard (the operator: no fringe or bench player propped up): green needs season mpg and tonight's
    # projected minutes both >= GUARD_MIN. Reported with and without it.
    def guard(r):
        return (r["min_avg"] or 0) >= GUARD_MIN and (r["min_proj"] or 0) >= GUARD_MIN
    thr_rows = []
    for h, rows in slates:
        tr = [t for t in tags if t != h]
        b0h, wh = fit(np.vstack([feats[final][t] for t in tr]), np.concatenate([Y[t] for t in tr]))
        w7h = 7 * wh / wh.sum()
        S = np.concatenate([feats[final][t] @ w7h for t in tr])
        share = np.mean(np.concatenate([equal_count(dict(slates)[t]) >= 4 for t in tr]))
        c = float(np.quantile(S, 1 - share))
        sh = feats[final][h] @ w7h
        gd = np.array([guard(r) for r in rows])
        g, gg = sh >= c, (sh >= c) & gd
        cur = equal_count(rows) >= 4                      # today's green with 5 boxes counted: 4+ of 5 (80%)
        y = Y[h] == 1
        thr_rows.append({"slate": h, "cut": round(c, 2), "green_new": int(g.sum()), "hit_new": int((g & y).sum()),
                         "green_guard": int(gg.sum()), "hit_guard": int((gg & y).sum()),
                         "green_now": int(cur.sum()), "hit_now": int((cur & y).sum()), "hits": int(y.sum()),
                         "fringe_new": int((g & ~gd & ~cur).sum()), "fringe_now": int((cur & ~gd).sum()),
                         # the same number of players picked by our own P(5x) instead (the plain baseline)
                         "hit_p5x_same_n": topk(np.array([1 - norm.cdf((5 * r["sal"] / 1000 - (r["fp"] or 0)) / (1.25 * r["miss"])) for r in rows]),
                                                Y[h], int(gg.sum()))})
    cut = float(np.median([r["cut"] for r in thr_rows]))
    # bench / fringe players newly green at that cut without the guard (projected or season minutes under 20)
    fringe = []
    for t, rows in slates:
        s7 = feats[final][t] @ w7
        cur = equal_count(rows) >= 4
        for r, s, c0 in zip(rows, s7, cur):
            if s >= cut and not c0 and not guard(r):
                fringe.append({"slate": t, "name": r["name"], "team": r["team"], "salary": r["sal"], "min_proj": r["min_proj"],
                               "mpg": r["min_avg"], "score7": round(float(s), 2), "hit5x": r["y"]})
    with open(os.path.join(a.out, "greens.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(thr_rows[0]), lineterminator="\r\n")
        wr.writeheader()
        wr.writerows(thr_rows)
    tot = {k: sum(r[k] for r in thr_rows) for k in thr_rows[0] if k not in ("slate", "cut")}
    print("greens held out:", tot)
    summary = {"slates": len(slates), "players": sum(len(r) for _, r in slates), "hits": int(sum(Y[t].sum() for t in tags)),
               "final_variant": {"w_last5": final[0], "minutes": final[1], "price": final[2]},
               "weights7": dict(zip(NAMES, [round(float(x), 2) for x in w7])), "raw_weights": [round(float(x), 3) for x in w],
               "green_cut": cut, "picks": Counter("%s/%s/%s" % p for p in picks).most_common(), "fringe_new_green": fringe,
               "threshold_rows": thr_rows, "green_totals": tot, "guard_min": GUARD_MIN}
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=1)

    def stats(key_b, key_a):
        d = [r[key_b] - r[key_a] for r in per if r[key_b] is not None and r[key_a] is not None]
        m, se = float(np.mean(d)), float(np.std(d, ddof=1) / math.sqrt(len(d)))
        return m, se, sum(x > 0 for x in d), sum(x < 0 for x in d), len(d)
    print("slates", len(slates), "players", summary["players"], "5x hits", summary["hits"])
    for k in ("a", "b", "value", "p5x"):
        print(k, "AUC %.3f" % np.mean([r["auc_" + k] for r in per if r["auc_" + k] is not None]),
              "top10 %d top20 %d" % (sum(r["top10_" + k] for r in per), sum(r["top20_" + k] for r in per)),
              "rho %.3f" % np.mean([r["rho_" + k] for r in per]))
    for kb, ka in (("auc_b", "auc_a"), ("auc_b", "auc_value"), ("auc_b", "auc_p5x"), ("auc_value", "auc_a"), ("top10_b", "top10_a"), ("top20_b", "top20_a")):
        m, se, up, dn, n = stats(kb, ka)
        print("%s - %s: %+.4f (SE %.4f) better %d worse %d of %d" % (kb, ka, m, se, up, dn, n))
    print("final", summary["final_variant"], summary["weights7"], "cut", cut, "picks", summary["picks"])
    print("fringe newly green", len(fringe))


if __name__ == "__main__":
    main()
