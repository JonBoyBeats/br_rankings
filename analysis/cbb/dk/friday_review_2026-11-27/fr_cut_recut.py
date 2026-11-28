"""Addendum 2026-11-28 (S8 re-cut): fr_cut.py's keep-size gradient (kept lineups ranked by the board's sim value:
top 10/25/50/75% minus all kept, real finish pct) split by the unified contest type (scripts/dk_contest_type.py),
plus the variants' share of the top tenth (and top half) of the kept pool. Every build with board values, a
graded night record and standings on hand is used; the rest are listed as excluded with the reason."""
import json, glob, csv, os, sys, math, statistics as S, bisect
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); DK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.normpath(os.path.join(DK, "..", "..", "..", "scripts")))
import dk_eval as E, dk_contest_type as T
ev = defaultdict(dict)
for r in csv.DictReader(open(DK + "/eval.csv")): ev[r["draft_group"]][r["contest_id"]] = (r["contest"], int(float(r["entries"])))
Q = (0.1, 0.25, 0.5, 0.75)
res = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))     # type -> slate -> key -> [per contest]
allc = defaultdict(lambda: defaultdict(list))                          # original view: all 100+ contests
vshare = defaultdict(dict)                                             # slate -> {top10, top50}
types_of = defaultdict(set)
for f in sorted(glob.glob(DK + "/builds/*.json")):
    name = os.path.basename(f)[8:-5]; g = name.split("_")[1]; rec = os.path.join(DK, name + ".csv")
    if not os.path.exists(rec): print("excluded", name, "- no night record (not graded yet)"); continue
    pts = {r["dk_id"]: E.num(r.get("actual_dk")) for r in E.read(rec)}
    if not any(v is not None for v in pts.values()): print("excluded", name, "- night record has no actuals"); continue
    b = json.load(open(f)); kept = list(b.get("final") or [])
    vals = ((b.get("cut_state") or {}).get("board") or {}).get("values") or (b.get("idea_board") or {}).get("values")
    if not vals or len(vals) != len(kept): print("excluded", name, "- no board values aligned with the kept pool", len(vals or []), len(kept)); continue
    order = [k for _, k in sorted(zip([-v[0] if isinstance(v, list) else -v for v in vals], kept))]
    groups = b.get("groups") or {}
    tg = lambda i: b["tags"][i] if isinstance(b["tags"][i], list) else [b["tags"][i]]
    isvar = lambda i: any(str(t).startswith("variant of") or groups.get(t) == "Variants of the top" for t in tg(i))
    for q in (0.1, 0.5):
        top = order[:max(1, round(q * len(order)))]; vshare[name][q] = 100 * sum(map(isvar, top)) / len(top)
    vshare[name]["all"] = 100 * sum(map(isvar, kept)) / len(kept)
    ngot = 0
    for cid, (cname, n) in ev[g].items():
        sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(sf): continue
        field = sorted(e["points"] for e in E.standings_rows(open(sf, encoding="utf-8-sig"))[0]); N = len(field)
        if not N: continue
        pct = lambda L: 100 * bisect.bisect_right(field, sum((pts.get(str(i)) or 0) for i in L)) / N
        P = {i: pct(b["pool"][i]) for i in set(kept)}
        row = {1.0: S.mean(P[i] for i in kept)}
        for q in Q:
            k = order[:max(1, round(q * len(order)))]; row[q] = S.mean(P[i] for i in k)
        t = T.contest_type(cname, n); types_of[name].add(t); ngot += 1
        for k_, v in row.items():
            res[t][name][k_].append(v)
            if n >= 100: allc[name][k_].append(v)
    if not ngot: print("excluded", name, "- no standings on hand")
def tag(v, k, n):
    m, se = S.mean(v), S.stdev(v) / math.sqrt(len(v))
    if m > 2 * se and k > n / 2: return "PROVEN"
    if m > 0 and k / n >= 0.6: return "DIRECTIONAL"
    return "NOISE"
def report(label, by):
    print("\n==", label, "| slates:", ", ".join(sorted(by)))
    for q in Q:
        d = [S.mean(r[q]) - S.mean(r[1.0]) for r in by.values()]
        if len(d) < 2: print("  top %2d%% - all kept: %+.2f (1 slate)" % (q * 100, d[0])); continue
        k = sum(x > 0 for x in d)
        print("  top %2d%% - all kept: %+.2f ± %.2f (%d slates), positive on %d of %d, 2xSE %.2f -> %s"
              % (q * 100, S.mean(d), S.stdev(d) / math.sqrt(len(d)), len(d), k, len(d), 2 * S.stdev(d) / math.sqrt(len(d)), tag(d, k, len(d))))
    sh = [vshare[s][0.1] for s in by]; sa = [vshare[s]["all"] for s in by]
    print("  variants' share of the top tenth: %.1f%% (mean over slates; range %.1f-%.1f) vs %.1f%% of all kept" % (S.mean(sh), min(sh), max(sh), S.mean(sa)))
report("ALL 100+ entry contests (reproduces fr_cut.py)", allc)
for t in ("flagship", "main", "qualifier"):
    if res[t]: report(t.upper() + " (unified contest type)", res[t])
print("\nvariants' share of the TOP HALF of the kept pool, flagship nights since 11-24:")
fl = sorted(s for s in res["flagship"] if s[:10] >= "2026-11-24")
for s in fl: print("  %s top half %.1f%%, top tenth %.1f%%, all kept %.1f%%" % (s, vshare[s][0.5], vshare[s][0.1], vshare[s]["all"]))
if fl: print("  mean: top half %.1f%%, all kept %.1f%%" % (S.mean(vshare[s][0.5] for s in fl), S.mean(vshare[s]["all"] for s in fl)))
