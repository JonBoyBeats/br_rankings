"""The DraftKings CBB scorecard (2026-11-25, the coordinator's tracking and grading framework): one headline per arm,
LIVE against PREVIOUS (the arm's version before its last change, logged the same nights) against RULER (the frozen
ruler-2026-11-23, battle-royale-research scripts/cbb_ruler.py), over the last LAST slates and the season. The slate is
the unit: every number is a per-slate value, averaged over slates, and every comparison is a paired difference over the
slates that logged both, +- its SE (the per-slate differences' sd / sqrt(slates)). Grading only.

  minutes      ROTATION band (ours 10-25 DK points) minutes MAE: min_proj | min_old | ruler_min
  per-minute   STARS band (ours 25+) points MAE: fp_dk | old_fp | ruler_fp (all without the DK-average gate; ruler_fp_gate,
               the lock's gated number, is in the night record beside it)
  ownership    the chalk band (max(projected, actual) 15%+) over the slate's graded player-contests: MAE in points and
               the share off by 10+: own_proj | own_raw | own_ruler (the record's, joined by player)
  field        the simulated field's lines against the real ones, per graded contest of 100+ entries: cash line and
               top-10% line, sim minus real (the top-1% line is not logged; eval.csv has the winning score, cash and
               top 10%)
  pool         the cut's kept lineups minus the whole bank: mean real finish percentile in each 100+ contest (as the lab)
  fill         the entered set minus random fills from the whole bank (fill_eval.csv): dollars back, and the entered
               set's percentile among the random fills
  (late swap   removed from the scorecard 2026-11-28, batch item 5: the operator doesn't use late swap)
  over-trust   our entries' real points minus their projected (the sim's mean at lock) points, against the field's
               (field_lineups.csv), per night and rolling (batch item 5, 2026-11-28)
  results      the owner's entries: dollars back minus fees, and return on fees. Read over 20+ nights only.

Columns that were not logged on a slate are n/a on it, never filled in, with three exceptions marked "backfilled":
the ruler's projection on 2026-11-23 and 2026-11-24 (157021, 157024, 157026) IS the live one (the live model was the
lock's until 2026-11-25), and its ownership there is own_raw (the lock's field, before the correction). Slates before
2026-11-23 have no ruler: the lock model's inputs (careers, game logs) for them were never stored.

Versions: scripts/dk_arms.py (analysis/cbb/dk/arm_versions.json). An arm is settling until LAST graded slates have run
under its current version. The same-night-pair check: after a change, the PREVIOUS column must be logged on each of
the first LAST slates (analysis/cbb/dk/process.md); where it is missing, the scorecard says so.

  python3 scripts/dk_eval.py scorecard        (writes analysis/cbb/dk/scorecard.md; misses --friday prints it too)
"""
import csv, datetime as dt, glob, json, math, os, statistics as S
from collections import defaultdict

import dk_arms
import dk_eval as E
import dk_proj_grade as PG

LAST = 7
SCORECARD = os.path.join(E.DK, "scorecard.md")
RULER = "ruler-2026-11-23"
RULER_BACKFILL = {"157021", "157024", "157026"}     # the live model was the ruler's: see the docstring
ARM_OF = {"minutes": "projection", "per-minute": "projection", "ownership": "ownership", "field": "field", "pool": "cut",
          "fill": "fill", "results": None}       # late swap removed 2026-11-28 (batch item 5)
num = PG.num


def mae(pairs):
    return S.mean(abs(a - p) for a, p in pairs) if pairs else None


def three_way(rows, act, live, prev, ruler):
    """{"live", "prev", "ruler", "d_prev", "d_ruler", "n"}: live MAE on every row; each other column's MAE on the rows
    that have it, and live minus it on those same rows (None where it isn't logged)."""
    L = [(act(r), live(r)) for r in rows]
    out = {"live": mae(L), "n": len(L), "prev": None, "ruler": None, "d_prev": None, "d_ruler": None}
    for k, f in (("prev", prev), ("ruler", ruler)):
        rs = [r for r in rows if f(r) is not None]
        if rs:
            c, l = mae([(act(r), f(r)) for r in rs]), mae([(act(r), live(r)) for r in rs])
            out[k], out["d_" + k] = c, l - c
    return out


def logged(rows, col, live_col):
    """The previous column counts as logged on a slate only where it differs from live on some row (cbb_daily fills it
    with the live value before it existed)."""
    return any(num(r.get(col)) is not None and num(r.get(live_col)) is not None and abs(num(r[col]) - num(r[live_col])) > 1e-9 for r in rows)


def ruler_col(rows, g, col, live_col):
    """The ruler's value getter for a slate: the logged column, the live one on the backfilled slates, else None."""
    if g in RULER_BACKFILL:
        return lambda r: num(r.get(live_col))
    if any(num(r.get(col)) is not None for r in rows):
        return lambda r: num(r.get(col))
    return lambda r: None


def projection_arms(name, rows):
    g = name.split("_")[1]
    G = PG.graded(rows)
    rot = [r for r in PG.band(G, *PG.ROTATION) if num(r.get("min")) is not None and num(r.get("min_proj")) is not None]
    stars = PG.band(G, *PG.STARS)
    mp = logged(rows, "min_old", "min_proj")
    pp = logged(rows, "old_fp", "fp_dk")
    m = three_way(rot, lambda r: num(r["min"]), lambda r: num(r["min_proj"]),
                  (lambda r: num(r.get("min_old"))) if mp else (lambda r: None), ruler_col(rows, g, "ruler_min", "min_proj"))
    p = three_way(stars, lambda r: num(r["actual_dk"]), lambda r: num(r["fp_dk"]),
                  (lambda r: num(r.get("old_fp"))) if pp else (lambda r: None), ruler_col(rows, g, "ruler_fp", "fp_dk"))
    for x in (m, p):
        x["backfilled"] = g in RULER_BACKFILL
    return m, p


def ownership_arm(g, rec, own_rows):
    """The chalk band for live, raw and ruler, each scored on the player-contests in the band by max(actual, live, it)."""
    ruler_by = {r["dk_id"]: num(r.get("own_ruler")) for r in rec}
    rows = [r for r in own_rows if str(r["draft_group"]) == g]
    if not rows:
        return None
    prev_on = any(abs(r["p"] - r["raw"]) > 1e-9 for r in rows)
    get = {"prev": (lambda r: r["raw"]) if prev_on else (lambda r: None),
           "ruler": (lambda r: r["raw"]) if g in RULER_BACKFILL else (lambda r: ruler_by.get(r["dk_id"]))}
    band = [r for r in rows if max(r["a"], r["p"]) >= E.CHALK_OWN]
    if not band:
        return None
    off = lambda rs, f: sum(abs(r["a"] - f(r)) >= E.CHALK_OFF for r in rs) / len(rs)
    out = {"live": mae([(r["a"], r["p"]) for r in band]), "live_off": off(band, lambda r: r["p"]), "n": len(band),
           "backfilled": g in RULER_BACKFILL}
    for k, f in get.items():
        rs = [r for r in rows if f(r) is not None and max(r["a"], r["p"], f(r)) >= E.CHALK_OWN]
        if rs:
            c, l = mae([(r["a"], f(r)) for r in rs]), mae([(r["a"], r["p"]) for r in rs])
            out[k], out[k + "_off"], out["d_" + k] = c, off(rs, f), l - c
        else:
            out[k] = out[k + "_off"] = out["d_" + k] = None
    return out


