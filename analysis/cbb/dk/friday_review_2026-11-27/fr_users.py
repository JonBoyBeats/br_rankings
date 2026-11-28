"""Friday review 2026-11-27, section 5 (redefined): the best DFS users in our contests, and how they build.

Data: every graded slate's contests with standings on hand (analysis/cbb/dk/standings, eval.csv's contests), the night
record (salary, game, team, min_proj, actual_dk), the mirror's lock-time slate (fee and payout table), dk_own_review's
big-game flags. A user is the EntryName before " (k/n)". Our own entries are labelled "us" and never named.

Per entry: finish pct = 100 x (N - entries scoring more) / N; top 10% / top 1% = place within ceil(0.1 N) / ceil(0.01 N);
payout from the contest's table at its place (ties not split, as dk_eval fills). Per lineup traits (field = all entries
of the contest): own_sum (real %Drafted summed), sub10 (players under 10% real), sal_left (50,000 - salary), max_game
and max_team (players from one game / team), stack21 (a game with 2+ from one team and 1+ from the other), stack32
(3+ and 2+), dup (other entries with the same 8 players), punts (players we projected under 15 minutes), big (players
coming off a big game), chalk (players 15%+ real), topval (players in the slate's top 10 by actual DK pts / $1k).
Per user-slate (multi-entry): max player exposure and distinct 3-player cores (the lineup's three highest salaries).

  python3 fr_users.py  (paths assume sibling checkouts under /home/user)
"""
import csv, glob, json, math, os, random, re, statistics as S, sys
from collections import defaultdict, Counter
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E, dk_proj_grade as PG, dk_own_review as R
M = E.Mirror("/home/user/br-adp-mirror")
DK = "/home/user/br_rankings/analysis/cbb/dk"
num = E.num
MIN_SLATES, MIN_ENTRIES, BOOT = 5, 10, 2000
TRAITS = ["own_sum", "sub10", "sal_left", "max_game", "max_team", "stack21", "stack32", "dup", "punts", "big", "chalk", "topval"]

def ctype(name, size):
    if re.search("qualifier|satellite", name, re.I) or size < 100: return "qualifier/small"
    if re.search("pull up jumper", name, re.I) or size < 800: return "flagship"
    return "main"

bigs = R.big_game_flags("/home/user/br-adp-mirror")
ev = defaultdict(set)
for r in csv.DictReader(open(DK + "/eval.csv")): ev[r["draft_group"]].add(r["contest_id"])
E_rows = []            # one per entry
US = E.USER
for name, rows in PG.slates():
    g = name.split("_")[1]
    rec = {r["dk_id"]: r for r in rows}
    byname = {}
    for r in rows: byname.setdefault(r["name"], []).append(r["dk_id"])
    byname = {k: v[0] for k, v in byname.items() if len(v) == 1}
    vals = sorted([r for r in rows if num(r.get("actual_dk")) is not None and num(r.get("salary"))], key=lambda r: -num(r["actual_dk"]) / num(r["salary"]))
    topv = {r["dk_id"] for r in vals[:10]}
    bg = bigs.get(g) or set()
    for cid in sorted(ev[g]):
        f = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(f): continue
        entries, players = E.standings_rows(open(f, encoding="utf-8-sig"))
        if len(entries) < 2: continue
        _, slate, _ = E.slate_for(M, cid)
        contest = next((c for c in (slate or {}).get("contests", []) if str(c["id"]) == cid), None) if slate else None
        if not contest: continue
        table, fee = E.pay_table(contest.get("payouts")), contest.get("entry_fee") or 0
        N = len(entries); field = sorted((e["points"] for e in entries), reverse=True)
        own = {nm: (v[0] or 0.0) for nm, v in players.items()}
        lus = [tuple(sorted(E.lineup_names(e["lineup"]))) for e in entries]
        cnt = Counter(lus)
        ct = ctype(contest.get("name", ""), N)
        for e, L in zip(entries, lus):
            if len(L) != 8: continue
            ids = [byname.get(nm) for nm in L]
            if any(i is None for i in ids): continue
            rs = [rec[i] for i in ids]
            u = e["name"].split(" (")[0].strip()
            u = "us" if u.lower() == US else u
            place = E.placed(e["points"], field)
            games = Counter(r["game"] for r in rs); teams = Counter(r["team"] for r in rs)
            def stack(a, b):
                for gm in games:
                    tc = sorted([teams[t] for t in {r["team"] for r in rs if r["game"] == gm}], reverse=True) + [0]
                    if tc[0] >= a and tc[1] >= b: return 1
                return 0
            sal = sum(num(r["salary"]) for r in rs)
            E_rows.append({"slate": name, "g": g, "cid": cid, "type": ct, "N": N, "fee": fee, "user": u,
                           "pct": 100 * (N - (place - 1)) / N, "top10": int(place <= math.ceil(0.1 * N)), "top1": int(place <= math.ceil(0.01 * N)),
                           "pay": table.get(place, 0),
                           "own_sum": sum(own.get(nm, 0) for nm in L), "sub10": sum(own.get(nm, 0) < 10 for nm in L),
                           "sal_left": 50000 - sal, "max_game": max(games.values()), "max_team": max(teams.values()),
                           "stack21": stack(2, 1), "stack32": stack(3, 2), "dup": cnt[L] - 1,
                           "punts": sum((num(r.get("min_proj")) or 0) < 15 for r in rs), "big": sum(i in bg for i in ids),
                           "chalk": sum(own.get(nm, 0) >= 15 for nm in L), "topval": sum(i in topv for i in ids),
                           "ids": ids, "core": tuple(sorted(sorted(ids, key=lambda i: -num(rec[i]["salary"]))[:3]))})
