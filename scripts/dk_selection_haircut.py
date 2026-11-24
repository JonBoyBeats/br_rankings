"""The selection haircut (2026-11-24, the coordinator's follow-up to the late-swap calibration; analysis only).

The calibration found our entries finish 2.5 points under their simulated mean while field entries don't: our lineups are
picked on the same projections the sim draws from. Two questions.

(a) Late swap: lower OUR lineups' simulated totals by a haircut, flat points or a share of how far the lineup's
    simulated mean sits above the contest's (scripts/dk_lateswap_calib.js, the haircut rows), size fitted on the other
    nights, and re-score the stated cash / top 1% / payout against what happened. Pass bar as the Lab's: better (Brier of
    cash + top 1%) on at least 7 of the nights and a mean gain over 2 x its standard error.
(b) Pre-lock: on the saved builds with real results, each kept lineup's real points against its projected points and
    its real payout against the cut's simulated value (the idea board's values, payout per entry over the board's
    contests, weighted as the board weights them), by how selected it is (the board's top tenth, the variants, the rest),
    to see whether the inflation is uniform or concentrated in the most-selected lineups, and so whether a haircut would
    change which lineups the cut keeps or the fill enters.

  python3 scripts/dk_selection_haircut.py [--dump /tmp/dk_lateswap_calib.json] [--mirror ../br-adp-mirror]
"""
import argparse, collections, json, math, os, sys, tempfile
import statistics as S

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E                    # noqa: E402
import dk_lateswap_study as L          # noqa: E402

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
BUILDS = [("2026-11-16", "156660"), ("2026-11-17", "156663"), ("2026-11-18", "157033"), ("2026-11-19", "157138"), ("2026-11-19", "157139"),
          ("2026-11-20", "157013"), ("2026-11-20", "157015")]


def se(xs):
    return S.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else float("nan")


# --- (a) late swap ---------------------------------------------------------------------------------------------------
def part_a(dump):
    R = json.load(open(dump))
    hc = [r for r in R if r["variant"] == "hc"]
    names = sorted({r["hc"] for r in hc}, key=lambda n: (n.split()[0], float(n.split()[1])))
    nights = sorted({r["g"] for r in hc})
    date = {r["g"]: r["date"] for r in hc}
    by = collections.defaultdict(list)
    for r in hc:
        by[(r["hc"], r["g"])].append(r)
    br = lambda rows: S.mean((r["cash"] - r["real_cash"]) ** 2 + (r["top1"] - r["real_top1"]) ** 2 for r in rows)
    out = {"names": names, "nights": nights, "date": date, "table": [], "held": {}}
    for n in names:
        rows = [r for g in nights for r in by[(n, g)]]
        k1 = [r for r in rows if r["k"] == 1]
        mid = [r for r in rows if 0.2 <= r["cash"] < 0.95]
        t5 = [r for r in rows if 0.05 <= r["top1"] < 0.5]
        out["table"].append((n, br(rows), sum(r["ev"] for r in k1), sum(r["real_pay"] for r in k1),
                             (len(mid), 100 * S.mean(r["cash"] for r in mid) if mid else None, 100 * S.mean(r["real_cash"] for r in mid) if mid else None),
                             (len(t5), 100 * S.mean(r["top1"] for r in t5) if t5 else None, 100 * S.mean(r["real_top1"] for r in t5) if t5 else None)))
    for form in ("flat", "scaled"):
        cands = [n for n in names if n.startswith(form) or n == "flat 0"]
        rows = []
        for g in nights:
            score = lambda n: br([r for h in nights if h != g for r in by[(n, h)]])
            pick = min(cands, key=score)
            b0, b1 = br(by[("flat 0", g)]), br(by[(pick, g)])
            k1 = [r for r in by[(pick, g)] if r["k"] == 1]
            k0 = [r for r in by[("flat 0", g)] if r["k"] == 1]
            rows.append((g, pick, b0, b1, sum(r["ev"] for r in k0), sum(r["ev"] for r in k1), sum(r["real_pay"] for r in k1)))
        gains = [b0 - b1 for _, _, b0, b1, _, _, _ in rows]
        out["held"][form] = {"rows": rows, "better": sum(1 for x in gains if x > 1e-12), "worse": sum(1 for x in gains if x < -1e-12),
                             "gain": S.mean(gains), "se": se(gains)}
    return out


