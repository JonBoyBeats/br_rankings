"""Middle band and tighter cores (2026-11-28, analysis only; HELD). Friday review section 5 decisions.

For each saved build with board values, a lock-time slate and simulated field on the mirror, and graded standings:
  1. quintiles: how well a lineup's PROJECTED own_sum (sum of our lock-time own, the night record's own column) tracks
     its REAL own_sum (sum of the contest's real ownership, from the lineups in the standings), per contest: the field's
     entries and our kept pool; Spearman, the share in the same quintile, and within one.
  2. variants of the kept pool, each filled by the page's pick (mb.js; fixed field at lock):
     base (today's fill model); a projected own_sum BAND (drop kept lineups below the Xth / above the Yth percentile of
     the kept pool's projected own_sum) on a grid, X and Y fitted held out by slate; tighter CORES (max core exposure
     30% / 50% for today's 15%; only the top 3 / 5 / 8 cores, a core = the lineup's 3 highest salaries, ranked by the
     best board value among its lineups); GREEN cores (cores with 2+ green players, green = the checks green flag
     recomputed at lock as fr_best.py does it); and combinations with the 20/80 band.
     Flagship contests are also filled the held proposal's way (top-half random by board value, 300 draws) from each set.
  Scored on the real standings: finish pct and $ per lineup per contest, per slate, by contest type
  (scripts/dk_contest_type.py), against the base fill and against the entered lineups (today's real fill).

  python3 mb.py [--sims 500] [--grade-only]
"""
import argparse, ast, bisect, csv, glob, json, math, os, random, re, statistics as S, subprocess, sys, tempfile
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dk_eval as E, dk_contest_type as CT
MIRROR = os.environ.get("MIRROR") or os.path.join(os.path.dirname(ROOT), "br-adp-mirror")
BRR = os.environ.get("BRR") or os.path.join(os.path.dirname(ROOT), "battle-royale-research")
num = E.num
BAND_X = [0, 10, 20, 30]; BAND_Y = [70, 80, 90, 100]


def nights(mirror):
    out = []
    for bf in sorted(glob.glob(os.path.join(E.DK, "builds", "dk_bank_*.json"))):
        B = json.load(open(bf)); g = str(B.get("draft_group"))
        slate = start = None
        for cid in (B.get("portfolios") or {}):
            _, slate, start = E.slate_for(mirror, cid)
            if slate and str(slate["draft_group_id"]) == g: break
            slate = None
        if not slate: continue
        fd = E.at_lock(mirror, "dk_cbb_field.json", start, g)
        Fd = ((fd or {}).get("slates") or {}).get(g)
        if not Fd or not Fd.get("field"): continue
        out.append((bf, start, {"slate": slate, "field": {"field": Fd["field"], "own": Fd.get("own") or {}}, "z": fd.get("z")}))
    return out


