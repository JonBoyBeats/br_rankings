import json, statistics as S, sys, os
sys.path.insert(0, "/home/user/br_rankings/scripts")
exec(open("fr_best.py").read().split("rows_out = []")[0])   # helpers only
R = json.load(open("fr_best.json"))
late = [o for o in R if o["slate"] >= "2026-11-21" and o["topv"]]
print("since 11-21 top-value n", len(late), "green", sum(1 for o in late if o["green"]), "score mean %.2f" % S.mean(o["score"] for o in late if o["score"] is not None))
V = [o for o in R if o["topv"]]
print("top-value with min_proj < 20: %d/%d; minutes +8 or more over proj: %d; actual min >= 30: %d" % (sum(1 for o in V if (o["min_proj"] or 0) < 20), len(V), sum(1 for o in V if o["min"] is not None and o["min_proj"] is not None and o["min"] - o["min_proj"] >= 8), sum(1 for o in V if (o["min"] or 0) >= 30)))
print("top-value whose ppm beat proj by 0.3+: %d; both min +5 and ppm +0.2: %d" % (sum(1 for o in V if o["ppm"] and o["ppm_proj"] and o["ppm"] - o["ppm_proj"] >= 0.3), sum(1 for o in V if o["ppm"] and o["ppm_proj"] and o["min"] is not None and o["ppm"] - o["ppm_proj"] >= 0.2 and o["min"] - o["min_proj"] >= 5)))
# base: average bank / kept / ours share among all fp>=10 players on build slates
import collections
bb, kk, oo = [], [], []
for name, rows in PG.slates():
    bd = build(name); g = name.split("_")[1]
    byname = {}
    for r in rows: byname.setdefault(r["name"], r["dk_id"])
    oc, on = ours(g, byname)
    for r in PG.graded(rows):
        if num(r["fp_dk"]) >= 10:
            if bd: bb.append(bd[0].get(r["dk_id"], 0)); kk.append(bd[1].get(r["dk_id"], 0))
            if on: oo.append(oc.get(r["dk_id"], 0) / on)
print("base rates fp>=10: bank %.3f kept %.3f ours %.3f" % (S.mean(bb), S.mean(kk), S.mean(oo)))