def field_arm(evals):
    """{draft group: {"cash": mean sim - real, "top10": ..., "n": contests}} over graded contests of 100+ entries."""
    by = defaultdict(dict)
    for r in evals:
        if (num(r.get("entries")) or 0) >= 100 and num(r.get("sim_cash")) is not None and num(r.get("field_cash")) is not None:
            by[str(r["draft_group"])][r["contest_id"]] = r
    out = {}
    for g, cs in by.items():
        v = list(cs.values())
        out[g] = {"cash": S.mean(num(r["sim_cash"]) - num(r["field_cash"]) for r in v),
                  "top10": S.mean(num(r["sim_top10"]) - num(r["field_top10"]) for r in v if num(r.get("sim_top10")) is not None),
                  "n": len(v)}
    return out


def pool_arm(evals):
    """{draft group: {"diff": kept minus whole bank, mean real finish percentile, "n": contests}} from the latest saved
    bank with a cut, over its slate's graded contests of 100+ entries."""
    banks = {}
    for f in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if b.get("pool") and b.get("final") and (g not in banks or (b.get("saved_at") or "") >= (banks[g].get("saved_at") or "")):
            banks[g] = b
    contests = defaultdict(set)
    for r in evals:
        contests[str(r["draft_group"])].add(r["contest_id"])
    out = {}
    for g, b in banks.items():
        rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (b["day"], g)))
        if not rec:
            continue
        kept, diffs = sorted(set(b["final"])), []
        for cid in sorted(contests.get(g, ())):
            path = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
            if not os.path.exists(path):
                continue
            entries, players = E.standings(path)
            n = len(entries)
            if n < E.LAB_MIN_ENTRIES:
                continue
            pts = E.night_points(rec, players)
            field = sorted((e["points"] for e in entries), reverse=True)
            pct = [100.0 * (n - (E.placed(sum(pts.get(str(i)) or 0 for i in lu), field) - 1)) / n for lu in b["pool"]]
            diffs.append(S.mean(pct[k] for k in kept) - S.mean(pct))
        if diffs:
            out[g] = {"diff": S.mean(diffs), "n": len(diffs)}
    return out


def fill_arm():
    out = {}
    for r in E.read(E.FILL_EVAL) if os.path.exists(E.FILL_EVAL) else []:
        if r["subset"] == "bank" and num(r.get("entered_dollars")) is not None:
            gap, fees = num(r["entered_dollars"]) - num(r["avg_dollars"]), num(r.get("fees"))
            # "fee": the gap as a share of the night's fees (2026-11-28): $0.10-$1 main-only nights read on the same
            # scale as nights carrying $15 flagships, whose dollars otherwise swamp the mean
            out[str(r["draft_group"])] = {"dollars": gap, "pct": 100.0 * (1 - num(r["beat_entered"])),
                                          "fee": 100.0 * gap / fees if fees else None}
    return out


def swap_arm():
    by = defaultdict(list)
    for r in E.read(E.SWAP_GRADES) if os.path.exists(E.SWAP_GRADES) else []:
        if r.get("accepted") == "1" and num(r.get("gain_actual")) is not None:
            by[str(r["draft_group"])].append(num(r["gain_actual"]))
    return {g: {"gain": S.mean(v), "n": len(v)} for g, v in by.items()}


def results_arm(evals):
    by = defaultdict(lambda: [0.0, 0.0])
    for r in evals:
        if r.get("who") == "mine" and num(r.get("fees")):
            by[str(r["draft_group"])][0] += num(r.get("dollars_back")) or 0
            by[str(r["draft_group"])][1] += num(r["fees"])
    return {g: {"net": d - f, "roi": (d - f) / f} for g, (d, f) in by.items() if f}


def collect():
    """[{slate, date, group, arms: {arm: per-slate dict or None}}] for every graded slate, oldest first."""
    evals = E.read(E.EVAL)
    own_rows = E.own_grade_rows()
    fld, pool, fill, res = field_arm(evals), pool_arm(evals), fill_arm(), results_arm(evals)
    out = []
    for name, rows in PG.slates():
        d, g = name.split("_")
        m, p = projection_arms(name, rows)
        out.append({"slate": name, "date": d, "group": g, "arms": {
            "minutes": m if m["live"] is not None else None, "per-minute": p if p["live"] is not None else None,
            "ownership": ownership_arm(g, rows, own_rows), "field": fld.get(g), "pool": pool.get(g), "fill": fill.get(g),
            "results": res.get(g)}})
    return out


def agg(vals):
    """(mean, SE, slates) of per-slate values (None skipped)."""
    v = [x for x in vals if x is not None]
    if not v:
        return None, None, 0
    return S.mean(v), (S.stdev(v) / math.sqrt(len(v)) if len(v) > 1 else None), len(v)


def f_ms(m, se, n, fmt="%.2f", signed=False):
    if not n:
        return "n/a"
    f = ("%+" + fmt[1:]) if signed else fmt
    return (f % m) + (" ± " + fmt % se if se is not None else "") + " (%d)" % n


def current(arm, arms, today):
    """(the arm's version live today, the one before it): a slate later today than any draft group."""
    return dk_arms.version(arm, today, 10 ** 12, arms)


def settling(arm, slates, arms, today):
    """(version live today, last-changed date, graded slates under it, status)."""
    if arm is None:
        return None, None, None, "-"
    v, _ = current(arm, arms, today)
    if v is None:
        return None, None, 0, "-"
    k = sum(1 for s in slates if dk_arms.version(arm, s["date"], s["group"], arms)[0] is v)
    return v, v["from"] + (" from %s" % v["first_slate"] if v.get("first_slate") else ""), k, ("settled" if k >= LAST else "settling %d of %d" % (k, LAST))


def pair_check(name, arm, slates, arms, today):
    """The same-night-pair check for the arm's version live today: PREVIOUS logged on each of its first LAST graded
    slates."""
    if arm is None:
        return None
    v, before = current(arm, arms, today)
    if v is None or before is None:
        return None
    under = [s for s in slates if dk_arms.version(arm, s["date"], s["group"], arms)[0] is v][:LAST]
    if name in ("minutes", "per-minute", "ownership"):
        miss = [s["slate"] for s in under if not s["arms"].get(name) or s["arms"][name].get("prev") is None]
        if not under:
            return "%s since %s: no graded slate yet; PREVIOUS must be logged on its first %d" % (v["tag"], v["from"], LAST)
        return ("%s: PREVIOUS logged on %d of %d slates" % (v["tag"], len(under) - len(miss), len(under))) + (
            "; MISSING on " + ", ".join(miss) if miss else "")
    return "%s: no PREVIOUS column is logged for this arm (a change here can't be paired on the same nights)" % v["tag"]


HEAD = {"minutes": "ROTATION minutes MAE", "per-minute": "STARS points MAE", "ownership": "chalk-band MAE (off 10+)",
        "field": "sim - real: cash line (top 10%)", "pool": "kept - bank, finish pct", "fill": "entered - random fills: $ (pct); % of fees",
        "late swap": "in - out, DK pts", "results": "net $ (ROI); 20+ nights only"}


