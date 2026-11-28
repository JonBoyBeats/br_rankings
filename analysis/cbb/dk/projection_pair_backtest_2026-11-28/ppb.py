"""Projection pair backtest (2026-11-28, operator-approved; analysis only, HELD).

Every graded slate, both models replayed from lock-time inputs, so the comparison doesn't rest on the 4 slates that log
PREVIOUS. Sources per slate:
  2026-11-16 .. 11-24 (14 slates), the QMIN / per-minute rebuild studies' replays (2026-11-25, held out by slate):
    OLD minutes     = (b) SIMPLE, the model live just before the rebuild (min_old's model), replayed (b_mins.json)
    REBUILT minutes = the shipped rebuild (steep 0.18, FORM 0.5; base params chosen on the other slates) (rb_mins.json)
    REBUILT ppm     = dk_ppm_study.project() with each slate's held-out final parameters (sel.json final_params;
                      the per-minute study's data.json: box scores, careers, opponents and lines before the slate)
  2026-11-25 .. 11-26 (4 slates), logged at lock: OLD = min_old, REBUILT = min_proj, REBUILT ppm = ppm_parts.ppm.
Situations (pre-lock, the lock file): fringe = |spread| >= 15, <= 2 games, a rotation teammate Out, Questionable or
p_play < 0.9; ordinary = the rest.
BASELINE = rebuilt minutes x rebuilt ppm (the live model). Bands (ROTATION 10-25, STARS 25+) from the baseline's points,
fixed for every candidate. Candidates (fitted pieces leave-one-slate-out):
  switch        minutes: OLD on ordinary rows, REBUILT on fringe; ppm rebuilt
  level         ppm x L, L fitted on the other slates (grid 0.85-1.05) on ROTATION + STARS points MAE
  pair          switch minutes and ppm x L (L fitted with the switch minutes)
  blowout       stars (baseline 25+): ppm x (1 - c x max(0, |pregame spread| - 10) / 10), c fitted on the other slates
  pair+blowout  all three
Headlines per slate (gain = baseline MAE - candidate MAE, positive better): ROTATION minutes MAE, STARS points MAE,
ROTATION points MAE; lenses: Spearman(projected points, actual) on players projected 10+, and top-10 value overlap
(projected vs actual DK points per $1k, players projected 10+)."""
import ast, json, math, os, statistics as S, sys
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_proj_grade as PG, dk_ppm_study as PS
num = PG.num
IN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inputs")   # the 11-25 studies' replays and data, copied
BRR = "/home/user/battle-royale-research"
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
def ms(v, d=3):
    v = [x for x in v if x is not None]
    if len(v) < 2: return "n/a"
    return ("%+." + str(d) + "f ± %." + str(d) + "f (%d), ahead %d") % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 1e-12 for x in v))
def lit(v):
    if isinstance(v, (dict, list)): return v
    try: return ast.literal_eval(v) if v not in (None, "", "None") else None
    except Exception: return None

bm = json.load(open(IN + "/b_mins.json")); rbm = json.load(open(IN + "/rb_mins.json"))
D = json.load(open(IN + "/data.json")); X = PS.prep(D); sel = json.load(open(IN + "/sel.json"))
ppm_rb = {}
for x in X:
    cfg = sel["final_params"].get(x["slate"])
    if cfg: ppm_rb[(x["slate"], x["dk_id"])] = PS.project(x, cfg, D)[1]["ppm"]
