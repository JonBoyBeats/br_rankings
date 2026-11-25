"""The minutes half rebuilt from a clean base (2026-11-25, the operator's method change: every fix re-earns its place).

CLEAN BASE: QMIN minutes only. His on-court rates by game state (win probability from margin and time left; the spread-
based version contaminates the decided-state rates with a heavy favorite's opening minutes, dk_qmin_study.py), tonight's
expected time in each state at tonight's spread, his rates blended with the games matching tonight's top-5 availability
(step 6: n_match / (n_match + K_CTX), absence games carried at the measured persistence), then each team scaled to 200 in
proportion (none over 40). Nothing else: no prior season, no MIN_BY_SPREAD, no FORM, no Out hand-off, no fit weighting, no
steepen. A player with no clean games this season gets the league's 9+ role rates. Points: today's points per minute held
(fp x new minutes / today's), so only the minutes half changes.

FIXES re-earned one at a time, held out by slate (14 graded slates), forward selection by the largest gain, the Lab's bar
(better on 10+ of 14 and a mean gain over 2 x SE of the rotation band's minutes MAE; stars' points and the minutes lenses
not worse beyond noise), each fix's parameter and the base's chosen on the other slates; then a backward check.

  python3 scripts/dk_qmin_rebuild.py --brr ../battle-royale-research --data <dir> --study <study.json> --out <json>
"""
import argparse, json, math, os, statistics as S, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_qmin_study as q  # noqa: E402

BASE_GRID = [{"fade": f, "k_ctx": k} for f in (1.0, 0.8, 0.6) for k in (2, 8)]
FIXES = {          # name: (in today's projection?, parameter grid, what it is)
    "prior": (True, [None], "prior season / CARRY / crowd_keep / MISSED_SEASON blended in at MIN_FILL (players with a prior season)"),
    "newcomer": (True, [None], "MIN_BY_BPR_RANK / Underdog start for players with no prior season (EvanMiya newcomers), at MIN_FILL"),
    "form": (True, [0.25, 0.5, 1.0], "raw FORM 0.8 minutes blended into the QMIN minutes at weight w"),
    "spread": (True, [None], "MIN_BY_SPREAD x his tier"),
    "game_adj": (True, [None], "GAME_ADJ as a minutes factor by the spread"),
    "outhand": (True, [None], "OUT_REG_MIN hand-off: OUT_SHARE of an Out regular's minutes to teammates by m(40-m), position-weighted"),
    "fitw": (True, [None], "fit_minutes (excess off by 40-m, shortfall on by m(40-m)) instead of proportional"),
    "steep": (True, [0.06, 0.12, 0.18], "steepen m^(1+g) after the fit"),
}
AVAIL = {
    "zero_gp": (True, [None], "zero-games cut: x ZERO_GP_F for a player with no games while his team has 3+"),
    "q_play": (False, [None], "a Questionable player's minutes x p_play (today: x 1.0, the operator's call)"),
}


