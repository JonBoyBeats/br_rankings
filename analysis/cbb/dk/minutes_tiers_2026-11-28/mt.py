"""Minutes tiers (2026-11-28, operator-approved; analysis only, HELD).

Rows: graded slate files, players with fp_dk > 0, a real score and actual minutes (dk_proj_grade.graded). LIVE = min_proj
(the minutes at lock), PREVIOUS = min_old, RULER = ruler_min; rebuild-era slates (both logged): 2026-11-25 on. The
headline is the scorecard's: ROTATION band (fp_dk 10-25) minutes MAE.
Situations, all known at lock (lock file battle-royale-research data/dk/cbb/<slate>_proj.json):
  fringe = |spread| >= 15 (blowout-likely) or <= 2 games played or a rotation teammate (season mpg >= 15) Out at
           lock or status Questionable / p_play < 0.9 (DNP risk). OT can't be flagged before lock in a usable way: a
           spread-based "OT-sensitive" (|spread| <= 2.5) flagged 36% of rotation rows, so close games stay ordinary
           (the operator's definition) and OT is reported only after the fact in the Friday review.
  ordinary = the rest.
Team volatility before lock (ESPN box cache, battle-royale-research data/cbb/box/2026-27, games before the slate's date):
  vol = mean over the team's games of the SD of each regular's (3+ games, 15+ mpg) minutes across games;
  churn = share of consecutive games whose top 8 by minutes differ by 2+ players.
Slate is the unit: per-slate means, then mean +- SE over slates (slates positive / ahead).
"""
import ast, glob, json, math, os, statistics as S, sys
from collections import defaultdict
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_proj_grade as PG
num = PG.num
BRR = "/home/user/battle-royale-research"
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
def ms(v, d=2):
    v = [x for x in v if x is not None]
    if not v: return "n/a"
    if len(v) == 1: return ("%+." + str(d) + "f (1)") % v[0]
    return ("%+." + str(d) + "f ± %." + str(d) + "f (%d), +%d") % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 0 for x in v))
