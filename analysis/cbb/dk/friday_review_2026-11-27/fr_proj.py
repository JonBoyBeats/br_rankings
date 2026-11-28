"""Friday review 2026-11-27, sections 1-2: minutes and per-minute diagnosis, paired LIVE vs PREVIOUS vs RULER.
Rows as the scorecard (dk_proj_grade.graded / band). Per-slate means, then mean over slates +- SE."""
import ast, csv, glob, json, math, os, statistics as S, sys
BR = "/home/user/br_rankings"; BRR = "/home/user/battle-royale-research"
sys.path.insert(0, BR + "/scripts")
import dk_proj_grade as PG
num = PG.num

def ms(v):
    v = [x for x in v if x is not None]
    if not v: return "n/a"
    se = S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
    return "%+.2f ± %.2f (%d)" % (S.mean(v), se, len(v))

def lv(v):
    v = [x for x in v if x is not None]
    if not v: return "n/a"
    se = S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
    return "%.2f ± %.2f (%d)" % (S.mean(v), se, len(v))

BOX = {}
def box(ev):
    if ev not in BOX:
        f = f"{BRR}/data/cbb/box/2026-27/{ev}.json"
        BOX[ev] = json.load(open(f)) if os.path.exists(f) else None
    return BOX[ev]

def game_info(ev):
    b = box(ev)
    if not b: return None
    pts, mins = {}, {}
    for p in b["p"].values():
        pts[p["t"]] = pts.get(p["t"], 0) + (p.get("pts") or 0)
        mins[p["t"]] = mins.get(p["t"], 0) + (p.get("min") or 0)
    if len(pts) != 2: return None
    a, c = list(pts.values())
    return {"margin": abs(a - c), "ot": max(mins.values()) >= 215}

def parse(v):
    if isinstance(v, dict): return v
    try: return ast.literal_eval(v) if v not in (None, "", "None") else None
    except Exception: return None

slates = PG.slates()
out = []
def P(*a): out.append(" ".join(str(x) for x in a))

# Section 1: minutes, rotation band, by subgroup, paired diffs
def rot_rows(rows):
    return [r for r in PG.band(PG.graded(rows), *PG.ROTATION) if num(r.get("min")) is not None and num(r.get("min_proj")) is not None]

def stars_rows(rows):
    return PG.band(PG.graded(rows), *PG.STARS)

groups = {}
def add(key, slate, live, prev, rul):
    g = groups.setdefault(key, {})
    g.setdefault(slate, []).append((live, prev, rul))

lock = {}
for name, rows in slates:
    f = f"{BRR}/data/dk/cbb/{name}_proj.json"
    lock[name] = json.load(open(f)) if os.path.exists(f) else {}

for name, rows in slates:
    L = lock[name]
    for r in rot_rows(rows):
        act = num(r["min"]); live = abs(act - num(r["min_proj"]))
        prev = abs(act - num(r["min_old"])) if num(r.get("min_old")) is not None else None
        rul = abs(act - num(r["ruler_min"])) if num(r.get("ruler_min")) is not None else None
        p = L.get(r["dk_id"], {})
        gi = game_info(p.get("event")) if p.get("event") else None
        keys = ["all"]
        if gi:
            keys.append("blowout (margin 20+)" if gi["margin"] >= 20 else "close (margin <10)" if gi["margin"] < 10 else "mid (10-19)")
            if gi["ot"]: keys.append("OT game")
        else:
            keys.append("no box")
        pr = p.get("prior")
        keys.append("newcomer (no 2025-26 prior)" if pr in (None, "", "None") else "returner")
        gp = num(p.get("gp")) or 0
        keys.append("gp<=2" if gp <= 2 else "gp 3+")
        keys.append("DNP (0 min)" if act == 0 else "played")
        sgn = act - num(r["min_proj"])
        for k in keys: add(("min", k), name, live, prev, rul)
        groups.setdefault(("minbias", "all"), {}).setdefault(name, []).append(sgn)