def build(args):
    cn = q.load_nightly(args.brr)
    games = q.load_games(args.data)
    st = json.load(open(args.study))
    P0 = (st["wp0"]["sig"], 0.0, st["wp0"]["eps"])
    q.PMODE.update(wp0=P0)
    pp = q.clean_games(games, P0, "wp0")[0]
    box = q.all_box_games(games)
    ps, _ = q.played_sets(games)
    p_keep = max(0.0, min(1.0, st["returns"]["persist_min"]))
    slates = []
    for name, proj, rc in q.slate_rows(args.brr):
        before = min(r["game_start"] for r in proj.values() if r.get("game_start"))
        stime = q.state_time(pp, before, "wp0")[0]
        tops = q.team_tops(pp, before, 5)
        roles = {f: q.role_tables_mode(pp, before, f, q.STATES, 60, "COMP") for f in (1.0, 0.8, 0.6)}
        by_espn = {str(r.get("espn")): r for r in proj.values() if r.get("espn")}
        pl = {}
        for k, r in proj.items():
            if r.get("status") == "Out" or r.get("min") is None:
                continue
            espn = str(r.get("espn") or "")
            bg = [g for g in box.get(espn, []) if g["date"] < before]
            cg = [g for g in pp.get(espn, []) if g["date"] < before]
            rec = {"a": r["min"], "spread": r.get("spread"), "team": r.get("espn_team"), "src": r.get("src"), "pos": r.get("position"),
                   "status": r.get("status"), "p_play": r.get("p_play"), "zero": (r.get("zero_gp") or {}).get("f"), "q": {}}
            pre = r.get("min_raw", r["min"])
            m_a = None
            for tm in (10, 24, 30):
                f = cn.spread_factor(r.get("spread"), tm)
                if cn.spread_factor(r.get("spread"), pre / f) == f:
                    m_a = pre / f
                    break
            rec["m_a"] = m_a
            if bg and m_a is not None:
                cur, gw = q.form_min(bg)
                rec.update(cur=cur, gw=gw, mp=(m_a * (gw + cn.MIN_FILL) - gw * cur))
            elif m_a is not None:
                rec.update(cur=None, gw=0.0, mp=m_a * cn.MIN_FILL)          # no games: today's minutes are all prior
            # QMIN minutes under each base parameter set (context: tonight's absent top 5; Q teammates by p_play)
            tpl = [x for x in tops.get(r.get("espn_team"), []) if x != espn]
            stf = lambda x: (by_espn.get(x) or {}).get("status") if x in by_espn else "Out"
            out_now = frozenset(x for x in tpl if stf(x) == "Out")
            qs = [x for x in tpl if stf(x) == "Questionable"][:2]
            combos = [(out_now, 1.0)]
            for x in qs:
                pq = (by_espn.get(x) or {}).get("p_play")
                pq = 0.8 if pq is None else float(pq)
                combos = [(c, w * pq) for c, w in combos] + [(c | {x}, w * (1 - pq)) for c, w in combos]
            sb = stime.get(q.spread_bin(r.get("spread"))) or {}
            for bp in BASE_GRID:
                tmr, lg, role_of = roles[bp["fade"]]
                if cg:
                    prior = (tmr.get(r.get("espn_team")) or {}).get(role_of.get(espn, 1)) or lg.get(role_of.get(espn, 1)) or {}
                    tot = 0.0
                    for A, w in combos:
                        tot += w * qmin_ctx(cg, r.get("espn_team"), set(A), tpl, ps, p_keep, bp, prior, sb)
                    rec["q"][json.dumps(bp, sort_keys=True)] = tot
                else:
                    rec["q"][json.dumps(bp, sort_keys=True)] = sum(sb.get(s, 0.0) * lg.get(2, {}).get("COMP" if s == "OT" else s, 0.0) / 60 for s in q.STATES)
            pl[k] = rec
        outs = {k: r for k, r in proj.items() if r.get("status") == "Out" and r.get("min") is not None}
        slates.append({"name": name, "rc": rc, "pl": pl, "outs": outs, "cn": cn})
    return slates


def qmin_ctx(cg, t, A, tops, ps, p_keep, bp, prior, sb):
    cw = q.ctx_weights(cg, t, A, tops, ps, p_keep)
    nm = sum(1 for m, _, _ in cw if m)
    wm = nm / (nm + bp["k_ctx"]) if nm else 0.0
    k = len(cg)

    def acc(sel):
        on, gm = defaultdict(float), defaultdict(float)
        for j, (g, x) in enumerate(zip(cg, sel)):
            w = bp["fade"] ** (k - 1 - j) * x
            for s in q.STATES:
                gm[s] += w * g["gst"].get(s, 0.0)
                on[s] += w * g["on"].get(s, 0.0)
        return on, gm
    on_m, gm_m = acc([1.0 if m else 0.0 for m, _, _ in cw])
    on_s, gm_s = acc([w for _, w, _ in cw])
    exp = 0.0
    for s in q.STATES:
        src = "COMP" if s == "OT" else s
        kp = 10 if src == "COMP" else 15
        rs = (on_s[src] + kp * 60 * prior.get(src, 0.0)) / (gm_s[src] + kp * 60)
        if gm_m[src] > 0:
            rs = wm * (on_m[src] + kp * 60 * prior.get(src, 0.0)) / (gm_m[src] + kp * 60) + (1 - wm) * rs
        exp += sb.get(s, 0.0) * rs / 60.0
    return exp


