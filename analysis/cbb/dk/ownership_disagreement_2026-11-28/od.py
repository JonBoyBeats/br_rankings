"""The ownership disagreement test (2026-11-28, operator-approved; analysis only).

When our projected ownership and the field's real ownership disagree about a player, who was right about the result?

Rows: one per slate x player. ours = our projected ownership at lock (own_eval's own_proj, the page's live number;
own_raw beside it), real = the field's real ownership, both entries-weighted over the slate's graded contests of 100+
entries. d = real - ours. proj = fp_dk (our projected DK points at lock), act = actual_dk, value = act / salary x 1000,
x5 = act >= 5 x salary/1000. The analysis set is players with max(ours, real) >= 5 and a real score.
The slate is the unit: every figure is a per-slate statistic, then mean +- SE over slates (and a 2,000-draw bootstrap
over slates for the 90% band where shown).

  python3 od.py        (paths assume sibling checkouts under /home/user)
"""
import ast, csv, json, math, os, random, statistics as S, sys
from collections import defaultdict, Counter
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E, dk_proj_grade as PG
num = E.num
BRR = "/home/user/battle-royale-research"
MIN_N, MIN_OWN, BIG = 100, 5.0, 10.0
rng = random.Random(5)
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
def lit(v):
    if isinstance(v, (list, dict)): return v
    try: return ast.literal_eval(v) if v not in (None, "", "None") else None
    except Exception: return None
def ms(v):
    v = [x for x in v if x is not None and not (isinstance(x, float) and math.isnan(x))]
    if not v: return "n/a"
    if len(v) == 1: return "%+.3f (1)" % v[0]
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(2000))
    return "%+.3f ± %.3f (%d) [%+.3f, %+.3f], +%d" % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), bs[100], bs[1900], sum(x > 0 for x in v))
def corr(x, y):
    if len(x) < 4 or len(set(x)) < 2 or len(set(y)) < 2: return None
    mx, my = S.mean(x), S.mean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2
        i = j + 1
    return r
def spear(x, y): return corr(rank(x), rank(y))

# ---------- data
own = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])          # (g, dk_id) -> [sum ours*n, sum real*n, sum raw*n, sum n]
for r in E.own_grade_rows():
    if r["n"] < MIN_N: continue
    k = (str(r["draft_group"]), r["dk_id"]); o = own[k]
    o[0] += r["p"] * r["n"]; o[1] += r["a"] * r["n"]; o[2] += (r["raw"] if r["raw"] is not None else r["p"]) * r["n"]; o[3] += r["n"]
rows = []
slates = PG.slates()
for name, recs in slates:
    g = name.split("_")[1]
    pj = os.path.join(BRR, "data/dk/cbb/%s_proj.json" % name)
    L = json.load(open(pj)) if os.path.exists(pj) else {}
    for r in recs:
        o = own.get((g, r["dk_id"]))
        if not o or not o[3]: continue
        fp, act, sal = num(r.get("fp_dk")), num(r.get("actual_dk")), num(r.get("salary"))
        if fp is None or act is None or not sal: continue
        ours, real, raw = o[0] / o[3], o[1] / o[3], o[2] / o[3]
        p = L.get(r["dk_id"], {})
        rows.append({"slate": name, "g": g, "id": r["dk_id"], "name": r["name"], "team": r["team"], "pos": (r.get("position") or "?").split("/")[0],
                     "sal": sal, "fp": fp, "act": act, "res": act - fp, "value": act / sal * 1000, "pval": fp / sal * 1000, "x5": int(act >= 5 * sal / 1000),
                     "ours": ours, "real": real, "raw": raw, "d": real - ours, "min_proj": num(r.get("min_proj")), "min": num(r.get("min")),
                     "status": r.get("status") or p.get("status") or "", "L": p})
