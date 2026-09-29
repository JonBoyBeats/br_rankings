"""Build analysis/workload.json for the Analysis page: every RB, WR and TE's role, baseline
and next matchup.

Data: nflverse play-by-play, weekly stats, snap counts, players and schedules, plus
ffopportunity expected points. Only the previous and current seasons are read, which is
all a 16-game window needs. Everything is scored half-PPR, the way Underdog scores:
rec .5, rush/rec yd .1, TD 6, pass yd .04, pass TD 4, INT -1, fumble lost -2, 2pt 2.

Role, per game (every share is of the player's own team in that game):
  RB      snap % = offensive snaps · carry % = carries · usage = targets + carries
          RZ %   = targets + carries inside the 20
  WR, TE  route % = routes run / team dropbacks · target % = targets
          first-read % = first-read targets / the team's · air yd % = air yards on targets
Route % and first-read % are Fantasy Points Data's: this season from the weekly exports in
analysis/fpd/<season>/, last season from analysis/fpd/history_<season>.csv (derived from
their weekly routes and first-read counts). Their L16 is the mean of the per-game values.
Windows: L16 is the last 16 games across seasons, as ratio-of-sums; the per-game cells
are this season's last 4 games; L4 (baseline only) is the mean of those same games.
Tiers are where each position's cutoff ranks landed each week, 2021-2025:
  RB 6 / 12 / 24 · WR 8 / 18 / 36 · TE 3 / 6 / 12.

Matchup: points the opponent allowed to the position over its last 8 games, the team's
implied total and spread, weighted by how much each moved that position's next-game
scoring 2017-2025, then ranked 1-32 for the week: Elite 1-6, Great 7-12, Average 13-24,
Tough 25-32.

Workload Score: expected half-PPR points next game (and per game over the next 3), from a
linear model per position on the inputs above, fitted and tested in the nfl_tails repo
(research/workload/score_fit.py) and carried here as scripts/score_model.json. The drawer
splits it into baseline (production) + role + matchup, the last two relative to average.
p50/p80/p85 are the outcome percentiles players at that score level actually posted.

Usage: python3 scripts/build_workload.py [--data DIR]   (DIR caches the downloads)"""
import glob, json, os, re, sys, time, urllib.request
import numpy as np, pandas as pd

NV = 'https://github.com/nflverse/nflverse-data/releases/download'
EP = 'https://github.com/ffverse/ffopportunity/releases/download/latest-data'
DATA = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else '.cache'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'workload.json')