print("entries %d, users %d, slates %d, contests %d" % (len(E_rows), len({e['user'] for e in E_rows}), len({e['slate'] for e in E_rows}), len({e['cid'] for e in E_rows})))

# ---- WHO: per-user measures; slate-level means, bootstrap over slates
by_user = defaultdict(list)
for e in E_rows: by_user[e["user"]].append(e)
max_ent = defaultdict(int)
for e in E_rows: pass
per_uc = Counter((e["user"], e["cid"]) for e in E_rows)
for (u, c), n in per_uc.items(): max_ent[u] = max(max_ent[u], n)
def kind(u): return "multi (20-150)" if max_ent[u] >= 20 else ("single" if max_ent[u] == 1 else "few (2-19)")
def slate_means(es, key):
    d = defaultdict(list)
    for e in es: d[e["slate"]].append(e[key])
    return {s: S.mean(v) for s, v in d.items()}
rng = random.Random(11)
def boot(es):
    sm = slate_means(es, "pct"); ss = list(sm)
    if len(ss) < 2: return None, None
    bs = sorted(S.mean(sm[rng.choice(ss)] for _ in ss) for _ in range(BOOT))
    return bs[int(0.05 * BOOT)], bs[int(0.95 * BOOT)]
Q = []
for u, es in by_user.items():
    ns = len({e["slate"] for e in es})
    if ns < MIN_SLATES or len(es) < MIN_ENTRIES: continue
    sm = slate_means(es, "pct"); lo, hi = boot(es)
    fees = sum(e["fee"] for e in es); pay = sum(e["pay"] for e in es)
    Q.append({"user": u, "kind": kind(u), "slates": ns, "entries": len(es), "pct": S.mean(sm.values()), "lo": lo, "hi": hi,
              "top10": S.mean(e["top10"] for e in es), "top1": S.mean(e["top1"] for e in es), "roi": (pay - fees) / fees if fees else None,
              "types": dict(Counter(e["type"] for e in es))})
print("\nqualified users (>= %d slates, >= %d entries): %d" % (MIN_SLATES, MIN_ENTRIES, len(Q)))
for k in ("multi (20-150)", "few (2-19)", "single"):
    G = sorted([q for q in Q if q["kind"] == k], key=lambda q: -q["pct"])
    print("\n== %s: %d users; ranked by mean finish pct over slates (90%% bootstrap band over slates)" % (k, len(G)))
    for i, q in enumerate(G):
        if i < 15 or q["user"] == "us":
            print("%3d %-20s slates %2d entries %4d | pct %.1f [%.1f, %.1f] | top10 %.3f top1 %.3f | ROI %s | %s" % (
                i + 1, q["user"], q["slates"], q["entries"], q["pct"], q["lo"], q["hi"], q["top10"], q["top1"],
                "%+.0f%%" % (100 * q["roi"]) if q["roi"] is not None else "n/a", q["types"]))
field_pct = S.mean(e["pct"] for e in E_rows)
print("\nfield mean pct %.1f (by construction about 50)" % field_pct)
nonsep = sum(1 for q in Q if q["lo"] is not None and q["lo"] <= 50 <= q["hi"])
print("qualified users whose 90%% band contains 50: %d of %d" % (nonsep, len(Q)))

# ---- HOW THEY BUILD: top group = qualified non-us users whose band lower edge > 50 ("clear") and top 10 by pct
ranked = sorted([q for q in Q if q["user"] != "us"], key=lambda q: -q["pct"])
top = [q["user"] for q in ranked[:10]]
clear = [q["user"] for q in ranked if q["lo"] is not None and q["lo"] > 50]
print("\ntop 10 by pct:", top, "\nclear (band above 50):", clear)
def traits(es):
    return {t: S.mean(e[t] for e in es) for t in TRAITS}
def slate_trait(es, t):
    return slate_means(es, t)