def proj_at_lock(day, g, start):
    rel = "data/dk/cbb/%s_%s_proj.json" % (day, g)
    sha = subprocess.run(["git", "-C", BRR, "log", "-1", "--format=%H", "--before=" + start.strftime("%Y-%m-%dT%H:%M:%SZ"), "--", rel],
                         capture_output=True, text=True).stdout.strip()
    if not sha: return None
    r = subprocess.run(["git", "-C", BRR, "show", "%s:%s" % (sha, rel)], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def greens_at_lock(P):
    """The checks green flag at lock, from fr_best.py's checks() (the page's checks score and green rule), loaded without
    running the rest of that script."""
    src = open(os.path.join(HERE, "..", "friday_review_2026-11-27", "fr_best.py")).read()
    src = src[src.index("W = {"):src.index("# field ownership by slate")]
    ns = {"num": num, "ast": ast}
    exec(src, ns)
    return {k for k, (s, g) in ns["checks"](P).items() if g}


def build_variants(B, rec):
    kept = B.get("final") or list(range(len(B["pool"])))
    vals = ((B.get("cut_state") or {}).get("board") or {}).get("values")
    if not vals or len(vals) != len(kept): return None, None
    val = [v[0] if isinstance(v, list) else v for v in vals]
    own = {r["dk_id"]: num(r.get("own")) or 0.0 for r in rec}
    sal = {r["dk_id"]: num(r.get("salary")) or 0 for r in rec}
    L = [[str(i) for i in B["pool"][k]] for k in kept]
    osum = [sum(own.get(i, 0.0) for i in l) for l in L]
    srt = sorted(osum)
    pct = [100.0 * (bisect.bisect_left(srt, o) + bisect.bisect_right(srt, o)) / 2 / len(srt) for o in osum]
    core = [tuple(sorted(sorted(l, key=lambda i: -sal.get(i, 0))[:3])) for l in L]
    return {"kept": kept, "val": val, "osum": osum, "pct": pct, "core": core, "L": L}, own


def subsets(V, greens):
    n = len(V["L"]); allk = list(range(n))
    band = lambda x, y: [k for k in allk if x <= V["pct"][k] <= y]
    best = defaultdict(lambda: -1e9)
    for k in allk: best[V["core"][k]] = max(best[V["core"][k]], V["val"][k])
    ranked = sorted(best, key=lambda c: -best[c])
    topk = lambda K, base: [k for k in base if V["core"][k] in set(ranked[:K])] if K else base
    green2 = [k for k in allk if sum(1 for i in V["core"][k] if i in greens) >= 2]
    rankedG = sorted({V["core"][k] for k in green2}, key=lambda c: -best[c])
    topkG = lambda K: [k for k in green2 if V["core"][k] in set(rankedG[:K])]
    out = [{"name": "base", "set": allk, "maxCore": None}]
    for x in BAND_X:
        for y in BAND_Y:
            if (x, y) != (0, 100): out.append({"name": "band%d_%d" % (x, y), "set": band(x, y), "maxCore": None})
    out += [{"name": "core30", "set": allk, "maxCore": 30}, {"name": "core50", "set": allk, "maxCore": 50},
            {"name": "top3cores", "set": topk(3, allk), "maxCore": 100}, {"name": "top5cores", "set": topk(5, allk), "maxCore": 100},
            {"name": "top8cores", "set": topk(8, allk), "maxCore": 100},
            {"name": "green2", "set": green2, "maxCore": None}, {"name": "green2_core30", "set": green2, "maxCore": 30},
            {"name": "green2_top5", "set": topkG(5), "maxCore": 100}]
    b = band(20, 80); bs = set(b)
    out += [{"name": "band20_80+core30", "set": b, "maxCore": 30}, {"name": "band20_80+top5cores", "set": [k for k in topk(5, b)], "maxCore": 100},
            {"name": "band20_80+green2", "set": [k for k in green2 if k in bs], "maxCore": None},
            {"name": "band20_80+green2_top5", "set": [k for k in topkG(5) if k in bs], "maxCore": 100}]
    return out


def run(a):
    M = E.Mirror(MIRROR); res = {}
    for bf, start, night in nights(M):
        B = json.load(open(bf)); name = "%s_%s" % (B["day"], B["draft_group"])
        rec = E.read(os.path.join(E.DK, name + ".csv"))
        if not rec or not any(num(r.get("actual_dk")) is not None for r in rec): print("  %s: not graded" % name); continue
        V, own = build_variants(B, rec)
        if not V: print("  %s: no board values" % name); continue
        P = proj_at_lock(B["day"], B["draft_group"], start)
        greens = greens_at_lock(P) if P else set()
        vs = subsets(V, greens)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t: json.dump(night, t); nf = t.name
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t: json.dump({"sims": a.sims, "variants": vs}, t); pf = t.name
        r = subprocess.run(["node", os.path.join(HERE, "mb.js"), nf, bf, pf], capture_output=True, text=True)
        os.unlink(nf); os.unlink(pf)
        if r.returncode: print("  %s: %s" % (name, r.stderr.strip()[-400:])); continue
        o = json.loads(r.stdout)
        o["sizes"] = {v["name"]: len(v["set"]) for v in vs}; o["greens"] = sorted(greens); o["proj_at_lock"] = bool(P)
        o["payouts"] = {str(c["id"]): c.get("payouts") for c in night["slate"]["contests"]}
        res[name] = o
        print("  %s: %d contests, kept %d, greens %d (proj at lock: %s), green2 lineups %d, top5cores %d" % (
            name, len(o["contests"]), o["kept"], len(greens), bool(P), o["sizes"]["green2"], o["sizes"]["top5cores"]), flush=True)
    json.dump(res, open(os.path.join(HERE, "picks.json"), "w"))
    return res


def quintiles():
    """Projected vs real own_sum, per contest with complete lineups, field entries and our kept pool."""
    P = lambda *x: OUT.append(" ".join(str(y) for y in x))
    def ranks(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
            for t in range(i, j + 1): r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    def sp(a, b):
        ra, rb = ranks(a), ranks(b); return S.correlation(ra, rb) if len(set(ra)) > 1 and len(set(rb)) > 1 else None
    def qagree(a, b):
        n = len(a); ra, rb = ranks(a), ranks(b)
        qa = [min(4, int(5 * x / n)) for x in ra]; qb = [min(4, int(5 * x / n)) for x in rb]
        return sum(x == y for x, y in zip(qa, qb)) / n, sum(abs(x - y) <= 1 for x, y in zip(qa, qb)) / n, qa, qb
    recs = {}
    for f in glob.glob(os.path.join(E.DK, "????-??-??_*.csv")):
        rows = E.read(f)
        if rows: recs[(rows[0]["date"], rows[0]["draft_group"])] = rows
    fl = defaultdict(list)
    for r in csv.DictReader(open(os.path.join(E.DK, "field_lineups.csv"))): fl[r["contest_id"]].append(r)
    res = defaultdict(list); trans = defaultdict(lambda: [[0] * 5 for _ in range(5)])
    for cid, rs in fl.items():
        rec = recs.get((rs[0]["date"], rs[0]["draft_group"]))
        sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not rec or not os.path.exists(sf): continue
        own = {r["dk_id"]: num(r.get("own")) or 0.0 for r in rec}
        name_id = {r["name"]: r["dk_id"] for r in rec}
        _, players = E.standings(sf)
        real = {name_id[n]: v[0] or 0.0 for n, v in players.items() if n in name_id}
        Ls = [r["lineup"].split() for r in rs if r["lineup"] and "?" not in r["lineup"]]
        if len(Ls) < 50: continue
        a = [sum(own.get(i, 0.0) for i in L) for L in Ls]; b = [sum(real.get(i, 0.0) for i in L) for L in Ls]
        rho = sp(a, b); same, adj, qa, qb = qagree(a, b)
        t = CT.contest_type(rs[0]["contest"], int(rs[0]["size"]))
        res[t].append((rs[0]["draft_group"], rho, same, adj, len(Ls)))
        for x, y in zip(qa, qb): trans[t][x][y] += 1
    P("## Quintile tracking: projected own_sum (lock-time own) vs real own_sum, field entries, per contest (50+ complete lineups)")
    allr = [x for v in res.values() for x in v]
    for t, v in [("all", allr)] + sorted(res.items()):
        by = defaultdict(list)
        for g, rho, same, adj, n in v: by[g].append((rho, same, adj))
        sl = [(S.mean(x[0] for x in xs if x[0] is not None), S.mean(x[1] for x in xs), S.mean(x[2] for x in xs)) for xs in by.values()]
        se = lambda k: S.stdev([s[k] for s in sl]) / math.sqrt(len(sl)) if len(sl) > 1 else float("nan")
        P("  %-10s contests %3d, slates %2d | Spearman %.2f ± %.2f | same quintile %.0f%% ± %.0f | within one %.0f%% ± %.0f (chance: 20%% / 52%%)" % (
            t, len(v), len(sl), S.mean(s[0] for s in sl), se(0), 100 * S.mean(s[1] for s in sl), 100 * se(1), 100 * S.mean(s[2] for s in sl), 100 * se(2)))
    T = [[sum(trans[t][i][j] for t in trans) for j in range(5)] for i in range(5)]
    P("  all field entries: projected quintile (rows, 1 = least owned) -> real quintile (columns), row %:")
    for i in range(5):
        P("     Q%d  %s" % (i + 1, "  ".join("%3.0f" % (100 * T[i][j] / max(1, sum(T[i]))) for j in range(5))))


def grade(res):
    PR = lambda *x: OUT.append(" ".join(str(y) for y in x))
    rng = random.Random(11)
    rows = []          # per (slate, contest): type, n, per variant {pct, pay}, entered {pct, pay}, flagship top-half random per variant
    for name, o in res.items():
        recs = E.read(os.path.join(E.DK, name + ".csv"))
        pts = {r["dk_id"]: num(r.get("actual_dk")) or 0.0 for r in recs}
        B = json.load(open(os.path.join(E.DK, "builds", "dk_bank_%s.json" % name)))
        kept = B.get("final") or list(range(len(B["pool"])))
        vals = [v[0] if isinstance(v, list) else v for v in B["cut_state"]["board"]["values"]]
        V, _ = build_variants(B, recs); greens = set(o["greens"]); vs = {v["name"]: v["set"] for v in subsets(V, greens)}
        for c in o["contests"]:
            sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c["id"])
            if not os.path.exists(sf): continue
            entries, players = E.standings(sf)
            fdesc = sorted((e["points"] for e in entries), reverse=True); Nn = len(fdesc)
            T = E.pay_table(o["payouts"].get(c["id"]))
            def score(L):
                v = sum(pts.get(str(i), 0.0) for i in L); pl = E.placed(v, fdesc)
                return 100 * (Nn - (pl - 1)) / Nn, T.get(pl, 0)
            def agg(Ls):
                s = [score(L) for L in Ls]; return {"pct": S.mean(x[0] for x in s), "pay": S.mean(x[1] for x in s)}
            t = CT.contest_type(c["name"], c["size"])
            row = {"slate": name, "cid": c["id"], "type": t, "n": c["n"], "fee": c["fee"] or 0}
            for v, Ls in c["sets"].items():
                if Ls: row[v] = agg(Ls)
            ent = [B["pool"][k] for k in B["portfolios"][c["id"]]]
            row["entered"] = agg(ent)
            if t == "flagship":       # the held proposal: top-half random by board value, from each set
                for v in ("base", "band20_80", "core30", "top5cores", "green2", "band20_80+green2"):
                    st = vs.get(v) or []
                    if len(st) < 2 * c["n"]: continue
                    half = sorted(st, key=lambda k: -vals[k])[:max(c["n"], len(st) // 2)]
                    sc = {k: score([str(i) for i in V["L"][k]]) for k in half}
                    d = [rng.sample(half, c["n"]) for _ in range(300)]
                    row["rand_" + v] = {"pct": S.mean(S.mean(sc[k][0] for k in p) for p in d), "pay": S.mean(S.mean(sc[k][1] for k in p) for p in d)}
            rows.append(row)
    json.dump(rows, open(os.path.join(HERE, "graded.json"), "w"))
    def per_slate(R, v, ref, m):
        by = defaultdict(list)
        for r in R:
            if v in r and ref in r: by[r["slate"]].append(r[v][m] - r[ref][m])
        return {s: S.mean(x) for s, x in by.items()}
    def ms(d, digits=2):
        v = list(d.values()) if isinstance(d, dict) else d
        if len(v) < 2: return "n/a (%d)" % len(v)
        return ("%+." + str(digits) + "f ± %." + str(digits) + "f (%d), ahead %d") % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 1e-12 for x in v))
    types = ("all", "flagship", "main", "qualifier")
    sel = lambda t: [r for r in rows if t == "all" or r["type"] == t]
    PR("\n## Graded: %d contests on %d slates (%s)" % (len(rows), len({r["slate"] for r in rows}),
       ", ".join("%s %d" % (t, sum(1 for r in rows if r["type"] == t)) for t in types[1:])))
    PR("   replay check, base (the page's pick on the kept pool, fixed field) - entered (the lineups really entered):")
    for t in types:
        PR("     %-9s finish pct %s | $ per lineup %s" % (t, ms(per_slate(sel(t), "base", "entered", "pct")), ms(per_slate(sel(t), "base", "entered", "pay"), 3)))
    # 1. the band: every grid point vs base, and X/Y fitted held out by slate (on all contests' finish pct)
    PR("\n## 1. Projected own_sum band (kept pool percentiles X-Y), page's pick, vs base (no band)")
    grid = ["band%d_%d" % (x, y) for x in BAND_X for y in BAND_Y if (x, y) != (0, 100)]
    for t in types:
        PR("  -- %s" % t)
        for v in grid:
            PR("     %-12s finish pct %s | $ %s" % (v, ms(per_slate(sel(t), v, "base", "pct")), ms(per_slate(sel(t), v, "base", "pay"), 3)))
    slates = sorted({r["slate"] for r in rows})
    for t in types:
        for m in ("pct", "pay"):
            ho = {}; picks = []
            for s in slates:
                tr = [r for r in sel(t) if r["slate"] != s]; te = [r for r in sel(t) if r["slate"] == s]
                if not te: continue
                score_ = {v: S.mean(per_slate(tr, v, "base", m).values() or [-1e9]) for v in grid + ["base"] if per_slate(tr, v, "base", m) or v == "base"}
                score_["base"] = 0.0
                b = max(score_, key=score_.get); picks.append(b)
                d = per_slate(te, b, "base", m) if b != "base" else {s: 0.0}
                if s in d: ho[s] = d[s]
            PR("  held-out band (%s, %s): %s; chosen %s" % (t, m, ms(ho, 2 if m == "pct" else 3), dict((p, picks.count(p)) for p in set(picks))))
    # 2. cores
    PR("\n## 2. Tighter cores (page's pick), vs base; variance = SD of per-slate result, worst slate")
    cv = ["core30", "core50", "top3cores", "top5cores", "top8cores", "green2", "green2_core30", "green2_top5"]
    for t in types:
        PR("  -- %s" % t)
        for v in ["base"] + cv:
            ab = per_slate(sel(t), v, "entered", "pct"); ap = per_slate(sel(t), v, "entered", "pay")
            dv = per_slate(sel(t), v, "base", "pct"); dp = per_slate(sel(t), v, "base", "pay")
            lvl = defaultdict(list)
            for r in sel(t):
                if v in r: lvl[r["slate"]].append(r[v]["pct"])
            L = [S.mean(x) for x in lvl.values()]
            PR("     %-14s vs base: pct %s, $ %s | slate finish pct mean %.1f, SD %.1f, worst %.1f (%d slates)" % (
                v, ms(dv) if v != "base" else "-", ms(dp, 3) if v != "base" else "-", S.mean(L) if L else float("nan"),
                S.stdev(L) if len(L) > 1 else float("nan"), min(L) if L else float("nan"), len(L)))
    # 3. combinations
    PR("\n## 3. Combinations with the 20/80 band, vs base")
    for t in types:
        PR("  -- %s" % t)
        for v in ("band20_80", "band20_80+core30", "band20_80+top5cores", "band20_80+green2", "band20_80+green2_top5"):
            PR("     %-22s pct %s | $ %s" % (v, ms(per_slate(sel(t), v, "base", "pct")), ms(per_slate(sel(t), v, "base", "pay"), 3)))
    PR("  -- flagship, the held proposal (top-half random by board value) from each set, vs the page's pick on the kept pool (base) and vs entered")
    F = sel("flagship")
    for v in ("base", "band20_80", "core30", "top5cores", "green2", "band20_80+green2"):
        k = "rand_" + v
        PR("     top-half random from %-17s vs base: pct %s, $ %s | vs entered: pct %s, $ %s" % (
            v, ms(per_slate(F, k, "base", "pct")), ms(per_slate(F, k, "base", "pay"), 3), ms(per_slate(F, k, "entered", "pct")), ms(per_slate(F, k, "entered", "pay"), 3)))
        if v != "base":
            PR("        ... vs top-half random from the whole kept pool: pct %s, $ %s" % (ms(per_slate(F, k, "rand_base", "pct")), ms(per_slate(F, k, "rand_base", "pay"), 3)))


OUT = []
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sims", type=int, default=500); ap.add_argument("--grade-only", action="store_true")
    a = ap.parse_args()
    res = json.load(open(os.path.join(HERE, "picks.json"))) if a.grade_only else run(a)
    quintiles(); grade(res)
    open(os.path.join(HERE, "mb.out"), "w").write("\n".join(OUT) + "\n"); print("\n".join(OUT))
