"""Quality minutes (QMIN), 2026-11-25 (the coordinator's request, the operator's yes: ships only if it passes the bar).

The question: blowouts and overtime pollute a player's minutes (and their trend), and coaches differ in whether the
starters come back in a blowout. Does rebuilding each player's on-court time from ESPN's play-by-play, split by how
close the game was, give a better minutes projection than today's?

1. STINTS. Each game's substitution events ("X subbing in/out for TEAM", with the clock and the score) rebuild every
   player's time on court, from the box score's starters. A player-game whose rebuilt minutes miss the box score's
   by more than RECON_TOL is dropped (coverage reported). Foul-limited games (a 4th foul with more than LATE_2H left in
   regulation, or fouled out) and injury exits (a starter with no court time in the last INJ_LATE of regulation while
   the game stayed competitive, not foul-limited) are flagged and kept out of the rate fits.
2. GAME STATE by in-game win probability, fit on these games: P(home wins) = Phi((m - K x spread x tau) / (SIG x
   sqrt(tau) + EPS)), m the home margin, tau the share of regulation left, spread the home spread at the open. From
   each team's side: COMPETITIVE (the leader under 90%), LEANING (90-98%), DECIDED (over 98%), the last two split
   leading / trailing; overtime its own state. Plain margin buckets (under 10, 10-19, 20-29, 30+, leading / trailing)
   are run beside it.
3. QMIN = his on-court rate in COMPETITIVE time x 40: his role when the game matters. Stability: game-to-game SD and
   split-half (odd vs even games) reliability against raw minutes and minutes per 40 of game; first-half vs
   second-half competitive rates.
4. TONIGHT: expected minutes = sum over states of (expected minutes of tonight's game in that state, from these games
   at tonight's spread) x (his rate in that state). His rate in a state is shrunk toward his team's rate for his role
   (top 5 / 6-8 / 9+ by QMIN on the team) with K_PLAYER minutes of it, and the team's toward the league's role rate with
   K_TEAM. It stands in for the current season's minutes x MIN_BY_SPREAD (the prior season's MIN_FILL part keeps
   MIN_BY_SPREAD), so the spread enters once.
5. TREND on the clean competitive rate: games weighted FADE^(games ago), the fade chosen held out; a role-change flag
   when his last ROLE_N games' competitive rate differs from the earlier ones by ROLE_D or more.

The test: each of the 14 graded slates held out (parameters chosen on the other 13), the banded grade
(dk_proj_grade.py): the ROTATION band's minutes MAE is the headline; top-5 minutes match and minutes rank agreement
within the band; the STARS band's points MAE must not worsen. Three models: (a) today's, (b) SIMPLE (overtime scaled to
regulation, blowouts down-weighted, a recency fade, then MIN_BY_SPREAD as now), (c) the full QMIN model. Each team's
minutes then go through the nightly's own team_minutes (Out regulars' minutes, the fit to 200, steepen), points per
minute held. The Lab's bar: better on 10+ of 14 slates and a mean gain over 2 x SE.

  python3 scripts/dk_qmin_study.py --brr ../battle-royale-research --data <dir with sum/*.json, events.json> [--md OUT]
"""
import argparse, copy, csv, glob, json, math, os, statistics as S, sys
from collections import defaultdict

DK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "cbb", "dk")
RECON_TOL = 2.0            # minutes: rebuilt vs box score
LATE_2H = 480              # seconds of regulation left: a 4th foul before this is foul-limited
INJ_LATE = 900             # seconds: a starter with no court time in the last 15 minutes while competitive
STATES = ["COMP", "LEAN_L", "LEAN_T", "DEC_L", "DEC_T", "OT"]
MSTATES = ["M0", "M10_L", "M10_T", "M20_L", "M20_T", "M30_L", "M30_T", "OT"]
SPREAD_BINS = [-20, -12, -6, -2, 2, 6, 12, 20]
ROLE_N, ROLE_D = 2, 0.15
num = lambda v: float(v) if v not in ("", None) else None


def clock_s(c):
    try:
        mm, ss = str(c).split(":")
        return int(mm) * 60 + float(ss)
    except ValueError:
        return float(c or 0)


def elapsed(period, clock):
    if period <= 2:
        return (period - 1) * 1200 + 1200 - clock_s(clock)
    return 2400 + (period - 3) * 300 + 300 - clock_s(clock)


def parse(path):
    """One game: teams, the line, the final, every on-court second of each player by (home margin, time left, period)."""
    d = json.load(open(path))
    plays = d.get("plays") or []
    comp = d["header"]["competitions"][0]
    side = {c["team"]["id"]: c["homeAway"] for c in comp["competitors"]}
    home = next(t for t, s in side.items() if s == "home")
    away = next(t for t, s in side.items() if s == "away")
    pk = (d.get("pickcenter") or [{}])[0]
    spread = pk.get("spread")
    box, starters = {}, {home: set(), away: set()}
    for tb in d["boxscore"].get("players", []):
        t = tb["team"]["id"]
        st = tb["statistics"][0]
        names = st.get("names") or st.get("labels")
        for a in st.get("athletes", []):
            aid = a["athlete"]["id"]
            v = dict(zip(names, a.get("stats") or []))
            mn = num(v.get("MIN")) if v.get("MIN") not in ("--", None) else None
            g3 = lambda k: num(str(v.get(k) or "").split("-")[0]) or 0.0
            pts, reb, ast, stl, blk, to = (num(v.get(k)) or 0.0 for k in ("PTS", "REB", "AST", "STL", "BLK", "TO"))
            dk = pts + 0.5 * g3("3PT") + 1.25 * reb + 1.5 * ast + 2 * stl + 2 * blk - 0.5 * to + (1.5 if sum(x >= 10 for x in (pts, reb, ast)) >= 2 else 0)
            box[aid] = {"team": t, "min": mn or 0.0, "pf": num(v.get("PF")) or 0, "starter": bool(a.get("starter")), "dk": dk,
                        "pos": ((a["athlete"].get("position") or {}).get("abbreviation") or "")[:1]}
            if a.get("starter"):
                starters[t].add(aid)
    if not plays or len(starters[home]) != 5 or len(starters[away]) != 5:
        return None
    plays = sorted(plays, key=lambda p: int(p.get("sequenceNumber") or 0))
    nper = max(p["period"]["number"] for p in plays)
    end = 2400 + 300 * max(0, nper - 2)
    on = {home: set(starters[home]), away: set(starters[away])}
    t0, hm = 0.0, 0                     # segment start, home margin
    secs = defaultdict(lambda: defaultdict(float))     # player -> (seg key) -> seconds; seg key = (hm, tleft, period)
    segs = []                                          # (t0, t1, hm, period)
    fouls, foul_lim, last_on = defaultdict(int), set(), {}
    bad_out = defaultdict(int)

    def flush(t1, per):
        nonlocal t0
        if t1 > t0:
            segs.append((t0, t1, hm, per))
            for t in (home, away):
                for p in on[t]:
                    secs[p][len(segs) - 1] += t1 - t0
                    last_on[p] = t1
            t0 = t1
    for p in plays:
        per = p["period"]["number"]
        t = elapsed(per, p.get("clock", {}).get("displayValue", "0:00"))
        t = max(t0, min(t, end))
        flush(t, per)
        txt = str(p.get("text") or "")
        typ = (p.get("type") or {}).get("text", "")
        part = [x["athlete"]["id"] for x in p.get("participants") or [] if x.get("athlete")]
        tm = (p.get("team") or {}).get("id")
        if typ == "Substitution" and part and tm in on:
            if "subbing in" in txt:
                on[tm].add(part[0])
            elif "subbing out" in txt:
                if part[0] in on[tm]:
                    on[tm].discard(part[0])
                else:
                    bad_out[part[0]] += 1
        elif "Foul" in typ and part:
            fouls[part[0]] += 1
            if fouls[part[0]] >= 5 or (fouls[part[0]] >= 4 and per <= 2 and t < 2400 - LATE_2H):
                foul_lim.add(part[0])
        hm = (p.get("homeScore") or 0) - (p.get("awayScore") or 0)
    flush(end, nper)
    final = hm
    return {"id": os.path.basename(path)[:-5], "date": d["header"]["competitions"][0]["date"], "home": home, "away": away,
            "spread": spread, "total": pk.get("overUnder"), "final": final, "nOT": max(0, nper - 2), "box": box,
            "secs": {p: dict(v) for p, v in secs.items()}, "segs": segs, "foul_lim": foul_lim, "bad_out": dict(bad_out)}


