"""The points-per-minute half rebuilt from a clean base (2026-11-25, the operator's method: every fix re-earns its place;
the design principle: projection = tonight's minutes x tonight's DraftKings points a minute, nothing multiplying the
final number from outside).

CLEAN BASE: his per-category per-minute rates this season (points, rebounds, assists, steals, blocks, threes made,
turnovers; ESPN box scores of every D1 game before the slate), each with PM minutes of a simple prior (the league's
per-minute rate for players at his salary band), DraftKings-scored (points 1, threes +0.5, rebounds 1.25, assists 1.5,
steals 2, blocks 2, turnovers -0.5). Minutes: the rebuilt minutes half (dk_qmin_rebuild.py, held out), so these tests
run on top of it. PM is the base's one parameter, chosen on the other slates.

FIXES AND LAYERS (each added alone to the current set, held out by slate; forward selection by the largest gain, then a
backward check; a fix's parameter chosen on the other slates):
  miya_prior   EvanMiya's DraftKings points a minute (MIYA_DK) as the prior in place of the simple one
  carry        last season's rate through CARRY (stayed / transfer) as the prior (with miya_prior: MIYA_W blend)
  miya_rate    EvanMiya as an ongoing rate: (1 - w) x his rate + w x EvanMiya's (MIYA_RATE_W)
  form_raw     FORM recency weights (decay per game back) on his raw games (today's FORM on points a minute)
  form_clean   L2: the same weights on his competitive minutes only (QMIN's states, clean games)
  vegas_last   today's implied-total factor: team implied total against LAST season's points a game, slope fitted
  vegas_this   L4: against THIS season's schedule-adjusted scoring, faded from last season by games played
  game_adj     GAME_ADJ by the spread, inside points a minute
  dd           the double-double bonus from his per-category rates and tonight's minutes (dd_chance, DD_BONUS)
  gate         the DraftKings-average gate at $6k+: w x ours + (1 - w) x DraftKings' season average
  opp_<cat>    L3: the opponent's allowed rate in that category against what his opponents usually produce,
               schedule-adjusted and shrunk by K pseudo-games, applied as factor^alpha

Graded on the banded grade (dk_proj_grade.py's bands, by TODAY's projection so every candidate is scored on the same
players): STARS (25+) points MAE the headline, ROTATION (10-25) points MAE second; the Lab's bar (better on 10+ of 14
and a mean gain over 2 x SE), the other band not worse beyond noise.

  python3 scripts/dk_ppm_study.py assemble --brr ../battle-royale-research --boxes DIR --qmin DIR --rb rb_mins.json --out data.json
  python3 scripts/dk_ppm_study.py select --data data.json --out result.json [--md OUT]
"""
import argparse, csv, glob, json, math, os, statistics as S, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
CATS = ("pts", "tpm", "reb", "ast", "stl", "blk", "to")
DKW = {"pts": 1.0, "tpm": 0.5, "reb": 1.25, "ast": 1.5, "stl": 2.0, "blk": 2.0, "to": -0.5}
SAL_BANDS = [(0, 4000), (4000, 5000), (5000, 6000), (6000, 7500), (7500, 99999)]
STARS, ROT = 25.0, 10.0


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def dkpts(st):
    return sum(DKW[c] * st.get(c, 0.0) for c in CATS)


# ---------------------------------------------------------------- assemble
def load_boxes(d):
    out = {}
    for f in glob.glob(os.path.join(d, "*.json")):
        b = json.load(open(f))
        if b.get("p"):
            out[b["id"]] = b
    return out


def careers(ids, cache, nightly):
    """{espn id: career} through cbb_nightly.career, cached on disk."""
    import concurrent.futures as cf
    os.makedirs(cache, exist_ok=True)

    def one(a):
        p = os.path.join(cache, a + ".json")
        if os.path.exists(p):
            return a, json.load(open(p))
        try:
            c = nightly.career(a) or {}
        except Exception:
            c = {}
        json.dump(c, open(p, "w"))
        return a, c
    with cf.ThreadPoolExecutor(12) as ex:
        return dict(ex.map(one, sorted(ids)))


