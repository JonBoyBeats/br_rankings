"""'Minutes is king' for cheap players (2026-11-21, the operator's question via the coordinator). Analysis only.

The alternative projection: players below a salary line get projected minutes x a flat rate (the slate's projected DK
points per minute over the players not Out: sum of projections / sum of projected minutes, so nothing after lock), or
the same by position (G / F, a G/F by his first letter). Lines: under $5,000, and the bottom third of the slate by
salary (the players not Out). Players above the line keep our projection. Also (added after the first run showed the slate's rate runs well above
what cheap players score) the flat rate of the cheap group itself (flatgrp), so the test of dropping the per-player rate
isn't only a test of raising the level. The plain variant: our per-player rate
shrunk halfway to the flat rate, i.e. 0.5 x our projection + 0.5 x minutes x flat.

  accuracy                      (a) on every slate with box scores: the cheap players' points MAE, correlation and bias
                                under each variant, the biggest misses, our cheap misses split into minutes and rate,
                                and the A2 lenses (scripts/dk_minutes_steep_study.py's, points swapped for the variant)
  score --dir DIR               (b) the rule-free banks drawn by scripts/dk_cheap_minutes_study.js (one per variant, same
                                seeds), scored on real points against the contest's real top-10% and cash lines and the
                                real field's percentile, as the punt test (scripts/dk_bank_noise_study.py) did

  python3 scripts/dk_cheap_minutes_study.py accuracy
  python3 scripts/dk_cheap_minutes_study.py score --dir DIR
"""
import argparse, csv, glob, json, math, os, statistics as S, sys

sys.path.insert(0, os.path.dirname(__file__))
import dk_minutes_steep_study as M          # noqa: E402  (the A2 lenses)

DK = os.path.join(os.path.dirname(__file__), "..", "analysis", "cbb", "dk")
num = lambda v: float(v) if v not in ("", None) else None
VARIANTS = ["cur", "flat_5k", "flatpos_5k", "flatgrp_5k", "shrink_5k", "flat_third", "flatpos_third", "flatgrp_third", "shrink_third"]
# the lineup part's nights: the punt test's (scripts/dk_bank_noise_study.py NIGHTS), the nights with standings on file
NIGHTS = [("2026-11-16", "2026-11-16", "156660", "197791872"), ("2026-11-17", "2026-11-17", "156663", "197921824"), ("2026-11-18", "2026-11-18", "157033", "197938363"),
          ("2026-11-19e", "2026-11-19", "157138", "197974021"), ("2026-11-19", "2026-11-19", "157139", "197974030")]


def alt_points(players, variant):
    """players: [{id, salary, status, min, proj, pos}] -> {id: points} under the variant (shared with the .js)."""
    if variant == "cur":
        return {p["id"]: p["proj"] for p in players}, set()
    mode, line = variant.split("_")
    live = [p for p in players if p["status"] != "Out" and (p["min"] or 0) > 0]
    flat = sum(p["proj"] for p in live) / sum(p["min"] for p in live)
    fpos = {}
    for g in ("G", "F"):
        v = [p for p in live if (p["pos"] or "?")[0] == g]
        fpos[g] = sum(p["proj"] for p in v) / sum(p["min"] for p in v) if v else flat
    if line == "5k":
        cheap = {p["id"] for p in live if p["salary"] < 5000}
    else:
        srt = sorted(live, key=lambda p: p["salary"])
        cheap = {p["id"] for p in srt[:math.ceil(len(srt) / 3)]}
    grp = [p for p in live if p["id"] in cheap]
    fgrp = sum(p["proj"] for p in grp) / sum(p["min"] for p in grp) if grp else flat
    out = {}
    for p in players:
        if p["id"] not in cheap:
            out[p["id"]] = p["proj"]; continue
        f = fpos.get((p["pos"] or "?")[0], flat) if mode == "flatpos" else fgrp if mode == "flatgrp" else flat
        out[p["id"]] = p["min"] * f if mode in ("flat", "flatpos", "flatgrp") else 0.5 * p["proj"] + 0.5 * p["min"] * f
    return out, cheap


def slates():
    return [(os.path.basename(f)[:-4], rows) for f, rows in ((f, list(csv.DictReader(open(f)))) for f in sorted(glob.glob(os.path.join(DK, "20??-??-??_*.csv"))))
            if rows and any(r.get("actual_dk") not in ("", None) for r in rows)]


def players_of(rows):
    return [{"id": r["dk_id"], "salary": num(r["salary"]), "status": r.get("status") or "", "min": num(r.get("min_proj")) or 0,
             "proj": num(r.get("fp_dk")) or 0, "pos": r.get("position") or ""} for r in rows]


def corr(a, b):
    ma, mb = S.mean(a), S.mean(b); sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else None


