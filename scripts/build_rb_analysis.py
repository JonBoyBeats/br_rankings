"""Build analysis/rb.json for the Analysis page: every RB's role, baseline and next matchup.

Data: nflverse play-by-play, weekly stats, snap counts, players and schedules, plus
ffopportunity expected points. Only the previous and current seasons are read, which is
all a 16-game window needs. Everything is scored half-PPR, the way Underdog scores:
rec .5, rush/rec yd .1, TD 6, pass yd .04, pass TD 4, INT -1, fumble lost -2, 2pt 2.

Role, per game:  snap %  = own offensive snaps / team offensive snaps
                 carry % = carries / team carries
                 usage   = (targets + carries) / (team targets + team carries)
                 RZ %    = (red-zone targets + carries) / team's, inside the 20
Windows: L16 is the last 16 games across seasons, as ratio-of-sums; the per-game cells
are this season's last 4 games; L4 (baseline only) is the mean of those same games.
Tier cutoffs are where the RB6 / RB12 / RB24 landed each week, 2021-2025.

Matchup: points the opponent's defense allowed to RBs over its last 8 games, the team's
implied total and spread, weighted by how much each moved next-game RB scoring
2017-2025, then ranked 1-32 for the week.

Usage: python3 scripts/build_rb_analysis.py [--data DIR]   (DIR caches the downloads)"""
import json, os, sys, time, urllib.request
import numpy as np, pandas as pd

NV = 'https://github.com/nflverse/nflverse-data/releases/download'
EP = 'https://github.com/ffverse/ffopportunity/releases/download/latest-data'
DATA = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else '.cache'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'rb.json')

# RB6 / RB12 / RB24 lines by window: game, last 4, last 16 (fit on 2021-2025)
CUTS = {
    'snap':  {'game': [.778, .682, .537], 'l16': [.696, .624, .507]},
    'carry': {'game': [.727, .619, .467], 'l16': [.623, .551, .437]},
    'usage': {'game': [.400, .344, .255], 'l16': [.354, .306, .246]},
    'rz':    {'game': [.500, .417, .270], 'l16': [.385, .336, .263]},
    'xfp':   {'l4': [15.9, 13.5, 10.6], 'l16': [15.1, 13.0, 10.3]},
    'fp':    {'l4': [17.2, 14.2, 10.2], 'l16': [15.8, 13.3, 10.1]},
}
# Next-game RB points per unit, from a fit that also held the player's own baseline fixed
MATCHUP_W = {'opp_rb_allowed': 0.101, 'implied_total': 0.108, 'spread': 0.020}
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


def seasons_to_read():
    sched = fetch(f'{NV}/schedules/games.parquet', 'games.parquet')
    sched = sched[sched.game_type == 'REG'].copy()
    for c in ['home_team', 'away_team']: sched[c] = sched[c].replace(TEAM_FIX)
    played = sched[sched.result.notna()]
    season = int(played.season.max())
    # a week counts as played once every game in it is; a Thursday opener doesn't move it
    cur = sched[sched.season == season]
    done = cur.groupby('week').result.apply(lambda r: r.notna().all())
    through = int(done[done].index.max()) if done.any() else 0
    return sched, season, through


def load_season(y):
    cols = ['game_id', 'season', 'week', 'season_type', 'posteam', 'play_type', 'qb_kneel', 'qb_spike',
            'two_point_attempt', 'receiver_player_id', 'rusher_player_id', 'pass_attempt', 'rush_attempt', 'yardline_100']
    p = fetch(f'{NV}/pbp/play_by_play_{y}.parquet', f'pbp_{y}.parquet')[cols]
    p = p[(p.season_type == 'REG') & p.posteam.notna()].copy()
    p['posteam'] = p.posteam.replace(TEAM_FIX)
    o = p[p.play_type.isin(['pass', 'run']) & (p.qb_kneel != 1) & (p.qb_spike != 1) & (p.two_point_attempt != 1)]
    tg = o[o.receiver_player_id.notna() & (o.pass_attempt == 1)].assign(pid=lambda d: d.receiver_player_id)
    ca = o[(o.rush_attempt == 1) & o.rusher_player_id.notna()].assign(pid=lambda d: d.rusher_player_id)
    k, kk = ['game_id', 'posteam'], ['game_id', 'posteam', 'pid']
    team = pd.DataFrame({
        'tm_tgt': tg.groupby(k).size(), 'tm_car': ca.groupby(k).size(),
        'tm_rz': tg[tg.yardline_100 <= 20].groupby(k).size().add(ca[ca.yardline_100 <= 20].groupby(k).size(), fill_value=0),
    }).fillna(0).reset_index().rename(columns={'posteam': 'team'})
    pl = pd.DataFrame({
        'tgt': tg.groupby(kk).size(), 'car': ca.groupby(kk).size(),
        'rz': tg[tg.yardline_100 <= 20].groupby(kk).size().add(ca[ca.yardline_100 <= 20].groupby(kk).size(), fill_value=0),
    }).fillna(0).reset_index().rename(columns={'posteam': 'team', 'pid': 'player_id'})

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


