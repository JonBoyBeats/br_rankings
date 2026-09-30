"""Build analysis/cfb.json: the college baseline the Board shows on CFB slates.

Every player gets the same baseline from collegefootballdata.com (CFBD), whatever any
writer covers; source notes (analysis/cfb/takes/) are layered on top by the page.

  usage     share of his team's plays he was involved in, garbage time excluded:
            overall, rush (share of team rushes) and pass (share of team pass plays)
  rushing   carries, yards, TDs, yards per carry · receiving: catches, yards, TDs
  passing   (QBs) completions, attempts, yards, TDs, INTs
  matchup   this week's opponent, spread, total and implied team total for EVERY FBS game,
            plus the opponent's defense against the run and the pass: EPA per play allowed,
            ranked 1 (stingiest) to N, cut into quarters: Tough, Average, Great, Elite

Season = the current college season; week = the next week with games still to play.
About a dozen API calls a run, well inside the free tier.

Usage: CFBD_API_KEY=... python3 scripts/build_cfb.py [--fixture DIR]
       (--fixture reads saved responses named after the endpoint instead of calling the API)"""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

API = 'https://api.collegefootballdata.com'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'cfb.json')
FIXTURE = sys.argv[sys.argv.index('--fixture') + 1] if '--fixture' in sys.argv else None
POSITIONS = {'QB', 'RB', 'WR', 'TE'}
TIERS = ['Tough', 'Average', 'Great', 'Elite']      # by the opponent's defensive rank, best defense first


def get(path, **params):
    if FIXTURE:
        name = path.strip('/').replace('/', '_') + ('_' + params['category'] if 'category' in params else '')
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
                            'opp_run_d': run_d.get(op), 'opp_pass_d': pass_d.get(op), 'opp_sp_d_rank': sp.get(op)}

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
    games_played = {}
    for s in get('/stats/season', year=season):
        if s.get('statName') == 'games' and s.get('team') in playing: games_played[s['team']] = num(s.get('statValue'))

    out = []
    for p in players.values():
        if p.get('pos') not in POSITIONS: continue
        us, ru, re_ = p.get('usage', {}), p.get('rush', {}), p.get('rece', {})
        if not (us.get('overall', 0) >= 0.02 or ru.get('car', 0) >= 5 or re_.get('rec', 0) >= 3 or p.get('pass', {}).get('att', 0) >= 10):
            continue
        p['games'] = games_played.get(p['team'])
        if 'rece' in p: p['rec'] = p.pop('rece')
        out.append(p)
    out.sort(key=lambda p: (-(p.get('usage', {}).get('overall') or 0)))

    doc = {'season': season, 'week': week, 'built': now.strftime('%Y-%m-%dT%H:%MZ'),
           'matchups': matchups, 'players': out}
    with open(OUT, 'w') as f: json.dump(doc, f, separators=(',', ':'))
    lined = sum(1 for m in matchups.values() if m['spread'] is not None)
    print(f'{season} week {week}: {len(games)} FBS games ({lined // 2} with lines), {len(out)} players, '
          f'run/pass defenses ranked {len(run_d)}/{len(pass_d)} -> analysis/cfb.json')


if __name__ == '__main__':
    main()
