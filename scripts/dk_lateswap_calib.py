"""Late-swap calibration (2026-11-24, the coordinator's request; analysis only, no page change).

Are the Swap step's stated numbers right? At each tip break of every saved night (the late-swap backtest's nights,
analysis/cbb/dk/lateswap_2026-11-21.md, and the later graded nights), the stated cash %, top-1 % and expected payout of
each of our entries (and a sample of field entries) are rebuilt with the page's machinery (scripts/dk_lateswap_calib.js:
dk_sim.js nightPoints at the page's 1,000 nights, dk_swap.js hiddenMass / hiddenOwn / fieldDraw / board, the chalk
fitted per contest as dk.html swapChalkFit), the started games' points so far from ESPN's play-by-play at the next tip
(scripts/dk_lateswap_study.py knowledge), and scored against the real final standings: calibration tables, expected vs
real payout, and the simulated spread of each entry's remaining points and of the cash line against the realized.
Variants rescale each player's simulated deviation (a variance multiplier) or turn on the team / game draws; one is
picked held out by night.

  python3 scripts/dk_lateswap_calib.py [--mirror ../br-adp-mirror] [--S 1000] [--sample 40] [--add 2026-11-24:157024]

The standings are read from analysis/cbb/dk/standings/ (a slate's contests: its lobby's, matched by player names).
Usernames are used in memory only (telling our entries apart); nothing written names a user or an entry.
"""
import argparse, collections, json, math, os, random, subprocess, sys, tempfile, glob
import statistics as S

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dk_eval as E                    # noqa: E402
import dk_lateswap_study as L          # noqa: E402

DK = os.path.join(HERE, "..", "analysis", "cbb", "dk")
NIGHTS = [("2026-11-16", "156660"), ("2026-11-17", "156663"), ("2026-11-18", "157033"), ("2026-11-19", "157138"), ("2026-11-19", "157139"),
          ("2026-11-20", "157013"), ("2026-11-20", "157015"), ("2026-11-21", "157017"), ("2026-11-22", "157019")]
BACKTEST = {"156660", "156663", "157033", "157138", "157139"}          # the 2026-11-21 backtest's five
VARIANTS = [{"name": "page", "s": 1.0}, {"name": "x1.25", "s": 1.25}, {"name": "x1.5", "s": 1.5}, {"name": "x2", "s": 2.0},
            {"name": "corr", "s": 1.0, "corr": {"team": 0.2, "game": 0.1}}]
CASH_B = [(0, 20), (20, 50), (50, 80), (80, 95), (95, 100.01)]
TOP_B = [(0, 5), (5, 20), (20, 50), (50, 100.01)]


def contests(sl):
    """The slate's contests with a payout table: every entry with 8 known players, its real rank and points."""
    R = sl["R"]
    byname = {}
    for i, r in R.items():
        byname.setdefault(r["name"], i)
    out = []
    for c in sl["contests"]:
        table, fee = L.pay_of(c)
        if not table:
            continue
        ent, _ = E.standings(os.path.join(DK, "standings", "contest-standings-%s.csv" % c["id"]))
        rows = []
        for e in ent:
            s8 = L.lineup_slots(e["lineup"])
            if len(s8) != 8 or any(n not in byname for _, n in s8):
                continue
            rows.append({"slots": [[s, byname[n]] for s, n in s8], "ours": e["name"].split(" (")[0].lower() == E.USER, "rank": e["rank"], "points": e["points"]})
        out.append({"id": c["id"], "table": {str(k): v for k, v in table.items()}, "fee": fee, "entries": rows, "N_total": len(ent)})
    return out


