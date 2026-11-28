"""The green-core shadow (2026-11-28, the operator; logging and grading only, nothing played changes).

For every MAIN contest (scripts/dk_contest_type.py) of every saved build, what two picks would have entered, beside the
page's own pick (base, replayed) and the real entries, on the same night, graded on the real standings:
  top5cores   the page's pick from the kept lineups whose core (the 3 highest salaries) is among the 5 cores with the best
              board value of any of their lineups, the core cap lifted within them
  green_top5  the same from cores with 2+ green players at lock (the checks green flag, recomputed on the mirror's slate
              as it stood at lock), limited to the top 5 such cores
  base        the page's pick (DKSim.pick, Max ROI) from the whole kept pool, the build's caps
  entered     the lineups really entered
The machinery is middle_band_cores_2026-11-28 (cc44bc8): scripts/dk_core_shadow.js runs the page's pick on the
simulated field at lock. One row per contest and variant in analysis/cbb/dk/core_shadow.csv: the lineups (DraftKings
ids), mean finish percentile, dollars back and fees. No entry ids, no username. The nights cc44bc8 graded (through
PREREG_END) are logged as "pre-registration" context; the decision count (dk_scorecard.py, "Green-core shadow (mains)")
starts with the first main night after it.

  python3 scripts/dk_core_shadow.py --mirror ../br-adp-mirror [--sims 500]      (nightly runs it: dk_eval.py nightly)
"""
import argparse, ast, bisect, csv, glob, json, os, subprocess, sys, tempfile
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dk_eval as E          # noqa: E402
import dk_contest_type as CT  # noqa: E402

LOG = os.path.join(E.DK, "core_shadow.csv")
COLS = ["date", "draft_group", "contest_id", "contest", "size", "fee", "n", "variant", "set_size", "finish_pct", "dollars", "fees", "phase", "lineups"]
PREREG_END = "2026-11-26"       # the last night graded in cc44bc8: these are context, not the 10-slate decision count
VARIANTS = ("base", "top5cores", "green_top5", "entered")
TOP_CORES = 5
num = E.num

# The checks score and green flag (the DK page's checks: CK_W, CK_GREEN 5.2, CK_GUARD 20), as recomputed in
# analysis/cbb/dk/friday_review_2026-11-27/fr_best.py; on 9 nights it gives the same greens as the lock-time projection.
CK_W = {"obpr": 0.42, "mpg": 1.63, "ppm": 0.0, "x5": 4.45, "x2": 0.50}


def _lit(v):
    if isinstance(v, (list, dict)):
        return v
    try:
        return ast.literal_eval(v) if v not in (None, "", "None") else None
    except Exception:
        return None


def _pctl(sorted_, v):
    if v is None or not sorted_:
        return 0.5
    lo = sum(1 for x in sorted_ if x < v)
    hi = sum(1 for x in sorted_ if x <= v)
    return (lo + hi) / 2 / len(sorted_)


