"""The tiered-ownership test (2026-11-28, operator-approved; analysis only, HELD). Friday review section 3.

A. A field-ownership model below a salary crossover built from FIELD-SIDE, lock-time signals (not our projection), our
   ownership (live = the record's own, with the correction; raw = own_raw) kept above it, a linear blend over the
   $1k below the crossover. Fitted leave-one-slate-out; the crossover ($6k / $6.5k / $7k / $7.5k / $8k) and the blend
   chosen on the other slates.
   Rows: every player in a graded slate's night record not Out at lock; real ownership = entries-weighted mean over the
   slate's 100+ entry contests (0 where a contest's standings don't list him: undrafted).
   Field-side features (lock file battle-royale-research data/dk/cbb/<slate>_proj.json; each also as its percentile
   within the slate, since the field picks relative to the slate):
     sal        salary ($k)
     dkv        DraftKings' season average per $1k (the value the field sees on DK's own screen)
     l1v, l3v   last game's / last 3 games' DK points per $1k
     lmin, mavg last game's minutes; season mpg
     miya       EvanMiya's per-minute x season mpg per $1k (the outside source)
     imp        implied team total (ou / 2 - spread / 2)
     tconc      teammates whose dkv is in the slate's top 15 (field-side chalk concentration)
     gp         games played
   Model: least squares on log(real + 0.5), predictions back-transformed; the sub-crossover predictions rescaled to our
   own sub-crossover total on the slate (the slate's ownership total is kept; only who gets it changes), or not, and a
   concentration exponent (pred^1 / 1.5 / 2 / 3) before the rescale; all chosen held out. Crossovers $5k-$8k.
   Scores per slate: chalk-band MAE (max(real, pred) >= 15) and its off-by-10+ share, the concentration miss (the
   field's top-8 sum minus the model's top-8 sum), all-player MAE, and each by salary tier; against live and raw.
B/C. Tiered exposure on the builds with board values (14): keep half of the kept pool, ranked by
     score = board value rank (0-1) + lambda x (sum over the lineup's sub-$7k players of max(0, field_i - exposure_i) / 100)
   where exposure_i is his share of the kept pool and field_i the predicted field ownership: B = today's ownership
   (live), C = the tiered model of A (A+B). lambda in {0, 0.5, 1, 2, 4} chosen held out on mean finish percentile;
   lambda = 0 is the board-only top half (the reference). Scored on the 100+ entry contests: finish percentile and
   payout per lineup per contest ($, from the contest's table), by contest type.
"""
import ast, bisect, csv, glob, json, math, os, re, statistics as S, sys
from collections import defaultdict
import numpy as np
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dk_eval as E, dk_proj_grade as PG
num = E.num
BRR = os.environ.get("BRR") or os.path.join(os.path.dirname(ROOT), "battle-royale-research")
MIRROR = os.environ.get("MIRROR") or os.path.join(os.path.dirname(ROOT), "br-adp-mirror")
OUT = []
def P(*a): OUT.append(" ".join(str(x) for x in a))
def ms(v, d=2):
    v = [x for x in v if x is not None]
    if len(v) < 2: return "n/a (%d)" % len(v)
    return ("%+." + str(d) + "f ± %." + str(d) + "f (%d), ahead %d") % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 1e-12 for x in v))
