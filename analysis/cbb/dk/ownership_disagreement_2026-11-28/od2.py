"""Ownership disagreement test, part 2: our entries (1e), pre-lock signals (2), the cost of leaning away (3).
Reads od_rows.json (od.py) and the lock files; our entries from the public standings (labelled "us", never named).

Signals, each from the lock-time file (battle-royale-research data/dk/cbb/<slate>_proj.json) unless said:
  q          tagged Questionable at lock
  last1      last game's DK points - our projection
  last3      mean of the last 3 games' DK points - our projection
  min_trend  mean minutes of the last 3 games - season mpg
  min_gap    last game's minutes - our projected minutes
  dk_avg     DraftKings' season average - our projection (another source's view)
  miya       EvanMiya per-minute rate - ours (miya_ppm - ppm), only where logged
  sal_move   salary - previous salary ($k)
  pval       our projected value (fp per $1k)
  corr_res   our ownership correction (own - own_raw)
  checks     the checks score (today's rule, recomputed: friday_review_2026-11-27/fr_best.py)
  cheap_min  salary < $5k and last game's minutes >= our projected minutes + 5
  transfer   moved schools (the lock file's "moved")
Held out: for each slate, the sign of the signal's pooled correlation on the other slates is used; the held-out slate
scores +1 if its own correlation has that sign, for d (real - ours) and for act - proj separately; "both" = the
signal points the same way for both on the other slates and both hold on the held-out slate.
Projection test (ex ante): act - proj regressed on the signal on the other slates, held-out MAE gain."""
import ast, json, math, os, random, statistics as S, sys, bisect
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E
num = E.num
BRR = "/home/user/battle-royale-research"
rng = random.Random(9)
rows = json.load(open(os.path.join(HERE, "od_rows.json")))
src = open(os.path.join(HERE, "..", "friday_review_2026-11-27", "fr_best.py")).read()
ns = {}
exec(src.split("# field ownership by slate")[0], ns)
checks = ns["checks"]
def lit(v):
    if isinstance(v, (list, dict)): return v
    try: return ast.literal_eval(v) if v not in (None, "", "None") else None
    except Exception: return None
def ms(v):
    v = [x for x in v if x is not None]
    if len(v) < 2: return "n/a (%d)" % len(v)
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(2000))
    return "%+.3f ± %.3f (%d) [%+.3f, %+.3f], +%d" % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), bs[100], bs[1900], sum(x > 0 for x in v))
def corr(x, y):
    if len(x) < 5 or len(set(x)) < 2 or len(set(y)) < 2: return None
    mx, my = S.mean(x), S.mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
A = [r for r in rows if max(r["ours"], r["real"]) >= 5]
SL = sorted({r["slate"] for r in rows})
D = {(r["slate"], r["id"]): r for r in rows}

# ---------- 1e. our entries
P("## 1e. Our entries: exposure to field-loved (real 10+ over ours) and field-faded (10+ under) players, and finishes")
import csv
ev = defaultdict(set)
for r in csv.DictReader(open("/home/user/br_rankings/analysis/cbb/dk/eval.csv")): ev[r["draft_group"]].add((r["contest_id"], int(float(r["entries"]))))
gap_l, gap_f, gap_s, pct_by = [], [], [], defaultdict(lambda: defaultdict(list))
cost = []
for s in SL:
    g = s.split("_")[1]
    byname = {}
    for r in rows:
        if r["slate"] == s: byname.setdefault(r["name"], r)
    loved = {r["id"] for r in A if r["slate"] == s and r["d"] >= 10}; faded = {r["id"] for r in A if r["slate"] == s and r["d"] <= -10}
    us_l, us_f, fl_l, fl_f, n_us, n_f = 0, 0, 0, 0, 0, 0
    for cid, n in ev[g]:
        if n < 100: continue
        f = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(f): continue
        entries, _ = E.standings_rows(open(f, encoding="utf-8-sig"))
        field = sorted(e["points"] for e in entries); N = len(field)
        for e in entries:
            L = [byname.get(nm) for nm in E.lineup_names(e["lineup"])]
            if len(L) != 8 or any(x is None for x in L): continue
            nl = sum(x["id"] in loved for x in L); nf = sum(x["id"] in faded for x in L)
            mine = e["name"].lower().startswith(E.USER)
            if mine:
                us_l += nl; us_f += nf; n_us += 1
                pct = 100 * bisect.bisect_right(field, e["points"]) / N
                pct_by[min(nl, 2)][s].append(pct)
            else:
                fl_l += nl; fl_f += nf; n_f += 1
    if n_us and n_f:
        gap_l.append(us_l / n_us - fl_l / n_f); gap_f.append(us_f / n_us - fl_f / n_f); gap_s.append(s)
P("loved players per lineup, us - field: %s" % ms(gap_l))
P("faded players per lineup, us - field: %s" % ms(gap_f))
for k in (0, 1, 2):
    P("our lineups holding %s loved: per-slate mean finish pct %s, lineups %d" % ("2+" if k == 2 else k, ms([S.mean(v) for v in pct_by[k].values()]), sum(len(v) for v in pct_by[k].values())))
pairs = [S.mean(pct_by[1][s] + pct_by[2][s]) - S.mean(pct_by[0][s]) for s in SL if pct_by[0][s] and (pct_by[1][s] or pct_by[2][s])]
P("paired per slate, our lineups with 1+ loved minus with 0: %s" % ms(pairs))
# cost in points: our loved/faded gap x (loved residual - within residual) per slate
lv = defaultdict(list); fd = defaultdict(list); wi = defaultdict(list)
for r in A:
    (lv if r["d"] >= 10 else fd if r["d"] <= -10 else wi)[r["slate"]].append(r["res"])