def greens(players):
    """{dk id} of the players the checks mark green, from a slate's players dict."""
    band = lambda s: 0 if s < 5000 else 1 if s < 7000 else 2
    rows = []
    for k, p in players.items():
        q = dict(p)
        q["id"] = k
        for f in ("salary", "min_avg", "gp", "obpr", "dk_avg", "min", "bpr_rank"):
            q[f] = num(p.get(f))
        q["last5"] = _lit(p.get("last5")) or []
        q["season_dk"] = _lit(p.get("season_dk")) or []
        rows.append(q)

    def rate(r, x):
        sal = (r["salary"] or 0) / 1000
        f = (lambda v: v >= x * sal) if x > 0 else (lambda v: v < -x * sal)
        l5 = [q[2] for q in r["last5"] if len(q) > 2 and q[2] is not None]
        sea = [v for v in r["season_dk"] if v is not None]
        rl = sum(map(f, l5)) / len(l5) if l5 else None
        rs = sum(map(f, sea)) / len(sea) if sea else None
        if rl is None and rs is None:
            return None
        return rl if rs is None else rs if rl is None else 0.5 * rl + 0.5 * rs
    get = {"obpr": lambda r: r["obpr"], "mpg": lambda r: r["min_avg"],
           "ppm": lambda r: r["dk_avg"] / r["min_avg"] if r["min_avg"] and r["dk_avg"] is not None else None,
           "x5": lambda r: rate(r, 5), "x2": lambda r: rate(r, -2)}
    rot = [r for r in rows if (r["min_avg"] or 0) >= 15 and (r["gp"] or 0) >= 3]
    pool = {k: sorted(v for v in map(g, rot) if v is not None) for k, g in get.items()}
    bpool = {k: [sorted(v for v in (g(r) for r in rot if band(r["salary"] or 0) == b) if v is not None) for b in range(3)] for k, g in get.items()}
    out = set()
    for r in rows:
        sc = {}
        for k, g in get.items():
            v = g(r)
            sc[k] = 0.5 if v is None else 0.75 * _pctl(pool[k], v) + 0.25 * _pctl(bpool[k][band(r["salary"] or 0)], v)
        if (r["bpr_rank"] or 99) <= 2:
            sc["obpr"] = max(sc["obpr"], 0.7)
        sc["x2"] = 1 - sc["x2"]
        s = sum(CK_W[k] * sc[k] for k in CK_W)
        if s >= 5.2 and (r["min_avg"] or 0) >= 20 and (r["min"] or 0) >= 20 and (r.get("status") or "") not in ("Out", "Questionable", "Doubtful") \
                and (r["gp"] or 0) > 0:
            out.add(r["id"])
    return out


def core_sets(B, sal, green):
    """{variant: [kept-pool positions]} for top5cores and green_top5, and the kept pool's size; None without board values."""
    kept = B.get("final") or list(range(len(B["pool"])))
    vals = ((B.get("cut_state") or {}).get("board") or {}).get("values")
    if not vals or len(vals) != len(kept):
        return None
    val = [v[0] if isinstance(v, list) else v for v in vals]
    core = [tuple(sorted(sorted((str(i) for i in B["pool"][k]), key=lambda i: -sal.get(i, 0))[:3])) for k in kept]
    best = defaultdict(lambda: -1e18)
    for k, c in enumerate(core):
        best[c] = max(best[c], val[k])
    top = set(sorted(best, key=lambda c: -best[c])[:TOP_CORES])
    gcores = [c for c in best if sum(1 for i in c if i in green) >= 2]
    gtop = set(sorted(gcores, key=lambda c: -best[c])[:TOP_CORES])
    return {"base": list(range(len(kept))), "top5cores": [k for k, c in enumerate(core) if c in top],
            "green_top5": [k for k, c in enumerate(core) if c in gtop]}


def night_for(mirror, B):
    """(slate, start, the night file for the sim) for a build, or (None, None, why)."""
    g = str(B.get("draft_group"))
    slate = start = None
    for cid in (B.get("portfolios") or {}):
        _, slate, start = E.slate_for(mirror, cid)
        if slate and str(slate["draft_group_id"]) == g:
            break
        slate = None
    if not slate:
        return None, None, "no night record yet"
    fd = E.at_lock(mirror, "dk_cbb_field.json", start, g)
    F = ((fd or {}).get("slates") or {}).get(g)
    if not F or not F.get("field"):
        return None, None, "no simulated field saved before lock"
    return slate, start, {"slate": slate, "field": {"field": F["field"], "own": F.get("own") or {}}, "z": fd.get("z")}


def grade_lineups(Ls, pts, entries, table):
    fdesc = sorted((e["points"] for e in entries), reverse=True)
    n = len(fdesc)
    pct, dollars = [], 0.0
    for L in Ls:
        v = sum(pts.get(str(i), 0.0) for i in L)
        pl = E.placed(v, fdesc)
        pct.append(100.0 * (n - (pl - 1)) / n)
        dollars += table.get(pl, 0)
    return sum(pct) / len(pct), dollars


