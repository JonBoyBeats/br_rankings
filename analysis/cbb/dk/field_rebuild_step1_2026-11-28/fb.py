"""Field rebuild step 1 (2026-11-28): real field vs the sim field on the same contests, by contest type.
Run from the repo root: python3 analysis/cbb/dk/field_rebuild_step1_2026-11-28/fb.py --mirror ../br-adp-mirror
Writes fb_rows.json (one row per contest x side) and prints the by-type summary (fb.out)."""
import argparse, csv, json, os, random, statistics as S, sys
from collections import Counter, defaultdict
from itertools import combinations
sys.path.insert(0, "scripts")
import dk_eval as E

ap = argparse.ArgumentParser(); ap.add_argument("--mirror", default="../br-adp-mirror"); a = ap.parse_args()
OUT = os.path.dirname(os.path.abspath(__file__))
mirror = E.Mirror(a.mirror)
ctype = {}
for r in csv.DictReader(open(os.path.join(E.DK, "field_lineups.csv"))):
    ctype[r["contest_id"]] = r["contest_type"]
graded = {}
for r in E.read(E.EVAL):
    graded.setdefault((r["date"], str(r["draft_group"])), {})[r["contest_id"]] = r["contest"]

def metrics(L, info, rown, pown, pj):
    n = len(L)
    own = [sum(rown.get(i, 0) for i in x) for x in L]
    po = [sum(pown.get(i, 0) for i in x) for x in L]
    q = lambda v, p: sorted(v)[int(p * (len(v) - 1))]
    team = lambda i: info[i].get("team"); game = lambda i: info[i].get("game")
    t2 = t3 = g3 = 0
    for x in L:
        tc = Counter(team(i) for i in x); gc = Counter(game(i) for i in x)
        t2 += max(tc.values()) >= 2; t3 += max(tc.values()) >= 3
        # game stack: 3+ from one game with both of its teams in it
        g3 += any(c >= 3 and len({team(i) for i in x if game(i) == g}) == 2 for g, c in gc.items())
    cnt = Counter(L)
    pairs, trips = Counter(), Counter()
    for x in L:
        pairs.update(combinations(x, 2)); trips.update(combinations(x, 3))
    return {"n": n,
            "own_sum": round(S.mean(own), 1), "own_p10": round(q(own, .1)), "own_p50": round(q(own, .5)), "own_p90": round(q(own, .9)),
            "own_sd": round(S.pstdev(own), 1), "pown_sum": round(S.mean(po), 1),
            "chalk10": round(S.mean(sum(rown.get(i, 0) >= 10 for i in x) for x in L), 2),
            "chalk20": round(S.mean(sum(rown.get(i, 0) >= 20 for i in x) for x in L), 2),
            "chalk30": round(S.mean(sum(rown.get(i, 0) >= 30 for i in x) for x in L), 2),
            "punt_min": round(100 * S.mean(any((E.num(info[i].get("min")) or 0) < 15 for i in x) for x in L), 1),
            "punt_sal": round(100 * S.mean(any(int(info[i]["salary"]) < 4000 for i in x) for x in L), 1),
            "sal_left": round(S.mean(50000 - sum(int(info[i]["salary"]) for i in x) for x in L)),
            "team2": round(100 * t2 / n, 1), "team3": round(100 * t3 / n, 1), "game3": round(100 * g3 / n, 1),
            "dup": round(100 * sum(c for c in cnt.values() if c > 1) / n, 1),
            "top_pair": round(100 * pairs.most_common(1)[0][1] / n, 1), "top5_pairs": round(100 * S.mean(c for _, c in pairs.most_common(5)) / n, 1),
            "top_trip": round(100 * trips.most_common(1)[0][1] / n, 1), "top5_trips": round(100 * S.mean(c for _, c in trips.most_common(5)) / n, 1),
            "proj": round(S.mean(sum(pj.get(i, 0) for i in x) for x in L), 1)}