def main():
    sched, season, through = seasons_to_read()
    players = fetch(f'{NV}/players/players.parquet', 'players.parquet')
    parts = [load_season(y) for y in (season - 1, season)]
    pl, team, st, sn, tm_snaps, ep = [pd.concat(x, ignore_index=True) for x in zip(*parts)]

    sn = sn.merge(players[['gsis_id', 'pfr_id']].dropna(), left_on='pfr_player_id', right_on='pfr_id', how='inner')
    sn = sn.rename(columns={'gsis_id': 'player_id'}).groupby(['game_id', 'team', 'player_id'], as_index=False).offense_snaps.max()

    pos = players.set_index('gsis_id').position
    base = pd.concat([sn[sn.offense_snaps > 0][['game_id', 'team', 'player_id']], pl[['game_id', 'team', 'player_id']]]).drop_duplicates()
    base = base[base.player_id.map(pos) == 'RB']
    g = sched[['game_id', 'season', 'week', 'home_team', 'away_team']]
    D = (base.merge(g, on='game_id').merge(sn, on=['game_id', 'team', 'player_id'], how='left')
             .merge(tm_snaps, on=['game_id', 'team'], how='left').merge(pl, on=['game_id', 'team', 'player_id'], how='left')
             .merge(team, on=['game_id', 'team'], how='left').merge(st, on=['game_id', 'team', 'player_id'], how='left')
             .merge(ep, on=['game_id', 'player_id'], how='left'))
    D['opp'] = np.where(D.team == D.home_team, D.away_team, D.home_team)
    D[['offense_snaps', 'tgt', 'car', 'rz', 'fp']] = D[['offense_snaps', 'tgt', 'car', 'rz', 'fp']].fillna(0)
    D = D.sort_values(['player_id', 'season', 'week'])

    # the defense side: half-PPR points each defense allowed to RBs per game, last 8 before now
    allowed = D.groupby(['game_id', 'season', 'week', 'opp']).fp.sum().reset_index().sort_values(['season', 'week'])
    opp_allowed = allowed.groupby('opp').tail(8).groupby('opp').fp.mean()

    def ratio(num, den):
        return None if den <= 0 else round(float(num / den), 3)

    info = players.set_index('gsis_id')
    rows = []
    for pid, d in D.groupby('player_id'):
        cur = d[d.season == season]
        if cur.empty: continue
        l16, last4 = d.tail(16), cur.tail(4)
        now_team = cur.team.iloc[-1]
        games = [{'wk': int(r.week), 'opp': r.opp,
                  'snap': ratio(r.offense_snaps, r.tm_snaps or 0), 'carry': ratio(r.car, r.tm_car),
                  'usage': ratio(r.tgt + r.car, r.tm_tgt + r.tm_car), 'rz': ratio(r.rz, r.tm_rz),
                  'xfp': None if pd.isna(r.xfp) else round(float(r.xfp), 1), 'fp': round(float(r.fp), 1)}
                 for r in last4.itertuples()]
        x16, x4 = l16.xfp.dropna(), last4.xfp.dropna()
        rows.append({
            'id': pid, 'name': info.display_name.get(pid, pid), 'team': now_team,
            'rookie': bool(info.rookie_season.get(pid) == season),
            'new_team': bool((l16.team != now_team).any()),
            'l16_games': int(len(l16)),
            'l16': {'snap': ratio(l16.offense_snaps.sum(), l16.tm_snaps.sum()), 'carry': ratio(l16.car.sum(), l16.tm_car.sum()),
                    'usage': ratio((l16.tgt + l16.car).sum(), (l16.tm_tgt + l16.tm_car).sum()), 'rz': ratio(l16.rz.sum(), l16.tm_rz.sum()),
                    'xfp': round(float(x16.mean()), 1) if len(x16) else None, 'fp': round(float(l16.fp.mean()), 1)},
            'l4': {'xfp': round(float(x4.mean()), 1) if len(x4) else None, 'fp': round(float(last4.fp.mean()), 1)},
            'games': games,
        })

    # next week's matchups, ranked 1-32
    nxt = sched[(sched.season == season) & (sched.week == through + 1)]
    sides = []
    for r in nxt.itertuples():
        for tm, op, home in ((r.home_team, r.away_team, True), (r.away_team, r.home_team, False)):
            spread = r.spread_line if home else -r.spread_line          # positive = this team favored
            implied = (r.total_line + spread) / 2 if pd.notna(r.total_line) else None
            sides.append({'team': tm, 'opp': op, 'home': home, 'implied_total': implied, 'spread': spread,
                          'opp_rb_allowed': float(opp_allowed.get(op, np.nan)), 'kickoff': str(r.gameday)})
    M = pd.DataFrame(sides)
    matchups = {}
    if len(M):
        M = M.fillna({'implied_total': M.implied_total.mean(), 'spread': 0, 'opp_rb_allowed': M.opp_rb_allowed.mean()})
        M['score'] = sum(M[k] * w for k, w in MATCHUP_W.items())
        M['rank'] = M.score.rank(ascending=False, method='first').astype(int)
        for r in M.itertuples():
            tier = next(t for cap, t in MATCHUP_TIERS if r.rank <= cap)
            matchups[r.team] = {'opp': r.opp, 'home': bool(r.home), 'rank': int(r.rank), 'tier': tier,
                                'implied_total': round(float(r.implied_total), 1), 'spread': round(float(r.spread), 1),
                                'opp_rb_allowed': round(float(r.opp_rb_allowed), 1), 'kickoff': r.kickoff}

    doc = {'season': season, 'through_week': through, 'next_week': through + 1,
           'built': time.strftime('%Y-%m-%dT%H:%MZ', time.gmtime()), 'teams_on_bye': sorted(set(D[D.season == season].team) - set(matchups)),
           'cuts': CUTS, 'matchup_weights': MATCHUP_W, 'matchups': matchups,
           'players': sorted(rows, key=lambda r: -(r['l4']['xfp'] or 0))}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f: json.dump(doc, f, separators=(',', ':'))
    print(f'{len(rows)} RBs, {season} through week {through}, {len(matchups)} week-{through + 1} matchups -> {os.path.relpath(OUT)}')


if __name__ == '__main__':
    main()