P("## S1 minutes: rotation band minutes MAE by subgroup (per-slate mean, then over slates)")
P("| group | rows | LIVE | LIVE-PREV | LIVE-RULER |")
for (kind, k), g in sorted(groups.items()):
    if kind != "min": continue
    n = sum(len(v) for v in g.values())
    L_ = [S.mean(x[0] for x in v) for v in g.values()]
    dp = [S.mean(x[0] - x[1] for x in v if x[1] is not None) if any(x[1] is not None for x in v) else None for v in g.values()]
    dr = [S.mean(x[0] - x[2] for x in v if x[2] is not None) if any(x[2] is not None for x in v) else None for v in g.values()]
    P(f"| {k} | {n} | {lv(L_)} | {ms(dp)} | {ms(dr)} |")
P("signed minutes bias (actual - ours) rotation:", ms([S.mean(v) for v in groups[("minbias", "all")].values()]))

# minute parts (11-25 on): rotation band MAE of each part, and held-out best blend of parts
P("\n## S1b minute parts (slates with min_parts)")
parts_rows = {}
for name, rows in slates:
    L = lock[name]
    for r in rot_rows(rows):
        mp = parse(L.get(r["dk_id"], {}).get("min_parts"))
        if not mp or any(mp.get(k) is None for k in ("final","pre","form","qmin")): continue
        parts_rows.setdefault(name, []).append((num(r["min"]), mp, num(r["min_old"]), num(r["ruler_min"])))
for k in ("final", "pre", "form", "qmin"):
    P(k, "MAE", lv([S.mean(abs(a - mp[k]) for a, mp, *_ in v) for v in parts_rows.values()]),
      "minus final", ms([S.mean(abs(a - mp[k]) - abs(a - mp["final"]) for a, mp, *_ in v) for v in parts_rows.values()]))
# signed bias by part
for k in ("final", "qmin"):
    P(k, "bias (actual-part)", ms([S.mean(a - mp[k] for a, mp, *_ in v) for v in parts_rows.values()]))
# held-out shrink: final' = final + s*(final - pre) etc. one param: scale around slate rotation mean (steepness)
def steep(v, s):
    m = S.mean(mp["final"] for a, mp, *_ in v)
    return S.mean(abs(a - (m + s * (mp["final"] - m))) for a, mp, *_ in v)
names = sorted(parts_rows)
P("steepness rescale around slate mean, held out by slate (fit s on others):")
gains = []
for h in names:
    tr = [parts_rows[n] for n in names if n != h]
    best = min((sum(steep(v, s) for v in tr), s) for s in [x / 100 for x in range(70, 131, 2)])[1]
    gains.append(steep(parts_rows[h], 1.0) - steep(parts_rows[h], best))
    P("  held out", h, "s=", best, "gain", round(gains[-1], 3))
P("  mean gain", ms(gains))

# Section 2: per-minute (stars band points MAE), by subgroup and layers
P("\n## S2 per-minute: stars band points MAE (fp_dk), by subgroup")
g2 = {}
for name, rows in slates:
    L = lock[name]
    for r in stars_rows(rows):
        act = num(r["actual_dk"]); live = abs(act - num(r["fp_dk"]))
        prev = abs(act - num(r["old_fp"])) if num(r.get("old_fp")) is not None else None
        rul = abs(act - num(r["ruler_fp"])) if num(r.get("ruler_fp")) is not None else None
        p = L.get(r["dk_id"], {})
        gi = game_info(p.get("event")) if p.get("event") else None
        keys = ["all"]
        if gi: keys.append("blowout (margin 20+)" if gi["margin"] >= 20 else "close (margin <10)" if gi["margin"] < 10 else "mid (10-19)")
        if gi and gi["ot"]: keys.append("OT game")
        mn = num(r.get("min")); mp = num(r.get("min_proj"))
        if mn is not None and mp is not None:
            keys.append("minutes within 4" if abs(mn - mp) <= 4 else "minutes off 4+")
        for k in keys: g2.setdefault(k, {}).setdefault(name, []).append((live, prev, rul, act - num(r["fp_dk"])))
