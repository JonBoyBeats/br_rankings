"""Max-entry random draws by contest type (2026-11-28; analysis only).

For every saved build with real standings: each entered contest's max entries per user (the contest's max_per_user,
capped at the kept pool) drawn at random from the build's kept pool, 1,000 draws per contest, under two rules:
  plain - uniform from the whole kept pool;
  top50 - uniform from the top half of the kept pool by board sim value (builds whose board values cover the pool).
Caps, as the page's main profile: player exposure at most ceil(60% of the entries), and every pair of our lineups
at least 3 players apart (min unique 3); a draw that breaks either is redrawn (up to 200 tries per seat; seats that
can't be filled are counted and reported).
The same is done at the ACTUAL entry count (the lineups really entered in that contest), for the small-sample view.
Scoring: our real entries are taken out of the standings (dk_eval.USER), the drawn lineups are put in together, and
each of ours is paid the mean of the places its points tie over (ties split; our own lineups push each other down).
Contest type: scripts/dk_contest_type.py (the page's profile), from the contest's name and lobby size."""
import json, glob, os, sys, math, random, statistics as S
from collections import defaultdict, Counter
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dk_eval as E, dk_contest_type as CT
M = E.Mirror(os.environ.get("MIRROR", "/home/user/br-adp-mirror"))
DRAWS = int(os.environ.get("DRAWS", 1000))
rng = random.Random(20261128)

banks = {}
for f in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
    b = json.load(open(f)); g = str(b["draft_group"])
    if g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or ""): banks[g] = b

def draw(idx, N, L, sets_):
    """N lineups from idx (uniform, without replacement) under the exposure and min-unique caps."""
    cap = max(1, math.ceil(0.6 * N)); cnt = Counter(); out = []; tries = 0
    pool = idx[:]
    while len(out) < N and tries < 200 * N:
        tries += 1
        k = pool[rng.randrange(len(pool))]
        if k in out: continue
        s = sets_[k]
        if any(cnt[p] >= cap for p in s): continue
        if any(len(s & sets_[j]) > 5 for j in out): continue
        out.append(k); cnt.update(s)
    return out

def score(ours_pts, field_desc, table, n_tot):
    """Payout and finish pct for each of our lineups, inserted together with the field (ties split)."""
    import bisect
    fa = sorted(field_desc)                          # ascending, for counts
    od = sorted(ours_pts)
    res = []
    for v in ours_pts:
        f_gt = len(fa) - bisect.bisect_right(fa, v); f_eq = bisect.bisect_right(fa, v) - bisect.bisect_left(fa, v)
        o_gt = len(od) - bisect.bisect_right(od, v); o_eq = bisect.bisect_right(od, v) - bisect.bisect_left(od, v)
        start = 1 + f_gt + o_gt; t = f_eq + o_eq
        pay = sum(table.get(p, 0) for p in range(start, start + t)) / t
        res.append((pay, 100.0 * (n_tot - (start - 1)) / n_tot, start <= max(1, math.ceil(0.01 * n_tot))))
    return res

rows = []
for g, b in sorted(banks.items(), key=lambda kv: kv[1]["day"]):
    pf = {c: ks for c, ks in (b.get("portfolios") or {}).items() if ks}
    files = {c: os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c) for c in pf}
    if not pf or not all(os.path.exists(p) for p in files.values()):
        print("skip", b["day"], g, "standings missing" if pf else "no portfolios"); continue
    pool = b["pool"]; kept = sorted(set(b.get("final") or range(len(pool))))
    vals = ((b.get("cut_state") or {}).get("board") or {}).get("values")
    top = None
    if vals and len(vals) == len(b["final"]):
        order = [k for _, k in sorted(zip([-(v[0] if isinstance(v, list) else v) for v in vals], b["final"]))]
        top = order[:len(order) // 2]
    sets_ = {k: frozenset(str(i) for i in pool[k]) for k in kept}
    for cid, ks in pf.items():
        entries, players = E.standings(files[cid])
        rec, slate, _ = E.slate_for(M, cid)
        if not rec: print("skip", cid, "no night record"); continue
        con = next(c for c in slate["contests"] if str(c["id"]) == cid)
        typ = CT.contest_type(con.get("name", ""), con.get("size") or len(entries))
        table = E.pay_table(con.get("payouts")); fee = con.get("entry_fee") or 0
        field = sorted((e["points"] for e in entries if (e["name"] or "").split(" (")[0].lower() != E.USER.lower()), reverse=True)
        ours_real = [e for e in entries if (e["name"] or "").split(" (")[0].lower() == E.USER.lower()]
        pts = E.night_points(rec, players)
        P = {k: sum(pts.get(str(i)) or 0 for i in pool[k]) for k in set(kept) | set(ks)}
        mx = int(con.get("max_per_user") or len(ks)); N_max = min(mx, len(kept)); N_act = len(ks)
        real = score([P[k] for k in ks], field, table, len(field) + N_act)
        r = {"g": g, "day": b["day"], "cid": cid, "name": con.get("name"), "type": typ, "fee": fee, "n_field": len(field),
             "max": mx, "N_max": N_max, "N_act": N_act, "pool": len(kept), "binds": mx > len(kept),
             "real": {"pay": sum(x[0] for x in real), "pct": S.mean(x[1] for x in real)}, "rules": {}}
        for rule, idx in (("plain", kept), ("top50", top)):
            if idx is None: continue
            for lab, N in (("max", N_max), ("act", N_act)):
                pays, pcts, t1, cash, short = [], [], 0, 0, 0
                for _ in range(DRAWS):
                    pick = draw(idx, N, P, sets_)
                    short += N - len(pick)
                    sc = score([P[k] for k in pick], field, table, len(field) + len(pick))
                    pays.append(sum(x[0] for x in sc)); pcts.append(S.mean(x[1] for x in sc) if sc else float("nan"))
                    t1 += sum(x[2] for x in sc); cash += sum(x[0] > 0 for x in sc)
                r["rules"]["%s_%s" % (rule, lab)] = {"N": N, "pays": pays, "pct": S.mean(pcts), "top1": t1 / (DRAWS * N),
                                                     "cash": cash / (DRAWS * N), "short": short / DRAWS}
        rows.append(r)
        print(b["day"], g, cid, typ, "max", mx, "act", N_act, "pool", len(kept), flush=True)
json.dump(rows, open(os.path.join(os.path.dirname(__file__), "med_rows.json"), "w"))
