import csv, math, statistics as S
from collections import defaultdict
DK = "/home/user/br_rankings/analysis/cbb/dk"
num = lambda v: float(v) if v not in (None, "") else None
ev = {r["contest_id"]: r for r in csv.DictReader(open(DK + "/eval.csv")) if r.get("sim_cash")}
fe = defaultdict(dict)
for r in csv.DictReader(open(DK + "/field_eval.csv")): fe[r["contest_id"]][r["side"]] = r
print("sides:", sorted({s for v in fe.values() for s in v}))
rows = []
for cid, e in ev.items():
    if num(e.get("sim_cash")) is None or num(e.get("field_cash")) is None or int(float(e["entries"])) < 100: continue
    f = fe.get(cid, {}); re_, si = f.get("real"), f.get("sim")
    if not re_ or not si or num(re_.get("proj_mean")) is None or num(si.get("proj_mean")) is None: continue
    rows.append({"date": e["date"], "g": e["draft_group"], "cid": cid, "n": int(float(e["entries"])), "ver": e.get("version", ""),
                 "gap": num(e["sim_cash"]) - num(e["field_cash"]), "gap10": num(e["sim_top10"]) - num(e["field_top10"]),
                 "constr": num(si["proj_mean"]) - num(re_["proj_mean"]), "level": num(re_["proj_mean"]) - num(e["field_avg"]),
                 "real_spread": num(e["field_cash"]) - num(e["field_avg"]), "sim_spread_proxy": num(e["sim_cash"]) - num(si["proj_mean"]),
                 "sal_r": num(re_["sal_mean"]), "sal_s": num(si["sal_mean"]), "dup_r": num(re_.get("dup_field")), "dup_s": num(si.get("dup_field")),
                 "own_r": num(re_["own_sum"]), "own_s": num(si["own_sum"]), "punt_r": num(re_["punt1"]), "punt_s": num(si["punt1"])})
print("contests (100+ entries, both sides logged):", len(rows), "slates", len({r['g'] for r in rows}))
by = defaultdict(list)
for r in rows: by[r["g"]].append(r)
def ms(k, rs=None):
    v = [S.mean(x[k] for x in g if x[k] is not None) for g in (rs or by).values() if any(x[k] is not None for x in g)]
    return "%+.1f ± %.1f (%d slates)" % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v))
for k, lab in (("gap", "sim - real cash line"), ("gap10", "sim - real top-10% line"), ("constr", "construction: sim field's projected mean - real field's projected mean (our projections)"),
               ("level", "level: real field's projected mean - its actual mean"), ("sim_spread_proxy", "sim cash - sim projected mean"), ("real_spread", "real cash - real actual mean")):
    print("%-95s %s" % (lab, ms(k)))
print("identity check: gap = constr + level + (sim_spread - real_spread)")
for a, b, lab in (("sal_s", "sal_r", "salary mean sim vs real"), ("own_s", "own_r", "own sum"), ("dup_s", "dup_r", "dup"), ("punt_s", "punt_r", "punt1 share")):
    d = defaultdict(list)
    for r in rows:
        if r[a] is not None and r[b] is not None: d[r["g"]].append((r[a], r[b]))
    if not d: print(lab, "not logged"); continue
    sv = [S.mean(x for x, _ in v) for v in d.values()]; rv = [S.mean(y for _, y in v) for v in d.values()]
    print("%-25s sim %.1f real %.1f (diff %+.1f, %d slates)" % (lab, S.mean(sv), S.mean(rv), S.mean(sv) - S.mean(rv), len(sv)))
print("\nper slate: gap | constr | level | spread diff")
for g, v in sorted(by.items(), key=lambda kv: kv[1][0]["date"]):
    m = lambda k: S.mean(x[k] for x in v)
    print(v[0]["date"], g, len(v), "%+.1f | %+.1f | %+.1f | %+.1f" % (m("gap"), m("constr"), m("level"), m("sim_spread_proxy") - m("real_spread")))
print("\nheld-out level shift of the sim lines by the other slates' mean construction gap / mean total gap:")
G = [(g, S.mean(x["gap"] for x in v), S.mean(x["constr"] for x in v), S.mean(x["gap10"] for x in v)) for g, v in by.items()]
for lab, idx in (("construction shift", 2), ("total-gap shift", 1)):
    d = []; d10 = []
    for i, (g, gap, c, g10) in enumerate(G):
        sh = S.mean(x[idx] for j, x in enumerate(G) if j != i)
        d.append(abs(gap) - abs(gap - sh)); d10.append(abs(g10) - abs(g10 - sh))
    print(lab, "cash |gap| gain %+.2f ± %.2f, better on %d/%d; top10 gain %+.2f ± %.2f" % (S.mean(d), S.stdev(d)/math.sqrt(len(d)), sum(x > 0 for x in d), len(d), S.mean(d10), S.stdev(d10)/math.sqrt(len(d10))))