rows = []
src_note = defaultdict(int)
for name, recs in PG.slates():
    L = json.load(open(BRR + "/data/dk/cbb/%s_proj.json" % name)) if os.path.exists(BRR + "/data/dk/cbb/%s_proj.json" % name) else {}
    outs = defaultdict(int)
    for p in L.values():
        if p.get("status") == "Out" and (num(p.get("min_avg")) or 0) >= 15: outs[p.get("team")] += 1
    for r in PG.graded(recs):
        k = r["dk_id"]; p = L.get(k, {})
        act_min, act = num(r.get("min")), num(r.get("actual_dk"))
        if act_min is None: continue
        if name in rbm:
            if k not in rbm[name] or k not in bm.get(name, {}) or (name, k) not in ppm_rb: continue
            mo, mr, pr = bm[name][k][0], rbm[name][k][0], ppm_rb[(name, k)]; src = "replay"
        else:
            pp = lit(p.get("ppm_parts")) or {}
            mo, mr, pr = num(r.get("min_old")), num(r.get("min_proj")), pp.get("ppm")
            if mo is None or mr is None or pr is None: continue
            src = "logged"
        src_note[src] += 1
        sp = num(r.get("spread")); gp = num(p.get("gp")) or 0
        fringe = (sp is not None and abs(sp) >= 15) or gp <= 2 or bool(outs.get(r["team"])) or (r.get("status") or p.get("status")) == "Questionable" \
            or (num(p.get("p_play")) is not None and num(p.get("p_play")) < 0.9)
        base = mr * pr
        rows.append({"slate": name, "id": k, "sal": num(r["salary"]), "min": act_min, "act": act, "mo": mo, "mr": mr, "ppm": pr, "base": base,
                     "fringe": fringe, "sp": sp, "ev": p.get("event"), "team": r["team"],
                     "band": "stars" if base >= 25 else "rot" if base >= 10 else None})
SL = sorted({r["slate"] for r in rows})
P("rows %d on %d slates (%s); replayed slates %d, logged slates %d" % (len(rows), len(SL), dict(src_note), sum(1 for s in SL if s in rbm), sum(1 for s in SL if s not in rbm)))

# ---------- candidates
def mins(r, c):
    m = r["mo"] if (c.get("switch") and not r["fringe"] and r["mr"] >= c.get("thr", 0)) else r["mr"]
    if c.get("close") and r["band"] == "stars" and r["sp"] is not None and abs(r["sp"]) < 5:
        m = min(40.0, m + c["close"])
    return m
def ppm(r, c):
    x = r["ppm"] * (c.get("L", 1.0) if not (c.get("rot_only") and r["band"] != "rot") else 1.0)
    if c.get("blow") and r["band"] == "stars" and r["sp"] is not None:
        x *= 1 - c["blow"] * max(0.0, abs(r["sp"]) - 10) / 10
    return x
def pts(r, c): return mins(r, c) * ppm(r, c)
def heads(v, c):
    rot = [r for r in v if r["band"] == "rot"]; st = [r for r in v if r["band"] == "stars"]
    h = {"rot_min": S.mean(abs(r["min"] - mins(r, c)) for r in rot) if rot else None,
         "stars_pts": S.mean(abs(r["act"] - pts(r, c)) for r in st) if st else None,
         "rot_pts": S.mean(abs(r["act"] - pts(r, c)) for r in rot) if rot else None}
    g = [r for r in v if r["base"] >= 10]
    h["spear"] = PS_spear([pts(r, c) for r in g], [r["act"] for r in g]) if len(g) > 5 else None
    pv = sorted(g, key=lambda r: -pts(r, c) / r["sal"])[:10]; av = sorted(g, key=lambda r: -r["act"] / r["sal"])[:10]
    h["top10"] = len({r["id"] for r in pv} & {r["id"] for r in av}) / 10
    return h
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); rr = [0.0] * len(v)
    for j, i in enumerate(o): rr[i] = j
    return rr
def PS_spear(a, b):
    ra, rb = rank(a), rank(b); ma, mb = S.mean(ra), S.mean(rb)
    return sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
def fit(tr, c, key):
    if key == "thr":
        grid = [0, 10, 20, 30]
        score = lambda t: S.mean(abs(r["min"] - mins(r, dict(c, thr=t))) for r in tr if r["band"] == "rot")
        return min(grid, key=lambda g: (score(g), g))
    if key == "close":
        grid = [0.5 * i for i in range(0, 9)]
        score = lambda a: S.mean(abs(r["min"] - mins(r, dict(c, close=a))) for r in tr if r["band"] == "stars")
        return min(grid, key=lambda g: (score(g), g))
    if key == "L":
        grid = [0.85 + 0.01 * i for i in range(21)]
        score = lambda L: S.mean(abs(r["act"] - pts(r, dict(c, L=L))) for r in tr if r["band"])
    else:
        grid = [0.01 * i for i in range(0, 16)]
        score = lambda b: S.mean(abs(r["act"] - pts(r, dict(c, blow=b))) for r in tr if r["band"] == "stars")
    return min(grid, key=lambda g: (score(g), abs(g - (1.0 if key == "L" else 0.0))))
