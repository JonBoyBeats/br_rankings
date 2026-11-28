"""Section 5: the slates' best players (top 10 by actual DK points per $1k, top 10 by raw points), with what we had at lock."""
import ast, csv, glob, json, math, os, re, sys, statistics as S
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E, dk_proj_grade as PG
num = PG.num
DK = "/home/user/br_rankings/analysis/cbb/dk"; BRR = "/home/user/battle-royale-research"
W = {"obpr": 0.42, "mpg": 1.63, "ppm": 0.0, "x5": 4.45, "x2": 0.50}
def lit(v):
    if isinstance(v, (list, dict)): return v
    try: return ast.literal_eval(v) if v not in (None, "", "None") else None
    except Exception: return None
def pctl(sorted_, v):
    if v is None or not sorted_: return 0.5
    lo = sum(1 for x in sorted_ if x < v); hi = sum(1 for x in sorted_ if x <= v); return (lo + hi) / 2 / len(sorted_)
def band(s): return 0 if s < 5000 else 1 if s < 7000 else 2
def checks(P):
    rows = []
    for k, p in P.items():
        q = dict(p); q["id"] = k
        for f in ("salary", "min_avg", "gp", "obpr", "dk_avg", "min", "bpr_rank"): q[f] = num(p.get(f))
        q["last5"] = lit(p.get("last5")) or []; q["season_dk"] = lit(p.get("season_dk")) or []
        rows.append(q)
    def rate(r, x):
        sal = (r["salary"] or 0) / 1000; f = (lambda v: v >= x * sal) if x > 0 else (lambda v: v < -x * sal)
        l5 = [q[2] for q in r["last5"] if len(q) > 2 and q[2] is not None]; sea = [v for v in r["season_dk"] if v is not None]
        rl = sum(map(f, l5)) / len(l5) if l5 else None; rs = sum(map(f, sea)) / len(sea) if sea else None
        if rl is None and rs is None: return None
        if rs is None: return rl
        if rl is None: return rs
        return 0.5 * rl + 0.5 * rs
    get = {"obpr": lambda r: r["obpr"], "mpg": lambda r: r["min_avg"], "ppm": lambda r: r["dk_avg"] / r["min_avg"] if r["min_avg"] and r["dk_avg"] is not None else None,
           "x5": lambda r: rate(r, 5), "x2": lambda r: rate(r, -2)}
    rot = [r for r in rows if (r["min_avg"] or 0) >= 15 and (r["gp"] or 0) >= 3]
    pool = {k: sorted(v for v in map(g, rot) if v is not None) for k, g in get.items()}
    bpool = {k: [sorted(v for v in (g(r) for r in rot if band(r["salary"] or 0) == b) if v is not None) for b in range(3)] for k, g in get.items()}
    out = {}
    for r in rows:
        sc = {}
        for k, g in get.items():
            v = g(r); sc[k] = 0.5 if v is None else 0.75 * pctl(pool[k], v) + 0.25 * pctl(bpool[k][band(r["salary"] or 0)], v)
        if (r["bpr_rank"] or 99) <= 2: sc["obpr"] = max(sc["obpr"], 0.7)
        sc["x2"] = 1 - sc["x2"]
        s = sum(W[k] * sc[k] for k in W)
        st = r.get("status") or ""
        green = s >= 5.2 and (r["min_avg"] or 0) >= 20 and (r["min"] or 0) >= 20 and st not in ("Out", "Questionable", "Doubtful") and (r["gp"] or 0) > 0
        out[r["id"]] = (round(s, 2), green)
    return out
# field ownership by slate: entries-weighted mean over the slate's contests
fo = defaultdict(lambda: [0.0, 0.0])
for r in E.own_grade_rows():
    k = (str(r["draft_group"]), r["dk_id"]); fo[k][0] += r["a"] * r["n"]; fo[k][1] += r["n"]
ev = list(csv.DictReader(open(DK + "/eval.csv")))
contests = defaultdict(set)
for r in ev: contests[r["draft_group"]].add(r["contest_id"])
def ours(g, byname):
    cnt = defaultdict(int); n = 0
    for cid in contests[g]:
        f = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(f): continue
        for row in E.standings_rows(open(f, encoding="utf-8-sig"))[0]:
            if not row["name"].lower().startswith(E.USER): continue
            L = E.lineup_names(row["lineup"])
            if not L: continue
            n += 1
            for nm in L:
                if nm in byname: cnt[byname[nm]] += 1
    return cnt, n
def build(name):
    f = os.path.join(DK, "builds", "dk_bank_%s.json" % name)
    if not os.path.exists(f): return None
    b = json.load(open(f)); pool = b["pool"]; kept = sorted(set(b.get("final") or range(len(pool))))
    bank = defaultdict(float); kp = defaultdict(float)
    for L in pool:
        for i in L: bank[str(i)] += 1 / len(pool)
    for k in kept:
        for i in pool[k]: kp[str(i)] += 1 / len(kept)
    return bank, kp
