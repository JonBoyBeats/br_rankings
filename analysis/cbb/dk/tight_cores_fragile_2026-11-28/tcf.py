"""Tight cores + fragile cap, mains only (2026-11-28; analysis only). The pre-registered fills in
../tight_cores_fragile_2026-11-28.md, replayed with scripts/dk_core_shadow.py's machinery (tcf.js).

  python3 analysis/cbb/dk/tight_cores_fragile_2026-11-28/tcf.py --mirror ../br-adp-mirror [--sims 500]
"""
import argparse, csv, glob, json, math, os, re, subprocess, sys, tempfile
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../../scripts"))
import dk_eval as E            # noqa: E402
import dk_contest_type as CT    # noqa: E402
import dk_core_shadow as CS     # noqa: E402
num = E.num
SRC = os.environ.get("BRR_SOURCES", os.path.join(HERE, "../../../../../battle-royale-research/data/dk/cbb/sources"))
TODAY = dict(maxExpo=60, minUnique=3, maxCore=15)
TIGHT = dict(maxExpo=60, minUnique=1, maxCore=40)
FRAG_CAP = 25


def q75(xs):
    xs = sorted(xs)
    if not xs:
        return None
    p = 0.75 * (len(xs) - 1)
    lo = int(math.floor(p))
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (p - lo)


def fragile_a(rec):
    band = [r for r in rec if (r.get("status") or "") != "Out" and (num(r.get("salary")) or 0) < 7000
            and 10 <= (num(r.get("fp_dk")) or 0) < 25]
    val = {r["dk_id"]: num(r["fp_dk"]) / (num(r["salary"]) / 1000) for r in band}
    cut = q75(list(val.values()))
    return {k for k, v in val.items() if cut is not None and v >= cut - 1e-12}, {r["dk_id"] for r in band}