cost = []
for s, gl, gf in zip(gap_s, gap_l, gap_f):
    if not wi[s]: continue
    w = S.mean(wi[s]); c = 0.0
    if lv[s]: c += gl * (S.mean(lv[s]) - w)
    if fd[s]: c += gf * (S.mean(fd[s]) - w)
    cost.append(c)
P("points per lineup from the gap, (us - field loved) x (loved - within act-proj) + (us - field faded) x (faded - within), per slate: %s" % ms(cost))

# ---------- 2. pre-lock signals
P("\n## 2. Pre-lock signals: do they predict both d (real - ours) and act - proj, held out by slate?")
for s in SL:
    pj = os.path.join(BRR, "data/dk/cbb/%s_proj.json" % s)
    Lk = json.load(open(pj)) if os.path.exists(pj) else {}
    ck = checks(Lk) if Lk else {}
    for r in rows:
        if r["slate"] != s: continue
        p = Lk.get(r["id"], {}); l5 = lit(p.get("last5")) or []
        g = [(q[1], q[2]) for q in l5 if len(q) > 2 and q[1] is not None and q[2] is not None]
        fp = r["fp"]; mp = r["min_proj"]; ma = num(p.get("min_avg"))
        sg = {}
        sg["q"] = 1.0 if (p.get("status") or r["status"]) == "Questionable" else 0.0
        sg["last1"] = g[-1][1] - fp if g else None
        sg["last3"] = S.mean(x[1] for x in g[-3:]) - fp if g else None
        sg["min_trend"] = S.mean(x[0] for x in g[-3:]) - ma if g and ma else None
        sg["min_gap"] = g[-1][0] - mp if g and mp is not None else None
        sg["dk_avg"] = num(p.get("dk_avg")) - fp if num(p.get("dk_avg")) is not None else None
        sg["miya"] = num(p.get("miya_ppm")) - num(p.get("ppm")) if num(p.get("miya_ppm")) is not None and num(p.get("ppm")) is not None else None
        sg["sal_move"] = (r["sal"] - num(p.get("sal_prev"))) / 1000 if num(p.get("sal_prev")) else None
        sg["pval"] = r["pval"]
        sg["corr_res"] = r["ours"] - r["raw"]
        sg["checks"] = ck.get(r["id"], (None,))[0]
        sg["cheap_min"] = 1.0 if (r["sal"] < 5000 and g and mp is not None and g[-1][0] >= mp + 5) else 0.0
        sg["transfer"] = 1.0 if str(p.get("moved")) == "True" else 0.0
        r["sg"] = sg
SIG = ["q", "last1", "last3", "min_trend", "min_gap", "dk_avg", "miya", "sal_move", "pval", "corr_res", "checks", "cheap_min", "transfer"]
A = [r for r in rows if max(r["ours"], r["real"]) >= 5 and "sg" in r]
def slate_r(sig, key, sl):
    out = {}
    for s in sl:
        v = [r for r in A if r["slate"] == s and r["sg"].get(sig) is not None]
        out[s] = corr([r["sg"][sig] for r in v], [r[key] for r in v])
    return out
rank_rows = []
for sig in SIG:
    rd = slate_r(sig, "d", SL); rr = slate_r(sig, "res", SL)
    hd = hr = hb = nb = 0; gains = []
    for h in SL:
        if rd.get(h) is None or rr.get(h) is None: continue
        od = [rd[s] for s in SL if s != h and rd.get(s) is not None]; orr = [rr[s] for s in SL if s != h and rr.get(s) is not None]
        if not od or not orr: continue
        sd, sr = S.mean(od) > 0, S.mean(orr) > 0
        hd += (rd[h] > 0) == sd; hr += (rr[h] > 0) == sr; nb += 1
        if sd == sr: hb += ((rd[h] > 0) == sd) and ((rr[h] > 0) == sr)
        tr = [r for r in A if r["slate"] != h and r["sg"].get(sig) is not None]; te = [r for r in A if r["slate"] == h and r["sg"].get(sig) is not None]
        if len(tr) > 10 and te and len({r["sg"][sig] for r in tr}) > 1:
            mx, my = S.mean(r["sg"][sig] for r in tr), S.mean(r["res"] for r in tr)
            b = sum((r["sg"][sig] - mx) * (r["res"] - my) for r in tr) / sum((r["sg"][sig] - mx) ** 2 for r in tr); a0 = my - b * mx
            gains.append(S.mean(abs(r["res"]) for r in te) - S.mean(abs(r["res"] - a0 - b * r["sg"][sig]) for r in te))
    md = [x for x in rd.values() if x is not None]; mr = [x for x in rr.values() if x is not None]
    same = (S.mean(md) > 0) == (S.mean(mr) > 0) if md and mr else None
    rank_rows.append((sig, len([r for r in A if r["sg"].get(sig) is not None]), ms(md), ms(mr), same, hd, hr, hb, nb, ms(gains), S.mean(gains) if gains else None, (S.stdev(gains) / math.sqrt(len(gains))) if len(gains) > 1 else None))
rank_rows.sort(key=lambda x: -(x[7] / x[8] if x[8] else 0))
P("signal | rows | r(signal, d) | r(signal, act-proj) | same direction | held-out sign right: d, act-proj, both (of n) | ex-ante projection: held-out MAE gain")
for x in rank_rows:
    P("%-10s | %4d | %s | %s | %s | %d, %d, %d of %d | %s" % (x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9]))
P("\nnot reconstructable from what is logged at lock: news/status changes after the projection was set (only the status at lock is stored, not when it changed or which update the field saw), line/total movement (only the lock line is stored), any outside source beyond EvanMiya and DraftKings' average.")
print("\n".join(OUT))