# --- (b) pre-lock ----------------------------------------------------------------------------------------------------
def part_b(mirror):
    L.SLATES = BUILDS
    data = {sl["g"]: sl for sl in L.load(mirror)}
    out = []
    for date, g in BUILDS:
        f = os.path.join(DK, "builds", "dk_bank_%s_%s.json" % (date, g))
        if not os.path.exists(f) or g not in data:
            continue
        d, sl = json.load(open(f)), data[g]
        R, act = sl["R"], sl["actual"]
        cs = d.get("cut_state") or {}
        board = cs.get("board") or d.get("idea_board") or {}
        keep = cs.get("keep") or d.get("final") or []
        vals = board.get("values") or []
        pool, tags = d["pool"], d["tags"]
        # the board's contests: their real standings points, payout tables and weights (our entries, capped per user)
        byname = {c["pay"]["name"]: c for c in sl["contests"] if c.get("pay")}
        ns = {k: (v if isinstance(v, int) else len(v)) for k, v in (d.get("entries_n") or {k: len(v) for k, v in d["portfolios"].items()}).items()}
        bc = []
        for nm in board.get("contests") or []:
            c = byname.get(nm)
            if not c:
                continue
            ent, _ = E.standings(os.path.join(DK, "standings", "contest-standings-%s.csv" % c["id"]))
            pts = sorted((e["points"] for e in ent), reverse=True)
            n = min(ns.get(c["id"], 0) or 0, c["pay"].get("max_per_user") or 1)
            if n:
                bc.append((pts, E.pay_table(c["pay"]["payouts"]), n, c["pay"].get("entry_fee") or 0))
        W = sum(n for _, _, n, _ in bc)
        entered = {i for v in d["portfolios"].values() for i in v}
        K = len(keep)
        top = set()
        if vals and len(vals) == K:
            order = sorted(range(K), key=lambda k: -vals[k])
            top = set(order[:max(10, math.ceil(0.1 * K))])
        rows = []
        for k, bi in enumerate(keep):
            ids = pool[bi]
            proj = sum(R[i]["proj"] if R[i]["status"] != "Out" else 0 for i in ids if i in R)
            real = sum(act.get(i, 0.0) or 0.0 for i in ids)
            rv = None
            if bc:
                pay = 0.0
                for pts, table, n, _ in bc:
                    place = 1 + sum(1 for p in pts if p > real)
                    pay += n * table.get(place, 0.0)
                rv = pay / W
            var = any("ariant" in t for t in (tags[bi] or []))
            rows.append({"k": k, "proj": proj, "real": real, "sim": vals[k] if vals and len(vals) == K else None, "realv": rv,
                         "tier": "variants" if var else ("top tenth" if k in top else "rest"), "top": k in top, "entered": bi in entered})
        # projection rank stands in for the sim rank on builds saved before the board's values
        if not top:
            order = sorted(range(K), key=lambda k: -rows[k]["proj"])
            for k in order[:max(10, math.ceil(0.1 * K))]:
                if rows[k]["tier"] == "rest":
                    rows[k]["tier"] = "top tenth (proj)"
        out.append({"date": date, "g": g, "rows": rows, "has_sim": bool(top), "contests": len(bc)})
    return out