def assemble(a):
    sys.path.insert(0, os.path.join(a.brr, "scripts"))
    import cbb_nightly as cn
    sys.path.insert(0, HERE)
    import dk_qmin_study as q
    boxes = load_boxes(a.boxes)
    games = q.load_games(os.path.join(a.qmin, "data"))
    st = json.load(open(os.path.join(a.qmin, "out2.json")))
    P0 = (st["wp0"]["sig"], 0.0, st["wp0"]["eps"])
    q.PMODE.update(wp0=P0)
    pp = q.clean_games(games, P0, "wp0")[0]
    comp = {(p, g["gid"]): g["on"].get("COMP", 0.0) / 60.0 for p, gl in pp.items() for g in gl}
    rb = json.load(open(a.rb))
    tf = json.load(open(cn.TEAM_STRENGTH))
    last_ppg, strength = tf["points"], tf["teams"]
    # per player: his box games; per team: per game, what it scored and allowed by category
    pg = defaultdict(list)
    tg = defaultdict(list)
    for b in boxes.values():
        tids = list(b["teams"])
        tot = {t: defaultdict(float) for t in tids}
        for pid, s in b["p"].items():
            if s["t"] in tot:
                for c in CATS + ("min", "fga", "fta"):
                    tot[s["t"]][c] += s.get(c, 0.0)
            pg[pid].append({"date": b["date"], "gid": b["id"], "t": s["t"], "min": s["min"], **{c: s.get(c, 0.0) for c in CATS},
                            "comp": comp.get((pid, b["id"]))})
        if len(tids) == 2:
            for t in tids:
                o = [x for x in tids if x != t][0]
                tg[t].append({"date": b["date"], "opp": o, "for": dict(tot[t]), "against": dict(tot[o]),
                              "pts_for": b["teams"][t]["score"], "pts_against": b["teams"][o]["score"]})
    for v in pg.values():
        v.sort(key=lambda x: x["date"])
    for v in tg.values():
        v.sort(key=lambda x: x["date"])
    ev_teams = {i: list(b["teams"]) for i, b in boxes.items()}
    rows_out, ids = [], set()
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        name = os.path.basename(f)[:-4]
        if name not in rb:
            continue
        pj = json.load(open(os.path.join(a.brr, "data", "dk", "cbb", name + "_proj.json")))
        before = min(r["game_start"] for r in pj.values() if r.get("game_start"))
        for r in csv.DictReader(open(f)):
            k = r["dk_id"]
            if k not in rb[name] or (num(r.get("fp_dk")) or 0) <= 0 or num(r.get("actual_dk")) is None:
                continue
            p = pj.get(k, {})
            espn = str(r.get("espn") or p.get("espn") or "")
            team = str(p.get("espn_team") or "")
            ev = str(p.get("event") or "")
            opp = next((t for t in ev_teams.get(ev, []) if t != team), None)
            ids.add(espn)
            rows_out.append({"slate": name, "before": before, "dk_id": k, "espn": espn, "name": r["name"], "team": team, "opp": opp,
                             "salary": num(r["salary"]), "pos": r.get("position"), "fp_dk": num(r["fp_dk"]), "min_proj": num(r["min_proj"]),
                             "ppm_proj": num(r.get("ppm_proj")), "spread": num(p.get("spread")), "ou": num(p.get("ou")), "dk_avg": num(p.get("dk_avg")),
                             "miya": p.get("miya_ppm"), "moved": p.get("moved"), "m_rb": rb[name][k][0], "actual": num(r["actual_dk"]),
                             "min": num(r.get("min")), "status": r.get("status") or p.get("status"), "p_dd": num(r.get("p_dd"))})
    car = careers(ids, os.path.join(a.cache), cn)
    json.dump({"rows": rows_out, "pg": {k: v for k, v in pg.items() if k in ids}, "tg": tg, "careers": car,
               "last_ppg": last_ppg, "strength": strength, "carry": cn.CARRY, "carry_min": cn.CARRY_MIN, "jump_cap": cn.JUMP_CAP,
               "game_adj": cn.GAME_ADJ, "dd_table": cn.DD_TABLE, "dd_bonus": cn.DD_BONUS, "season": cn.SEASON,
               "prior_gp": cn.PRIOR_GP}, open(a.out, "w"))
    print("rows", len(rows_out), "players", len(ids), "slates", len({r["slate"] for r in rows_out}))


