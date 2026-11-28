"""1a. Greens on every graded slate, retroactively, with the shipped weights (dk.html checksMap, 2026-11-24):
score = 0.42 OBPR + 1.63 MPG + 0 DK/min + 4.45 5x-rate + 0.50 (1 - under-2x rate), each box a mid-rank percentile among the
slate's rotation players (season mpg >= 15, 3+ games, any status); OBPR and MPG 75% slate-wide + 25% within salary band
(<5k, 5-7k, 7k+), OBPR floored at 0.7 for a team's top-2 BPR; 5x / under-2x half last 5, half season at tonight's salary.
Green: score >= 5.2, season mpg >= 20, projected minutes >= 20, not Out, 1+ game; Questionable counts as grey (the
page greys Q with no Play decision; the decisions are not logged).
Then green vs non-green actual outcomes among the slate's rotation players who were not Out, matched on salary band x
projection band (our lock DK projection fp_dk: <10, 10-25, 25+), per slate; mean and SE over slates.

  python3 greens_player.py --logs gamelogs.json --brr ../battle-royale-research [--fetch] > greens_player.out
  (--fetch writes gamelogs.json first: ESPN's game log per player, cbb_nightly.form(), as dk_checks_weights.py --fetch)
Writes greens_by_slate.json (the green ids per slate, for the lineup replays)."""
import argparse, csv, glob, json, math, os, statistics as St
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DK = os.path.dirname(HERE)
W = {"obpr": 0.42, "mpg": 1.63, "ppm": 0.0, "x5": 4.45, "x2": 0.50}
GREEN, GUARD, PRICE, BLEND = 5.2, 20, 0.75, 0.5


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pctf(pool):
    s = sorted(v for v in pool if v is not None)

    def f(v):
        if v is None or not s:
            return 0.5
        lo = sum(1 for x in s if x < v)
        hi = sum(1 for x in s if x <= v)
        return (lo + hi) / 2 / len(s)
    return f


def band(s):
    return 0 if s < 5000 else 1 if s < 7000 else 2


def rate(games, sal, x):
    if not games:
        return None
    return sum(1 for g in games if (g >= x * sal if x > 0 else g < -x * sal)) / len(games)