SL = sorted({r["slate"] for r in rows})
A = [r for r in rows if max(r["ours"], r["real"]) >= MIN_OWN]
P("rows (slate x player with a 100+ entry real ownership): %d; analysis set (max(ours, real) >= %d%%): %d on %d slates" % (len(rows), MIN_OWN, len(A), len(SL)))
def per(rs, f):
    d = defaultdict(list)
    for r in rs: d[r["slate"]].append(r)
    return [f(v) for s, v in sorted(d.items()) if v]

# ---------- 1a buckets
P("\n## 1a. Buckets of d = real - ours (per-slate means, then mean ± SE over slates [90% bootstrap], slates positive)")
B = [("field 10+ above us", lambda r: r["d"] >= BIG), ("within 10", lambda r: abs(r["d"]) < BIG), ("field 10+ below us", lambda r: r["d"] <= -BIG)]
for lab, f in B:
    rs = [r for r in A if f(r)]
    P("%-20s n=%4d | act - proj %s | value %s | 5x %s | mean d %+.1f" % (lab, len(rs), ms(per(rs, lambda v: S.mean(x["res"] for x in v))),
      ms(per(rs, lambda v: S.mean(x["value"] for x in v))), ms(per(rs, lambda v: S.mean(x["x5"] for x in v))), S.mean(r["d"] for r in rs)))
# paired within slate: loved - within, faded - within
for lab, f in (("loved - within", B[0][1]), ("faded - within", B[2][1])):
    dd = []; dv = []; d5 = []
    for s in SL:
        a = [r for r in A if r["slate"] == s and f(r)]; w = [r for r in A if r["slate"] == s and B[1][1](r)]
        if a and w:
            dd.append(S.mean(x["res"] for x in a) - S.mean(x["res"] for x in w)); dv.append(S.mean(x["value"] for x in a) - S.mean(x["value"] for x in w)); d5.append(S.mean(x["x5"] for x in a) - S.mean(x["x5"] for x in w))
    P("paired %-15s act-proj %s | value %s | 5x %s" % (lab, ms(dd), ms(dv), ms(d5)))
P("\ncontinuous (per-slate Pearson r, then over slates):")
for lab, key in (("d vs act - proj", "res"), ("d vs value", "value"), ("d vs 5x", "x5")):
    P("  %-18s %s" % (lab, ms(per(A, lambda v: corr([x["d"] for x in v], [x[key] for x in v])))))
P("  slope of act - proj on d (DK pts per 10 points of d): %s" % ms(per(A, lambda v: (lambda b: b * 10 if b is not None else None)(
    (lambda xs, ys: (sum((a - S.mean(xs)) * (c - S.mean(ys)) for a, c in zip(xs, ys)) / sum((a - S.mean(xs)) ** 2 for a in xs)) if len(set(xs)) > 1 else None)([x["d"] for x in v], [x["res"] for x in v])))))
P("  same with own_raw (d_raw = real - raw) vs act - proj: %s" % ms(per(A, lambda v: corr([x["real"] - x["raw"] for x in v], [x["res"] for x in v]))))

# ---------- 1b splits
P("\n## 1b. Splits: per-slate r(d, act - proj); and loved / faded mean act - proj")
splits = [("salary < $5k", lambda r: r["sal"] < 5000), ("salary $5-7k", lambda r: 5000 <= r["sal"] < 7000), ("salary $7k+", lambda r: r["sal"] >= 7000),
          ("proj < 10", lambda r: r["fp"] < 10), ("rotation 10-25", lambda r: 10 <= r["fp"] < 25), ("stars 25+", lambda r: r["fp"] >= 25),
          ("G", lambda r: r["pos"] == "G"), ("F", lambda r: r["pos"] in ("F", "C"))]
for lab, f in splits:
    rs = [r for r in A if f(r)]
    lov = [r for r in rs if r["d"] >= BIG]; fad = [r for r in rs if r["d"] <= -BIG]
    P("%-15s n=%4d | r %s | loved n=%3d act-proj %s | faded n=%3d act-proj %s" % (lab, len(rs), ms(per(rs, lambda v: corr([x["d"] for x in v], [x["res"] for x in v]))),
      len(lov), ms(per(lov, lambda v: S.mean(x["res"] for x in v))), len(fad), ms(per(fad, lambda v: S.mean(x["res"] for x in v)))))