def run(mirror, sims=500, log=LOG):
    done = {(r["date"], r["draft_group"], r["contest_id"]) for r in E.read(log)}
    new = []
    for bf in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
        B = json.load(open(bf))
        day, g = B.get("day"), str(B.get("draft_group"))
        rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (day, g)))
        if not rec or not any(num(r.get("actual_dk")) is not None for r in rec):
            print("  core shadow %s_%s: not graded yet" % (day, g))
            continue
        slate, start, night = night_for(mirror, B)
        if not slate:
            print("  core shadow %s_%s: %s" % (day, g, night))
            continue
        cs = {str(c["id"]): c for c in slate.get("contests") or []}
        mains = [cid for cid, ks in (B.get("portfolios") or {}).items() if ks and cid in cs
                 and CT.contest_type(cs[cid].get("name"), num(cs[cid].get("size")) or 0) == "main"
                 and (day, g, cid) not in done and os.path.exists(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))]
        if not mains:
            continue
        sal = {r["dk_id"]: num(r.get("salary")) or 0 for r in rec}
        lock = E.at_lock(mirror, "dk_cbb_morning.json", start)
        ls = next((x for x in (lock or {}).get("slates", []) if str(x["draft_group_id"]) == g), None)
        green = greens(ls["players"]) if ls else set()
        sets = core_sets(B, sal, green)
        if not sets:
            print("  core shadow %s_%s: no board values in the build (save it after the cut)" % (day, g))
            continue
        variants = [{"name": "base", "set": sets["base"], "maxCore": None}, {"name": "top5cores", "set": sets["top5cores"], "maxCore": 100},
                    {"name": "green_top5", "set": sets["green_top5"], "maxCore": 100}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump(night, t)
            nf = t.name
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump({"sims": sims, "variants": variants, "contests": mains}, t)
            pf = t.name
        r = subprocess.run(["node", os.path.join(os.path.dirname(os.path.abspath(__file__)), "dk_core_shadow.js"), nf, bf, pf], capture_output=True, text=True)
        os.unlink(nf)
        os.unlink(pf)
        if r.returncode:
            print("  core shadow %s_%s: %s" % (day, g, r.stderr.strip()[-300:]))
            continue
        o = json.loads(r.stdout)
        pts = {x["dk_id"]: num(x.get("actual_dk")) or 0.0 for x in rec}
        phase = "pre-registration" if day <= PREREG_END else "counted"
        for c in o["contests"]:
            cid = c["id"]
            entries, _ = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
            table = E.pay_table(cs[cid].get("payouts"))
            fee = num(cs[cid].get("entry_fee")) or 0
            picks = dict(c["sets"])
            picks["entered"] = [B["pool"][k] for k in B["portfolios"][cid]]
            for v in VARIANTS:
                Ls = picks.get(v)
                if not Ls:
                    new.append({"date": day, "draft_group": g, "contest_id": cid, "contest": c["name"], "size": c["size"], "fee": fee, "n": c["n"],
                                "variant": v, "set_size": len(sets.get(v, [])), "finish_pct": "", "dollars": "", "fees": round(fee * c["n"], 2),
                                "phase": phase, "lineups": ""})
                    continue
                p, d = grade_lineups(Ls, pts, entries, table)
                new.append({"date": day, "draft_group": g, "contest_id": cid, "contest": c["name"], "size": c["size"], "fee": fee, "n": c["n"],
                            "variant": v, "set_size": len(sets[v]) if v in sets else "", "finish_pct": round(p, 2), "dollars": round(d, 2),
                            "fees": round(fee * len(Ls), 2), "phase": phase, "lineups": "|".join(" ".join(str(i) for i in L) for L in Ls)})
        print("  core shadow %s_%s: %d main contest%s logged (%s); greens at lock %d, green-core lineups %d, top-5-core lineups %d" % (
            day, g, len(o["contests"]), "" if len(o["contests"]) == 1 else "s", phase, len(green), len(sets["green_top5"]), len(sets["top5cores"])))
    if new:
        exists = os.path.exists(log)
        with open(log, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
            if not exists:
                w.writeheader()
            w.writerows(new)
    print("core shadow: %d rows added to %s" % (len(new), log))
    return new


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True)
    ap.add_argument("--sims", type=int, default=500)
    a = ap.parse_args(argv)
    run(E.Mirror(a.mirror), a.sims)


if __name__ == "__main__":
    main()
