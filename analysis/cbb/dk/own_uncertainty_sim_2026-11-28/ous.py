"""Ownership uncertainty in the sim: the driver and the grade (2026-11-28, analysis only; HELD).

For every saved build with a lock-time slate and simulated field on the mirror and graded standings: ous.js picks each
entered contest's lineups three ways (A today's fixed field / kept pool; B the uncertain field / kept pool; C the
uncertain field / a re-cut), at the measured uncertainty sizes (sizes.json) x 1, x 0.5 and x 2. Then each set is scored
on the real standings (finish percentile and payout per lineup), beside random fills of the same size from the kept
pool (1,000 draws), per contest and by contest type, per slate with SE over slates. Calibration: each set's stated
expected payout and top-1% (under the sim that picked it, and under the other) against what it really paid and how
often it really reached the top 1%.

  python3 ous.py [--sims 500] [--scales 1,0.5,2]     (sibling checkouts: br-adp-mirror beside br_rankings)
"""
import argparse, bisect, csv, glob, json, math, os, random, re, statistics as S, subprocess, sys, tempfile, datetime as dt
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dk_eval as E
MIRROR = os.environ.get("MIRROR") or os.path.join(os.path.dirname(ROOT), "br-adp-mirror")


def nights(mirror):
    """[(build path, night dict)] as dk_flagship_compare.py builds them: the slate and the field at lock."""
    out = []
    for bf in sorted(glob.glob(os.path.join(E.DK, "builds", "dk_bank_*.json"))):
        B = json.load(open(bf)); g = str(B.get("draft_group"))
        slate = start = None
        for cid in (B.get("portfolios") or {}):
            _, slate, start = E.slate_for(mirror, cid)
            if slate and str(slate["draft_group_id"]) == g:
                break
            slate = None
        if not slate:
            continue
        fd = E.at_lock(mirror, "dk_cbb_field.json", start, g)
        Fd = ((fd or {}).get("slates") or {}).get(g)
        if not Fd or not Fd.get("field"):
            continue
        out.append((bf, {"slate": slate, "field": {"field": Fd["field"], "own": Fd.get("own") or {}}, "z": fd.get("z")}))
    return out


def ctype(name, n):
    if re.search("qualifier|satellite", name or "", re.I) or n < 100: return "qualifier/small"
    if re.search("pull up jumper", name or "", re.I) or n < 800: return "flagship"
    return "main"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=500)
    ap.add_argument("--scales", default="1,0.5,2")
    a = ap.parse_args()
    sizes = json.load(open(os.path.join(HERE, "sizes.json")))
    M = E.Mirror(MIRROR)
    res = {}
    for bf, night in nights(M):
        B = json.load(open(bf)); name = "%s_%s" % (B["day"], B["draft_group"])
        rec = os.path.join(E.DK, name + ".csv")
        if not os.path.exists(rec) or not any(E.num(r.get("actual_dk")) is not None for r in E.read(rec)):
            print("  %s: not graded" % name); continue
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump(night, t); nf = t.name
        res[name] = {}
        confs = [(x, float(x), False) for x in a.scales.split(",")] + [("concentration only x1", 1.0, True)]
        for lab, sc, ko in confs:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
                json.dump(dict(sizes, sims=a.sims, scale=sc, kappa_only=ko), t); pf = t.name
            r = subprocess.run(["node", os.path.join(HERE, "ous.js"), nf, bf, pf], capture_output=True, text=True)
            os.unlink(pf)
            if r.returncode:
                print("  %s %s: %s" % (name, lab, r.stderr.strip()[-400:])); continue
            o = json.loads(r.stdout); res[name][lab] = o
            if o["contests"]:
                print("  %s %s: %d contests, re-cut changed %d of %d kept, tau %.2f, ESS %.0f of %d, top-8 %.0f -> %.0f ± %.0f, player log SD %.2f" % (
                    name, lab, len(o["contests"]), o["recut_new"], o["kept"], o["tau"], o["achieved"]["ess"], o["achieved"]["field"], o["achieved"]["top8_base"],
                    o["achieved"]["top8_mean"], o["achieved"]["top8_sd"], o["achieved"]["player_log_sd"]))
        os.unlink(nf)
    json.dump(res, open(os.path.join(HERE, "picks.json"), "w"))
    grade(res)


