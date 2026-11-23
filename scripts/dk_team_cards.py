"""The team write-up (2026-11-23, the operator's build, display only): per team, per slate, a conversational card,
rotation and minutes first, every number computed from our data, every verdict a named rule below. Nothing here moves a
projection, the draw or the field.

Sources (nothing typed by hand):
  - the slate card: mirror dk_cbb_morning.json (projected minutes, salary, status, Vegas O/U and spread, EvanMiya's
    DK rate miya_ppm and OBPR, the out redistribution out_from / out_gain, p_play and its reason);
  - EvanMiya's newest files in battle-royale-research cbb/inputs/evanmiya: team ratings (Off Rank, Def Rank, True Tempo,
    Tempo Rank) and player ratings (OBPR, for the team rank);
  - ESPN box scores (site.api summary per completed game, the same calls dk_cbb_teams.py makes): per game minutes, the
    starter flag, position, and the stat line, scored in DraftKings points here (dk_points);
  - the analysts' posts in mirror cbb_news.json (kind analyst), kept as they are.

  python3 scripts/dk_team_cards.py sample --team CLEM --slate 157021 --out analysis/cbb/dk/team_card_sample
  python3 scripts/dk_team_cards.py backtest          (the pool-advice rule on the graded slates)
"""
import argparse, csv, glob, html, json, math, os, statistics as S, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MIRROR = os.path.join(HERE, "..", "..", "br-adp-mirror")
BRR = os.path.join(HERE, "..", "..", "battle-royale-research")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball"

# ---- the rules (each one a named constant; the card's wording follows them and nothing else) ----------------------
ROTATION_PROJ_MIN = 10.0
"""A player gets a line in the card when he is not Out and projected for this many minutes or more tonight."""
TIGHT_TOP7, DEEP_TOP7 = 0.90, 0.80
"""Rotation shape from the season's box scores: the top 7 by minutes take this share of the team's minutes or more:
tight; under DEEP_TOP7: deep; between: standard."""
MPG_BAR = 15.0
"""'Rotation regular': 15+ minutes a game over the games he played."""
MIN_SAFE_BAND = 3.0
"""'Minutes safe as projected': tonight's projection within 3 minutes of both his season average and his last 3."""
RISE_MIN = 3.0
"""'Rising role' / 'shrinking role': his last 3 games average 3+ minutes above / below his season average."""
PROJ_ABOVE_MIN = 3.0
"""'Projection above recent role': tonight's projection 3+ minutes over the higher of his season and last-3 averages
(the out redistribution, out_gain, is named when it explains it)."""
HIT_X, CEILING_X, FLOOR_X = 4.0, 5.0, 2.0
"""Per game, against tonight's salary: a 'hit' is 4x salary (in thousands) DraftKings points, a 'ceiling game' 5x, a
'floor game' under 2x. Past games are judged at tonight's price."""
FORM_GAMES = 5
"""Recent DraftKings output = points per minute over his last 5 games played."""
BOUNCE_BELOW, HOT_ABOVE = 0.85, 1.15
"""Recent output against EvanMiya's skills-based DraftKings rate (miya_ppm): under 0.85 of it 'due to bounce back',
over 1.15 'running hot, regression risk', between 'in line'. Needs 3+ games and a Miya rate."""
SHY_CV, SHY_MPG = 0.25, 20.0
"""'Shy away even if starting': his minutes' coefficient of variation 0.25+ and his average under 20."""
MIXED_ROLE = (0.0, 1.0)
"""A position group is 'moving' when two or more of its players have both started and come off the bench this season
(start rate strictly between 0 and 1)."""
POOL_LAST_N, POOL_MIN_PROJ = 5, 20.0
"""Pool advice: a rotation player with no ceiling game (CEILING_X) in his last 5 games played AND projected under 20
minutes. Backtest (backtest()): 2026-11 graded slates, the rule's group hit 5x on the night at 5.0% (15 of 302) against
17.8% (76 of 427) for everyone else."""
POOL_HOLDS = 0.5
"""The pool rule is worded as advice ('leave out of your pool') only while the backtest holds: the rule group's 5x rate
at most half the others' pooled AND lower on 3 of 4 slates or more; otherwise it is worded 'rarely hits a ceiling'."""
GRIND_TEMPO, PACE_TEMPO, OU_GAP = 240, 120, 5.0
"""Game environment: both teams' EvanMiya tempo ranks averaging 240+ (slow) or the slate's lowest O/U by 5+ points:
a grind; averaging 120 or better and not the slate's lowest O/U: a pace-up spot; otherwise middling."""
NEW_OUT_MIN_GP = 1
"""An Out player who has played this many games this season or more is a NEW out: his minutes' redistribution (out_gain)
is listed. A season-long out (0 games) is already missing from everyone's averages, so no list (it reads as double
counting)."""
CORE_MIN_PROJ, CORE_MAX_CV, CORE_MAX = 30.0, 0.15, 3
"""Bottom line, Core: projected 30+ minutes, his minutes' coefficient of variation at most 0.15 (a stable role), started
every game he played; the top 3 by projected minutes at most."""
VALUE_MAX_SALARY, VALUE_MIN_PROJ, VALUE_MIN_CEIL = 5000, 25.0, 2
"""Bottom line, Value: salary $5,000 or less, projected 25+ minutes, 2+ ceiling games (CEILING_X) this season; the
running-hot verdict (HOT_ABOVE) is named as a caveat when it fires."""
STRONG_MIN_PROJ = 27.0
"""Bottom line, Strong: projected 27+ minutes (with STRONG_MAX_CV and STRONG_STARTS or STRONG_TOP_DK)."""
STRONG_MAX_CV = 0.20
"""Bottom line, Strong: his minutes' coefficient of variation at most 0.20 over the games he played."""
STRONG_STARTS = 4
"""Bottom line, Strong: started 4+ of his last STRONG_LAST games played ..."""
STRONG_LAST = 5
"""... the window for STRONG_STARTS."""
STRONG_TOP_DK = 2
"""... or top 2 on the team in DraftKings points a game (among tonight's rotation lines). Core and Value players are
not repeated as Strong."""
JOB_START_RATE, STEADY_MIN_MPG, LOW_START_MPG = 0.75, 25.0, 20.0
"""A moving position group, read player by player: started 75%+ of his games: 'has the starting job'; 25+ mpg with
minutes CV at most CORE_MAX_CV while starting under half: 'minutes as steady as a starter's'; started half or more but
a median under 20 minutes: 'starts but plays little'. The team's best DraftKings rate per minute among the rotation is
named where its holder is in the group."""
MOST_NIGHTS = 0.6
"""'Plays a-b most nights': the range of his lowest 60% of games by minutes."""
DD_STATS = ("PTS", "REB", "AST", "STL", "BLK")


