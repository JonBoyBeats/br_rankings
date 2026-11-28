"""Section 9: entered (the fill's portfolios) vs random fills, per contest and contest type; softened fills."""
import json, glob, os, sys, math, random, re, statistics as S
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E
M = E.Mirror("/home/user/br-adp-mirror")
def ctype(name, size):
    """The one definition (scripts/dk_contest_type.py, the DK page's profile; 2026-11-28). This script reported
    "qualifier/small"; it passes its own size argument, which the page reads as the lobby size."""
    import dk_contest_type
    t = dk_contest_type.contest_type(name, size)
    return "qualifier/small" if t == "qualifier" else t
banks = {}
for f in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
    b = json.load(open(f)); g = str(b["draft_group"])
    if g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or ""): banks[g] = b
rng = random.Random(7); SETS = 1000
rows = []
for g, b in sorted(banks.items(), key=lambda kv: kv[1]["day"]):
    pf = {c: ks for c, ks in (b.get("portfolios") or {}).items() if ks}
    files = {c: os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c) for c in pf}
    if not pf or not all(os.path.exists(p) for p in files.values()): continue
    pool = b["pool"]; kept = sorted(set(b.get("final") or range(len(pool))))
    vals = ((b.get("cut_state") or {}).get("board") or {}).get("values")
    order = [k for _, k in sorted(zip([-(v[0] if isinstance(v, list) else v) for v in vals], b["final"]))] if vals and len(vals) == len(b["final"]) else None
    recown = None
    for cid, ks in pf.items():
        entries, players = E.standings(files[cid])
        rec, slate, _ = E.slate_for(M, cid)
        if not rec: break
        contest = next(c for c in slate["contests"] if str(c["id"]) == cid)
        table, n = E.pay_table(contest.get("payouts")), len(entries)
        field = sorted((e["points"] for e in entries), reverse=True)
        pts = E.night_points(rec, players)
        tot = lambda L: sum(pts.get(str(i)) or 0 for i in L)
        def pay(k):
            v = tot(pool[k]); return table.get(E.placed(v, field), 0), 100 * (n - (E.placed(v, field) - 1)) / n
        P = {k: pay(k) for k in set(kept) | set(ks)}
        ent_d = sum(P[k][0] for k in ks); ent_p = S.mean(P[k][1] for k in ks)
        def rand(idx):
            ds = []; ps = []
            for _ in range(SETS):
                pick = rng.sample(idx, len(ks)); ds.append(sum(P[k][0] for k in pick)); ps.append(S.mean(P[k][1] for k in pick))
            return S.mean(ds), S.median(ds), sum(d < ent_d for d in ds) / SETS + 0.5 * sum(d == ent_d for d in ds) / SETS, S.mean(ps)
        r = {"g": g, "day": b["day"], "cid": cid, "type": ctype(contest.get("name", ""), n), "n": n, "k": len(ks), "fee": contest.get("entry_fee") or 0,
             "ent_d": ent_d, "ent_p": ent_p, "rand": rand(kept)}
        if order:
            for q in (0.1, 0.25, 0.5):
                idx = order[:max(len(ks), round(q * len(order)))]; r["top%d" % (q * 100)] = rand(idx)
        rows.append(r)
json.dump(rows, open("fr_fill.json", "w"))
def ms(v): return "%+.2f ± %.2f (%d)" % (S.mean(v), S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan"), len(v))
print("contests:", len(rows), "slates:", len({r['g'] for r in rows}))
for t in ("all", "flagship", "main", "qualifier/small"):
    R = [r for r in rows if t == "all" or r["type"] == t]
    if not R: continue
    by = defaultdict(list)
    for r in R: by[r["g"]].append(r)
    d = [sum(x["ent_d"] - x["rand"][0] for x in v) for v in by.values()]
    dm = [sum(x["ent_d"] - x["rand"][1] for x in v) for v in by.values()]
    pc = [S.mean(x["rand"][2] for x in v) for v in by.values()]
    fp = [S.mean(x["ent_p"] - x["rand"][3] for x in v) for v in by.values()]
    print("%-16s contests %3d | entered - random mean $ %s | entered - random median $ %s | entered's percentile among random fills %.0f | finish pct entered - random %s"
          % (t, len(R), ms(d), ms(dm), 100 * S.mean(pc), ms(fp)))
    for k in ("top10", "top25", "top50"):
        RR = [r for r in R if k in r]
        if not RR: continue
        b2 = defaultdict(list)
        for r in RR: b2[r["g"]].append(r)
        dd = [sum(x[k][0] - x["ent_d"] for x in v) for v in b2.values()]; dr = [sum(x[k][0] - x["rand"][0] for x in v) for v in b2.values()]
        dp = [S.mean(x[k][3] - x["ent_p"] for x in v) for v in b2.values()]
        print("    softened: random from the board's %-6s - entered $ %s; - random kept $ %s; finish pct - entered %s" % (k, ms(dd), ms(dr), ms(dp)))