def window_cells(name, part):
    """[LIVE, PREVIOUS, RULER, LIVE-PREV, LIVE-RULER] for one window."""
    xs = [s["arms"].get(name) for s in part]
    xs = [x for x in xs if x]
    if name in ("minutes", "per-minute", "ownership"):
        live = agg([x["live"] for x in xs])
        cells = [f_ms(*live), f_ms(*agg([x["prev"] for x in xs])), f_ms(*agg([x["ruler"] for x in xs])),
                 f_ms(*agg([x["d_prev"] for x in xs]), signed=True), f_ms(*agg([x["d_ruler"] for x in xs]), signed=True)]
        if name == "ownership":
            for i, k in ((0, "live_off"), (1, "prev_off"), (2, "ruler_off")):
                m, _, n = agg([x.get(k) for x in xs])
                if n:
                    cells[i] += " (%.0f%%)" % (100 * m)
        if any(x.get("backfilled") for x in xs):
            cells[2] += "*"
        return cells
    if name == "field":
        c, t = agg([x["cash"] for x in xs]), agg([x["top10"] for x in xs])
        return [f_ms(*c, fmt="%.1f", signed=True) + (" (%s)" % f_ms(*t, fmt="%.1f", signed=True) if t[2] else ""), "n/a", "n/a", "n/a", "n/a"]
    if name == "pool":
        return [f_ms(*agg([x["diff"] for x in xs]), fmt="%.1f", signed=True), "n/a", "n/a", "n/a", "n/a"]
    if name == "fill":
        d, p, fe = agg([x["dollars"] for x in xs]), agg([x["pct"] for x in xs]), agg([x.get("fee") for x in xs])
        return [f_ms(*d, fmt="%.2f", signed=True) + (" (%.0f pct)" % p[0] if p[2] else "")
                + ("; %s %% of fees" % f_ms(*fe, fmt="%.0f", signed=True) if fe[2] else ""), "n/a", "n/a", "n/a", "n/a"]
    if name == "late swap":
        return [f_ms(*agg([x["gain"] for x in xs]), fmt="%.1f", signed=True), "n/a", "n/a", "n/a", "n/a"]
    if name == "results":
        n, r = agg([x["net"] for x in xs]), agg([x["roi"] for x in xs])
        return [f_ms(*n, fmt="%.2f", signed=True) + (" (%+.0f%%)" % (100 * r[0]) if r[2] else ""), "n/a", "n/a", "n/a", "n/a"]