def dk_points(v):
    """DraftKings CBB Classic points from an ESPN box line (dict of stat name -> string): points 1, made three +0.5,
    rebound 1.25, assist 1.5, steal 2, block 2, turnover -0.5, double-double +1.5, triple-double +3."""
    n = lambda k: float(str(v.get(k) or 0).split("-")[0] or 0)
    tpm = n("3PT")
    tens = sum(n(k) >= 10 for k in DD_STATS)
    return (n("PTS") + 0.5 * tpm + 1.25 * n("REB") + 1.5 * n("AST") + 2 * n("STL") + 2 * n("BLK") - 0.5 * n("TO")
            + (1.5 if tens >= 2 else 0) + (3 if tens >= 3 else 0))


def minutes_note(proj, season, last3, out_gain=None):
    """The minutes verdict (MIN_SAFE_BAND, RISE_MIN, PROJ_ABOVE_MIN), or None."""
    if season is None:
        return None
    if proj >= max(season, last3) + PROJ_ABOVE_MIN:
        return "projection above recent role" + (" (+%.0f from the outs)" % out_gain if out_gain and out_gain >= 1 else "")
    if last3 - season >= RISE_MIN:
        return "rising role"
    if season - last3 >= RISE_MIN:
        return "shrinking role"
    if abs(proj - season) <= MIN_SAFE_BAND and abs(proj - last3) <= MIN_SAFE_BAND:
        return "minutes safe as projected"
    return None


def count_games(dks, salary, x):
    """Games with DraftKings points at or over x times the salary in thousands (HIT_X, CEILING_X)."""
    return sum(d >= x * salary / 1000 for d in dks)


def cv(xs):
    """Coefficient of variation of a list (population sd / mean); 0 for an empty or zero list."""
    return S.pstdev(xs) / S.mean(xs) if xs and S.mean(xs) else 0.0


def new_out(played):
    """NEW_OUT_MIN_GP: True for an out who has played this season."""
    return played >= NEW_OUT_MIN_GP


def is_core(L):
    """CORE_MIN_PROJ, CORE_MAX_CV: a stable 30-minute starter."""
    return (L["proj_min"] or 0) >= CORE_MIN_PROJ and L["gp"] >= 3 and L["starts"] == L["gp"] and cv(L["mins"]) <= CORE_MAX_CV


def is_strong(L, top_dk_names):
    """STRONG_MIN_PROJ, STRONG_MAX_CV, STRONG_STARTS / STRONG_LAST or STRONG_TOP_DK (top_dk_names: the team's top
    STRONG_TOP_DK by DK points a game)."""
    return ((L["proj_min"] or 0) >= STRONG_MIN_PROJ and L["gp"] >= 3 and cv(L["mins"]) <= STRONG_MAX_CV
            and (sum(L.get("start_flags", [])[-STRONG_LAST:]) >= STRONG_STARTS or L["name"] in top_dk_names))


def is_value(L):
    """VALUE_MAX_SALARY, VALUE_MIN_PROJ, VALUE_MIN_CEIL."""
    return L["salary"] <= VALUE_MAX_SALARY and (L["proj_min"] or 0) >= VALUE_MIN_PROJ and L["ceil"] >= VALUE_MIN_CEIL


def group_read(L, best_ppm_name):
    """One sentence on a moving group's player (JOB_START_RATE, STEADY_MIN_MPG, LOW_START_MPG), or None."""
    rate = L["starts"] / L["gp"] if L["gp"] else 0
    med = S.median(L["mins"]) if L["mins"] else 0
    best = " and the team's best per-minute rate (%.2f)" % L["dk_pm"] if L["name"] == best_ppm_name else ""
    if rate >= JOB_START_RATE and med >= LOW_START_MPG:
        return "%s has the starting job (%d of %d)%s" % (last(L["name"]), L["starts"], L["gp"], best)
    if rate < 0.5 and (L["season_mpg"] or 0) >= STEADY_MIN_MPG and cv(L["mins"]) <= CORE_MAX_CV:
        return "%s's %.0f minutes off the bench (%d of %d starts) are as steady as a starter's (%.0f-%.0f)%s" % (
            last(L["name"]), L["season_mpg"], L["starts"], L["gp"], min(L["mins"]), max(L["mins"]), best)
    if rate >= 0.5 and med < LOW_START_MPG:
        lo = sorted(L["mins"])[:max(1, math.ceil(MOST_NIGHTS * len(L["mins"])))]
        return "%s starts (%d of %d) but plays %.0f-%.0f most nights (median %.0f)%s" % (
            last(L["name"]), L["starts"], L["gp"], min(lo), max(lo), med, best)
    return None