def accuracy(a):
    sl = slates()
    print("Slates with box scores: %d (%s). A thin sample: about ten nights." % (len(sl), ", ".join(n for n, _ in sl)))
    for line in ("5k", "third"):
        print("\n== Cheap players: %s ==" % ("salary under $5,000" if line == "5k" else "the bottom third of each slate by salary"))
        vs = ["cur", "flat_" + line, "flatpos_" + line, "flatgrp_" + line, "shrink_" + line]
        pooled = {v: [] for v in vs}; wins = {v: 0 for v in vs}; flats = []
        rowsby = {(n_, r["dk_id"]): r for n_, rows in sl for r in rows}
        for name, rows in sl:
            P = players_of(rows); by = {r["dk_id"]: r for r in rows}
            pts = {v: alt_points(P, v) for v in vs}
            cheap = sorted(pts[vs[1]][1])
            act = [num(by[i]["actual_dk"]) or 0 for i in cheap]
            mae = {}
            for v in vs:
                pr = [pts[v][0][i] for i in cheap]
                mae[v] = S.mean(abs(x - y) for x, y in zip(act, pr))
                pooled[v] += [(name, i, x, y) for i, x, y in zip(cheap, act, pr)]
            for v in vs[1:]:
                wins[v] += mae[v] < mae["cur"] - 1e-9
            live = [p for p in P if p["status"] != "Out" and p["min"] > 0]
            flats.append(sum(p["proj"] for p in live) / sum(p["min"] for p in live))
            print("  %-18s n %3d  MAE cur %.2f | flat %.2f | flat by pos %.2f | flat of the cheap group %.2f | shrink %.2f" % (name, len(cheap), mae["cur"], mae[vs[1]], mae[vs[2]], mae[vs[3]], mae[vs[4]]))
        print("  slates where the variant's MAE beats ours: " + ", ".join("%s %d of %d" % (v, wins[v], len(sl)) for v in vs[1:]))
        print("  pooled (%d player-games over %d slates):" % (len(pooled["cur"]), len(sl)))
        for v in vs:
            xs = [x for _, _, x, _ in pooled[v]]; ys = [y for _, _, _, y in pooled[v]]
            pl = [(x, y) for (n, i, x, y) in pooled[v] if (num(rowsby[(n, i)].get("min")) or 0) > 0]
            print("    %-14s MAE %.2f  corr %.3f  bias (actual-proj) %+.2f   played only: MAE %.2f bias %+.2f (n %d)" % (
                v, S.mean(abs(x - y) for x, y in zip(xs, ys)), corr(xs, ys), S.mean(x - y for x, y in zip(xs, ys)),
                S.mean(abs(x - y) for x, y in pl), S.mean(x - y for x, y in pl), len(pl)))
        # minutes vs rate: our misses on the cheap players who played; DNPs (all minutes) apart
        mn, rt, cr, dnp, n = 0.0, 0.0, 0.0, [], 0; ppm_act, ppm_ours = [], []
        for (nm, i, x, y) in pooled["cur"]:
            r = rowsby[(nm, i)]; ma, mp = num(r.get("min")) or 0, num(r.get("min_proj")) or 0
            if mp <= 0:
                continue
            rp = y / mp
            if ma <= 0:
                dnp.append(x - y); continue
            dm, dr = (ma - mp) * rp, ma * (x / ma - rp)
            mn += dm * dm; rt += dr * dr; cr += 2 * dm * dr; n += 1
            ppm_act.append(x / ma); ppm_ours.append(rp)
        tot = mn + rt + cr
        print("  our misses on the cheap players who played (n %d): squared error from minutes %.0f%%, from rate %.0f%%, the cross term %+.0f%%" % (
            n, 100 * mn / tot, 100 * rt / tot, 100 * cr / tot))
        print("  their real points per minute %.3f (median %.3f) vs our rate %.3f vs the slates' flat rate %.3f (mean); DNPs %d, our miss on them %.2f a player" % (
            S.mean(ppm_act), S.median(ppm_act), S.mean(ppm_ours), S.mean(flats), len(dnp), -S.mean(dnp) if dnp else 0))
        # biggest misses: ours, with the flat variant beside, and the flat variant's own worst
        rows_ = [(nm, i, x, y, dict(((n2, i2), y2) for n2, i2, _, y2 in pooled["flat_" + line])[(nm, i)]) for nm, i, x, y in pooled["cur"]]
        for title, key in (("our biggest misses", lambda t: abs(t[2] - t[3])), ("the flat variant's biggest misses", lambda t: abs(t[2] - t[4]))):
            print("  %s:" % title)
            for nm, i, x, y, z in sorted(rows_, key=key, reverse=True)[:8]:
                r = rowsby[(nm, i)]
                print("    %-18s %-24s $%5d  ours %5.1f  flat %5.1f  actual %5.1f  min %4.1f proj / %4.1f real" % (
                    nm, r["name"][:24], num(r["salary"]), y, z, x, num(r.get("min_proj")) or 0, num(r.get("min")) or 0))
    # A2 lenses: the steep study's, points swapped for the variant (minutes untouched, so its minutes lens can't move)
    print("\n== A2 lenses, every slate (points MAE all players; |shape| top-2 ours-recent; Vegas slope of team points on implied totals; 2 sd salary gaps unexplained). Minutes are untouched, so the minutes lens can't move ==")
    for v in VARIANTS[1:]:
        cnt = {"pts": 0, "shape": 0, "gaps": 0}; sums = {"b": [], "a": []}
        for name, rows in sl:
            P = players_of(rows); pts = alt_points(P, v)[0]
            M.steepen = lambda rows_, g, _p=pts, _r=rows: {r["dk_id"]: (num(r["min_proj"]), (num(r.get("fp_dk")) or 0) if g == 0 else _p[r["dk_id"]])
                                                          for r in _r if r.get("status") != "Out" and num(r.get("min_proj"))}
            b, a_ = M.lenses(rows, 0.0), M.lenses(rows, 1.0)
            cnt["pts"] += a_["pts_mae"] < b["pts_mae"] - 1e-9
            cnt["shape"] += abs(a_["shape_top2_vs_recent"] or 0) > abs(b["shape_top2_vs_recent"] or 0) + 1e-9
            cnt["gaps"] += a_["unexplained"] - b["unexplained"]
            sums["b"].append(b); sums["a"].append(a_)
        m = lambda side, k: S.mean(x[k] for x in sums[side] if x[k] is not None)
        print("  %-14s points MAE %.3f -> %.3f (better on %d of %d); |shape| %.3f -> %.3f (larger on %d); Vegas slope %.3f -> %.3f; unexplained gaps %+d in all" % (
            v, m("b", "pts_mae"), m("a", "pts_mae"), cnt["pts"], len(sl), S.mean(abs(x["shape_top2_vs_recent"] or 0) for x in sums["b"]),
            S.mean(abs(x["shape_top2_vs_recent"] or 0) for x in sums["a"]), cnt["shape"], m("b", "vegas_slope"), m("a", "vegas_slope"), cnt["gaps"]))


