"""Lab d after the control switch (2026-11-28): the registered form (kept green lineups vs the replayed plain L0 U0
draw, uncut) beside a symmetric check (every drawn green lineup, kept or cut, vs the same replay), per night."""
import glob, json, math, os, statistics as St, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "scripts"))
import dk_eval as E
from collections import defaultdict
ev = defaultdict(dict)
for r in E.read(E.EVAL):
    ev[r["draft_group"]][r["contest_id"]] = r["contest"]
res = {"kept": [], "drawn": []}
for bf in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
    b = json.load(open(bf)); g = str(b["draft_group"]); day = b["day"]
    if day < "2026-11-24":
        continue
    ctrl = E.lab_control(day, g)
    rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (day, g)))
    if not ctrl or not rec:
        continue
    tags = [set(t) if isinstance(t, list) else {t} for t in b["tags"]]
    gname = b.get("groups") or {}
    green = lambda t: "GREENS " in t or bool(E.GREEN_IDEA_RE.fullmatch(str(gname.get(t, "")).strip()))
    kept = set(b.get("final") or range(len(b["pool"])))
    Tk = [b["pool"][k] for k in kept if any(green(t) for t in tags[k])]
    Td = [b["pool"][k] for k in range(len(b["pool"])) if any(green(t) for t in tags[k])]
    if not Tk:
        continue
    dk, dd = [], []
    for cid in ev.get(g, {}):
        p = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(p):
            continue
        ents, players = E.standings(p)
        n = len(ents)
        if n < E.LAB_MIN_ENTRIES:
            continue
        pts = E.night_points(rec, players)
        field = sorted((e["points"] for e in ents), reverse=True)
        f = lambda L: St.mean(100.0 * (n - (E.placed(sum(pts.get(str(i)) or 0 for i in x), field) - 1)) / n for x in L)
        c = f(ctrl)
        dk.append(f(Tk) - c); dd.append(f(Td) - c)
    print("%s %s  green kept %4d drawn %5d | kept - replay %+6.2f | drawn - replay %+6.2f" % (day, g, len(Tk), len(Td), St.mean(dk), St.mean(dd)))
    res["kept"].append(St.mean(dk)); res["drawn"].append(St.mean(dd))
for k, v in res.items():
    print("%-6s %+.2f ± %.2f over %d nights, ahead on %d" % (k, St.mean(v), St.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 0 for x in v)))