def last(name):
    """A last name for the prose (suffixes kept off)."""
    parts = [x for x in name.split() if x.rstrip(".").upper() not in ("JR", "SR", "II", "III", "IV")]
    return parts[-1] if parts else name


def form_note(dks, mins, miya_ppm):
    """(verdict, recent DK per minute, ratio to Miya) over the last FORM_GAMES games (BOUNCE_BELOW, HOT_ABOVE)."""
    d, m = dks[-FORM_GAMES:], mins[-FORM_GAMES:]
    if len(d) < 3 or not miya_ppm or not sum(m):
        return None, (sum(d) / sum(m) if sum(m) else None), None
    ppm = sum(d) / sum(m)
    r = ppm / miya_ppm
    return ("due to bounce back" if r < BOUNCE_BELOW else "running hot, regression risk" if r > HOT_ABOVE else "in line"), ppm, r


def shy_away(mins):
    """SHY_CV / SHY_MPG on the games he played."""
    if len(mins) < 3:
        return False
    mu = S.mean(mins)
    return mu < SHY_MPG and (S.pstdev(mins) / mu if mu else 0) >= SHY_CV


def pool_flag(dks_last, salary, proj_min):
    """True: the pool rule (POOL_LAST_N, POOL_MIN_PROJ, CEILING_X) marks him: no ceiling game in his last N, projected
    under POOL_MIN_PROJ minutes."""
    bar = CEILING_X * salary / 1000
    return len(dks_last) >= 3 and not any(x >= bar for x in dks_last[-POOL_LAST_N:]) and proj_min < POOL_MIN_PROJ


def shape(mins_by_player, games):
    """(label, top-5 share, top-7 share, players at MPG_BAR+): from the season's box minutes."""
    tot = sum(sum(v) for v in mins_by_player.values())
    per = sorted((sum(v) for v in mins_by_player.values()), reverse=True)
    t5, t7 = sum(per[:5]) / tot, sum(per[:7]) / tot
    regs = sum(1 for v in mins_by_player.values() if v and S.mean(v) >= MPG_BAR)
    return ("tight" if t7 >= TIGHT_TOP7 else "deep" if t7 < DEEP_TOP7 else "standard"), t5, t7, regs


def environment(tempo_rank, opp_tempo_rank, ou, slate_ous):
    """'grind' / 'pace-up' / 'middling' (GRIND_TEMPO, PACE_TEMPO, OU_GAP)."""
    lo = sorted(slate_ous)
    lowest_by = (lo[1] - lo[0]) if len(lo) > 1 and ou == lo[0] else 0
    avg = (tempo_rank + opp_tempo_rank) / 2
    if avg >= GRIND_TEMPO or lowest_by >= OU_GAP:
        return "grind"
    if avg <= PACE_TEMPO and ou != lo[0]:
        return "pace-up"
    return "middling"


def variant(key, options):
    """Deterministic phrasing: the same player or team always reads the same way, different ones differ."""
    return options[sum(map(ord, key)) % len(options)]


# ---- data --------------------------------------------------------------------------------------------------------
def get(url, cache):
    if url in cache:
        return cache[url]
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                cache[url] = json.load(r)
                return cache[url]
        except Exception:
            if a == 3:
                raise
            time.sleep(2 ** a)


def boxes(espn_team, cache):
    """This season's completed games, oldest first: [{date, opp, players: {athlete id: {name, pos, starter, min, dk}}}]."""
    evs = sorted((e["date"], e["id"]) for e in get(f"{ESPN}/teams/{espn_team}/schedule", cache).get("events", [])
                 if e["competitions"][0]["status"]["type"].get("completed"))
    out = []
    for date, ev in evs:
        d = get(f"{ESPN}/summary?event={ev}", cache)
        g = {"date": date[:10], "players": {}}
        for team in (d.get("boxscore") or {}).get("players", []):
            if str(team["team"]["id"]) != str(espn_team):
                g["opp"] = team["team"].get("abbreviation")
                continue
            st = team["statistics"][0]
            for a in st["athletes"]:
                v = dict(zip(st["names"], a.get("stats") or []))
                try:
                    m = float(v.get("MIN") or 0)
                except ValueError:
                    m = 0.0
                if m > 0:
                    g["players"][str(a["athlete"]["id"])] = {"name": a["athlete"].get("displayName"), "starter": bool(a.get("starter")),
                                                            "pos": (a["athlete"].get("position") or {}).get("abbreviation"), "min": m, "dk": dk_points(v)}
        out.append(g)
    return out