# ---------------------------------------------------------------- model
GRIDS = {
    "base": [{"pm": 30}, {"pm": 90}, {"pm": 200}],
    "miya_prior": [{"w": 1.0}],
    "carry": [{"w": 0.0}, {"w": 0.5}],          # w: EvanMiya's share of the prior when miya_prior is in (MIYA_W)
    "miya_rate": [{"w": 0.2}, {"w": 0.35}, {"w": 0.5}],
    "form_raw": [{"d": 0.9}, {"d": 0.8}, {"d": 0.7}],
    "form_clean": [{"d": 1.0}, {"d": 0.9}, {"d": 0.8}],
    "vegas_last": [{"s": 0.006}, {"s": 0.012}, {"s": 0.018}],
    "vegas_this": [{"s": s, "k": k} for s in (0.006, 0.012, 0.018) for k in (0.01, 3, 8)],
    "game_adj": [{}],
    "dd": [{}],
    "gate": [{"w": 0.75}, {"w": 0.5}],
}
OPP_CATS = ("pts", "tpm", "reb", "ast", "stl", "blk", "to")
for _c in OPP_CATS:
    GRIDS["opp_" + _c] = [{"k": k, "a": al} for k in (3, 8) for al in (0.5, 1.0)]
GRIDS["opp_all"] = [{"k": k, "a": al} for k in (3, 8) for al in (0.5, 1.0)]
IN_OLD = {"miya_prior": True, "carry": True, "miya_rate": True, "form_raw": True, "form_clean": False, "vegas_last": True,
          "vegas_this": False, "game_adj": True, "dd": True, "gate": True, "opp_all": False, **{"opp_" + c: False for c in OPP_CATS}}
EXCLUSIVE = [("form_raw", "form_clean"), ("vegas_last", "vegas_this")] + [("opp_all", "opp_" + c) for c in OPP_CATS]


def p_at_least(lam, k=10, step=1):
    mu, need = lam / step, math.ceil(k / step)
    if mu <= 0:
        return 0.0
    term, cdf = math.exp(-mu), 0.0
    for i in range(need):
        cdf += term
        term *= mu / (i + 1)
    return max(0.0, 1 - cdf)


def dd_chance(rates, minutes, table):
    if not minutes:
        return 0.0
    lam = {k: rates[k] * minutes for k in ("pts", "reb", "ast")}
    a, b, c = p_at_least(lam["pts"], step=2), p_at_least(lam["reb"]), p_at_least(lam["ast"])
    raw = a * b + a * c + b * c - 2 * a * b * c
    return next(p for edge, p in table if raw < edge)


def band_of(sal):
    return next(i for i, (lo, hi) in enumerate(SAL_BANDS) if lo <= sal < hi)