# --- win probability -------------------------------------------------------------------------------------------
def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def wp_home(m, tleft, spread, P):
    """P(home wins) at home margin m with tleft seconds of regulation left, the home spread at the open."""
    sig, k, eps = P
    tau = max(0.0, tleft) / 2400.0
    mu = m - k * (spread or 0.0) * tau
    den = sig * math.sqrt(tau) + eps
    return phi(mu / den)


def fit_wp(games, ks=(0.6, 0.8, 1.0, 1.2)):
    """SIG, K, EPS by likelihood over every segment (weighted by its seconds) of regulation."""
    obs = []
    for g in games:
        if g["final"] == 0:
            continue
        y = 1 if g["final"] > 0 else 0
        for (a, b, hm, per) in g["segs"]:
            if per <= 2:
                obs.append((hm, 2400 - a, g["spread"] or 0.0, y, b - a))
    best = None
    for sig in [8, 9, 10, 11, 12, 13, 14, 15, 16]:
        for k in ks:
            for eps in [0.5, 1.0, 2.0]:
                ll = 0.0
                for (hm, tl, sp, y, w) in obs:
                    p = min(1 - 1e-6, max(1e-6, wp_home(hm, tl, sp, (sig, k, eps))))
                    ll += w * math.log(p if y else 1 - p)
                if best is None or ll > best[0]:
                    best = (ll, (sig, k, eps))
    return best[1], len(obs)


PMODE = {}


def state(team_home, hm, tleft, per, spread, P, mode):
    """The state of one segment from a team's side."""
    if per > 2:
        return "OT"
    m = hm if team_home else -hm
    if mode == "margin":
        a = abs(m)
        if a < 10:
            return "M0"
        tag = "_L" if m > 0 else "_T"
        return ("M10" if a < 20 else "M20" if a < 30 else "M30") + tag
    ph = wp_home(hm, tleft, spread, PMODE.get(mode, P))
    pt = ph if team_home else 1 - ph
    lead = max(pt, 1 - pt)
    if lead < 0.90:
        return "COMP"
    tag = "_L" if pt >= 0.5 else "_T"
    return ("LEAN" if lead <= 0.98 else "DEC") + tag


def game_states(g, P, mode):
    """{team: {state: game seconds}}, and {player: {state: on-court seconds}} for one game."""
    out_t = {g["home"]: defaultdict(float), g["away"]: defaultdict(float)}
    seg_state = {}
    for i, (a, b, hm, per) in enumerate(g["segs"]):
        for t in (g["home"], g["away"]):
            s = state(t == g["home"], hm, 2400 - a, per, g["spread"], P, mode)
            out_t[t][s] += b - a
            seg_state[(t, i)] = s
    pl = {}
    for p, v in g["secs"].items():
        t = g["box"].get(p, {}).get("team")
        if t not in out_t:
            continue
        acc = defaultdict(float)
        for i, s in v.items():
            acc[seg_state[(t, i)]] += s
        pl[p] = dict(acc)
    return out_t, pl, seg_state


def clean_games(games, P, mode):
    """Per player, his clean games: [(date, game id, team, {state: game sec}, {state: on sec}, box min, nOT, final margin
    from his side, first-half comp rate, second-half comp rate)], plus coverage counts."""
    per_player = defaultdict(list)
    cov = defaultdict(int)
    for g in games:
        ts, pl, ss = game_states(g, P, mode)
        if mode == "wp":
            wss = ss
        else:
            _, _, wss = game_states(g, P, "wp")
        for p, b in g["box"].items():
            if b["min"] <= 0:
                continue
            cov["player_games"] += 1
            rb = sum(pl.get(p, {}).values()) / 60.0
            if abs(rb - b["min"]) > RECON_TOL:
                cov["dropped_recon"] += 1
                continue
            team = b["team"]
            if p in g["foul_lim"]:
                cov["foul_limited"] += 1
                continue
            # injury exit: a starter, no court time in the last INJ_LATE of regulation, competitive at least 5 min of it
            if b["starter"] and b["min"] >= 3:
                late_on = sum(s for i, s in g["secs"].get(p, {}).items() if g["segs"][i][0] >= 2400 - INJ_LATE and g["segs"][i][3] <= 2)
                late_comp = sum(bb - a for i, (a, bb, hm, per) in enumerate(g["segs"]) if a >= 2400 - INJ_LATE and per <= 2
                                and wss[(team, i)] == "COMP")
                if late_on == 0 and late_comp >= 300:
                    cov["injury_exit"] += 1
                    continue
            # halves' competitive rates
            hr = [None, None]
            for hidx in (0, 1):
                gs = on_s = 0.0
                for i, (a, bb, hm, per) in enumerate(g["segs"]):
                    if per != hidx + 1:
                        continue
                    if wss[(team, i)] == "COMP":
                        gs += bb - a
                        on_s += g["secs"].get(p, {}).get(i, 0.0)
                hr[hidx] = on_s / gs if gs >= 120 else None
            mside = g["final"] if team == g["home"] else -g["final"]
            sp = g["spread"]
            sp_team = (sp if team == g["home"] else -sp) if sp is not None else None
            per_player[p].append({"date": g["date"], "gid": g["id"], "team": team, "gst": dict(ts[team]), "on": pl.get(p, {}),
                                  "min": b["min"], "dk": b["dk"], "nOT": g["nOT"], "margin": mside, "spread": sp_team, "h1": hr[0], "h2": hr[1]})
            cov["clean"] += 1
    for v in per_player.values():
        v.sort(key=lambda x: x["date"])
    return per_player, dict(cov)