rows_out = []
for name, rows in PG.slates():
    g = name.split("_")[1]
    pj = os.path.join(BRR, "data/dk/cbb/%s_proj.json" % name)
    ck = checks(json.load(open(pj))) if os.path.exists(pj) else {}
    G = [r for r in rows if num(r.get("actual_dk")) is not None and num(r.get("salary"))]
    for r in G: r["_v"] = num(r["actual_dk"]) / num(r["salary"]) * 1000
    tv = sorted(G, key=lambda r: -r["_v"])[:10]; tp = sorted(G, key=lambda r: -num(r["actual_dk"]))[:10]
    byname = {}
    for r in rows: byname.setdefault(r["name"], r["dk_id"])
    oc, on = ours(g, byname)
    bd = build(name)
    for r in {id(x): x for x in tv + tp}.values():
        k = r["dk_id"]; f = fo.get((g, k)); c = ck.get(k)
        mp, fp = num(r.get("min_proj")), num(r.get("fp_dk"))
        rows_out.append({"slate": name, "name": r["name"], "team": r["team"], "sal": int(num(r["salary"])), "act": num(r["actual_dk"]), "val": r["_v"],
                         "topv": r in tv, "topp": r in tp, "fp": fp, "min_proj": mp, "min": num(r.get("min")),
                         "ppm_proj": fp / mp if fp and mp else None, "ppm": num(r["actual_dk"]) / num(r["min"]) if num(r.get("min")) else None,
                         "own_raw": num(r.get("own_raw")) if num(r.get("own_raw")) is not None else num(r.get("own")), "own_real": f[0] / f[1] if f and f[1] else None,
                         "score": c[0] if c else None, "green": c[1] if c else None, "status": r.get("status"),
                         "bank": bd[0].get(k, 0.0) if bd else None, "kept": bd[1].get(k, 0.0) if bd else None,
                         "ours": oc.get(k, 0) / on if on else None, "our_n": on, "val_rank_proj": None})
    # our projected value rank on the slate
    live = sorted([x for x in G if num(x.get("fp_dk"))], key=lambda x: -num(x["fp_dk"]) / num(x["salary"]))
    vr = {x["dk_id"]: i + 1 for i, x in enumerate(live)}
    for o in rows_out:
        if o["slate"] == name:
            o["val_rank_proj"] = vr.get(next((x["dk_id"] for x in G if x["name"] == o["name"]), None))
json.dump(rows_out, open("fr_best.json", "w"))
V = [o for o in rows_out if o["topv"]]; Pp = [o for o in rows_out if o["topp"]]
def summ(lab, X):
    m = lambda f: S.mean(o[f] for o in X if o[f] is not None)
    print("%s n=%d | salary $%.0f | actual %.1f vs ours %.1f (act-ours %+.1f) | min %.1f vs proj %.1f | ppm %.2f vs proj %.2f | own raw %.1f, field real %.1f | checks score %.2f, green %d/%d | our proj value rank median %d | bank share %.3f kept %.3f (n with build %d) | in our entries share %.3f (slates with entries %d), held by >=1 of our lineups %d/%d"
          % (lab, len(X), m("sal"), m("act"), m("fp"), m("act") - m("fp"), m("min"), m("min_proj"), m("ppm"), m("ppm_proj"), m("own_raw"), m("own_real"), m("score"),
             sum(1 for o in X if o["green"]), sum(1 for o in X if o["green"] is not None), S.median(o["val_rank_proj"] for o in X if o["val_rank_proj"]),
             m("bank"), m("kept"), sum(1 for o in X if o["bank"] is not None), m("ours"), sum(1 for o in X if o["ours"] is not None),
             sum(1 for o in X if o["ours"]), sum(1 for o in X if o["ours"] is not None)))
summ("TOP-10 VALUE", V); summ("TOP-10 POINTS", Pp)
# what separated them: compare top-value with the rest of the rotation (fp_dk>=10) at lock
print("\nbase rates, all players fp_dk>=10 with a score:")
allr = []
for name, rows in PG.slates():
    g = name.split("_")[1]; pj = os.path.join(BRR, "data/dk/cbb/%s_proj.json" % name)
    ck = checks(json.load(open(pj))) if os.path.exists(pj) else {}
    for r in PG.graded(rows):
        if num(r["fp_dk"]) >= 10:
            c = ck.get(r["dk_id"]); f = fo.get((g, r["dk_id"]))
            v = num(r["actual_dk"]) / num(r["salary"]) * 1000
            allr.append((v, c[1] if c else None, num(r["fp_dk"]) / num(r["salary"]) * 1000, num(r["salary"]), f[0] / f[1] if f and f[1] else None, name))
gr = [x for x in allr if x[1] is not None]
print("greens: %d, mean actual value %.2f; non-greens %d, mean %.2f" % (sum(1 for x in gr if x[1]), S.mean(x[0] for x in gr if x[1]), sum(1 for x in gr if not x[1]), S.mean(x[0] for x in gr if not x[1])))
print("5x hit rate greens %.3f, non-greens %.3f" % (S.mean(x[0] >= 5 for x in gr if x[1]), S.mean(x[0] >= 5 for x in gr if not x[1])))
# salary tier of top-value
for lo, hi in ((0, 5000), (5000, 7000), (7000, 99999)):
    print("salary %d-%d: share of top-10 value %.2f; share of the fp>=10 pool %.2f" % (lo, hi, S.mean(lo <= o["sal"] < hi for o in V), S.mean(lo <= x[3] < hi for x in allr)))
print("\nper-slate top-value list (name, sal, act, value, ours fp, min proj/actual, own raw/real, score, green, bank, kept, ours):")
for o in sorted(V, key=lambda o: (o["slate"], -o["val"])):
    f = lambda v, d=1: "-" if v is None else ("%." + str(d) + "f") % v
    print(o["slate"], "|", o["name"], o["sal"], f(o["act"]), f(o["val"], 2), f(o["fp"]), f(o["min_proj"]) + "/" + f(o["min"], 0), f(o["own_raw"]) + "/" + f(o["own_real"]), f(o["score"], 2), o["green"], f(o["bank"], 3), f(o["kept"], 3), f(o["ours"], 2))