rows = []
for (date, g), contests in sorted(graded.items()):
    slate = None
    for _, sha in reversed(mirror.versions("dk_cbb_morning.json", E.iso(date + "T00:00:00Z") - E.dt.timedelta(days=1), E.iso(date + "T00:00:00Z") + E.dt.timedelta(days=2))):
        slate = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
        if slate: break
    fd = E.at_lock(mirror, "dk_cbb_field.json", E.iso(slate["start"]), g) if slate else None
    F = ((fd or {}).get("slates") or {}).get(g) or {}
    if not slate or not F.get("field"):
        print("skip", date, g, "no sim field at lock"); continue
    info = slate["players"]
    names = defaultdict(list)
    for k, r in info.items(): names[r["name"]].append(k)
    byname = {nm: v[0] for nm, v in names.items() if len(v) == 1}
    sim = [tuple(sorted(str(i) for i in L)) for L in F["field"]]
    pj = {k: E.num(r.get("fp_gate")) if E.num(r.get("fp_gate")) is not None else (E.num(r.get("fp_dk")) or 0) for k, r in info.items()}
    pown = {str(k): v for k, v in (F.get("own") or {}).items()}
    for cid, cname in sorted(contests.items()):
        path = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(path): continue
        L, U, total = E.real_field(path, byname)
        L = [x for x, u in zip(L, U) if u != E.USER]          # our entries out
        if len(L) < 20: continue
        rown = Counter(i for x in L for i in x); rown = {k: 100 * v / len(L) for k, v in rown.items()}
        n = min(len(L), len(sim), 1000)
        rnd = random.Random(int(cid) % 100003)
        Ls = rnd.sample(L, n) if len(L) > n else L
        Ss = rnd.sample(sim, n) if len(sim) > n else sim
        t = ctype.get(cid) or "main"
        base = {"date": date, "draft_group": g, "contest_id": cid, "contest": cname, "type": t, "real_total": len(L)}
        rows.append(dict(base, side="real", **metrics(Ls, info, rown, pown, pj)))
        rows.append(dict(base, side="sim", **metrics(Ss, info, rown, pown, pj)))
json.dump(rows, open(os.path.join(OUT, "fb_rows.json"), "w"), indent=0)

# summary by type: mean over contests, and sim - real per slate (contests averaged within a slate) with SE over slates
keys = ["own_sum", "own_p10", "own_p50", "own_p90", "own_sd", "pown_sum", "chalk10", "chalk20", "chalk30", "punt_min", "punt_sal",
        "sal_left", "team2", "team3", "game3", "dup", "top_pair", "top5_pairs", "top_trip", "top5_trips", "proj"]
def se(v): return S.stdev(v) / len(v) ** .5 if len(v) > 1 else float("nan")
for t in ("flagship", "main", "qualifier", "all"):
    R = [r for r in rows if t == "all" or r["type"] == t]
    cids = sorted({r["contest_id"] for r in R}); slates = sorted({(r["date"], r["draft_group"]) for r in R})
    print("\n== %s: %d contests, %d slates" % (t, len(cids), len(slates)))
    print("%-11s %8s %8s %16s %s" % ("metric", "real", "sim", "sim-real ±SE", "sim>real slates"))
    for k in keys:
        rv = S.mean(r[k] for r in R if r["side"] == "real"); sv = S.mean(r[k] for r in R if r["side"] == "sim")
        d = []
        for s in slates:
            rr = [r[k] for r in R if (r["date"], r["draft_group"]) == s and r["side"] == "real"]
            ss = [r[k] for r in R if (r["date"], r["draft_group"]) == s and r["side"] == "sim"]
            d.append(S.mean(ss) - S.mean(rr))
        print("%-11s %8.2f %8.2f %+8.2f ± %5.2f   %d of %d" % (k, rv, sv, S.mean(d), se(d), sum(x > 0 for x in d), len(d)))