def gadj(cn, s):
    return next(f for e, f in cn.GAME_ADJ if s < e) if s is not None else 1.0


def project(sl, cfg):
    """{dk_id: minutes} for one slate under cfg: {"base": params, fix: param, ...}."""
    cn = sl["cn"]
    bkey = json.dumps(cfg["base"], sort_keys=True)
    m = {}
    for k, r in sl["pl"].items():
        x = r["q"][bkey]
        if "form" in cfg and r.get("cur") is not None:
            x = cfg["form"] * r["cur"] + (1 - cfg["form"]) * x
        pri = ("prior" in cfg and r["src"] == "box") or ("newcomer" in cfg and r["src"] == "miya")
        if pri and r.get("mp") is not None:
            if r.get("cur") is None:
                x = r["m_a"]
            else:
                x = (r["gw"] * x + r["mp"]) / (r["gw"] + cn.MIN_FILL)
        if "spread" in cfg:
            x *= cn.spread_factor(r["spread"], x)
        if "game_adj" in cfg:
            x *= gadj(cn, r["spread"])
        if "zero_gp" in cfg and r["zero"]:
            x *= r["zero"]                  # the cut as it was live that night (the rule from 2026-11-22)
        if "q_play" in cfg and r["status"] == "Questionable" and r.get("p_play") is not None:
            x *= float(r["p_play"])
        m[k] = max(0.0, min(40.0, x))
    teams = defaultdict(list)
    for k, r in sl["pl"].items():
        teams[r["team"]].append(k)
    if "outhand" in cfg:
        grp = lambda p: "G" if str(p or "").startswith("G") else "B"
        for t, ks in teams.items():
            sat = [o for o in sl["outs"].values() if o.get("espn_team") == t and o["min"] >= cn.OUT_REG_MIN and (o.get("gp") or 0) >= cn.OUT_REG_GAMES]
            if not sat:
                continue
            freed, gs = cn.OUT_SHARE * sum(o["min"] for o in sat), {grp(o.get("position")) for o in sat}
            w = {k: m[k] * max(1.0, 40 - m[k]) * (1.0 if grp(sl["pl"][k]["pos"]) in gs else cn.OUT_POS_OTHER) for k in ks}
            W = sum(w.values()) or 1.0
            for k in ks:
                m[k] = min(40.0, m[k] + freed * w[k] / W)
    for t, ks in teams.items():
        v = [m[k] for k in ks]
        if "fitw" in cfg:
            v = cn.fit_minutes(v)
        else:
            tot = sum(v)
            if tot > 0:
                v = [min(40.0, x * 200.0 / tot) for x in v]
                for _ in range(20):
                    free = [i for i, x in enumerate(v) if x < 40 - 1e-9]
                    gap = 200.0 - sum(v)
                    if abs(gap) < 1e-6 or not free:
                        break
                    s = sum(v[i] for i in free)
                    v = [min(40.0, x * (1 + gap / s)) if i in free else x for i, x in enumerate(v)]
        if "steep" in cfg:
            v = cn.steepen(v, cfg["steep"])
        for k, x in zip(ks, v):
            m[k] = x
    return m


def score(sl, cfg):
    m = project(sl, cfg)
    ma = {k: r["a"] for k, r in sl["pl"].items()}
    return q.grade(sl["rc"], m, ma)


def held(slates, fixed, cand_grid):
    """Per slate: the base params and the candidate's param chosen on the other slates (pooled rotation minutes MAE)."""
    cache = {}
    combos = [dict(fixed, base=b, **({c: p for c, p in cg.items()})) for b in BASE_GRID for cg in cand_grid]
    for i, cfg in enumerate(combos):
        for sl in slates:
            cache[(i, sl["name"])] = score(sl, cfg)
    out = []
    for sl in slates:
        others = [s["name"] for s in slates if s["name"] != sl["name"]]
        best = min(range(len(combos)), key=lambda i: S.mean(cache[(i, o)]["rot_min"] for o in others))
        out.append((sl["name"], combos[best], cache[(best, sl["name"])]))
    return out


