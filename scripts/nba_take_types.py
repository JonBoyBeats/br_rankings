"""NBA takes by type of move, for one tier and window (default: AM T5, 6-drafter, primary sample).

Each take (a decision pair your locked order and the rebuilt Tiers button order put the other way round, scored with
the swap rule as in scripts/nba_tier_takes.py) is given one type, first that fits: a Q-tag push (the player you moved
down was tagged Q, D or GTD at the AM board), a Q-tag raise (the one you moved up was), a beneficiary pick (the one you
moved up had a teammate tagged or out then), ownership order (the two within 2 projected points and you put the less
drafted first), or another read. Prints pairs, how often you were right and points per take, with an 80% range from
resampling slates.

  python3 scripts/nba_take_types.py [pod] [sample] [am|pm] [tiers, e.g. 5 or 34]
"""
import csv,collections,random,glob,re,sys
WINDOW=sys.argv[3] if len(sys.argv)>3 else 'am'
H=list(csv.DictReader(open('analysis/nba/report/tier_history.csv')))
S=list(csv.DictReader(open('analysis/nba/report/swaps.csv')))
f=lambda v: float(v) if v not in ('',None) else None
sw=collections.defaultdict(lambda:[0,0.0]); night=collections.defaultdict(lambda:[0,0.0])
for r in S:
    n=int(r['teams']); x=sw[(r['date'],r['out_id'])]; x[0]+=n; x[1]+=n*float(r['swap_fp'])
    y=night[r['date']]; y[0]+=n; y[1]+=n*float(r['swap_fp'])
allsw=sum(v[1] for v in night.values())/sum(v[0] for v in night.values())
def slot(r):
    if r['scratched']=='1':
        k=(r['date'],r['player_id'])
        if k in sw: return sw[k][1]/sw[k][0]
        d=night.get(r['date']); return d[1]/d[0] if d else allsw
    return f(r['actual'])
# tags at the AM board for every player on the slate (out included), by team
tagged_teams=collections.defaultdict(set)
for p in glob.glob('analysis/nba/daily/*_main.csv'):
    for r in csv.DictReader(open(p)):
        if re.match(r'^(q|d|g|o)', r['injury_' + WINDOW] or '', re.I): tagged_teams[r['date']].add(r['team'])
QT=re.compile(r'^(q|d|g)',re.I)
def kind(a,b,d):
    if QT.match(b['tag'] or ''): return 'Q-tag push (tagged player moved down)'
    if QT.match(a['tag'] or ''): return 'Q-tag raise (tagged player moved up)'
    if a['team'] in tagged_teams[d]: return 'beneficiary pick (teammate tagged or out)'
    if f(a['proj']) is not None and f(b['proj']) is not None and abs(f(a['proj'])-f(b['proj']))<=2 and f(a['drafted']) is not None and f(b['drafted']) is not None and f(a['drafted'])<f(b['drafted']):
        return 'ownership order (within 2 pts, less drafted first)'
    return 'other read'
import sys
pod=sys.argv[1] if len(sys.argv)>1 else '6'; sample=sys.argv[2] if len(sys.argv)>2 else 'primary'
tier=sys.argv[4] if len(sys.argv)>4 else '5'
res=collections.defaultdict(lambda: collections.defaultdict(list)); ex=collections.defaultdict(list)
for d in sorted({r['date'] for r in H}):
    q=[r for r in H if r['date']==d and r['window']==WINDOW and r['pod']==pod and r['sample']==sample and r['tier'] in tier
       and r['your_rank'] and r['built'] and r['actual']!='' and f(r['adp']) is not None and f(r['adp'])<(24 if pod=='4' else 36)]
    for i in range(len(q)):
        for j in range(i+1,len(q)):
            x,y=q[i],q[j]
            if abs(f(x['adp'])-f(y['adp']))>4: continue
            you=int(x['your_rank'])<int(y['your_rank']); btn=int(x['built'])<int(y['built'])
            if you==btn: continue
            a,b=(x,y) if you else (y,x)
            g=slot(a)-slot(b)
            if g==0: continue
            k=kind(a,b,d); res[k][d].append(g); ex[k].append((d,a['name'],b['name'],round(g,1)))
rnd=random.Random(1)
print('pod',pod,WINDOW.upper(),sample,'tier',tier)
print('| Type of move | Nights | Pairs | You right | Points per take | 80% range |')
print('|---|---|---|---|---|---|')
for k in sorted(res, key=lambda k:-sum(len(v) for v in res[k].values())):
    per=res[k]; ds=list(per); allp=[v for d in ds for v in per[d]]
    bs=sorted(sum(s)/len(s) for s in ([v for d in (rnd.choice(ds) for _ in ds) for v in per[d]] for _ in range(1000)) if s)
    print('| %s | %d | %d | %.0f%% | %+.1f | %+.1f to %+.1f |'%(k,len(ds),len(allp),100*sum(1 for v in allp if v>0)/len(allp),sum(allp)/len(allp),bs[len(bs)//10],bs[len(bs)*9//10]))
for k in ex:
    print(k, ex[k][:4])