P("| group | rows | LIVE | bias (act-ours) | LIVE-PREV | LIVE-RULER |")
for k, g in sorted(g2.items()):
    n = sum(len(v) for v in g.values())
    L_ = [S.mean(x[0] for x in v) for v in g.values()]
    B_ = [S.mean(x[3] for x in v) for v in g.values()]
    dp = [S.mean(x[0] - x[1] for x in v if x[1] is not None) if any(x[1] is not None for x in v) else None for v in g.values()]
    dr = [S.mean(x[0] - x[2] for x in v if x[2] is not None) if any(x[2] is not None for x in v) else None for v in g.values()]
    P(f"| {k} | {n} | {lv(L_)} | {ms(B_)} | {ms(dp)} | {ms(dr)} |")

# all bands for points MAE: rotation band points too
P("\n## S2b rotation band points MAE and per-minute MAE at actual minutes (min>=10)")
rp = {}
for name, rows in slates:
    for r in rot_rows(rows):
        act = num(r["actual_dk"])
        rp.setdefault(name, []).append((abs(act - num(r["fp_dk"])), abs(act - num(r["old_fp"])) if num(r.get("old_fp")) is not None else None,
                                         abs(act - num(r["ruler_fp"])) if num(r.get("ruler_fp")) is not None else None))
P("rotation points MAE", lv([S.mean(x[0] for x in v) for v in rp.values()]),
  "LIVE-PREV", ms([S.mean(x[0] - x[1] for x in v if x[1] is not None) if any(x[1] is not None for x in v) else None for v in rp.values()]),
  "LIVE-RULER", ms([S.mean(x[0] - x[2] for x in v if x[2] is not None) if any(x[2] is not None for x in v) else None for v in rp.values()]))

# layers: ppm_parts (11-25 on). Per-minute error at actual minutes, stars + rotation (fp_dk >= 10, min >= 10)
P("\n## S2c layers (ppm_parts), players fp_dk>=10 and actual min>=10; DK ppm error at actual minutes")
lay = {}
for name, rows in slates:
    L = lock[name]
    for r in PG.band(PG.graded(rows), 10, math.inf):
        mn = num(r.get("min"))
        if not mn or mn < 10: continue
        pp = parse(L.get(r["dk_id"], {}).get("ppm_parts"))
        if not pp or any(pp.get(k) is None for k in ("baseline","matchup","vegas","game_adj","ppm")): continue
        a = num(r["actual_dk"]) / mn
        lay.setdefault(name, []).append((a, pp, num(r["fp_dk"]), num(r["min_proj"]), num(r["actual_dk"]), num(r["old_ppm"]) if r.get("old_ppm") else None))
def layer_mae(v, drop=None):
    e = []
    for a, pp, *_ in v:
        x = pp["baseline"]
        for k in ("matchup", "vegas", "game_adj"):
            if k != drop: x *= pp[k]
        e.append(abs(a - x))
    return S.mean(e)
P("full ppm MAE", lv([layer_mae(v) for v in lay.values()]))
for k in ("matchup", "vegas", "game_adj"):
    P("drop", k, "-> MAE minus full (positive = layer helps):", ms([layer_mae(v, k) - layer_mae(v) for v in lay.values()]))
P("bias actual ppm - ours:", ms([S.mean(a - pp["ppm"] for a, pp, *_ in v) for v in lay.values()]))
P("bias actual ppm - old_ppm:", ms([S.mean(a - o for a, pp, f, m, ad, o in v if o) for v in lay.values()]))
# layer spreads
for k in ("matchup", "vegas", "game_adj"):
    vals = [pp[k] for v in lay.values() for a, pp, *_ in v]
    P(k, "range", round(min(vals), 3), round(S.median(vals), 3), round(max(vals), 3))
# game_adj by slate
P("game_adj per slate:", {n: sorted({round(pp['game_adj'], 3) for a, pp, *_ in v}) for n, v in lay.items()})
print("\n".join(out))
