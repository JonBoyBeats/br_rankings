"""NBA takes history: your locked order against the Tiers button's order, rebuilt for every past lock.

A take is a decision pair (same combined tier, ADP within 4 picks at that lock) that your locked board orders one way
and the rebuilt button order (analysis/nba/report/tier_history.csv, built) the other. T5 counts only players with a
draft ADP (below that, your order is the board's tail sort, not a choice). Each slot is scored with the swap rule:
a player who sat counts his swap's points (his credited swaps in analysis/nba/report/swaps.csv, else that night's
average swap, else the season's). Writes analysis/nba/report/takes_history.csv, one row per take, and prints the
grade by pod size, window, AM sample and tier, with an 80% range from resampling slates.

Each take is credited to a source (2026-11-09):
  ETR / Bagel   your move matches a note that day from ETR (Gallagher's columns, <date>_etr_*.csv) or Zakarian (Bagel,
                <date>_zakarian.csv) stamped (`at`) before the window's record (the lock, or the save it fell back to)
                and on the slate's own Pacific day: you moved up a player the note likes (Great, Good, Like, Lean) or
                moved down one it fades (Bad, Fade); a plain Note, a note without a stamp, one stamped after the record
                or one from an earlier day credits no one; both: "Bagel+ETR". Files before 2026-11-09 carry the time
                they were first committed to the repo (no earlier than they were in hand)
  NEWS          else, either player's projection or his team's status changed since the last lock: PM, ETR moved 2+
                points from its first upload to the PM record, or a tag on his team changed from the AM record to the
                PM record; AM (no lock before it that day), our Proj at the AM record 2+ off the morning file, or a tag
                on his team at the AM record
  OTHER         the rest

  python3 scripts/nba_tier_takes.py
"""
import csv, collections, datetime as dt, glob, json, os, random, re

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REP = os.path.join(HERE, "analysis", "nba", "report")
H=list(csv.DictReader(open(os.path.join(REP, 'tier_history.csv'))))
S=list(csv.DictReader(open(os.path.join(REP, 'swaps.csv'))))
f=lambda v: float(v) if v not in ('',None) else None
sw=collections.defaultdict(lambda:[0,0.0]); night=collections.defaultdict(lambda:[0,0.0])
for r in S:
    n=int(r['teams']); x=sw[(r['date'],r['out_id'])]; x[0]+=n; x[1]+=n*float(r['swap_fp'])
    y=night[r['date']]; y[0]+=n; y[1]+=n*float(r['swap_fp'])
allsw=sum(v[1] for v in night.values())/sum(v[0] for v in night.values())
def slot(r):
    """FP of the slot: the player, or his swap when he sat (credited swaps, else the night's, else the season's)."""
    if r['scratched']=='1':
        k=(r['date'],r['player_id'])
        if k in sw: return sw[k][1]/sw[k][0], 'swap'
        d=night.get(r['date']); return (d[1]/d[0] if d else allsw), 'swap (night avg)'
    return f(r['actual']), 'played'
DAILY = os.path.join(HERE, "analysis", "nba", "daily")
NOTES = {"ETR": "etr_*", "Bagel": "zakarian"}     # source -> <date>_<file>.csv in analysis/nba/takes (ETR: matchups, top plays)
TAG = re.compile(r"^(q|d|g|o)", re.I)
LIKES, FADES = {"great", "good", "like", "lean"}, {"bad", "fade"}
norm = lambda n: re.sub(r"[^a-z ]", "", (n or "").lower().replace("-", " ").replace(".", "")).strip()
iso = lambda t: dt.datetime.fromisoformat(t.replace("Z", "+00:00"))
meta = json.load(open(os.path.join(DAILY, "meta.json")))
daily = {}
for p in glob.glob(os.path.join(DAILY, "*_main.csv")):
    for r in csv.DictReader(open(p)):
        daily[(r["date"], r["player_id"])] = r
def notes(d):
    """{name key: [(source, at or None, stance)]} for the day."""
    out = collections.defaultdict(list)
    for src, fn in NOTES.items():
        for p in glob.glob(os.path.join(HERE, "analysis", "nba", "takes", "%s_%s.csv" % (d, fn))):
            for r in csv.DictReader(open(p)):
                out[norm(r["player"])].append((src, iso(r["at"]) if r.get("at") else None, (r.get("stance") or "").strip().lower()))
    return out
