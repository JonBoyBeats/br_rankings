"""NBA takes history: your locked order against the Tiers button's order, rebuilt for every past lock.

A take is a decision pair (same combined tier, ADP within 4 picks at that lock) that your locked board orders one way
and the rebuilt button order (analysis/nba/report/tier_history.csv, built) the other. T5 counts only players with a
draft ADP (below that, your order is the board's tail sort, not a choice). Each slot is scored with the swap rule:
a player who sat counts his swap's points (his credited swaps in analysis/nba/report/swaps.csv, else that night's
average swap, else the season's). Writes analysis/nba/report/takes_history.csv, one row per take, and prints the
grade by pod size, window, AM sample and tier, with an 80% range from resampling slates.

  python3 scripts/nba_tier_takes.py
"""
import csv, collections, os, random

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
res=collections.defaultdict(lambda: collections.defaultdict(list))
rows_out=[]
for (d,w),rs in [(k,[r for r in H if (r['date'],r['window'])==k]) for k in sorted({(r['date'],r['window']) for r in H})]:
    sample=rs[0]['sample']; pod=rs[0]['pod']
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
                rows_out.append({'date': d, 'window': w, 'pod': pod, 'sample': sample, 'tier': t, 'you_first': (x if you else y)['name'],
                                 'button_first': (y if you else x)['name'], 'gain': round(first-second, 1)})
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