def run_slate(sl, cs, S_, sample, cache):
    R = sl["R"]
    rows = [{"id": i, "team": r["team"], "game": r["game"], "proj": r["proj"] if r["status"] != "Out" else 0, "miss_dk": r["miss_dk"], "status": r["status"] or ""} for i, r in R.items()]
    cards = {i: {"name": r["name"], "salary": r["salary"], "roster": r["roster"], "game_start": r["tip"], "status": r["status"] or "", "team": r["team"],
                 "game": r["game"], "event": r["event"]} for i, r in R.items()}
    rng = random.Random(int(sl["g"]))
    for c in cs:
        field = [i for i, e in enumerate(c["entries"]) if not e["ours"]]
        pick = set(rng.sample(field, min(sample, len(field))))
        for i, e in enumerate(c["entries"]):
            e["sample"] = i in pick
    breaks = []
    for k in range(len(sl["tips"]) - 1):
        base, left, _ = L.knowledge(sl, k, cache)
        started = [i for i, r in R.items() if r["tip"] and r["tip"] <= sl["tips"][k]]
        breaks.append({"k": k + 1, "at": sl["tips"][k + 1], "started": started, "base": base, "left": left})
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "in.json"), os.path.join(d, "out.json")
        json.dump({"rows": rows, "cards": cards, "own": sl["own"], "z": sl["z"], "S": S_, "seed": int(sl["g"]), "variants": VARIANTS,
                   "contests": cs, "breaks": breaks}, open(a, "w"))
        subprocess.run(["node", os.path.join(HERE, "dk_lateswap_calib.js"), a, b], check=True)
        res = json.load(open(b))
    meta = {c["id"]: c for c in cs}
    for r in res:
        c = meta[r["cid"]]
        N = len(c["entries"])
        paid = max(int(k) for k in c["table"])
        r.update(date=sl["date"], g=sl["g"], W=len(sl["tips"]), N=N, fee=c["fee"], real_cash=int(r["rank"] <= paid),
                 real_top1=int(r["rank"] <= max(1, math.ceil(0.01 * N))), real_pay=float(c["table"].get(str(r["rank"]), 0.0)))
    return res


def bucket(rows, key, real, B):
    out = []
    for lo, hi in B:
        x = [r for r in rows if lo <= 100 * r[key] < hi]
        out.append((lo, min(hi, 100), len(x), 100 * S.mean(r[key] for r in x) if x else None, 100 * S.mean(r[real] for r in x) if x else None,
                    len({(r["g"]) for r in x})))
    return out


def brier(rows):
    return S.mean((r["cash"] - r["real_cash"]) ** 2 + (r["top1"] - r["real_top1"]) ** 2 for r in rows) if rows else None


