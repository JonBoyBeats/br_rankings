"""Recipes against each other (score_out.json): jitter, greencore and light against all-plain; max exposure against d9."""
import json, statistics as S, math
d = json.load(open("score_out.json"))
def line(l, v): print("%-40s %+6.2f ± %5.2f  %d slates, ahead %d" % (l, S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 0 for x in v)))
P, F = d["pool"], d["fill"]
for a, b in (("jitter", "plain"), ("greencore", "plain"), ("light", "plain")):
    ks = [k for k in P[a] if k in P[b]]
    line("kept pct %s - %s" % (a, b), [P[a][k]["kept"] - P[b][k]["kept"] for k in ks])
    line("kept cores %s - %s" % (a, b), [P[a][k]["cores"] - P[b][k]["cores"] for k in ks])
    line("kept max exposure %s - %s" % (a, b), [P[a][k]["maxexpo"] - P[b][k]["maxexpo"] for k in ks])
    ks = [k for k in F[a] if k in F[b] and "all" in F[a][k] and "all" in F[b][k]]
    line("fill pct %s - %s" % (a, b), [F[a][k]["all"][0] - F[b][k]["all"][0] for k in ks])
for a in ("plain", "greencore", "jitter", "light"):
    ks = [k for k in P[a] if k in P["d9"]]
    line("kept max exposure %s - d9" % a, [P[a][k]["maxexpo"] - P["d9"][k]["maxexpo"] for k in ks])
