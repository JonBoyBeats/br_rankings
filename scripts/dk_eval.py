"""DraftKings CBB: grading the sim and the rule sets against real contests, and the projection gate.

The owner downloads each contest's full standings from DraftKings after it settles and drops it, as downloaded, in
analysis/cbb/dk/standings/ (contest-standings-<contest id>.csv; never edited). With last night's record
(analysis/cbb/dk/<date>_<draft group>.csv, scripts/cbb_daily.py) and the shadow portfolios saved before lock (the
mirror's dk_cbb_shadow.json, scripts/dk_shadow.js):

  nightly   per standings file not graded yet, rows in analysis/cbb/dk/eval.csv: each of the five frozen rule sets'
            shadow portfolio, and the owner's own entries (EntryName jonboyjackson), placed among the contest's real
            entries: share of lineups in the top 10%, share that cashed, dollars back on fees. Then the field's cut
            lines (winning score, top 10%, last paid place) against the sim's prediction (when the shadow was built
            for that contest), and each drafted player's projected ownership against his real %Drafted
            (analysis/cbb/dk/own_eval.csv).
  gate      analysis/cbb/dk/gate.json: by salary band, whether DraftKings' season average has beaten ours over the
            graded nights (lower mean error on everyone not tagged Out, a player who sat scoring 0, with at least
            GATE_NIGHTS nights and GATE_N player-nights, and the better of the two on GATE_SHARE of the nights). Where
            it has, the gate opens with w, the least-squares weight on ours in w x ours + (1 - w) x DK average; the DK
            page and the shadow portfolios then use that blend there (dk_sim.js gatedProj).
  readout   the monthly readout, not nightly: each rule set against "No extra rules" slate by slate (slates won
            and the paired gap, on the top-10% rate first, then cash; dollars only as the long-run check), the
            owner's entries against the field's 10%, ownership by band, the sim's cut lines, the correlation check
            (real teammate and opponent correlation of misses, which the sim takes as 0, and the spread of game
            totals against the sim's), whether real scores land where the sim's draws put them, and where the
            30-slate decision stands: does any rule set, or the owner's entries, beat the field's top-10% rate?

  python3 scripts/dk_eval.py nightly --mirror ../br-adp-mirror
  python3 scripts/dk_eval.py gate
  python3 scripts/dk_eval.py readout
"""
import argparse
import csv
import datetime as dt
import glob
import json
import math
import os
import re
import statistics as S
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from nba_daily import Mirror, iso  # noqa: E402

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
STANDINGS = os.path.join(DK, "standings")
EVAL, OWN_EVAL, GATE = os.path.join(DK, "eval.csv"), os.path.join(DK, "own_eval.csv"), os.path.join(DK, "gate.json")
USER = "jonboyjackson"
EVAL_COLS = ["date", "draft_group", "contest_id", "contest", "entries", "fee", "who", "lineups", "top10", "cash", "dollars_back",
             "fees", "field_win", "field_top10", "field_cash", "sim_win", "sim_top10", "sim_cash"]
