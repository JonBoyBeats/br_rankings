"""The chalk-miss study (2026-11-24, the operator; analysis only, nothing the page reads): on the chalk band (players
with max(ours, actual) at or over dk_eval.CHALK_OWN, 15%), what predicts the signed miss, actual minus our projected
ownership? Every feature is defined at lock from the night record (analysis/cbb/dk/<date>_<draft group>.csv, the
projection at lock) and, for the big-game flag, the mirror's morning file before the slate started.

  a  val_rank     his value (projected DK points per $1K) rank within his salary tier on the slate (1 = the best value)
  b  chalk_game   how many players we projected 15%+ in his game; chalk_team the same on his team;
     own_rank     his rank by our projected ownership on his team (1 = our most-owned)
  c  salary       in $1K
  d  big          coming off a big game (last game's DK points 10+ over his season average: dk_eval.ownwatch's rule)
  e  q            tagged Questionable at lock
  f  ou, spread   the game's total; his team's spread (negative = favored)
  g  own          our projected ownership itself

The correction is additive, own' = ours + c0 + b x (the signed miss regressed on one or two features), fitted
leave-one-slate-out and scored on the held-out slate's chalk band: its MAE in points and its share off by 10+ points,
against ours. Two versions:
  A  as specified: fitted and applied on chalk-band rows (the band uses the actual, so this one can't be run at lock)
  B  deployable: fitted and applied on players we projected 10%+ (known at lock), scored on the same chalk band
Pass bar (the Lab's): better MAE on 7+ of the slates AND a mean improvement over 2 x its standard error across slates;
anything short of that is directional only.

  python3 scripts/dk_chalk_miss.py --mirror ../br-adp-mirror
"""
import argparse, csv, glob, itertools, math, os, statistics as S, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E          # noqa: E402
import dk_own_review as R    # noqa: E402

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
FEATS = ["val_rank", "chalk_game", "chalk_team", "own_rank", "salary", "big", "q", "ou", "spread", "own"]
DEPLOY_OWN = 10


def slate_features(rec, big):
    """{dk_id: features} for one slate's night record."""
    live = [r for r in rec if r.get("status") != "Out" and E.num(r.get("own")) is not None]
    tier = lambda s: next(i for i, (lo, hi) in enumerate(E.BANDS) if lo <= s <= hi)
    vr = {}
    for t in range(len(E.BANDS)):
        rs = sorted([r for r in live if tier(E.num(r["salary"])) == t], key=lambda r: -(E.num(r.get("value")) or 0))
        vr.update({r["dk_id"]: i + 1 for i, r in enumerate(rs)})
    chalk = [r for r in live if E.num(r["own"]) >= E.CHALK_OWN]
    cg, ct = defaultdict(int), defaultdict(int)
    for r in chalk:
        cg[r["game"]] += 1; ct[r["team"]] += 1
    orank = {}
    for t in {r["team"] for r in live}:
        rs = sorted([r for r in live if r["team"] == t], key=lambda r: -E.num(r["own"]))
        orank.update({r["dk_id"]: i + 1 for i, r in enumerate(rs)})
    out = {}
    for r in live:
        out[r["dk_id"]] = {"val_rank": vr.get(r["dk_id"], 99), "chalk_game": cg[r["game"]], "chalk_team": ct[r["team"]],
                           "own_rank": orank.get(r["dk_id"], 99), "salary": E.num(r["salary"]) / 1000, "big": float(r["dk_id"] in big),
                           "q": float(r.get("status") == "Questionable"), "ou": E.num(r.get("ou")), "spread": E.num(r.get("spread")),
                           "own": E.num(r["own"])}
    return out


def load(mirror):
    bigs = R.big_game_flags(mirror)
    recs = {}
    for f in glob.glob(os.path.join(DK, "????-??-??_*.csv")):
        rec = E.read(f)
        if rec:
            recs[str(rec[0]["draft_group"])] = rec
    feats = {g: slate_features(rec, bigs.get(g) or set()) for g, rec in recs.items()}
    rows = []
    for r in E.own_grade_rows():
        g = str(r["draft_group"]); x = (feats.get(g) or {}).get(r["dk_id"])
        if x and all(x[k] is not None for k in FEATS):
            rows.append(dict(x, g=g, date=r["date"], cid=r["contest_id"], name=r["name"], p=r["p"], a=r["a"], n=r["n"]))
    return rows


def ols(X, y):
    """Least squares with an intercept: [c0, b1, ...] (normal equations, tiny ridge for safety)."""
    k = len(X[0]) + 1
    A = [[0.0] * k for _ in range(k)]; v = [0.0] * k
    for xs, t in zip(X, y):
        z = [1.0] + list(xs)
        for i in range(k):
            v[i] += z[i] * t
            for j in range(k):
                A[i][j] += z[i] * z[j]
    for i in range(1, k):
        A[i][i] += 1e-6
    for i in range(k):                              # Gauss-Jordan
        piv = max(range(i, k), key=lambda r: abs(A[r][i]))
        A[i], A[piv] = A[piv], A[i]; v[i], v[piv] = v[piv], v[i]
        d = A[i][i] or 1e-12
        for j in range(i, k):
            A[i][j] /= d
        v[i] /= d
        for r in range(k):
            if r != i and A[r][i]:
                f = A[r][i]
                for j in range(i, k):
                    A[r][j] -= f * A[i][j]
                v[r] -= f * v[i]
    return v


def in_band(r):
    return max(r["p"], r["a"]) >= E.CHALK_OWN


