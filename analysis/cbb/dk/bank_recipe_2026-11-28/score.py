"""Score the Section 7 replays (recipe.js outputs) on the real standings.

Per slate (draft group), every graded contest of 100+ entries with standings:
  finish percentile of a lineup = 100 x (entries - real entries scoring more) / entries (the Lab's measure); top 10% hit.
1b  GREENS rule (600) vs plain L0 U0 (600): mean finish percentile of each draw, paired by contest, slate = mean over
    contests; by contest type (scripts/dk_contest_type.py).
2   each recipe: the bank's and the kept pool's mean finish percentile over the slate's graded contests (kept - bank,
    the pool row), the kept pool's diversity (distinct 3-player cores by salary, as DKSim.cores; the most-used player's
    share), and the fill: the picked lineups in each contest the build entered that has standings, placed among the
    real entries (ours left out, ties split as DraftKings pays them): finish percentile and net $ (payout - fee) per
    entry, by contest type. Each recipe against (a) today's Draw-the-9 mix, paired by slate; mean ± SE over slates.
  python3 score.py --out DIR > score.out"""
import argparse, csv, glob, json, math, os, statistics as St, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dk_eval as E
import dk_contest_type as CT

ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
evals = defaultdict(dict)
for r in E.read(E.EVAL):
    evals[r["draft_group"]][r["contest_id"]] = (r["contest"], int(float(r["entries"] or 0)))


def se(v):
    return St.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")


def line(lab, v):
    if not v:
        return "%-44s  (none)" % lab
    return "%-44s %+7.2f ± %5.2f  over %2d slates, ahead on %2d" % (lab, St.mean(v), se(v), len(v), sum(1 for x in v if x > 0))


def pay_of(payouts):
    t = {}
    for a_, b_, v in payouts or []:
        for i in range(int(a_), int(b_) + 1):
            t[i] = v
    return t


R1 = defaultdict(list)            # 1b: type -> slate diffs
R1top = []
POOL = defaultdict(lambda: defaultdict(dict))     # recipe -> slate -> metrics
FILL = defaultdict(lambda: defaultdict(dict))     # recipe -> slate -> {type: (pct list, net list, fee)}
rows_1b = []
for f in sorted(glob.glob(os.path.join(a.out, "*.json"))):
    O = json.load(open(f))
    day, g = O["date"], O["g"]
    rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (day, g)))
    if not rec:
        continue
    sal = {r["dk_id"]: float(r["salary"] or 0) for r in rec}
    graded = []
    for cid, (cname, n) in evals.get(g, {}).items():
        p = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(p):
            continue
        ents, players = E.standings(p)
        if len(ents) < E.LAB_MIN_ENTRIES:
            continue
        pts = E.night_points(rec, players)
        field = sorted((e["points"] for e in ents), reverse=True)
        others = sorted((e["points"] for e in ents if not e["name"].lower().startswith(E.USER)), reverse=True)
        graded.append((cid, cname, len(ents), pts, field, others))

    def score_set(L, c):
        cid, cname, n, pts, field, _ = c
        out = []
        for ids in L:
            s = sum(pts.get(str(i)) or 0 for i in ids)
            p = E.placed(s, field)
            out.append((100.0 * (n - (p - 1)) / n, p <= math.ceil(0.1 * n)))
        return out
    # 1b
    Rc = O["recipes"]
    if "greens600" in Rc and "plain600" in Rc and graded:
        per = defaultdict(list)
        tops = []
        for c in graded:
            t = score_set(Rc["greens600"]["bank"], c)
            q = score_set(Rc["plain600"]["bank"], c)
            d = St.mean(x[0] for x in t) - St.mean(x[0] for x in q)
            per[CT.contest_type(c[1], c[2])].append(d)
            per["all"].append(d)
            tops.append(St.mean(x[1] for x in t) - St.mean(x[1] for x in q))
            rows_1b.append((day, g, c[1][:40], c[2], O["greens"], O["green_n"], round(St.mean(x[0] for x in t), 2), round(St.mean(x[0] for x in q), 2), round(d, 2)))
        for k, v in per.items():
            R1[k].append(St.mean(v))
        R1top.append(St.mean(tops))
    # 2
    cs = {c["id"]: c for c in O.get("contests", [])}
    for name, r in Rc.items():
        if name.endswith("600") or "kept" not in r or not graded:
            continue
        bank = r["bank"]
        kept = [bank[i] for i in r["kept"]]
        bp = St.mean(x[0] for c in graded for x in score_set(bank, c))
        kp = St.mean(x[0] for c in graded for x in score_set(kept, c))
        cores = {",".join(sorted(sorted(L, key=lambda i: (-sal.get(str(i), 0), str(i)))[:3])) for L in kept}
        cnt = defaultdict(int)
        for L in kept:
            for i in L:
                cnt[i] += 1
        POOL[name][(day, g)] = {"bank": bp, "kept": kp, "kmb": kp - bp, "cores": len(cores), "core_share": len(cores) / len(kept), "maxexpo": 100.0 * max(cnt.values()) / len(kept), "kept_n": len(kept)}
        byt = defaultdict(lambda: [[], [], 0.0])
        allsets = []
        for cid, ix in r["picks"].items():
            c = next((x for x in graded if x[0] == cid), None)
            if c is None or cid not in cs:
                continue
            L = [kept[i] for i in ix]
            allsets += L
            cc = cs[cid]
            pay = pay_of(cc.get("payouts"))
            _, cname, n, pts, field, others = c
            ours = [sum(pts.get(str(i)) or 0 for i in ids) for ids in L]
            t = CT.contest_type(cname, cc.get("size") or n)
            for x in ours:
                above = sum(1 for p in others if p > x) + sum(1 for y in ours if y > x)
                tied = sum(1 for p in others if p == x) + sum(1 for y in ours if y == x) - 1
                w = sum(pay.get(k, 0) for k in range(above + 1, above + 2 + tied)) / (tied + 1)
                pl = E.placed(x, field)
                for k in (t, "all"):
                    byt[k][0].append(100.0 * (n - (pl - 1)) / n)
                    byt[k][1].append(w - (cc.get("fee") or 0))
                    byt[k][2] += cc.get("fee") or 0
        if allsets:
            cnt2 = defaultdict(int)
            for L in allsets:
                for i in L:
                    cnt2[i] += 1
            POOL[name][(day, g)]["entry_maxexpo"] = 100.0 * max(cnt2.values()) / len(allsets)
            POOL[name][(day, g)]["entry_cores"] = len({",".join(sorted(sorted(L, key=lambda i: (-sal.get(str(i), 0), str(i)))[:3])) for L in allsets})
            POOL[name][(day, g)]["entries"] = len(allsets)
        FILL[name][(day, g)] = {k: (St.mean(v[0]), sum(v[1]) / len(v[1]), sum(v[1]), v[2]) for k, v in byt.items() if v[0]}

