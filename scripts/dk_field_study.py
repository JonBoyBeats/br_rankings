"""The field study (2026-11-23, the coordinator's spec, the B2 refit extended): what real DraftKings college fields play
against our simulated field, by contest size, and a field builder fitted to it. Analysis only: nothing here changes
the live field (battle-royale-research scripts/dk_cbb_field.py FIELD_STYLES).

Contest-size bands (the operator's, centred on ~1,000 / ~100 / ~10 with the cut-offs at the log midpoints):
  Large 300+ entries, Medium 30-299, Small under 30 (the under-10 contests noted apart, fit with Small).

  measure   every graded contest (br_rankings eval.csv + its standings file) against our ownership at lock
            (data/dk/cbb/<date>_<g>_own.json) and the field as it builds today (FIELD_STYLES, from the projections saved
            at lock): player ownership by salary / ownership band / position / team total; pair and trio lifts (the
            co-occurrence over the product of the marginals) for the top pairs and trios, same team / same game / cross
            game; lineup shape (duplication with another user, salary left, 3+ from a team or a game, punts under
            $3,500, the ownership-sum spread, the most common trio's share)
  fit       candidate builders (style mix, the weight on ours vs DraftKings' average, noise, and a shared-core step:
            a share of lineups built around a popular 2-3 player core taken from a pre-lock pilot field) scored against
            every contest; per band, and left one night out (the held-out check)
  report    the markdown write-up from the saved runs

  python3 scripts/dk_field_study.py measure --brr ../battle-royale-research --out DIR
  python3 scripts/dk_field_study.py fit --brr ../battle-royale-research --out DIR
  python3 scripts/dk_field_study.py report --out DIR [--banks DIR/banks.json]
"""
import argparse, csv, itertools, json, math, os, statistics as S, sys
from collections import Counter, defaultdict
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E                      # noqa: E402  (standings, real_field, field_metrics: the one definitions)

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
BANDS = [("Large", 300, 10 ** 9), ("Medium", 30, 299), ("Small", 0, 29)]
PUNT = 3500
num = lambda v: float(v) if v not in ("", None) else None


def band(n):
    return next(b for b, lo, hi in BANDS if lo <= n <= hi)


def nights():
    """{(date, g): {contest id: name}} from eval.csv (the graded contests)."""
    out = defaultdict(dict)
    for r in E.read(E.EVAL):
        out[(r["date"], str(r["draft_group"]))][r["contest_id"]] = r["contest"]
    return dict(sorted(out.items()))


def load_night(brr, date, g):
    players = json.load(open(os.path.join(brr, "data/dk/cbb", "%s_%s_proj.json" % (date, g))))
    ownf = os.path.join(brr, "data/dk/cbb", "%s_%s_own.json" % (date, g))
    own = json.load(open(ownf)) if os.path.exists(ownf) else {}
    names = defaultdict(list)
    for k, r in players.items():
        names[r["name"]].append(k)
    return players, own, {nm: v[0] for nm, v in names.items() if len(v) == 1}


# --- the measures ---------------------------------------------------------------------------------------------------
def game_of(players, i):
    return players[i].get("game") or players[i].get("team")


def lifts(L, players, top=30):
    """Pairs and trios: {kind: (mean lift of the top pairs by count, weighted by count), ...} split same team / same
    game / cross game, the top trios' mean lift, and the most common trio's share and the top-5 trios' share."""
    n = len(L)
    cnt, pc, tc = Counter(), Counter(), Counter()
    for x in L:
        cnt.update(x)
        s = sorted(x)
        pc.update(itertools.combinations(s, 2))
        tc.update(itertools.combinations(s, 3))
    m = {i: c / n for i, c in cnt.items()}
    out = {}
    tp = pc.most_common(top)
    for kind in ("team", "game", "cross"):
        xs = []
        for (a, b), c in tp:
            same_t = players[a]["team"] == players[b]["team"]
            same_g = game_of(players, a) == game_of(players, b)
            k = "team" if same_t else "game" if same_g else "cross"
            if k == kind:
                xs.append((c / n / (m[a] * m[b]), c))
        out["lift_" + kind] = sum(l * c for l, c in xs) / sum(c for _, c in xs) if xs else None
    out["lift_pairs"] = sum(c / n / (m[a] * m[b]) * c for (a, b), c in tp) / sum(c for _, c in tp) if tp else None
    tt = tc.most_common(20)
    out["lift_trios"] = sum(c / n / (m[a] * m[b] * m[c_]) * c for (a, b, c_), c in tt) / sum(c for _, c in tt) if tt else None
    out["trio1"] = 100 * tt[0][1] / n if tt else 0
    out["trio5"] = 100 * sum(c for _, c in tt[:5]) / n if tt else 0
    out["top_trios"] = [([players[i]["name"] for i in t], round(100 * c / n, 1)) for t, c in tt[:3]]
    return out