def all_box_games(games):
    """Per player every game he played (box minutes, OT, final margin, date), clean or not: for (a) and (b)."""
    out = defaultdict(list)
    for g in games:
        for p, b in g["box"].items():
            if b["min"] > 0:
                ms = g["final"] if b["team"] == g["home"] else -g["final"]
                out[p].append({"date": g["date"], "gid": g["id"], "team": b["team"], "min": b["min"], "dk": b["dk"], "nOT": g["nOT"], "margin": ms})
    for v in out.values():
        v.sort(key=lambda x: x["date"])
    return out


# --- stability -----------------------------------------------------------------------------------------------------
def stability(pp):
    """Within-player game-to-game SD (and CV) and odd/even split-half correlation of: raw minutes, minutes per 40 of
    game, QMIN (competitive rate x 40); and first vs second half competitive rates."""
    meas = {"raw minutes": [], "minutes per 40": [], "QMIN": []}
    halves = {"H1": [], "H2": []}
    split = {k: ([], []) for k in meas}
    hsplit = {"H1": ([], []), "H2": ([], [])}
    for p, gs in pp.items():
        vals = {"raw minutes": [], "minutes per 40": [], "QMIN": []}
        h1, h2 = [], []
        for g in gs:
            gl = sum(g["gst"].values())
            cs = g["gst"].get("COMP", 0.0)
            if cs < 300:
                continue
            vals["raw minutes"].append(g["min"])
            vals["minutes per 40"].append(g["min"] * 2400 / gl if gl else None)
            vals["QMIN"].append(40 * g["on"].get("COMP", 0.0) / cs)
            if g["h1"] is not None:
                h1.append(40 * g["h1"])
            if g["h2"] is not None:
                h2.append(40 * g["h2"])
        if len(vals["QMIN"]) >= 4 and S.mean(vals["raw minutes"]) >= 10:
            for k, v in vals.items():
                meas[k].append((S.pstdev(v), S.mean(v)))
                split[k][0].append(S.mean(v[0::2]))
                split[k][1].append(S.mean(v[1::2]))
        for k, v in (("H1", h1), ("H2", h2)):
            if len(v) >= 4 and S.mean(vals["raw minutes"] or [0]) >= 10:
                halves[k].append((S.pstdev(v), S.mean(v)))
                hsplit[k][0].append(S.mean(v[0::2]))
                hsplit[k][1].append(S.mean(v[1::2]))
    out = {}
    for k, v in list(meas.items()) + list(halves.items()):
        sp = (split.get(k) or hsplit.get(k))
        out[k] = {"players": len(v), "sd": S.mean(x[0] for x in v) if v else None,
                  "cv": S.mean(x[0] / x[1] for x in v if x[1]) if v else None,
                  "split_r": corr(*sp) if len(sp[0]) > 2 else None}
    return out


def corr(a, b):
    ma, mb = S.mean(a), S.mean(b)
    num_ = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num_ / den if den else None


# --- the projection pieces ---------------------------------------------------------------------------------------
def spread_bin(s):
    s = s or 0.0
    return sum(s >= e for e in SPREAD_BINS)


def state_time(pp_games, before, mode):
    """{spread bin: {state: expected seconds}} from every team-game before `before` (each game from both sides)."""
    seen, acc, n = set(), defaultdict(lambda: defaultdict(float)), defaultdict(int)
    for gs in pp_games.values():
        for g in gs:
            key = (g["gid"], g["team"])
            if g["date"] >= before or key in seen:
                continue
            seen.add(key)
            b = spread_bin(g["spread"])
            n[b] += 1
            for s, v in g["gst"].items():
                acc[b][s] += v
    out = {}
    for b in range(len(SPREAD_BINS) + 1):
        if n[b]:
            out[b] = {s: v / n[b] for s, v in acc[b].items()}
    return out, dict(n)


def rates(gs, fade, sts):
    """His state rates (on / game seconds), games weighted fade^(games ago), and the seconds behind each."""
    k = len(gs)
    on, gm = defaultdict(float), defaultdict(float)
    for j, g in enumerate(gs):
        w = fade ** (k - 1 - j)
        for s in sts:
            gm[s] += w * g["gst"].get(s, 0.0)
            on[s] += w * g["on"].get(s, 0.0)
    return on, gm


def simple_minutes(gs, fade, wb, ot=True):
    """(b): overtime scaled to regulation, blowouts (final margin 20+ either way) weighted wb, recency fade."""
    k = len(gs)
    num_ = den = 0.0
    for j, g in enumerate(gs):
        m = g["min"] * 40.0 / (40 + 5 * g["nOT"]) if ot else g["min"]
        w = fade ** (k - 1 - j) * (wb if abs(g["margin"]) >= 20 else 1.0)
        num_ += w * m
        den += w
    return num_ / den if den else None


def form_min(gs):
    """Today's current-season minutes: FORM-weighted (0.8 per game back), the weights' sum."""
    k = len(gs)
    w = [0.8 ** (k - 1 - j) for j in range(k)]
    return sum(x * g["min"] for x, g in zip(w, gs)) / sum(w), sum(w)


def load_games(data):
    """Every D1 game parsed (parsed/*.json from the fetch: parse()'s output, compact), else the raw summaries."""
    pj = sorted(glob.glob(os.path.join(data, "parsed", "*.json")))
    if pj:
        out = []
        for f in pj:
            g = json.load(open(f))
            if g.get("skip"):
                continue
            g["foul_lim"] = set(g["foul_lim"])
            g["secs"] = {p: {int(k): v for k, v in d.items()} for p, d in g["secs"].items()}
            g["segs"] = [tuple(x) for x in g["segs"]]
            out.append(g)
        return out
    return [g for g in (parse(f) for f in sorted(glob.glob(os.path.join(data, "sum", "*.json")))) if g]


def load_nightly(brr):
    sys.path.insert(0, os.path.join(brr, "scripts"))
    import cbb_nightly
    return cbb_nightly


