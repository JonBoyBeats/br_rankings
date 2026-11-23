"""Bank noise backtest (2026-11-19; see scripts/dk_bank_noise_study.js for the steps).

  extract --mirror DIR --out OUT   each graded night's main contest's slate and simulated field as they stood at lock
  score --dir OUT                  each bank (banks_*.json, rep_*.json) scored on real points: its average projection
                                   and summed projected ownership, and the share reaching the contest's real top-10%
                                   line (the points at rank ceil(10% of entries)) and cash line (the last paid rank),
                                   beside the real field's (its entries matched to DK ids by name)
"""
import argparse
import csv
import datetime as dt
import glob
import json
import math
import os
import statistics as St
import sys

sys.path.insert(0, os.path.dirname(__file__))
import dk_eval as E                        # noqa: E402
from nba_daily import Mirror, iso          # noqa: E402

# (file key, date, draft group, contest): the key tells two slates of one date apart (2026-11-20: 11-19 early and main)
NIGHTS = [("2026-11-16", "2026-11-16", "156660", "197791872"), ("2026-11-17", "2026-11-17", "156663", "197921824"), ("2026-11-18", "2026-11-18", "157033", "197938363"),
          ("2026-11-19e", "2026-11-19", "157138", "197974021"), ("2026-11-19", "2026-11-19", "157139", "197974030"),
          # the 11-23 lock review: 11-20 early and main, 11-21 and 11-22 (each slate's largest contest with standings)
          ("2026-11-20e", "2026-11-20", "157013", "197996182"), ("2026-11-20", "2026-11-20", "157015", "197996199"),
          ("2026-11-21", "2026-11-21", "157017", "198025084"), ("2026-11-22", "2026-11-22", "157019", "198036489")]


def extract(a):
    M = Mirror(a.mirror)
    os.makedirs(a.out, exist_ok=True)

    def last_before(file, start, g, listy):
        for _, sha in reversed(M.versions(file, start - dt.timedelta(days=2), start)):
            d = M.show(sha, file)
            sl = d.get("slates") or ([] if listy else {})
            x = next((x for x in sl if str(x["draft_group_id"]) == g), None) if listy else sl.get(g)
            if x and (x.get("players") or x.get("field")):
                return d, x
        return None, None
    for key, date, g, cid in NIGHTS:
        start = None
        for _, sha in reversed(M.versions("dk_cbb_morning.json", iso(date + "T00:00:00Z") - dt.timedelta(days=1), iso(date + "T00:00:00Z") + dt.timedelta(days=2))):
            s = next((x for x in M.show(sha, "dk_cbb_morning.json").get("slates", []) if str(x["draft_group_id"]) == g), None)
            if s:
                start = iso(s["start"])
                break
        _, s = last_before("dk_cbb_morning.json", start, g, True)
        f, F = last_before("dk_cbb_field.json", start, g, False)
        c = next((c for c in s.get("contests", []) if str(c["id"]) == cid), None)
        json.dump({"date": date, "g": g, "cid": cid, "slate": s, "field": F, "z": f["z"], "contest": c}, open(os.path.join(a.out, key + ".json"), "w"))
        print(date, g, len(s["players"]), "players,", len(F["field"]), "field lineups,", c["name"])


def score(a):
    print("%-10s %-22s %5s %6s %6s %7s %6s" % ("night", "side", "n", "proj", "own", "top10%", "cash%"))
    for key, date, g, cid in NIGHTS:
        if not os.path.exists(os.path.join(a.dir, key + ".json")):
            continue
        N = json.load(open(os.path.join(a.dir, key + ".json")))
        P = {r["dk_id"]: r for r in csv.DictReader(open(os.path.join(E.DK, "%s_%s.csv" % (date, g))))}
        act = {k: float(r["actual_dk"] or 0) for k, r in P.items()}
        own = N["field"]["own"]
        ents, _ = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
        pts = sorted([e["points"] for e in ents], reverse=True)
        t10, cash = pts[math.ceil(0.1 * len(pts)) - 1], pts[min(max(E.pay_table(N["contest"]["payouts"])), len(pts)) - 1]
        names = {}
        for k, r in N["slate"]["players"].items():
            names.setdefault(r["name"], []).append(k)
        byname = {nm: v[0] for nm, v in names.items() if len(v) == 1}
        real = [(ids, e["points"]) for e in ents for ids in [[byname.get(x) for x in E.lineup_names(e["lineup"])]] if len(ids) == 8 and all(ids)]
        sides = []
        for f in sorted(glob.glob(os.path.join(a.dir, "*_%s.json" % key))):
            B = json.load(open(f))
            kind = "ideas" if os.path.basename(f).startswith("rep_") else "no rules"
            sides += [("%s s=%s" % (kind, s), L, None, B["proj"]) for s, L in B["banks"].items()]
        proj = sides[0][3] if sides else {}
        for label, L, sc, pj in [("real field", [x[0] for x in real], [x[1] for x in real], proj)] + sides:
            sc = sc or [sum(act.get(x, 0) for x in ids) for ids in L]
            print("%-11s %-22s %5d %6.1f %5.0f%% %6.1f%% %5.1f%%" % (
                key, label, len(L), St.mean(sum(pj.get(x, 0) for x in i) for i in L), St.mean(sum(own.get(x, 0) for x in i) for i in L),
                100 * St.mean(x >= t10 for x in sc), 100 * St.mean(x >= cash for x in sc)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("extract")
    x.add_argument("--mirror", required=True)
    x.add_argument("--out", required=True)
    y = sub.add_parser("score")
    y.add_argument("--dir", required=True)
    a = ap.parse_args()
    {"extract": extract, "score": score}[a.cmd](a)