def prep(D):
    """Per row everything the candidates need, computed once."""
    rows, pg, tg, car = D["rows"], D["pg"], D["tg"], D["careers"]
    season, pgp = D["season"], D["prior_gp"]
    by_slate = defaultdict(list)
    for r in rows:
        by_slate[r["slate"]].append(r)
    out = []
    for name, rs in sorted(by_slate.items()):
        before = rs[0]["before"]
        # league: per-category per-minute rate by salary band (the slate's players' games before it), team-game averages
        bsum = [defaultdict(float) for _ in SAL_BANDS]
        for r in rs:
            for g in pg.get(r["espn"], []):
                if g["date"] < before:
                    b = bsum[band_of(r["salary"])]
                    for c in CATS + ("min",):
                        b[c] += g[c]
        brate = [{c: (b[c] / b["min"] if b["min"] else 0.0) for c in CATS} for b in bsum]
        tgb = {t: [g for g in v if g["date"] < before] for t, v in tg.items()}
        allg = [g for v in tgb.values() for g in v]
        L = {c: S.mean(g["for"].get(c, 0.0) for g in allg) for c in CATS}
        Lpts = S.mean(g["pts_for"] for g in allg)
        off_avg = {t: {c: S.mean(g["for"].get(c, 0.0) for g in v) for c in CATS} for t, v in tgb.items() if v}
        allowed_pts = {t: S.mean(g["pts_against"] for g in v) for t, v in tgb.items() if v}

        def opp_raw(o):
            v = tgb.get(o) or []
            al = {c: sum(g["against"].get(c, 0.0) for g in v) for c in CATS}
            ex = {c: sum(off_avg.get(g["opp"], L)[c] for g in v) for c in CATS}
            return al, ex, len(v)
        opp_cache = {}
        for r in rs:
            gs = [g for g in pg.get(r["espn"], []) if g["date"] < before]
            o = r["opp"]
            if o not in opp_cache:
                opp_cache[o] = opp_raw(o)
            al, ex, no = opp_cache[o]
            # last season (CARRY) and EvanMiya priors, as totals
            c0 = car.get(r["espn"]) or {}
            pri = [s for s in sorted(c0, reverse=True) if s < season and c0[s].get("gp", 0) >= pgp and (c0[s].get("min") or 0) > 0]
            carry = None
            if pri:
                p = c0[pri[0]]
                m0, p0 = p["min"], p.get("dk", p["fp"]) / p["min"]
                moved = str(p.get("team")) != str(r["team"])
                X = [1, m0]
                if moved:
                    jump = D["strength"].get(str(r["team"]), 0.0) - D["strength"].get(str(p.get("team")), 0.0)
                    X.append(max(-D["jump_cap"], min(D["jump_cap"], jump)))
                bm, bp = D["carry"]["transfer" if moved else "stayed"]
                carry = p0 * sum(cc * x for cc, x in zip(bp, X)) if m0 >= D["carry_min"] else p0
            # this season's schedule-adjusted scoring, games played
            tv = tgb.get(r["team"]) or []
            adj = [g["pts_for"] - (allowed_pts.get(g["opp"], Lpts) - Lpts) for g in tv]
            out.append({**{k: r[k] for k in ("slate", "dk_id", "name", "salary", "fp_dk", "min_proj", "m_rb", "actual", "min", "spread", "ou",
                                               "dk_avg", "miya", "status")},
                        "games": [(g["min"], {c: g[c] for c in CATS}, g.get("comp")) for g in gs],
                        "band_rate": brate[band_of(r["salary"])], "carry": carry,
                        "opp_al": al, "opp_ex": ex, "opp_n": no, "L": L,
                        "last_ppg": D["last_ppg"].get(str(r["team"])), "this_ppg": S.mean(adj) if adj else None, "n_team": len(adj)})
    return out