norm = lambda s: re.sub(r"[^a-z]", "", re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", (s or "").lower()))


def source_proj(day, g, rec):
    """{source: {dk_id: fp}} for the night's banked source files (Gajewski FPTs; RotoWire DK points from its lines)."""
    out = {}
    names = {norm(r["name"]): r["dk_id"] for r in rec}
    gf = [f for f in glob.glob(os.path.join(SRC, "gajewski", "%s_%s.*" % (day, g)))]
    if gf:
        d = {}
        for r in csv.DictReader(open(gf[0]), delimiter="\t" if gf[0].endswith(".tsv") else ","):
            k = names.get(norm(r.get("Player")))
            if k:
                d[k] = num(r.get("FPTs")) or 0.0
        out["gajewski"] = d
    rf = glob.glob(os.path.join(SRC, "rotowire", "%s_all.*" % day)) + glob.glob(os.path.join(SRC, "rotowire", "%s_%s.*" % (day, g)))
    if rf:
        rows = list(csv.reader(open(rf[0])))
        h = next(i for i, r in enumerate(rows) if "Name" in r and "MIN" in r)
        H = rows[h]
        d = {}
        for r in rows[h + 1:]:
            a = dict(zip(H, r))
            k = names.get(norm(a.get("Name")))
            if not k:
                continue
            f = lambda c: float(a.get(c) or 0)
            d[k] = f("PTS") + 0.5 * f("3PM") + 1.25 * f("REB") + 1.5 * f("AST") + 2 * f("STL") + 2 * f("BLK") - 0.5 * f("TO")
        out["rotowire"] = d
    return out


def fragile_b(rec, src):
    if not src:
        return None
    ours = {r["dk_id"]: num(r.get("fp_dk")) or 0.0 for r in rec if (r.get("status") or "") != "Out"}
    keep = None
    for s, d in src.items():
        both = [k for k in d if k in ours and ours[k] >= 10 and d[k] >= 10]
        cut = q75([ours[k] - d[k] for k in both])
        flag = {k for k in both if cut is not None and ours[k] - d[k] >= cut - 1e-12}
        keep = flag if keep is None else keep & flag
    return keep or set()


def stats(cs_, sal):
    ex = defaultdict(int)
    cores = set()
    for L in cs_:
        for i in L:
            ex[str(i)] += 1
        cores.add(tuple(sorted(sorted(map(str, L), key=lambda i: -sal.get(i, 0))[:3])))
    n = len(cs_)
    return (max(ex.values()) / n if n else 0), len(cores)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", required=True)
    ap.add_argument("--sims", type=int, default=500)
    a = ap.parse_args(argv)
    M = E.Mirror(a.mirror)
    rows, sanity = [], []
    for bf in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
        B = json.load(open(bf))
        day, g = B.get("day"), str(B.get("draft_group"))
        rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (day, g)))
        if not rec or not any(num(r.get("actual_dk")) is not None for r in rec):
            print("%s_%s: not graded" % (day, g)); continue
        slate, start, night = CS.night_for(M, B)
        if not slate:
            print("%s_%s: %s" % (day, g, night)); continue
        cs = {str(c["id"]): c for c in slate.get("contests") or []}
        mains = [cid for cid, ks in (B.get("portfolios") or {}).items() if ks and cid in cs
                 and CT.contest_type(cs[cid].get("name"), num(cs[cid].get("size")) or 0) == "main"
                 and os.path.exists(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))]
        if not mains:
            print("%s_%s: no main contest with standings" % (day, g)); continue
        sal = {r["dk_id"]: num(r.get("salary")) or 0 for r in rec}
        lock = E.at_lock(M, "dk_cbb_morning.json", start)
        ls = next((x for x in (lock or {}).get("slates", []) if str(x["draft_group_id"]) == g), None)
        green = CS.greens(ls["players"]) if ls else set()
        # top 3 cores, greens first (cc44bc8 ranking: best board value of any of the core's lineups)
        kept = B.get("final") or list(range(len(B["pool"])))
        vals = ((B.get("cut_state") or {}).get("board") or {}).get("values")
        if not vals or len(vals) != len(kept):
            print("%s_%s: no board values" % (day, g)); continue
        val = [v[0] if isinstance(v, list) else v for v in vals]
        core = [tuple(sorted(sorted((str(i) for i in B["pool"][k]), key=lambda i: -sal.get(i, 0))[:3])) for k in kept]
        best = defaultdict(lambda: -1e18)
        for k, c in enumerate(core):
            best[c] = max(best[c], val[k])
        gc = sorted([c for c in best if sum(1 for i in c if i in green) >= 2], key=lambda c: -best[c])
        oc = sorted([c for c in best if c not in set(gc)], key=lambda c: -best[c])
        top3 = set((gc + oc)[:3])
        tight = [k for k, c in enumerate(core) if c in top3]
        allk = list(range(len(kept)))
        fa, band = fragile_a(rec)
        src = source_proj(day, g, rec)
        fb = fragile_b(rec, src)
        pts = {r["dk_id"]: num(r.get("actual_dk")) or 0.0 for r in rec}
        proj = {r["dk_id"]: num(r.get("fp_dk")) or 0.0 for r in rec}
        for k in band:
            sanity.append({"day": day, "g": g, "fragile": k in fa, "res": pts[k] - proj[k]})
        V = [dict(name="today", set=allk, **TODAY), dict(name="fragA", set=allk, caps={k: FRAG_CAP for k in fa}, **TODAY),
             dict(name="tight", set=tight, **TIGHT), dict(name="tight_fragA", set=tight, caps={k: FRAG_CAP for k in fa}, **TIGHT)]
        if fb is not None:
            V += [dict(name="fragB", set=allk, caps={k: FRAG_CAP for k in fb}, **TODAY), dict(name="tight_fragB", set=tight, caps={k: FRAG_CAP for k in fb}, **TIGHT)]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump(night, t); nf = t.name
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as t:
            json.dump({"sims": a.sims, "variants": V, "contests": mains}, t); pf = t.name
        r = subprocess.run(["node", os.path.join(HERE, "tcf.js"), nf, bf, pf], capture_output=True, text=True)
        os.unlink(nf); os.unlink(pf)
        if r.returncode:
            print("%s_%s: %s" % (day, g, r.stderr.strip()[-400:])); continue
        o = json.loads(r.stdout)
        for c in o["contests"]:
            cid = c["id"]
            entries, _ = E.standings(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid))
            table = E.pay_table(cs[cid].get("payouts"))
            fee = num(cs[cid].get("entry_fee")) or 0
            for v, Ls in c["sets"].items():
                p, d = CS.grade_lineups(Ls, pts, entries, table)
                mx, nc = stats(Ls, sal)
                rows.append({"day": day, "g": g, "contest": cid, "name": c["name"], "n": c["n"], "variant": v, "seats": len(Ls),
                             "topped": c["topped"][v], "pct": p, "dollars": d, "fees": fee * len(Ls), "max_expo": mx, "cores": nc,
                             "n_fragA": len(fa), "n_fragB": (None if fb is None else len(fb)), "tight_lineups": len(tight)})
        print("%s_%s: %d main contests; greens %d, fragile A %d (of %d in band), fragile B %s, tight-core lineups %d" % (
            day, g, len(o["contests"]), len(green), len(fa), len(band), "n/a" if fb is None else len(fb), len(tight)))
    json.dump({"rows": rows, "sanity": sanity}, open(os.path.join(HERE, "tcf_rows.json"), "w"), indent=0)
    report(rows, sanity)