OWN_COLS = ["date", "draft_group", "contest_id", "dk_id", "name", "salary", "own_proj", "own_actual"]
BANDS = [(6000, 99999), (4000, 5999), (0, 3999)]
GATE_NIGHTS, GATE_N, GATE_SHARE = 5, 100, 0.6
OWN_BANDS = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 35), (35, 101)]
DECISION_SLATES = 30
SIM_Z_SD = 1.266          # the spread of the sim's draws, in expected misses (cbb_form_study.py SIM_Z)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def read(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def standings(path):
    """(entries [{rank, name, points}], {player name: (%drafted, fpts)}) from a DraftKings standings CSV."""
    entries, players = [], {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("EntryId") and num(r.get("Points")) is not None:
                entries.append({"rank": int(num(r["Rank"])), "name": r.get("EntryName") or "", "points": num(r["Points"])})
            if r.get("Player"):
                players[r["Player"].strip()] = (num(str(r.get("%Drafted", "")).rstrip("%")), num(r.get("FPTS")))
    return entries, players


def at_lock(mirror, file, start):
    v = mirror.versions(file, start - dt.timedelta(days=2), start)
    return mirror.show(v[-1][1], file) if v else None


def placed(points, field_desc):
    """Place among the field's scores (sorted high to low): 1 + entries scoring more."""
    lo, hi = 0, len(field_desc)
    while lo < hi:
        mid = (lo + hi) // 2
        if field_desc[mid] > points:
            lo = mid + 1
        else:
            hi = mid
    return lo + 1


def pay_table(payouts):
    t = {}
    for a, b, v in payouts or []:
        for i in range(int(a), int(b) + 1):
            t[i] = v
    return t


def nightly(a):
    mirror = Mirror(a.mirror)
    done = {(r["contest_id"]) for r in read(EVAL)}
    out, own_out = [], []
    for path in sorted(glob.glob(os.path.join(STANDINGS, "*.csv"))):
        m = re.search(r"(\d{6,})", os.path.basename(path))
        if not m or m.group(1) in done:
            continue
        cid = m.group(1)
        entries, players = standings(path)
        if not entries:
            print("  %s: no entries read" % os.path.basename(path))
            continue
        # which slate: the record whose contests list this one (the mirror's DraftKings file as it stood at lock)
        rec, slate, start = None, None, None
        for f in sorted(glob.glob(os.path.join(DK, "????-??-??_*.csv"))):
            rows = read(f)
            if not rows:
                continue
            g = rows[0]["draft_group"]
            vs = mirror.versions("dk_cbb_morning.json", iso(rows[0]["date"] + "T00:00:00Z") - dt.timedelta(days=1),
                                 iso(rows[0]["date"] + "T00:00:00Z") + dt.timedelta(days=2))
            for t, sha in reversed(vs):
                doc = mirror.show(sha, "dk_cbb_morning.json")
                s = next((x for x in doc.get("slates", []) if str(x["draft_group_id"]) == g), None)
                if s and any(str(c["id"]) == cid for c in s.get("contests", [])):
                    rec, slate, start = rows, s, iso(s["start"])
                    break
            if rec:
                break
        if not rec:
            print("  %s: no graded DraftKings slate lists contest %s yet" % (os.path.basename(path), cid))
            continue
        contest = next(c for c in slate["contests"] if str(c["id"]) == cid)
        pay, fee, n = pay_table(contest.get("payouts")), contest.get("entry_fee") or 0, len(entries)
        paid = max(pay) if pay else 0
        field = sorted((e["points"] for e in entries), reverse=True)
        top10 = math.ceil(0.1 * n)
        cut = {"win": field[0], "top10": field[top10 - 1], "cash": field[paid - 1] if paid and paid <= n else None}
        # every drafted player's DraftKings points: the standings' FPTS, else the record's
        by_name = {r["name"]: r for r in rec}
        pts = {r["dk_id"]: num(r["actual_dk"]) for r in rec}
        for r in rec:
            if r["name"] in players and players[r["name"]][1] is not None:
                pts[r["dk_id"]] = players[r["name"]][1]
        shadow = at_lock(mirror, "dk_cbb_shadow.json", start) or {}
        sh = (shadow.get("slates") or {}).get(str(slate["draft_group_id"]))
        base = {"date": rec[0]["date"], "draft_group": slate["draft_group_id"], "contest_id": cid, "contest": contest["name"],
                "entries": n, "fee": fee, "field_win": cut["win"], "field_top10": cut["top10"], "field_cash": cut["cash"]}
        if sh:
            same = str(sh["contest"]["id"]) == cid
            for key, rs in sh["rulesets"].items():
                L = rs.get("lineups") or []
                if not L:
                    continue
                scores = [sum(pts.get(i) or 0 for i in l["ids"]) for l in L]
                places = [placed(s, field) for s in scores]
                out.append(dict(base, who=key, lineups=len(L), top10=sum(p <= top10 for p in places) / len(L),
                                cash=sum(p <= paid for p in places) / len(L), dollars_back=sum(pay.get(p, 0) for p in places),
                                fees=fee * len(L), sim_win=rs["cut"]["win"] if same else "", sim_top10=rs["cut"]["top10"] if same else "",
                                sim_cash=rs["cut"]["cash"] if same else ""))
        mine = [e for e in entries if e["name"].lower().startswith(USER)]
        if mine:
            out.append(dict(base, who="mine", lineups=len(mine), top10=sum(e["rank"] <= top10 for e in mine) / len(mine),
                            cash=sum(e["rank"] <= paid for e in mine) / len(mine), dollars_back=sum(pay.get(e["rank"], 0) for e in mine),
                            fees=fee * len(mine), sim_win="", sim_top10="", sim_cash=""))
        for name, (pct, _) in players.items():
            r = by_name.get(name)
            if r and pct is not None:
                own_out.append({"date": r["date"], "draft_group": r["draft_group"], "contest_id": cid, "dk_id": r["dk_id"], "name": name,
                                "salary": r["salary"], "own_proj": r["own"], "own_actual": pct})
        print("  graded %s (%s, %d entries): shadow %s, your entries %d" % (contest["name"], rec[0]["date"], n, "yes" if sh else "none saved", len(mine)))
    for path, cols, rows in ((EVAL, EVAL_COLS, out), (OWN_EVAL, OWN_COLS, own_out)):
        if rows:
            new = not os.path.exists(path)
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=cols)
                if new:
                    w.writeheader()
                w.writerows(rows)
    if not out:
        print("  DraftKings standings: nothing new to grade")