# Per position: the four role stats [key, column label, long description], the tier
# ranges, cutoffs [elite, great, average] by window (single game, last 4, last 16), and
# matchup weights (next-game points per unit, with the player's own baseline held fixed).
POSITIONS = {
    'RB': {
        'stats': [['snap', 'Snap %', 'Share of team offensive snaps'],
                  ['carry', 'Carry %', 'Share of team carries'],
                  ['usage', 'Usage', 'Targets + carries as a share of the team\'s'],
                  ['rz', 'RZ %', 'Share of team targets + carries inside the 20']],
        'tiers': ['RB25+', 'RB13–24', 'RB7–12', 'RB1–6'],
        'cuts': {'snap': {'game': [.778, .682, .537], 'l16': [.696, .624, .507]},
                 'carry': {'game': [.727, .619, .467], 'l16': [.623, .551, .437]},
                 'usage': {'game': [.400, .344, .255], 'l16': [.354, .306, .246]},
                 'rz': {'game': [.500, .417, .270], 'l16': [.385, .336, .263]},
                 'xfp': {'l4': [15.9, 13.5, 10.6], 'l16': [15.1, 13.0, 10.3]},
                 'fp': {'l4': [17.2, 14.2, 10.2], 'l16': [15.8, 13.3, 10.1]}},
        'matchup_w': {'opp_allowed': 0.101, 'implied_total': 0.108, 'spread': 0.020},
    },
    'WR': {
        'stats': [['route', 'Route %', 'Routes run as a share of team dropbacks'],
                  ['tgt', 'Target %', 'Share of team targets'],
                  ['fr', '1st read %', 'Share of the team\'s first-read targets'],
                  ['ay', 'Air yd %', 'Share of team air yards on targets']],
        'tiers': ['WR37+', 'WR19–36', 'WR9–18', 'WR1–8'],
        'cuts': {'route': {'game': [.931, .886, .806], 'l16': [.884, .841, .768]},
                 'tgt': {'game': [.324, .265, .200], 'l16': [.274, .241, .187]},
                 'fr': {'game': [.400, .315, .227], 'l16': [.341, .289, .222]},
                 'ay': {'game': [.496, .390, .279], 'l16': [.386, .329, .261]},
                 'xfp': {'l4': [13.9, 11.4, 8.7], 'l16': [13.2, 11.1, 9.0]},
                 'fp': {'l4': [15.0, 12.0, 8.7], 'l16': [13.9, 11.4, 8.9]}},
        'matchup_w': {'opp_allowed': 0.007, 'implied_total': 0.130, 'spread': -0.032},
    },
    'TE': {
        'stats': [['route', 'Route %', 'Routes run as a share of team dropbacks'],
                  ['tgt', 'Target %', 'Share of team targets'],
                  ['fr', '1st read %', 'Share of the team\'s first-read targets'],
                  ['ay', 'Air yd %', 'Share of team air yards on targets']],
        'tiers': ['TE13+', 'TE7–12', 'TE4–6', 'TE1–3'],
        'cuts': {'route': {'game': [.853, .800, .721], 'l16': [.788, .739, .685]},
                 'tgt': {'game': [.275, .230, .181], 'l16': [.223, .196, .163]},
                 'fr': {'game': [.316, .267, .192], 'l16': [.260, .219, .170]},
                 'ay': {'game': [.303, .240, .170], 'l16': [.229, .187, .143]},
                 'xfp': {'l4': [11.2, 9.5, 7.5], 'l16': [10.4, 8.8, 7.2]},
                 'fp': {'l4': [12.6, 10.0, 7.8], 'l16': [11.1, 9.3, 7.3]}},
        'matchup_w': {'opp_allowed': 0.069, 'implied_total': 0.090, 'spread': 0.0},
    },
}
FPD_DIR = os.path.join(os.path.dirname(OUT), 'fpd')
FPD_TEAM = {'ARZ': 'ARI', 'BLT': 'BAL', 'CLV': 'CLE', 'HST': 'HOU'}
SCORE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'score_model.json')))
PROD, MATCH = {'xfp16', 'xfp4', 'fp16', 'fp4'}, {'opp_allowed', 'imp_tot', 'spread'}
SCORE_RANKS = {'RB': [6, 12, 24], 'WR': [8, 18, 36], 'TE': [3, 6, 12]}
MATCHUP_TIERS = [(6, 'Elite'), (12, 'Great'), (24, 'Average'), (32, 'Tough')]
TEAM_FIX = {'OAK': 'LV', 'SD': 'LAC', 'STL': 'LA', 'LAR': 'LA', 'JAC': 'JAX', 'WSH': 'WAS', 'LVR': 'LV'}


def fetch(url, name):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    fresh = os.path.exists(path) and time.time() - os.path.getmtime(path) < 3 * 3600
    if not fresh:
        for attempt in range(4):
            try:
                urllib.request.urlretrieve(url, path)
                break
            except Exception:
                if attempt == 3: raise
                time.sleep(2 ** (attempt + 1))
    return pd.read_parquet(path)


def schedule():
    sched = fetch(f'{NV}/schedules/games.parquet', 'games.parquet')
    sched = sched[sched.game_type == 'REG'].copy()
    for c in ['home_team', 'away_team']: sched[c] = sched[c].replace(TEAM_FIX)
    season = int(sched[sched.result.notna()].season.max())
    # a week counts as played once every game in it is; a Thursday opener doesn't move it
    done = sched[sched.season == season].groupby('week').result.apply(lambda r: r.notna().all())
    through = int(done[done].index.max()) if done.any() else 0
    return sched, season, through