def grade(rows, pred):
    """Chalk-band MAE and off-by-10+ share with pred(r) as the projection."""
    ch = [r for r in rows if in_band(r)]
    e = [abs(r["a"] - pred(r)) for r in ch]
    return (S.mean(e), sum(x >= E.CHALK_OFF for x in e) / len(e)) if e else (None, None)


def run(rows, terms, version):
    """Leave one slate out: per slate (ours MAE, cand MAE, ours off10, cand off10)."""
    use = (lambda r: in_band(r)) if version == "A" else (lambda r: r["p"] >= DEPLOY_OWN)
    out = []
    for g in sorted({r["g"] for r in rows}):
        tr = [r for r in rows if r["g"] != g and use(r)]
        te = [r for r in rows if r["g"] == g]
        c = ols([[r[t] for t in terms] for r in tr], [r["a"] - r["p"] for r in tr]) if terms else [S.mean(r["a"] - r["p"] for r in tr)]
        pred = lambda r: max(0.0, r["p"] + c[0] + sum(b * r[t] for b, t in zip(c[1:], terms))) if use(r) else r["p"]
        m0, o0 = grade(te, lambda r: r["p"]); m1, o1 = grade(te, pred)
        if m0 is not None:
            out.append((g, m0, m1, o0, o1))
    return out


def summary(res):
    d = [m0 - m1 for _, m0, m1, _, _ in res]
    se = S.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else float("inf")
    better = sum(x > 1e-9 for x in d)
    off_better = sum(o1 < o0 - 1e-9 for _, _, _, o0, o1 in res)
    return {"ours": S.mean(m0 for _, m0, _, _, _ in res), "cand": S.mean(m1 for _, _, m1, _, _ in res), "gain": S.mean(d), "se": se,
            "better": better, "n": len(d), "off0": S.mean(o0 for *_, o0, _ in res), "off1": S.mean(o1 for *_, o1 in res), "offb": off_better,
            "pass": better >= math.ceil(0.7 * len(d)) and S.mean(d) > 2 * se and S.mean(o1 for *_, o1 in res) <= S.mean(o0 for *_, o0, _ in res)}


def describe(rows):
    """Each feature against the signed miss on the chalk band: pooled correlation and its sign by slate."""
    ch = [r for r in rows if in_band(r)]
    out = []
    for f in FEATS:
        c = E.corr([r[f] for r in ch], [r["a"] - r["p"] for r in ch]) if len({r[f] for r in ch}) > 1 else None
        signs = []
        for g in sorted({r["g"] for r in ch}):
            rs = [r for r in ch if r["g"] == g]
            if len({r[f] for r in rs}) > 1:
                cg = E.corr([r[f] for r in rs], [r["a"] - r["p"] for r in rs])
                if cg is not None:
                    signs.append(cg > 0)
        out.append((f, c, sum(signs), len(signs)))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror")); a = ap.parse_args()
    rows = load(a.mirror)
    ch = [r for r in rows if in_band(r)]
    print("Rows: %d player-contests on %d slates (%d contests); chalk band %d" % (len(rows), len({r["g"] for r in rows}), len({r["cid"] for r in rows}), len(ch)))
    print("\n== Each feature against the signed miss (actual - ours) on the chalk band: pooled correlation, positive on k of n slates ==")
    for f, c, k, n in describe(rows):
        print("  %-10s r %s   positive on %d of %d slates" % (f, "%+.3f" % c if c is not None else "  -  ", k, n))
    for version in ("A", "B"):
        print("\n== Version %s: %s ==" % (version, "fitted and applied on the chalk band (not runnable at lock)" if version == "A"
                                         else "fitted and applied on players we projected %d%%+ (runnable at lock), scored on the chalk band" % DEPLOY_OWN))
        res = {(): summary(run(rows, [], version))}
        for f in FEATS:
            res[(f,)] = summary(run(rows, [f], version))
        singles = sorted(FEATS, key=lambda f: -res[(f,)]["gain"])
        for pair in itertools.combinations(FEATS, 2):
            res[pair] = summary(run(rows, list(pair), version))
        def line(k, s):
            return "  %-24s MAE %.2f vs ours %.2f (gain %+.2f, 2xSE %.2f), better on %d of %d; off by 10+ %.1f%% vs %.1f%% (lower on %d)%s" % (
                "+".join(k) or "bias only", s["cand"], s["ours"], s["gain"], 2 * s["se"], s["better"], s["n"], 100 * s["off1"], 100 * s["off0"], s["offb"],
                "  PASS" if s["pass"] else "")
        print(line((), res[()]))
        for f in singles:
            print(line((f,), res[(f,)]))
        best = sorted([k for k in res if len(k) == 2], key=lambda k: -res[k]["gain"])[:5]
        print("  best pairs:")
        for k in best:
            print(line(k, res[k]))
    # the fit on every slate for the best deployable single and pair, for the write-up
    for terms in (["own"], ["chalk_game"], ["val_rank"]):
        tr = [r for r in rows if r["p"] >= DEPLOY_OWN]
        c = ols([[r[t] for t in terms] for r in tr], [r["a"] - r["p"] for r in tr])
        print("  fit on every slate, players %d%%+ (%s): c0 %+.2f, %s" % (DEPLOY_OWN, "+".join(terms), c[0], ", ".join("%s %+.3f" % (t, b) for t, b in zip(terms, c[1:]))))


if __name__ == "__main__":
    main()
