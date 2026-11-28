"""Time-trend follow-up to the projection pair backtest (2026-11-28, analysis only, HELD).

Are the candidates' gains growing as the season fills in? Reuses ppb.py's rows and candidate code (executed up to its
baseline). Per candidate and headline:
  per slate  the held-out gain on each slate (parameters fitted on the other slates, as ppb.py) against slate order:
             OLS slope per 10 slates +- its SE over slates
  per row    the same gain per player row, by games played at lock (<= 3, 4-6, 7+): per-slate bucket means, then
             mean +- SE over slates; and the row-level OLS slope on games played (capped at 10) with a cluster-robust
             SE by slate (CR0 sandwich)
Gains: positive = the candidate is better than the live baseline (rebuilt minutes x rebuilt ppm); for "rebuilt vs old
minutes", positive = rebuilt better.
  python3 ppb_trend.py > ppb_trend.out
"""
import os, math, statistics as S
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "ppb.py")).read()
ns = {"__file__": os.path.join(HERE, "ppb.py"), "__name__": "ppb"}
exec(src.split("base_h = {")[0], ns)
rows, SL, fit, mins, pts = ns["rows"], ns["SL"], ns["fit"], ns["mins"], ns["pts"]
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
P(ns["OUT"][0])
def ols(xs, ys):
    mx, my = S.mean(xs), S.mean(ys); sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return b, my - b * mx, mx, sxx
def slope_slates(vals):
    xs = [i for i, v in enumerate(vals) if v is not None]; ys = [v for v in vals if v is not None]
    b, a, mx, sxx = ols(xs, ys)
    res = [y - a - b * x for x, y in zip(xs, ys)]
    se = math.sqrt(sum(e * e for e in res) / (len(xs) - 2) / sxx)
    return "%+.3f ± %.3f per 10 slates (%d slates)" % (10 * b, 10 * se, len(xs))
def slope_rows_cluster(rr):
    xs = [min(10, r["gp"]) for r in rr]; ys = [r["g"] for r in rr]
    b, a, mx, sxx = ols(xs, ys)
    cl = defaultdict(float)
    for r, x, y in zip(rr, xs, ys): cl[r["slate"]] += (x - mx) * (y - a - b * x)
    se = math.sqrt(sum(v * v for v in cl.values())) / sxx
    return "%+.3f ± %.3f per game played (rows %d, %d slate clusters)" % (b, se, len(rr), len(cl))
def ms(v):
    v = [x for x in v if x is not None]
    if len(v) < 2: return "n/a (%d)" % len(v)
    return "%+.3f ± %.3f (%d), ahead %d" % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 0 for x in v))
CANDS = {"rebuilt vs old minutes": None, "switch": {"switch": True}, "level on ROTATION only": {"fitL": True, "rot_only": True},
         "pair (switch + level)": {"switch": True, "fitL": True}}
HEADS = {"rebuilt vs old minutes": ["rot_min"], "switch": ["rot_min", "rot_pts"], "level on ROTATION only": ["rot_pts"],
         "pair (switch + level)": ["stars_pts", "rot_pts", "rot_min"]}
def row_gain(r, c, head):
    if head == "rot_min":
        return abs(r["min"] - mins(r, {})) - abs(r["min"] - mins(r, c)) if r["band"] == "rot" else None
    band = "rot" if head == "rot_pts" else "stars"
    return abs(r["act"] - pts(r, {})) - abs(r["act"] - pts(r, c)) if r["band"] == band else None
B = [("<=3", lambda g: g <= 3), ("4-6", lambda g: 4 <= g <= 6), ("7+", lambda g: g >= 7)]
for cn, spec in CANDS.items():
    P("\n== %s" % cn)
    G = []
    for h in SL:
        te = [r for r in rows if r["slate"] == h]
        if spec is None:
            for r in te:
                if r["band"] == "rot": G.append(dict(r, g=abs(r["min"] - r["mo"]) - abs(r["min"] - r["mr"]), head="rot_min"))
            continue
        tr = [r for r in rows if r["slate"] != h]
        c = {"switch": spec.get("switch", False), "rot_only": spec.get("rot_only", False)}
        if spec.get("fitL"): c["L"] = fit(tr, c, "L")
        for head in HEADS[cn]:
            for r in te:
                g = row_gain(r, c, head)
                if g is not None: G.append(dict(r, g=g, head=head))
    for head in HEADS[cn]:
        rr = [r for r in G if r["head"] == head]
        per = [S.mean(r["g"] for r in rr if r["slate"] == s) if any(r["slate"] == s for r in rr) else None for s in SL]
        P("  %-9s per-slate gain %s | trend over slate order %s" % (head, ms(per), slope_slates(per)))
        first, last = per[:len(per) // 2], per[len(per) // 2:]
        P("            first half of slates %s | second half %s" % (ms(first), ms(last)))
        for lab, f in B:
            sb = defaultdict(list)
            for r in rr:
                if f(r["gp"]): sb[r["slate"]].append(r["g"])
            P("            games at lock %-4s %s (rows %d)" % (lab, ms([S.mean(v) for v in sb.values()]), sum(len(v) for v in sb.values())))
        P("            row-level slope on games played: %s" % slope_rows_cluster(rr))
# games-played mix by slate (how starved the early slates were)
P("\nshare of rotation rows with 7+ games at lock, by slate:")
P("  " + ", ".join("%s %.0f%%" % (s[5:10], 100 * S.mean(r["gp"] >= 7 for r in rows if r["slate"] == s and r["band"] == "rot")) for s in SL))
print("\n".join(OUT))