def compare(new, old):
    d = [o[2]["rot_min"] - n[2]["rot_min"] for n, o in zip(new, old)]
    ds = [n[2]["star_pts"] - o[2]["star_pts"] for n, o in zip(new, old) if n[2]["star_pts"] is not None]
    dr = [n[2]["rank"] - o[2]["rank"] for n, o in zip(new, old) if n[2]["rank"] is not None and o[2]["rank"] is not None]
    dt = [n[2]["top5"] - o[2]["top5"] for n, o in zip(new, old) if n[2]["top5"] is not None and o[2]["top5"] is not None]
    se = lambda x: S.stdev(x) / math.sqrt(len(x)) if len(x) > 1 else float("inf")
    return {"gain": S.mean(d), "se": se(d), "better": sum(x > 0 for x in d), "of": len(d), "star": S.mean(ds), "star_se": se(ds),
            "rank": S.mean(dr) if dr else 0.0, "rank_se": se(dr), "top5": S.mean(dt) if dt else 0.0, "top5_se": se(dt),
            "rot": S.mean(n[2]["rot_min"] for n in new)}


def passes(c):
    return (c["better"] >= 10 and c["gain"] > 2 * c["se"] and c["star"] < 2 * c["star_se"] and -c["rank"] < 2 * c["rank_se"]
            and -c["top5"] < 2 * c["top5_se"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brr", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--study", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    slates = build(a)
    today = [(s["name"], None, q.grade(s["rc"], {k: r["a"] for k, r in s["pl"].items()}, {k: r["a"] for k, r in s["pl"].items()})) for s in slates]
    res = {"steps": [], "avail": {}}
    fixed = {}
    cur = held(slates, fixed, [{}])
    res["base"] = compare(cur, today)
    remaining = dict(FIXES)
    while remaining:
        trials = {}
        for f, (_, grid, _) in remaining.items():
            h = held(slates, fixed, [{f: p} for p in grid])
            trials[f] = (h, compare(h, cur))
        ok = {f: t for f, t in trials.items() if passes(t[1])}
        res["steps"].append({f: dict(t[1], param=None) for f, t in trials.items()})
        if not ok:
            break
        f = max(ok, key=lambda x: ok[x][1]["gain"])
        h, c = ok[f]
        # the fix's parameter on all slates
        grid = remaining[f][1]
        allp = min(grid, key=lambda p: S.mean(score(s, dict(fixed, base=h[0][1]["base"], **{f: p}))["rot_min"] for s in slates))
        fixed[f] = allp
        cur = h
        res["steps"][-1]["chosen"] = {"fix": f, "param": allp}
        del remaining[f]
    # backward: drop a kept fix whose removal doesn't hurt held out
    back = {}
    for f in list(fixed):
        without = {k: v for k, v in fixed.items() if k != f}
        h0 = held(slates, without, [{}])
        c = compare(cur, h0)               # the full set against the set without f
        back[f] = c
        if not passes(c):
            fixed = without
            cur = held(slates, fixed, [{}])
    res["backward"] = back
    res["final_fixes"] = fixed
    final = held(slates, fixed, [{}])
    res["final_vs_today"] = compare(final, today)
    res["final_per_slate"] = [{"slate": n, "base": cfg["base"], "rot": g["rot_min"], "today": t[2]["rot_min"]} for (n, cfg, g), t in zip(final, today)]
    for f, (_, grid, _) in AVAIL.items():
        h = held(slates, fixed, [{f: p} for p in grid])
        res["avail"][f] = compare(h, final)
    # today's shipped (b): its held-out rows from the study
    st = json.load(open(a.study))
    bper = {r["slate"]: r["rot"] for r in st["held"]["b"]["per_slate"]}
    d = [bper[n] - g["rot_min"] for n, _, g in final]
    res["final_vs_b"] = {"gain": S.mean(d), "se": S.stdev(d) / math.sqrt(len(d)), "better": sum(x > 0 for x in d), "of": len(d)}
    res["fixes_meta"] = {f: {"in_today": v[0], "what": v[2]} for f, v in list(FIXES.items()) + list(AVAIL.items())}
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(json.dumps({k: res[k] for k in ("base", "final_fixes", "final_vs_today", "final_vs_b")}, indent=1, default=str))


if __name__ == "__main__":
    main()
