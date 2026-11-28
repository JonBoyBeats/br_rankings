"""A2: does disagreement with the outside sources (Gajewski, RotoWire) predict a bigger miss of our lock projection?
Pre-registered in conf_jitter_2026-11-28.md. Reads the PRIVATE per-player source tables from battle-royale-research and
prints aggregates only (no player rows). Actuals from ESPN box scores (cbb_daily.box, the night records' scoring).
  python3 a2.py --brr ../../../../../battle-royale-research > a2.out"""
import argparse, csv, json, math, os, statistics as St, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); import cbb_daily as CD
ap = argparse.ArgumentParser(); ap.add_argument("--brr", required=True); a = ap.parse_args()
num = lambda x: float(x) if x not in (None, "") else None
src = defaultdict(lambda: defaultdict(dict))          # slate -> dk_id -> source -> row
for s in ("gajewski", "rotowire"):
    f = os.path.join(a.brr, "data", "dk", "cbb", "sources", s + "_table.csv")
    if os.path.exists(f):
        for r in csv.DictReader(open(f)):
            if r.get("in_lock") == "1":
                src[r["slate"]][r["dk_id"]][s] = r
box = {}
def boxes(evs):
    for e in evs:
        if e and e not in box:
            b = CD.box(e); box[e] = b[0] if b else None
def pct(vals):
    s = sorted(vals)
    return lambda v: (sum(1 for x in s if x < v) + sum(1 for x in s if x <= v)) / 2 / len(s)
B = ("agree", "mild", "strong"); out = {}; who = defaultdict(lambda: [0, 0, 0, 0])
for slate in sorted(src):
    R = src[slate]; anyrow = lambda d: next(iter(d.values()))
    boxes({anyrow(d)["event"] for d in R.values()})
    rows = []
    for k, d in R.items():
        r0 = anyrow(d); ev = box.get(r0["event"])
        if ev is None or r0["status"] == "Out":
            continue
        om, of = num(r0["min"]), num(r0["fp_dk"])
        if not om or om < 10 or of is None:
            continue
        S = [(num(x["src_min"]), num(x["src_fp"])) for x in d.values() if num(x["src_min"]) and num(x["src_min"]) >= 10 and num(x["src_fp"]) is not None]
        if not S:
            continue
        a_ = ev.get(str(r0["espn"])) or {}; amin, adk = a_.get("min", 0.0), a_.get("actual_dk", 0.0)
        dm = max(abs(om - m) for m, _ in S); dp = max(abs(of / om - fp / m) for m, fp in S)
        near = min(S, key=lambda x: abs(x[1] - of))    # the source closest to us on points
        rows.append(dict(dm=dm, dp=dp, ab=abs(adk - of), mn=abs(amin - om), sab=abs(adk - near[1]), smn=abs(amin - near[0])))
    if not rows:
        continue
    fm, fp_ = pct([r["dm"] for r in rows]), pct([r["dp"] for r in rows])
    for r in rows:
        D = max(fm(r["dm"]), fp_(r["dp"])); r["bin"] = "agree" if D < 0.5 else "mild" if D < 0.8 else "strong"
        if r["bin"] != "agree":
            w = who[r["bin"]]; w[0] += r["sab"] < r["ab"]; w[1] += r["smn"] < r["mn"]; w[2] += 1
    out[slate] = {b: {"n": sum(1 for r in rows if r["bin"] == b), "ab": St.mean([r["ab"] for r in rows if r["bin"] == b] or [float("nan")]),
                      "mn": St.mean([r["mn"] for r in rows if r["bin"] == b] or [float("nan")])} for b in B}
    print("%-18s n=%3d | " % (slate, len(rows)) + " | ".join("%-6s n=%3d |miss| %5.2f |min miss| %5.2f" % (b, out[slate][b]["n"], out[slate][b]["ab"], out[slate][b]["mn"]) for b in B))
n_sl = len(out); n_pl = sum(sum(v[b]["n"] for b in B) for v in out.values())
print("\nslates %d, players %d (not Out, our min >= 10, a source with 10+ min, game final)" % (n_sl, n_pl))
for m, lab in (("ab", "|actual DK - our proj|"), ("mn", "|actual min - our min|")):
    g = [v["strong"][m] - v["agree"][m] for v in out.values()]
    s = St.stdev(g) / math.sqrt(len(g)) if len(g) > 1 else float("nan")
    print("%-24s strong - agree: %+.2f%s over %d slates, positive on %d" % (lab, St.mean(g), (" ± %.2f" % s) if len(g) > 1 else " (one slate, no SE)", len(g), sum(1 for x in g if x > 0)))
    if len(g) > 1 and St.mean(g) > 0:
        sd = St.stdev(g); print("%24s slates needed for gain > 2xSE at this spread: %d" % ("", math.ceil((2 * sd / St.mean(g)) ** 2)))
for b in ("mild", "strong"):
    w = who[b]
    if w[2]:
        print("who is right, %-6s (n=%d): the source closer than us on points %.0f%%, on minutes %.0f%%" % (b, w[2], 100 * w[0] / w[2], 100 * w[1] / w[2]))