def mse(xs):
    n = len(xs)
    if n == 0:
        return float("nan"), float("nan")
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5 if n > 1 else float("nan")
    return m, se


def report(rows, sanity):
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[(r["day"], r["g"])][r["variant"]].append(r)
    slates = sorted(by)
    print("\nslates with mains: %d (%s)" % (len(slates), ", ".join("%s_%s" % s for s in slates)))

    def slate_val(rs, key):
        w = sum(r["seats"] for r in rs)
        if key == "pct":
            return sum(r["pct"] * r["seats"] for r in rs) / w
        return sum(r["dollars"] for r in rs) / w
    variants = ["today", "fragA", "tight", "tight_fragA", "fragB", "tight_fragB"]
    print("\n%-12s %-26s %-26s %-10s %-8s %-7s %-9s %-6s" % ("fill", "finish pct vs today", "$/lineup vs today", "net%fees", "seats", "topped", "max expo", "cores"))
    out = {}
    for v in variants:
        S = [s for s in slates if v in by[s] and "today" in by[s]]
        if not S:
            print("%-12s n = 0 slates" % v); continue
        dp = [slate_val(by[s][v], "pct") - slate_val(by[s]["today"], "pct") for s in S]
        dd = [slate_val(by[s][v], "d") - slate_val(by[s]["today"], "d") for s in S]
        rs = [r for s in S for r in by[s][v]]
        net = 100 * (sum(r["dollars"] for r in rs) - sum(r["fees"] for r in rs)) / max(1e-9, sum(r["fees"] for r in rs))
        mp, sp = mse(dp); md, sd = mse(dd)
        kp, kd = sum(x > 0 for x in dp), sum(x > 0 for x in dd)
        mx = sum(r["max_expo"] * r["seats"] for r in rs) / sum(r["seats"] for r in rs)
        nc = sum(r["cores"] for r in rs) / len(rs)
        out[v] = dict(n=len(S), mp=mp, sp=sp, kp=kp, md=md, sd=sd, kd=kd, net=net)
        if v == "today":
            print("%-12s %-26s %-26s %+8.1f%% %5d/%-3d %-7d %6.0f%% %6.1f" % (v, "(base)", "(base)", net, sum(r["seats"] for r in rs),
                  sum(r["n"] for r in rs), sum(r["topped"] for r in rs), 100 * mx, nc))
        else:
            print("%-12s %+6.2f ± %4.2f, %d of %-2d     %+6.2f ± %4.2f, %d of %-2d     %+8.1f%% %5d/%-3d %-7d %6.0f%% %6.1f" % (
                v, mp, sp, kp, len(S), md, sd, kd, len(S), net, sum(r["seats"] for r in rs), sum(r["n"] for r in rs),
                sum(r["topped"] for r in rs), 100 * mx, nc))
    print("\nper slate (finish pct / $ per lineup):")
    for s in slates:
        print("  %s_%s  " % s + "  ".join("%s %.1f/%.2f" % (v, slate_val(by[s][v], "pct"), slate_val(by[s][v], "d")) for v in variants if v in by[s]))
    # Fragile A sanity
    print("\nFragile A sanity (band: salary < $7k, fp_dk 10-25, not Out):")
    nights = sorted({(x["day"], x["g"]) for x in sanity})
    for fl in (True, False):
        per = []
        for n_ in nights:
            xs = [x["res"] for x in sanity if (x["day"], x["g"]) == n_ and x["fragile"] == fl]
            if xs:
                per.append((sum(xs) / len(xs), sum(x > 0 for x in xs) / len(xs), len(xs)))
        m, se = mse([p[0] for p in per]); b, bse = mse([p[1] for p in per])
        print("  %-10s per night n %.1f; actual - proj %+.2f ± %.2f; beat-projection rate %.3f ± %.3f (%d nights)" % (
            "fragile" if fl else "other", sum(p[2] for p in per) / len(per), m, se, b, bse, len(per)))
    d = []
    for n_ in nights:
        f = [x["res"] for x in sanity if (x["day"], x["g"]) == n_ and x["fragile"]]
        o = [x["res"] for x in sanity if (x["day"], x["g"]) == n_ and not x["fragile"]]
        if f and o:
            d.append(sum(f) / len(f) - sum(o) / len(o))
    m, se = mse(d)
    print("  fragile - other, actual - proj: %+.2f ± %.2f, fragile worse on %d of %d nights" % (m, se, sum(x < 0 for x in d), len(d)))
    json.dump(out, open(os.path.join(HERE, "tcf_summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