def ppm_rates(x, cfg):
    """Per-category per-minute rates under cfg (base prior, priors, form)."""
    pm = cfg["base"]["pm"]
    prof = x["band_rate"]
    ptot = dkpts(prof) or 1.0
    prior_total = ptot
    if "miya_prior" in cfg and x["miya"] is not None:
        prior_total = x["miya"]
    if "carry" in cfg and x["carry"] is not None:
        w = cfg["carry"]["w"] if ("miya_prior" in cfg and x["miya"] is not None) else 0.0
        prior_total = (1 - w) * x["carry"] + w * prior_total
    prior = {c: prof[c] * prior_total / ptot for c in CATS}
    gs = x["games"]
    k = len(gs)
    if "form_raw" in cfg:
        d = cfg["form_raw"]["d"]
        wts = [d ** (k - 1 - j) for j in range(k)]
        mins = [g[0] for g in gs]
    elif "form_clean" in cfg:
        d = cfg["form_clean"]["d"]
        wts = [d ** (k - 1 - j) * ((g[2] / g[0]) if (g[2] is not None and g[0] > 0) else 0.0) for j, g in enumerate(gs)]
        mins = [g[0] for g in gs]
    else:
        wts = [1.0] * k
        mins = [g[0] for g in gs]
    M = sum(w * m for w, m in zip(wts, mins))
    rates = {}
    for c in CATS:
        made = sum(w * g[1][c] for w, g in zip(wts, gs))
        rates[c] = (made + pm * prior[c]) / (M + pm)
    return rates


def project(x, cfg, D):
    """(projection, ppm breakdown)"""
    rates = ppm_rates(x, cfg)
    base = dkpts(rates)
    opp_keys = [k for k in cfg if k.startswith("opp_")]
    for ok in opp_keys:
        cats = OPP_CATS if ok == "opp_all" else (ok[4:],)
        K, al = cfg[ok]["k"], cfg[ok]["a"]
        for c in cats:
            ex = x["opp_ex"][c] + K * x["L"][c]
            f = (x["opp_al"][c] + K * x["L"][c]) / ex if ex > 0 else 1.0
            rates[c] *= f ** al
    matchup = dkpts(rates)
    ppm = matchup
    if "miya_rate" in cfg and x["miya"] is not None:
        w = cfg["miya_rate"]["w"]
        ppm = (1 - w) * ppm + w * x["miya"]
    pace = 1.0
    if x["ou"] and x["spread"] is not None:
        imp = x["ou"] / 2 - x["spread"] / 2
        if "vegas_last" in cfg and x["last_ppg"] is not None:
            pace = 1 + cfg["vegas_last"]["s"] * max(-15, min(15, imp - x["last_ppg"]))
        elif "vegas_this" in cfg and (x["last_ppg"] is not None or x["this_ppg"] is not None):
            k, n = cfg["vegas_this"]["k"], x["n_team"]
            lp = x["last_ppg"] if x["last_ppg"] is not None else x["this_ppg"]
            tp = x["this_ppg"] if x["this_ppg"] is not None else lp
            usual = (n * tp + k * lp) / (n + k)
            pace = 1 + cfg["vegas_this"]["s"] * max(-15, min(15, imp - usual))
    ga = 1.0
    if "game_adj" in cfg and x["spread"] is not None:
        ga = next(f for e, f in D["game_adj"] if x["spread"] < e)
    ppm_final = ppm * pace * ga
    m = x["m_rb"]
    proj = m * ppm_final
    if "dd" in cfg:
        proj += D["dd_bonus"] * dd_chance(rates, m, D["dd_table"])
    if "gate" in cfg and x["salary"] >= 6000 and x["dk_avg"]:
        w = cfg["gate"]["w"]
        proj = w * proj + (1 - w) * x["dk_avg"]
    return proj, {"baseline": round(base, 4), "matchup": round(matchup / base, 4) if base else 1.0,
                  "miya": round(ppm / matchup, 4) if matchup else 1.0, "pace": round(pace, 4), "game_adj": ga, "ppm": round(ppm_final, 4)}


def slate_score(xs, cfg, D):
    """{stars, rot, both}: points MAE by band (today's projection decides the band)."""
    e = {"stars": [], "rot": []}
    for x in xs:
        p = project(x, cfg, D)[0]
        b = "stars" if x["fp_dk"] >= STARS else "rot" if x["fp_dk"] >= ROT else None
        if b:
            e[b].append(abs(x["actual"] - p))
    st, ro = (S.mean(e["stars"]) if e["stars"] else None), (S.mean(e["rot"]) if e["rot"] else None)
    return {"stars": st, "rot": ro, "both": S.mean(e["stars"] + e["rot"]), "bal": (st + ro) / 2 if st is not None and ro is not None else ro}