# ---------- 1c leave one slate out: fit proj' = proj + b*d on the other slates, score MAE on the held-out
P("\n## 1c. Leave one slate out: does the d -> result relation carry to a new slate? (ex post: real own is known only after lock)")
gains = []; signs = []
for h in SL:
    tr = [r for r in A if r["slate"] != h]; te = [r for r in A if r["slate"] == h]
    mx, my = S.mean(r["d"] for r in tr), S.mean(r["res"] for r in tr)
    b = sum((r["d"] - mx) * (r["res"] - my) for r in tr) / sum((r["d"] - mx) ** 2 for r in tr)
    gains.append(S.mean(abs(r["res"]) for r in te) - S.mean(abs(r["res"] - b * r["d"]) for r in te)); signs.append(b)
    hb = corr([r["d"] for r in te], [r["res"] for r in te]); signs[-1] = (b, hb)
P("fitted b (pts per point of d) range %.3f to %.3f; held-out slate's own r has the fitted sign on %d of %d" % (min(x[0] for x in signs), max(x[0] for x in signs), sum(1 for b, hb in signs if hb is not None and (hb > 0) == (b > 0)), len(signs)))
P("held-out MAE gain (proj -> proj + b d), analysis set: %s" % ms(gains))

# ---------- 1d who ranks outcomes better
P("\n## 1d. Per-slate Spearman with actual value (analysis set): ours = projected value fp/sal; field = real own; blend = mean of ranks (weight fit LOSO)")
def blend_rank(v, w):
    a, b = rank([x["pval"] for x in v]), rank([x["real"] for x in v]); return [w * x + (1 - w) * y for x, y in zip(a, b)]
res = {"ours": [], "field": [], "our own": [], "blend": [], "w": []}
for h in SL:
    v = [r for r in A if r["slate"] == h]
    if len(v) < 8: continue
    y = [x["value"] for x in v]
    res["ours"].append(spear([x["pval"] for x in v], y)); res["field"].append(spear([x["real"] for x in v], y)); res["our own"].append(spear([x["ours"] for x in v], y))
    def score(w, sl):
        out = []
        for s in sl:
            vv = [r for r in A if r["slate"] == s]
            if len(vv) >= 8: out.append(corr(blend_rank(vv, w), rank([x["value"] for x in vv])))
        return S.mean([o for o in out if o is not None])
    w = max([i / 10 for i in range(11)], key=lambda w: score(w, [s for s in SL if s != h]))
    res["w"].append(w); res["blend"].append(corr(blend_rank(v, w), rank(y)))
for k in ("ours", "field", "our own", "blend"): P("%-8s %s" % (k, ms(res[k])))
P("field - ours per slate: %s; blend - ours: %s; LOSO blend weight on ours: %s" % (ms([b - a for a, b in zip(res["ours"], res["field"])]), ms([b - a for a, b in zip(res["ours"], res["blend"])]), sorted(Counter(res["w"]).items())))
# same, rotation+ only (fp >= 10)
for lab, f in (("fp >= 10", lambda r: r["fp"] >= 10), ("whole slate (every player with a real own, incl. < 5%)", lambda r: True)):
    o, fl = [], []
    for h in SL:
        v = [r for r in (rows if "whole" in lab else A) if r["slate"] == h and f(r)]
        if len(v) < 8: continue
        o.append(spear([x["pval"] for x in v], [x["value"] for x in v])); fl.append(spear([x["real"] for x in v], [x["value"] for x in v]))
    P("  %s: ours %s | field %s | field - ours %s" % (lab, ms(o), ms(fl), ms([b - a for a, b in zip(o, fl)])))

json.dump([{k: v for k, v in r.items() if k != "L"} for r in rows], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "od_rows.json"), "w"))
print("\n".join(OUT))