groups = {"top 10": [e for e in E_rows if e["user"] in top], "field": E_rows, "us": [e for e in E_rows if e["user"] == "us"]}
print("\ntraits per lineup (mean over entries): group | " + " | ".join(TRAITS))
for k, es in groups.items():
    tr = traits(es); print("%-8s n=%5d | " % (k, len(es)) + " | ".join("%.2f" % tr[t] for t in TRAITS))
# paired per slate: (group - field) on each trait, contest-matched (field = same contests)
print("\nper slate, group minus field in the SAME contests (mean ± SE over slates, positive on k):")
def paired(group, t, slates=None):
    d = []
    for s in sorted({e["slate"] for e in group}):
        if slates is not None and s not in slates: continue
        ge = [e for e in group if e["slate"] == s]; cs = {e["cid"] for e in ge}
        fe = [e for e in E_rows if e["slate"] == s and e["cid"] in cs]
        d.append(S.mean(e[t] for e in ge) - S.mean(e[t] for e in fe))
    return d
def f(d): return "%+.2f ± %.2f (%d), +%d" % (S.mean(d), S.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else float("nan"), len(d), sum(x > 0 for x in d)) if d else "n/a"
for t in TRAITS + ["pct"]:
    print("%-9s top10-field %s | us-field %s" % (t, f(paired(groups["top 10"], t)), f(paired(groups["us"], t))))

# exposure spread for multi-entry users per slate
print("\nexposure spread per user-slate (users with 20+ entries that slate): max player exposure, distinct cores / entries")
def spread(u):
    out = []
    for s in sorted({e["slate"] for e in by_user[u]}):
        es = [e for e in by_user[u] if e["slate"] == s]
        if len(es) < 20: continue
        c = Counter(i for e in es for i in e["ids"])
        out.append((max(c.values()) / len(es), len({e["core"] for e in es}) / len(es)))
    return out
allmulti = [u for u in by_user if u != "us" and kind(u).startswith("multi")]
for lab, us_ in (("top 10 multi", [u for u in top if kind(u).startswith("multi")]), ("all other multi", [u for u in allmulti if u not in top]), ("us", ["us"])):
    v = [x for u in us_ for x in spread(u)]
    if v: print("%-16s user-slates %3d | max exposure %.2f | distinct cores share %.2f" % (lab, len(v), S.mean(x[0] for x in v), S.mean(x[1] for x in v)))

# ---- CONSISTENCY: each top user's style across slates (SD over slates of slate-mean own_sum, sal_left, stack32)
print("\nconsistency of each top user's style across slates (mean / SD over slates):")
for u in top:
    es = by_user[u]; row = []
    for t in ("own_sum", "sub10", "sal_left", "stack32", "max_game", "dup"):
        sm = list(slate_means(es, t).values()); row.append("%s %.1f/%.1f" % (t, S.mean(sm), S.stdev(sm) if len(sm) > 1 else 0))
    print("  %-20s %s" % (u, " ".join(row)))
# pairwise: how different are top users from each other vs from field (own_sum and sal_left)
for t in ("own_sum", "sal_left", "stack32"):
    ms = [S.mean(e[t] for e in by_user[u]) for u in top]
    print("top users' %s means: min %.2f max %.2f | field %.2f" % (t, min(ms), max(ms), S.mean(e[t] for e in E_rows)))

# ---- HELD OUT: define the top group on half the slates, test skill persistence and trait separation on the other half
sl = sorted({e["slate"] for e in E_rows})
halves = [(set(sl[0::2]), set(sl[1::2])), (set(sl[1::2]), set(sl[0::2]))]
print("\nheld out (slates alternated; top group = top 10 qualified non-us users by mean pct on the fit half, >= 3 slates and 5 entries there):")
for i, (A, B) in enumerate(halves):
    def qual(slates, ms_, me_):
        out = []
        for u, es in by_user.items():
            if u == "us": continue
            ee = [e for e in es if e["slate"] in slates]
            if len({e["slate"] for e in ee}) >= ms_ and len(ee) >= me_: out.append((S.mean(slate_means(ee, "pct").values()), u))
        return out
    qa = sorted(qual(A, 3, 5), reverse=True); T = [u for _, u in qa[:10]]
    grpB = [e for e in E_rows if e["user"] in T and e["slate"] in B]
    print(" split %d: fit on %d slates, test on %d; top group %s" % (i + 1, len(A), len(B), T))
    print("   skill persists? pct top-field on the test half:", f(paired(grpB, "pct")))
    for t in TRAITS:
        fa = paired([e for e in E_rows if e["user"] in T and e["slate"] in A], t); fb = paired(grpB, t)
        print("   %-9s fit half %s | test half %s" % (t, f(fa), f(fb)))
json.dump({"Q": Q, "top": top}, open("/tmp/claude-0/-home-user/bae0c6e2-0e8b-51f6-b7b0-513f67c00739/scratchpad/fr_users.json", "w"))
