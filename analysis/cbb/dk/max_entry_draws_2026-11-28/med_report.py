"""Report for med.py (med_rows.json). ROI = payouts / fees - 1, fees = entry fee x lineups filled (mean per draw; the caps can leave a seat empty)."""
import json, os, math, statistics as S
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, "med_rows.json")))
D = len(next(iter(rows[0]["rules"].values()))["pays"])
NE = lambda q: q["N"] - q["short"]       # seats actually filled (mean per draw): fees are paid on those
def ms(v): return "%+.1f%% ± %.1f" % (100 * S.mean(v), 100 * S.stdev(v) / math.sqrt(len(v))) if len(v) > 1 else "%+.1f%%" % (100 * v[0])
def pctl(v, q): v = sorted(v); return v[min(len(v) - 1, int(q * len(v)))]
print("draws per contest:", D, "| contests:", len(rows), "| slates:", len({r['g'] for r in rows}))
print("pool smaller than max entries (cap binds):", [(r["day"], r["cid"]) for r in rows if r["binds"]] or "none")
for typ in ("flagship", "main", "qualifier"):
    for key in ("plain_act", "plain_max", "top50_act", "top50_max"):
        RR = [r for r in rows if r["type"] == typ and key in r["rules"]]
        if RR:
            seats = sum(r["rules"][key]["N"] for r in RR); sh = sum(r["rules"][key]["short"] for r in RR)
            print("seats left unfilled under the caps, %-9s %-9s: %.1f of %d per draw (%.1f%%)" % (typ, key, sh, seats, 100 * sh / seats))
for typ in ("flagship", "main", "qualifier"):
    R = [r for r in rows if r["type"] == typ]
    if not R: continue
    print("\n==", typ.upper(), "| contests %d on %d slates | max entries per user: %s | actual entries: %s" % (
        len(R), len({r['g'] for r in R}), sorted({r['max'] for r in R}), sorted({r['N_act'] for r in R})))
    # real entries
    by = defaultdict(list)
    for r in R: by[r["g"]].append(r)
    real = [sum(x["real"]["pay"] for x in v) / sum(x["fee"] * x["N_act"] for x in v) - 1 for v in by.values() if sum(x["fee"] * x["N_act"] for x in v)]
    fees_real = sum(r["fee"] * r["N_act"] for r in R); pay_real = sum(r["real"]["pay"] for r in R)
    print("  ENTERED lineups, re-scored: slate ROI %s, positive %d of %d, median %+.1f%% | period ROI %+.1f%% on $%.0f fees" % (
        ms(real), sum(x > 0 for x in real), len(real), 100 * S.median(real), 100 * (pay_real / fees_real - 1), fees_real))
    for rule in ("plain", "top50"):
        for lab in ("act", "max"):
            key = rule + "_" + lab
            RR = [r for r in R if key in r["rules"]]
            if not RR: continue
            b2 = defaultdict(list)
            for r in RR: b2[r["g"]].append(r)
            sl = []
            for v in b2.values():
                fees = sum(x["fee"] * NE(x["rules"][key]) for x in v)
                if fees: sl.append(sum(S.mean(x["rules"][key]["pays"]) for x in v) / fees - 1)
            fees_tot = sum(r["fee"] * NE(r["rules"][key]) for r in RR)
            per = [sum(r["rules"][key]["pays"][d] for r in RR) / fees_tot - 1 for d in range(D)]
            n_l = sum(NE(r["rules"][key]) for r in RR)     # top1 and cash in med.py are per seat requested; hits / filled seats
            t1 = sum(r["rules"][key]["top1"] * r["rules"][key]["N"] for r in RR) / n_l
            ca = sum(r["rules"][key]["cash"] * r["rules"][key]["N"] for r in RR) / n_l
            print("  %-5s %-3s count (%4d lineups, $%6.0f fees, %2d slates): slate ROI %s, positive %d of %d, median %+.1f%% | period ROI p5 %+.1f%% p50 %+.1f%% p95 %+.1f%%, P(negative) %.2f | top-1%% %.3f, cash %.3f per lineup" % (
                rule, lab, n_l, fees_tot, len(sl), ms(sl), sum(x > 0 for x in sl), len(sl), 100 * S.median(sl),
                100 * pctl(per, .05), 100 * pctl(per, .5), 100 * pctl(per, .95), sum(p < 0 for p in per) / D, t1, ca))
print("\n== PER SLATE (flagship and main): real entries vs random at the actual count vs random at the max count (plain; ROI, and p5..p95 of the slate over draws)")
for typ in ("flagship", "main"):
    R = [r for r in rows if r["type"] == typ]
    by = defaultdict(list)
    for r in R: by[(r["day"], r["g"])].append(r)
    for (day, g), v in sorted(by.items()):
        out = []
        fa = sum(x["fee"] * x["N_act"] for x in v)
        out.append("real %+.0f%%" % (100 * (sum(x["real"]["pay"] for x in v) / fa - 1)) if fa else "real n/a")
        for key in ("plain_act", "plain_max", "top50_max"):
            if not all(key in x["rules"] for x in v): continue
            fees = sum(x["fee"] * NE(x["rules"][key]) for x in v)
            sd = [sum(x["rules"][key]["pays"][d] for x in v) / fees - 1 for d in range(D)]
            out.append("%s %+.0f%% [%+.0f%%, %+.0f%%] (%d lineups)" % (key, 100 * S.mean(sd), 100 * pctl(sd, .05), 100 * pctl(sd, .95), sum(x["rules"][key]["N"] for x in v)))
        print("  %-8s %s %s: %s" % (typ, day, g, " | ".join(out)))
print("\n== FLAGSHIP vs MAIN, per-slate ROI difference on slates with both (plain, max count)")
for key in ("plain_max", "top50_max", "plain_act"):
    pair = []
    for g in sorted({r["g"] for r in rows}):
        rr = {}
        for typ in ("flagship", "main"):
            v = [r for r in rows if r["g"] == g and r["type"] == typ and key in r["rules"]]
            fees = sum(x["fee"] * NE(x["rules"][key]) for x in v)
            if fees: rr[typ] = sum(S.mean(x["rules"][key]["pays"]) for x in v) / fees - 1
        if len(rr) == 2: pair.append(rr["flagship"] - rr["main"])
    if len(pair) > 1:
        m, se = S.mean(pair), S.stdev(pair) / math.sqrt(len(pair))
        print("  %-9s flagship - main %+.1f%% ± %.1f, flagship ahead on %d of %d slates, 2xSE %.1f" % (key, 100 * m, 100 * se, sum(x > 0 for x in pair), len(pair), 200 * se))