def slate_rows(brr):
    """[(name, game day, {dk_id: proj row}, {dk_id: graded csv row})] for the graded slates."""
    out = []
    for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))):
        rows = list(csv.DictReader(open(f)))
        if not any(num(r.get("actual_dk")) is not None for r in rows):
            continue
        name = os.path.basename(f)[:-4]
        pj = os.path.join(brr, "data", "dk", "cbb", name + "_proj.json")
        if not os.path.exists(pj):
            continue
        out.append((name, json.load(open(pj)), {r["dk_id"]: r for r in rows}))
    return out


def project_slate(cn, proj, model, pp_clean, pp_box, ctx, params):
    """New final minutes {dk_id: min} for one slate under model a / b / c / c-margin."""
    rows = copy.deepcopy(proj)
    starts = [r.get("game_start") for r in rows.values() if r.get("game_start")]
    before = min(starts) if starts else "9999"
    changed = 0
    ppmr, ctx_changed = {}, set()
    by_espn = {str(r.get("espn")): r for r in rows.values() if r.get("espn")}
    for k, r in rows.items():
        if r.get("status") == "Out" or r.get("min") is None or model == "a":
            continue
        if r.get("src") not in ("box", "miya"):
            continue
        espn = str(r.get("espn") or "")
        bg = [g for g in pp_box.get(espn, []) if g["date"] < before]
        if not bg:
            continue
        cur, gw = form_min(bg)
        pre = r.get("min_raw", r["min"])
        m_a = None
        for tier_m in (10, 24, 30):        # undo MIN_BY_SPREAD: find m with m x sf(spread, m) = pre
            f = cn.spread_factor(r.get("spread"), tier_m)
            m = pre / f
            if cn.spread_factor(r.get("spread"), m) == f:
                m_a = m
                break
        if m_a is None:
            continue
        sf = cn.spread_factor(r.get("spread"), m_a)
        mp_part = m_a * (gw + cn.MIN_FILL) - gw * cur          # = MIN_FILL x prior minutes (or 0 with no prior)
        if model in ("b_ctx", "d"):
            t = r.get("espn_team")
            tops = [x for x in ctx[("tops", before)].get(t, []) if x != espn]
            st_of = lambda x: (by_espn.get(x) or {}).get("status") if x in by_espn else "Out"
            out_now = {x for x in tops if st_of(x) == "Out"}
            qs = [x for x in tops if st_of(x) == "Questionable"][:2]
            combos = [(frozenset(out_now), 1.0)]
            for x in qs:
                pp_ = (by_espn.get(x) or {}).get("p_play")
                pp_ = 0.8 if pp_ is None else float(pp_)
                combos = [(c, w * pp_) for c, w in combos] + [(c | {x}, w * (1 - pp_)) for c, w in combos]
            last = bg[-1]
            if {x for x in tops if x not in ctx["ps"].get((last["gid"], t), set())} != out_now:
                ctx_changed.add(k)
            tot_m = tot_r = 0.0
            ok = True
            for A, w in combos:
                res_ = ctx_minutes(model, espn, t, A, tops, bg, pp_clean, ctx, params, r, before)
                if res_ is None:
                    ok = False
                    break
                tot_m += w * res_[0]
                tot_r += w * res_[1]
            if not ok:
                continue
            if model == "b_ctx":
                new = (gw * tot_m + mp_part) / (gw + cn.MIN_FILL) * sf
            else:
                new = (gw * tot_m + mp_part * sf) / (gw + cn.MIN_FILL)
            ppmr[k] = tot_r
        elif model == "b":
            nb = simple_minutes(bg, params["fade_b"], params["wb"], params.get("ot", True))
            if nb is None:                  # every game a blowout at weight 0: today's number stands
                continue
            new = (gw * nb + mp_part) / (gw + cn.MIN_FILL) * sf
        else:
            mode = {"c_margin": "margin", "c_wp0": "wp0"}.get(model, "wp")
            cg = [g for g in pp_clean[mode].get(espn, []) if g["date"] < before]
            if len(cg) < 1:
                continue
            sts = MSTATES if mode == "margin" else STATES
            comp_key = "M0" if mode == "margin" else "COMP"
            tm, lg, role_of = ctx[(mode, before, params["fade_c"])]
            stime = ctx[(mode, before, "stime")]
            q, _ = qmin_minutes_mode(cg, r.get("espn_team"), r.get("spread"), stime, tm, lg, role_of.get(espn, 1),
                                     params["fade_c"], params["k_player"], sts, comp_key)
            if q is None:
                continue
            new = (gw * q + mp_part * sf) / (gw + cn.MIN_FILL)
        r["min"] = max(0.0, min(40.0, new))
        r.pop("min_raw", None)
        changed += 1
    for r in rows.values():                   # team_minutes wants these
        r.setdefault("fp", r.get("fp_dk") or 0.0)
    if model != "a":
        cn.team_minutes(list(rows.values()))
    mins = {k: r.get("min") for k, r in rows.items()}
    if model in ("b_ctx", "d"):
        return mins, changed, ppmr, ctx_changed
    return mins, changed


def qmin_minutes_mode(gs, team, spread, stime, tm, lg, role, fade, k_player, sts, comp_key):
    on, gm = rates(gs, fade, sts)
    prior = (tm.get(team) or {}).get(role) or lg.get(role) or {s: 0.0 for s in sts}
    st = stime.get(spread_bin(spread)) or {}
    if not st:
        return None, None
    exp, r = 0.0, {}
    for s in sts:
        src = comp_key if s == "OT" else s
        kk = min(k_player, 10) if src == comp_key else k_player
        r[s] = (on[src] + kk * 60 * prior.get(src, 0.0)) / (gm[src] + kk * 60)
        exp += st.get(s, 0.0) * r[s] / 60.0
    return exp, 40 * r[comp_key]