def miya_files():
    d = os.path.join(BRR, "cbb", "inputs", "evanmiya")
    newest = sorted(glob.glob(os.path.join(d, "*_team_ratings.csv")))[-1]
    day = os.path.basename(newest)[:10]
    teams = list(csv.DictReader(open(newest)))
    players = list(csv.DictReader(open(os.path.join(d, day + "_ratings.csv"))))
    return day, teams, players


def norm(s):
    import unicodedata, re
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.'\-]", " ", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", " ", s)
    return " ".join(s.split())


def miya_team(rows, players):
    """EvanMiya's team name for a slate team: the team most of its slate players are listed under."""
    names = {norm(r["name"]) for r in rows}
    hits = [p["Team"] for p in players if norm(p["Name"]) in names]
    return max(set(hits), key=hits.count) if hits else None


# ---- the card ----------------------------------------------------------------------------------------------------
def build(team, slate_id, cache):
    doc = json.load(open(os.path.join(MIRROR, "dk_cbb_morning.json")))
    sl = next(s for s in doc["slates"] if str(s["draft_group_id"]) == str(slate_id))
    P = sl["players"]
    rows = [dict(v, id=k) for k, v in P.items() if v["team"] == team]
    r0 = rows[0]
    opp = r0["opp"]
    opp_rows = [dict(v, id=k) for k, v in P.items() if v["team"] == opp]
    day, mteams, mplayers = miya_files()
    mt, mo = miya_team(rows, mplayers), miya_team(opp_rows, mplayers)
    T = next(t for t in mteams if t["Team"] == mt)
    O = next(t for t in mteams if t["Team"] == mo)
    games = {}
    for v in P.values():
        games.setdefault(v["game"], v.get("ou"))
    ous = [x for x in games.values() if x]
    ou, spread = r0.get("ou"), r0.get("spread")
    implied = ou / 2 - spread / 2 if ou and spread is not None else None
    env = {"team": mt, "opp": mo, "off_rank": int(T["Off Rank"]), "tempo_rank": int(T["Tempo Rank"]), "tempo": float(T["True Tempo"]),
           "opp_def_rank": int(O["Def Rank"]), "opp_tempo_rank": int(O["Tempo Rank"]), "ou": ou, "spread": spread, "implied": implied,
           "ou_rank": sorted(ous).index(ou) + 1, "ou_n": len(ous), "ous": sorted(ous), "miya_day": day, "game": r0["game"]}
    env["kind"] = environment(env["tempo_rank"], env["opp_tempo_rank"], ou, ous)
    bx = boxes(r0["espn_team"], cache)
    n = len(bx)
    # team-wide from the box scores
    mins_by, dks_by = {}, {}
    for g in bx:
        for pid, x in g["players"].items():
            mins_by.setdefault(pid, []).append(x["min"])
            dks_by.setdefault(pid, []).append(x["dk"])
    shp = shape(mins_by, n)
    tot_dk = sum(sum(v) for v in dks_by.values())
    top3_dk = sum(sorted((sum(v) for v in dks_by.values()), reverse=True)[:3]) / tot_dk if tot_dk else 0
    # OBPR team rank (EvanMiya players on the team)
    team_m = sorted([p for p in mplayers if p["Team"] == mt], key=lambda p: -float(p["OBPR"] or -99))
    obpr_rank = {norm(p["Name"]): i + 1 for i, p in enumerate(team_m)}
    obpr = {norm(p["Name"]): float(p["OBPR"]) for p in team_m}
    lines, outs, flags = [], [], []
    for r in sorted(rows, key=lambda r: -(r.get("min") or 0)):
        pid = str(r.get("espn") or "")
        games_in = [g["players"][pid] for g in bx if pid in g["players"]]
        if r.get("status") == "Out":
            outs.append({"name": r["name"], "played": len(games_in), "of": n,
                         "missed_last": next((i for i, g in enumerate(reversed(bx)) if pid in g["players"]), n)})
            continue
        if r.get("status") == "Questionable":
            flags.append("%s is Questionable" % r["name"])
        if r.get("zero_gp"):
            flags.append("%s hasn't played this season (projection scaled)" % r["name"])
        if (r.get("p_play") or 1) < 0.8 and (r.get("min") or 0) >= ROTATION_PROJ_MIN:
            flags.append("%s carries sit risk (%.0f%% to play: %s)" % (r["name"], 100 * r["p_play"], r.get("p_play_why") or ""))
        if (r.get("min") or 0) < ROTATION_PROJ_MIN:
            continue
        mins = [x["min"] for x in games_in]
        dks = [x["dk"] for x in games_in]
        starts = sum(x["starter"] for x in games_in)
        sal = r["salary"]
        season = S.mean(mins) if mins else None
        last3 = S.mean(mins[-3:]) if mins else None
        verdict, ppm_recent, ratio = form_note(dks, mins, r.get("miya_ppm"))
        lines.append({
            "id": r["id"], "name": r["name"], "salary": sal, "pos": (games_in[-1]["pos"] if games_in else r.get("position")),
            "starts": starts, "gp": len(games_in), "team_games": n, "season_mpg": season, "last3": last3,
            "last5_mins": mins[-5:], "proj_min": r.get("min"), "proj_dk": r.get("fp_gate"),
            "min_note": minutes_note(r.get("min") or 0, season, last3, r.get("out_gain")), "out_gain": r.get("out_gain"),
            "obpr": obpr.get(norm(r["name"]), r.get("obpr")), "obpr_rank": obpr_rank.get(norm(r["name"])), "obpr_of": len(team_m),
            "dk_pg": S.mean(dks) if dks else None, "dk_pm": (sum(dks) / sum(mins)) if mins else None, "dks": dks,
            "start_flags": [int(x["starter"]) for x in games_in],
            "hits": count_games(dks, sal, HIT_X), "ceil": count_games(dks, sal, CEILING_X), "mins": mins,
            "floor": len(dks) - count_games(dks, sal, FLOOR_X), "form": verdict, "ppm_recent": ppm_recent, "miya_ppm": r.get("miya_ppm"),
            "form_ratio": ratio, "shy": shy_away(mins), "pool_out": pool_flag(dks, sal, r.get("min") or 0),
            "status": r.get("status"),
        })
    # moving position groups (MIXED_ROLE)
    groups = {}
    for L in lines:
        if L["gp"] >= 3 and MIXED_ROLE[0] < L["starts"] / L["gp"] < MIXED_ROLE[1]:
            groups.setdefault("G" if (L["pos"] or "G")[0] == "G" else "F", []).append(L)
    moving = {k: v for k, v in groups.items() if len(v) >= 2}
    try:                           # the nightly run has no news file before the day's read (cbb_news.py); notes are optional
        news = json.load(open(os.path.join(MIRROR, "cbb_news.json")))
    except (OSError, ValueError):
        news = {}
    ids = {r["id"] for r in rows}
    notes = [a for a in news.get("analyst", []) if team in (a.get("teams") or []) or ids & set(a.get("players") or [])][:2]
    out_from = r0.get("out_from")
    return {"team": team, "slate": slate_id, "env": env, "games": n, "shape": shp, "top3_dk": top3_dk, "outs": outs, "out_from": out_from,
            "flags": flags, "lines": lines, "moving": moving, "analyst": notes, "generated": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())}