def shape(L, U, players, n):
    fm, own = E.field_metrics(L, U, players, n)
    sal = [sum(int(players[i]["salary"]) for i in x) for x in L]
    gm = lambda x: max(Counter(game_of(players, i) for i in x).values()) >= 3
    osum = sorted(sum(own.get(i, 0) for i in x) for x in L)
    q = lambda p: osum[min(len(osum) - 1, int(p * len(osum)))]
    out = {"dup": fm["dup_other"], "left": S.mean(E.CAP_DK - s for s in sal), "left_le1k": 100 * sum(E.CAP_DK - s <= 1000 for s in sal) / len(sal),
           "at_cap": fm["at_cap"], "sal_p10": fm["sal_p10"], "team3": fm["team3"], "game3": 100 * sum(gm(x) for x in L) / len(L),
           "punt1": 100 * sum(any(int(players[i]["salary"]) < PUNT for i in x) for x in L) / len(L),
           "own_p10": q(0.1), "own_p50": q(0.5), "own_p90": q(0.9), "top_own": fm["top_own"]}
    return out, own


def player_gaps(real_own, proj_own, players):
    """Real / projected ownership summed within groups: salary, our ownership band, position, team total."""
    g = defaultdict(lambda: [0.0, 0.0])
    tt = {}
    for i, r in players.items():
        ou, sp = num(r.get("ou")), num(r.get("spread"))
        if ou is not None and sp is not None:
            tt[i] = ou / 2 - sp / 2
    tts = sorted(tt.values())
    cut = (tts[len(tts) // 3], tts[2 * len(tts) // 3]) if tts else (0, 0)
    for i, r in players.items():
        if r.get("status") == "Out":
            continue
        p, x = proj_own.get(i, 0) or 0, real_own.get(i, 0) or 0
        sal = int(r["salary"])
        keys = ["sal " + ("<4k" if sal < 4000 else "4-6k" if sal < 6000 else "6k+"),
                "own " + ("<5" if p < 5 else "5-20" if p < 20 else "20+"),
                "pos " + ("G" if "G" in (r.get("roster") or "").split("/") and "F" not in (r.get("roster") or "").split("/") else
                          "F" if "F" in (r.get("roster") or "").split("/") and "G" not in (r.get("roster") or "").split("/") else "G/F")]
        if i in tt:
            keys.append("team total " + ("low" if tt[i] < cut[0] else "mid" if tt[i] < cut[1] else "high"))
        for k in keys:
            g[k][0] += x; g[k][1] += p
    mae = S.mean(abs((real_own.get(i, 0) or 0) - (proj_own.get(i, 0) or 0)) for i in set(real_own) | set(proj_own) if i in players)
    return {k: (round(v[0] / v[1], 3) if v[1] else None) for k, v in g.items()}, mae


# --- the builder: dk_cbb_field.field, with a shared-core step ---------------------------------------------------------
def no_punts(players):
    """The page's pool rule for the field (dk.html isPunt): a player projected under 15 minutes is left out unless a
    teammate is Out and his minutes are above his average (news)."""
    out_team = {r.get("team") for r in players.values() if r.get("status") == "Out"}
    keep = {}
    for k, r in players.items():
        m, avg = num(r.get("min")) or 0, num(r.get("min_avg"))
        if r.get("status") != "Out" and m < 15 and not (r.get("team") in out_team and avg is not None and m > avg):
            continue
        keep[k] = r
    return keep


def build(brr, players, styles, core, q, seed=7, n=1000, punts=True):
    """n field lineups from the styles; core: share of lineups built around a popular 2-3 player core (from a pre-lock
    pilot field of the same styles: its most common trios and pairs, by count), the rest as dk_cbb_field.field."""
    sys.path.insert(0, os.path.join(brr, "scripts"))
    import numpy as np
    import dk_cbb_field as fld
    from scipy.optimize import Bounds, LinearConstraint, milp
    rng = np.random.default_rng(seed)
    if not punts:
        players = no_punts(players)
    if not core:
        L, _ = fld.field(players, rng, styles, n=n, q=q)
        return [tuple(sorted(x)) for x in L]
    pilot, _ = fld.field(players, np.random.default_rng(seed + 1), styles, n=300, q=q)
    tc, pc = Counter(), Counter()
    for x in pilot:
        s = sorted(x); tc.update(itertools.combinations(s, 3)); pc.update(itertools.combinations(s, 2))
    cores = [(t, c) for t, c in tc.most_common(15)] + [(t, c) for t, c in pc.most_common(15)]
    cw = np.array([c for _, c in cores], dtype=float)
    ids = [k for k, r in players.items() if r.get("status") != "Out" and r.get("fp_dk") is not None]
    ix = {k: j for j, k in enumerate(ids)}
    qm = np.array([q if players[k].get("status") == "Questionable" else 1.0 for k in ids])
    ours = np.array([players[k]["fp_dk"] for k in ids]) * qm
    avg = np.array([players[k]["dk_avg"] or players[k]["fp_dk"] for k in ids]) * qm
    sal = np.array([players[k]["salary"] for k in ids], dtype=float)
    gg = np.array([fld.eligible(players[k]["roster"], "G") for k in ids], dtype=float)
    ff = np.array([fld.eligible(players[k]["roster"], "F") for k in ids], dtype=float)
    A = np.vstack([np.ones(len(ids)), gg, ff, sal])
    share = np.array([st["share"] for st in styles], dtype=float)
    out = []
    for _ in range(n):
        st = styles[rng.choice(len(styles), p=share / share.sum())]
        base = st["w"] * ours + (1 - st["w"]) * avg
        c = -np.maximum(0.0, base * (1 + st["noise"] * rng.standard_normal(len(ids))))
        lo = np.zeros(len(ids))
        if rng.random() < core:
            t = cores[rng.choice(len(cores), p=cw / cw.sum())][0]
            for k in t:
                if k in ix:
                    lo[ix[k]] = 1
        res = milp(c, constraints=LinearConstraint(A, [8, 3, 3, st.get("min_sal", 0)], [8, np.inf, np.inf, fld.CAP]),
                   integrality=np.ones(len(ids)), bounds=Bounds(lo, 1))
        if not res.success:
            continue
        out.append(tuple(sorted(ids[i] for i in np.flatnonzero(res.x > 0.5))))
    return out


# the candidates: the main style's weight on ours and noise (the steepness), the chalk style's share, the core share
def candidates(current):
    out = [("current", current, 0.0)]
    for vw in (0.5, 0.25):
        for vn in (0.25, 0.4):
            for ca in (0.2, 0.3):
                for core in (0.0, 0.2, 0.4):
                    st = [{"share": ca, "w": 0.0, "noise": 0.06, "min_sal": 0}, {"share": 1 - ca, "w": vw, "noise": vn, "min_sal": 0}]
                    out.append(("w%.2f n%.2f chalk%.1f core%.1f" % (vw, vn, ca, core), st, core))
    # the second grid (after the first fit): the chalk style at the B2 refit's noise 0.08, on DraftKings' average or half
    # ours, and the field without punts (the first grid's fields all played a sub-$3,500 punt about twice as often as real)
    for cw in (0.0, 0.5):
        for ca in (0.2, 0.3):
            for core in (0.0, 0.2):
                for punts in (True, False):
                    st = [{"share": ca, "w": cw, "noise": 0.08, "min_sal": 0}, {"share": 1 - ca, "w": 0.5, "noise": 0.25, "min_sal": 0}]
                    out.append(("chalk%.1f cw%.1f cn.08 core%.1f%s" % (ca, cw, core, "" if punts else " nopunt"), st, core, punts))
    return out


def _job(args):
    brr, date, g, label, styles, core, q = args[:7]
    punts = args[7] if len(args) > 7 else True
    players, _, _ = load_night(brr, date, g)
    return (date, g, label), build(brr, players, styles, core, q, punts=punts)


def real_fields(nts, brr):
    out = {}
    for (date, g), cids in nts.items():
        players, own, byname = load_night(brr, date, g)
        for cid, name in cids.items():
            path = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
            if not os.path.exists(path):
                continue
            L, U, total = E.real_field(path, byname)
            if len(L) >= 2:
                out[(date, g, cid)] = {"name": name, "L": L, "U": U, "entries": total, "band": band(total)}
    return out


def measures(L, U, players, n, proj_own=None):
    sh, own = shape(L, U, players, n)
    d = dict(sh); d.update({k: v for k, v in lifts(L, players).items()})
    return d, own


def score(sim, real, own_mae):
    """The fit's gap: ownership, pair and trio lifts, duplication, salary, stacks, each over its scale."""
    rel = lambda k, s=None: abs((sim[k] or 0) - (real[k] or 0)) / (s or max(abs(real[k] or 0), 1))
    return (own_mae / 3 + rel("dup") + rel("lift_pairs") + rel("lift_trios") + rel("at_cap") + rel("team3") + rel("punt1")
            + abs(sim["sal_p10"] - real["sal_p10"]) / 500)


def measure(a):
    os.makedirs(a.out, exist_ok=True)
    nts = nights()
    R = real_fields(nts, a.brr)
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import dk_cbb_field as fld
    q = fld.q_factor(os.path.join(DK, "gate.json"))
    jobs = [(a.brr, d, g, "current", fld.FIELD_STYLES, 0.0, q) for d, g in nts]
    with Pool(min(4, os.cpu_count() or 1)) as P:
        sims = dict(P.map(_job, jobs))
    rows = []
    for (date, g, cid), x in R.items():
        players, own, _ = load_night(a.brr, date, g)
        n = min(len(x["L"]), 1000)
        rm, rown = measures(x["L"], x["U"], players, n)
        sm, sown = measures(sims[(date, g, "current")], None, players, n)
        gaps, mae = player_gaps(rown, own, players)
        rows.append({"date": date, "g": g, "cid": cid, "name": x["name"], "entries": x["entries"], "band": x["band"], "matched": len(x["L"]),
                     "under10": x["entries"] < 10, "real": rm, "sim": sm, "gaps": gaps, "own_mae": mae,
                     "sim_own_mae": S.mean(abs(sown.get(i, 0) - rown.get(i, 0)) for i in set(rown) | set(sown))})
        print("measured %s %s %s (%s, %d entries)" % (date, g, cid, x["band"], x["entries"]), file=sys.stderr)
    json.dump(rows, open(os.path.join(a.out, "measure.json"), "w"), default=str)


def fit(a):
    nts = nights()
    R = real_fields(nts, a.brr)
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import dk_cbb_field as fld
    q = fld.q_factor(os.path.join(DK, "gate.json"))
    C = candidates(fld.FIELD_STYLES)
    jobs = [(a.brr, d, g) + tuple(c) + (q,) if len(c) == 3 else (a.brr, d, g, c[0], c[1], c[2], q, c[3]) for c in C for d, g in nts]
    cache = os.path.join(a.out, "fields.json")
    have = json.load(open(cache)) if os.path.exists(cache) else {}
    todo = [j for j in jobs if "|".join((j[1], j[2], j[3])) not in have]
    print("%d candidates x %d nights; %d field builds to run" % (len(C), len(nts), len(todo)), file=sys.stderr)
    with Pool(min(4, os.cpu_count() or 1)) as P:
        for k, L in P.imap_unordered(_job, todo):
            have["|".join(k)] = L
            json.dump(have, open(cache, "w"))
            print("built %s" % "|".join(k), file=sys.stderr, flush=True)
    out = []
    for c in C:
        lab, st, core = c[:3]
        for (date, g, cid), x in R.items():
            players, _, _ = load_night(a.brr, date, g)
            L = [tuple(v) for v in have["|".join((date, g, lab))]]
            n = min(len(x["L"]), 1000)
            rm, rown = measures(x["L"], x["U"], players, n)
            sm, sown = measures(L, None, players, n)
            mae = S.mean(abs(sown.get(i, 0) - rown.get(i, 0)) for i in set(rown) | set(sown))
            out.append({"label": lab, "styles": st, "core": core, "date": date, "g": g, "cid": cid, "band": x["band"], "entries": x["entries"],
                        "score": score(sm, rm, mae), "own_mae": mae, "real": {k: rm[k] for k in rm if k != "top_trios"},
                        "sim": {k: sm[k] for k in sm if k != "top_trios"}})
    json.dump(out, open(os.path.join(a.out, "fit.json"), "w"))
    print("fit rows: %d" % len(out), file=sys.stderr)


# --- the banks: the cut against the current field and the calibrated one ----------------------------------------------
def banks(a):
    """Each night's largest graded contest with a payout table: one rule-free bank (scripts/dk_field_study.js), cut to
    KEEP against the current field and against the calibrated one (label: the setting chosen for the contest's band, or
    one shared), the kept lineups scored on real results."""
    import subprocess, tempfile
    import dk_sit as K
    fields = json.load(open(os.path.join(a.out, "fields.json")))
    choice = dict(x.split("=", 1) for x in a.labels.split(";"))
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import dk_cbb_field as fld
    R = real_fields(nights(), a.brr)
    rows, summary, todo = [], [], []
    for (date, g) in sorted({(d, g) for d, g, _ in R}):
        players, _, byname = load_night(a.brr, date, g)
        sl, _ = K.lock_doc(a.mirror, "dk_cbb_morning.json", date, g)
        cs = [(cid, x) for (d, gg, cid), x in R.items() if (d, gg) == (date, g)]
        cs = [(cid, x, E.contest_info(sl, cid)) for cid, x in cs]
        cs = [c for c in cs if c[2] and c[2].get("payouts")]
        if not cs:
            continue
        cid, x, con = max(cs, key=lambda c: c[1]["entries"])
        lab = choice.get(x["band"]) or choice.get("shared")
        F = {"current": fields["|".join((date, g, "current"))], "calibrated": fields["|".join((date, g, lab))]}
        inp = {"players": players, "z": fld.SIM_Z, "contest": {"size": con.get("size") or x["entries"], "entry_fee": con.get("entry_fee"), "payouts": con["payouts"]},
               "fields": F, "bank": a.bank, "keep": a.keep, "cut": a.cut, "nights": a.nights, "seed": int(g)}
        fi, fo = os.path.join(a.out, "bank_in_%s_%s.json" % (date, g)), os.path.join(a.out, "bank_out_%s_%s.json" % (date, g))
        json.dump(inp, open(fi, "w"))
        todo.append((fi, fo, date, g, cid, x, con, lab))
    from concurrent.futures import ThreadPoolExecutor
    run = lambda t: os.path.exists(t[1]) or subprocess.run(["node", os.path.join(HERE, "dk_field_study.js"), t[0], t[1]], check=True)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(run, todo))
    for fi, fo, date, g, cid, x, con, lab in todo:
        players, _, byname = load_night(a.brr, date, g)
        res = json.load(open(fo))
        act = {r["dk_id"]: float(r["actual_dk"] or 0) for r in csv.DictReader(open(os.path.join(DK, "%s_%s.csv" % (date, g))))}
        ents, ownr = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
        pts = sorted((e["points"] for e in ents), reverse=True)
        t10 = pts[math.ceil(0.1 * len(pts)) - 1]
        cash = pts[min(max(E.pay_table(con["payouts"])), len(pts)) - 1]
        asc = sorted(pts)
        real = set(x["L"])
        idown = {byname[nm]: v[0] for nm, v in ownr.items() if nm in byname and v[0] is not None}
        keeps = {}
        for f in ("current", "calibrated"):
            K_ = [res["bank"][i] for i in res["keep"][f]]
            keeps[f] = {tuple(sorted(L)) for L in K_}
            sc = [sum(act.get(i, 0) for i in L) for L in K_]
            rows.append({"night": "%s %s" % (date, g), "contest": "%s (%d, %s)" % (x["name"][:26], x["entries"], x["band"]), "field": f + ("" if f == "current" else " (" + lab + ")"),
                         "n": len(K_), "t10": S.mean(v >= t10 for v in sc), "cash": S.mean(v >= cash for v in sc),
                         "pctl": S.mean(sum(1 for p in asc if p < v) / len(asc) for v in sc),
                         "in_real": S.mean(tuple(sorted(L)) in real for L in K_), "own_sum": S.mean(sum(idown.get(i, 0) for i in L) for L in K_)})
        both = len(keeps["current"] & keeps["calibrated"])
        summary.append({"night": "%s %s" % (date, g), "overlap": both / max(1, len(keeps["current"]))})
        print("banks %s %s: %s" % (date, g, rows[-2:]), file=sys.stderr)
    cur = [r for r in rows if r["field"] == "current"]; cal = [r for r in rows if r["field"] != "current"]
    w = lambda k: sum(1 for c, d in zip(cur, cal) if d[k] > c[k] + 1e-9)
    l = lambda k: sum(1 for c, d in zip(cur, cal) if d[k] < c[k] - 1e-9)
    txt = ("Pooled over %d nights (thin): top 10%% %.1f%% -> %.1f%%, cash %.1f%% -> %.1f%%, percentile %.1f -> %.1f; calibrated better / worse on top 10%% %d / %d, "
           "cash %d / %d, percentile %d / %d nights. Kept lineups the real field also held: %.1f%% -> %.1f%%; their real ownership sum %.0f -> %.0f. "
           "The two cuts keep the same lineups %.0f%% of the time (mean over nights)." % (
               len(cur), 100 * S.mean(r["t10"] for r in cur), 100 * S.mean(r["t10"] for r in cal), 100 * S.mean(r["cash"] for r in cur), 100 * S.mean(r["cash"] for r in cal),
               100 * S.mean(r["pctl"] for r in cur), 100 * S.mean(r["pctl"] for r in cal), w("t10"), l("t10"), w("cash"), l("cash"), w("pctl"), l("pctl"),
               100 * S.mean(r["in_real"] for r in cur), 100 * S.mean(r["in_real"] for r in cal), S.mean(r["own_sum"] for r in cur), S.mean(r["own_sum"] for r in cal),
               100 * S.mean(x["overlap"] for x in summary)))
    json.dump({"rows": rows, "summary": txt, "overlap": summary}, open(os.path.join(a.out, "banks.json"), "w"))
    print(txt)


# --- the write-up -----------------------------------------------------------------------------------------------------
def report(a):
    M = json.load(open(os.path.join(a.out, "measure.json")))
    F = json.load(open(os.path.join(a.out, "fit.json")))
    B = json.load(open(a.banks)) if a.banks and os.path.exists(a.banks) else None
    L = ["# The field study: real DraftKings college fields against ours, by contest size (2026-11-23)", "",
         "Generated by `scripts/dk_field_study.py` (+ `.js` for the banks). Analysis only: the live field (FIELD_STYLES) is unchanged. "
         "Bands: Large 300+ entries, Medium 30-299, Small under 30 (under-10 contests noted, fit with Small). "
         "Every graded contest with a standings file: %d contests on %d nights (%s). Thin: one to two weeks of slates." % (
             len(M), len({(r["date"], r["g"]) for r in M}), ", ".join(sorted({"%s %s" % (r["date"], r["g"]) for r in M}))), ""]
    L += ["## Counts by band", "", "| Band | Contests | Nights | Entries (median) | Under 10 |", "|---|---|---|---|---|"]
    for b, _, _ in BANDS:
        rs = [r for r in M if r["band"] == b]
        L.append("| %s | %d | %d | %s | %d |" % (b, len(rs), len({(r["date"], r["g"]) for r in rs}), int(S.median(r["entries"] for r in rs)) if rs else "-",
                                                 sum(r["under10"] for r in rs)))
    keys = [("dup", "duplication %"), ("left", "salary left $"), ("left_le1k", "<= $1k left %"), ("at_cap", "at the cap %"), ("team3", "3+ one team %"),
            ("game3", "3+ one game %"), ("punt1", "a punt (<$3.5k) %"), ("own_p10", "own-sum p10"), ("own_p50", "own-sum p50"), ("own_p90", "own-sum p90"),
            ("top_own", "top owned %"), ("lift_pairs", "top-30 pair lift"), ("lift_team", "  same team"), ("lift_game", "  same game"), ("lift_cross", "  cross game"),
            ("lift_trios", "top-20 trio lift"), ("trio1", "most common trio %"), ("trio5", "top-5 trios %")]
    L += ["", "## Real against the current field, by band (real / sim, contests averaged)", "",
          "| Measure | " + " | ".join(b for b, _, _ in BANDS) + " |", "|---|" + "---|" * len(BANDS)]
    for k, lab in keys:
        cells = []
        for b, _, _ in BANDS:
            rs = [r for r in M if r["band"] == b and r["real"].get(k) is not None and r["sim"].get(k) is not None]
            cells.append("%.2f / %.2f" % (S.mean(r["real"][k] for r in rs), S.mean(r["sim"][k] for r in rs)) if rs else "-")
        L.append("| %s | %s |" % (lab, " | ".join(cells)))
    gk = sorted({k for r in M for k in r["gaps"]})
    L += ["", "## Players: real / our projected ownership, summed within each group, by band", "",
          "| Group | " + " | ".join(b for b, _, _ in BANDS) + " |", "|---|" + "---|" * len(BANDS)]
    for k in gk:
        cells = []
        for b, _, _ in BANDS:
            xs = [r["gaps"][k] for r in M if r["band"] == b and r["gaps"].get(k) is not None]
            cells.append("%.2f" % S.mean(xs) if xs else "-")
        L.append("| %s | %s |" % (k, " | ".join(cells)))
    L.append("| ownership miss (pts, ours at lock) | %s |" % " | ".join("%.2f" % S.mean(r["own_mae"] for r in M if r["band"] == b) if any(r["band"] == b for r in M) else "-" for b, _, _ in BANDS))
    under = [r for r in M if r["under10"]]
    if under:
        L += ["", "Under-10 contests (%d): duplication %.1f%% real, 3+ one team %.1f%%, a punt %.1f%%, own-sum p50 %.0f (Small overall: %.1f%%, %.1f%%, %.1f%%, %.0f)." % (
            len(under), S.mean(r["real"]["dup"] for r in under), S.mean(r["real"]["team3"] for r in under), S.mean(r["real"]["punt1"] for r in under),
            S.mean(r["real"]["own_p50"] for r in under), *[S.mean(r["real"][k] for r in M if r["band"] == "Small") for k in ("dup", "team3", "punt1", "own_p50")])]
    L += ["", "## Common cores (the top trios, real), the largest contest each night", ""]
    for (d, g) in sorted({(r["date"], r["g"]) for r in M}):
        r = max((x for x in M if (x["date"], x["g"]) == (d, g)), key=lambda x: x["entries"])
        L.append("- %s %s, %s (%d): %s" % (d, g, r["name"], r["entries"], "; ".join("%s %.1f%%" % (" + ".join(t), s) for t, s in r["real"]["top_trios"])))
    # the fit, scored on band means: each measure averaged over the band's contests, real against sim, then the gap
    # (a contest-by-contest average of relative gaps lets one quiet contest swamp the band: 11-22's 3.5% duplication)
    labs = sorted({f["label"] for f in F})
    keys_ = ["dup", "lift_pairs", "lift_trios", "at_cap", "team3", "punt1", "sal_p10"]
    def bscore(xs):
        if not xs:
            return None
        rm = {k: S.mean(x["real"][k] or 0 for x in xs) for k in keys_}; sm = {k: S.mean(x["sim"][k] or 0 for x in xs) for k in keys_}
        return score(sm, rm, S.mean(x["own_mae"] for x in xs))
    by = defaultdict(list)
    for f in F:
        by[(f["label"], f["band"])].append(f)
    L += ["", "## The fit, scored on band means (lower is better; the current field and the best five per band)", ""]
    best = {}
    for b, _, _ in BANDS:
        sc = sorted((bscore(by[(lab, b)]), lab) for lab in labs if by[(lab, b)])
        if not sc:
            continue
        best[b] = sc[0][1]
        # the noise of the best's band score: by night, half the nights against the other half
        nb = sorted({(x["date"], x["g"]) for x in by[(sc[0][1], b)]})
        halves = [bscore([x for x in by[(sc[0][1], b)] if (x["date"], x["g"]) in set(nb[k::2])]) for k in (0, 1)]
        L.append("**%s** (%d contests, %d nights): current %.3f; best %s (its two halves of nights %s)." % (
            b, len(by[("current", b)]), len(nb), bscore(by[("current", b)]), ", ".join("%s %.3f" % (l, v) for v, l in sc[:5]),
            " / ".join("%.3f" % h for h in halves if h is not None)))
        for lab in (sc[0][1], "current"):
            bx = by[(lab, b)]
            m = lambda side, k: S.mean(x[side][k] or 0 for x in bx)
            L.append("  %s vs real: dup %.1f/%.1f%%, pair lift %.2f/%.2f, trio lift %.2f/%.2f, most common trio %.1f/%.1f%%, at cap %.1f/%.1f%%, 3+ team %.1f/%.1f%%, punt %.1f/%.1f%%, own-sum p50 %.0f/%.0f, own miss %.2f." % (
                lab, m("sim", "dup"), m("real", "dup"), m("sim", "lift_pairs"), m("real", "lift_pairs"), m("sim", "lift_trios"), m("real", "lift_trios"),
                m("sim", "trio1"), m("real", "trio1"), m("sim", "at_cap"), m("real", "at_cap"), m("sim", "team3"), m("real", "team3"),
                m("sim", "punt1"), m("real", "punt1"), m("sim", "own_p50"), m("real", "own_p50"), S.mean(x["own_mae"] for x in bx)))
    L += ["", "Each band's best on every band (band-mean score):", "", "| Setting | " + " | ".join(b for b, _, _ in BANDS) + " |", "|---|" + "---|" * len(BANDS)]
    for b, lab in best.items():
        L.append("| %s (%s's best) | %s |" % (lab, b, " | ".join("%.3f" % bscore(by[(lab, bb)]) if by[(lab, bb)] else "-" for bb, _, _ in BANDS)))
    allsc = sorted((S.mean(bscore(by[(lab, bb)]) for bb, _, _ in BANDS if by[(lab, bb)] and bb != "Small"), lab) for lab in labs)
    L.append("| %s (one setting: best over Large and Medium) | %s |" % (allsc[0][1], " | ".join("%.3f" % bscore(by[(allsc[0][1], bb)]) if by[(allsc[0][1], bb)] else "-" for bb, _, _ in BANDS)))
    L.append("| current | %s |" % " | ".join("%.3f" % bscore(by[("current", bb)]) if by[("current", bb)] else "-" for bb, _, _ in BANDS))
    # held out by night: chosen on the other nights' band means, scored on the night's own contests (its band means)
    L += ["", "## Held out by night (chosen without the night, on band means; scored on the night)", "",
          "| Night | Band | Chosen | Its score | Current |", "|---|---|---|---|---|"]
    ns = sorted({(f["date"], f["g"]) for f in F})
    res = defaultdict(list)
    for nt in ns:
        for b, _, _ in BANDS:
            if b == "Small":
                continue
            here = [f for f in F if (f["date"], f["g"]) == nt and f["band"] == b]
            if not here:
                continue
            other = defaultdict(list)
            for f in F:
                if (f["date"], f["g"]) != nt and f["band"] == b:
                    other[f["label"]].append(f)
            ch = min(other, key=lambda lab: bscore(other[lab]))
            s_ch = bscore([x for x in here if x["label"] == ch]); s_cur = bscore([x for x in here if x["label"] == "current"])
            res[b].append((s_ch, s_cur, ch))
            L.append("| %s %s | %s | %s | %.3f | %.3f |" % (nt[0], nt[1], b, ch, s_ch, s_cur))
    for b, v in res.items():
        L.append("")
        L.append("%s held out: the chosen setting beats the current on %d of %d nights; mean score %.3f vs %.3f; chosen most often: %s." % (
            b, sum(1 for x, y, _ in v if x < y), len(v), S.mean(x for x, _, _ in v), S.mean(y for _, y, _ in v), Counter(c for _, _, c in v).most_common(1)[0][0]))
    if B:
        L += ["", "## Banks cut against each field (rule-free banks at noise 0.35, the same seed; the cut's kept lineups on real results)", "",
              "| Night | Contest | Field | Kept | Top 10% | Cash | Percentile | Kept in the real field (duplicated) | Kept own-sum (real) |", "|---|---|---|---|---|---|---|---|---|"]
        for r in B["rows"]:
            L.append("| %s | %s | %s | %d | %.1f%% | %.1f%% | %.1f | %.1f%% | %.0f |" % (r["night"], r["contest"], r["field"], r["n"], 100 * r["t10"], 100 * r["cash"], 100 * r["pctl"], 100 * r["in_real"], r["own_sum"]))
        L += ["", B["summary"]]
    open(os.path.join(DK, "field_study_2026-11-23.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("measure", "fit"):
        p = sub.add_parser(c); p.add_argument("--brr", default=os.path.join(HERE, "..", "..", "battle-royale-research")); p.add_argument("--out", required=True)
    p = sub.add_parser("report"); p.add_argument("--out", required=True); p.add_argument("--banks")
    p = sub.add_parser("banks"); p.add_argument("--brr", default=os.path.join(HERE, "..", "..", "battle-royale-research")); p.add_argument("--out", required=True)
    p.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror")); p.add_argument("--labels", required=True, help="Large=label;Medium=label;shared=label")
    p.add_argument("--bank", type=int, default=2000); p.add_argument("--keep", type=int, default=200); p.add_argument("--nights", type=int, default=500)
    p.add_argument("--cut", type=float, default=0.25)
    a = ap.parse_args()
    {"measure": measure, "fit": fit, "report": report, "banks": banks}[a.cmd](a)