CANDS = {"switch": {"switch": True}, "level": {"fitL": True}, "pair": {"switch": True, "fitL": True},
         "blowout": {"fitB": True}, "pair+blowout": {"switch": True, "fitL": True, "fitB": True},
         "EXPLORATORY level on ROTATION only": {"fitL": True, "rot_only": True},
         "EXPLORATORY switch20 (threshold LOSO)": {"switch": True, "fitT": True},
         "EXPLORATORY pair20 (switch20 + level)": {"switch": True, "fitT": True, "fitL": True},
         "EXPLORATORY close-game stars' minutes + level": {"fitC": True, "fitL": True}}
base_h = {s: heads([r for r in rows if r["slate"] == s], {}) for s in SL}
P("\nbaseline (rebuilt minutes x rebuilt ppm), per-slate mean over %d slates: rot_min %.3f, stars_pts %.3f, rot_pts %.3f, spearman %.3f, top10 %.3f" % (
    len(SL), *[S.mean(base_h[s][k] for s in SL if base_h[s][k] is not None) for k in ("rot_min", "stars_pts", "rot_pts", "spear", "top10")]))
fitted = defaultdict(list)
for cn, spec in CANDS.items():
    g = defaultdict(list); go = defaultdict(list)
    for h in SL:
        tr = [r for r in rows if r["slate"] != h]; te = [r for r in rows if r["slate"] == h]
        c = {"switch": spec.get("switch", False), "rot_only": spec.get("rot_only", False)}
        if spec.get("fitT"): c["thr"] = fit(tr, c, "thr"); fitted[cn + " thr"].append(c["thr"])
        if spec.get("fitC"): c["close"] = fit(tr, c, "close"); fitted[cn + " close"].append(c["close"])
        if spec.get("fitB"): c["blow"] = fit(tr, c, "B"); fitted[cn + " c"].append(c["blow"])
        if spec.get("fitL"): c["L"] = fit(tr, c, "L"); fitted[cn + " L"].append(c["L"])
        ch = heads(te, c); bh = base_h[h]
        for k in ("rot_min", "stars_pts", "rot_pts"):
            if ch[k] is not None: g[k].append(bh[k] - ch[k])
        for k in ("spear", "top10"):
            if ch[k] is not None: g[k].append(ch[k] - bh[k])
        # ordinary-only rotation minutes and stars points
        o = [r for r in te if not r["fringe"]]
        oc, ob = heads(o, c), heads(o, {})
        for k in ("rot_min", "stars_pts", "rot_pts"):
            if oc[k] is not None and ob[k] is not None: go[k].append(ob[k] - oc[k])
        fr = [r for r in te if r["fringe"]]
        fc, fb = heads(fr, c), heads(fr, {})
        for k in ("rot_min", "stars_pts", "rot_pts"):
            if fc[k] is not None and fb[k] is not None: go["fringe_" + k].append(fb[k] - fc[k])
    P("\n== %s (gain = baseline - candidate, held out by slate)" % cn)
    for k in ("rot_min", "stars_pts", "rot_pts"): P("  %-10s all %s | ordinary %s | fringe %s" % (k, ms(g[k]), ms(go[k]), ms(go["fringe_" + k])))
    for k in ("spear", "top10"): P("  lens %-6s %s" % (k, ms(g[k])))
    # replayed slates only and logged slates only for the headline that matters most
    for lab, ss in (("replayed 14", [s for s in SL if s in rbm]), ("logged 4", [s for s in SL if s not in rbm])):
        idx = [i for i, s in enumerate(SL) if s in ss]
        P("  %s: rot_min %s | stars_pts %s | rot_pts %s" % (lab, ms([g["rot_min"][i] for i in idx]), ms([g["stars_pts"][i] for i in idx]), ms([g["rot_pts"][i] for i in idx])))
for k, v in fitted.items(): P("fitted %s across folds: min %.2f median %.2f max %.2f" % (k, min(v), S.median(v), max(v)))