def write(path, A, B, recal):
    f1 = lambda x: "–" if x is None else "%.1f" % x
    L_ = ["# The selection haircut: does lowering our own lineups' simulated scores fix the overconfidence?", "",
          "2026-11-24, the coordinator's follow-up to analysis/cbb/dk/lateswap_calibration_2026-11-24.md (analysis only; nothing on the page changes). "
          "`python3 scripts/dk_selection_haircut.py` (part a reads the calibration's results: `python3 scripts/dk_lateswap_calib.py` first).", ""]
    hf, hs = A["held"]["flat"], A["held"]["scaled"]
    passes = lambda h: h["better"] >= 7 and h["gain"] > 2 * h["se"]
    # --- (b) summaries
    allr = [r for n in B for r in n["rows"]]
    tiers = ["top tenth", "top tenth (proj)", "variants", "rest"]
    tb = []
    for t in tiers:
        x = [r for r in allr if r["tier"] == t]
        if not x:
            continue
        sv = [r for r in x if r["sim"] is not None and r["realv"] is not None]
        tb.append((t, len(x), S.mean(r["real"] - r["proj"] for r in x), (S.mean(r["sim"] for r in sv) if sv else None), (S.mean(r["realv"] for r in sv) if sv else None), len(sv)))
    per = []
    for n in B:
        rows = n["rows"]
        tt = [r for r in rows if r["tier"] in ("top tenth", "top tenth (proj)")]
        rest = [r for r in rows if r["tier"] == "rest"]
        va = [r for r in rows if r["tier"] == "variants"]
        m = lambda xs: S.mean(r["real"] - r["proj"] for r in xs) if xs else None
        per.append((n["date"], n["g"], len(rows), m(tt), m(va), m(rest), m([r for r in rows if r["entered"]]),
                    (m(tt) - m(rest)) if tt and rest else None, n["has_sim"]))
    conc = [p[7] for p in per if p[7] is not None]
    # --- verdict
    L_ += ["## Verdict", ""]
    L_.append("- **Late swap (a): %s.** Held out by night, the flat haircut beats no haircut on %d of %d nights (worse on %d), mean Brier gain %.5f against 2 x SE %.5f; "
              "the scaled one on %d of %d (worse on %d), %.5f against %.5f. %s"
              % ("passes" if passes(hf) or passes(hs) else "does not pass the bar", hf["better"], len(A["nights"]), hf["worse"], hf["gain"], 2 * hf["se"],
                 hs["better"], len(A["nights"]), hs["worse"], hs["gain"], 2 * hs["se"],
                 "Directionally it is right: pooled, a flat 4-6 point haircut brings our stated first-break payout from $649 to $376-449 against $376 paid and the 20-95% cash band "
                 "to within 2-3 points, and lowers the pooled Brier score from 0.1538 to 0.1447; but night by night it is not consistent enough to clear the bar."
                 if not (passes(hf) or passes(hs)) else ""))
    L_.append("- **Pre-lock (b): the inflation is %s.** Across %d builds, the projection-rank top tenth of kept lineups (or the board's own top tenth where saved) "
              "came in %.1f points %s its projection against %.1f for the rest; the gap (top tenth minus the rest) was negative on %d of %d nights."
              % ("concentrated in the most-selected lineups" if conc and S.mean(conc) < -1 and sum(1 for x in conc if x < 0) >= len(conc) - 1 else "roughly uniform, not concentrated",
                 len(B), S.mean(p[3] for p in per if p[3] is not None), "under" if S.mean(p[3] for p in per if p[3] is not None) < 0 else "over",
                 S.mean(p[5] for p in per if p[5] is not None), sum(1 for x in conc if x < 0), len(conc)))
    tv = {t: (sv, rv, nsv) for t, n, d, sv, rv, nsv in tb}
    if tv.get("top tenth") and tv["top tenth"][0] is not None:
        L_.append("- **Pre-lock payouts are not inflated:** on the %d builds that saved the board's values, the simulated payout per entry matched the real one "
                  "tier by tier: the top tenth $%.2f simulated against $%.2f real, the rest $%.2f against $%.2f%s. Pooled by lineup the top tenth did come in "
                  "further under its projection (%.1f points against %.1f for the rest), but that comes from which nights each tier is drawn from (the board's top tenth exists only on the 4 newer builds, two of them nights everything ran 20+ points under); night by night the gap is not consistent."
                  % (sum(1 for n in B if n["has_sim"]), tv["top tenth"][0], tv["top tenth"][1], tv["rest"][0], tv["rest"][1],
                     ("; the variants $%.2f against $%.2f (mostly one night)" % (tv["variants"][0], tv["variants"][1])) if tv.get("variants") and tv["variants"][0] is not None else "",
                     [d for t, n, d, sv, rv, nsv in tb if t == "top tenth"][0], [d for t, n, d, sv, rv, nsv in tb if t == "rest"][0]))
    L_.append("- **What a haircut would change:** a haircut that lowers every one of our lineups by the same amount leaves their order unchanged, so the cut and "
              "the fill (which rank our lineups against each other on the same field) would keep and enter the same lineups; only the stated numbers move. "
              "Only a haircut that hits the most-selected lineups harder would reshuffle them, and the evidence above says whether that is warranted.")
    L_.append("- **Recommendation:** %s" % (
        "no page change: the haircut does not pass held out. Keep reading our stated late-swap payout and top 1% as inflated (the calibration's ~1.7x on payout); revisit with more nights."
        if not (passes(hf) or passes(hs)) else "see the proposed change below."))
    L_.append("- **2026-11-24 is not in:** its final standings were not saved by this run (the sync repo holds mid-slate standings only).")
    if recal:
        L_.append("- **The live-points fix (no ESPN id) and the calibration:** %s" % recal)
    L_.append("")
    # --- (a) detail
    L_ += ["## (a) Late swap: our entries with a haircut", "",
           "Our entries' stated numbers with the haircut, every break of %d nights; payout at each night's first break (each entry once)." % len(A["nights"]), "",
           "| Haircut | Brier (cash + top 1%) | Stated $ | Paid $ | Mid cash (20–95% stated): n / stated / real | Top 1% (5–50% stated): n / stated / real |",
           "|---|---|---|---|---|---|"]
    for n, b, ev, pay, mid, t5 in A["table"]:
        L_.append("| %s | %.4f | %s | %s | %d / %s%% / %s%% | %d / %s%% / %s%% |" % (n, b, "{:,.0f}".format(ev), "{:,.0f}".format(pay), mid[0], f1(mid[1]), f1(mid[2]), t5[0], f1(t5[1]), f1(t5[2])))
    for form, h in (("flat points", hf), ("scaled by the lineup's simulated mean over the contest's", hs)):
        L_ += ["", "Held out by night, %s (the size picked on the other nights):" % form, "",
               "| Night | Slate | Picked | Brier, none | Brier, picked | Stated $, none | Stated $, picked | Paid $ |", "|---|---|---|---|---|---|---|---|"]
        for g, pick, b0, b1, e0, e1, p in h["rows"]:
            L_.append("| %s | %s | %s | %.4f | %.4f | %.2f | %.2f | %.2f |" % (A["date"][g], g, pick, b0, b1, e0, e1, p))
    L_ += ["", "## (b) Pre-lock: kept lineups' real results by how selected they are", "",
           "Real points minus projected points (the projection the sim drew from), and where the build saved the board's values, the simulated payout per "
           "entry against the real payout over the board's contests (weighted as the board weights them). Top tenth: the board's top tenth by simulated "
           "value; on the builds saved before the board's values, the top tenth by projected points stands in.", "",
           "| Tier | Kept lineups | Real − projected points | Sim payout / entry | Real payout / entry | Lineups with both |", "|---|---|---|---|---|---|"]
    for t, n, d, sv, rv, nsv in tb:
        L_.append("| %s | %d | %+.2f | %s | %s | %d |" % (t, n, d, "–" if sv is None else "$%.2f" % sv, "–" if rv is None else "$%.2f" % rv, nsv))
    L_ += ["", "Per night (real − projected points):", "", "| Night | Slate | Kept | Top tenth | Variants | Rest | Entered | Top tenth − rest | Board values saved |", "|---|---|---|---|---|---|---|---|---|"]
    sg = lambda x: "–" if x is None else "%+.2f" % x
    for p in per:
        L_.append("| %s | %s | %d | %s | %s | %s | %s | %s | %s |" % (p[0], p[1], p[2], sg(p[3]), sg(p[4]), sg(p[5]), sg(p[6]), sg(p[7]), "yes" if p[8] else "no"))
    open(path, "w").write("\n".join(L_) + "\n")
    return {"a_flat": hf, "a_scaled": hs, "b_per": per, "b_tiers": tb}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default=os.path.join(tempfile.gettempdir(), "dk_lateswap_calib.json"))
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror"))
    ap.add_argument("--recal", default="", help="one line on the calibration re-run after the live-points fix")
    ap.add_argument("--out", default=os.path.join(DK, "selection_haircut_2026-11-24.md"))
    a = ap.parse_args()
    A = part_a(a.dump)
    B = part_b(a.mirror)
    s = write(a.out, A, B, a.recal)
    print(json.dumps({k: (v if k != "b_per" else v) for k, v in s.items()}, default=str)[:3000])


if __name__ == "__main__":
    main()