def grade(rows_csv, mins_new, mins_a, ppmr=None, subset=None):
    """Per slate: ROTATION minutes MAE, top-5 match / rank agreement within the band, STARS points MAE, with the new
    minutes (points per minute held against (a)'s)."""
    rot, star = [], []
    for k, r in rows_csv.items():
        if subset is not None and k not in subset:
            continue
        fp = num(r.get("fp_dk"))
        act, mn = num(r.get("actual_dk")), num(r.get("min"))
        if not fp or fp <= 0 or act is None:
            continue
        ma, mnew = mins_a.get(k), mins_new.get(k)
        if ma is None or mnew is None:
            mnew, ma = num(r.get("min_proj")), num(r.get("min_proj"))
        fpn = (fp * (mnew / ma) if ma else fp) * ((ppmr or {}).get(k) or 1.0)
        rec = (r, mnew, fpn, act, mn)
        if 10 <= fp < 25:
            rot.append(rec)
        elif fp >= 25:
            star.append(rec)
    mae = lambda v: S.mean(abs(x[4] - x[1]) for x in v if x[4] is not None and x[1] is not None) if v else None
    pmae = lambda v: S.mean(abs(x[3] - x[2]) for x in v) if v else None
    # top-5 minutes match and rank agreement per team, within the band's players of each team
    by_t = defaultdict(list)
    for x in rot + star:
        by_t[x[0]["team"]].append(x)
    t5, rk = [], []
    for v in by_t.values():
        v = [x for x in v if x[4] is not None]
        if len(v) < 5:
            continue
        top_p = set(id(x) for x in sorted(v, key=lambda x: -x[1])[:5])
        top_a = set(id(x) for x in sorted(v, key=lambda x: -x[4])[:5])
        t5.append(len(top_p & top_a))
        rk.append(spearman([x[1] for x in v], [x[4] for x in v]))
    return {"rot_min": mae(rot), "rot_n": len(rot), "star_pts": pmae(star), "star_n": len(star),
            "top5": S.mean(t5) if t5 else None, "rank": S.mean([x for x in rk if x is not None]) if rk else None}


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    return corr(ra, rb) if len(a) > 2 else None


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for t in range(i, j + 1):
            r[o[t]] = (i + j) / 2
        i = j + 1
    return r