def today_score(xs, kind):
    e = {"stars": [], "rot": []}
    for x in xs:
        p = x["fp_dk"] if kind == "today" else x["m_rb"] * x["fp_dk"] / x["min_proj"] if x["min_proj"] else x["fp_dk"]
        b = "stars" if x["fp_dk"] >= STARS else "rot" if x["fp_dk"] >= ROT else None
        if b:
            e[b].append(abs(x["actual"] - p))
    return {"stars": S.mean(e["stars"]), "rot": S.mean(e["rot"]), "both": S.mean(e["stars"] + e["rot"]),
            "bal": (S.mean(e["stars"]) + S.mean(e["rot"])) / 2}


# ---------------------------------------------------------------- selection
def key(cfg):
    return json.dumps(cfg, sort_keys=True)


class Ev:
    def __init__(self, X, D):
        self.D = D
        self.sl = defaultdict(list)
        for x in X:
            self.sl[x["slate"]].append(x)
        self.names = sorted(self.sl)
        self.cache = {}

    def sc(self, cfg, s):
        k = (key(cfg), s)
        if k not in self.cache:
            self.cache[k] = slate_score(self.sl[s], cfg, self.D)
        return self.cache[k]

    def held(self, fold_cfgs, fix=None):
        """fold_cfgs: {slate: cfg}. With fix: choose fix's parameter per fold on the other slates. Returns
        ({slate: score}, {slate: cfg used})."""
        res, used = {}, {}
        for s in self.names:
            base = fold_cfgs[s]
            if fix is None:
                c = base
            else:
                cands = [dict(base, **{fix: g}) for g in GRIDS[fix]]
                c = min(cands, key=lambda cc: S.mean(self.sc(cc, o)["bal"] for o in self.names if o != s))
            res[s], used[s] = self.sc(c, s), c
        return res, used


def gain(cur, new, b):
    return [cur[s][b] - new[s][b] for s in cur if cur[s][b] is not None and new[s][b] is not None]


def se(xs):
    return S.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else float("inf")


def verdict(cur, new, n_need=10):
    out = {}
    for b in ("stars", "rot", "both", "bal"):
        g = gain(cur, new, b)
        out[b] = {"mean": S.mean(g), "se": se(g), "better": sum(x > 0 for x in g), "n": len(g)}
    ok = lambda b: out[b]["mean"] > 2 * out[b]["se"] and out[b]["better"] >= n_need
    notworse = lambda b: out[b]["mean"] > -2 * out[b]["se"]
    out["pass"] = (ok("stars") and notworse("rot")) or (ok("rot") and notworse("stars"))
    return out


def blocked(fix, have):
    for grp in EXCLUSIVE:
        if fix in grp and any(h in grp and h != fix for h in have):
            return True
    return fix in have


