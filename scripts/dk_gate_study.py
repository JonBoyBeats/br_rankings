"""The projection gate at the freeze (2026-11-23 lock review). The calibration blend (ours x 0.5 + DraftKings' average x
0.5 in every salary band, versions.csv cal-1, 'until the owner's choice at the freeze') against the gate closed (ours
alone: the gate's own rule, dk_eval.py gate, opens a band only where DK's average beats ours, and it beats ours in none).

  lenses              the A2 lenses on every graded slate with the page's points under each (Questionable x the factor
                      in both; minutes untouched): points MAE, shape, Vegas slope, salary gaps
  score --dir DIR     the banks drawn by scripts/dk_gate_study.js on the review's 9 nights with standings
                      (scripts/dk_bank_noise_study.py NIGHTS), scored on real points against each contest's real top-10%
                      and cash lines and the real field's percentile

  python3 scripts/dk_bank_noise_study.py extract --mirror ../br-adp-mirror --out DIR
  for n in DIR/20*.json; do node scripts/dk_gate_study.js $n 2000 DIR/gate_$(basename $n); done
  python3 scripts/dk_gate_study.py lenses
  python3 scripts/dk_gate_study.py score --dir DIR
"""
import argparse, csv, json, math, os, statistics as S, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_minutes_steep_study as M     # noqa: E402
import dk_lock_review_proj as R       # noqa: E402

num = R.num
CLOSED = dict(R.GATE, bands=[dict(b, open=False) for b in R.GATE.get("bands", [])])
PART = dict(R.GATE, bands=[dict(b, open=b["open"] if b["lo"] >= 6000 else False) for b in R.GATE.get("bands", [])])     # closed under $6k
V = [("ours", CLOSED), ("part", PART)]


def pts(r, gate):
    p, s = num(r.get("fp_dk")) or 0, num(r["salary"]) or 0
    b = next((b for b in gate.get("bands", []) if b.get("open") and b["lo"] <= s <= b["hi"]), None)
    if b and num(r.get("dk_avg")):
        p = b["w"] * p + (1 - b["w"]) * num(r["dk_avg"])
    return p * R.QF if r.get("status") == "Questionable" else p


def lenses(a):
    for name, G in V:
        print("== %s against the blend ==" % name); lenses_one(G)


def lenses_one(G):
    sl = R.slates()
    cnt = {"pts": 0, "shape": 0, "gaps": 0, "vegas": 0}; sums = {"cur": [], "ours": []}
    print("Per slate (cur = the blend, ours = the gate closed): points MAE, |shape|, Vegas slope, unexplained gaps")
    for n, rows in sl:
        P = {v: {r["dk_id"]: pts(r, g) for r in rows if r.get("status") != "Out"} for v, g in (("cur", R.GATE), ("ours", G))}
        M.steepen = lambda rows_, gg, _r=rows: {r["dk_id"]: (num(r["min_proj"]), P["cur" if gg == 0 else "ours"][r["dk_id"]]) for r in _r
                                                 if r.get("status") != "Out" and num(r.get("min_proj"))}
        b, x = M.lenses(rows, 0.0), M.lenses(rows, 1.0)
        sums["cur"].append(b); sums["ours"].append(x)
        cnt["pts"] += x["pts_mae"] < b["pts_mae"] - 1e-9
        cnt["shape"] += abs(x["shape_top2_vs_recent"] or 0) > abs(b["shape_top2_vs_recent"] or 0) + 1e-9
        cnt["gaps"] += x["unexplained"] - b["unexplained"]
        print("  %s  pts %.3f -> %.3f  |shape| %.3f -> %.3f  Vegas %s -> %s  gaps %d -> %d" % (
            n, b["pts_mae"], x["pts_mae"], abs(b["shape_top2_vs_recent"] or 0), abs(x["shape_top2_vs_recent"] or 0),
            "%.2f" % b["vegas_slope"] if b["vegas_slope"] is not None else "-", "%.2f" % x["vegas_slope"] if x["vegas_slope"] is not None else "-", b["unexplained"], x["unexplained"]))
    m = lambda side, k: S.mean(v[k] for v in sums[side] if v[k] is not None)
    print("Pooled: points MAE %.3f -> %.3f (better on %d of %d); |shape| %.3f -> %.3f (larger on %d); Vegas slope %.2f -> %.2f; unexplained gaps %+d in all" % (
        m("cur", "pts_mae"), m("ours", "pts_mae"), cnt["pts"], len(sl), S.mean(abs(v["shape_top2_vs_recent"] or 0) for v in sums["cur"]),
        S.mean(abs(v["shape_top2_vs_recent"] or 0) for v in sums["ours"]), cnt["shape"], m("cur", "vegas_slope"), m("ours", "vegas_slope"), cnt["gaps"]))


def score(a):
    import dk_eval as E
    from dk_bank_noise_study import NIGHTS
    res = {}
    for key, date, g, cid in NIGHTS:
        f = os.path.join(a.dir, "gate_%s.json" % key)
        if not os.path.exists(f):
            continue
        N = json.load(open(os.path.join(a.dir, key + ".json"))); B = json.load(open(f))
        P = {r["dk_id"]: r for r in csv.DictReader(open(os.path.join(R.DK, "%s_%s.csv" % (date, g))))}
        act = {k: float(r["actual_dk"] or 0) for k, r in P.items()}
        ents, _ = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
        pts_ = sorted([e["points"] for e in ents], reverse=True)
        t10, cash = pts_[math.ceil(0.1 * len(pts_)) - 1], pts_[min(max(E.pay_table(N["contest"]["payouts"])), len(pts_)) - 1]
        asc = sorted(pts_)
        res[key] = {}
        for v in ("cur", "ours", "part"):
            if v not in B["banks"]:
                continue
            sc = [sum(act.get(x, 0) for x in ids) for ids in B["banks"][v]]
            res[key][v] = {"n": len(sc), "t10": S.mean(x >= t10 for x in sc), "cash": S.mean(x >= cash for x in sc),
                           "pctl": S.mean(sum(1 for p in asc if p < x) / len(asc) for x in sc)}
    print("Rule-free banks at bank noise 0.35, the same seed under each gate, scored on real points (%d nights with standings: thin)." % len(res))
    print("%-11s %-5s %5s %7s %6s %6s" % ("night", "gate", "n", "top10%", "cash%", "pctl"))
    for k, r in res.items():
        for v in [x for x in ("cur", "ours", "part") if x in r]:
            x = r[v]; print("%-11s %-5s %5d %6.1f%% %5.1f%% %5.1f%%" % (k, v, x["n"], 100 * x["t10"], 100 * x["cash"], 100 * x["pctl"]))
    for v in [x for x in ("cur", "ours", "part") if all(x in res[n] for n in res)]:
        m = lambda q: S.mean(res[n][v][q] for n in res)
        w = lambda q: sum(res[n][v][q] > res[n]["cur"][q] + 1e-9 for n in res)
        l = lambda q: sum(res[n][v][q] < res[n]["cur"][q] - 1e-9 for n in res)
        print("  pooled %-5s top10 %.1f%% cash %.1f%% pctl %.1f%%   vs cur: top10 better %d / worse %d, cash %d / %d, pctl %d / %d of %d" % (
            v, 100 * m("t10"), 100 * m("cash"), 100 * m("pctl"), w("t10"), l("t10"), w("cash"), l("cash"), w("pctl"), l("pctl"), len(res)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lenses"); y = sub.add_parser("score"); y.add_argument("--dir", required=True)
    a = ap.parse_args()
    {"lenses": lenses, "score": score}[a.cmd](a)