def checks(P, logs):
    """{dk_id: (score, green)} on one slate's lock rows P."""
    rows = []
    for k, p in P.items():
        tip = str(p.get("game_start") or "9999")[:10]
        g = logs.get(str(p.get("espn"))) or {}
        sea = [x for d, x in zip(g.get("dates", []), g.get("dks", [])) if d < tip]
        l5 = [q[2] for q in (p.get("last5") or [])]
        if not l5 and sea:
            l5 = sea[-5:]
        sal = p["salary"] / 1000
        def bl(x):
            a, b = rate(l5, sal, x), rate(sea, sal, x)
            if a is None and b is None:
                return None
            if b is None:
                return a
            if a is None:
                return b
            return BLEND * a + (1 - BLEND) * b
        ppm = p["dk_avg"] / p["min_avg"] if p.get("min_avg") and p.get("dk_avg") is not None else None
        rows.append(dict(id=k, p=p, obpr=p.get("obpr"), mpg=p.get("min_avg"), ppm=ppm, x5=bl(5), x2=bl(-2)))
    rot = [r for r in rows if (r["p"].get("min_avg") or 0) >= 15 and (r["p"].get("gp") or 0) >= 3]
    f = {k: pctf([r[k] for r in rot]) for k in ("obpr", "mpg", "ppm", "x5", "x2")}
    fb = {k: [pctf([r[k] for r in rot if band(r["p"]["salary"]) == b]) for b in range(3)] for k in ("obpr", "mpg", "ppm")}
    out = {}
    for r in rows:
        p, b = r["p"], band(r["p"]["salary"])
        pr = lambda k: 0.5 if r[k] is None else PRICE * f[k](r[k]) + (1 - PRICE) * fb[k][b](r[k])
        s1 = pr("obpr")
        if p.get("bpr_rank") is not None and p["bpr_rank"] <= 2:
            s1 = max(s1, 0.7)
        sc = W["obpr"] * s1 + W["mpg"] * pr("mpg") + W["ppm"] * pr("ppm") + W["x5"] * f["x5"](r["x5"]) + W["x2"] * (1 - f["x2"](r["x2"]))
        grey = p.get("status") in ("Out", "Questionable") or not p.get("gp")
        guard = (p.get("min_avg") or 0) >= GUARD and (p.get("min") or 0) >= GUARD
        out[r["id"]] = (sc, (not grey) and guard and sc >= GREEN)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", required=True)
    ap.add_argument("--brr", required=True)
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        import sys
        from concurrent.futures import ThreadPoolExecutor
        sys.path.insert(0, os.path.join(a.brr, "scripts"))
        import cbb_nightly as c
        ids = sorted({r["espn"] for f in glob.glob(os.path.join(DK, "2026-11-*_1*.csv")) for r in csv.DictReader(open(f)) if r["espn"]})
        go = lambda i: (i, (lambda f: {"dates": f["dates"], "dks": f["dks"], "mins": f["mins"]} if f else None)(c.form(i)))
        with ThreadPoolExecutor(12) as ex:
            json.dump(dict(ex.map(go, ids)), open(a.logs, "w"))
    logs = json.load(open(a.logs))
    per, greens = [], {}
    pool_all = []
    for f in sorted(glob.glob(os.path.join(DK, "2026-11-*_1*.csv"))):
        tag = os.path.basename(f)[:-4]
        pj = os.path.join(a.brr, "data", "dk", "cbb", tag + "_proj.json")
        if not os.path.exists(pj):
            continue
        P = json.load(open(pj))
        if not P:
            continue
        C = checks(P, logs)
        greens[tag] = sorted(k for k, (s, g) in C.items() if g)
        rows = []
        for r in csv.DictReader(open(f)):
            p, act, fp = P.get(r["dk_id"]), num(r["actual_dk"]), num(r["fp_dk"])
            if not p or act is None or fp is None or p.get("status") == "Out":
                continue
            if (p.get("min_avg") or 0) < 15 or (p.get("gp") or 0) < 3:
                continue
            sal = p["salary"] / 1000
            rows.append(dict(g=C[r["dk_id"]][1], sb=band(p["salary"]), pb=0 if fp < 10 else 1 if fp < 25 else 2,
                             x5=1.0 if act >= 5 * sal else 0.0, res=act - fp, ppk=act / sal, val=fp / sal, act=act, fp=fp))
        pool_all += [dict(r, slate=tag) for r in rows]
        G = [r for r in rows if r["g"]]
        if not G:
            per.append((tag, len(rows), 0, None))
            continue
        # matched: per salary x projection cell, green mean - non-green mean, weighted by the cell's greens
        d = {m: [] for m in ("x5", "res", "ppk", "val")}
        wt = []
        for sb in range(3):
            for pb in range(3):
                g = [r for r in rows if r["g"] and r["sb"] == sb and r["pb"] == pb]
                n = [r for r in rows if not r["g"] and r["sb"] == sb and r["pb"] == pb]
                if g and n:
                    for m in d:
                        d[m].append(St.mean(r[m] for r in g) - St.mean(r[m] for r in n))
                    wt.append(len(g))
        if not wt:
            per.append((tag, len(rows), len(G), None))
            continue
        per.append((tag, len(rows), len(G), {m: float(np.average(v, weights=wt)) for m, v in d.items()} | {"matched": sum(wt)},
                    {"x5": St.mean(r["x5"] for r in G), "res": St.mean(r["res"] for r in G)}))
    json.dump(greens, open(os.path.join(HERE, "greens_by_slate.json"), "w"), indent=0)
    print("1a. Greens on every graded slate (shipped weights), green minus matched non-green (same salary band x projection band)")
    print("%-18s %4s %4s %4s | %7s %7s %7s %7s" % ("slate", "rot", "grn", "mtch", "5x", "act-prj", "DK/$1k", "projval"))
    S = {m: [] for m in ("x5", "res", "ppk", "val")}
    for row in per:
        tag, n, g, d = row[:4]
        if d is None:
            print("%-18s %4d %4d    - |   (no matched greens)" % (tag, n, g))
            continue
        for m in S:
            S[m].append(d[m])
        print("%-18s %4d %4d %4d | %+7.3f %+7.2f %+7.3f %+7.3f" % (tag, n, g, d["matched"], d["x5"], d["res"], d["ppk"], d["val"]))
    print()
    for m, lab in (("x5", "5x rate"), ("res", "actual - our projection"), ("ppk", "DK per $1k"), ("val", "our projected value (pts/$1k), for reference")):
        v = S[m]
        se = St.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
        print("%-48s %+.3f ± %.3f over %d slates, positive on %d" % (lab, St.mean(v), se, len(v), sum(1 for x in v if x > 0)))
    # unmatched raw: greens vs all rotation players
    G = [r for r in pool_all if r["g"]]
    N = [r for r in pool_all if not r["g"]]
    print("\nraw (unmatched), all slates pooled: greens n=%d 5x %.3f act-prj %+.2f | non-greens n=%d 5x %.3f act-prj %+.2f" % (
        len(G), St.mean(r["x5"] for r in G), St.mean(r["res"] for r in G), len(N), St.mean(r["x5"] for r in N), St.mean(r["res"] for r in N)))
    # does green add to our projection? logistic-free check: within projected-value deciles, green vs not 5x rate
    print("\n5x rate by our projected-value tercile (pooled rows), green vs non-green:")
    vals = sorted(r["val"] for r in pool_all)
    cuts = [vals[len(vals) // 3], vals[2 * len(vals) // 3]]
    for i, lab in enumerate(("low", "mid", "high")):
        sel = [r for r in pool_all if (r["val"] < cuts[0] if i == 0 else r["val"] < cuts[1] if i == 1 else True) and (i == 0 or r["val"] >= cuts[i - 1])]
        g = [r for r in sel if r["g"]]
        n = [r for r in sel if not r["g"]]
        print("  %-5s greens n=%3d 5x %.3f act-prj %+5.2f | others n=%4d 5x %.3f act-prj %+5.2f" % (lab, len(g), St.mean(r["x5"] for r in g) if g else float("nan"),
              St.mean(r["res"] for r in g) if g else float("nan"), len(n), St.mean(r["x5"] for r in n), St.mean(r["res"] for r in n)))


main()