def grade(res):
    OUT = []
    P = lambda *x: OUT.append(" ".join(str(y) for y in x))
    def ms(v, d=2):
        v = [x for x in v if x is not None]
        if len(v) < 2: return "n/a (%d)" % len(v)
        return ("%+." + str(d) + "f ± %." + str(d) + "f (%d), ahead %d") % (S.mean(v), S.stdev(v) / math.sqrt(len(v)), len(v), sum(x > 1e-12 for x in v))
    rng = random.Random(3)
    real = {}          # (slate, scale, contest) -> per variant: pct, pay, top1 rate, stated
    for name, by in res.items():
        g = name.split("_")[1]
        pts = {r["dk_id"]: E.num(r.get("actual_dk")) or 0.0 for r in E.read(os.path.join(E.DK, name + ".csv"))}
        B = json.load(open(os.path.join(E.DK, "builds", "dk_bank_%s.json" % name)))
        kept = B.get("final") or list(range(len(B["pool"])))
        for sc, o in by.items():
            for c in o["contests"]:
                sf = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c["id"])
                if not os.path.exists(sf): continue
                entries, _ = E.standings(sf)
                fdesc = sorted((e["points"] for e in entries), reverse=True); Nn = len(fdesc)
                key = (name, sc, c["id"])
                real[key] = {"type": ctype(c["name"], Nn), "n": c["n"], "fee": c["fee"] or 0}
                def score(L):
                    v = sum(pts.get(str(i), 0.0) for i in L); pl = E.placed(v, fdesc)
                    return 100 * (Nn - (pl - 1)) / Nn, pl
                for v, s in c["sets"].items():
                    sc_ = [score(L) for L in s["lineups"]]
                    real[key][v] = {"pct": S.mean(x[0] for x in sc_), "places": [x[1] for x in sc_], "stated": s}
                rp = []
                for _ in range(300):
                    pick = rng.sample(kept, min(c["n"], len(kept)))
                    rp.append(S.mean(score(B["pool"][k])[0] for k in pick))
                real[key]["R"] = {"pct": S.mean(rp)}
                real[key]["places_N"] = Nn
    # payouts: the contest's table from the night file is in picks? use the mirror slate
    Mi = E.Mirror(MIRROR); tables = {}
    for (name, sc, cid), r in real.items():
        if cid not in tables:
            _, slate, _ = E.slate_for(Mi, cid)
            cc = next((x for x in (slate or {}).get("contests", []) if str(x["id"]) == cid), None) if slate else None
            tables[cid] = E.pay_table(cc.get("payouts")) if cc else {}
        T = tables[cid]
        for v in ("A", "B", "C"):
            if v in r:
                r[v]["pay"] = S.mean(T.get(pl, 0) for pl in r[v]["places"])
                t1 = max(1, math.ceil(0.01 * r["places_N"]))
                r[v]["top1"] = int(any(pl <= t1 for pl in r[v]["places"]))
                r[v]["real_total"] = sum(T.get(pl, 0) for pl in r[v]["places"])
    for sc in sorted({k[1] for k in real}):
        P("\n## %s" % (sc if "only" in sc else "uncertainty sizes x%s" % sc))
        ach = [res[n][sc]["achieved"] for n in res if sc in res[n] and res[n][sc].get("contests")]
        if ach:
            P("   achieved: ESS %.0f of %.0f lineups; top-8 ownership +%.1f ± %.1f (SD over nights) over the field's own; per-player log SD %.2f (tau %.2f)" % (
                S.mean(x["ess"] for x in ach), S.mean(x["field"] for x in ach), S.mean(x["top8_mean"] - x["top8_base"] for x in ach), S.mean(x["top8_sd"] for x in ach),
                S.mean(x["player_log_sd"] for x in ach), S.mean(res[n][sc]["tau"] for n in res if sc in res[n] and res[n][sc].get("contests"))))
        for t in ("all", "flagship", "main", "qualifier/small"):
            ks = [k for k in real if k[1] == sc and (t == "all" or real[k]["type"] == t)]
            if not ks: continue
            by = defaultdict(list)
            for k in ks: by[k[0]].append(real[k])
            def d(v1, v2, m):
                return [S.mean(x[v1][m] - x[v2][m] for x in xs) for xs in by.values()]
            P("-- %s (%d contests, %d slates)" % (t, len(ks), len(by)))
            P("   finish pct  B - A %s | C - A %s | A - random %s | B - random %s" % (ms(d("B", "A", "pct")), ms(d("C", "A", "pct")), ms(d("A", "R", "pct")), ms(d("B", "R", "pct"))))
            P("   $ per lineup  B - A %s | C - A %s" % (ms(d("B", "A", "pay"), 3), ms(d("C", "A", "pay"), 3)))
        # calibration: stated (by the sim that picked) vs real, summed over contests; top-1% stated vs real rate
        ks = [k for k in real if k[1] == sc]
        for v, simk, lab in (("A", "stated_fixed", "A, fixed sim"), ("B", "stated_uncertain", "B, uncertain sim"), ("A", "stated_uncertain", "A's lineups, uncertain sim")):
            st = sum(real[k][v]["stated"][simk]["ev"] for k in ks); rl = sum(real[k][v]["real_total"] for k in ks); fee = sum(real[k]["fee"] * real[k]["n"] for k in ks)
            t1s = S.mean(real[k][v]["stated"][simk]["top1"] for k in ks); t1r = S.mean(real[k][v]["top1"] for k in ks)
            P("   calibration %-26s stated payout $%.0f vs real $%.0f (x%.2f; fees $%.0f) | stated top-1%% coverage %.3f vs real %.3f (contests %d)" % (lab, st, rl, st / rl if rl else float("nan"), fee, t1s, t1r, len(ks)))
    open(os.path.join(HERE, "ous.out"), "w").write("\n".join(OUT) + "\n")
    print("\n".join(OUT))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--grade-only":
        grade(json.load(open(os.path.join(HERE, "picks.json"))))
    else:
        main()
