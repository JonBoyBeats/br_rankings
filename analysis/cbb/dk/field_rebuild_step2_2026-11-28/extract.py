"""Step 2 inputs: per graded slate with a sim field saved at lock, the lock-time slate, the saved field (PREVIOUS), z,
the shadow's gate, and every graded contest's lobby record, real lineups (ours out), our entries and eval.csv lines.
python3 analysis/cbb/dk/field_rebuild_step2_2026-11-28/extract.py --mirror ../br-adp-mirror --data <scratch dir>"""
import argparse, csv, json, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts")
import dk_eval as E

ap = argparse.ArgumentParser(); ap.add_argument("--mirror"); ap.add_argument("--data"); a = ap.parse_args()
os.makedirs(a.data, exist_ok=True)
mirror = E.Mirror(a.mirror)
ctype = {r["contest_id"]: r["contest_type"] for r in csv.DictReader(open(os.path.join(E.DK, "field_lineups.csv")))}
ev = defaultdict(dict)
for r in E.read(E.EVAL):
    ev[(r["date"], str(r["draft_group"]))][r["contest_id"]] = r
for (date, g), contests in sorted(ev.items()):
    slate = None
    for _, sha in reversed(mirror.versions("dk_cbb_morning.json", E.iso(date + "T00:00:00Z") - E.dt.timedelta(days=1), E.iso(date + "T00:00:00Z") + E.dt.timedelta(days=2))):
        slate = next((x for x in mirror.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
        if slate: break
    if not slate: continue
    start = E.iso(slate["start"])
    fd = E.at_lock(mirror, "dk_cbb_field.json", start, g)
    F = ((fd or {}).get("slates") or {}).get(g) or {}
    if not F.get("field"):
        print("skip", date, g, "no sim field at lock"); continue
    sh = E.at_lock(mirror, "dk_cbb_shadow.json", start, g) or {}
    sh_c = (((sh.get("slates") or {}).get(g) or {}).get("contest") or {}).get("id")
    info = slate["players"]
    names = defaultdict(list)
    for k, r in info.items(): names[r["name"]].append(k)
    byname = {nm: v[0] for nm, v in names.items() if len(v) == 1}
    out = {"date": date, "g": g, "start": slate["start"], "players": info, "prev_field": F["field"], "prev_own": F.get("own"),
           "prev_params": F.get("params"), "z": fd.get("z"), "gate": sh.get("gate"), "shadow_contest": str(sh_c or ""), "contests": []}
    for cid, er in sorted(contests.items()):
        path = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(path): continue
        c = E.contest_info(slate, cid) or {}
        entries, _ = E.standings(path)
        L, U, total = E.real_field(path, byname)
        mine = []
        pay = E.pay_table(c.get("payouts"))
        for e in entries:
            if e["name"].lower().startswith(E.USER):
                ids = [byname.get(nm) for nm in E.lineup_names(e.get("lineup") or "")]
                if len(ids) == 8 and all(ids):
                    mine.append({"ids": ids, "rank": e["rank"], "points": e["points"], "won": pay.get(e["rank"], 0)})
        out["contests"].append({"id": cid, "name": er["contest"], "type": ctype.get(cid) or E.contest_type(c), "entries": int(float(er["entries"])),
                                "size": c.get("size"), "fee": c.get("entry_fee"), "payouts": c.get("payouts"), "max_per_user": c.get("max_per_user"),
                                "field_cash": E.num(er["field_cash"]), "field_top10": E.num(er["field_top10"]), "field_avg": E.num(er["field_avg"]),
                                "sim_cash_logged": E.num(er.get("sim_cash")) if any(E.num(x.get("sim_cash")) is not None for x in [er]) else None,
                                "real": [list(x) for x, u in zip(L, U) if u != E.USER], "mine": mine})
    # eval.csv has one row per (contest, who); the logged sim cash is on the shadow contest's rule-set rows
    for c in out["contests"]:
        rows = [r for r in E.read(E.EVAL) if r["contest_id"] == c["id"] and E.num(r.get("sim_cash")) is not None]
        c["sim_cash_logged"] = E.num(rows[0]["sim_cash"]) if rows else None
        c["sim_top10_logged"] = E.num(rows[0]["sim_top10"]) if rows else None
    json.dump(out, open(os.path.join(a.data, "%s_%s.json" % (date, g)), "w"))
    print(date, g, "contests", len(out["contests"]), "shadow", sh_c, "mine", sum(len(c["mine"]) for c in out["contests"]))