def load_season(y):
    cols = ['game_id', 'season_type', 'posteam', 'play_type', 'qb_kneel', 'qb_spike', 'two_point_attempt',
            'receiver_player_id', 'rusher_player_id', 'pass_attempt', 'rush_attempt', 'yardline_100', 'air_yards']
    p = fetch(f'{NV}/pbp/play_by_play_{y}.parquet', f'pbp_{y}.parquet')[cols]
    p = p[(p.season_type == 'REG') & p.posteam.notna()].copy()
    p['posteam'] = p.posteam.replace(TEAM_FIX)
    o = p[p.play_type.isin(['pass', 'run']) & (p.qb_kneel != 1) & (p.qb_spike != 1) & (p.two_point_attempt != 1)]
    tg = o[o.receiver_player_id.notna() & (o.pass_attempt == 1)].assign(pid=lambda d: d.receiver_player_id)
    ca = o[(o.rush_attempt == 1) & o.rusher_player_id.notna()].assign(pid=lambda d: d.rusher_player_id)
    rtg, rca = tg[tg.yardline_100 <= 20], ca[ca.yardline_100 <= 20]
    k, kk = ['game_id', 'posteam'], ['game_id', 'posteam', 'pid']
    team = pd.DataFrame({'tm_tgt': tg.groupby(k).size(), 'tm_car': ca.groupby(k).size(),
                         'tm_rztgt': rtg.groupby(k).size(), 'tm_rzcar': rca.groupby(k).size(),
                         'tm_ay': tg.groupby(k).air_yards.sum()}).fillna(0).reset_index().rename(columns={'posteam': 'team'})
    pl = pd.DataFrame({'tgt': tg.groupby(kk).size(), 'car': ca.groupby(kk).size(),
                       'rztgt': rtg.groupby(kk).size(), 'rzcar': rca.groupby(kk).size(),
                       'ay': tg.groupby(kk).air_yards.sum()}).fillna(0).reset_index().rename(columns={'posteam': 'team', 'pid': 'player_id'})

    st = fetch(f'{NV}/stats_player/stats_player_week_{y}.parquet', f'spw_{y}.parquet')
    st = st[st.season_type == 'REG'].copy()
    st['team'] = st.team.replace(TEAM_FIX)
    z = lambda c: st[c].fillna(0) if c in st else 0
    st['fp'] = (z('passing_yards') * .04 + z('passing_tds') * 4 - z('passing_interceptions')
                + (z('rushing_yards') + z('receiving_yards')) * .1 + (z('rushing_tds') + z('receiving_tds')) * 6
                + z('receptions') * .5 - 2 * (z('rushing_fumbles_lost') + z('receiving_fumbles_lost') + z('sack_fumbles_lost'))
                + 2 * (z('passing_2pt_conversions') + z('rushing_2pt_conversions') + z('receiving_2pt_conversions')))
    st = st[['game_id', 'team', 'player_id', 'fp']]

    sn = fetch(f'{NV}/snap_counts/snap_counts_{y}.parquet', f'snaps_{y}.parquet')
    sn = sn[sn.game_type == 'REG'].copy()
    sn['team'] = sn.team.replace(TEAM_FIX)
    tm_snaps = sn.groupby(['game_id', 'team']).offense_snaps.max().rename('tm_snaps').reset_index()

    try:
        ep = fetch(f'{EP}/ep_weekly_{y}.parquet', f'ep_{y}.parquet')
        ep['xfp'] = ep.total_fantasy_points_exp - .5 * ep.receptions_exp.fillna(0) + ep.pass_interception_exp.fillna(0)
        ep = ep[['game_id', 'player_id', 'xfp']]
    except Exception:
        ep = pd.DataFrame(columns=['game_id', 'player_id', 'xfp'])   # expected points not published yet
    return pl, team, st, sn, tm_snaps, ep


