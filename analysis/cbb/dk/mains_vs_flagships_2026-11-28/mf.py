"""Mains vs flagships: per contest type, our real entries' results, construction, variance; field size and payout shape.
Contest types as in the Friday review (sections 9 and 11): qualifier/small = qualifier|satellite or <100 entries;
flagship = "Pull Up Jumper" or 100-799 entries; main = 800+ entries."""
import csv, json, os, re, sys, math, random, statistics as S, itertools
from collections import defaultdict, Counter
sys.path.insert(0, "/home/user/br_rankings/scripts")
import dk_eval as E
D = "/home/user/br_rankings/analysis/cbb/dk"
M = E.Mirror("/home/user/br-adp-mirror")
SUP = json.load(open(os.path.join(D, "contests_supplement.json")))["contests"]
def ctype(name, size):
    if re.search("qualifier|satellite", name, re.I) or size < 100: return "qualifier/small"
    if re.search("pull up jumper", name, re.I) or 100 <= size < 800: return "flagship"
    return "main"
ev = {r["contest_id"]: r for r in csv.DictReader(open(os.path.join(D, "eval.csv"))) if r["who"] == "mine"}
recs = {}
def rec_for(date, g):
    k = (date, g)
    if k not in recs:
        p = os.path.join(D, "%s_%s.csv" % (date, g)); recs[k] = E.read(p)
    return recs[k]
out = []
for cid, e in sorted(ev.items(), key=lambda kv: kv[1]["date"]):
    f = os.path.join(D, "standings", "contest-standings-%s.csv" % cid)
    if not os.path.exists(f): print("no standings", cid); continue
    entries, players = E.standings(f)
    n = len(entries); fee = float(e["fee"]); name = e["contest"]
    payouts = None
    if cid in SUP: payouts = SUP[cid]["payouts"]; maxpu = SUP[cid].get("max_per_user")
    else:
        rec_, slate, _ = E.slate_for(M, cid)
        c = next((c for c in (slate or {}).get("contests", []) if str(c["id"]) == cid), None) if slate else None
        payouts = (c or {}).get("payouts"); maxpu = (c or {}).get("max_entries_per_user") or (c or {}).get("max_per_user") or (c or {}).get("maxEntriesPerUser")
    table = E.pay_table(payouts)
    paid = max(table) if table else 0
    prize = sum(table.values())
    rec = rec_for(e["date"], e["draft_group"])
    info = {r["name"]: r for r in rec}
    own = {nm: v[0] or 0 for nm, v in players.items()}
    mine = [x for x in entries if x["name"].lower().startswith(E.USER)]
    def lineup_stats(L):
        if len(L) != 8: return None
        rs = [info.get(nm) for nm in L]
        if any(r is None for r in rs): return None
        sal = sum(int(r["salary"]) for r in rs)
        tc = Counter(r["team"] for r in rs); gc = Counter(r["game"] for r in rs)
        osum = sum(own.get(nm, 0) for nm in L)
        tops = sorted(gc.values(), reverse=True)
        return {"own_sum": osum, "sub10": sum(own.get(nm, 0) < 10 for nm in L), "chalk15": sum(own.get(nm, 0) >= 15 for nm in L),
                "sal_left": 50000 - sal, "team_max": max(tc.values()), "game_max": tops[0],
                "stack_3_2": int(tops[0] >= 3 and len(tops) > 1 and tops[1] >= 2), "stack_2_1": int(tops[0] >= 2),
                "proj": sum(E.num(r["fp_dk"]) or 0 for r in rs)}
    my = []
    for x in mine:
        L = E.lineup_names(x["lineup"]); st = lineup_stats(L)
        my.append({"rank": x["rank"], "pay": table.get(x["rank"], 0), "pct": 100 * (n - x["rank"]) / max(n - 1, 1), "L": tuple(sorted(L)), "st": st})
    # field (everyone else) construction, sampled
    rng = random.Random(1)
    fl = [x for x in entries if not x["name"].lower().startswith(E.USER)]
    samp = rng.sample(fl, min(400, len(fl)))
    fst = [s for s in (lineup_stats(E.lineup_names(x["lineup"])) for x in samp) if s]
    # dup within field: share of our lineups some other entry also has
    fsets = Counter(tuple(sorted(E.lineup_names(x["lineup"]))) for x in fl)
    # overlap among our entries
    Ls = [m["L"] for m in my if len(m["L"]) == 8]
    pair = [len(set(a) & set(b)) for a, b in itertools.combinations(Ls, 2)]
    expo = Counter(nm for L in Ls for nm in L)
    out.append({"cid": cid, "date": e["date"], "g": e["draft_group"], "name": name, "type": ctype(name, n), "n": n, "fee": fee,
                "k": len(my), "fees": fee * len(my), "back": sum(m["pay"] for m in my), "eval_back": float(e["dollars_back"]), "eval_fees": float(e["fees"]),
                "pays": [m["pay"] for m in my], "pcts": [m["pct"] for m in my], "paid_places": paid, "prize": prize,
                "top_prize": table.get(1, 0), "maxpu": maxpu,
                "my_st": [m["st"] for m in my if m["st"]], "field_st": fst,
                "dup_field": sum(fsets.get(L, 0) > 0 for L in Ls) / len(Ls) if Ls else None,
                "pair_overlap": S.mean(pair) if pair else None,
                "max_expo": max(expo.values()) / len(Ls) if Ls else None,
                "distinct": len(set(Ls))})
json.dump(out, open("mf_rows.json", "w"))
print("contests", len(out), "fees check standings vs eval:", sum(r["fees"] for r in out), sum(r["eval_fees"] for r in out),
      "back:", sum(r["back"] for r in out), sum(r["eval_back"] for r in out))