def select(a):
    D = json.load(open(a.data))
    X = prep(D)
    ev = Ev(X, D)
    names = ev.names
    # clean base: pm chosen per fold
    empty = {s: {} for s in names}
    base_res, base_used = ev.held(empty, "base")
    today = {s: today_score(ev.sl[s], "today") for s in names}
    oldppm = {s: today_score(ev.sl[s], "oldppm") for s in names}
    fixes = [f for f in GRIDS if f != "base"]
    single = {}
    for f in fixes:
        r, _ = ev.held(base_used, f)
        single[f] = verdict(base_res, r)
    # forward selection
    cur_res, cur_used, have, steps, trace = base_res, base_used, [], [], []
    while True:
        best = None
        for f in fixes:
            if blocked(f, have):
                continue
            r, u = ev.held(cur_used, f)
            v = verdict(cur_res, r)
            trace.append({"step": len(have) + 1, "fix": f, "stars": round(v["stars"]["mean"], 3), "rot": round(v["rot"]["mean"], 3),
                          "pass": v["pass"]})
            if v["pass"] and (best is None or v["bal"]["mean"] > best[1]["bal"]["mean"]):
                best = (f, v, r, u)
        if not best:
            break
        have.append(best[0])
        cur_res, cur_used = best[2], best[3]
        steps.append({"add": best[0], "verdict": best[1]})
    # backward check: drop any fix whose removal doesn't hurt beyond the bar
    changed = True
    back = []
    while changed and have:
        changed = False
        for f in list(have):
            rest = {s: {k: v for k, v in cur_used[s].items() if k != f} for s in names}
            r, _ = ev.held(rest)
            v = verdict(r, cur_res)          # adding f back to the rest: does it pass?
            back.append({"fix": f, "verdict": v})
            if not v["pass"]:
                have.remove(f)
                cur_res, cur_used = r, rest
                changed = True
                break
    final_vs_today = verdict(today, cur_res)
    final_vs_oldppm = verdict(oldppm, cur_res)
    base_vs_today = verdict(today, base_res)
    pooled = lambda res, b: S.mean(res[s][b] for s in names if res[s][b] is not None)
    out = {"slates": names, "n_rows": len(X), "base_pm": {s: base_used[s]["base"]["pm"] for s in names},
           "single": single, "steps": steps, "trace": trace, "backward": back, "final": have,
           "final_params": {s: cur_used[s] for s in names},
           "pooled": {k: {b: pooled(v, b) for b in ("stars", "rot", "both", "bal")} for k, v in
                      (("today", today), ("oldppm_rebuilt_min", oldppm), ("clean_base", base_res), ("final", cur_res))},
           "final_vs_today": final_vs_today, "final_vs_oldppm": final_vs_oldppm, "base_vs_today": base_vs_today,
           "per_slate": {s: {"today": today[s], "oldppm": oldppm[s], "base": base_res[s], "final": cur_res[s]} for s in names}}
    json.dump(out, open(a.out, "w"), indent=1, default=str)
    return out, X, D, ev


def opp_factor(x, cats, K, al, pm=90):
    """His per-minute DraftKings points under the opponent's allowed rates in these categories over his own, weighted by
    his category profile (clean-base rates with pm minutes of the band prior)."""
    rates = ppm_rates(x, {"base": {"pm": pm}})
    tot = dkpts(rates)
    adj = dict(rates)
    for c in cats:
        ex = x["opp_ex"][c] + K * x["L"][c]
        adj[c] = rates[c] * (((x["opp_al"][c] + K * x["L"][c]) / ex) if ex > 0 else 1.0) ** al
    return dkpts(adj) / tot if tot else 1.0