def ordinal(k):
    return "%d%s" % (k, "th" if 10 <= k % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(k % 10, "th"))


def prose(c, holds):
    """The card's paragraphs, from the numbers and the rules; varied phrasing by name (variant). Bottom line first;
    verdict tags in bold; 'minutes safe' and 'in line' gathered into one sentence instead of repeated per player."""
    e, out, Ls = c["env"], [], c["lines"]
    money = lambda x: "$%.1fk" % (x / 1000)
    # -- bottom line (is_core, is_value, pool_flag)
    core = [L for L in Ls if is_core(L)][:CORE_MAX]
    value = [L for L in Ls if is_value(L) and L not in core]
    top_dk = [L["name"] for L in sorted((L for L in Ls if L["dk_pg"] is not None), key=lambda L: -L["dk_pg"])[:STRONG_TOP_DK]]
    strong = [L for L in Ls if is_strong(L, top_dk) and L not in core and L not in value]
    fade = [L for L in Ls if L["pool_out"]]
    bl = []
    if core:
        bl.append("Core: %s, locked-in %.0f-minute roles." % (" and ".join(last(L["name"]) for L in core), S.mean(L["proj_min"] for L in core)))
    if strong:
        bl.append("Strong: %s." % "; ".join("%s (%s, %.0f min, %d of last %d started, %.1f DK a game)" % (
            last(L["name"]), money(L["salary"]), L["proj_min"], sum(L["start_flags"][-STRONG_LAST:]), min(STRONG_LAST, L["gp"]), L["dk_pg"]) for L in strong))
    if value:
        sal = sorted(L["salary"] for L in value)
        rng = money(sal[0]) if sal[0] == sal[-1] else "%s-%s" % (money(sal[0]), money(sal[-1])[1:])
        hot = [last(L["name"]) for L in value if L["form"] and L["form"].startswith("running hot")]
        bl.append("Value: %s (%s, %.0f min, multiple %gx games)%s." % (
            " and ".join(last(L["name"]) for L in value), rng, S.mean(L["proj_min"] for L in value), CEILING_X,
            ", but %s %s **running hot** vs Miya" % (" and ".join(hot), "is" if len(hot) == 1 else "are") if hot else ""))
    if fade:
        bl.append(("Fade: %s." if holds else "Light on ceiling: %s.") % ", ".join(last(L["name"]) for L in fade))
    if bl:
        out.append(("Bottom line.", " ".join(bl)))
    # -- game environment
    pos = "the lowest" if e["ou_rank"] == 1 else "the highest" if e["ou_rank"] == e["ou_n"] else "%s of %d" % (ordinal(e["ou_rank"]), e["ou_n"])
    gap = ""
    if e["ou_rank"] == 1 and len(e["ous"]) > 1:
        gap = ", %.1f under the next" % (e["ous"][1] - e["ous"][0])
    elif e["ou_rank"] == e["ou_n"] and len(e["ous"]) > 1:
        gap = ", %.1f over the next" % (e["ous"][-1] - e["ous"][-2])
    kind = {"grind": "**a grind**: fewer possessions to go around, so lean on the minutes leaders",
            "pace-up": "**a pace-up spot**: extra possessions lift everyone with minutes",
            "middling": "no pace edge either way"}[e["kind"]]
    out.append(("%s today." % e["team"],
                "Per EvanMiya (%s), %s's offense ranks %s and its true tempo %s (%.1f). %s's defense ranks %s, its pace %s. "
                "The over/under is %.1f, %s on the slate%s; the spread has %s %s%.1f, an implied %.1f points. Read: %s." % (
                    e["miya_day"], e["team"], ordinal(e["off_rank"]), ordinal(e["tempo_rank"]), e["tempo"], e["opp"], ordinal(e["opp_def_rank"]),
                    ordinal(e["opp_tempo_rank"]), e["ou"], pos, gap, e["team"], "-" if e["spread"] < 0 else "+",
                    abs(e["spread"]), e["implied"], kind)))
    # -- outs (NEW_OUT_MIN_GP: the redistribution only for new outs)
    if c["outs"]:
        old = [o for o in c["outs"] if not new_out(o["played"])]
        new = [o for o in c["outs"] if new_out(o["played"])]
        bits = []
        if old:
            bits.append("%s (out all season so far, 0 of %d games; already missing from everyone's averages)" % (
                " and ".join(o["name"] for o in old), old[0]["of"]))
        for o in new:
            bits.append("%s (**new**: played %d of %d, out the last %d)" % (o["name"], o["played"], o["of"], o["missed_last"]))
        txt = "; ".join(bits) + "."
        if new:
            gains = [(last(L["name"]), L["out_gain"]) for L in Ls if (L["out_gain"] or 0) >= 1]
            if gains:
                txt += " Their minutes go to: " + ", ".join("%s +%.0f" % g for g in gains) + "."
        out.append(("OUT:", txt))
    if c["flags"]:
        out.append(("Flags:", "; ".join(c["flags"]) + "."))
    # -- rotation shape
    lab, t5, t7, regs = c["shape"]
    out.append(("Rotation.", "%s plays a **%s** rotation: %d players at %d+ minutes a game; the top 5 take %.0f%% of the minutes and the top 7 %.0f%% (%d games). "
                "The top 3 fantasy scorers have produced %.0f%% of the team's DraftKings points." % (
                    e["team"], lab, regs, MPG_BAR, 100 * t5, 100 * t7, c["games"], 100 * c["top3_dk"])))
    # -- the steady ones, once (minutes safe and output in line)
    steady = [L for L in Ls if L["min_note"] == "minutes safe as projected" and L["form"] in ("in line", None) and not L["pool_out"]]
    if steady:
        out.append(("", "Minutes safe as projected and output in line with EvanMiya: %s." % ", ".join(last(L["name"]) for L in steady)))
    # -- player lines
    for L in Ls:
        role = "%d of %d starts" % (L["starts"], L["gp"])
        if L["starts"] == L["gp"] and L["gp"]:
            role = variant(L["name"], ["started every game", "a starter in all %d" % L["gp"], "%d-for-%d starter" % (L["starts"], L["gp"])])
        elif L["starts"] == 0:
            role = variant(L["name"], ["off the bench every game", "a reserve in all %d" % L["gp"], "no starts in %d" % L["gp"]])
        mins = ", ".join("%.0f" % m for m in L["last5_mins"])
        lead = variant(L["name"] + "x", ["**%s** (%s, %s) is at %.1f mpg", "**%s** (%s, %s) averages %.1f minutes", "**%s** (%s, %s): %.1f mpg"]) % (
            L["name"], "${:,}".format(L["salary"]), role, L["season_mpg"] or 0)
        s = lead + " (%s), %.1f projected" % (mins, L["proj_min"])
        s += " — **%s**." % L["min_note"] if L["min_note"] and L["min_note"] != "minutes safe as projected" else "."
        if L["obpr"] is not None and L["obpr_rank"]:
            s += " OBPR %.2f (%s on the team)." % (L["obpr"], ordinal(L["obpr_rank"]))
        s += " %.1f DK a game, %.2f a minute; %gx in %d of %d, %gx in %d, under %gx in %d." % (
            L["dk_pg"] or 0, L["dk_pm"] or 0, HIT_X, L["hits"], L["gp"], CEILING_X, L["ceil"], FLOOR_X, L["floor"])
        if L["form"] and L["form"] != "in line":
            s += " Recent %.2f a minute vs EvanMiya's %.2f: **%s**." % (L["ppm_recent"], L["miya_ppm"], L["form"])
        if L["shy"]:
            s += " **Shy away even if starting**: minutes too volatile and too low."
        if L["pool_out"]:
            s += " **%s**." % ("Fade" if holds else "Rarely hits a ceiling")
        out.append(("", s))
    # -- moving groups, read (group_read)
    best = max((L for L in Ls if L["dk_pm"] is not None and L["gp"] >= 3), key=lambda L: L["dk_pm"], default=None)
    for k, G in c["moving"].items():
        reads = [r for r in (group_read(L, best["name"] if best else None) for L in G) if r]
        other = [L for L in G if not group_read(L, best["name"] if best else None)]
        txt = "; ".join(reads) + "." if reads else ""
        if other:
            txt += " " + " ".join("%s: %d of %d starts, minutes %s." % (last(L["name"]), L["starts"], L["gp"], ", ".join("%.0f" % m for m in L["last5_mins"])) for L in other)
        out.append(("The %s spots have been moving." % ("guard" if k == "G" else "forward"), txt.strip()))
    # -- pool
    keep = [last(L["name"]) for L in Ls if not L["pool_out"]]
    if fade:
        why = "no %gx game in the last %d and projected under %d minutes" % (CEILING_X, POOL_LAST_N, POOL_MIN_PROJ)
        names = " and ".join(last(L["name"]) for L in fade)
        out.append(("Pool.", ("Keep %s. %s: %s, so **leave %s out of your pool today**." % (", ".join(keep), names, why, "them" if len(fade) > 1 else "him"))
                    if holds else "Keep %s. %s: %s; players like that rarely hit a ceiling." % (", ".join(keep), names, why)))
    else:
        out.append(("Pool.", "Every rotation player here has a ceiling game recently; keep %s." % ", ".join(keep)))
    return out