def score(a):
    import dk_eval as E
    res = {}
    for key, date, g, cid in NIGHTS:
        f = os.path.join(a.dir, "cheap_%s.json" % key)
        if not os.path.exists(f):
            continue
        N = json.load(open(os.path.join(a.dir, key + ".json"))); B = json.load(open(f))
        P = {r["dk_id"]: r for r in csv.DictReader(open(os.path.join(DK, "%s_%s.csv" % (date, g))))}
        act = {k: float(r["actual_dk"] or 0) for k, r in P.items()}
        own = N["field"]["own"]
        ents, _ = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
        pts = sorted([e["points"] for e in ents], reverse=True)
        t10, cash = pts[math.ceil(0.1 * len(pts)) - 1], pts[min(max(E.pay_table(N["contest"]["payouts"])), len(pts)) - 1]
        asc = sorted(pts)
        pctl = lambda x: sum(1 for p in asc if p < x) / len(asc)
        res[key] = {}
        for v in VARIANTS:
            L = B["banks"][v]; sc = [sum(act.get(x, 0) for x in ids) for ids in L]
            res[key][v] = {"n": len(L), "t10": S.mean(x >= t10 for x in sc), "cash": S.mean(x >= cash for x in sc), "pctl": S.mean(pctl(x) for x in sc),
                           "proj": S.mean(sum(B["proj"]["cur"].get(x, 0) for x in i) for i in L), "own": S.mean(sum(own.get(x, 0) for x in i) for i in L),
                           "cheap": S.mean(sum(1 for x in i if x in B["cheap"][v]) for i in L) if v != "cur" else None}
    print("Rule-free banks at bank noise 0.35, the same seeds under each projection, scored on real points (%d nights with standings: thin)." % len(res))
    print("%-11s %-14s %5s %6s %5s %7s %6s %6s %6s" % ("night", "variant", "n", "proj", "own", "top10%", "cash%", "pctl", "cheap"))
    for key, r in res.items():
        for v in VARIANTS:
            x = r[v]
            print("%-11s %-14s %5d %6.1f %4.0f%% %6.1f%% %5.1f%% %5.1f%% %6s" % (key, v, x["n"], x["proj"], x["own"], 100 * x["t10"], 100 * x["cash"], 100 * x["pctl"],
                                                                         "-" if x["cheap"] is None else "%.2f" % x["cheap"]))
    print("\nPooled (mean of the nights) and nights better than our projection:")
    for v in VARIANTS:
        m = lambda k: S.mean(res[n][v][k] for n in res)
        w = lambda k: sum(res[n][v][k] > res[n]["cur"][k] + 1e-9 for n in res)
        print("  %-14s top10 %.1f%% cash %.1f%% pctl %.1f%%   better: top10 %d, cash %d, pctl %d of %d" % (
            v, 100 * m("t10"), 100 * m("cash"), 100 * m("pctl"), w("t10"), w("cash"), w("pctl"), len(res)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("accuracy")
    y = sub.add_parser("score"); y.add_argument("--dir", required=True)
    a = ap.parse_args()
    {"accuracy": accuracy, "score": score}[a.cmd](a)