def se(xs):
    return S.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else float("inf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brr", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--md")
    a = ap.parse_args()
    cn = load_nightly(a.brr)
    games = load_games(a.data)
    P, nobs = fit_wp(games)
    P0, _ = fit_wp(games, ks=(0.0,))
    PMODE.update(wp=P, wp0=P0)
    out = {"games": len(games), "wp": {"sig": P[0], "k": P[1], "eps": P[2], "segments": nobs}, "wp0": {"sig": P0[0], "eps": P0[2]}}
    pp_clean = {}
    covs = {}
    for mode in ("wp", "wp0", "margin"):
        pp_clean[mode], covs[mode] = clean_games(games, P, mode)
    out["coverage"] = covs["wp"]
    out["stability"] = stability(pp_clean["wp"])
    pp_box = all_box_games(games)
    rs = return_study(games, pp_clean["wp"])
    out["returns"] = rs
    p_keep = max(0.0, min(1.0, rs["persist_min"] or 0.0))
    ps, _ = played_sets(games)
    sl = slate_rows(a.brr)
    out["slates"] = [s[0] for s in sl]
    # contexts per slate
    ctx = {"ps": ps}
    befores = {}
    for name, proj, _ in sl:
        starts = [r.get("game_start") for r in proj.values() if r.get("game_start")]
        b = min(starts)
        befores[name] = b
        ctx[("tops", b)] = team_tops(pp_clean["wp"], b, 5)
        for mode in ("wp", "wp0", "margin"):
            sts = MSTATES if mode == "margin" else STATES
            ctx[(mode, b, "stime")] = state_time(pp_clean[mode], b, mode)[0]
            for fade in (1.0, 0.9, 0.8, 0.7, 0.6):
                ctx[(mode, b, fade)] = role_tables_mode(pp_clean[mode], b, fade, sts, 60, "M0" if mode == "margin" else "COMP")
    grid_b = [{"fade_b": f, "wb": w, "ot": o} for f in (1.0, 0.9, 0.8, 0.7) for w in (1.0, 0.5, 0.25, 0.0) for o in (True, False)]
    grid_c = [{"fade_c": f, "k_player": k} for f in (1.0, 0.9, 0.8, 0.7, 0.6) for k in (15, 30, 60, 120)]
    res = {}                     # (model, params str, slate) -> grade
    mins_a = {}
    for name, proj, rc in sl:
        ma, _ = project_slate(cn, proj, "a", pp_clean, pp_box, ctx, {})
        mins_a[name] = ma
        res[("a", "", name)] = grade(rc, ma, ma)
        for p in grid_b:
            mn, ch = project_slate(cn, proj, "b", pp_clean, pp_box, ctx, p)
            res[("b", json.dumps(p, sort_keys=True), name)] = dict(grade(rc, mn, ma), changed=ch)
        for model in ("c", "c_wp0", "c_margin"):
            for p in grid_c:
                mn, ch = project_slate(cn, proj, model, pp_clean, pp_box, ctx, p)
                res[(model, json.dumps(p, sort_keys=True), name)] = dict(grade(rc, mn, ma), changed=ch)
    grid_bx = [{"fade_b": f, "wb": w, "ot": True, "k_ctx": k, "p_keep": p_keep} for f in (0.8, 0.7) for w in (1.0, 0.5) for k in (1, 2, 4, 8)]
    grid_d = [{"fade_c": f, "k_player": kp, "k_ctx": k, "p_keep": p_keep} for f in (0.9, 0.8) for kp in (15, 30) for k in (1, 2, 4, 8)]
    subsets = {}
    for name, proj, rc in sl:
        ma = mins_a[name]
        for model, grid in (("b_ctx", grid_bx), ("d", grid_d)):
            for p in grid:
                mn, ch, pr, cc = project_slate(cn, proj, model, pp_clean, pp_box, ctx, p)
                res[(model, json.dumps(p, sort_keys=True), name)] = dict(grade(rc, mn, ma, pr), changed=ch)
                subsets[name] = cc
    names = [s[0] for s in sl]

    def held_out(model, grid):
        """Each slate: the params best on the other slates (pooled rotation minutes MAE), applied to it."""
        rows = []
        for n in names:
            others = [x for x in names if x != n]
            best = min(grid, key=lambda p: S.mean(res[(model, json.dumps(p, sort_keys=True), o)]["rot_min"] for o in others))
            g = res[(model, json.dumps(best, sort_keys=True), n)]
            rows.append((n, best, g))
        return rows
    out["held"] = {}
    grid_b_ot = [p for p in grid_b if p["ot"]]
    grid_b_noot = [p for p in grid_b if not p["ot"]]
    chosen = {}
    for model, grid, key in (("b", grid_b_ot, "b"), ("b", grid_b_noot, "b_no_ot"), ("c", grid_c, "c"), ("c_wp0", grid_c, "c_wp0"), ("c_margin", grid_c, "c_margin"),
                             ("b_ctx", grid_bx, "b_ctx"), ("d", grid_d, "d")):
        hr = held_out(model, grid)
        chosen[key] = {n: p for n, p, _ in hr}
        d_rot = [res[("a", "", n)]["rot_min"] - g["rot_min"] for n, _, g in hr]
        d_star = [g["star_pts"] - res[("a", "", n)]["star_pts"] for n, _, g in hr if g["star_pts"] is not None]
        d_t5 = [g["top5"] - res[("a", "", n)]["top5"] for n, _, g in hr if g["top5"] is not None and res[("a", "", n)]["top5"] is not None]
        d_rk = [g["rank"] - res[("a", "", n)]["rank"] for n, _, g in hr if g["rank"] is not None and res[("a", "", n)]["rank"] is not None]
        out["held"][key] = {
            "per_slate": [{"slate": n, "params": p, "a_rot": res[("a", "", n)]["rot_min"], "rot": g["rot_min"],
                           "a_star": res[("a", "", n)]["star_pts"], "star": g["star_pts"], "a_top5": res[("a", "", n)]["top5"],
                           "top5": g["top5"], "a_rank": res[("a", "", n)]["rank"], "rank": g["rank"], "changed": g.get("changed")} for n, p, g in hr],
            "rot_gain": S.mean(d_rot), "rot_se": se(d_rot), "better": sum(x > 0 for x in d_rot), "of": len(d_rot),
            "star_worse": S.mean(d_star), "star_se": se(d_star), "top5_gain": S.mean(d_t5), "rank_gain": S.mean(d_rk),
            "a_rot": S.mean(res[("a", "", n)]["rot_min"] for n in names), "rot": S.mean(g["rot_min"] for _, _, g in hr),
            "params_all": min(grid, key=lambda p: S.mean(res[(model, json.dumps(p, sort_keys=True), o)]["rot_min"] for o in names))}
    # the player-nights whose key teammates' availability changed from his last game: rotation minutes MAE per model
    sub = defaultdict(lambda: defaultdict(list))
    for name, proj, rc in sl:
        ss = subsets.get(name) or set()
        if not ss:
            continue
        ma = mins_a[name]
        for key, model in (("a", "a"), ("b", "b"), ("c", "c"), ("b_ctx", "b_ctx"), ("d", "d")):
            if key == "a":
                mn, pr = ma, None
            else:
                r_ = project_slate(cn, proj, model, pp_clean, pp_box, ctx, chosen[key][name])
                mn, pr = r_[0], (r_[2] if len(r_) > 2 else None)
            for k_ in ss:
                rr = rc.get(k_)
                if not rr:
                    continue
                fp, mact = num(rr.get("fp_dk")), num(rr.get("min"))
                if fp and 10 <= fp < 25 and mact is not None and mn.get(k_) is not None:
                    sub[key]["err"].append(abs(mact - mn[k_]))
    out["changed_context"] = {k: {"n": len(v["err"]), "rot_min_mae": S.mean(v["err"]) if v["err"] else None} for k, v in sub.items()}
    out["p_keep"] = p_keep
    # state time by spread (all games) and a worked example
    out["state_time"], out["state_n"] = state_time(pp_clean["wp"], "9999", "wp")
    out["example"] = worked_example(pp_clean["wp"], P)
    out["role_change"] = role_flags(pp_clean["wp"])
    json.dump(out, open(a.md.replace(".md", ".json") if a.md else "/dev/stdout", "w"), indent=1, default=str)
    if a.md:
        write_md(a.md, out)


def role_tables_mode(pp, before, fade, sts, k_team, comp_key):
    by_team = defaultdict(list)
    for p, gs in pp.items():
        g0 = [g for g in gs if g["date"] < before]
        if not g0:
            continue
        on, gm = rates(g0, fade, sts)
        q = on[comp_key] / gm[comp_key] if gm[comp_key] else 0.0
        by_team[g0[-1]["team"]].append((q, p, on, gm))
    league = defaultdict(lambda: [defaultdict(float), defaultdict(float)])
    team_role, role_of = {}, {}
    for t, v in by_team.items():
        v.sort(key=lambda x: -x[0])
        tr = defaultdict(lambda: [defaultdict(float), defaultdict(float)])
        for i, (q, p, on, gm) in enumerate(v):
            r = 0 if i < 5 else 1 if i < 8 else 2
            role_of[p] = r
            for s in sts:
                tr[r][0][s] += on[s]
                tr[r][1][s] += gm[s]
                league[r][0][s] += on[s]
                league[r][1][s] += gm[s]
        team_role[t] = tr
    lg = {r: {s: (league[r][0][s] / league[r][1][s] if league[r][1][s] else 0.0) for s in sts} for r in league}
    tm = {t: {r: {s: (on[s] + k_team * 60 * lg[r][s]) / (gm[s] + k_team * 60) for s in sts} for r, (on, gm) in tr.items()}
          for t, tr in team_role.items()}
    return tm, lg, role_of


def role_flags(pp):
    """Players whose last ROLE_N clean games' competitive rate differs from the earlier ones by ROLE_D+."""
    n = flagged = 0
    for p, gs in pp.items():
        c = [g["on"].get("COMP", 0) / g["gst"]["COMP"] for g in gs if g["gst"].get("COMP", 0) >= 300]
        if len(c) >= ROLE_N + 2:
            n += 1
            if abs(S.mean(c[-ROLE_N:]) - S.mean(c[:-ROLE_N])) >= ROLE_D:
                flagged += 1
    return {"players": n, "flagged": flagged}


def worked_example(pp, P):
    """Two teams with different blowout habits: the top-5 players' DECIDED-leading rate vs their COMPETITIVE rate."""
    team = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for p, gs in pp.items():
        on, gm = rates(gs, 1.0, STATES)
        if gm["COMP"] < 1200 or on["COMP"] / gm["COMP"] < 0.6:
            continue
        t = gs[-1]["team"]
        team[t][0] += on["COMP"]; team[t][1] += gm["COMP"]; team[t][2] += on["DEC_L"]; team[t][3] += gm["DEC_L"]
    v = [(t, x[2] / x[3], x[0] / x[1], x[3]) for t, x in team.items() if x[3] >= 1200]
    v.sort(key=lambda x: x[1])
    return {"lowest": v[:3], "highest": v[-3:], "teams": len(v)}


def write_md(path, o):
    """The tables of quality_minutes_<date>.md (the prose around them is written by hand)."""
    L = []
    c = o["coverage"]
    L += ["### Coverage", "", "%d games with play-by-play (every D1 game played to date); %d player-games played, %d clean (%.1f%%): %d dropped "
          "(rebuilt minutes off the box score by more than %.0f), %d foul-limited, %d injury exits." % (
              o["games"], c["player_games"], c["clean"], 100 * c["clean"] / c["player_games"], c["dropped_recon"], RECON_TOL, c["foul_limited"], c["injury_exit"]), ""]
    L += ["### Stability (players with 4+ clean games, 10+ minutes)", "", "| Measure | Players | Game-to-game SD | CV | Odd vs even games r |", "|---|---|---|---|---|"]
    for k, v in o["stability"].items():
        L.append("| %s | %d | %.2f | %.3f | %.3f |" % (k, v["players"], v["sd"], v["cv"], v["split_r"]))
    L += ["", "### Held out by slate (14 graded slates; rotation 10-25 minutes MAE; parameters chosen on the other 13)", "",
          "| Model | Today | Model | Gain | SE | Better | Stars points (model - today) | Top-5 | Rank | Parameters (all slates) |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, h in o["held"].items():
        L.append("| %s | %.3f | %.3f | %+.3f | %.3f | %d of %d | %+.3f (SE %.3f) | %+.3f | %+.3f | %s |" % (
            k, h["a_rot"], h["rot"], h["rot_gain"], h["rot_se"], h["better"], h["of"], h["star_worse"], h["star_se"], h["top5_gain"], h["rank_gain"],
            json.dumps(h["params_all"])))
    L += ["", "### (b) per slate", "", "| Slate | Parameters | Today | (b) | Stars today | Stars (b) | Players moved |", "|---|---|---|---|---|---|---|"]
    for r in o["held"]["b"]["per_slate"]:
        L.append("| %s | %s | %.2f | %.2f | %.2f | %.2f | %s |" % (r["slate"], json.dumps(r["params"]), r["a_rot"], r["rot"], r["a_star"], r["star"], r["changed"]))
    L += ["", "### State time by tonight's spread (minutes of the game, from the team's side; all games)", "",
          "| Spread bin | Games | " + " | ".join(STATES) + " |", "|---|---|" + "---|" * len(STATES)]
    edges = ["<-20", "-20..-12", "-12..-6", "-6..-2", "-2..2", "2..6", "6..12", "12..20", "20+"]
    for b in sorted(o["state_time"], key=int):
        st = o["state_time"][b]
        L.append("| %s | %s | %s |" % (edges[int(b)], o["state_n"].get(b, o["state_n"].get(int(b), "")), " | ".join("%.1f" % (st.get(s, 0) / 60) for s in STATES)))
    r = o["returns"]
    L += ["", "### Returns (6b)", "", "%d cases (a top-5 QMIN player out 2+ straight games, then back), %d teammate observations. Persistence (slope of return - "
          "before on during - before): minutes rate %.2f, DK per minute %.2f; by case, minutes median %.2f (quartiles %.2f to %.2f)." % (
              r["n_cases"], r["teammate_obs"], r["persist_min"], r["persist_dkpm"], *r["case_persist_min"]), ""]
    m = r["mirror"]
    L += ["The mirror (his first missed game): his %.0f minutes before; teammates gained %.0f: top 5 %.0f, 6-8 %.0f, 9+ %.0f; same position %.0f, "
          "other %.0f." % (m["his minutes"], m["gained total"], m["top5"], m["6-8"], m["9+"], m["same position"], m["other position"]), ""]
    L += ["### Availability changed since his last game (rotation, n %d)" % o["changed_context"]["a"]["n"], "",
          "| Model | Minutes MAE |", "|---|---|"] + ["| %s | %.2f |" % (k, v["rot_min_mae"]) for k, v in o["changed_context"].items()]
    open(path, "w").write("\n".join(L) + "\n")



# --- step 6: lineup context ----------------------------------------------------------------------------------------
MIN_TOP = 3            # clean games for a player to rank in his team's top 5 / top 8 by QMIN


def played_sets(games):
    """{(game id, team): set of players who played}, and each team's games in order."""
    ps, tg = {}, defaultdict(list)
    for g in games:
        for t in (g["home"], g["away"]):
            ps[(g["id"], t)] = {p for p, b in g["box"].items() if b["team"] == t and b["min"] > 0}
            tg[t].append((g["date"], g["id"]))
    for v in tg.values():
        v.sort()
    return ps, tg


def team_tops(pp, before, n=5):
    """{team: [players]} the top n by QMIN (competitive rate) among players with MIN_TOP+ clean games before `before`."""
    by = defaultdict(list)
    for p, gs in pp.items():
        g0 = [g for g in gs if g["date"] < before]
        if len(g0) < MIN_TOP:
            continue
        on = sum(g["on"].get("COMP", 0) for g in g0)
        gm = sum(g["gst"].get("COMP", 0) for g in g0)
        if gm >= 600:
            by[g0[-1]["team"]].append((on / gm, p))
    return {t: [p for _, p in sorted(v, reverse=True)[:n]] for t, v in by.items()}


def return_study(games, pp):
    """6b: every top-5 (season QMIN) player who missed 2+ straight team games and came back. Teammates (top 8, present in
    every phase) before / during / return: competitive rate and DK per minute; persistence = the slope of (return -
    before) on (during - before). The mirror: on the first absence game, where his minutes went (role, position)."""
    ps, tg = played_sets(games)
    top5, top8 = team_tops(pp, "9999", 5), team_tops(pp, "9999", 8)
    clean = {(p, g["gid"]): g for p, gs in pp.items() for g in gs}
    pos = {}
    for g in games:
        for p, b in g["box"].items():
            pos[p] = b.get("pos") or pos.get(p, "")
    cases, obs_m, obs_u, mirror = [], [], [], []
    for t, games_t in tg.items():
        seq = [gid for _, gid in games_t]
        for x in top5.get(t, []):
            pres = [x in ps[(gid, t)] for gid in seq]
            i = 0
            while i < len(seq):
                if pres[i]:
                    i += 1
                    continue
                j = i
                while j < len(seq) and not pres[j]:
                    j += 1
                if i >= 1 and j < len(seq) and j - i >= 2:
                    bef, dur, ret = seq[:i], seq[i:j], seq[j:]
                    cm, cu = [], []
                    for y in top8.get(t, []):
                        if y == x:
                            continue
                        ph = []
                        for part in (bef, dur, ret):
                            gg = [clean[(y, gid)] for gid in part if (y, gid) in clean]
                            on = sum(g["on"].get("COMP", 0) for g in gg)
                            gm = sum(g["gst"].get("COMP", 0) for g in gg)
                            mn = sum(g["min"] for g in gg)
                            dk = sum(g["dk"] for g in gg)
                            ph.append((on / gm if gm >= 120 else None, dk / mn if mn >= 10 else None))
                        if all(v[0] is not None for v in ph):
                            cm.append((ph[0][0], ph[1][0], ph[2][0]))
                        if all(v[1] is not None for v in ph):
                            cu.append((ph[0][1], ph[1][1], ph[2][1]))
                    sl = lambda o: (sum((r - b) * (d - b) for b, d, r in o) / sum((d - b) ** 2 for b, d, r in o)) if o and sum((d - b) ** 2 for b, d, r in o) > 1e-9 else None
                    cases.append({"team": t, "player": x, "missed": j - i, "teammates": len(cm), "persist_min": sl(cm), "persist_dkpm": sl(cu)})
                    obs_m += cm
                    obs_u += cu
                    # the mirror: his minutes before, teammates' change on the first absence game
                    xb = [clean[(x, gid)]["min"] for gid in bef if (x, gid) in clean]
                    if xb:
                        g1 = dur[0]
                        for y in top8.get(t, []) + [p for p in ps[(g1, t)] if p not in top8.get(t, [])]:
                            if y == x:
                                continue
                            yb = [clean[(y, gid)]["min"] for gid in bef if (y, gid) in clean]
                            if (y, g1) in clean and yb:
                                role = "top5" if y in top5.get(t, []) else "6-8" if y in top8.get(t, []) else "9+"
                                mirror.append({"case": len(cases) - 1, "x_min": S.mean(xb), "gain": clean[(y, g1)]["min"] - S.mean(yb), "role": role,
                                               "same_pos": (pos.get(y, "")[:1] == pos.get(x, "")[:1]) and bool(pos.get(x))})
                i = j
    slope = lambda o: (sum((r - b) * (d - b) for b, d, r in o) / sum((d - b) ** 2 for b, d, r in o)) if o else None
    pm = [c["persist_min"] for c in cases if c["persist_min"] is not None]
    pu = [c["persist_dkpm"] for c in cases if c["persist_dkpm"] is not None]
    mir = {}
    if mirror:
        tot = sum(m["gain"] for m in mirror)
        xs = defaultdict(float)
        for m in mirror:
            xs[m["case"]] = m["x_min"]
        for k_, f in (("top5", lambda m: m["role"] == "top5"), ("6-8", lambda m: m["role"] == "6-8"), ("9+", lambda m: m["role"] == "9+"),
                      ("same position", lambda m: m["same_pos"]), ("other position", lambda m: not m["same_pos"])):
            mir[k_] = sum(m["gain"] for m in mirror if f(m))
        mir["his minutes"] = sum(xs.values())
        mir["gained total"] = tot
    return {"cases": cases, "n_cases": len(cases), "teammate_obs": len(obs_m), "persist_min": slope(obs_m), "persist_dkpm": slope(obs_u),
            "case_persist_min": (S.median(pm), sorted(pm)[len(pm) // 4] if pm else None, sorted(pm)[3 * len(pm) // 4] if pm else None) if pm else None,
            "case_persist_dkpm": (S.median(pu),) if pu else None, "mirror": mir}


def ctx_weights(gs, t, absent_tonight, tops, ps, p_keep):
    """Per game: (matched?, season weight). A game matches when the same top-5 teammates were missing as tonight; an
    absence game (a top-5 teammate out then, playing tonight) carries over at p_keep."""
    out = []
    for g in gs:
        miss = {x for x in tops if x not in ps.get((g["gid"], t), set())}
        out.append((miss == absent_tonight, p_keep if (miss - absent_tonight) else 1.0, miss))
    return out


def simple_w(gs, fade, wb, ot, extra):
    k = len(gs)
    num_ = den = 0.0
    for j, (g, x) in enumerate(zip(gs, extra)):
        m = g["min"] * 40.0 / (40 + 5 * g["nOT"]) if ot else g["min"]
        w = fade ** (k - 1 - j) * (wb if abs(g["margin"]) >= 20 else 1.0) * x
        num_ += w * m
        den += w
    return num_ / den if den else None


def ppm_w(gs, extra, fade=1.0):
    k = len(gs)
    a = sum(fade ** (k - 1 - j) * x * g["dk"] for j, (g, x) in enumerate(zip(gs, extra)))
    b = sum(fade ** (k - 1 - j) * x * g["min"] for j, (g, x) in enumerate(zip(gs, extra)))
    return a / b if b >= 10 else None


def ctx_minutes(model, espn, t, A, tops, bg, pp_clean, ctx, params, r, before):
    """(current-season minutes tonight under absent set A, DK-per-minute ratio vs his plain season rate)."""
    kk, pk = params["k_ctx"], params["p_keep"]
    cw = ctx_weights(bg, t, set(A), tops, ctx["ps"], pk)
    n_m = sum(1 for m, _, _ in cw if m)
    wm = n_m / (n_m + kk) if n_m else 0.0
    plain = ppm_w(bg, [1.0] * len(bg))
    pm = ppm_w(bg, [1.0 if m else 0.0 for m, _, _ in cw])
    ps_ = ppm_w(bg, [w for _, w, _ in cw])
    ppm_c = (wm * pm + (1 - wm) * ps_) if (pm is not None and ps_ is not None) else ps_
    ratio = max(0.8, min(1.25, ppm_c / plain)) if (plain and ppm_c) else 1.0
    if model == "b_ctx":
        sm = simple_w(bg, params["fade_b"], params["wb"], params.get("ot", True), [1.0 if m else 0.0 for m, _, _ in cw])
        ss = simple_w(bg, params["fade_b"], params["wb"], params.get("ot", True), [w for _, w, _ in cw])
        if ss is None:
            return None
        return (wm * sm + (1 - wm) * ss) if sm is not None else ss, ratio
    cg = [g for g in pp_clean["wp"].get(espn, []) if g["date"] < before]
    if not cg:
        return None
    ccw = ctx_weights(cg, t, set(A), tops, ctx["ps"], pk)
    sts = STATES
    fade = params["fade_c"]
    tm, lg, role_of = ctx[("wp", before, fade)]
    prior = (tm.get(t) or {}).get(role_of.get(espn, 1)) or lg.get(role_of.get(espn, 1)) or {x: 0.0 for x in sts}
    st = (ctx[("wp", before, "stime")] or {}).get(spread_bin(r.get("spread"))) or {}
    if not st:
        return None
    nm = sum(1 for m, _, _ in ccw if m)
    wmc = nm / (nm + kk) if nm else 0.0
    kgs = len(cg)

    def acc(sel):
        on, gm = defaultdict(float), defaultdict(float)
        for j, (g, x) in enumerate(zip(cg, sel)):
            w = fade ** (kgs - 1 - j) * x
            for s_ in sts:
                gm[s_] += w * g["gst"].get(s_, 0.0)
                on[s_] += w * g["on"].get(s_, 0.0)
        return on, gm
    on_m, gm_m = acc([1.0 if m else 0.0 for m, _, _ in ccw])
    on_s, gm_s = acc([w for _, w, _ in ccw])
    exp = 0.0
    for s_ in sts:
        src = "COMP" if s_ == "OT" else s_
        kp = min(params["k_player"], 10) if src == "COMP" else params["k_player"]
        rs = (on_s[src] + kp * 60 * prior.get(src, 0.0)) / (gm_s[src] + kp * 60)
        if gm_m[src] > 0:
            rm = (on_m[src] + kp * 60 * prior.get(src, 0.0)) / (gm_m[src] + kp * 60)
            rs = wmc * rm + (1 - wmc) * rs
        exp += st.get(s_, 0.0) * rs / 60.0
    return exp, ratio


if __name__ == "__main__":
    main()