def lv(v, d=2):
    v = [x for x in v if x is not None]
    return ("%." + str(d) + "f ± %." + str(d) + "f (%d)") % (S.mean(v), S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan"), len(v)) if v else "n/a"
def lit(v):
    if isinstance(v, (list, dict)): return v
    try: return ast.literal_eval(v) if v not in (None, "", "None") else None
    except Exception: return None
def pct_rank(vals):
    s = sorted(v for v in vals if v is not None)
    return [None if v is None else (sum(x < v for x in s) + sum(x <= v for x in s)) / 2 / len(s) for v in vals]

# ---------- real ownership per slate x player (100+ entry contests, entries-weighted, 0 when undrafted)
ev = defaultdict(dict)
for r in csv.DictReader(open(os.path.join(E.DK, "eval.csv"))): ev[r["draft_group"]][r["contest_id"]] = int(float(r["entries"]))
contest_own = {}
for g, cs in ev.items():
    for cid, n in cs.items():
        if n < 100: continue
        f = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(f): continue
        _, players = E.standings_rows(open(f, encoding="utf-8-sig"))
        contest_own[(g, cid)] = ({nm: (v[0] or 0.0) for nm, v in players.items()}, n)
rows = []
for name, recs in PG.slates():
    g = name.split("_")[1]
    cs = [(o, n) for (gg, cid), (o, n) in contest_own.items() if gg == g]
    if not cs: continue
    L = json.load(open(os.path.join(BRR, "data/dk/cbb/%s_proj.json" % name))) if os.path.exists(os.path.join(BRR, "data/dk/cbb/%s_proj.json" % name)) else {}
    W = sum(n for _, n in cs)
    sl = []
    for r in recs:
        if (r.get("status") or "") == "Out" or num(r.get("own")) is None or not num(r.get("salary")): continue
        p = L.get(r["dk_id"], {})
        real = sum(o.get(r["name"], 0.0) * n for o, n in cs) / W
        sal = num(r["salary"]) / 1000
        l5 = [q for q in (lit(p.get("last5")) or []) if len(q) > 2 and q[1] is not None and q[2] is not None]
        mavg, dka = num(p.get("min_avg")), num(p.get("dk_avg"))
        miya = num(p.get("miya_ppm"))
        sp, ou = num(r.get("spread")), num(r.get("ou"))
        sl.append({"slate": name, "g": g, "id": r["dk_id"], "name": r["name"], "team": r["team"], "sal": sal, "real": real,
                   "live": num(r["own"]), "raw": num(r.get("own_raw")) if num(r.get("own_raw")) is not None else num(r["own"]),
                   "fp": num(r.get("fp_dk")), "act": num(r.get("actual_dk")),
                   "f": {"sal": sal, "dkv": dka / sal if dka is not None else None,
                         "l1v": l5[-1][2] / sal if l5 else None, "l3v": S.mean(q[2] for q in l5[-3:]) / sal if l5 else None,
                         "lmin": l5[-1][1] if l5 else None, "mavg": mavg,
                         "miya": miya * mavg / sal if (miya is not None and mavg) else None,
                         "imp": (ou / 2 - sp / 2) if (sp is not None and ou is not None) else None,
                         "gp": num(p.get("gp"))}})
    # within-slate percentiles and team concentration (field-side: top-15 by DK-average value)
    for k in ("dkv", "l1v", "l3v", "lmin", "mavg", "miya", "imp", "sal"):
        pr = pct_rank([x["f"][k] for x in sl])
        for x, v in zip(sl, pr): x["f"]["p_" + k] = v
    top = sorted([x for x in sl if x["f"]["dkv"] is not None], key=lambda x: -x["f"]["dkv"])[:15]
    tc = defaultdict(int)
    for x in top: tc[x["team"]] += 1
    for x in sl: x["f"]["tconc"] = tc[x["team"]] - (1 if x in top else 0)
    rows += sl
SL = sorted({r["slate"] for r in rows})
FEATS = ["sal", "dkv", "l1v", "l3v", "lmin", "mavg", "miya", "imp", "tconc", "gp", "p_dkv", "p_l1v", "p_l3v", "p_lmin", "p_mavg", "p_miya", "p_imp", "p_sal"]
P("rows %d (players not Out, with our ownership) on %d slates; real ownership from %d contests of 100+ entries" % (len(rows), len(SL), len(contest_own)))

def X(r):
    out = [1.0]
    for k in FEATS:
        v = r["f"].get(k)
        out += [0.0 if v is None else float(v), 1.0 if v is None else 0.0] if k in ("dkv", "l1v", "l3v", "lmin", "mavg", "miya", "imp") else [0.0 if v is None else float(v)]
    return out
def fitm(tr):
    A = np.array([X(r) for r in tr]); y = np.array([math.log(r["real"] + 0.5) for r in tr])
    lam = 1.0 * np.eye(A.shape[1]); lam[0, 0] = 0
    return np.linalg.solve(A.T @ A + lam, A.T @ y)
def predict(te, b, cross, blend_w, rescale, expo=1.0, base_key="live"):
    out = {}
    raw_pred = {r["id"]: max(0.0, math.exp(float(np.dot(b, X(r)))) - 0.5) ** expo for r in te}
    below = [r for r in te if r["sal"] * 1000 < cross]
    if rescale and below:
        s_ours = sum(r[base_key] for r in below); s_new = sum(raw_pred[r["id"]] for r in below) or 1.0
        f = s_ours / s_new
        for r in below: raw_pred[r["id"]] *= f
    for r in te:
        s = r["sal"] * 1000
        if s >= cross: out[r["id"]] = r[base_key]
        elif s >= cross - 1000 and blend_w is not None:
            w = (cross - s) / 1000 * blend_w      # weight on the field-side model grows below the crossover
            out[r["id"]] = (1 - w) * r[base_key] + w * raw_pred[r["id"]]
        else: out[r["id"]] = raw_pred[r["id"]]
    return out
def scores(te, pred, lo=0, hi=1e9):
    v = [r for r in te if lo <= r["sal"] * 1000 < hi]
    if not v: return None
    ch = [r for r in v if max(r["real"], pred[r["id"]]) >= 15]
    top_real = sum(sorted((r["real"] for r in te), reverse=True)[:8]); top_pred = sum(sorted(pred.values(), reverse=True)[:8])
    return {"chalk": S.mean(abs(r["real"] - pred[r["id"]]) for r in ch) if ch else None,
            "off10": S.mean(abs(r["real"] - pred[r["id"]]) >= 10 for r in ch) if ch else None,
            "all": S.mean(abs(r["real"] - pred[r["id"]]) for r in v), "conc": top_real - top_pred}
CROSS = [6000, 6500, 7000, 7500, 8000]     # plus $5k below, so the data can push the field-side model down to the cheapest tier only
# expo: a concentration exponent on the field-side prediction (pred^expo, then the rescale), since a log-linear fit
# regresses toward the mean and comes out too flat
CONF = [(c, w, rs, ex) for c in [5000] + CROSS for w in (None, 1.0) for rs in (True, False) for ex in (1.0, 1.5, 2.0, 3.0)]
def chalk_all(sl_rows, b, conf, key="live"):
    out = []
    for s in sl_rows:
        te = [r for r in rows if r["slate"] == s]
        sc = scores(te, predict(te, b[s], *conf, base_key=key))
        out.append(sc["chalk"] if sc["chalk"] is not None else 0)
    return S.mean(out)
# LOSO: per held-out slate, fit the model on the other slates' sub-$8k rows; choose (cross, blend, rescale) by the
# other slates' chalk-band MAE (inner: their own models are fitted with the held-out slate excluded too -> use the
# outer fit for speed: the choice uses only training slates' rows and the training-fitted model).
A_res = defaultdict(lambda: defaultdict(list)); chosen = []; PRED = {}
TIERS = [("< $5k", 0, 5000), ("$5-6k", 5000, 6000), ("$6-7k", 6000, 7000), ("$7k+", 7000, 1e9), ("all", 0, 1e9)]
for h in SL:
    tr = [r for r in rows if r["slate"] != h and r["sal"] < 8.0]
    b = fitm(tr)
    trs = [s for s in SL if s != h]
    def tr_score(conf):
        return S.mean((lambda sc: sc["chalk"] if sc["chalk"] is not None else 0)(scores([r for r in rows if r["slate"] == s], predict([r for r in rows if r["slate"] == s], b, *conf))) for s in trs)
    conf = min(CONF, key=tr_score); chosen.append(conf)
    te = [r for r in rows if r["slate"] == h]
    pr = predict(te, b, *conf); PRED[h] = pr
    for lab, lo, hi in TIERS:
        for key, src in (("new", pr), ("live", {r["id"]: r["live"] for r in te}), ("raw", {r["id"]: r["raw"] for r in te})):
            A_res[lab][key].append(scores(te, src, lo, hi))
P("\n## A. Tiered field-ownership model, leave one slate out (%d slates)" % len(SL))
P("chosen (crossover, blend, rescale, exponent) per fold: %s" % dict(Counter(chosen)))
from collections import Counter
P("crossover chosen: %s" % dict(Counter(c[0] for c in chosen)))
for lab, lo, hi in TIERS:
    P("\n-- %s" % lab)
    for m in ("chalk", "off10", "all", "conc"):
        nv = [x[m] if x else None for x in A_res[lab]["new"]]; lvv = [x[m] if x else None for x in A_res[lab]["live"]]; rw = [x[m] if x else None for x in A_res[lab]["raw"]]
        if m == "conc" and lab != "all": continue
        dl = [b_ - a for a, b_ in zip(nv, lvv) if a is not None and b_ is not None]       # live - new: positive = new better (MAE / off10)
        dr = [b_ - a for a, b_ in zip(nv, rw) if a is not None and b_ is not None]
        if m == "conc":
            dl = [abs(b_) - abs(a) for a, b_ in zip(nv, lvv) if a is not None and b_ is not None]; dr = [abs(b_) - abs(a) for a, b_ in zip(nv, rw) if a is not None and b_ is not None]
        P("  %-6s new %s | live %s | raw %s | gain vs live %s | gain vs raw %s" % (m, lv(nv), lv(lvv), lv(rw), ms(dl), ms(dr)))
# coefficients on all slates (sub-$8k) for the write-up
b_all = fitm([r for r in rows if r["sal"] < 8.0])
names = ["const"]
for k in FEATS: names += [k, k + "_missing"] if k in ("dkv", "l1v", "l3v", "lmin", "mavg", "miya", "imp") else [k]
P("\ncoefficients on all slates (log(real + 0.5), ridge 1): " + ", ".join("%s %+.3f" % (n, c) for n, c in zip(names, b_all) if not n.endswith("_missing")))
# does the field-side model use our projection at all? (independent check) correlation of its prediction with our raw, sub-$7k
cc = []
for h in SL:
    v = [r for r in rows if r["slate"] == h and r["sal"] < 7.0]
    a = [PRED[h][r["id"]] for r in v]; c = [r["raw"] for r in v]
    ma, mc = S.mean(a), S.mean(c)
    cc.append(sum((x - ma) * (y - mc) for x, y in zip(a, c)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mc) ** 2 for y in c)))
