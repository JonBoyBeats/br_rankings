import json, statistics as S, random, math
from collections import defaultdict
R = json.load(open(__import__("os").environ.get("ROWS","mf_rows.json")))
T = ("flagship", "main", "qualifier/small")
def roi(rs): f = sum(r["fees"] for r in rs); return (sum(r["back"] for r in rs) - f) / f if f else float("nan")
print("== Results and variance (our real entries, standings-replayed; reconciles to eval.csv) ==")
for t in T:
    rs = [r for r in R if r["type"] == t]
    pays = sorted((p for r in rs for p in r["pays"]), reverse=True)
    fees = sum(r["fees"] for r in rs); back = sum(pays)
    slates = sorted({r["g"] for r in rs})
    cashes = sum(p > 0 for p in pays)
    # bootstrap over slates
    rng = random.Random(3); by = defaultdict(list)
    for r in rs: by[r["g"]].append(r)
    bs = []
    for _ in range(4000):
        pick = [x for g in rng.choices(slates, k=len(slates)) for x in by[g]]
        bs.append(roi(pick))
    bs.sort()
    print(f"{t:16s} contests {len(rs):2d} slates {len(slates):2d} entries {len(pays):4d} fees ${fees:7.2f} back ${back:7.2f} ROI {roi(rs):+.1%} | "
          f"cash rate {cashes/len(pays):.1%} | top cash ${pays[0]:.0f}, 2nd ${pays[1]:.0f} | ROI w/o top1 {(back-pays[0]-fees)/fees:+.1%} w/o top2 {(back-pays[0]-pays[1]-fees)/fees:+.1%} | "
          f"bootstrap 90% [{bs[200]:+.0%}, {bs[3800]:+.0%}] P(ROI>0) {sum(b>0 for b in bs)/4000:.2f}")
    # per-slate ROI sign
    ps = [roi(v) for v in by.values()]
    print(f"{'':16s} slates in profit {sum(p>0 for p in ps)} of {len(ps)}; median slate ROI {S.median(ps):+.0%}; mean finish pct {S.mean(p for r in rs for p in r['pcts']):.1f}; fee range ${min(r['fee'] for r in rs)}–${max(r['fee'] for r in rs)}; entries/contest {S.mean(r['k'] for r in rs):.1f}")
print("\n== Contest structure (per contest, mean) ==")
for t in T:
    rs = [r for r in R if r["type"] == t]
    print(f"{t:16s} field size median {S.median(r['n'] for r in rs):.0f} (range {min(r['n'] for r in rs)}–{max(r['n'] for r in rs)}) | paid share {S.mean(r['paid_places']/r['n'] for r in rs):.1%} | "
          f"1st prize / pool {S.mean(r['top_prize']/r['prize'] for r in rs if r['prize']):.1%} | pool/fees {S.mean(r['prize']/(r['fee']*r['n']) for r in rs if r['prize']):.2f} | names: {sorted({r['name'] for r in rs})[:4]}")
print("\n== Construction: us vs the field (per lineup; field = 400 sampled other entries per contest) ==")
keys = ["own_sum", "sub10", "chalk15", "sal_left", "team_max", "game_max", "stack_2_1", "stack_3_2", "proj"]
for t in T:
    rs = [r for r in R if r["type"] == t]
    us = [s for r in rs for s in r["my_st"]]; fd = [s for r in rs for s in r["field_st"]]
    print(t, f"(us n={len(us)}, field n={len(fd)})")
    for k in keys:
        # per-contest difference averaged over slates
        by = defaultdict(list)
        for r in rs:
            if r["my_st"] and r["field_st"]:
                by[r["g"]].append(S.mean(s[k] for s in r["my_st"]) - S.mean(s[k] for s in r["field_st"]))
        d = [S.mean(v) for v in by.values()]
        se = S.stdev(d)/math.sqrt(len(d)) if len(d) > 1 else float("nan")
        print(f"   {k:10s} us {S.mean(s[k] for s in us):8.2f} field {S.mean(s[k] for s in fd):8.2f} | us-field per slate {S.mean(d):+.2f} ± {se:.2f} ({sum(x>0 for x in d)}/{len(d)} +)")
    dups = [r["dup_field"] for r in rs if r["dup_field"] is not None]
    po = [r["pair_overlap"] for r in rs if r["pair_overlap"] is not None]
    me = [r["max_expo"] for r in rs if r["max_expo"] is not None and r["k"] > 1]
    print(f"   our lineups duplicated by another entry {S.mean(dups):.1%} | pairwise shared players among our entries {S.mean(po) if po else float('nan'):.2f}/8 | max player exposure {S.mean(me) if me else float('nan'):.0%} | distinct/entries {sum(r['distinct'] for r in rs)}/{sum(r['k'] for r in rs)}")
print("\n== Pick method era: before vs from 11-24 (joint fill for flagships from 11-24) ==")
for t in T:
    for era, f in (("pre 11-24", lambda r: r["date"] < "2026-11-24"), ("11-24 on", lambda r: r["date"] >= "2026-11-24")):
        rs = [r for r in R if r["type"] == t and f(r)]
        if not rs: continue
        pays = sorted((p for r in rs for p in r["pays"]), reverse=True)
        print(f"{t:16s} {era:9s} contests {len(rs):2d} slates {len({r['g'] for r in rs}):2d} entries {len(pays):3d} ROI {roi(rs):+.0%} w/o top1 {(sum(pays)-pays[0]-sum(r['fees'] for r in rs))/sum(r['fees'] for r in rs):+.0%} finish pct {S.mean(p for r in rs for p in r['pcts']):.1f}")