def lines(slates=None, arms=None, today=None):
    slates = collect() if slates is None else slates
    arms = arms or dk_arms.load()
    today = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    if not slates:
        return ["Scorecard: no graded slates yet"]
    last = slates[-LAST:]
    out = ["# DraftKings CBB scorecard", "",
           "%d graded slates (%s to %s); last %d: %s to %s. LIVE = what ran that night; PREVIOUS = the arm's version before "
           "its last change, logged the same nights; RULER = %s (frozen). Cells: mean over slates ± SE (slates). "
           "PREVIOUS and RULER: their own level on the slates that logged them; LIVE − X: paired per slate on the rows both "
           "logged, the comparison to read (negative = LIVE better for the MAE arms). Version: live today, with its last-changed date; "
           "status counts the graded slates under it. "
           "* = ruler backfilled (157021, 157024, 157026: the live model was the ruler's). Generated by "
           "`python3 scripts/dk_eval.py scorecard`." % (len(slates), slates[0]["slate"], slates[-1]["slate"], len(last),
                                                       last[0]["slate"], last[-1]["slate"], RULER), "",
           "| Arm | Headline | Version (last changed) | Status | Window | LIVE | PREVIOUS | RULER | LIVE − PREV | LIVE − RULER |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    checks = []
    for name, arm in ARM_OF.items():
        v, since, k, status = settling(arm, slates, arms, today)
        ver = "%s (%s)" % (v["tag"], since) if v else "-"
        for wname, part in (("last %d" % len(last), last), ("season %d" % len(slates), slates)):
            out.append("| %s | %s | %s | %s | %s | %s |" % (name, HEAD[name], ver, status, wname, " | ".join(window_cells(name, part))))
        c = pair_check(name, arm, slates, arms, today)
        if c:
            checks.append("- %s: %s" % (name, c))
    out += ["", "Same-night-pair check (process.md: after a change, PREVIOUS logged on each of the first %d slates):" % LAST, ""] + checks
    out += ["", "## Minutes and per-minute by games played at lock", "",
            "The same headlines split by how many games the player had played this season at lock (season, every graded slate; "
            "gp from the night record or analysis/cbb/dk/gp_at_lock.csv). Cells: mean over slates ± SE (slates).", ""] + gp_lines()
    sl_ = source_lines()
    write_tri_labels((source_grades() or {}).get("triangulation"))
    if sl_:
        out += [""] + sl_
    out += [""] + over_trust_lines()
    out += [""] + fill_type_lines()
    out += [""] + bank_lines()
    cs_ = core_shadow_lines()
    if cs_:
        out += [""] + cs_
    pd = pair_due(len(slates))
    if pd:
        out += ["", pd]
    out += ["", "Notes: the field arm's top-1% line is not logged (eval.csv keeps the winning score, top 10% and cash); "
            "the field, pool and fill arms read LIVE only in the table (fill and bank PREVIOUS: their own sections below/above). Results: read over 20+ nights only."]
    return out


# The games-played split (2026-11-28, the operator: the in-season pieces were starved on the early slates, so read the
# projection headlines by how many games a player had at lock). gp from the night record's gp column (cbb_daily.py from
# 2026-11-28) or, before that, analysis/cbb/dk/gp_at_lock.csv (scripts/dk_gp_backfill.py).
GP_BUCKETS = (("<=3 games", 0, 3), ("4-6 games", 4, 6), ("7+ games", 7, 10 ** 6))
GP_SIDECAR = os.path.join(E.DK, "gp_at_lock.csv")
PAIR_RUNS = os.path.join(E.DK, "pair_backtest_runs.json")


def gp_map():
    out = {}
    if os.path.exists(GP_SIDECAR):
        for r in E.read(GP_SIDECAR):
            out[(r["slate"], r["dk_id"])] = int(float(r["gp"]))
    return out


def gp_lines(window=None):
    """The minutes and per-minute headlines by games played at lock: per bucket, LIVE (mean over slates ± SE) and
    LIVE - PREV, LIVE - RULER (paired per slate on the rows both logged)."""
    side = gp_map()
    per = []
    for name, rows in PG.slates():
        g = name.split("_")[1]
        for r in rows:
            v = num(r.get("gp"))
            r["_gp"] = v if v is not None else side.get((name, r["dk_id"]))
        G = PG.graded(rows)
        mp, pp = logged(rows, "min_old", "min_proj"), logged(rows, "old_fp", "fp_dk")
        cells = {}
        for lab, lo, hi in GP_BUCKETS:
            B = [r for r in G if r["_gp"] is not None and lo <= r["_gp"] <= hi]
            rot = [r for r in PG.band(B, *PG.ROTATION) if num(r.get("min")) is not None and num(r.get("min_proj")) is not None]
            stars = PG.band(B, *PG.STARS)
            cells[lab] = (
                three_way(rot, lambda r: num(r["min"]), lambda r: num(r["min_proj"]), (lambda r: num(r.get("min_old"))) if mp else (lambda r: None),
                          ruler_col(rows, g, "ruler_min", "min_proj")) if rot else None,
                three_way(stars, lambda r: num(r["actual_dk"]), lambda r: num(r["fp_dk"]), (lambda r: num(r.get("old_fp"))) if pp else (lambda r: None),
                          ruler_col(rows, g, "ruler_fp", "fp_dk")) if stars else None)
        per.append(cells)
    if window:
        per = per[-window:]
    out = ["| Headline | Games at lock | LIVE | LIVE − PREV | LIVE − RULER | rows (season) |", "|---|---|---|---|---|---|"]
    for i, head in ((0, HEAD["minutes"]), (1, HEAD["per-minute"])):
        for lab, _, _ in GP_BUCKETS:
            xs = [c[lab][i] for c in per if c[lab][i]]
            out.append("| %s | %s | %s | %s | %s | %d |" % (head, lab, f_ms(*agg([x["live"] for x in xs])), f_ms(*agg([x["d_prev"] for x in xs]), signed=True),
                                                         f_ms(*agg([x["d_ruler"] for x in xs]), signed=True), sum(x["n"] for x in xs)))
    return out


def pair_due(n_graded):
    """The standing pair-backtest re-run: the last run's graded-slate count and when the next is due."""
    if not os.path.exists(PAIR_RUNS):
        return None
    d = json.load(open(PAIR_RUNS))
    last = d["runs"][-1]
    due = last["graded_slates"] + d["every"]
    return ("Projection pair backtest (analysis/cbb/dk/projection_pair_backtest_2026-11-28/ppb.py, ppb_trend.py): last run %s at %d graded "
            "slates; next re-run due at %d graded slates (now %d)%s." % (last["date"], last["graded_slates"], due, n_graded,
                                                                         " — DUE NOW" if n_graded >= due else ""))


# External projection sources in shadow (2026-11-28): battle-royale-research scripts/dk_source.py grades each source
# against ours and the ruler and publishes AGGREGATES only (the sources are paid content) to the mirror's
# dk_cbb_source_grades.json; read here from the mirror beside this checkout (MIRROR=<dir> overrides). Display only.
SOURCE_NAMES = {"gajewski": "Gajewski (shadow)", "rotowire": "RotoWire (shadow)"}
BLEND_AT = 10


def source_grades():
    root = os.path.abspath(os.path.join(E.DK, "..", "..", ".."))
    for d in (os.environ.get("MIRROR"), os.path.join(os.path.dirname(root), "br-adp-mirror")):
        if d and os.path.exists(os.path.join(d, "dk_cbb_source_grades.json")):
            return json.load(open(os.path.join(d, "dk_cbb_source_grades.json")))
    return None


def source_lines(doc=None):
    doc = doc if doc is not None else source_grades()
    if not doc:
        return []
    out = ["## External projection sources (shadow)", "",
           "Graded by battle-royale-research `scripts/dk_source.py` on the rows each source projects (aggregates only: the per-player "
           "values stay in the private repo). Bands by OUR projection; ours = 0 for a player Out at lock. Cells: mean over graded slates "
           "± SE (slates); source − ours is paired per slate (negative = the source better); 'better on' counts slates.", ""]
    for src, d in sorted((doc.get("sources") or {}).items()):
        name = SOURCE_NAMES.get(src, src + " (shadow)")
        sl = d.get("slates") or []
        g = [x for x in sl if x.get("status") == "graded"]
        pend = [x["slate"] for x in sl if x.get("status") != "graded"]
        out.append("### %s: %d graded slate%s%s" % (name, len(g), "" if len(g) == 1 else "s", ("; not final yet: " + ", ".join(pend)) if pend else ""))
        cov = [x["coverage"] for x in sl if isinstance(x.get("coverage"), dict)]
        if cov:
            out += ["", "Coverage (only covered players are graded; a player the source leaves out is not a zero): " + "; ".join(
                "%s ours with a source row %d of %d, teams %d of %d" % (x["slate"], c["ours_matched"], c["lock_players"], c["teams_covered"], c["teams"])
                for x, c in ((x, x["coverage"]) for x in sl if isinstance(x.get("coverage"), dict))) + "."]
        if g:
            out += ["", "| Headline | Ours | %s | Ruler | %s − ours | %s better on | rows |" % (name, name, name), "|---|---|---|---|---|---|---|"]
            for k, lab in (("rot_min", HEAD["minutes"]), ("stars_pts", HEAD["per-minute"]), ("rot_pts", "ROTATION points MAE"),
                           ("all_pts", "points MAE, every covered player"), ("all_min", "minutes MAE, every covered player")):
                xs = [x[k] for x in g if x.get(k) and x[k].get("ours") is not None and x[k].get("source") is not None]
                d_ = [x["source"] - x["ours"] for x in xs]
                out.append("| %s | %s | %s | %s | %s | %d of %d | %d |" % (lab, f_ms(*agg([x["ours"] for x in xs])), f_ms(*agg([x["source"] for x in xs])),
                                                                     f_ms(*agg([x["ruler"] for x in xs])), f_ms(*agg(d_), signed=True),
                                                                     sum(v < 0 for v in d_), len(d_), sum(x["n"] for x in xs)))
            sp = [x["spearman"] for x in g if x.get("spearman") and x["spearman"].get("ours") is not None and x["spearman"].get("source") is not None]
            out.append("| Spearman, projected 10+ (higher better) | %s | %s | n/a | %s | %d of %d | %d |" % (
                f_ms(*agg([x["ours"] for x in sp])), f_ms(*agg([x["source"] for x in sp])), f_ms(*agg([x["source"] - x["ours"] for x in sp]), signed=True),
                sum(x["source"] > x["ours"] for x in sp), len(sp), sum(x["n"] for x in sp)))
            out += ["", "Disagreements (|source − ours| ≥ 4 points), pooled over graded slates:"]
            for t in ("below $7k", "$7k+"):
                ds = [x["disagree"][t] for x in g if x.get("disagree") and x["disagree"].get(t) and x["disagree"][t].get("n")]
                n = sum(x["n"] for x in ds)
                if n:
                    closer = sum(x["source_closer"] * x["n"] for x in ds) / n
                    gap = sum(x["mae_ours_minus_source"] * x["n"] for x in ds) / n
                    out.append("- %s: %d players; the source closer on %.0f%%; |error| ours minus source %+.2f points" % (t, n, 100 * closer, gap))
                else:
                    out.append("- %s: none yet" % t)
            out += ["", "Minutes disagreements (|source − ours| ≥ 6 minutes), pooled over graded slates, who was closer on actual minutes:"]
            for t in ("below $7k", "$7k+"):
                ds = [x["min_disagree"][t] for x in g if x.get("min_disagree") and x["min_disagree"].get(t) and x["min_disagree"][t].get("n")]
                n = sum(x["n"] for x in ds)
                out.append("- %s: %d players; the source closer on %d, ours on %d; |minutes error| ours minus source %+.2f" % (
                    t, n, sum(x["source_closer"] for x in ds), sum(x["ours_closer"] for x in ds),
                    sum(x["mae_ours_minus_source"] * x["n"] for x in ds) / n) if n else "- %s: none yet" % t)
            out += ["", "DK points per minute, players with 10+ actual minutes (MAE; bias = actual − projected), by tier:"]
            for t in ("below $7k", "$7k+"):
                ps = [x["ppm"][t] for x in g if x.get("ppm") and x["ppm"].get(t) and x["ppm"][t].get("n")]
                if ps:
                    out.append("- %s: ours MAE %s, bias %s | source MAE %s, bias %s | rows %d" % (
                        t, f_ms(*agg([x["mae_ours"] for x in ps]), fmt="%.3f"), f_ms(*agg([x["bias_ours"] for x in ps]), fmt="%.3f", signed=True),
                        f_ms(*agg([x["mae_source"] for x in ps]), fmt="%.3f"), f_ms(*agg([x["bias_source"] for x in ps]), fmt="%.3f", signed=True), sum(x["n"] for x in ps)))
                else:
                    out.append("- %s: none yet" % t)
            ow = [x["own"] for x in g if isinstance(x.get("own"), dict)]
            if ow:
                out.append("")
                out.append("Ownership (chalk band, real from 100+ entry contests): source MAE %s, ours %s; off 10+ source %s, ours %s; "
                           "concentration miss (field top 8 − projected top 8) source %s, ours %s." % (
                               f_ms(*agg([x["source"]["mae"] for x in ow])), f_ms(*agg([x["ours"]["mae"] for x in ow])),
                               f_ms(*agg([x["source"]["off10"] for x in ow])), f_ms(*agg([x["ours"]["off10"] for x in ow])),
                               f_ms(*agg([x["conc_source"] for x in ow]), fmt="%.1f", signed=True), f_ms(*agg([x["conc_ours"] for x in ow]), fmt="%.1f", signed=True)))
        out += ["", "%s blend test (ours vs each source vs held-out blend weights of ours and the sources; a hybrid of the source's minutes x "
                "our points per minute; a held-out minutes-only blend weight; projection and ownership by salary tier, on covered players): due at %d graded slates "
                "(now %d)%s." % (name, BLEND_AT, len(g), " — DUE NOW" if len(g) >= BLEND_AT else ""), ""]
    return out + value_own_lines(doc.get("value_own")) + triangulation_lines(doc.get("triangulation"))


def value_own_lines(v):
    """Do source value scores predict ownership? (pre-registered analysis/cbb/dk/source_value_own_2026-11-28.md):
    the nightly aggregates from battle-royale-research dk_source.py value_own. Display only."""
    if not v:
        return []
    n = v.get("source_nights", 0)
    out = ["Source value vs ownership (pre-registered; source nights with real ownership: %d; first read at %d, decision at %d; "
           "PREVIOUS = the live correction %s): %s." % (n, v.get("first_read_at", 5), v.get("decision_at", 10),
                                                        " + ".join(v.get("previous_terms") or []), v.get("status"))]
    t1 = (v.get("test1") or {}).get("all")
    if t1 and t1.get("q5_minus_q1") is not None:
        out.append("- Test 1, our ownership miss (real − ours) by quintile of the sources' value minus ours, Q1 → Q5: %s; Q5 − Q1 %s, positive on %d of %d." % (
            " / ".join("%+.1f" % b["err_live"] if b.get("err_live") is not None else "–" for b in t1["bins"]),
            f_ms(t1["q5_minus_q1"], t1.get("se"), t1["n"], fmt="%.1f", signed=True), t1["positive"], t1["n"]))
    t2 = (v.get("test2") or {}).get("src_edge") or {}
    if t2.get("gain") is not None:
        out.append("- Test 2, + source edge on the correction, held out: chalk MAE %.2f → %.2f, gain %s, better on %d of %d; off 10+ gain %s; %s." % (
            t2["mae_prev"], t2["mae_cand"], f_ms(t2["gain"], t2.get("se"), t2["n"], signed=True), t2["better"], t2["n"],
            f_ms(t2["off10_gain"], t2.get("off10_se"), t2["n"], fmt="%.3f", signed=True), t2["tag"]))
    elif n:
        out.append("- Test 2: %s." % (t2.get("note") or "not run"))
    ps = (v.get("per_source") or {}).get("all") or {}
    nm = {"us": "US", "gj": "GJ", "rw": "RW"}
    if ps.get("alone"):
        cell = lambda d: f_ms(d["mean"], d.get("se"), d["n"]) if d else "n/a"
        out.append("- Per source, Spearman with real ownership (mean over nights): " + "; ".join(
            "%s value %s, projection %s, value within tier %s" % (nm.get(s_, s_), cell(d.get("value")), cell(d.get("proj")), cell(d.get("value_in_tier")))
            for s_, d in sorted(ps["alone"].items(), key=lambda x: ["us", "gj", "rw"].index(x[0]) if x[0] in nm else 9)) + ".")
    for k, d in sorted((ps.get("paired") or {}).items()):
        a_, b_ = k.split("_vs_")
        w = d.get("value_in_tier")
        if w:
            out.append("- %s − %s on common players (%d player-contests), within-tier value Spearman %s; %s leads on %d of %d nights." % (
                nm.get(a_, a_), nm.get(b_, b_), d.get("players", 0), f_ms(w["mean"], w.get("se"), w["n"], fmt="%.3f", signed=True), nm.get(a_, a_), w["leads"], w["n"]))
    var = v.get("variants") or {}
    if any((x or {}).get("gain") is not None for x in var.values()):
        out.append("- Model variants, the live correction + one term, held out (context): " + "; ".join(
            "+ %s gain %s, better on %d of %d" % (t, f_ms(x["gain"], x.get("se"), x["n"], signed=True), x["better"], x["n"])
            for t, x in sorted(var.items()) if (x or {}).get("gain") is not None) + ".")
    tri = v.get("triangulation")
    if isinstance(tri, dict) and tri:
        out.append("- Ownership miss (real − ours) by triangulation group: " + "; ".join(
            "%s %s" % (g, f_ms(x["miss"], x.get("se"), x["nights"], fmt="%.1f", signed=True)) for g, x in sorted(tri.items())) + ".")
    elif tri:
        out.append("- Triangulation groups: %s." % tri)
    return out + [""]


# Source triangulation (shadow; pre-registered analysis/cbb/dk/source_triangulation.md): battle-royale-research
# scripts/dk_triangulate.py groups each player by whether ours / Gajewski / RotoWire agree on minutes and points per
# minute and grades projection recipes per group. Aggregates from the mirror; the per-player group / outlier labels (no
# numbers) are written to analysis/cbb/dk/triangulation_labels.csv. Display only.
TRI_LABELS = os.path.join(E.DK, "triangulation_labels.csv")
TRI_GROUPS = (("G1", "minutes + ppm agree"), ("G2", "minutes split, ppm agree"), ("G3", "minutes agree, ppm split"),
              ("G4", "both split (toss-up)"), ("G5", "in/out split"), ("U", "ungrouped (one source)"))
TRI_RECIPES = ("US", "GJ", "RW", "MEAN", "MEDIAN", "COMBO", "BEST")
TRI_DECIDE = 10


def write_tri_labels(t):
    """The public per-player labels (date, dg, dk_id, name, group, minutes_outlier, ppm_outlier): no numbers."""
    if not t or not t.get("labels"):
        return
    cols = ["date", "dg", "dk_id", "name", "group", "minutes_outlier", "ppm_outlier"]
    with open(TRI_LABELS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(t["labels"])


def triangulation_lines(t):
    if not t or not t.get("slates"):
        return []
    sl = t["slates"]
    g = [x for x in sl if x.get("status") == "graded"]
    out = ["### Source triangulation (shadow): %d slate%s, %d graded" % (len(sl), "" if len(sl) == 1 else "s", len(g)), "",
           "Pre-registered (analysis/cbb/dk/source_triangulation.md): minutes agree within 15%, points per minute within 10% "
           "(max − min over mean); G5 = one source has him out while another has him at 10+. COMBO = ours in G1 / G4 / G5, the "
           "other sources' minutes x our ppm in G2, all sources' minutes x our ppm in G3; BEST = the per-group minutes and ppm "
           "source with the lowest MAE on earlier days. Per-player labels: analysis/cbb/dk/triangulation_labels.csv.", ""]
    out.append("Group counts per slate: " + "; ".join("%s %s" % (x["slate"], " ".join("%s %d" % (k, x["counts"].get(k, 0)) for k, _ in TRI_GROUPS if x["counts"].get(k)))
                                                    for x in sl) + ".")
    if g:
        out += ["", "Points MAE by group and recipe (mean over graded slates ± SE (slates); each source only where it lists the player; "
                "|actual − ours| is the US column):", "",
                "| Group | rows | " + " | ".join(TRI_RECIPES) + " |", "|---|---|" + "---|" * len(TRI_RECIPES)]
        for k, lab in TRI_GROUPS:
            gs = [x["groups"][k] for x in g if (x.get("groups") or {}).get(k)]
            if not gs:
                continue
            cells = [f_ms(*agg([(z["recipes"].get(r) or {}).get("pts") for z in gs])) for r in TRI_RECIPES]
            out.append("| %s %s | %d | %s |" % (k, lab, sum(z["n"] for z in gs), " | ".join(cells)))
        out += ["", "Minutes MAE / ppm MAE (10+ actual minutes), same layout:", "",
                "| Group | " + " | ".join(TRI_RECIPES) + " |", "|---|" + "---|" * len(TRI_RECIPES)]
        for k, lab in TRI_GROUPS:
            gs = [x["groups"][k] for x in g if (x.get("groups") or {}).get(k)]
            if not gs:
                continue
            cells = []
            for r in TRI_RECIPES:
                m = agg([(z["recipes"].get(r) or {}).get("min") for z in gs])
                p = agg([(z["recipes"].get(r) or {}).get("ppm") for z in gs])
                cells.append("%s / %s" % ("%.2f" % m[0] if m[2] else "n/a", "%.3f" % p[0] if p[2] else "n/a"))
            out.append("| %s | %s |" % (k, " | ".join(cells)))
        cl = []
        for k, _ in TRI_GROUPS:
            for dim in ("minutes", "ppm"):
                ts = [x["groups"][k]["closest"][dim] for x in g if (x.get("groups") or {}).get(k) and dim in (x["groups"][k].get("closest") or {})]
                n = sum(z["n"] for z in ts)
                if n:
                    tot = {}
                    for z in ts:
                        for s_, c in z["closest"].items():
                            tot[s_] = tot.get(s_, 0) + c
                    on = sum(z["outlier_n"] for z in ts)
                    cl.append("- %s %s split: closest %s of %d%s" % (k, dim, ", ".join("%s %d" % kv for kv in sorted(tot.items(), key=lambda kv: -kv[1])), n,
                                                                    ("; the outlier was right %d of %d" % (sum(z["outlier_closest"] for z in ts), on)) if on else ""))
        if cl:
            out += ["", "Who was closest on the split dimension (pooled):"] + cl
        g5 = [x["groups"]["G5"] for x in g if (x.get("groups") or {}).get("G5")]
        if g5:
            calls = {}
            for z in g5:
                for s_, c in (z.get("g5_calls") or {}).items():
                    a = calls.setdefault(s_, [0, 0])
                    a[0] += c["right"]; a[1] += c["n"]
            out += ["", "G5 in/out calls right (in = 10+ minutes, out = under 8; played = any minutes): " + ", ".join(
                "%s %d of %d" % (s_, a[0], a[1]) for s_, a in sorted(calls.items())) + "; played %d of %d." % (sum(z.get("g5_played", 0) for z in g5), sum(z["n"] for z in g5))]
        nz = []
        for k, _ in TRI_GROUPS:
            v = agg([(x["groups"].get(k) or {}).get("noise", {}).get("rel_miss_us") for x in g if (x.get("groups") or {}).get(k)])
            if v[2]:
                nz.append("%s %.2f" % (k, v[0]))
        if nz:
            bs = t.get("bank_sigma") or {}
            out += ["", "Realised |actual − ours| / ours by group (projected 10+): " + ", ".join(nz) +
                    ("; the bank's per-tier miss / mean: " + ", ".join("%s %.2f" % kv for kv in sorted(bs.items())) if bs else "") + "."]
        cv = [x["groups"]["_combo_vs_us"] for x in g if (x.get("groups") or {}).get("_combo_vs_us")]
        d_ = [z["gain"] for z in cv]
        out += ["", "COMBO vs ours, points MAE gain (positive = COMBO better): %s, ahead on %d of %d slates." % (
            f_ms(*agg(d_), signed=True), sum(v > 0 for v in d_), len(d_))]
    out += ["", "Triangulation decision (the per-group recipe with the lowest held-out points MAE, against ours under rule 5): due at %d graded "
            "source slates (now %d)%s." % (TRI_DECIDE, len(g), " — DUE NOW" if len(g) >= TRI_DECIDE else ""), ""]
    return out


# The green-core shadow (2026-11-28, the operator): scripts/dk_core_shadow.py logs, for every main contest of every saved
# build, what the top-5-cores and top-5 green-core picks would have entered beside the page's pick (base, replayed) and
# the real entries, graded on the real standings (analysis/cbb/dk/core_shadow.csv). The decision (process.md rule 5):
# PROVEN needs dollars AND finish pct ahead of the page's pick on 7 of 10 counted main slates. The nights graded in
# cc44bc8 (pre-registration) are context, outside the count.
CORE_SHADOW = os.path.join(E.DK, "core_shadow.csv")
CORE_VARIANTS = (("green_top5", "Top-5 green cores (2+ greens at lock)"), ("top5cores", "Top-5 cores"))
CORE_DECIDE = (7, 10)


def core_shadow_lines(rows=None, evals=None):
    rows = E.read(CORE_SHADOW) if rows is None else rows
    evals = E.read(os.path.join(E.DK, "eval.csv")) if evals is None else evals
    if not rows:
        return []
    import dk_contest_type as CT
    from dk_core_shadow import PREREG_END
    by = defaultdict(lambda: defaultdict(dict))          # slate -> contest -> variant -> row
    phase = {}
    for r in rows:
        k = "%s_%s" % (r["date"], r["draft_group"])
        by[k][r["contest_id"]][r["variant"]] = r
        phase[k] = r["phase"]
    def per_slate(v, ref, keys):
        """{slate: (finish pct delta, $ delta per lineup)} over the slate's main contests where both graded."""
        out = {}
        for k in keys:
            dp, dd = [], []
            for c in by[k].values():
                a, b = c.get(v), c.get(ref)
                if not a or not b or a["finish_pct"] in ("", None) or b["finish_pct"] in ("", None):
                    continue
                dp.append(float(a["finish_pct"]) - float(b["finish_pct"]))
                per = lambda x: float(x["dollars"]) / max(1, len(x["lineups"].split("|")) if x.get("lineups") else int(x["n"]))
                dd.append(per(a) - per(b))     # per lineup picked (a restricted set can fill short), each contest weighted alike (as cc44bc8)
            if dp:
                out[k] = (sum(dp) / len(dp), sum(dd) / len(dd))
        return out
    def net(v, keys):
        d = f = 0.0
        for k in keys:
            for c in by[k].values():
                a = c.get(v)
                if a and a["dollars"] not in ("", None):
                    d += float(a["dollars"])
                    f += float(a["fees"])
        return "%+.1f%%" % (100 * (d - f) / f) if f else "n/a"
    def filled(v, keys):
        """Lineups the pick found / entries to fill: within 5 cores the build's max exposure and min-unique caps can't always fill a contest."""
        got = want = 0
        for k in keys:
            for c in by[k].values():
                a = c.get(v)
                if a:
                    got += len(a["lineups"].split("|")) if a.get("lineups") else 0
                    want += int(a["n"])
        return "%d of %d" % (got, want)
    counted = sorted(k for k in by if phase[k] == "counted")
    pre = sorted(k for k in by if phase[k] != "counted")
    out = ["## Green-core shadow (mains)", "",
           "What two picks would have entered in each main contest (`scripts/dk_core_shadow.py`, logging only; nothing played changes): "
           "the page's pick from the top 5 cores (a core = the lineup's 3 highest salaries; cores ranked by their best board value), and from "
           "the top 5 cores holding 2+ greens at lock (the checks green flag). Each is compared with the page's own pick on the whole kept pool "
           "(replayed on the same machinery) and with the lineups really entered, on the real standings. Cells: per-slate deltas (the mean over the slate's "
           "main contests; $ per lineup, each contest weighted alike), mean ± SE (slates), ahead = slates the variant beat the reference. Decision (process.md rule 5): PROVEN needs dollars "
           "AND finish pct ahead of the page's pick on %d of %d counted main slates. Pre-registration: the %d nights graded in cc44bc8 (through %s), "
           "context only, outside the count. A restricted pick can fill short (the build's max exposure and min-unique caps within 5 cores): "
           "finish pct and $ are per lineup picked, net %% of fees on the fees those lineups would cost, and the last column shows the shortfall." % (
               CORE_DECIDE[0], CORE_DECIDE[1], len(pre), PREREG_END), ""]
    for lab, keys in (("Counted (from %s)" % (counted[0] if counted else "the first main night after %s" % PREREG_END), counted), ("Pre-registration", pre)):
        out += ["### %s: %d main slate%s" % (lab, len(keys), "" if len(keys) == 1 else "s"), ""]
        if not keys:
            out += ["No main slate graded yet: the count starts with the first main night after %s whose build is saved." % PREREG_END, ""]
            continue
        out += ["| Variant | vs the page's pick: finish pct | vs page: $ a lineup | vs entered: finish pct | vs entered: $ a lineup | "
                "Ahead of the page's pick on both | Net % of fees, pooled (variant / page / entered) | Entries filled (variant / page) |", "|---|---|---|---|---|---|---|---|"]
        for v, name in CORE_VARIANTS:
            pb, pe = per_slate(v, "base", keys), per_slate(v, "entered", keys)
            both = sum(1 for x in pb.values() if x[0] > 0 and x[1] > 0)
            cell = lambda d, i, fmt: f_ms(*agg([x[i] for x in d.values()]), fmt=fmt, signed=True) + ", ahead %d" % sum(1 for x in d.values() if x[i] > 0)
            need = " (need %d of %d)" % CORE_DECIDE if lab.startswith("Counted") else ""
            out.append("| %s | %s | %s | %s | %s | %d of %d%s | %s / %s / %s | %s / %s |" % (
                name, cell(pb, 0, "%.2f"), cell(pb, 1, "%.2f"), cell(pe, 0, "%.2f"), cell(pe, 1, "%.2f"), both, len(pb), need,
                net(v, keys), net("base", keys), net("entered", keys), filled(v, keys), filled("base", keys)))
        out.append("")
    # main nights played with no saved build (can't be graded): from eval.csv, after the pre-registration window
    builds = {os.path.basename(f)[8:-5] for f in glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))}
    miss = sorted({"%s_%s" % (r["date"], r["draft_group"]) for r in evals if r.get("who") == "mine" and r["date"] > PREREG_END
                   and CT.contest_type(r.get("contest"), int(float(r.get("entries") or 0))) == "main"
                   and "%s_%s" % (r["date"], r["draft_group"]) not in builds})
    if miss:
        out += ["Main nights with no saved build (can't be graded): " + ", ".join("%s — no saved build, press Save build" % m for m in miss) + ".", ""]
    return out