# ---- the backtest -----------------------------------------------------------------------------------------------
def backtest():
    """The pool rule on the graded slates (dk_eval records; each player's last games from the lock-time card):
    {rule: [n, hit 5x], other: [n, hit], per_slate: {slate: (rule rate, other rate)}, holds}."""
    sys.path.insert(0, HERE)
    import dk_eval as E
    from dk_dnp_study import lock_players
    num = E.num
    by = {}
    for r in E.records():
        if r["status"] != "Out" and num(r["actual_dk"]) is not None:
            by.setdefault((r["date"], r["draft_group"]), []).append(r)
    agg = {"rule": [0, 0], "other": [0, 0]}
    per = {}
    for (d, g), rs in sorted(by.items()):
        P, _ = lock_players(d, g)
        if not P:
            continue
        s = {"rule": [0, 0], "other": [0, 0]}
        for r in rs:
            l5 = (P.get(r["dk_id"]) or {}).get("last5") or []
            mp = num(r["min_proj"]) or 0
            if len(l5) < 3 or mp <= 0:
                continue
            k = "rule" if pool_flag([x[2] for x in l5], num(r["salary"]), mp) else "other"
            hit = num(r["actual_dk"]) >= CEILING_X * num(r["salary"]) / 1000
            for a in (agg[k], s[k]):
                a[0] += 1
                a[1] += hit
        if s["rule"][0] and s["other"][0]:          # a slate counts once both groups have players (a lock card with last games)
            per["%s_%s" % (d, g)] = tuple(round(x[1] / x[0], 3) for x in (s["rule"], s["other"]))
    rate = lambda a: a[1] / a[0] if a[0] else 0
    lower = sum(1 for a, b in per.values() if a < b)
    holds = rate(agg["rule"]) <= POOL_HOLDS * rate(agg["other"]) and lower >= 0.75 * len(per)
    return {"rule": agg["rule"], "other": agg["other"], "per_slate": per, "lower_on": lower, "slates": len(per), "holds": holds}