def write(path, res, add):
    by_v = collections.defaultdict(list)
    for r in res:
        by_v[r["variant"]].append(r)
    page = by_v["page"]
    ours = [r for r in page if r["kind"] == "ours"]
    field = [r for r in page if r["kind"] == "field"]
    slates = sorted({(r["date"], r["g"]) for r in page})
    f1 = lambda x: "–" if x is None else "%.1f" % x
    L_ = ["# Late swap: are the stated numbers calibrated?", "",
          "2026-11-24, the coordinator's request (analysis only; nothing on the page changes). `python3 scripts/dk_lateswap_calib.py`.", "",
          "At each tip break of %d saved nights (the 2026-11-21 backtest's five%s and the later graded nights), every one of our entries' **stated** "
          "cash %%, top-1 %% and expected payout is rebuilt with the page's own code (dk_sim.js nights at the page's 1,000, dk_swap.js board and field "
          "draws, the chalk fitted per contest as the page does, the started games' points so far from ESPN's play-by-play at the next tip) and "
          "scored against the real final standings. A random 40 field entries per contest are scored the same way (their lineups known, as ours are). "
          "An entry counts once per break, so a night's entries repeat across its breaks: the night is the unit, and the per-night rows carry the weight."
          % (len(slates), (" plus " + add) if add else ""), ""]
    # --- headline numbers
    def cal(rows):
        hi = [r for r in rows if r["cash"] >= 0.95]
        return (len(hi), 100 * S.mean(r["real_cash"] for r in hi) if hi else None, 100 * S.mean(r["cash"] for r in hi) if hi else None)
    nh, rh, sh = cal(ours)
    evs, pay = sum(r["ev"] for r in ours), sum(r["real_pay"] for r in ours)
    # --- per night
    nightrows = []
    for d, g in slates:
        o = [r for r in ours if r["g"] == g]
        fr = [r for r in field if r["g"] == g]
        last = max(r["k"] for r in o) if o else 0
        o1 = [r for r in o if r["k"] == 1]
        nightrows.append((d, g, len({r["e"] for r in o}), max((r["W"] for r in o), default=0) - 1, len(o),
                          100 * S.mean(r["cash"] for r in o) if o else None, 100 * S.mean(r["real_cash"] for r in o) if o else None,
                          100 * S.mean(r["top1"] for r in o) if o else None, 100 * S.mean(r["real_top1"] for r in o) if o else None,
                          sum(r["ev"] for r in o1), sum(r["real_pay"] for r in o1), sum(r["fee"] for r in o1),
                          100 * S.mean(r["cash"] for r in fr) if fr else None, 100 * S.mean(r["real_cash"] for r in fr) if fr else None))
    # z-scores of the remaining points and the cash line
    def zstats(rows):
        zs = [(r["points"] - r["sim_mean"]) / r["sim_sd"] for r in rows if r["sim_sd"] and r["sim_sd"] > 0]
        pits = [r["pit"] for r in rows]
        tail = 100 * S.mean(1 if p < 0.05 or p > 0.95 else 0 for p in pits) if pits else None
        return (S.pstdev(zs) if len(zs) > 1 else None, S.mean(zs) if zs else None, tail, len(zs))
    zo, zf = zstats(ours), zstats(field)
    seen, cl = set(), []
    for r in ours:
        key = (r["g"], r["cid"], r["k"])
        if key in seen or r["cl_sd"] is None:
            continue
        seen.add(key)
        cl.append(r)
    clz = [(r["real_line"] - r["cl_mean"]) / r["cl_sd"] for r in cl if r["cl_sd"] > 0]
    cltail = 100 * S.mean(1 if r["cl_pit"] < 0.05 or r["cl_pit"] > 0.95 else 0 for r in cl) if cl else None
    # --- variants, held out by night
    names = [v["name"] for v in VARIANTS]
    held = []
    for d, g in slates:
        best, bl = None, None
        for v in [n for n in names if n != "corr"]:
            tr = [r for r in by_v[v] if r["g"] != g]
            b = brier(tr)
            if bl is None or b < bl:
                best, bl = v, b
        te = [r for r in by_v[best] if r["g"] == g]
        held.append((d, g, best, brier([r for r in page if r["g"] == g]), brier(te)))
    def ev1(rows):
        x = [r for r in rows if r["k"] == 1]
        return sum(r["ev"] for r in x), sum(r["real_pay"] for r in x), sum(r["fee"] for r in x)
    eo, ef = ev1(ours), ev1(field)
    mid = [r for r in ours if 0.2 <= r["cash"] < 0.95]
    midf = [r for r in field if 0.2 <= r["cash"] < 0.95]
    t5 = [r for r in ours if 0.05 <= r["top1"] < 0.5]
    t5f = [r for r in field if 0.05 <= r["top1"] < 0.5]
    pit = lambda rows: S.mean(r["pit"] for r in rows)
    rms = lambda rows: (S.mean((r["points"] - r["sim_mean"]) ** 2 for r in rows) / S.mean(r["sim_sd"] ** 2 for r in rows)) ** 0.5
    miss = lambda rows: S.mean(r["points"] - r["sim_mean"] for r in rows)
    x125 = [r for r in by_v.get("x1.25", []) if r["kind"] == "ours"]
    e125 = ev1(x125) if x125 else (0, 0, 0)
    L_ += ["## Verdict", "",
           "**Overconfident for our entries; close to calibrated for the field.** The spread of the simulation is about right, so the cause is not mainly "
           "a too-narrow rest-of-game draw: it is that our lineups are picked on the same projections the simulation draws from, so it rates them too well.", "",
           "- **Expected payout:** at each night's first break our entries' stated expected payout sums to **$%s against $%s paid** (%.1fx; fees $%s). "
           "The field sample, scored the same way, states $%s against $%s paid (%.2fx), so the board itself is not inflating payouts." %
           ("{:,.0f}".format(eo[0]), "{:,.0f}".format(eo[1]), eo[0] / eo[1] if eo[1] else 0, "{:,.0f}".format(eo[2]),
            "{:,.0f}".format(ef[0]), "{:,.0f}".format(ef[1]), ef[0] / ef[1] if ef[1] else 0),
           "- **Top 1%%:** our entries stated at 5–50%% (%d entry-breaks, mean %.1f%%) finished top 1%% %.1f%% of the time; the field sample's (%d, mean %.1f%%) %.1f%%." %
           (len(t5), 100 * S.mean(r["top1"] for r in t5), 100 * S.mean(r["real_top1"] for r in t5), len(t5f), 100 * S.mean(r["top1"] for r in t5f), 100 * S.mean(r["real_top1"] for r in t5f)),
           "- **Cash:** stated 95%%+ holds (ours %d entry-breaks at a mean %.1f%% cashed %.1f%%). Between 20%% and 95%% it runs high: ours stated %.1f%%, cashed %.1f%% "
           "(%d entry-breaks); the field sample stated %.1f%%, cashed %.1f%%." % (nh, sh, rh, 100 * S.mean(r["cash"] for r in mid), 100 * S.mean(r["real_cash"] for r in mid), len(mid),
                                                                              100 * S.mean(r["cash"] for r in midf), 100 * S.mean(r["real_cash"] for r in midf)),
           "- **Why:** each entry's final total against its simulated distribution: the realized miss is %.2fx the simulated spread for ours and %.2fx for the field (1.0 = right), "
           "and the cash line's standardized miss has an sd of %s. But our entries finish %.1f points under their simulated mean on average (mean percentile %.3f; the field's "
           "%.1f and %.3f): the sim's projections favour the players our lineups were built from, and those players come in under them. That bias, not the width, is what "
           "inflates our stated payout and top 1%%." % (rms(ours), rms(field), "%.2f" % S.pstdev(clz) if len(clz) > 1 else "–", -miss(ours), pit(ours), miss(field), pit(field)),
           "- **The variance fix:** widening every draw x1.25 brings the share of final totals outside the 5–95%% band from %s%% to about 10%% and lowers the Brier score slightly, "
           "but held out by night it beats the page on only %d of %d nights, and it leaves our first-break stated payout at $%s against $%s. Turning on the team and game draws "
           "changes nothing that matters. Where the widening does help is the field's middle: the field sample's 20–95%% cash runs about 6 points high on the page's draw and close to right at x1.25 (the per-variant table below)." % (f1(zo[2]), sum(1 for _, _, _, bp, bv in held if bv < bp), len(held), "{:,.0f}".format(e125[0]), "{:,.0f}".format(e125[1])),
           "- **Recommendation:** read our stated expected payout and top 1%% as roughly %.1fx too high, and the 20–95%% cash figures as about %d points high; the 95%%+ cash "
           "figures are fine. A variance multiplier is not worth putting on the page on this evidence. The fix that would address the cause is a haircut on our own "
           "entries (their lineups' simulated points shrunk toward the field's view, e.g. by the ~%.1f-point mean miss), to be tested held out before any page change." %
           (eo[0] / eo[1] if eo[1] else 0, round(100 * (S.mean(r["cash"] for r in mid) - S.mean(r["real_cash"] for r in mid))), -miss(ours)),
           "- **A data gap the page shares:** the widest misses are late breaks where a started player has no ESPN id on his card (2026-11-19 main: Malique Ewin, 44.5 "
           "DraftKings points, counted 0 so far with almost no game left). The page's live points (dk_swap.js liveState) map players the same way, so such a player reads "
           "0 there too.",
           "- **2026-11-24 is not in yet:** the sync repo holds its late-swap standings from mid-slate only (time remaining and hidden slots). Once the final standings "
           "are saved to analysis/cbb/dk/standings/, add it with `python3 scripts/dk_lateswap_calib.py --add 2026-11-24:157024`.",
           "- **Thin sample:** %d nights; three of them (11-16, 11-21, 11-22) hold 1–4 of our entries, and a few big cashes decide the payout totals." % len(slates), ""]
    L_ += ["", "## Calibration: stated cash % (our entries, every break)", "", "| Stated cash | Entry-breaks | Nights | Mean stated | Real cash rate |", "|---|---|---|---|---|"]
    for lo, hi, n, s_, r_, ng in bucket(ours, "cash", "real_cash", CASH_B):
        L_.append("| %d–%d%% | %d | %d | %s%% | %s%% |" % (lo, hi, n, ng, f1(s_), f1(r_)))
    L_ += ["", "Field sample (40 a contest, lineups known):", "", "| Stated cash | Entry-breaks | Mean stated | Real cash rate |", "|---|---|---|---|"]
    for lo, hi, n, s_, r_, ng in bucket(field, "cash", "real_cash", CASH_B):
        L_.append("| %d–%d%% | %d | %s%% | %s%% |" % (lo, hi, n, f1(s_), f1(r_)))
    L_ += ["", "## Calibration: stated top 1%", "", "| Stated top 1% | Ours: entry-breaks | stated | real | Field sample: entry-breaks | stated | real |", "|---|---|---|---|---|---|---|"]
    fo, ff = bucket(ours, "top1", "real_top1", TOP_B), bucket(field, "top1", "real_top1", TOP_B)
    for x, y in zip(fo, ff):
        L_.append("| %d–%d%% | %d | %s%% | %s%% | %d | %s%% | %s%% |" % (x[0], x[1], x[2], f1(x[3]), f1(x[4]), y[2], f1(y[3]), f1(y[4])))
    L_ += ["", "## Per night (our entries; the payout columns at the first break only, so each entry counts once)", "",
           "| Night | Slate | Entries | Breaks | Entry-breaks | Stated cash | Real cash | Stated top 1% | Real top 1% | Stated $ (1st break) | Real $ | Fees | Field sample: stated cash | real cash |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in nightrows:
        L_.append("| %s | %s | %d | %d | %d | %s%% | %s%% | %s%% | %s%% | %s | %s | %s | %s%% | %s%% |" % (t[0], t[1], t[2], t[3], t[4], f1(t[5]), f1(t[6]), f1(t[7]), f1(t[8]),
                  "{:,.2f}".format(t[9]), "{:,.2f}".format(t[10]), "{:,.2f}".format(t[11]), f1(t[12]), f1(t[13])))
    tot = [sum(t[i] for t in nightrows) for i in (9, 10, 11)]
    L_.append("| **Pooled** | | | | | | | | | **%s** | **%s** | **%s** | | |" % tuple("{:,.2f}".format(x) for x in tot))
    L_ += ["", "## Why: the simulated spread against the realized", "",
           "Each entry's final total placed in its own simulated distribution at the break (z = (final − simulated mean) / simulated sd; "
           "the share outside the 5–95% band is 10% when the spread is right).", "",
           "| | Entry-breaks | sd of z (1 = right) | mean z | outside 5–95% |", "|---|---|---|---|---|",
           "| Our entries | %d | %s | %s | %s%% |" % (zo[3], "%.2f" % zo[0] if zo[0] else "–", "%+.2f" % zo[1] if zo[1] is not None else "–", f1(zo[2])),
           "| Field sample | %d | %s | %s | %s%% |" % (zf[3], "%.2f" % zf[0] if zf[0] else "–", "%+.2f" % zf[1] if zf[1] is not None else "–", f1(zf[2])),
           "| The cash line (each contest, each break) | %d | %s | %s | %s%% |" % (len(clz), "%.2f" % S.pstdev(clz) if len(clz) > 1 else "–",
                                                                                 "%+.2f" % S.mean(clz) if clz else "–", f1(cltail)), ""]
    L_ += ["## Variants", "", "Every player's simulated deviation from his projection scaled (x1.25 / x1.5 / x2), or the team and game draws turned on "
           "(team 0.2, game 0.1). Brier score of stated cash plus stated top 1% against what happened, ours and the field sample (lower is better).", "",
           "| Variant | Brier | 95%+ stated cash: n | real | Our final total outside 5–95% | sd of z |", "|---|---|---|---|---|---|"]
    for v in names:
        rv = by_v[v]
        ov = [r for r in rv if r["kind"] == "ours"]
        n_, r_, _ = cal(ov)
        z_ = zstats(ov)
        L_.append("| %s | %.4f | %d | %s%% | %s%% | %s |" % (v, brier(rv), n_, f1(r_), f1(z_[2]), "%.2f" % z_[0] if z_[0] else "–"))
    L_ += ["", "Stated cash against real, per variant (entry-breaks: stated / real):", "", "| Variant | Kind | 0–20% | 20–50% | 50–80% | 80–95% | 95–100% |", "|---|---|---|---|---|---|---|"]
    for v in names:
        for kd in ("ours", "field"):
            cells = ["%d: %s / %s" % (n, f1(s_), f1(r_)) for _, _, n, s_, r_, _ in bucket([r for r in by_v[v] if r["kind"] == kd], "cash", "real_cash", CASH_B)]
            L_.append("| %s | %s | %s |" % (v, kd, " | ".join(cells)))
    L_ += ["", "Held out by night (the multiplier picked on the other nights, scored on this one):", "",
           "| Night | Slate | Picked | Brier, page | Brier, picked |", "|---|---|---|---|---|"]
    better = 0
    for d, g, v, bp, bv in held:
        better += bv < bp
        L_.append("| %s | %s | %s | %.4f | %.4f |" % (d, g, v, bp, bv))
    L_ += ["", "The picked multiplier beats the page on %d of %d nights held out." % (better, len(held)), ""]
    open(path, "w").write("\n".join(L_) + "\n")
    return {"n95": nh, "real95": rh, "stated95": sh, "ev": evs, "pay": pay, "zsd": zo[0], "tail": zo[2], "held": held, "better": better}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", default=os.path.join(HERE, "..", "..", "br-adp-mirror"))
    ap.add_argument("--S", type=int, default=1000)
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--add", action="append", default=[], help="another night, DATE:DRAFTGROUP, once its final standings are in analysis/cbb/dk/standings/")
    ap.add_argument("--out", default=os.path.join(DK, "lateswap_calibration_2026-11-24.md"))
    ap.add_argument("--dump", default=os.path.join(tempfile.gettempdir(), "dk_lateswap_calib.json"))
    ap.add_argument("--from-dump", action="store_true")
    ap.add_argument("--cache", default=os.path.join(tempfile.gettempdir(), "dk_lateswap_pbp"))
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    if a.from_dump:
        res = json.load(open(a.dump))
    else:
        L.SLATES = NIGHTS + [tuple(x.split(":")) for x in a.add]
        res = []
        for sl in L.load(a.mirror):
            cs = contests(sl)
            if len(sl["tips"]) < 2 or not any(e["ours"] for c in cs for e in c["entries"]):
                print("%s %s: no break or none of ours, skipped" % (sl["date"], sl["g"]), file=sys.stderr)
                continue
            res += run_slate(sl, cs, a.S, a.sample, a.cache)
            print("%s %s done (%d rows)" % (sl["date"], sl["g"], len(res)), file=sys.stderr)
        json.dump(res, open(a.dump, "w"))
    s = write(a.out, res, ", ".join(a.add))
    print(json.dumps(s, default=str))


if __name__ == "__main__":
    main()
