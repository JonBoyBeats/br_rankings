import sys, math, statistics as S
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_proj_grade as PG
num = PG.num
def ms(v):
    v=[x for x in v if x is not None]; return "%+.2f ± %.2f (%d)" % (S.mean(v), S.stdev(v)/math.sqrt(len(v)), len(v))
for lab, lo, hi in (("rotation", 10, 25), ("stars", 25, math.inf)):
    pb, ob, ppb, opb, mb = [], [], [], [], []
    for name, rows in PG.slates():
        R = [r for r in PG.band(PG.graded(rows), lo, hi) if num(r.get("old_fp")) is not None]
        if not R: continue
        pb.append(S.mean(num(r["actual_dk"]) - num(r["fp_dk"]) for r in R))
        ob.append(S.mean(num(r["actual_dk"]) - num(r["old_fp"]) for r in R))
        Q = [r for r in R if (num(r["min"]) or 0) >= 10 and num(r.get("ppm_proj")) and num(r.get("old_ppm"))]
        ppb.append(S.mean(num(r["actual_dk"]) / num(r["min"]) - num(r["fp_dk"]) / num(r["min_proj"]) for r in Q if num(r["min_proj"])))
        mb.append(S.mean(num(r["min"]) - num(r["min_proj"]) for r in R))
    print(lab, "points bias live", ms(pb), "prev", ms(ob), "| ppm bias (DK, min>=10)", ms(ppb), "| minutes bias", ms(mb))