# Fill proposal 1 (2026-11-28, the operator's batch): flagship and main contests fill by a random draw from the kept
# pool's top half by sim value. Graded per contest type (dk_contest_type) against PREVIOUS, the fill as it was
# (fill_prev: the flagships' joint top-1%, the mains' Max ROI), on the same contests. Flagship tier PROVEN; main tier
# PROVISIONAL, reviewed at MAIN_REVIEW graded main slates on dollars (mains alone revert if they fail). The 11-27 gate:
# when 11-27's standings land, fr_fill.py then fr_p1_recut.py; if the flagship tier no longer clears 2 x SE on 7 slates,
# it reverts. The verdict goes in P1_GATE ({"status": "passes" | "fails", "note": ...}) by hand after that run.
P1_FROM = "2026-11-28"
MAIN_REVIEW = 10
QUAL_REVIEW = 10
P1_GATE = os.path.join(E.DK, "fill_p1_gate.json")
P1_GATE_CONTESTS = ("198269753", "198278517")


def fill_type_lines(evals=None, gate=None, standings_in=None):
    import dk_contest_type as CT
    evals = E.read(E.EVAL) if evals is None else evals
    by = defaultdict(lambda: defaultdict(dict))            # type -> slate -> who -> [dollars, fees]
    for r in evals:
        if r.get("who") not in ("mine", "fill_prev") or r["date"] < P1_FROM or num(r.get("fees")) is None:
            continue
        t = CT.contest_type(r.get("contest"), int(float(r.get("entries") or 0)))
        if t not in ("flagship", "main", "qualifier"):
            continue
        k = "%s_%s" % (r["date"], r["draft_group"])
        c = by[t][k].setdefault(r["contest_id"], {})
        c[r["who"]] = (num(r.get("dollars_back")) or 0.0, num(r["fees"]))
    out = ["## Fill by contest type (proposal 1, from %s)" % P1_FROM, "",
           "Flagship and main contests fill by a random draw from the kept pool's top half by sim value (dk.html, 2026-11-28); "
           "PREVIOUS = the fill as it was (fill_prev: flagships' joint top-1%, mains' Max ROI) from the same pool, graded on the same contests. "
           "Cells: entered minus PREVIOUS, $ per slate (summed over the slate's contests of that type), mean ± SE (slates), ahead = slates entered beat PREVIOUS.", ""]
    for t, tier in (("flagship", "PROVEN"), ("main", "PROVISIONAL"), ("qualifier", "PROVISIONAL")):
        d = []
        for k, cs in sorted(by[t].items()):
            both = [c for c in cs.values() if "mine" in c and "fill_prev" in c]
            if both:
                d.append(sum(c["mine"][0] - c["fill_prev"][0] for c in both))
        m, se, n = agg(d)
        line = "- %s (%s): %s, ahead %d" % (t, tier, f_ms(m, se, n, fmt="%.2f", signed=True), sum(1 for x in d if x > 0))
        if t == "main":
            line += "; review on dollars at %d graded main slates (now %d)%s" % (MAIN_REVIEW, n, " — DUE NOW" if n >= MAIN_REVIEW else "")
        if t == "qualifier":     # batch item 3 (2026-11-28): the qualifier field at QUAL_CHALK 0.35; PREVIOUS the fill under 0.8
            nq = sum(1 for cs in by[t].values() for c in cs.values() if "mine" in c and "fill_prev" in c)
            line += " (the field at QUAL_CHALK 0.35, PREVIOUS under 0.8); review at %d qualifier fields (now %d)%s" % (QUAL_REVIEW, nq, " — DUE NOW" if nq >= QUAL_REVIEW else "")
        out.append(line)
    if gate is None and os.path.exists(P1_GATE):
        gate = json.load(open(P1_GATE))
    if standings_in is None:
        standings_in = all(os.path.exists(os.path.join(E.STANDINGS, "contest-standings-%s.csv" % c)) for c in P1_GATE_CONTESTS[:1])
    if gate and gate.get("status") == "fails":
        st = "FAILS – revert the flagship tier" + (" (%s)" % gate["note"] if gate.get("note") else "")
    elif gate and gate.get("status") == "passes":
        st = "passes" + (" (%s)" % gate["note"] if gate.get("note") else "")
    elif standings_in:
        st = "pending: 11-27's standings are in; run friday_review_2026-11-27/fr_fill.py then fr_p1_recut.py and record the verdict in fill_p1_gate.json"
    else:
        st = "pending (11-27's flagship standings, contest %s, not uploaded)" % P1_GATE_CONTESTS[0]
    out += ["- 11-27 gate (flagship tier on 7 slates since 11-24, must clear 2 × SE): " + st, ""]
    return out