# ---------- old vs rebuilt minutes on every slate (the question behind "4 slates")
P("\n## rebuilt vs old minutes, every slate, ROTATION minutes MAE (positive = rebuilt better)")
d = []; do = []; df = []
for s in SL:
    v = [r for r in rows if r["slate"] == s and r["band"] == "rot"]
    d.append(S.mean(abs(r["min"] - r["mo"]) - abs(r["min"] - r["mr"]) for r in v))
    o = [r for r in v if not r["fringe"]]; f = [r for r in v if r["fringe"]]
    if o: do.append(S.mean(abs(r["min"] - r["mo"]) - abs(r["min"] - r["mr"]) for r in o))
    if f: df.append(S.mean(abs(r["min"] - r["mo"]) - abs(r["min"] - r["mr"]) for r in f))
P("all %s | ordinary %s | fringe %s" % (ms(d), ms(do), ms(df)))
for lo, hi in ((30, 99), (20, 30), (10, 20), (0, 10)):
    v = [(r["slate"], abs(r["min"] - r["mo"]) - abs(r["min"] - r["mr"])) for r in rows if lo <= r["mr"] < hi and not r["fringe"]]
    bys = defaultdict(list)
    for s, x in v: bys[s].append(x)
    P("  ordinary, rebuilt minutes %d-%d: %s (rows %d)" % (lo, hi, ms([S.mean(x) for x in bys.values()]), len(v)))

# ---------- 3. stars in blowouts, pregame
P("\n## 3. Stars (baseline 25+): per-minute and minutes residuals by PREGAME |spread| (per-slate means, then over slates)")
for lo, hi in ((0, 5), (5, 10), (10, 15), (15, 20), (20, 99)):
    v = [r for r in rows if r["band"] == "stars" and r["sp"] is not None and lo <= abs(r["sp"]) < hi and r["min"] >= 10]
    bys = defaultdict(list)
    for r in v: bys[r["slate"]].append(r)
    P("  |spread| %2d-%-2d n=%3d | ppm act - proj %s | minutes act - proj %s | points act - proj %s" % (lo, hi, len(v),
      ms([S.mean(r["act"] / r["min"] - r["ppm"] for r in x) for x in bys.values()]), ms([S.mean(r["min"] - r["mr"] for r in x) for x in bys.values()]),
      ms([S.mean(r["act"] - r["base"] for r in x) for x in bys.values()])))
# slope per slate of ppm residual on |spread| for stars
sl = []
for s in SL:
    v = [r for r in rows if r["slate"] == s and r["band"] == "stars" and r["sp"] is not None and r["min"] >= 10]
    if len(v) < 5 or len({abs(r["sp"]) for r in v}) < 2: continue
    xs = [abs(r["sp"]) for r in v]; ys = [r["act"] / r["min"] - r["ppm"] for r in v]; mx, my = S.mean(xs), S.mean(ys)
    sl.append(10 * sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs))
P("  per-slate slope of stars' ppm residual per 10 points of pregame |spread|: %s" % ms(sl))
# diagnostic: final margin (labelled; not usable before lock)
box = {}
def margin(ev):
    if ev in box: return box[ev]
    f = BRR + "/data/cbb/box/2026-27/%s.json" % ev
    m = None
    if ev and os.path.exists(f):
        b = json.load(open(f)); t = defaultdict(float)
        for p in b.get("p", {}).values(): t[p["t"]] += p.get("pts") or 0
        if len(t) == 2: a, c = t.values(); m = abs(a - c)
    box[ev] = m; return m
P("  DIAGNOSTIC ONLY (final margin, known after the game):")
for lo, hi in ((0, 10), (10, 20), (20, 99)):
    v = [r for r in rows if r["band"] == "stars" and margin(r["ev"]) is not None and lo <= margin(r["ev"]) < hi and r["min"] >= 10]
    bys = defaultdict(list)
    for r in v: bys[r["slate"]].append(r)
    P("    final margin %2d-%-2d n=%3d | ppm act - proj %s | minutes act - proj %s" % (lo, hi, len(v), ms([S.mean(r["act"] / r["min"] - r["ppm"] for r in x) for x in bys.values()]), ms([S.mean(r["min"] - r["mr"] for r in x) for x in bys.values()])))
print("\n".join(OUT))