def records():
    return [r for f in sorted(glob.glob(os.path.join(DK, "????-??-??_*.csv"))) for r in read(f)]


def band_name(b):
    return "$%s+" % format(b["lo"], ",") if b["hi"] > 9999 else "$%s-%s" % (format(b["lo"], ","), format(b["hi"], ","))


def gate(a):
    rows = [r for r in records() if r["status"] != "Out" and num(r["fp_dk"]) is not None and num(r["actual_dk"]) is not None]
    nights = sorted({r["date"] for r in rows})
    bands = []
    for lo, hi in BANDS:
        v = [r for r in rows if lo <= num(r["salary"]) <= hi and num(r["dk_avg"])]
        b = {"lo": lo, "hi": hi, "n": len(v), "nights": len({r["date"] for r in v}), "open": False, "w": 1.0}
        if v:
            b["mae_ours"] = round(S.mean(abs(num(r["fp_dk"]) - num(r["actual_dk"])) for r in v), 3)
            b["mae_avg"] = round(S.mean(abs(num(r["dk_avg"]) - num(r["actual_dk"])) for r in v), 3)
            won = 0
            for d in {r["date"] for r in v}:
                vd = [r for r in v if r["date"] == d]
                won += S.mean(abs(num(r["dk_avg"]) - num(r["actual_dk"])) for r in vd) < S.mean(abs(num(r["fp_dk"]) - num(r["actual_dk"])) for r in vd)
            b["nights_avg_won"] = won
            if b["nights"] >= GATE_NIGHTS and b["n"] >= GATE_N and b["mae_avg"] < b["mae_ours"] and won >= GATE_SHARE * b["nights"]:
                # least squares on actual - avg = w x (ours - avg)
                x = [num(r["fp_dk"]) - num(r["dk_avg"]) for r in v]
                y = [num(r["actual_dk"]) - num(r["dk_avg"]) for r in v]
                sxx = sum(xi * xi for xi in x)
                b.update(open=True, w=round(max(0.0, min(1.0, sum(xi * yi for xi, yi in zip(x, y)) / sxx if sxx else 1.0)), 3))
        bands.append(b)
    doc = {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "nights": len(nights), "bands": bands,
           "rule": "open where DraftKings' average beat ours: %d+ nights, %d+ player-nights, lower mean error, better on %d%%+ of nights"
                   % (GATE_NIGHTS, GATE_N, 100 * GATE_SHARE)}
    with open(GATE, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print("Projection gate (%d graded nights): %s" % (len(nights), "; ".join(
        "%s %s (n=%d, ours %s vs DK avg %s)" % (band_name(b), "OPEN w=%.2f" % b["w"] if b["open"] else "closed",
                                                b["n"], b.get("mae_ours", "-"), b.get("mae_avg", "-")) for b in bands)))


def readout(a):
    ev = read(EVAL)
    print("DraftKings CBB readout, %s" % dt.date.today().isoformat())
    slates = sorted({r["draft_group"] for r in ev})
    print("\n1. Rule sets and your entries against the field (%d graded slates of the %d the decision waits for)" % (len(slates), DECISION_SLATES))
    if not ev:
        print("   nothing graded yet: the standings files start it")
    else:
        # one value per slate and who: lineups-weighted across that slate's graded contests
        per = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0.0]))
        for r in ev:
            t = per[r["draft_group"]][r["who"]]
            n = num(r["lineups"])
            t[0] += num(r["top10"]) * n; t[1] += num(r["cash"]) * n; t[2] += n; t[3] += num(r["dollars_back"]); t[4] += num(r["fees"])
        who_all = sorted({w for s in per.values() for w in s}, key=lambda w: (w == "mine", w != "none", w))
        print("   %-8s %7s %8s %8s %12s %22s %22s" % ("", "slates", "top 10%", "cash", "$ back/fees", "top10 vs none: won, gap", "cash vs none: won, gap"))
        for w in who_all:
            sl = [s for s in per if w in per[s]]
            t10 = [per[s][w][0] / per[s][w][2] for s in sl]
            ca = [per[s][w][1] / per[s][w][2] for s in sl]
            back, fees = sum(per[s][w][3] for s in sl), sum(per[s][w][4] for s in sl)
            pair = ""
            pair_c = ""
            if w != "none":
                both = [s for s in sl if "none" in per[s]]
                g10 = [per[s][w][0] / per[s][w][2] - per[s]["none"][0] / per[s]["none"][2] for s in both]
                gc = [per[s][w][1] / per[s][w][2] - per[s]["none"][1] / per[s]["none"][2] for s in both]
                if both:
                    pair = "%d of %d, %+.1f pts" % (sum(g > 0 for g in g10), sum(g != 0 for g in g10), 100 * S.mean(g10))
                    pair_c = "%d of %d, %+.1f pts" % (sum(g > 0 for g in gc), sum(g != 0 for g in gc), 100 * S.mean(gc))
            print("   %-8s %7d %7.1f%% %7.1f%% %12s %22s %22s" % (w, len(sl), 100 * S.mean(t10), 100 * S.mean(ca),
                  "%.2f / %.2f" % (back, fees), pair, pair_c))
        print("   The field's top-10% rate is 10% by definition; its cash rate is the contest's paid places over entries."
              " 'won': slates where the rule set's rate beat No extra rules' (ties left out), 'gap': the mean of the per-slate differences.")
        if len(slates) >= DECISION_SLATES:
            beat = [w for w in who_all if S.mean(per[s][w][0] / per[s][w][2] for s in per if w in per[s]) > 0.10]
            print("   DECISION (%d slates): beating the field's 10%% top-10 rate: %s" % (len(slates), ", ".join(beat) or "none: cut back"))
        cuts = list({r["contest_id"]: r for r in ev if r["sim_top10"] not in ("", None)}.values())   # once a contest
        if cuts:
            for k in ("win", "top10", "cash"):
                d = [num(r["field_" + k]) - num(r["sim_" + k]) for r in cuts if num(r["field_" + k]) is not None and num(r["sim_" + k]) is not None]
                if d:
                    print("   cut line %-6s real - sim: %+.1f points on average (%d contests the shadow was built for)" % (k, S.mean(d), len(d)))

    own = read(OWN_EVAL)
    print("\n2. Projected ownership against real %%Drafted, by projected band (%d player-contests)" % len(own))
    for lo, hi in OWN_BANDS:
        v = [r for r in own if num(r["own_proj"]) is not None and lo <= num(r["own_proj"]) < hi]
        if v:
            print("   proj %2d-%-3d%% n=%-4d projected %5.1f%%  real %5.1f%%  mean miss %4.1f pts" % (
                lo, hi if hi < 101 else 100, len(v), S.mean(num(r["own_proj"]) for r in v), S.mean(num(r["own_actual"]) for r in v),
                S.mean(abs(num(r["own_proj"]) - num(r["own_actual"])) for r in v)))

    rec = [r for r in records() if r["status"] != "Out" and num(r["fp_dk"]) and num(r["miss_dk"])]
    print("\n3. The sim's players against reality (%d player-nights, %d nights)" % (len(rec), len({r["date"] for r in rec})))
    played = [r for r in rec if num(r["min"])]
    z = [(num(r["actual_dk"]) - num(r["fp_dk"])) / num(r["miss_dk"]) for r in played]
    if z:
        try:
            zs = json.load(open(a.sim_z))["z"] if a.sim_z else None
        except Exception:
            zs = None
        if zs:
            dec = [0] * 10
            for x in z:
                dec[min(9, int(10 * sum(q <= x for q in zs) / len(zs)))] += 1
            print("   where real scores fell in the sim's range, by tenth (10% each if the sim's spread is right): " +
                  " ".join("%.0f" % (100 * d / len(z)) for d in dec))
        print("   misses in expected misses: sd %.2f (the sim draws %.2f)" % (S.pstdev(z), SIM_Z_SD))
    # correlation of misses within a game, and the spread of game totals
    by_game = defaultdict(list)
    for r in rec:
        by_game[(r["date"], r.get("game"))].append(r)
    tm, op = [], []
    for v in by_game.values():
        v = [r for r in v if num(r["min"]) and num(r["fp_dk"]) >= 10]
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                zi = (num(v[i]["actual_dk"]) - num(v[i]["fp_dk"])) / num(v[i]["miss_dk"])
                zj = (num(v[j]["actual_dk"]) - num(v[j]["fp_dk"])) / num(v[j]["miss_dk"])
                (tm if v[i]["team"] == v[j]["team"] else op).append((zi, zj))

    def corr(p):
        if len(p) < 30:
            return None
        p = p + [(b, a2) for a2, b in p]
        xs, ys = zip(*p)
        mx, my, sx, sy = S.mean(xs), S.mean(ys), S.pstdev(xs), S.pstdev(ys)
        return sum((x - mx) * (y - my) for x, y in p) / (len(p) * sx * sy) if sx and sy else None
    ct, co = corr(tm), corr(op)
    print("   correlation of misses, players projected 10+: teammates %s (%d pairs), opponents %s (%d pairs); the sim takes both"
          " as 0 (2025-26: -0.007, -0.004)" % ("%.3f" % ct if ct is not None else "-", len(tm), "%.3f" % co if co is not None else "-", len(op)))
    real, sim = [], []
    for v in by_game.values():
        if len(v) >= 10:
            real.append(sum(num(r["actual_dk"]) for r in v) - sum(num(r["fp_dk"]) for r in v))
            sim.append(math.sqrt(sum((SIM_Z_SD * num(r["miss_dk"])) ** 2 for r in v)))
    if len(real) >= 5:
        print("   game totals (every projected player in the game): real misses spread %.1f against the sim's %.1f (n=%d games);"
              " real wider means missing in-game correlation" % (S.pstdev(real), S.mean(sim), len(real)))

    try:
        gt = json.load(open(GATE))
        print("\n4. Projection gate (%d graded nights): %s" % (gt["nights"], "; ".join(
            "%s %s" % (band_name(b), "OPEN w=%.2f" % b["w"] if b["open"] else "closed") for b in gt["bands"])))
    except Exception:
        print("\n4. Projection gate: no gate file yet")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("nightly")
    n.add_argument("--mirror", required=True)
    sub.add_parser("gate")
    r = sub.add_parser("readout")
    r.add_argument("--sim-z", dest="sim_z", help="a dk_cbb_field.json, for the sim's draw shape (default: none)")
    a = ap.parse_args()
    os.makedirs(STANDINGS, exist_ok=True)
    return {"nightly": nightly, "gate": gate, "readout": readout}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