# The bank (2026-11-28, batch item 2): the bank draws plain with Projection noise k 0.5 (Draw the 1). PREVIOUS = the
# night's Draw-the-9 replay at lock (analysis/cbb/dk/bank_prev/, dk_eval.py bankprev). Per slate: the live bank's
# lineups minus PREVIOUS's, mean real finish percentile over the slate's graded 100+ contests. PROVISIONAL, reviewed at
# BANK_REVIEW builds; the fallback is all plain (k 0).
BANK_FROM = "2026-11-28"
BANK_REVIEW = 10
BANK_PREV = os.path.join(E.DK, "bank_prev")


def bank_slate_diff(b, prev_lineups, contests):
    """Live bank minus PREVIOUS, mean real finish percentile over the slate's graded 100+ contests (None if none)."""
    rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (b["day"], b["draft_group"])))
    if not rec:
        return None
    diffs = []
    for cid in sorted(contests):
        path = os.path.join(E.STANDINGS, "contest-standings-%s.csv" % cid)
        if not os.path.exists(path):
            continue
        entries, players = E.standings(path)
        n = len(entries)
        if n < E.LAB_MIN_ENTRIES:
            continue
        pts = E.night_points(rec, players)
        field = sorted((e["points"] for e in entries), reverse=True)
        pc = lambda lu: 100.0 * (n - (E.placed(sum(pts.get(str(i)) or 0 for i in lu), field) - 1)) / n
        diffs.append(S.mean(pc(lu) for lu in b["pool"]) - S.mean(pc(lu) for lu in prev_lineups))
    return S.mean(diffs) if diffs else None


