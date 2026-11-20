"""A2 test (b), 2026-11-20: a Questionable player who missed his team's last game(s), out by default (as Doubtful,
with Play him) or a harder discount. Each graded slate's Q player-nights, with how many of his team's most recent
games (the mirror's slate file before lock: last5 dates, every teammate's) he missed in a row; the dates are on file
from 11-18 on. Then, on those slates, the rule: each such player Out, his team refit to 200 (battle-royale-research
cbb_nightly.fit_minutes), measured on news misses (projected 15+, played 0), the minutes MAE (A1's: blowouts and
news misses left out; a player the rule sat counts his real minutes) and the points MAE (Q x the gate's 0.353).

  python3 scripts/dk_q_missed_study.py      (expects ../br-adp-mirror and ../battle-royale-research)
"""
import sys, glob, csv, os, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
import dk_eval as E
from nba_daily import Mirror, iso
M = Mirror(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "br-adp-mirror"))
num = E.num
out = []
for f in sorted(glob.glob(os.path.join(E.DK, "20??-??-??_*.csv"))):
    rows = list(csv.DictReader(open(f)))
    if not rows or not any(r.get("actual_dk") for r in rows): continue
    d, g = rows[0]["date"], rows[0]["draft_group"]
    day = iso(d + "T00:00:00Z")
    vs = M.versions("dk_cbb_morning.json", day - dt.timedelta(days=1), day + dt.timedelta(days=2))
    start = sl = None
    for t, sha in reversed(vs):
        x = next((s for s in M.show(sha, "dk_cbb_morning.json").get("slates", []) if str(s["draft_group_id"]) == g), None)
        if x and start is None: start = iso(x["start"])
        if x and start and t < start: sl = x; break
    P = (sl or {}).get("players") or {}
    teamlast = {}
    for k, p in P.items():
        l5 = p.get("last5") or []
        if l5 and isinstance(l5[-1], list): teamlast[p["team"]] = max(teamlast.get(p["team"], ""), l5[-1][0])
    for r in rows:
        if r.get("status") != "Questionable": continue
        p = P.get(r["dk_id"]) or {}
        l5 = p.get("last5") or []
        mine = l5[-1][0] if l5 and isinstance(l5[-1], list) else None
        tl = teamlast.get(r["team"])
        # how many of the team's recent game dates he missed
        tdates = sorted({x[0] for q in P.values() if q.get("team") == r["team"] for x in (q.get("last5") or []) if isinstance(x, list)})
        mydates = {x[0] for x in l5 if isinstance(x, list)}
        missed_run = 0
        for td in reversed(tdates):
            if td in mydates: break
            missed_run += 1
        out.append((d, g, r["name"], r["team"], num(r["min_proj"]), num(r.get("min")) or 0, num(r["fp_dk"]), num(r.get("actual_dk")) or 0, mine, tl, missed_run, bool(sl)))
for o in out: print(o)

# --- the rule's effect: a Q player who missed his team's last game(s) Out by default; his team refit to 200
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "battle-royale-research", "scripts"))
from cbb_nightly import fit_minutes
hit = {(o[0], o[1], o[2]) for o in out if o[10] >= 1}
print("\nRule hits:", sorted(hit))
for f in sorted(glob.glob(os.path.join(E.DK, "20??-??-??_*.csv"))):
    rows = list(csv.DictReader(open(f)))
    if not rows or not any(r.get("actual_dk") for r in rows): continue
    d, g = rows[0]["date"], rows[0]["draft_group"]
    if d < "2026-11-18": continue
    teams = {}
    for r in rows: teams.setdefault(r["team"], []).append(r)
    score = {t: sum(num(r.get("pts")) or 0 for r in rs) for t, rs in teams.items()}
    opp = {}
    for r in rows:
        two = (r.get("game") or "").split("@")
        if len(two) == 2: opp[r["team"]] = two[1] if r["team"] == two[0] else two[0]
    blow = {t for t in teams if t in opp and opp[t] in score and abs(score[t] - score[opp[t]]) >= 20}
    res = {}
    for name, rule in (("now", False), ("rule", True)):
        mm, pm, news = [], [], 0
        for t, rs in teams.items():
            live = [r for r in rs if r.get("status") != "Out"]
            outed = [r for r in live if rule and (d, g, r["name"]) in hit]
            keep = [r for r in live if r not in outed]
            m0 = [num(r["min_proj"]) or 0 for r in keep]
            m1 = fit_minutes(m0) if outed and m0 else m0
            for r, a, b in zip(keep, m0, m1):
                act = num(r.get("min")) or 0
                if (num(r["min_proj"]) or 0) >= 15 and not act:
                    news += 1
                elif t not in blow:
                    mm.append(abs(act - b))
                q = 0.353 if r.get("status") == "Questionable" else 1.0
                pm.append(abs((num(r.get("actual_dk")) or 0) - (num(r["fp_dk"]) or 0) * (b / a if a else 1) * q))
            for r in outed:            # projected 0 now: his real minutes and points are the miss
                act = num(r.get("min")) or 0
                if t not in blow: mm.append(act)
                pm.append(num(r.get("actual_dk")) or 0)
        res[name] = (news, sum(mm) / len(mm), sum(pm) / len(pm))
    print("%s %s: news misses %d -> %d; minutes MAE %.3f -> %.3f; points MAE (Q x0.353) %.3f -> %.3f" % (d, g, res["now"][0], res["rule"][0], res["now"][1], res["rule"][1], res["now"][2], res["rule"][2]))