P("per-slate r(field-side prediction, our raw ownership), sub-$7k: %s" % lv(cc))

# ---------- B / C: tiered exposure on the builds with board values
P("\n## B / C. Tiered exposure: keep half the kept pool by board value + lambda x (sub-$7k fade gap below predicted field ownership)")
M = E.Mirror(MIRROR)
def ctype(name, n):
    """The one definition (scripts/dk_contest_type.py, the DK page's profile; 2026-11-28). This script reported
    "qualifier/small"; it passes its own size argument, which the page reads as the lobby size."""
    import dk_contest_type
    t = dk_contest_type.contest_type(name, n)
    return "qualifier/small" if t == "qualifier" else t
LAMS = [0.0, 0.5, 1.0, 2.0, 4.0]
build_res = {}
for f in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
    name = os.path.basename(f)[8:-5]; g = name.split("_")[1]
    if name not in SL: continue
    b = json.load(open(f)); pool = b["pool"]; kept = list(b.get("final") or [])
    vals = ((b.get("cut_state") or {}).get("board") or {}).get("values")
    if not kept or not vals or len(vals) != len(kept): continue
    rv = [v[0] if isinstance(v, list) else v for v in vals]
    order = sorted(range(len(kept)), key=lambda i: -rv[i]); vrank = {kept[i]: 1 - j / len(kept) for j, i in enumerate(order)}
    sal = {r["id"]: r["sal"] for r in rows if r["slate"] == name}
    exp = defaultdict(float)
    for k in kept:
        for i in pool[k]: exp[str(i)] += 100.0 / len(kept)
    live = {r["id"]: r["live"] for r in rows if r["slate"] == name}
    fields = {"B (today's ownership)": live, "C (tiered model, A+B)": PRED[name]}
    pts = {r["dk_id"]: num(r.get("actual_dk")) for r in E.read(os.path.join(E.DK, name + ".csv"))}
    contests = []
    for cid, n in ev[g].items():
        if n < 100: continue
        sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(sf): continue
        entries, _ = E.standings(sf)
        _, slate, _ = E.slate_for(M, cid)
        c = next((c for c in (slate or {}).get("contests", []) if str(c["id"]) == cid), None) if slate else None
        if not c: continue
        fdesc = sorted((e["points"] for e in entries), reverse=True)
        contests.append((cid, ctype(c.get("name", ""), len(fdesc)), fdesc, E.pay_table(c.get("payouts"))))
    if not contests: continue
    def res_of(ks):
        out = {}
        for cid, ct, fdesc, table in contests:
            N = len(fdesc); pc = []; pay = []
            for k in ks:
                v = sum(pts.get(str(i)) or 0 for i in pool[k]); pl = E.placed(v, fdesc)
                pc.append(100 * (N - (pl - 1)) / N); pay.append(table.get(pl, 0))
            out[cid] = (ct, S.mean(pc), S.mean(pay))
        return out
    r_ = {"all kept": res_of(kept)}
    for lab, fo in fields.items():
        gap = {str(i): max(0.0, fo.get(str(i), 0.0) - exp[str(i)]) for k in kept for i in pool[k] if (sal.get(str(i)) or 99) < 7.0}
        for lam in LAMS:
            sc = {k: vrank[k] + lam * sum(gap.get(str(i), 0.0) for i in pool[k]) / 100 for k in kept}
            r_[(lab, lam)] = res_of(sorted(kept, key=lambda k: -sc[k])[:len(kept) // 2])
    build_res[name] = r_
BS = sorted(build_res)
P("builds with board values and graded 100+ contests: %d" % len(BS))
def slate_metric(r, metric, ctypes=None):
    v = [(x[1] if metric == "pct" else x[2]) for cid, x in r.items() if ctypes is None or x[0] in ctypes]
    return S.mean(v) if v else None
for lab in ("B (today's ownership)", "C (tiered model, A+B)"):
    P("\n-- %s" % lab)
    lam_ch = []
    out = defaultdict(list)
    for h in BS:
        trn = [s for s in BS if s != h]
        lam = max(LAMS, key=lambda l: (S.mean(slate_metric(build_res[s][(lab, l)], "pct") - slate_metric(build_res[s][(lab, 0.0)], "pct") for s in trn), -l))
        lam_ch.append(lam)
        for metric in ("pct", "pay"):
            for cname, cts in (("all", None), ("flagship", ("flagship",)), ("main", ("main",))):
                c = slate_metric(build_res[h][(lab, lam)], metric, cts); z = slate_metric(build_res[h][(lab, 0.0)], metric, cts); k = slate_metric(build_res[h]["all kept"], metric, cts)
                if c is None: continue
                out[(metric, cname, "vs board top half")].append(c - z); out[(metric, cname, "vs all kept")].append(c - k)
    P("  lambda chosen per fold: %s" % dict(Counter(lam_ch)))
    for (metric, cname, ref), v in sorted(out.items()):
        P("  %-4s %-9s %-18s %s" % (metric, cname, ref, ms(v, 3 if metric == "pay" else 2)))
    # each fixed lambda vs board-only (not held out, the shape)
    for lam in LAMS[1:]:
        P("  fixed lambda %.1f vs board top half: pct %s" % (lam, ms([slate_metric(build_res[s][(lab, lam)], "pct") - slate_metric(build_res[s][(lab, 0.0)], "pct") for s in BS])))
print("\n".join(OUT))
