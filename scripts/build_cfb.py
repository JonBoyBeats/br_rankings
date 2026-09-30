"""Build analysis/cfb.json: the college baseline the Board shows on CFB slates.

Every player gets the same baseline from collegefootballdata.com (CFBD), whatever any
writer covers; source notes (analysis/cfb/takes/) are layered on top by the page.

  usage     share of his team's plays he was involved in, garbage time excluded:
            overall, rush (share of team rushes) and pass (share of team pass plays)
  rushing   carries, yards, TDs, yards per carry · receiving: catches, yards, TDs
  passing   (QBs) completions, attempts, yards, TDs, INTs
  last 4    his last four games: carries and share of team carries, catches and share of
            team catches, and half-PPR points (Underdog scoring) from the box score
            (finished weeks are cached in analysis/cfb/cache/, one call a week)
  matchup   this week's opponent, spread, total and implied team total for EVERY FBS game,
            plus the opponent's defense against the run and the pass, each a BLEND of three
            ranks so one noisy early-season number can't flip it: EPA per play allowed (garbage
            time excluded), yards per carry / per pass attempt allowed, and SP+ defense
            (opponent-adjusted, leans on its preseason prior early). The blended rank, 1 =
            stingiest, is cut into quarters: Tough, Average, Great, Elite. Stuff rate and line
            yards ride along for the run.
  volume    his team's plays per game and pass rate
  tiers     every per-player number is placed against qualified FBS players at his position
            this season (RB 20+ carries, WR/TE 6+ catches, QB 40+ attempts): top 15% Elite,
            next 25% Great, next 30% Average, the rest Low. Single games against single games.
            Implied totals and plays per game are placed against the other teams the same way.

Season = the current college season; week = the next week with games still to play.
About a dozen API calls a run, well inside the free tier.

Usage: CFBD_API_KEY=... python3 scripts/build_cfb.py [--fixture DIR]
       (--fixture reads saved responses named after the endpoint instead of calling the API)"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

API = 'https://api.collegefootballdata.com'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'cfb.json')
CACHE = os.path.join(os.path.dirname(OUT), 'cfb', 'cache')
FIXTURE = sys.argv[sys.argv.index('--fixture') + 1] if '--fixture' in sys.argv else None
POSITIONS = {'QB', 'RB', 'WR', 'TE'}
TIERS = ['Tough', 'Average', 'Great', 'Elite']      # by the opponent's defensive rank, best defense first


def get(path, **params):
    if FIXTURE:
        name = path.strip('/').replace('/', '_') + ''.join('_' + str(params[k]) for k in ('week', 'category') if k in params and path == '/games/players') \
            + ('_' + params['category'] if 'category' in params and path != '/games/players' else '')
        with open(os.path.join(FIXTURE, name + '.json')) as f:
            return json.load(f)
    url = API + path + ('?' + urllib.parse.urlencode(params) if params else '')
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['CFBD_API_KEY'],
                                               'Accept': 'application/json'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            sample = data[0] if isinstance(data, list) and data else data
            print(f'{path}: {len(data) if isinstance(data, list) else 1} rows; fields: {sorted(sample)[:25] if isinstance(sample, dict) else type(sample).__name__}')
            return data
        except Exception as e:
            if attempt == 3: raise
            print(f'{path}: {e!r}, retrying'); time.sleep(2 ** (attempt + 1))


def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def pick(d, *keys):
    """The first key present: CFBD has renamed fields between API versions."""
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None: return d[k]
    return None


# box-score fields kept per player per game: (category, stat) -> key
BOX = {('rushing', 'CAR'): 'car', ('rushing', 'YDS'): 'rush_yds', ('rushing', 'TD'): 'rush_td',
       ('receiving', 'REC'): 'rec', ('receiving', 'YDS'): 'rec_yds', ('receiving', 'TD'): 'rec_td',
       ('passing', 'YDS'): 'pass_yds', ('passing', 'TD'): 'pass_td', ('passing', 'INT'): 'int',
       ('fumbles', 'LOST'): 'fum_lost'}


def half_ppr(g):
    """Underdog half-PPR, the NFL side's scoring: pass yd .04, pass TD 4, INT -1, rush/rec yd .1,
    TD 6, catch .5, fumble lost -2."""
    z = lambda k: g.get(k) or 0
    return round(z('pass_yds') * .04 + z('pass_td') * 4 - z('int') + (z('rush_yds') + z('rec_yds')) * .1
                 + (z('rush_td') + z('rec_td')) * 6 + z('rec') * .5 - 2 * z('fum_lost'), 1)


def week_boxes(season, wk):
    """One finished week's box scores: each player's line per game, with team carry and catch
    totals for shares. Cached on disk: a finished week never changes, so it costs one call once."""
    path = os.path.join(CACHE, f'{season}_w{wk:02d}_v2.json')
    if os.path.exists(path) and not FIXTURE:
        with open(path) as f: return json.load(f)
    games = {}
    for g in get('/games/players', year=season, week=wk, seasonType='regular'):
        teams = g.get('teams') or []
        names = [pick(t, 'team', 'school') for t in teams]
        for t in teams:
            tm = pick(t, 'team', 'school')
            row = games.setdefault(f"{g.get('id')}|{tm}", {'week': wk, 'team': tm,
                                   'opp': next((n for n in names if n != tm), None), 'home': t.get('homeAway') == 'home',
                                   'car': 0, 'rec': 0, 'players': {}})
            for c in t.get('categories') or []:
                cat = (c.get('name') or '').lower()
                for ty in c.get('types') or []:
                    key = BOX.get((cat, (ty.get('name') or '').upper()))
                    if not key: continue
                    for a in ty.get('athletes') or []:
                        v = num(a.get('stat')) or 0
                        if key in ('car', 'rec'): row[key] += v
                        pl = row['players'].setdefault(str(a.get('id')), {'name': a.get('name')})
                        pl[key] = v
    out = list(games.values())
    for row in out:
        for pl in row['players'].values(): pl['fp'] = half_ppr(pl)
    if not FIXTURE:
        os.makedirs(CACHE, exist_ok=True)
        with open(path, 'w') as f: json.dump(out, f, separators=(',', ':'))
    return out


def season_and_week(now):
    season = now.year if now.month >= 7 else now.year - 1
    cal = get('/calendar', year=season)
    weeks = []
    for c in cal:
        if (pick(c, 'seasonType', 'season_type') or 'regular') != 'regular': continue
        end = pick(c, 'endDate', 'lastGameStart', 'last_game_start')
        weeks.append((int(c['week']), end))
    weeks.sort()
    for wk, end in weeks:
        if end and datetime.fromisoformat(end.replace('Z', '+00:00')) >= now:
            return season, wk
    return season, weeks[-1][0] if weeks else 1


def main():
    now = datetime.now(timezone.utc)
    season, week = season_and_week(now)

    teams = {t['school']: t for t in get('/teams/fbs', year=season)}
    abbr = {s: (t.get('abbreviation') or s) for s, t in teams.items()}

    # ---- this week's games and lines, every FBS matchup
    games = [g for g in get('/games', year=season, week=week, seasonType='regular', classification='fbs')]
    lines = {}
    for l in get('/lines', year=season, week=week, seasonType='regular'):
        books = l.get('lines') or []
        book = next((b for b in books if (b.get('provider') or '').lower() == 'consensus'), None) or \
               next((b for b in books if b.get('spread') is not None), None)
        if book: lines[(pick(l, 'homeTeam', 'home_team'), pick(l, 'awayTeam', 'away_team'))] = book

    # ---- defenses: EPA (PPA) allowed per rush and per pass, garbage time excluded
    adv = {a['team']: a for a in get('/stats/season/advanced', year=season, excludeGarbageTime='true')}
    def def_rank(kind):
        vals = {t: num(pick(pick(a.get('defense') or {}, kind) or {}, 'ppa')) for t, a in adv.items() if t in teams}
        vals = {t: v for t, v in vals.items() if v is not None}
        order = sorted(vals, key=lambda t: vals[t])        # least EPA allowed first
        n = len(order)
        return {t: {'ppa': round(vals[t], 3), 'rank': i + 1, 'of': n, 'tier': TIERS[min(3, i * 4 // n)]}
                for i, t in enumerate(order)}
    run_d, pass_d = def_rank('rushingPlays'), def_rank('passingPlays')
    try:
        sp = {r['team']: pick(r.get('defense') or {}, 'ranking') for r in get('/ratings/sp', year=season)}
    except Exception as e:
        print('ratings/sp unavailable:', e); sp = {}

    team_stats = {}
    for s in get('/stats/season', year=season):
        team_stats.setdefault(s.get('team'), {})[s.get('statName')] = num(s.get('statValue'))
    names = sorted({k for v in team_stats.values() for k in v})
    print('team stat names:', ', '.join(names))
    def stat(team, *keys):
        for k in keys:
            v = team_stats.get(team, {}).get(k)
            if v is not None: return v
    def volume(team):
        g, ra, pa = stat(team, 'games'), stat(team, 'rushingAttempts'), stat(team, 'passAttempts')
        if not g or ra is None or pa is None: return None
        return {'plays_pg': round((ra + pa) / g, 1), 'pass_rate': round(pa / (ra + pa), 3)}
    # yards per carry allowed, if CFBD carries the opponent side of the team stats
    ypc_allowed = {}
    for t in teams:
        y, a = stat(t, 'rushingYardsOpponent', 'opponentRushingYards'), stat(t, 'rushingAttemptsOpponent', 'opponentRushingAttempts')
        if y is not None and a: ypc_allowed[t] = y / a
    ypc_rank = {t: i + 1 for i, t in enumerate(sorted(ypc_allowed, key=lambda t: ypc_allowed[t]))}
    for t, d in run_d.items():
        dfn = (adv.get(t) or {}).get('defense') or {}
        d['stuff'] = num(pick(dfn, 'stuffRate', 'stuff_rate'))
        d['line_yds'] = num(pick(dfn, 'lineYards', 'line_yards'))
        if t in ypc_allowed: d['ypc'], d['ypc_rank'] = round(ypc_allowed[t], 2), ypc_rank[t]
        for k in ('stuff', 'line_yds'):
            if d[k] is not None: d[k] = round(d[k], 3)

    # yards per pass attempt allowed, then blend each side's three ranks into one
    ypa_allowed = {}
    for t in teams:
        y, a = stat(t, 'netPassingYardsOpponent'), stat(t, 'passAttemptsOpponent')
        if y is not None and a: ypa_allowed[t] = y / a
    ypa_rank = {t: i + 1 for i, t in enumerate(sorted(ypa_allowed, key=lambda t: ypa_allowed[t]))}
    for t, d in pass_d.items():
        if t in ypa_allowed: d['ypa'], d['ypa_rank'] = round(ypa_allowed[t], 2), ypa_rank[t]
    def blend(side, yard_rank):
        mean = {}
        for t, d in side.items():
            d['epa_rank'] = d['rank']
            d['sp_rank'] = sp.get(t)
            parts = [r for r in (d['epa_rank'], d.get(yard_rank), sp.get(t)) if r]
            mean[t] = sum(parts) / len(parts)
        order = sorted(mean, key=lambda t: (mean[t], side[t]['epa_rank']))
        n = len(order)
        for i, t in enumerate(order):
            side[t]['rank'], side[t]['tier'] = i + 1, TIERS[min(3, i * 4 // n)]
    blend(run_d, 'ypc_rank')
    blend(pass_d, 'ypa_rank')

    matchups = {}
    for g in games:
        home, away = pick(g, 'homeTeam', 'home_team'), pick(g, 'awayTeam', 'away_team')
        book = lines.get((home, away)) or {}
        spread = num(book.get('spread'))                   # home line: negative = home favored
        total = num(pick(book, 'overUnder', 'over_under'))
        for tm, op, is_home in ((home, away, True), (away, home, False)):
            fav = None if spread is None else (-spread if is_home else spread)   # + = this team favored
            implied = None if total is None or fav is None else round((total + fav) / 2, 1)
            matchups[tm] = {'opp': op, 'opp_abbr': abbr.get(op, op), 'home': is_home,
                            'neutral': bool(pick(g, 'neutralSite', 'neutral_site')),
                            'kickoff': pick(g, 'startDate', 'start_date'),
                            'spread': fav, 'total': total, 'implied': implied,
                            'opp_run_d': run_d.get(op), 'opp_pass_d': pass_d.get(op), 'opp_sp_d_rank': sp.get(op),
                            'volume': volume(tm)}

    # ---- players: usage plus counting stats, for every team playing this week
    playing = set(matchups)
    players = {}
    def rec(pid, name, team, pos):
        key = str(pid or name + '|' + team)
        if key not in players:
            players[key] = {'id': key, 'name': name, 'team': team, 'abbr': abbr.get(team, team), 'pos': pos}
        elif pos and not players[key].get('pos'): players[key]['pos'] = pos
        return players[key]
    for u in get('/player/usage', year=season, excludeGarbageTime='true'):
        if u.get('team') not in playing: continue
        p = rec(u.get('id'), u.get('name'), u['team'], u.get('position'))
        us = u.get('usage') or {}
        p['usage'] = {k: round(num(us.get(k)), 3) for k in ('overall', 'rush', 'pass') if num(us.get(k)) is not None}
    for cat, keys in (('rushing', {'CAR': 'car', 'YDS': 'yds', 'TD': 'td', 'YPC': 'ypc'}),
                      ('receiving', {'REC': 'rec', 'YDS': 'yds', 'TD': 'td'}),
                      ('passing', {'COMPLETIONS': 'cmp', 'ATT': 'att', 'YDS': 'yds', 'TD': 'td', 'INT': 'int'})):
        for s in get('/stats/player/season', year=season, category=cat):
            if s.get('team') not in playing or s.get('statType') not in keys: continue
            p = rec(pick(s, 'playerId', 'player_id'), s.get('player'), s['team'], s.get('position'))
            p.setdefault(cat[:4], {})[keys[s['statType']]] = num(s.get('stat'))
    games_played = {t: stat(t, 'games') for t in playing}

    # ---- last three games: share of team carries and catches, from box scores
    boxes = []
    for wk in range(1, week):
        try: boxes += week_boxes(season, wk)
        except Exception as e: print(f'week {wk} box scores unavailable: {e!r}')
    by_team = {}
    for b in boxes:
        if b['team'] in playing: by_team.setdefault(b['team'], []).append(b)
    for t in by_team: by_team[t].sort(key=lambda b: b['week'])

    out = []
    for p in players.values():
        if p.get('pos') not in POSITIONS: continue
        us, ru, re_ = p.get('usage', {}), p.get('rush', {}), p.get('rece', {})
        if not (us.get('overall', 0) >= 0.02 or ru.get('car', 0) >= 5 or re_.get('rec', 0) >= 3 or p.get('pass', {}).get('att', 0) >= 10):
            continue
        p['games'] = games_played.get(p['team'])
        last = []
        for b in by_team.get(p['team'], [])[-4:]:
            me = b['players'].get(str(p['id'])) or next((v for v in b['players'].values() if v.get('name') == p['name']), {})
            last.append({'wk': b['week'], 'opp': abbr.get(b['opp'], b['opp']), 'home': b['home'],
                         'car': me.get('car', 0), 'rush_sh': round(me.get('car', 0) / b['car'], 3) if b['car'] else None,
                         'rec': me.get('rec', 0), 'rec_sh': round(me.get('rec', 0) / b['rec'], 3) if b['rec'] else None,
                         'fp': me.get('fp') if me else None})       # None = not in the box score (didn't play)
        if last: p['last'] = last
        if 'rece' in p: p['rec'] = p.pop('rece')
        out.append(p)
    out.sort(key=lambda p: (-(p.get('usage', {}).get('overall') or 0)))

    # ---- per-player numbers and where they sit at the position
    qual = {'RB': lambda p: (p.get('rush') or {}).get('car', 0) >= 20,
            'WR': lambda p: (p.get('rec') or {}).get('rec', 0) >= 6,
            'TE': lambda p: (p.get('rec') or {}).get('rec', 0) >= 6,
            'QB': lambda p: (p.get('pass') or {}).get('att', 0) >= 40}
    pool, game_pool = {}, {}
    for p in out:
        ru, rc, ps, us = p.get('rush') or {}, p.get('rec') or {}, p.get('pass') or {}, p.get('usage') or {}
        team_games = by_team.get(p['team'], [])
        mine = [(b, b['players'].get(str(p['id'])) or next((v for v in b['players'].values() if v.get('name') == p['name']), {}))
                for b in team_games]
        car, tcar = sum(m.get('car', 0) for b, m in mine), sum(b['car'] for b, m in mine)
        rec, trec = sum(m.get('rec', 0) for b, m in mine), sum(b['rec'] for b, m in mine)
        g = p.get('games') or len(team_games) or None
        per = lambda v: None if v is None or not g else v / g
        m = {'rush_sh': car / tcar if tcar else None, 'rec_sh': rec / trec if trec else None,
             'pass_use': us.get('pass'), 'touch_pg': per(ru.get('car', 0) + rc.get('rec', 0)),
             'ypc': ru.get('ypc') if ru.get('car', 0) >= 10 else None,
             'td_pg': per(ru.get('td', 0) + rc.get('td', 0)), 'rec_pg': per(rc.get('rec', 0)), 'yds_pg': per(rc.get('yds', 0)),
             'pass_yds_pg': per(ps.get('yds')), 'pass_td_pg': per(ps.get('td')), 'rush_yds_pg': per(ru.get('yds', 0))}
        played = [mm['fp'] for b, mm in mine if mm and mm.get('fp') is not None]
        if played: m['fp_pg'] = sum(played) / len(played)
        p['m'] = {k: round(v, 3) for k, v in m.items() if v is not None}
        if qual[p['pos']](p):
            for k, v in p['m'].items(): pool.setdefault(p['pos'], {}).setdefault(k, []).append(v)
            for b, mm in mine:
                for k, tot, v in (('rush_sh', b['car'], mm.get('car', 0)), ('rec_sh', b['rec'], mm.get('rec', 0))):
                    if tot: game_pool.setdefault(p['pos'], {}).setdefault(k, []).append(v / tot)
                if mm and mm.get('fp') is not None: game_pool.setdefault(p['pos'], {}).setdefault('fp', []).append(mm['fp'])
    def cuts_of(vals):
        v = sorted(vals)
        at = lambda q: round(v[min(len(v) - 1, int(q * len(v)))], 3)
        return [at(.85), at(.60), at(.30)] if len(v) >= 8 else None
    cuts = {pos: {k: cuts_of(v) for k, v in d.items()} for pos, d in pool.items()}
    for pos, d in game_pool.items():
        for k, v in d.items(): cuts.setdefault(pos, {})[k + '_g'] = cuts_of(v)
    implied = [m['implied'] for m in matchups.values() if m['implied'] is not None]
    plays = [m['volume']['plays_pg'] for m in matchups.values() if m.get('volume')]
    team_cuts = {'implied': cuts_of(implied), 'plays_pg': cuts_of(plays)}

    doc = {'season': season, 'week': week, 'built': now.strftime('%Y-%m-%dT%H:%MZ'),
           'matchups': matchups, 'cuts': cuts, 'team_cuts': team_cuts, 'players': out}
    with open(OUT, 'w') as f: json.dump(doc, f, separators=(',', ':'))
    lined = sum(1 for m in matchups.values() if m['spread'] is not None)
    print(f'{season} week {week}: {len(games)} FBS games ({lined // 2} with lines), {len(out)} players, '
          f'run/pass defenses ranked {len(run_d)}/{len(pass_d)} -> analysis/cfb.json')


if __name__ == '__main__':
    main()