print("1b. GREENS rule (at least n of the slate's retroactive greens; n 3 with 5+ greens, else 2) vs the plain L0 U0 draw, 600 each,")
print("    real finish percentile, GREENS - plain, paired by contest (100+ entries), slate = mean over its contests")
for k in ("all", "flagship", "main", "qualifier"):
    print(line("  " + k, R1.get(k, [])))
print(line("  top-10%% rate (points of rate x 100)", [100 * x for x in R1top]))
print("\n  per contest: date, draft group, contest, entries, greens, n, GREENS pct, plain pct, diff")
for x in rows_1b:
    print("   ", *x)

print("\n2. Bank recipes (1,500 drawn each, merit cut to 30%, the build's contests filled), each against (a) today's Draw-the-9 mix")
names = [n for n in ("d9", "plain", "greencore", "jitter", "light") if n in POOL]
print("\n  The pool (all graded 100+ contests, every lineup): mean finish percentile")
print("  %-10s %6s %6s %7s %6s %6s %7s %6s" % ("recipe", "bank", "kept", "k-b", "cores", "/kept", "maxexp", "slates"))
for n in names:
    P = POOL[n]
    m = lambda k: St.mean(v[k] for v in P.values())
    print("  %-10s %6.2f %6.2f %+7.2f %6.0f %6.2f %6.1f%% %6d" % (n, m("bank"), m("kept"), m("kmb"), m("cores"), m("core_share"), m("maxexpo"), len(P)))
for n in names[1:]:
    ks = [k for k in POOL[n] if k in POOL["d9"]]
    print(line("  kept pct, %s - d9" % n, [POOL[n][k]["kept"] - POOL["d9"][k]["kept"] for k in ks]))
    print(line("  kept - bank, %s - d9" % n, [POOL[n][k]["kmb"] - POOL["d9"][k]["kmb"] for k in ks]))
    print(line("  distinct kept cores, %s - d9" % n, [POOL[n][k]["cores"] - POOL["d9"][k]["cores"] for k in ks]))
print("\n  The fill (entered contests with standings): finish pct and net $ per entry, entries-weighted within a slate")
for t in ("all", "flagship", "main", "qualifier"):
    print("  -- %s" % t)
    for n in names:
        F = FILL[n]
        v = [F[k][t] for k in F if t in F[k]]
        if not v:
            continue
        print("  %-10s pct %6.2f  net/entry %+7.2f  net %+8.2f on fees %7.2f  (%d slates)" % (n, St.mean(x[0] for x in v), St.mean(x[1] for x in v), sum(x[2] for x in v), sum(x[3] for x in v), len(v)))
    for n in names[1:]:
        ks = [k for k in FILL[n] if t in FILL[n][k] and k in FILL["d9"] and t in FILL["d9"][k]]
        print(line("    pct, %s - d9" % n, [FILL[n][k][t][0] - FILL["d9"][k][t][0] for k in ks]))
        print(line("    net $/entry, %s - d9" % n, [FILL[n][k][t][1] - FILL["d9"][k][t][1] for k in ks]))
print("\n  The entries' spread: max player exposure across the night's entries, distinct cores among them")
for n in names:
    v = [x for x in POOL[n].values() if "entries" in x]
    print("  %-10s max exposure %5.1f%%  distinct entry cores %5.1f of %5.1f entries" % (n, St.mean(x["entry_maxexpo"] for x in v), St.mean(x["entry_cores"] for x in v), St.mean(x["entries"] for x in v)))
json.dump({"pool": {n: {"%s_%s" % k: v for k, v in POOL[n].items()} for n in names},
           "fill": {n: {"%s_%s" % k: v for k, v in FILL[n].items()} for n in names}}, open(os.path.join(HERE, "score_%s.json" % os.path.basename(os.path.normpath(a.out))), "w"), indent=0)