# ---- the page ---------------------------------------------------------------------------------------------------
def render(c, paras, bt):
    md = lambda s: html.escape(s).replace("**", "\x00").split("\x00")
    def bold(s):
        parts = md(s)
        return "".join(("<b>%s</b>" % p if i % 2 else p) for i, p in enumerate(parts))
    body = []
    for head, txt in paras:
        body.append("<p>%s%s</p>" % ("<b>%s</b> " % html.escape(head) if head else "", bold(txt)))
    rows = "".join(
        "<tr><td class='nm'>%s%s</td><td>%d/%d</td><td>%.1f</td><td>%.1f</td><td>%s</td><td>%.1f</td><td>%.2f</td><td>%d/%d/%d</td><td>%s</td><td>%s</td></tr>" % (
            html.escape(L["name"]), " <span class='tag'>pool: out</span>" if L["pool_out"] else "", L["starts"], L["gp"], L["season_mpg"] or 0,
            L["last3"] or 0, "%.1f" % L["proj_min"], L["dk_pg"] or 0, L["dk_pm"] or 0, L["hits"], L["ceil"], L["floor"],
            "%.2f (%s)" % (L["obpr"], ordinal(L["obpr_rank"])) if L["obpr_rank"] else "-",
            html.escape(L["form"] or "-")) for L in c["lines"])
    chips = "".join("<span class='chip'>%s <button>%s</button></span>" % (html.escape(L["name"]), "Drop" if L["pool_out"] else "Use")
                    for L in c["lines"])
    notes = "".join("<p class='an'>@%s: %s… <a href='%s'>post</a></p>" % (html.escape(a["author"]), html.escape(a["text"][:280]), html.escape(a["url"]))
                    for a in c["analyst"]) or "<p class='an'>No analyst post on this team in the window.</p>"
    rule = "Pool rule backtest (%d graded slates): no %gx in last %d and under %d projected minutes hit %gx on the night %d of %d (%.1f%%); everyone else %d of %d (%.1f%%); lower on %d of %d slates: %s." % (
        bt["slates"], CEILING_X, POOL_LAST_N, POOL_MIN_PROJ, CEILING_X, bt["rule"][1], bt["rule"][0], 100 * bt["rule"][1] / max(1, bt["rule"][0]),
        bt["other"][1], bt["other"][0], 100 * bt["other"][1] / max(1, bt["other"][0]), bt["lower_on"], bt["slates"], "worded as advice" if bt["holds"] else "worded 'rarely hits a ceiling'")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Team card sample</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{--bg:#080b11;--surface:#12151c;--ink:#fff;--muted:#8b94a4;--line:#1c212c;--line-strong:#2a3140;--warn:#f0c541;--live:#4dc48d;--bad:#f08a7e;
--sans:"Archivo",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f6f7f9;--surface:#fff;--ink:#0d1017;--muted:#5b6474;--line:#e3e6ec;--line-strong:#cfd4dc;--warn:#9a7400;--live:#1f8a5a;--bad:#b4433a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:760px;margin:0 auto;padding:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
h1{font-size:18px;margin:0 0 2px}.sub{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-bottom:10px}
p{margin:0 0 10px}b{font-weight:700}
.tbl{overflow-x:auto;margin:8px -4px 6px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;font-family:var(--mono);font-size:11.5px;white-space:nowrap}
th,td{padding:4px 6px;border-bottom:1px solid var(--line);text-align:right}th{color:var(--muted);font-weight:500}
td.nm,th.nm{text-align:left;position:sticky;left:0;background:var(--surface)}
.tag{font-size:10px;color:var(--bad);border:1px solid var(--bad);border-radius:4px;padding:0 3px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}.chip{font-size:12.5px;border:1px solid var(--line-strong);border-radius:16px;padding:2px 4px 2px 10px}
.chip button{font:600 12px var(--sans);margin-left:6px;border:1px solid var(--line-strong);background:var(--bg);color:var(--ink);border-radius:12px;padding:2px 8px}
.an{font-size:13px;color:var(--muted);border-left:2px solid var(--line-strong);padding-left:8px}
.an a{color:var(--muted)}.foot{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-top:8px}
</style></head><body><div class="wrap"><div class="card">
<h1>%s · %s</h1><div class="sub">Sample team card · slate %s · built %s · display only</div>
%s
<div class="tbl"><table><tr><th class="nm">Player</th><th>Starts</th><th>MPG</th><th>L3</th><th>Proj</th><th>DK/g</th><th>DK/min</th><th>4x/5x/&lt;2x</th><th>OBPR (rank)</th><th>Form</th></tr>%s</table></div>
<div class="chips">%s</div>
<div class="sub">Analyst</div>%s
<div class="foot">%s Rules: scripts/dk_team_cards.py. Chips are the page's existing Use / Drop, wired when the card ships.</div>
</div></div></body></html>""" % (html.escape(c["team"]), html.escape(c["env"]["game"]), c["slate"], c["generated"], "\n".join(body), rows, chips, notes, html.escape(rule))


BACKTEST = os.path.join(HERE, "..", "analysis", "cbb", "dk", "team_card_backtest.json")
"""The pool rule's backtest, kept (the nightly run reads it: it has no mirror history to rerun it); `backtest` rewrites it."""


def cached_backtest():
    try:
        return json.load(open(BACKTEST))
    except (OSError, ValueError):
        return {"rule": [0, 0], "other": [0, 0], "per_slate": {}, "lower_on": 0, "slates": 0, "holds": False}


TABLE_KEYS = ("id", "name", "salary", "starts", "gp", "season_mpg", "last3", "proj_min", "dk_pg", "dk_pm", "hits", "ceil", "floor",
              "obpr", "obpr_rank", "form", "min_note", "pool_out", "shy")


def writeups(holds):
    """Every team on every open slate in the mirror: {slates: {draft group: {team: {paras, table, pool}}}}."""
    doc = json.load(open(os.path.join(MIRROR, "dk_cbb_morning.json")))
    out, cache = {}, {}
    for sl in doc.get("slates", []):
        teams = sorted({v["team"] for v in (sl.get("players") or {}).values() if v.get("team")})
        out[str(sl["draft_group_id"])] = got = {}
        for t in teams:
            try:
                c = build(t, sl["draft_group_id"], cache)
            except Exception as e:                     # one team's missing data never stops the rest
                print("dk_team_cards: %s %s skipped (%s)" % (sl["draft_group_id"], t, e))
                continue
            rnd = lambda v: round(v, 2) if isinstance(v, float) else v
            got[t] = {"paras": prose(c, holds), "games": c["games"],
                      "table": [{k: rnd(L.get(k)) for k in TABLE_KEYS} for L in c["lines"]]}
    return out


def main():
    global MIRROR, BRR
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror")
    ap.add_argument("--brr", help="battle-royale-research's root (EvanMiya files)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--team", required=True)
    s.add_argument("--slate", required=True)
    s.add_argument("--out", required=True)
    sub.add_parser("backtest")
    w = sub.add_parser("all")
    w.add_argument("--out", required=True, help="the JSON the page reads, e.g. mirror/dk_cbb_writeups.json")
    a = ap.parse_args()
    MIRROR, BRR = a.mirror or MIRROR, a.brr or BRR
    if a.cmd == "backtest":
        bt = backtest()
        json.dump(bt, open(BACKTEST, "w"), indent=1)
        print(json.dumps(bt, indent=1))
        return
    bt = cached_backtest()
    if a.cmd == "all":
        doc = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "backtest": bt,
               "rule": "scripts/dk_team_cards.py (br_rankings); display only", "slates": writeups(bt["holds"])}
        json.dump(doc, open(a.out, "w"), indent=1)
        print("dk_team_cards: %s" % ", ".join("%s %d teams" % (k, len(v)) for k, v in doc["slates"].items()))
        return
    cache = {}
    c = build(a.team, a.slate, cache)
    paras = prose(c, bt["holds"])
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, "%s_%s" % (a.slate, a.team))
    open(stem + ".html", "w").write(render(c, paras, bt))
    open(stem + ".txt", "w").write("\n\n".join(("%s %s" % p).strip() for p in paras) + "\n")
    json.dump({"card": c, "backtest": bt}, open(stem + ".json", "w"), indent=1, default=str)
    print("\n\n".join(("%s %s" % p).strip() for p in paras))


if __name__ == "__main__":
    main()