def lv(v):
    v = [x for x in v if x is not None]
    return "%.2f ± %.2f (%d)" % (S.mean(v), S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan"), len(v)) if v else "n/a"

# ---------- box cache: per team, games with players' minutes
games = []
for f in glob.glob(BRR + "/data/cbb/box/2026-27/*.json"):
    b = json.load(open(f))
    if b.get("date") and b.get("p"): games.append((b["date"][:10], b))
games.sort(key=lambda x: x[0])
team_games = defaultdict(list)          # espn team id -> [(date, {player: min})]
for d, b in games:
    by = defaultdict(dict)
    for pid, p in b["p"].items():
        by[p["t"]][pid] = p.get("min") or 0.0
    for t, m in by.items(): team_games[t].append((d, m))
def volatility(team, before):
    gs = [m for d, m in team_games.get(str(team), []) if d < before]
    if len(gs) < 3: return None, None, len(gs)
    allp = defaultdict(list)
    for m in gs:
        for p, v in m.items(): allp[p].append(v)
    reg = [p for p, v in allp.items() if len(v) >= 3 and S.mean(v) >= 15]
    sd = [S.stdev([m.get(p, 0.0) for m in gs]) for p in reg]
    tops = [set(sorted(m, key=lambda p: -m[p])[:8]) for m in gs]
    ch = [len(a - b) >= 2 for a, b in zip(tops, tops[1:])]
    return (S.mean(sd) if sd else None), (S.mean(ch) if ch else None), len(gs)

# ---------- rows
rows = []
for name, recs in PG.slates():
    L = json.load(open(BRR + "/data/dk/cbb/%s_proj.json" % name)) if os.path.exists(BRR + "/data/dk/cbb/%s_proj.json" % name) else {}
    outs = defaultdict(int)
    for p in L.values():
        if p.get("status") == "Out" and (num(p.get("min_avg")) or 0) >= 15: outs[p.get("team")] += 1
    date = name[:10]
    for r in PG.graded(recs):
        m, mp = num(r.get("min")), num(r.get("min_proj"))
        if m is None or mp is None: continue
        p = L.get(r["dk_id"], {})
        sp = num(r.get("spread")); gp = num(p.get("gp")) or 0
        fr = []
        if sp is not None and abs(sp) >= 15: fr.append("blowout-likely")
        if gp <= 2: fr.append("<=2 games")
        if outs.get(r["team"]): fr.append("teammate out")
        if (r.get("status") or p.get("status")) == "Questionable" or (num(p.get("p_play")) is not None and num(p.get("p_play")) < 0.9): fr.append("DNP risk")
        vol, churn, ng = volatility(p.get("espn_team"), date) if p.get("espn_team") else (None, None, 0)
        rows.append({"slate": name, "team": r["team"], "fp": num(r["fp_dk"]), "min": m, "live": mp, "prev": num(r.get("min_old")), "ruler": num(r.get("ruler_min")),
                     "min_avg": num(p.get("min_avg")), "fringe": fr, "ord": not fr, "vol": vol, "churn": churn})
ROT = [r for r in rows if 10 <= r["fp"] < 25]
REB = sorted({r["slate"] for r in rows if r["prev"] is not None})
P("rows %d (rotation band %d) on %d slates; rebuild-era slates with PREVIOUS logged: %s" % (len(rows), len(ROT), len({r['slate'] for r in rows}), REB))
TIERS = [("30+", lambda r: r["live"] >= 30), ("20-30", lambda r: 20 <= r["live"] < 30), ("10-20", lambda r: 10 <= r["live"] < 20), ("<10", lambda r: r["live"] < 10)]
def per(rs, f):
    d = defaultdict(list)
    for r in rs: d[r["slate"]].append(r)
    return [f(v) for v in d.values() if v]
def mae(v, k): return S.mean(abs(x["min"] - x[k]) for x in v)
def pair(v, k):
    w = [x for x in v if x.get(k) is not None]
    return S.mean(abs(x["min"] - x["live"]) - abs(x["min"] - x[k]) for x in w) if w else None

# ---------- 1. tiers
P("\n## 1. By projected-minutes tier (LIVE at lock), every graded player; LIVE - X: negative = LIVE better")
P("| tier | situation | rows | LIVE MAE | bias (act - live) | off 5+ | LIVE - PREV (rebuild era) | LIVE - RULER |")
for tl, tf in TIERS:
    for sl, sf in (("all", lambda r: True), ("ordinary", lambda r: r["ord"]), ("fringe", lambda r: not r["ord"])):
        rs = [r for r in rows if tf(r) and sf(r)]
        if not rs: continue
        P("| %s | %s | %d | %s | %s | %s | %s | %s |" % (tl, sl, len(rs), lv(per(rs, lambda v: mae(v, "live"))), ms(per(rs, lambda v: S.mean(x["min"] - x["live"] for x in v))),
          lv(per(rs, lambda v: S.mean(abs(x["min"] - x["live"]) >= 5 for x in v))), ms(per([r for r in rs if r["prev"] is not None], lambda v: pair(v, "prev"))),
          ms(per([r for r in rs if r["ruler"] is not None], lambda v: pair(v, "ruler")))))
P("\nrotation band (headline), ordinary vs fringe, rebuild era:")
for sl, sf in (("all", lambda r: True), ("ordinary", lambda r: r["ord"]), ("fringe", lambda r: not r["ord"])):
    rs = [r for r in ROT if sf(r) and r["prev"] is not None]
    P("  %-9s rows %4d | LIVE %s | PREV %s | LIVE - PREV %s" % (sl, len(rs), lv(per(rs, lambda v: mae(v, "live"))), lv(per(rs, lambda v: mae(v, "prev"))), ms(per(rs, lambda v: pair(v, "prev")))))
fc = defaultdict(int)
for r in ROT:
    for x in r["fringe"]: fc[x] += 1
P("  fringe flags among rotation rows (all slates): %s; ordinary share %.0f%%" % (dict(fc), 100 * sum(r["ord"] for r in ROT) / len(ROT)))

# ---------- 2. teams
P("\n## 2. Teams: rotation-band minutes MAE (all 18 slates, LIVE), bias, rebuild - previous; volatility before lock")
bt = defaultdict(list)
for r in ROT: bt[r["team"]].append(r)
allm = S.mean(abs(r["min"] - r["live"]) for r in ROT)
K = 10      # shrinkage: team MAE shrunk toward the pooled MAE with K pseudo-rows
trows = []
for t, v in bt.items():
    n = len(v); m = S.mean(abs(r["min"] - r["live"]) for r in v)
    sh = (n * m + K * allm) / (n + K)
    vol = [r["vol"] for r in v if r["vol"] is not None]; ch = [r["churn"] for r in v if r["churn"] is not None]
    pv = [abs(r["min"] - r["live"]) - abs(r["min"] - r["prev"]) for r in v if r["prev"] is not None]
    trows.append((t, n, m, sh, S.mean(r["min"] - r["live"] for r in v), S.mean(vol) if vol else None, S.mean(ch) if ch else None, S.mean(pv) if pv else None, len(pv)))
trows.sort(key=lambda x: x[3])
P("teams with 6+ rotation rows: %d. Best and worst 8 by shrunk MAE (K=%d toward the pooled %.2f):" % (sum(1 for x in trows if x[1] >= 6), K, allm))
sel = [x for x in trows if x[1] >= 6]
for x in sel[:8] + [None] + sel[-8:]:
    if x is None: P("  ..."); continue
    P("  %-6s rows %2d | MAE %.2f (shrunk %.2f) | bias %+.2f | vol %s | churn %s | rebuild - prev %s (%d)" % (x[0], x[1], x[2], x[3], x[4], "%.2f" % x[5] if x[5] is not None else "n/a",
      "%.2f" % x[6] if x[6] is not None else "n/a", "%+.2f" % x[7] if x[7] is not None else "n/a", x[8]))
def corr(a, b):
    if len(a) < 5 or len(set(a)) < 2 or len(set(b)) < 2: return None
    ma, mb = S.mean(a), S.mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
P("\nis it the swingy teams? per slate, r(team volatility before lock, player |miss|) over rotation rows:")
for k in ("vol", "churn"):
    P("  %-6s %s" % (k, ms(per([r for r in ROT if r[k] is not None], lambda v: corr([x[k] for x in v], [abs(x["min"] - x["live"]) for x in v])), 3)))
# predictable before lock: volatility measured on games before slate t vs the team's miss on slate t and later
P("  high-vol (above the slate's median) minus low-vol rotation MAE, per slate: %s" % ms(per([r for r in ROT if r["vol"] is not None], lambda v: (lambda med: (S.mean(abs(x["min"] - x["live"]) for x in v if x["vol"] > med) - S.mean(abs(x["min"] - x["live"]) for x in v if x["vol"] <= med)) if any(x["vol"] > med for x in v) and any(x["vol"] <= med for x in v) else None)(S.median(x["vol"] for x in v)))))
# team miss persistence: a team's mean |miss| on earlier slates vs on later slates (split by date)
SLS = sorted({r["slate"] for r in ROT}); half = set(SLS[:len(SLS) // 2])
e = defaultdict(list); l = defaultdict(list)
for r in ROT: (e if r["slate"] in half else l)[r["team"]].append(abs(r["min"] - r["live"]))
both = [t for t in e if t in l and len(e[t]) >= 3 and len(l[t]) >= 3]
P("  team miss persistence, first-half slates vs second-half (teams with 3+ rows each, %d teams): r %s" % (len(both), "%.3f" % corr([S.mean(e[t]) for t in both], [S.mean(l[t]) for t in both]) if len(both) >= 5 else "n/a"))
vb = [t for t in both if any(r["vol"] is not None for r in bt[t])]
P("  team volatility (mean before lock) vs its second-half miss: r %s (%d teams)" % ("%.3f" % corr([S.mean([r["vol"] for r in bt[t] if r["vol"] is not None]) for t in vb], [S.mean(l[t]) for t in vb]) if len(vb) >= 5 else "n/a", len(vb)))

# ---------- 3. candidates, held out by slate, rebuild era (PREVIOUS needed for a and b)
P("\n## 3. Candidate fixes, held out by slate on the rotation-minutes headline (rebuild era: %d slates)" % len(REB))
R4 = [r for r in ROT if r["prev"] is not None]
W = [i / 10 for i in range(11)]
def tier_of(r): return next(tl for tl, tf in TIERS if tf(r))
def run(name, pred_fn, fit_fn):
    g_all, g_ord, g_fr = [], [], []
    for h in REB:
        tr = [r for r in R4 if r["slate"] != h]; te = [r for r in R4 if r["slate"] == h]
        par = fit_fn(tr)
        def gain(v): return S.mean(abs(x["min"] - x["live"]) - abs(x["min"] - pred_fn(x, par)) for x in v) if v else None
        g_all.append(gain(te)); g_ord.append(gain([x for x in te if x["ord"]])); g_fr.append(gain([x for x in te if not x["ord"]]))
    P("%-48s all %s | ordinary %s | fringe %s" % (name, ms(g_all), ms(g_ord), ms(g_fr)))
    return g_all
def fit_w(rs, key=lambda r: "x"):
    out = {}
    for k in {key(r) for r in rs}:
        v = [r for r in rs if key(r) == k]
        out[k] = min(W, key=lambda w: (S.mean(abs(x["min"] - (w * x["live"] + (1 - w) * x["prev"])) for x in v), -w))
    return out
# reference: previous outright
run("ref: PREVIOUS outright (LIVE -> min_old)", lambda x, p: x["prev"], lambda tr: None)
run("(b0) one blend weight, all rows", lambda x, p: p.get("x", 1) * x["live"] + (1 - p.get("x", 1)) * x["prev"], lambda tr: fit_w(tr))
run("(a) situation switch: rebuild on fringe, blend on ordinary (w per tier)",
    lambda x, p: x["live"] if not x["ord"] else p.get(tier_of(x), 1) * x["live"] + (1 - p.get(tier_of(x), 1)) * x["prev"],
    lambda tr: fit_w([r for r in tr if r["ord"]], tier_of))
run("(b) tier blend (w per projected-minutes tier, all rows)",
    lambda x, p: p.get(tier_of(x), 1) * x["live"] + (1 - p.get(tier_of(x), 1)) * x["prev"], lambda tr: fit_w(tr, tier_of))
# (c) volatility shrinkage toward the player's season mpg on teams above the training slates' median volatility
def fit_c(tr):
    med = S.median(r["vol"] for r in tr if r["vol"] is not None)
    best = min([i / 10 for i in range(0, 8)], key=lambda s: (S.mean(abs(x["min"] - ((1 - s) * x["live"] + s * x["min_avg"])) if (x["vol"] is not None and x["vol"] > med and x["min_avg"]) else abs(x["min"] - x["live"]) for x in tr), s))
    return {"med": med, "s": best}
def pred_c(x, p):
    return (1 - p["s"]) * x["live"] + p["s"] * x["min_avg"] if (x["vol"] is not None and x["vol"] > p["med"] and x["min_avg"]) else x["live"]
gc = run("(c) volatility shrinkage toward season mpg (high-vol teams)", pred_c, fit_c)
# fitted parameters on all 4
P("fitted on all rebuild-era slates: one weight %s; ordinary per tier %s; per tier %s; (c) %s" % (fit_w(R4), fit_w([r for r in R4 if r["ord"]], tier_of), fit_w(R4, tier_of), fit_c(R4)))
# (c) on every graded slate (it needs no PREVIOUS): held out across all 18 slates on the live minutes of the day
ALLS = sorted({r["slate"] for r in ROT})
g = []; go = []; gf = []
for h in ALLS:
    tr = [r for r in ROT if r["slate"] != h and r["vol"] is not None]; te = [r for r in ROT if r["slate"] == h]
    if not tr: continue
    p = fit_c(tr)
    G = lambda v: S.mean(abs(x["min"] - x["live"]) - abs(x["min"] - pred_c(x, p)) for x in v) if v else None
    g.append(G(te)); go.append(G([x for x in te if x["ord"]])); gf.append(G([x for x in te if not x["ord"]]))
P("(c) on all %d graded slates (each slate's own live minutes): all %s | ordinary %s | fringe %s" % (len(ALLS), ms(g), ms(go), ms(gf)))
print("\n".join(OUT))
