import json, glob, re, csv, os, sys, statistics as S, bisect
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E
DK = "/home/user/br_rankings/analysis/cbb/dk"
ev = defaultdict(dict)
for r in csv.DictReader(open(DK + "/eval.csv")): ev[r["draft_group"]][r["contest_id"]] = int(float(r["entries"]))
GRE = re.compile(r"green(\s*[345])?", re.I)
for f in sorted(glob.glob(DK + "/builds/*.json")):
    name = os.path.basename(f)[8:-5]
    if name < "2026-11-24": continue
    g = name.split("_")[1]; rec = os.path.join(DK, name + ".csv")
    if not os.path.exists(rec): continue
    pts = {r["dk_id"]: E.num(r.get("actual_dk")) for r in E.read(rec)}
    if not any(v is not None for v in pts.values()): print(name, "not graded"); continue
    b = json.load(open(f)); groups = b.get("groups") or {}; kept = sorted(set(b.get("final") or []))
    def grp(i):
        t = b["tags"][i]; ts = t if isinstance(t, list) else [t]; out = set()
        for x in ts:
            gn = str(groups.get(x, "")).strip()
            if "GREENS " in x: out.add("GREENS <game>")
            elif GRE.fullmatch(gn): out.add(gn.upper())
            elif x.startswith("variant of"): out.add("Variants")
            else: out.add("other (hand / base)")
        return out
    for cid, n in ev[g].items():
        if n < 100: continue
        sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(sf): continue
        field = sorted(e["points"] for e in E.standings_rows(open(sf, encoding="utf-8-sig"))[0])
        N = len(field)
        def pct(L):
            p = sum((pts.get(str(i)) or 0) for i in L); more = N - bisect.bisect_right(field, p); return 100 * (N - more) / N
        by = defaultdict(list); allk = []
        for i in kept:
            v = pct(b["pool"][i]); allk.append(v)
            for gg in grp(i): by[gg].append(v)
        print(name, cid, "N=%d" % N, "all kept %.1f (%d)" % (S.mean(allk), len(allk)), " | ".join("%s %.1f (%d)" % (k, S.mean(v), len(v)) for k, v in sorted(by.items())))