def bank_lines(evals=None):
    evals = E.read(E.EVAL) if evals is None else evals
    contests = defaultdict(set)
    for r in evals:
        contests[str(r["draft_group"])].add(r["contest_id"])
    builds = {}
    for f in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if (b.get("day") or "") >= BANK_FROM and b.get("pool") and (g not in builds or (b.get("saved_at") or "") >= (builds[g].get("saved_at") or "")):
            builds[g] = b
    d, miss = [], []
    for g, b in sorted(builds.items(), key=lambda kv: kv[1]["day"]):
        pf = os.path.join(BANK_PREV, "%s_%s.json" % (b["day"], g))
        if not os.path.exists(pf):
            miss.append("%s_%s" % (b["day"], g))
            continue
        x = bank_slate_diff(b, json.load(open(pf)).get("lineups") or [], contests.get(g, ()))
        if x is not None:
            d.append(x)
    m, se, n = agg(d)
    out = ["## Bank (batch item 2, from %s)" % BANK_FROM, "",
           "The bank draws plain with Projection noise k 0.5 (Draw the 1); PREVIOUS = the night's Draw-the-9 replay at lock (bank_prev/). "
           "Per slate: live bank minus PREVIOUS, mean real finish percentile over the slate's graded 100+ contests.", "",
           "- live bank − Draw-the-9 replay: %s, ahead %d; PROVISIONAL, review at %d builds (now %d)%s; fallback all plain (k 0)" % (
               f_ms(m, se, n, fmt="%.2f", signed=True), sum(1 for x in d if x > 0), BANK_REVIEW, len(builds), " — DUE NOW" if len(builds) >= BANK_REVIEW else "")]
    if miss:
        out.append("- no Draw-the-9 replay yet for: " + ", ".join(miss) + " (dk_eval.py bankprev, nightly)")
    return out + [""]