def old_plus(a):
    """L3 on TODAY's points a minute (with the rebuilt minutes): today's projection x new minutes / today's minutes x the
    opponent factor, held out by slate the same way."""
    D = json.load(open(a.data))
    X = prep(D)
    sl = defaultdict(list)
    for x in X:
        sl[x["slate"]].append(x)
    names = sorted(sl)
    sets = {"opp_reb": ("reb",), "opp_pts": ("pts",), "opp_ast": ("ast",), "opp_tpm": ("tpm",), "opp_4": ("pts", "tpm", "reb", "ast"),
            "opp_all": OPP_CATS}
    grid = [(k, al) for k in (3, 8) for al in (0.5, 1.0)]
    cache = {}

    def sc(s, cats, g):
        kk = (s, cats, g)
        if kk not in cache:
            e = {"stars": [], "rot": []}
            for x in sl[s]:
                base = x["m_rb"] * x["fp_dk"] / x["min_proj"] if x["min_proj"] else x["fp_dk"]
                p = base * (opp_factor(x, cats, *g) if cats else 1.0)
                b = "stars" if x["fp_dk"] >= STARS else "rot" if x["fp_dk"] >= ROT else None
                if b:
                    e[b].append(abs(x["actual"] - p))
            cache[kk] = {"stars": S.mean(e["stars"]), "rot": S.mean(e["rot"]), "both": S.mean(e["stars"] + e["rot"]), "bal": (S.mean(e["stars"]) + S.mean(e["rot"])) / 2}
        return cache[kk]
    cur = {s: sc(s, (), None) for s in names}
    res = {}
    for nm, cats in sets.items():
        new = {}
        for s in names:
            g = min(grid, key=lambda gg: S.mean(sc(o, cats, gg)["bal"] for o in names if o != s))
            new[s] = sc(s, cats, g)
        v = verdict(cur, new)
        res[nm] = {b: (round(v[b]["mean"], 3), round(v[b]["se"], 3), v[b]["better"]) for b in ("stars", "rot", "bal")}
        res[nm]["pass"] = v["pass"]
    full = {k: (round(S.mean(cur[s][k] for s in names), 3)) for k in ("stars", "rot")}
    print(json.dumps({"oldppm_rebuilt_min": full, "layers": res}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd")
    x = sp.add_parser("assemble")
    x.add_argument("--brr", required=True)
    x.add_argument("--boxes", required=True)
    x.add_argument("--qmin", required=True)
    x.add_argument("--rb", required=True)
    x.add_argument("--cache", required=True)
    x.add_argument("--out", required=True)
    z = sp.add_parser("oldplus")
    z.add_argument("--data", required=True)
    y = sp.add_parser("select")
    y.add_argument("--data", required=True)
    y.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "assemble":
        assemble(a)
    elif a.cmd == "oldplus":
        old_plus(a)
    elif a.cmd == "select":
        out = select(a)[0]
        print(json.dumps({k: out[k] for k in ("final", "pooled", "final_vs_today", "base_vs_today")}, indent=1, default=str))


if __name__ == "__main__":
    main()


def decompose(slate_files=None):
    """The miss split into minutes and points a minute (players who played, projected 10+): miss = (min_act - min_proj) x
    (fp / min_proj) + min_act x (act / min_act - fp / min_proj); each part's share of the summed squares, by band."""
    files = slate_files or sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv")))
    acc = {"rot": [0.0, 0.0, 0], "stars": [0.0, 0.0, 0]}
    used = 0
    for f in files:
        rows = [r for r in csv.DictReader(open(f)) if num(r.get("actual_dk")) is not None]
        if not rows:
            continue
        used += 1
        for r in rows:
            fp, mp, ma, act = num(r["fp_dk"]), num(r["min_proj"]), num(r.get("min")), num(r["actual_dk"])
            if not fp or fp < ROT or not mp or not ma:
                continue
            b = "stars" if fp >= STARS else "rot"
            mpart = (ma - mp) * (fp / mp)
            ppart = ma * (act / ma - fp / mp)
            acc[b][0] += mpart ** 2
            acc[b][1] += ppart ** 2
            acc[b][2] += 1
    return {b: {"minutes": v[0] / (v[0] + v[1]), "per_minute": v[1] / (v[0] + v[1]), "n": v[2]} for b, v in acc.items()}, used


def reliability(D, min_games=6, min_min=10):
    """Split-half reliability of DraftKings points a minute (odd vs even games, minutes-weighted, games of min_min+),
    Spearman-Brown to the full season; and the single-game noise: the within-player SD of one game's points a minute,
    against the per-minute part of our miss."""
    xs, ys, within = [], [], []
    for pid, gl in D["pg"].items():
        gs = [g for g in gl if g["min"] >= min_min]
        if len(gs) < min_games:
            continue
        rate = lambda sub: sum(dkpts(g) for g in sub) / sum(g["min"] for g in sub)
        xs.append(rate(gs[0::2]))
        ys.append(rate(gs[1::2]))
        allr = rate(gs)
        within.append(S.mean((dkpts(g) / g["min"] - allr) ** 2 for g in gs) * len(gs) / (len(gs) - 1))
    r = S.correlation(xs, ys)
    return {"players": len(xs), "half_r": r, "full_r": 2 * r / (1 + r), "game_sd": math.sqrt(S.mean(within))}