def norm(s):
    s = re.sub(r"[.'’]", '', str(s).lower())
    return ' '.join(re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', ' ', s).replace('-', ' ').split())


def fpd_season(season, D):
    """{(player_id, season, week): {'route': x, 'fr': y}} from this season's Fantasy Points exports.
    A week the export covers counts as 0 for a WR/TE who played it but isn't listed."""
    ids = D[D.season == season].drop_duplicates('player_id')
    by_name_team = {(norm(n), t): pid for n, t, pid in zip(ids.name, ids.team, ids.player_id)}
    names = ids.assign(n=ids.name.map(norm)).groupby('n').player_id.agg(list)
    out, covered, missed = {}, {}, []
    for key, pattern in (('route', '*rte_pct*.csv'), ('fr', '*first_read_pct*.csv')):
        files = sorted(glob.glob(os.path.join(FPD_DIR, str(season), pattern)))
        if not files: continue
        f = pd.read_csv(files[-1], header=1)
        f = f[f.Rank.astype(str).str.isdigit()]
        weeks = [c for c in f.columns if c.isdigit() and pd.to_numeric(f[c], errors='coerce').notna().any()]
        covered[key] = {int(w) for w in weeks}
        for r in f.to_dict('records'):
            n, t = norm(r['Name']), FPD_TEAM.get(r['Team'], r['Team'])
            pid = by_name_team.get((n, t)) or (names[n][0] if n in names.index and len(names[n]) == 1 else None)
            if pid is None: missed.append(r['Name']); continue
            for w in weeks:
                v = pd.to_numeric(r[w], errors='coerce')
                if pd.notna(v): out.setdefault((pid, season, int(w)), {})[key] = round(float(v) / 100, 3)
    return out, covered, sorted(set(missed))


def ratio(num, den):
    return None if pd.isna(den) or den <= 0 or pd.isna(num) else round(float(num / den), 3)


def role(r, pos):
    """The four role stats for one game, or for a window of summed games."""
    base = {'snap': ratio(r['offense_snaps'], r['tm_snaps'])}
    if pos == 'RB':
        base.update(carry=ratio(r['car'], r['tm_car']), usage=ratio(r['tgt'] + r['car'], r['tm_tgt'] + r['tm_car']),
                    rz=ratio(r['rztgt'] + r['rzcar'], r['tm_rztgt'] + r['tm_rzcar']))
    else:
        base.update(tgt=ratio(r['tgt'], r['tm_tgt']), ay=ratio(r['ay'], r['tm_ay']) if r['tm_ay'] > 0 else None)
    return base


def main():
    sched, season, through = schedule()
    players = fetch(f'{NV}/players/players.parquet', 'players.parquet')
    parts = [load_season(y) for y in (season - 1, season)]
    pl, team, st, sn, tm_snaps, ep = [pd.concat(x, ignore_index=True) for x in zip(*parts)]

    sn = sn.merge(players[['gsis_id', 'pfr_id']].dropna(), left_on='pfr_player_id', right_on='pfr_id', how='inner')
    sn = sn.rename(columns={'gsis_id': 'player_id'}).groupby(['game_id', 'team', 'player_id'], as_index=False).offense_snaps.max()

    info = players.set_index('gsis_id')
    base = pd.concat([sn[sn.offense_snaps > 0][['game_id', 'team', 'player_id']], pl[['game_id', 'team', 'player_id']]]).drop_duplicates()
    base['pos'] = base.player_id.map(info.position)
    base = base[base.pos.isin(POSITIONS)]
    g = sched[['game_id', 'season', 'week', 'home_team', 'away_team']]
    D = (base.merge(g, on='game_id').merge(sn, on=['game_id', 'team', 'player_id'], how='left')
             .merge(tm_snaps, on=['game_id', 'team'], how='left').merge(pl, on=['game_id', 'team', 'player_id'], how='left')
             .merge(team, on=['game_id', 'team'], how='left').merge(st, on=['game_id', 'team', 'player_id'], how='left')
             .merge(ep, on=['game_id', 'player_id'], how='left'))
    D['opp'] = np.where(D.team == D.home_team, D.away_team, D.home_team)
    num = ['offense_snaps', 'tgt', 'car', 'rztgt', 'rzcar', 'ay', 'fp']
    D[num] = D[num].fillna(0)
    D = D.sort_values(['player_id', 'season', 'week'])
    D['name'] = D.player_id.map(info.display_name)

    # route % and first-read %: last season from the derived history, this season from the exports
    fpd, covered, missed = fpd_season(season, D)
    hist = os.path.join(FPD_DIR, f'history_{season - 1}.csv')
    if os.path.exists(hist):
        for r in pd.read_csv(hist).to_dict('records'):
            fpd[(r['player_id'], int(r['season']), int(r['week']))] = {k: (None if pd.isna(r[k]) else r[k]) for k in ('route', 'fr')}
        covered_prev = True
    else:
        covered_prev = False

    def receiving(r):
        got = fpd.get((r['player_id'], int(r['season']), int(r['week'])), {})
        out = {}
        for k in ('route', 'fr'):
            v = got.get(k)
            if v is None:   # listed nowhere for a week the data covers: no routes / no first reads
                cov = covered_prev if r['season'] < season else int(r['week']) in covered.get(k, ())
                v = 0.0 if cov else None
            out[k] = v
        return out

    # the defense side: half-PPR points each defense allowed to each position, last 8 games
    allowed = D.groupby(['game_id', 'season', 'week', 'opp', 'pos']).fp.sum().reset_index().sort_values(['season', 'week'])
    opp_allowed = allowed.groupby(['opp', 'pos']).tail(8).groupby(['opp', 'pos']).fp.mean()

    rows = []
    sums = ['offense_snaps', 'tm_snaps', 'tgt', 'car', 'rztgt', 'rzcar', 'ay', 'tm_tgt', 'tm_car', 'tm_rztgt', 'tm_rzcar', 'tm_ay']
    for pid, d in D.groupby('player_id'):
        cur = d[d.season == season]
        if cur.empty: continue
        pos = cur.pos.iloc[-1]
        l16, last4 = d.tail(16), cur.tail(4)
        now_team = cur.team.iloc[-1]
        games = []
        rec = lambda r: receiving(r) if pos != 'RB' else {}
        for r in last4.to_dict('records'):
            games.append({'wk': int(r['week']), 'opp': r['opp'], **role(r, pos), **rec(r),
                          'xfp': None if pd.isna(r['xfp']) else round(float(r['xfp']), 1), 'fp': round(float(r['fp']), 1)})
        x16, x4 = l16.xfp.dropna(), last4.xfp.dropna()
        mean16 = {}
        if pos != 'RB':
            vals = [receiving(r) for r in l16.to_dict('records')]
            for k in ('route', 'fr'):
                v = [x[k] for x in vals if x[k] is not None]
                mean16[k] = round(sum(v) / len(v), 3) if v else None
        last = d.iloc[-1].to_dict()
        lastrole = {**role(last, pos), **rec(last)}
        l16role = {**role(l16[sums].fillna(0).sum().to_dict(), pos), **mean16}
        x = {'fp16': float(l16.fp.mean()), 'xfp16': float(x16.mean()) if len(x16) else None,
             'fp4': float(d.tail(4).fp.mean()), 'xfp4': float(d.tail(4).xfp.dropna().mean()) if d.tail(4).xfp.notna().any() else None,
             **{k + '1': v for k, v in lastrole.items()}, **{k + '16': v for k, v in l16role.items()}}
        rows.append({
            '_x': x,
            'id': pid, 'name': info.display_name.get(pid, pid), 'pos': pos, 'team': now_team,
            'rookie': bool(info.rookie_season.get(pid) == season),
            'new_team': bool((l16.team != now_team).any()),
            'l16_games': int(len(l16)),
            'l16': {**role(l16[sums].fillna(0).sum().to_dict(), pos), **mean16,
                    'xfp': round(float(x16.mean()), 1) if len(x16) else None, 'fp': round(float(l16.fp.mean()), 1)},
            'l4': {'xfp': round(float(x4.mean()), 1) if len(x4) else None, 'fp': round(float(last4.fp.mean()), 1)},
            'games': games,
        })

    # next week's matchups, ranked 1-32 per position
    nxt = sched[(sched.season == season) & (sched.week == through + 1)]
    sides = []
    for r in nxt.itertuples():
        for tm, op, home in ((r.home_team, r.away_team, True), (r.away_team, r.home_team, False)):
            spread = r.spread_line if home else -r.spread_line          # positive = this team favored
            implied = (r.total_line + spread) / 2 if pd.notna(r.total_line) else np.nan
            sides.append({'team': tm, 'opp': op, 'home': home, 'implied_total': implied, 'spread': spread, 'kickoff': str(r.gameday)})
    M = pd.DataFrame(sides)
    matchups = {pos: {} for pos in POSITIONS}
    if len(M):
        M = M.fillna({'implied_total': M.implied_total.mean(), 'spread': 0})
        for pos, cfg in POSITIONS.items():
            P = M.copy()
            P['opp_allowed'] = [float(opp_allowed.get((o, pos), np.nan)) for o in P.opp]
            P['opp_allowed'] = P.opp_allowed.fillna(P.opp_allowed.mean())
            P['score'] = sum(P[k] * w for k, w in cfg['matchup_w'].items())
            P['rank'] = P.score.rank(ascending=False, method='first').astype(int)
            for r in P.itertuples():
                matchups[pos][r.team] = {'opp': r.opp, 'home': bool(r.home), 'rank': int(r.rank),
                                         'tier': next(t for cap, t in MATCHUP_TIERS if r.rank <= cap),
                                         'implied_total': round(float(r.implied_total), 1), 'spread': round(float(r.spread), 1),
                                         'opp_allowed': round(float(r.opp_allowed), 1), 'kickoff': r.kickoff}

    # Workload Score, for everyone with a game next week
    for r in rows:
        x, m, sm = r.pop('_x'), matchups[r['pos']].get(r['team']), SCORE[r['pos']]
        if not m: continue
        x.update(opp_allowed=m['opp_allowed'], imp_tot=m['implied_total'], spread=m['spread'])
        vals = [sm['fill'][f] if x.get(f) is None or pd.isna(x.get(f)) else x[f] for f in sm['features']]
        parts = {'baseline': sm['intercept'], 'role': 0.0, 'matchup': 0.0}
        for f, c, v in zip(sm['features'], sm['coef'], vals):
            if f in PROD: parts['baseline'] += c * v
            else:
                grp = 'matchup' if f in MATCH else 'role'
                parts['baseline'] += c * sm['mean'][f]; parts[grp] += c * (v - sm['mean'][f])
        nxt = sum(parts.values())
        n3 = sm['next3_intercept'] + sum(c * v for c, v in zip(sm['next3_coef'], vals))
        q = np.array(sm['quantiles'])
        off = {k: float(np.interp(nxt, q[:, 0], q[:, i] - q[:, 0])) for i, k in ((1, 'p50'), (2, 'p80'), (3, 'p85'))}
        r['score'] = {'next': round(nxt, 1), 'next3': round(n3, 1), **{k: round(max(0.0, nxt + v), 1) for k, v in off.items()},
                      'parts': {k: round(v, 1) for k, v in parts.items()}}
    for pos in POSITIONS:
        ranked = sorted((r for r in rows if r['pos'] == pos and 'score' in r), key=lambda r: -r['score']['next'])
        for i, r in enumerate(ranked, 1):
            r['score']['rank'] = i
            r['score']['tier'] = 3 - sum(i > cap for cap in SCORE_RANKS[pos])

    doc = {'season': season, 'through_week': through, 'next_week': through + 1,
           'built': time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime()),
           'positions': {p: {k: v for k, v in c.items()} for p, c in POSITIONS.items()},
           'matchups': matchups,
           'score_model': {p: {'features': m['features'], 'metrics': m['metrics']} for p, m in SCORE.items()},
           'players': sorted(rows, key=lambda r: -(r['l4']['xfp'] or 0))}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f: json.dump(doc, f, separators=(',', ':'))
    counts = pd.Series([r['pos'] for r in rows]).value_counts().to_dict()
    if missed: print(f'Fantasy Points names not matched ({len(missed)}):', ', '.join(missed[:40]))
    print(f'{counts} players, {season} through week {through}, week-{through + 1} matchups for {len(M) // 2 if len(M) else 0} games -> analysis/workload.json')


if __name__ == '__main__':
    main()