# The over-trust gauge (2026-11-28, batch item 5): how far our entered lineups finish under what the sim expected of
# them at lock, against the field's lineups on the same slate. The sim's mean of a lineup is its projected points
# (fp_dk at lock, the night record), so the gauge is real minus projected, ours (the saved build's portfolios) and the
# field's (field_lineups.csv: every real lineup in the slate's standings), per night and rolling. The late-swap
# calibration (lateswap_calibration_2026-11-27.md) read -7.5 vs -1.4 at each night's first break.
def over_trust_rows():
    fl = defaultdict(list)
    path = os.path.join(E.DK, "field_lineups.csv")
    for r in (E.read(path) if os.path.exists(path) else []):
        ids = (r.get("lineup") or "").split()
        if len(ids) == 8 and "?" not in ids:
            fl[str(r["draft_group"])].append(ids)
    builds = {}
    for f in sorted(glob.glob(os.path.join(E.BUILDS, "dk_bank_*.json"))):
        b = json.load(open(f))
        g = str(b.get("draft_group"))
        if b.get("pool") and b.get("portfolios") and (g not in builds or (b.get("saved_at") or "") >= (builds[g].get("saved_at") or "")):
            builds[g] = b
    out = []
    for g, b in sorted(builds.items(), key=lambda kv: kv[1]["day"]):
        rec = E.read(os.path.join(E.DK, "%s_%s.csv" % (b["day"], g)))
        if not rec or not fl.get(g):
            continue
        P = {r["dk_id"]: num(r.get("fp_dk")) or 0.0 for r in rec}
        A = {r["dk_id"]: num(r.get("actual_dk")) for r in rec}
        if not any(v is not None for v in A.values()):
            continue
        gap = lambda L: sum(A.get(str(i)) or 0.0 for i in L) - sum(P.get(str(i), 0.0) for i in L)
        ours = [b["pool"][i] for ks in b["portfolios"].values() for i in ks]
        if not ours:
            continue
        o, f = S.mean(gap(L) for L in ours), S.mean(gap(L) for L in fl[g])
        out.append({"slate": "%s_%s" % (b["day"], g), "ours": o, "field": f, "d": o - f, "n": len(ours)})
    return out


def over_trust_lines(rows=None):
    rows = over_trust_rows() if rows is None else rows
    out = ["## Over-trust gauge (batch item 5, 2026-11-28)", "",
           "Our entered lineups' real points minus their projected points (the sim's mean at lock), against the field's real lineups "
           "on the same slate (field_lineups.csv). Negative = under what the sim expected. Cells: mean over nights ± SE (nights).", ""]
    if not rows:
        return out + ["No night with a saved build, a graded record and the field's lineups yet.", ""]
    for lab, part in (("last %d" % min(LAST, len(rows)), rows[-LAST:]), ("season %d" % len(rows), rows)):
        out.append("- %s: ours %s, field %s, ours − field %s" % (lab, f_ms(*agg([r["ours"] for r in part]), fmt="%.1f", signed=True),
                   f_ms(*agg([r["field"] for r in part]), fmt="%.1f", signed=True), f_ms(*agg([r["d"] for r in part]), fmt="%.1f", signed=True)))
    r = rows[-1]
    out.append("- last night (%s, %d entries): ours %+.1f, field %+.1f" % (r["slate"], r["n"], r["ours"], r["field"]))
    return out + [""]


def write(ls):
    with open(SCORECARD, "w", newline="\n") as f:
        f.write("\n".join(ls) + "\n")


def main(a=None):
    ls = lines()
    write(ls)
    print("\n".join(ls))
