"""Qualifier field refit: QUAL_CHALK held out by field. Real: field_users.csv own_sum / sub5 per user (the field side).
Sim: the slate's lock-time simulated field (mirror dk_cbb_field.json, the contest's band field), reweighted as dk.html
qualField does for each QUAL_CHALK; own_sum and sub5 on the night record's own (fieldusers' definition)."""
import csv, re, sys, os, math, statistics as S
from collections import OrderedDict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E, dk_field_study as FS, dk_sit as K
MIR = "/home/user/br-adp-mirror"; DK = "/home/user/br_rankings/analysis/cbb/dk"
q = OrderedDict()
for r in csv.DictReader(open(DK + "/field_users.csv")):
    if re.search("qualifier|satellite", r["contest"], re.I): q.setdefault((r["date"], r["draft_group"], r["contest_id"], int(r["size"])), []).append(r)
GRID = [x / 10 for x in range(0, 11)]
def qual_field(base, dkavg, c):
    ranked = sorted(range(len(base)), key=lambda i: (-sum(dkavg.get(str(p), 0) for p in base[i]), i))
    ranked = [base[i] for i in ranked]; nt = max(1, round(0.2 * len(ranked))); top, rest = ranked[:nt], ranked[nt:]
    N = len(base); ntop = round(c * N); out = [top[i % len(top)] for i in range(ntop)]
    j = 0
    while len(out) < N and rest:
        out.append(rest[min(len(rest) - 1, math.floor(j * len(rest) / (N - ntop)))]); j += 1
    return out
res = []
for (date, g, cid, size), us in q.items():
    rec = E.read(os.path.join(DK, "%s_%s.csv" % (date, g)))
    own = {r["dk_id"]: (E.num(r.get("own")) or 0.0) for r in rec}
    dka = {r["dk_id"]: (0 if r.get("status") == "Out" else (E.num(r.get("dk_avg")) or E.num(r.get("fp_dk")) or 0)) for r in rec}
    sl, start = K.lock_doc(MIR, "dk_cbb_morning.json", date, g)
    fd, _ = K.lock_doc(MIR, "dk_cbb_field.json", date, g, start)
    if not fd or not fd.get("field"): print("no field", date, g); continue
    bf = (fd.get("bands") or {}).get(FS.band(size).lower())
    F = bf["field"] if bf and bf.get("field") else fd["field"]
    real = [float(u["own_sum"]) for u in us]; rsub = [float(u["sub5"]) for u in us]
    sims = {}
    for c in GRID:
        QF = qual_field(F, dka, c)
        os_ = [sum(own.get(str(p), 0) for p in L) for L in QF]; sb = [sum(1 for p in L if own.get(str(p), 0) < 5) for L in QF]
        sims[c] = (S.median(os_), S.mean(sb))
    res.append({"key": (date, g, cid, size), "real_med": S.median(real), "real_sub5": S.mean(rsub), "n": len(us), "sims": sims})
    print(date, g, cid, size, "users", len(us), "real own_sum median %.0f sub5 %.2f" % (S.median(real), S.mean(rsub)),
          "| sim median at 0/0.5/0.8/1.0: " + " / ".join("%.0f" % sims[c][0] for c in (0.0, 0.5, 0.8, 1.0)))
# held out by field: choose c minimizing |sim_med - real_med| summed on the other fields; score held out vs c=0.8
err = lambda r, c: abs(r["sims"][c][0] - r["real_med"])
ho = []
for i, r in enumerate(res):
    tr = [x for j, x in enumerate(res) if j != i]
    best = min(GRID, key=lambda c: (sum(err(x, c) for x in tr), c))
    ho.append((r["key"], best, err(r, 0.8), err(r, best)))
    print("held out", r["key"][2], "c* =", best, "err at 0.8 %.1f, at c* %.1f" % (err(r, 0.8), err(r, best)))
d = [a - b for _, _, a, b in ho]
print("held-out gain (own_sum median abs err, 0.8 minus refit): %+.1f ± %.1f (%d), better on %d, worse on %d" % (S.mean(d), S.stdev(d) / math.sqrt(len(d)), len(d), sum(x > 0 for x in d), sum(x < 0 for x in d)))
print("pooled best c:", min(GRID, key=lambda c: sum(err(x, c) for x in res)), {c: round(S.mean(x["sims"][c][0] - x["real_med"] for x in res), 1) for c in GRID})
print("signed mean (sim - real) own_sum median at 0.8: %+.1f; sub5 sim-real at 0.8 %+.2f" % (S.mean(x["sims"][0.8][0] - x["real_med"] for x in res), S.mean(x["sims"][0.8][1] - x["real_sub5"] for x in res)))