PT = __import__("zoneinfo").ZoneInfo("America/Los_Angeles")
def in_time(t, d, at):
    """A note counts for a take when stamped on the slate's Pacific day and before the window's record."""
    return t is not None and at is not None and t.astimezone(PT).date().isoformat() == d and t <= at
def record_at(d, w):
    m = next((v for k, v in meta.items() if k.startswith(d)), {})
    x = m.get(w) or {}
    return iso(x["at"]) if x.get("at") else None
def changed(d, w, r):
    """Whether his projection or his team's status changed since the last lock (see the docstring)."""
    e, mates = daily.get((d, r["player_id"]), {}), [x for x in daily_by_team.get((d, r["team"]), [])]
    if w == "pm":
        a, b = f(e.get("etr_first")), f(e.get("etr_pm"))
        moved = a is not None and b is not None and abs(a - b) >= 2
        return moved or any((x.get("injury_am") or "") != (x.get("injury_pm") or "") for x in mates)
    a, b = f(e.get("ours_raw")), f(e.get("ours_am"))
    return (a is not None and b is not None and abs(a - b) >= 2) or any(TAG.match(x.get("injury_am") or "") for x in mates)
daily_by_team = collections.defaultdict(list)
for (d, pid), r in daily.items():
    daily_by_team[(d, r["team"])].append(r)
def source(d, w, a, b, nt):
    at = record_at(d, w)
    # a: the player you moved up; b: the one you moved down. Credit the sources whose note agrees with the move.
    got = sorted({src for r, want in ((a, LIKES), (b, FADES)) for src, t, st in nt.get(norm(r["name"]), [])
                  if st in want and in_time(t, d, at)})
    if got:
        return "+".join(got)
    return "NEWS" if changed(d, w, a) or changed(d, w, b) else "OTHER"
res=collections.defaultdict(lambda: collections.defaultdict(list))
rows_out=[]
for (d,w),rs in [(k,[r for r in H if (r['date'],r['window'])==k]) for k in sorted({(r['date'],r['window']) for r in H})]:
    sample=rs[0]['sample']; pod=rs[0]['pod']; nt=notes(d)
    for t in '12345':
        cap0=24.0 if pod=='4' else 36.0
        q=[r for r in rs if r['tier']==t and r['your_rank'] and r['built'] and r['actual']!='' and f(r['adp']) is not None and f(r['adp'])<cap0]
        for i in range(len(q)):
            for j in range(i+1,len(q)):
                x,y=q[i],q[j]
                cap=24.0 if pod=='4' else 36.0
                if abs((f(x['adp']) or cap)-(f(y['adp']) or cap))>4: continue
                you= int(x['your_rank'])<int(y['your_rank']); btn=int(x['built'])<int(y['built'])
                if you==btn: continue
                fx,fy=slot(x)[0],slot(y)[0]
                if fx==fy: continue
                first,second=(fx,fy) if you else (fy,fx)
                res[(pod,w,sample,t)][d].append(first-second)
                a,b=(x,y) if you else (y,x)
                rows_out.append({'date': d, 'window': w, 'pod': pod, 'sample': sample, 'tier': t, 'you_first': a['name'],
                                 'button_first': b['name'], 'gain': round(first-second, 1), 'you_first_id': a['player_id'],
                                 'button_first_id': b['player_id'], 'source': source(d, w, a, b, nt)})
print('| Pod | Window | Sample | Tier | Nights | Takes (pairs) | You right | Points per take | 80% range |')
print('|---|---|---|---|---|---|---|---|---|')
rnd=random.Random(1)
for k in sorted(res):
    per=res[k]; ds=list(per); allp=[v for d in ds for v in per[d]]
    if not allp: continue
    right=sum(1 for v in allp if v>0)/len(allp); ppt=sum(allp)/len(allp)
    bs=[]
    for _ in range(1000):
        s=[v for d in (rnd.choice(ds) for _ in ds) for v in per[d]]
        if s: bs.append(sum(s)/len(s))
    bs.sort()
    tt='T3/T4' if False else 'T'+k[3]
    print('| %s | %s | %s | %s | %d | %d | %.0f%% | %+.1f | %+.1f to %+.1f |'%(k[0],k[1].upper(),k[2],tt,len(ds),len(allp),100*right,ppt,bs[len(bs)//10],bs[len(bs)*9//10]))

with open(os.path.join(REP, 'takes_history.csv'), 'w', newline='') as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
    wr.writeheader()
    wr.writerows(rows_out)
print('%d takes -> analysis/nba/report/takes_history.csv' % len(rows_out))
